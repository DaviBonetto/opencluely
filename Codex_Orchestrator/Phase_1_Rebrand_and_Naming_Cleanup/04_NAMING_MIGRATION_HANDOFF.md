# Handoff Packet Template

## Header

- Agent: Agent 04 - Naming Migration Planner
- Phase: Phase 1 - Rebrand and Naming Cleanup
- Date: 2026-03-11
- Status: Ready for approval

## Inputs Consumed

- Approved artifacts used:
  - `Codex_Orchestrator/MASTER_RUNBOOK.md`
  - `Codex_Orchestrator/ARTIFACT_TEMPLATES/04_NAMING_MIGRATION_MATRIX.md`
  - `Codex_Orchestrator/ARTIFACT_TEMPLATES/00_HANDOFF_PACKET_TEMPLATE.md`
  - `Codex_Orchestrator/Phase_0_Audit_and_Cleanup/01_LEGACY_AUDIT_MATRIX_FILLED.md`
  - `Codex_Orchestrator/Phase_1_Rebrand_and_Naming_Cleanup/03_BRAND_SYSTEM_SPEC_FILLED.md`
  - Current repository file names, UI labels, and seed content
- Reference image categories used:
  - `CURRENT_STATE`
  - `BAD_PATTERNS_TO_REMOVE`
- Key assumptions:
  - Public-facing naming must be strict and literal
  - Sensitive historical runtime data is not automatically safe to migrate
  - Internal naming may lag public naming as long as UX is already clean

## What Was Produced

- Primary artifact:
  - `Codex_Orchestrator/Phase_1_Rebrand_and_Naming_Cleanup/04_NAMING_MIGRATION_MATRIX_FILLED.md`
- Secondary notes:
  - Added blacklist rules, migration order, and explicit breaking-risk markers
- Decisions locked:
  - `Prep Deck` is the permanent replacement for `LALA`
  - `Brief` is the replacement for public `Template` language
  - Historical references stay only in archive and migration docs

## Open Risks

- Risk: `config/lala_prep.json` still carries personal data under legacy naming.
- Impact: The repository cannot be treated as fully publishable until the file is quarantined or removed.
- Recommended owner: Security lead plus maintainers handling OSS readiness

- Risk: Some internal code identifiers still use `Template` for API stability.
- Impact: Developers may blur public and internal language if the matrix is ignored.
- Recommended owner: Shell Experience Designer and implementation maintainers

## Blockers

- Blocker: No blocker for planning approval
- What is missing: Final quarantine decision for sensitive runtime data
- Best next action: Treat this matrix as a hard constraint and apply it in all downstream implementation work

## Downstream Handoff

- Next agent(s):
  - Agent 05 - Shell Experience Designer
  - Agent 06 - Design Token and Component Lead
  - All later workflow and packaging agents
- What they can trust as stable:
  - Replacement terms and their intended scope
  - The blacklist and archive-only term set
  - Migration priority and breaking-risk categories
- What they must not reinterpret:
  - `Prep Deck` is locked
  - `Brief` is the public preset term
  - `Parakeet` and `LALA` must not return to user-facing surfaces
- What still needs approval:
  - Runtime-data quarantine execution

## Verification

- Checklist used:
  - Brand spec alignment
  - Audit alignment
  - Fresh scan of user-facing files and current labels
- Gaps found:
  - Sensitive runtime data still exists in legacy form
  - Historical orchestrator docs intentionally retain old terms
- Ready for approval: Yes
