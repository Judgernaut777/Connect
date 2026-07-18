#!/usr/bin/env bash
# Sandbox worker: build + host-sandboxed standalone run.
#
# Builds a container image with agentconnect-core / agentconnect-model-manager /
# agentconnect-runtime[worker] installed from a local mcp-agentconnect checkout,
# then runs it attached to the compose network so it can reach ComputeConnect,
# with the shared workspace bind-mounted read-write and everything else on a
# read-only, non-root, capability-dropped rootfs.
#
# All paths/names are env-overridable (sensible defaults below); no secrets are
# hardcoded — COMPUTECONNECT_TOKEN (if you need one) comes from the environment,
# e.g. by sourcing ../.env first:
#
#   set -a; . ../.env; set +a; ./run.sh
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MONOREPO="${MONOREPO_DIR:-/home/mini/mcp-agentconnect}/packages"
WORKSPACE_HOST="${WORKSPACE_DIR:-/home/mini/connect-workspace}"
IMAGE="${CONNECT_WORKER_IMAGE:-connect-worker:m1}"
NETWORK="${CONNECT_NETWORK:-connect_default}"
CONTAINER_UID="${CONTAINER_UID:-10001}"

# --- 1. Stage the three local packages into a clean build context -----------
# (excludes build/ output dirs, egg-info, and __pycache__ so the image only
# gets source + packaging metadata, not stale build artifacts).
CTX="$HERE/.build_context"
rm -rf "$CTX"
mkdir -p "$CTX"
for pkg in agentconnect-core agentconnect-model-manager agentconnect-runtime; do
    cp -a "$MONOREPO/$pkg" "$CTX/$pkg"
    rm -rf "$CTX/$pkg/build"
    find "$CTX/$pkg" -name '*.egg-info' -type d -prune -exec rm -rf {} +
    find "$CTX/$pkg" -name '__pycache__' -type d -prune -exec rm -rf {} +
    find "$CTX/$pkg" -name '*.pyc' -delete
done
cp "$HERE/run_task.py" "$CTX/run_task.py"

# --- 2. Grant the container's non-root uid write access to the shared -------
#        workspace on the host (host dir is typically owned by uid 1000 mode
#        755; the sandboxed container runs as a non-root uid and needs to
#        create files there). Additive ACL, does not touch existing
#        owner/group/other bits.
if command -v setfacl >/dev/null 2>&1; then
    setfacl -R -m "u:${CONTAINER_UID}:rwx" -m "d:u:${CONTAINER_UID}:rwx" "$WORKSPACE_HOST"
else
    echo "WARNING: setfacl not found; falling back to chmod o+w on $WORKSPACE_HOST" >&2
    chmod -R o+w "$WORKSPACE_HOST"
fi

# --- 3. Build ------------------------------------------------------------
docker build -t "$IMAGE" -f "$HERE/Dockerfile" "$CTX"

# --- 4. Confirm the existing compose stack is undisturbed before we run -----
echo "--- compose stack before run ---"
docker compose -p "${COMPOSE_PROJECT:-connect}" ps || true

# --- 5. Sandbox proof (uid, read-only rootfs, workspace write) --------------
echo ""
echo "--- sandbox proof ---"
docker run --rm \
    --network "$NETWORK" \
    -v "$WORKSPACE_HOST:/workspace" \
    --read-only \
    --tmpfs /tmp \
    --user "$CONTAINER_UID" \
    --cap-drop ALL \
    --security-opt no-new-privileges \
    --memory "${SANDBOX_MEMORY_LIMIT:-2g}" \
    --workdir /workspace \
    --entrypoint sh \
    "$IMAGE" -c '
        echo "id -u: $(id -u)";
        echo "-- attempting touch /etc/x (expect permission denied / read-only) --";
        touch /etc/x 2>&1 || true;
        echo "-- attempting touch /root/x (expect permission denied / read-only) --";
        touch /root/x 2>&1 || true;
        echo "-- attempting write inside /workspace (expect success) --";
        touch /workspace/.sandbox_write_test && echo "workspace write: OK" && rm -f /workspace/.sandbox_write_test;
    '

# --- 6. The real standalone task run -----------------------------------------
echo ""
echo "--- task run ---"
docker run --rm \
    --network "$NETWORK" \
    -v "$WORKSPACE_HOST:/workspace" \
    --read-only \
    --tmpfs /tmp \
    --user "$CONTAINER_UID" \
    --cap-drop ALL \
    --security-opt no-new-privileges \
    --memory "${SANDBOX_MEMORY_LIMIT:-2g}" \
    --workdir /workspace \
    -e CC_BASE_URL="${COMPUTECONNECT_CONTAINER_URL:-http://computeconnect:8090/v1}" \
    ${COMPUTECONNECT_TOKEN:+-e CC_API_KEY="${COMPUTECONNECT_TOKEN}"} \
    -e MODEL_ID="${MODEL_ID:-glm-4.7-flash}" \
    "$IMAGE"

# --- 7. Confirm the existing compose stack is still undisturbed -------------
echo ""
echo "--- compose stack after run ---"
docker compose -p "${COMPOSE_PROJECT:-connect}" ps || true

echo ""
echo "--- fizzbuzz.py on the HOST after the run ---"
ls -la "$WORKSPACE_HOST/fizzbuzz.py" 2>&1 || echo "NOT FOUND on host"
