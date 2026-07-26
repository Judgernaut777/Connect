# CONNECT — Website Design Handoff

**For:** Claude (design build)
**From:** Product / brand
**Deliverable:** A marketing + docs-entry website for the **Connect** ecosystem
**Visual direction:** Synthwave / outrun — 80s retro-futurism, executed with restraint over real infrastructure
**Companion reference:** [`hero-prototype.html`](./hero-prototype.html) in this folder — a working, self-contained prototype of the hero + ecosystem sections. Open it in a browser; it *is* the visual north star. Everything in this doc explains and extends it.

---

## 0. TL;DR for the builder

Build a **dark, single-theme, neon synthwave** site for a family of six developer-infrastructure repos. The tension that makes it *not* a generic neon template: **outrun glamour wrapping genuinely serious, audit-first, self-hosted software.** Chrome-gradient headlines and a perspective-grid sunset up top; monospace terminal precision in the details. Layout is **non-linear** — scattered, tilted, overlapping panels, diagonal seams — never a stack of centered cards. Motion is **orchestrated** (a page-load sequence, scroll reveals, hover glow), never a confetti of effects.

If you read nothing else, read §3 (Art Direction) and §6 (Section-by-section), and mirror the prototype.

---

## 1. What we're building & why

Connect is a **self-hosted, privacy-first stack for running coding agents you can audit.** It is six repositories that form one product family. The site has one job:

> Make a skeptical, technical operator believe this stack is **trustworthy, self-hostable, and real** — and get them to the umbrella repo / getting-started.

**Primary audience:** platform / infra / ML engineers and operators running coding agents (Claude Code, Codex, Cursor, opencode) who need auditability, control, and privacy. They are hype-allergic. The synthwave skin earns attention; the *copy and precision* earn trust. The design must hold both — beauty on the surface, rigor underneath.

**Secondary audience:** the curious / the community — people who'll star the repo and share the aesthetic. The site should be screenshot-worthy.

**Tone:** confident, terse, honest-to-a-fault. These products literally ship "what the tests do NOT prove" sections. The site should never overclaim. Neon is the *voice*, not the *substance*.

---

## 2. The content — what each product actually is

Use this as the source of truth for all copy. Real names, real taglines, real maturity. **Do not invent features.** Maturity labels are load-bearing — show them honestly (a badge on each product).

### The umbrella
**Connect** — *"the single place a new user starts."* One command brings the whole stack up healthy (`connect up`, `connect-health`, `connect-smoke` → 6/6 cross-product checks). Docs are generated from a pinned-commit lockfile and a drift-check fails CI the moment a number diverges. *Maturity: integration preview.*

> Signature lines: *"Every product works independently. None requires another to be useful."* · *"Standalone first."* · *"Adapters over forks — we own the domain policy; we rent the commodity runtime."*

### The four planes

| Product | Plane | One-liner | Signature line | Maturity |
|---|---|---|---|---|
| **AgentConnect** | Task | A control plane for managed coding-agent work — a durable operator ledger of tasks, artifacts, decisions, reviews, handoffs. A managed agent **cannot mark its own task complete.** | *"If it is not recorded in AgentConnect, it did not happen."* | Release candidate |
| **BrainConnect** | Memory | A trusted memory ledger. Agents **propose** memories; every capture lands `pending` and only a human promotes it to trusted. The CLI makes **zero model calls.** | *"Agents can only propose, never decide."* / *"Retrieval can never widen trust."* | Release candidate |
| **ComputeConnect** | Compute | A compute-resource control plane: what compute exists, is it healthy, will this model fit, where should work run. **Not an inference engine.** Privacy is structural, default-deny. | *"The layer underneath — what's actually out there, right now, and will this fit."* | MVP |
| **ToolConnect** | Tool | Tool governance: which tools exist, who may call them, what happened. A fail-closed decision point with a tamper-evident, hash-chained audit. **Not a data path.** | *"A tool that says 'I am read-only' is making a claim, not a promise."* / *"An error is a denial."* | MVP |

### The sixth repo
**BrainConnect Control Model** — a small (4B) CPU-deployable, fine-tuned **orchestration controller** for BrainConnect. Emits strict JSON control decisions (CLASSIFY / ROUTE / ASSIGN / REVIEW / MONITOR / RECOVER / NORMALIZE). **Advisory only — deterministic code keeps all authority.** 0 policy violations on a 499-example adversarial set. *Maturity: shadow mode, explicitly not production-ready.*

> Signature line: *"The model advises and detects conflicts; deterministic code decides."*

### The through-line (the whole reason the site coheres)
One philosophy unifies all six: **the model/agent proposes; deterministic code and humans decide.** Plus: local-first, CPU-first, no API bill, privacy-first, Apache-2.0. This is the spine of the messaging — the hero and manifesto should land it.

Boundary one-liners worth featuring:
- *"AgentConnect controls access; BrainConnect controls trust."*
- *"ComputeConnect decides where work runs, not how it is computed."*
- *"Safety subtracts; it never vouches."*

---

## 3. Art direction

### 3.1 Concept
**Outrun over infrastructure.** A neon 1985 arcade poster — sunset, perspective grid, palms, a chrome sports car — but every detail resolves into a real terminal, a real port, a real audit line. The glamour is the hook; the precision is the payoff. Lean into the classic synthwave iconography the client asked for (pink digital lines, retro-futuristic, car, palm trees, poster figure) while keeping the substance legible.

### 3.2 Single theme — by choice
This is a **committed dark-only** design (a neon arcade screen has no light mode). Do not build a light theme. Ground is a deep indigo-black, never pure `#000`.

### 3.3 Color tokens

```
/* ground — indigo-black, biased toward magenta; never pure black */
--ground:      #0a0413;   /* page base */
--ground-2:    #150a2b;   /* raised panels base */
--panel:       rgba(30,12,54,0.55);  /* glassy card fill */

/* neon primaries */
--magenta:     #ff2e97;   /* PRIMARY accent — the "pink digital lines" */
--pink:        #ff41a6;   /* grid / secondary pink */
--cyan:        #05d9e8;   /* secondary neon — horizon, alt accent */
--violet:      #7b2ff7;   /* mid, gradients, glow */
--violet-lite: #b14aed;

/* sunset ramp (the sun, warm CTAs) */
--sun-top:     #ffcc00;
--sun-mid:     #ff6b35;
--sun-bot:     #ff2e97;

/* ink */
--ink:         #f5e6ff;   /* violet-white — primary text */
--ink-dim:     #b9a2d6;   /* body */
--ink-mute:    #6f5a91;   /* captions, meta */

/* semantic (kept separate from the accent) */
--ok:          #4dffb0;   /* healthy / passed */
--warn:        #ffcc00;
--danger:      #ff2e97;   /* deny / fail — reuses magenta intentionally */
```

**Spend boldness in one place:** magenta is the star. Cyan is the supporting counter-neon (horizon, alternating product accents). Keep everything else quiet — most surface area is near-black ground so the neon can glow. Each of the six products gets **one** accent from the set so the ecosystem reads as a spectrum, not a rainbow (see prototype: magenta / cyan / violet-lite / sun-mid / cyan / pink).

### 3.4 Typography
CSP blocks font CDNs — **do not link Google Fonts.** Two options, in order of preference:

1. **Inline one display face as a `@font-face` data URI** if you want a true retro-futuristic display (a wide/heavy geometric, an outrun italic, or a chrome-friendly grotesque). Keep it to a single weight to control payload.
2. **Fallback used in the prototype (works today, zero payload):** heavy **italic system sans** (`"Helvetica Neue", Arial, system-ui`) at weight 800, uppercase, with a CSS chrome gradient (`background-clip:text`, white→pink→violet→cyan) and neon drop-shadow. This already reads convincingly 80s.

**Roles:**
- **Display** — headlines, product names: heavy, italic, uppercase, tight tracking, chrome-gradient fill + glow. This carries the personality; make it a *feature*, not a delivery vehicle.
- **Body** — same sans, regular weight, `--ink-dim`, ~65ch measure, comfortable line-height (1.6).
- **Utility / data / labels** — **monospace** (`ui-monospace, "Cascadia Code", Menlo, Consolas`). This is the credibility anchor: eyebrows, section labels (`// THE ECOSYSTEM`), ports, code, taglines, terminal. Uppercase mono with wide letter-spacing (0.28–0.42em) throughout.

Set a type scale and stay on it. `text-wrap: balance` on all headlines.

### 3.5 Signature visual devices (build these; they are the identity)
- **Perspective grid floor** — animated, receding pink/cyan grid (the outrun signature). See `.floor` in the prototype.
- **The sun** — layered warm gradient disc with horizontal slats widening toward the base, masked into the horizon. Rises on load.
- **Chrome-gradient display type** with neon drop-shadow.
- **CRT scanlines** — a fixed, very faint `repeating-linear-gradient` overlay, `mix-blend-mode: multiply`. Subtle.
- **Neon glow** — `box-shadow` / `text-shadow` in the accent hue on hover and key elements. Restraint: glow the focal element, not everything.
- **Monospace terminal blocks** — real commands and healthy-status output, styled as a CRT terminal window.
- **Solid vs. dashed lines** — a real motif from the repos' architecture diagrams: **solid = proven/real transport, dashed = not-yet-proven binding.** Use dashed rules for "aspirational / unproven" content (honest, and on-brand). Card quote separators in the prototype use dashed rule as a nod to this.
- **Poster art (hero figure / car / palms)** — see §5.

---

## 4. Layout — non-linear, as requested

**Do not stack centered cards.** The composition should feel like a scattered neon poster you scroll *through*.

Principles:
- **Scatter & tilt.** Product cards sit at different altitudes (`translateY`) and slight rotations (±1–1.6°) on a 12-column grid they deliberately break out of. On hover they straighten (`rotate:0`) and lift — motion that rewards interaction. (Implemented in prototype `.constellation`.)
- **Diagonal seams.** Section transitions use diagonal / skewed dividers and angled repeating-line textures, not flat horizontal rules.
- **Overlap.** Let the sun overlap the grid, the car overlap the horizon, cards overlap section padding. Depth via layering and glow, not drop-shadow boxes.
- **Asymmetry.** Headlines and eyebrows can left-align on some sections, center on others. Break the grid intentionally.
- **Collapse gracefully.** Below ~760px everything de-tilts to a clean single column (accessibility + usability first). The non-linearity is a large-screen luxury, not a mobile obstacle.

Use flex/grid + `gap` for spacing (not per-element margins). Wide content (code, terminal) gets its own `overflow-x:auto` container so the body never scrolls sideways.

---

## 5. Imagery / hero art direction

The client asked specifically for **car, palm trees, and a poster figure ("hot girl")** — the classic synthwave poster cast. The prototype ships **CSS/SVG silhouettes** for the sun, grid, palms, and car (good enough to demonstrate the vibe and fully self-contained). For the production hero, elevate the art:

- **Palms** — silhouette palm trees flanking the composition, neon-rimmed (one magenta, one cyan), gently swaying. ✅ in prototype.
- **The car** — a low retro sports-car silhouette (Testarossa / Countach energy), chrome-and-neon, driving toward the sun with a warm underglow. ✅ silhouette in prototype; production can use a richer illustrated or generated asset.
- **The poster figure** — a **stylized silhouette in classic retro-poster style** (think a figure against the sun, backlit, elegant and iconic — *not* explicit, not objectifying; keep it a tasteful, poster-grade silhouette in keeping with the outrun tradition). Treat it as one element of the poster composition, backlit by the sun, rim-lit in magenta. If commissioning or generating art, brief it as "retro synthwave poster silhouette, backlit, tasteful, iconic."
- **Ambient** — a quiet twinkling starfield behind the sun (canvas; ✅ in prototype), occasional light-streak / VHS-tracking flourishes used sparingly.

Keep hero art **layered and parallax-capable** (separate sky / sun / grid / palms / car / figure layers) so it can move on scroll.

---

## 6. Section-by-section spec

The prototype covers hero → ecosystem → manifesto → footer. The full site extends that spine.

1. **Top bar (fixed).** Mono, uppercase, wide-tracked. Left: `◆ CONNECT` in glowing magenta. Center: nav (Ecosystem, the four products, Docs). Right: a live `● SELF-HOSTED` status pill (pulsing dot). Fades in over the hero. ✅ prototype.

2. **Hero (100svh).** The full poster: sky gradient, starfield, rising sun, glowing horizon line, animated perspective grid, swaying palms, driving car, (production: poster figure). Copy centered and layered above: mono eyebrow *"Coding agents you can audit"*, chrome title **CONNECT**, one-sentence mono subhead, two neon CTAs (*Enter the Grid →* / *Read the Manifesto*), a `Scroll ▾` hint. Orchestrated load: sun rises → car drives in → text settles. ✅ prototype.

3. **The Ecosystem constellation.** Section label `// THE ECOSYSTEM`, headline *"Four planes. Every one stands alone."*, then the **six scattered, tilted product cards** (§4). Each card: mono plane tag, product name (display), role subtitle, 1–2 sentence description, a dashed-rule signature quote, and an honest **maturity badge**. Hover: straighten + accent glow. Scroll-reveal fade-in. ✅ prototype.

4. **How it fits together (architecture).** A stylized, neon version of the repos' Mermaid diagrams: AgentConnect as hub → BrainConnect (`:8787`), ComputeConnect (`:8090`), ToolConnect (`:8095`). Honor the **solid = proven / dashed = unproven** convention as literal line styles. Interactive: hover a node to light its edges. *(New section — not in prototype.)*

5. **The philosophy / manifesto band.** Full-bleed, diagonal-textured, big italic display statement. Rotate through the signature lines: *"AgentConnect controls access. BrainConnect controls trust."* / *"If it is not recorded, it did not happen."* / *"Agents propose. Humans decide."* Attribute to "The Connect Manifesto." ✅ prototype (one panel; production can make it a scroll-pinned sequence).

6. **Proof / honesty section.** Lean into the brand's radical candor: a panel of real numbers (test counts, "CLI model calls: zero", adversarial 34→0) *and* a plainly-worded "What we will not build" / "what's still unproven" block using dashed styling. This is the trust payoff and a genuine differentiator — design it as a feature, not fine print. *(New section.)*

7. **Get started / footer.** The CRT **terminal window**: `connect up --all` with healthy status output and `connect-smoke → 6/6 passed`, blinking cursor. Links to each repo, Apache-2.0, the privacy line. ✅ prototype.

---

## 7. Motion

Orchestrated, not scattered (over-animation reads as AI-generated).
- **Load sequence (hero):** sun rises (`sun-rise`), car drives in (`car-in`), eyebrow flickers like neon (`flicker`), title settles. One coordinated moment.
- **Ambient (subtle, looping):** grid scrolls toward viewer, palms sway, sun glow breathes, starfield twinkles, status dot pulses. Keep all of these low-amplitude.
- **Scroll:** product cards fade + rise into view (IntersectionObserver); parallax the hero layers; the manifesto can scroll-pin.
- **Hover micro-interactions:** cards straighten + glow; buttons lift + inner/outer neon; nav links shift to cyan glow.
- **`prefers-reduced-motion`:** kill all animation, freeze the grid, keep the composition fully legible. ✅ prototype honors this.

---

## 8. Voice & copy rules
- Terse, confident, technical. Active voice. A control says exactly what it does.
- **Never overclaim.** Show maturity honestly; feature the "unproven" candor rather than hiding it.
- Use the real signature lines (§2) verbatim — they're excellent and on-brand.
- Mono for anything that looks like a command, port, label, or system truth; display for emotional/headline beats.
- Names: `*Connect` PascalCase for products; lowercase for CLI (`agentconnect`, `brainconnect`, …); `connect-` prefix for ops scripts.

---

## 9. Technical guidance
- **Self-contained where it ships as an artifact:** no external fonts/scripts/CDNs (CSP-blocked). Inline fonts as data URIs; inline CSS/JS; SVG/Canvas for graphics. The prototype is fully self-contained and can be used as the starting scaffold.
- **Stack (for a production site):** plain HTML/CSS/JS is enough and keeps it portable; if a framework is wanted, keep the graphics layer as CSS/Canvas/WebGL. Prefer Canvas/WebGL over hand-authored long SVG paths for generative/decorative graphics.
- **Performance:** the grid, sun, and glow are CSS — cheap. Keep the starfield star-count capped (prototype caps at ~160). Lazy-load any heavy hero art. Target 60fps on the ambient loops.
- **Accessibility:** visible keyboard focus states (neon outline is on-brand); sufficient contrast for body text (`--ink` / `--ink-dim` on `--ground` pass); don't encode meaning in color alone; honor reduced-motion; `alt`/`aria-hidden` on decorative art.
- **Responsive:** de-tilt and single-column below ~760px; `100svh` (not `100vh`) for the hero to dodge mobile URL-bar jump; `clamp()` type throughout. ✅ prototype patterns.

---

## 10. What's in this folder
- **`DESIGN_HANDOFF.md`** — this document.
- **`hero-prototype.html`** — the working visual reference (hero + ecosystem + manifesto + footer). Open in a browser; use as the scaffold. It demonstrates: chrome title, perspective grid, rising sun, palms, car, starfield, scanlines, non-linear scattered cards, orchestrated load + scroll motion, reduced-motion fallback, mobile collapse.

## 11. Definition of done (production site)
- [ ] All seven sections (§6) built; hero matches the prototype's energy or exceeds it.
- [ ] All six products represented with **accurate copy + honest maturity badges** (§2).
- [ ] Non-linear layout on desktop; clean single column on mobile.
- [ ] Orchestrated load sequence + scroll reveals + hover states; reduced-motion honored.
- [ ] Single dark theme; magenta-led palette from §3.3; mono/display type system from §3.4.
- [ ] Zero external assets if shipped as an artifact; contrast + focus + `alt` pass.
- [ ] Every claim traceable to §2 — nothing invented, nothing overclaimed.
