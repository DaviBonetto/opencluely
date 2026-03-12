# Reference Image Framework

## Reference Thesis

- Use these screenshots only to reinforce the approved Opencluely direction: Windows-first, premium dark-glass blue/white, calm live shell, transcript-grounded assistance.
- Treat each file as one of three things: target structure reference, target styling reference, or legacy anti-pattern evidence.
- When one file belongs to multiple categories, read it for the primary category first and use secondary tags only as supporting detail.

## Image Inventory

| Filename | Primary Category | Secondary Categories | What It Should Inform | What It Must Not Decide Alone |
| --- | --- | --- | --- | --- |
| `Captura de tela 2026-03-10 154759.png` | `TARGET_BUTTONS_AND_CARDS` | N/A | compact button silhouette, corner radius, label density | full card layout, glass hierarchy, or motion |
| `Captura de tela 2026-03-10 155108.png` | `TARGET_SETUP_FLOW` | N/A | full-screen setup structure, field grouping, first-run sequencing | token details or debrief behavior |
| `Captura de tela 2026-03-10 155447.png` | `TARGET_BUTTONS_AND_CARDS` | `TARGET_GLASSY_UI` | card treatment, layered surfaces, button/container pairing | shell layout or transcript information architecture |
| `Captura de tela 2026-03-10 155559.png` | `TARGET_SETUP_FLOW` | N/A | setup sub-surface, focused step detail, stacked controls | whole-app shell or post-meeting layouts |
| `Captura de tela 2026-03-10 155827.png` | `TARGET_TOP_BAR` | `TARGET_GLASSY_UI` | floating capsule proportion, top-level control grouping, shell calmness | transcript rows or summary workspace |
| `Captura de tela 2026-03-10 160917.png` | `TARGET_TRANSCRIPT_CHAT` | `TARGET_TOP_BAR`, `TARGET_GLASSY_UI` | live transcript/chat pairing, shell density, layered glass treatment | full debrief IA or setup flow |
| `Captura de tela 2026-03-10 161952.png` | `TARGET_POST_MEETING_SUMMARY` | N/A | debrief workspace hierarchy, summary artifact grouping, wide-layout rhythm | live-shell controls or component micro-states |
| `Captura de tela 2026-03-10 162030.png` | `TARGET_TRANSCRIPT_CHAT` | `TARGET_TOP_BAR` | transcript browsing, evidence-first content stacking, secondary controls | code display or setup behavior |
| `Captura de tela 2026-03-10 164320.png` | `CURRENT_STATE` | `BAD_PATTERNS_TO_REMOVE` | legacy shell evidence, removal targets, QA before/after comparisons | target aesthetics, component tokens, or future interaction rules |

## Category Index

| Category | Purpose | Source Files | Quality | Missing Gaps |
| --- | --- | --- | --- | --- |
| `CURRENT_STATE` | Preserve visual evidence of what the legacy product looks like today so later agents can prove the rewrite is structurally different. | `Captura de tela 2026-03-10 164320.png` | weak | Missing the expanded overlay, notes state, transcript state, Session Setup, and LALA surfaces. |
| `TARGET_TOP_BAR` | Guide the always-on-top control capsule, high-priority action grouping, and calm desktop shell density. | `Captura de tela 2026-03-10 155827.png`, `Captura de tela 2026-03-10 160917.png`, `Captura de tela 2026-03-10 162030.png` | strong | Missing explicit hover/focus/recording-active states, but structure coverage is good enough for Phase 2 specs. |
| `TARGET_GLASSY_UI` | Guide blur layering, border contrast, panel depth, and the approved dark-glass blue/white mood. | `Captura de tela 2026-03-10 155447.png`, `Captura de tela 2026-03-10 155827.png`, `Captura de tela 2026-03-10 160917.png` | medium | Missing a full-window example that shows how glass rules extend beyond the shell capsule. |
| `TARGET_TRANSCRIPT_CHAT` | Guide evidence-first transcript browsing, live assistant surfaces, and transcript/chat adjacency. | `Captura de tela 2026-03-10 160917.png`, `Captura de tela 2026-03-10 162030.png` | medium | Missing empty, loading, and error states plus a grounded follow-up panel example. |
| `TARGET_POST_MEETING_SUMMARY` | Guide the debrief workspace, structured summary groupings, and wide-layout information hierarchy. | `Captura de tela 2026-03-10 161952.png` | medium | Only one canonical summary reference exists; export and drill-down states are still uncovered. |
| `TARGET_BUTTONS_AND_CARDS` | Guide reusable component styling for buttons, cards, surface edges, and compact control clusters. | `Captura de tela 2026-03-10 154759.png`, `Captura de tela 2026-03-10 155447.png` | medium | Missing disabled, destructive, selected, and code-snippet variants. |
| `TARGET_SETUP_FLOW` | Guide Launchpad/setup sequencing, field density, and the shift away from the legacy Session Setup sprawl. | `Captura de tela 2026-03-10 155108.png`, `Captura de tela 2026-03-10 155559.png` | medium | Missing first-run vs returning-user contrast and profile persistence states. |
| `TARGET_CODE_DISPLAY` | Guide code blocks, snippet cards, generated answer formatting, and developer-facing surfaces. | none | missing | A clean canonical code-display reference is still absent and blocks final component-level code-surface decisions. |
| `BAD_PATTERNS_TO_REMOVE` | Preserve visual evidence of legacy UI patterns that must not leak into Opencluely. | `Captura de tela 2026-03-10 164320.png` | weak | Missing fresh captures of legacy Session Setup, LALA/prep panel, and expanded overlay clutter. |

## Agent Mapping

| Agent | Required Categories | Why |
| --- | --- | --- |
| Agent 05 - Shell Experience Designer | `TARGET_TOP_BAR`, `TARGET_GLASSY_UI`, `TARGET_TRANSCRIPT_CHAT` | Defines the shell, live bar, hierarchy, and interaction model. |
| Agent 06 - Design Token and Component Lead | `TARGET_BUTTONS_AND_CARDS`, `TARGET_CODE_DISPLAY`, `TARGET_SETUP_FLOW` | Converts visual direction into tokens, component rules, and code-surface patterns. |
| Agent 07 - Workflow Architect | `TARGET_SETUP_FLOW`, `TARGET_TOP_BAR`, `TARGET_POST_MEETING_SUMMARY` | Replaces Session Setup with Launchpad -> Live Bar -> Debrief flow. |
| Agent 08 - Context Vault Architect | `TARGET_TRANSCRIPT_CHAT`, `TARGET_BUTTONS_AND_CARDS` | Shapes transcript-adjacent context surfaces, snippet cards, and vault empty states. |
| Agent 11 - Post-Meeting Intelligence Designer | `TARGET_POST_MEETING_SUMMARY`, `TARGET_TRANSCRIPT_CHAT` | Designs the debrief workspace, grounded chat, and artifact grouping. |
| Agent 13 - Quality and Reliability Lead | `CURRENT_STATE`, `TARGET_TOP_BAR`, `TARGET_GLASSY_UI`, `TARGET_TRANSCRIPT_CHAT`, `TARGET_POST_MEETING_SUMMARY`, `TARGET_SETUP_FLOW` | Builds before/after visual acceptance criteria and regression gates. |

## Inspiration Rules

### Copy As Inspiration

- composition: use the target top-bar files for a compact floating shell with clear primary/secondary control zones instead of a long undifferentiated strip.
- spacing: use the glassy and setup references for restrained density, breathing room between task groups, and fewer competing edges per surface.
- hierarchy: use transcript/chat and summary references to keep evidence first, generated insight second, and actions tertiary.
- motion idea: infer calm expand/collapse behavior only; treat motion as state clarification, not spectacle.

### Category-Specific Borrowing

- `TARGET_TOP_BAR`: borrow silhouette, compactness, and grouped controls.
- `TARGET_GLASSY_UI`: borrow depth cues, border subtlety, and restrained glow.
- `TARGET_TRANSCRIPT_CHAT`: borrow transcript-led structure and side-by-side assistance affordances.
- `TARGET_POST_MEETING_SUMMARY`: borrow artifact grouping, section contrast, and wide-view scanning rhythm.
- `TARGET_BUTTONS_AND_CARDS`: borrow button weight, card containment, and small-surface polish.
- `TARGET_SETUP_FLOW`: borrow staged setup pacing and focused field grouping.

### Do Not Copy

- branding: do not copy Cluely or any third-party names, logos, or product-specific labels.
- exact wording: do not copy button text, prompts, empty states, or any UI copy verbatim.
- proprietary interaction: do not assume unseen interaction details, motion timing, or feature semantics from static screenshots.
- layout literalism: do not recreate third-party screens 1:1; extract the principle, then restate it inside the approved Opencluely product model.

## Anti-Pattern List

- `Captura de tela 2026-03-10 164320.png` should only be used as removal evidence. It shows an over-compressed strip that is too thin to communicate hierarchy, state, or trust.
- Do not let any legacy Session Setup screen survive as a blocking preflight wall. Agent 01 already flagged that surface as a controller-heavy monolith; the missing screenshot should be captured only to document removal, not to inspire design.
- Do not preserve the legacy `LALA` sidecar or prep-panel framing. Only the reusable prep-content concept survives; the brand, panel identity, and personal-data framing do not.
- Do not derive system-wide component rules from `154759.png` alone. It is a micro-crop, useful for button detail but too narrow to define the broader component language.
- Do not invent `TARGET_CODE_DISPLAY` behavior from transcript or summary screenshots. That category remains open until a real code-surface reference exists.
- Do not blur together `CURRENT_STATE` and target references during reviews. Legacy evidence belongs in comparison checklists, not in future-state mood boards.

## Missing Reference Requests

| Gap | Why It Matters | Proposed Capture |
| --- | --- | --- |
| Clean `TARGET_CODE_DISPLAY` example | Agent 06 cannot lock code block, snippet card, or generated answer styling without a canonical reference. | Capture one polished code-centric surface that shows inline code, multiline block, actions, and surrounding card context. |
| Full legacy Session Setup capture for `BAD_PATTERNS_TO_REMOVE` | Agent 07 needs exact visual evidence of the workflow sprawl being replaced. | Capture the full legacy setup window in its default populated state. |
| Full legacy LALA/prep-panel capture for `BAD_PATTERNS_TO_REMOVE` | Agent 08 needs to separate salvageable prep concepts from the legacy branded surface. | Capture the expanded LALA/prep panel with realistic populated content, then quarantine sensitive data if present. |
| Expanded live legacy overlay capture for `CURRENT_STATE` | Agent 13 needs before/after validation material beyond the narrow strip screenshot. | Capture the live overlay in expanded mode with transcript, notes, and any suggestion area visible. |
| Post-meeting export/drill-down reference | Agent 11 has only one summary overview and no export-state precedent. | Capture or source one summary workspace variant that shows export actions or artifact drill-down behavior. |
