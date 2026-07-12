// Cedar policy set for the Connect full-stack deployment's ToolConnect decision point.
//
// Entity attributes available (see ToolConnect src/toolconnect/policy.py):
//   principal (Agent):  privacy_tier, kind, delegated
//   resource  (Tool):   effect, reversible, idempotent, requires_approval,
//                       reads_sensitive, external_sink
//
// Cedar is default-deny: everything not explicitly permitted is denied, and a tool
// that was never asserted never reaches policy evaluation at all. This starter set
// permits exactly one safe shape — a local agent invoking a non-sensitive READ tool —
// which is what the ecosystem smoke test exercises. Widen it deliberately for your
// own tools; do not loosen it by default.

// Local agents may invoke READ-effect tools that do not read sensitive data.
@id("local-reads")
permit(
    principal,
    action == Action::"invoke",
    resource
) when {
    principal.privacy_tier == "local" &&
    resource.effect == "read" &&
    !resource.reads_sensitive
};

// Nothing running at the rented privacy tier may touch a sensitive reader.
// Delegation cannot launder this: effective_tier() is the worst tier in the chain.
@id("no-sensitive-reads-for-rented")
forbid(
    principal,
    action == Action::"invoke",
    resource
) when {
    principal.privacy_tier == "rented" &&
    resource.reads_sensitive
};
