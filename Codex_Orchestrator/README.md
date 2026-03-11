# Codex Orchestrator

This folder packages the approved Opencluely execution plan into phase folders and copy-paste-ready agent prompts.

## Goal

Use these prompts to run a disciplined multi-agent rewrite from the current Parakeet AI MVP into Opencluely:

- Windows-first desktop product
- local-first and BYOK
- Groq `whisper-large-v3-turbo` for live transcription
- Gemini only for image workflows and answer generation
- premium dark-glass + blue/white UI
- clean OSS-ready repository and installer

## Phase Folders

- `Phase_0_Audit_and_Cleanup`
- `Phase_1_Rebrand_and_Naming_Cleanup`
- `Phase_2_Design_System_and_Shell_Redesign`
- `Phase_3_Feature_Architecture_Refactor`
- `Phase_4_Transcription_and_Backend_Hardening`
- `Phase_5_Post_Meeting_Intelligence_Workflows`
- `Phase_6_Packaging_Installer_and_OSS_Readiness`
- `Phase_7_Polish_QA_Docs_and_Launch_Readiness`
- `ARTIFACT_TEMPLATES`

## Artifact Templates

Use `ARTIFACT_TEMPLATES` to keep every agent output in a stable shape before implementation starts.

- every agent should use one primary template
- every agent should also emit a handoff packet with `00_HANDOFF_PACKET_TEMPLATE.md`
- the runbook and prompts reference the matching template for each agent
- if a section does not apply, mark it `N/A` instead of deleting it

## Reference Image Categories

Use the uncategorized files in `Imagens_Referência` with this mapping:

- `CURRENT_STATE`: `Captura de tela 2026-03-10 164320.png`
- `TARGET_TOP_BAR`: `155827.png`, `160917.png`, `162030.png`
- `TARGET_GLASSY_UI`: `155447.png`, `155827.png`, `160917.png`
- `TARGET_TRANSCRIPT_CHAT`: `160917.png`, `162030.png`
- `TARGET_POST_MEETING_SUMMARY`: `161952.png`
- `TARGET_BUTTONS_AND_CARDS`: `154759.png`, `155447.png`
- `TARGET_SETUP_FLOW`: `155108.png`, `155559.png`
- `TARGET_CODE_DISPLAY`: currently missing a clean canonical file; the Reference Librarian must flag the gap
- `BAD_PATTERNS_TO_REMOVE`: `164320.png` plus fresh captures of legacy Session Setup and legacy LALA surfaces

## Shared Rules For Every Agent

- Work only inside the assigned phase and scope.
- Preserve useful legacy behavior, but do not preserve Parakeet, LALA, personal data, or messy repository habits.
- Treat the current Python/PyQt app as a behavior reference, not the future production base.
- Always reference the approved product direction: Opencluely, Windows-first, MIT, local-first, premium shell, BYOK.
- Call out blockers early instead of silently guessing.
- Before claiming completion, apply `$verification-before-completion`.

## Suggested Global Output Contract

Every agent should report:

```text
Agent:
Phase:
Status:
Completed:
- ...
Next:
- ...
Blockers:
- ...
Artifacts:
- ...
```

Then attach:

- the primary artifact built from the matching template in `ARTIFACT_TEMPLATES`
- the handoff packet built from `ARTIFACT_TEMPLATES/00_HANDOFF_PACKET_TEMPLATE.md`

## Agent Count

This orchestrator ships 14 specialized prompts:

- 2 prompts in Phase 0
- 2 prompts in Phase 1
- 2 prompts in Phase 2
- 2 prompts in Phase 3
- 2 prompts in Phase 4
- 1 prompt in Phase 5
- 2 prompts in Phase 6
- 1 prompt in Phase 7

## Recommended Run Order

1. Finish both Phase 0 prompts.
2. Run Phase 1 after Phase 0 artifacts exist.
3. Run Phase 2 after the brand and rename matrix are approved.
4. Run Phases 3-5 in sequence, with limited parallelism only when dependencies are satisfied.
5. Run Phases 6-7 only after product, architecture, and debrief specs are stable.
