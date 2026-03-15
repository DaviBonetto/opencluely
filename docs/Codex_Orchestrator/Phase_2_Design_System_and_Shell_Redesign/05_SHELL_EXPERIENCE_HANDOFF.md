# Handoff Packet Template

## Header

- Agent: Agent 05 - Shell Experience Designer
- Phase: Phase 2 - Design System and Shell Redesign
- Date: 2026-03-12
- Status: Ready for approval

## Inputs Consumed

- Approved artifacts used:
  - `Codex_Orchestrator/MASTER_RUNBOOK.md`
  - `Codex_Orchestrator/ARTIFACT_TEMPLATES/05_SHELL_EXPERIENCE_SPEC.md`
  - `Codex_Orchestrator/ARTIFACT_TEMPLATES/00_HANDOFF_PACKET_TEMPLATE.md`
  - `Codex_Orchestrator/Phase_1_Rebrand_and_Naming_Cleanup/03_BRAND_SYSTEM_SPEC_FILLED.md`
  - `Codex_Orchestrator/Phase_1_Rebrand_and_Naming_Cleanup/04_NAMING_MIGRATION_MATRIX_FILLED.md`
  - `Codex_Orchestrator/Phase_0_Audit_and_Cleanup/02_REFERENCE_IMAGE_FRAMEWORK_FILLED.md`
- Reference image categories used:
  - `TARGET_TOP_BAR`
  - `TARGET_GLASSY_UI`
  - `TARGET_TRANSCRIPT_CHAT`
- Key assumptions:
  - Windows-native quality matters more than novelty
  - The shell stays compact until the operator explicitly expands it
  - The wordmark remains text-only
  - The suggestion rail belongs only to the expanded `Ask` surface

## What Was Produced

- Primary artifact:
  - `Codex_Orchestrator/Phase_2_Design_System_and_Shell_Redesign/05_SHELL_EXPERIENCE_SPEC_FILLED.md`
- Secondary notes:
  - Locked the top capsule structure, expanded sheet behavior, keyboard order, and motion rules
- Decisions locked:
  - `Opencluely` wordmark is pure text on the left
  - profile context is a separate chip
  - session controls stay compact in the capsule
  - `Ask` and `Transcript` are tabs inside the expanded sheet
  - Notes and Prep Deck remain utility surfaces, not top-level navigation

## Open Risks

- Risk: The current reference map still lacks an ideal code-display image.
- Impact: Code-heavy answer surfaces may still need interpretation by the component lead.
- Recommended owner: Design Token and Component Lead

- Risk: The shell can still become too dense if new actions are added directly to the capsule.
- Impact: Readability and discoverability will degrade on smaller screens.
- Recommended owner: Workflow Architect plus UI maintainers

## Blockers

- Blocker: No blocker for shell approval
- What is missing: A canonical code-display reference for later component-level decisions
- Best next action: Approve the shell structure and let the component lead lock token and code-surface rules

## Downstream Handoff

- Next agent(s):
  - Agent 06 - Design Token and Component Lead
  - Agent 07 - Workflow Architect
- What they can trust as stable:
  - Surface hierarchy
  - Live Bar capsule anatomy
  - Expanded `Ask` and `Transcript` split
  - Accessibility and focus behavior
- What they must not reinterpret:
  - the wordmark is text-only
  - the shell is compact-first
  - the suggestion rail appears only in expanded `Ask`
  - utility panels stay secondary
- What still needs approval:
  - no structural shell question remains open

## Verification

- Checklist used:
  - Brand and naming alignment
  - Reference-image alignment
  - Product lifecycle consistency check
  - Shell-to-implementation parity check
- Gaps found:
  - Missing canonical code-display reference
- Ready for approval: Yes
