# MASTER RUNBOOK

This runbook is the operational guide for executing the Opencluely rewrite through the agent prompts stored in this folder.

It is designed to answer five things clearly:

1. What gets run first
2. What can run in parallel
3. What must exist before the next wave starts
4. What each agent must hand off
5. How to keep the entire effort disciplined, reviewable, and commit-friendly

## 1. Mission

Transform the current Parakeet AI MVP into Opencluely:

- Windows-first desktop product
- local-first and BYOK
- Groq `whisper-large-v3-turbo` for live transcription
- Gemini restricted to image workflows and answer generation
- premium dark-glass blue/white UI
- clean installer and OSS-ready repository

The current Python/PyQt codebase is a legacy behavior reference, not the intended long-term production base.

## 2. Operator Rules

- Treat this runbook as the top-level execution contract.
- Use the prompt files inside each phase folder as the single source of truth for each agent.
- Use the matching file in `ARTIFACT_TEMPLATES` as the default output shape for each primary deliverable.
- Require every agent to attach `ARTIFACT_TEMPLATES/00_HANDOFF_PACKET_TEMPLATE.md` at handoff time.
- Do not skip phases.
- Do not start downstream agents until upstream artifacts are approved.
- Do not claim a phase is complete without applying `$verification-before-completion`.
- Do not preserve `Parakeet`, `LALA`, personal content, root logs, or hardcoded secrets.
- Do not let commit volume outrun artifact quality.

## 3. Folder Map

- [README.md](C:\Users\Davib\OneDrive\Área de Trabalho\LALA\parakeet_clone\Codex_Orchestrator\README.md): index and reference summary
- [ARTIFACT_TEMPLATES](C:\Users\Davib\OneDrive\Área de Trabalho\LALA\parakeet_clone\Codex_Orchestrator\ARTIFACT_TEMPLATES): output templates and handoff packet model
- [Phase_0_Audit_and_Cleanup](C:\Users\Davib\OneDrive\Área de Trabalho\LALA\parakeet_clone\Codex_Orchestrator\Phase_0_Audit_and_Cleanup): legacy audit and image taxonomy
- [Phase_1_Rebrand_and_Naming_Cleanup](C:\Users\Davib\OneDrive\Área de Trabalho\LALA\parakeet_clone\Codex_Orchestrator\Phase_1_Rebrand_and_Naming_Cleanup): brand and rename system
- [Phase_2_Design_System_and_Shell_Redesign](C:\Users\Davib\OneDrive\Área de Trabalho\LALA\parakeet_clone\Codex_Orchestrator\Phase_2_Design_System_and_Shell_Redesign): shell and component system
- [Phase_3_Feature_Architecture_Refactor](C:\Users\Davib\OneDrive\Área de Trabalho\LALA\parakeet_clone\Codex_Orchestrator\Phase_3_Feature_Architecture_Refactor): lifecycle and Context Vault
- [Phase_4_Transcription_and_Backend_Hardening](C:\Users\Davib\OneDrive\Área de Trabalho\LALA\parakeet_clone\Codex_Orchestrator\Phase_4_Transcription_and_Backend_Hardening): audio and provider orchestration
- [Phase_5_Post_Meeting_Intelligence_Workflows](C:\Users\Davib\OneDrive\Área de Trabalho\LALA\parakeet_clone\Codex_Orchestrator\Phase_5_Post_Meeting_Intelligence_Workflows): debrief intelligence
- [Phase_6_Packaging_Installer_and_OSS_Readiness](C:\Users\Davib\OneDrive\Área de Trabalho\LALA\parakeet_clone\Codex_Orchestrator\Phase_6_Packaging_Installer_and_OSS_Readiness): installer and docs
- [Phase_7_Polish_QA_Docs_and_Launch_Readiness](C:\Users\Davib\OneDrive\Área de Trabalho\LALA\parakeet_clone\Codex_Orchestrator\Phase_7_Polish_QA_Docs_and_Launch_Readiness): QA and release gates

## 4. Reference System

The active image folder is [Imagens_Referência](C:\Users\Davib\OneDrive\Área de Trabalho\LALA\parakeet_clone\Imagens_Referência).

Use these categories consistently:

- `CURRENT_STATE`
- `TARGET_TOP_BAR`
- `TARGET_GLASSY_UI`
- `TARGET_TRANSCRIPT_CHAT`
- `TARGET_POST_MEETING_SUMMARY`
- `TARGET_BUTTONS_AND_CARDS`
- `TARGET_SETUP_FLOW`
- `TARGET_CODE_DISPLAY`
- `BAD_PATTERNS_TO_REMOVE`

If any prompt needs a screenshot and the correct category is still weak or missing, the run must pause and the gap must be documented before design decisions continue.

## 5. Execution Model

The rewrite is organized into phases and waves.

- A phase is a strategic boundary.
- A wave is a batch of agents that may run in parallel once dependencies are satisfied.
- A checkpoint is the approval gate between waves.
- A primary artifact template defines the expected structure of the main output.
- A handoff packet is mandatory at the end of every agent run.

### Phase and Wave Summary

1. Phase 0
   Wave 0A: Legacy Audit Curator
   Wave 0B: Reference Librarian

2. Phase 1
   Wave 1A: Brand System Architect
   Wave 1B: Naming Migration Planner

3. Phase 2
   Wave 2A: Shell Experience Designer
   Wave 2B: Design Token and Component Lead

4. Phase 3
   Wave 3A: Workflow Architect
   Wave 3B: Context Vault Architect

5. Phase 4
   Wave 4A: Audio Pipeline Engineer
   Wave 4B: Provider Orchestration Architect

6. Phase 5
   Wave 5A: Post-Meeting Intelligence Designer

7. Phase 6
   Wave 6A: Installer and Distribution Engineer
   Wave 6B: Documentation and Community Maintainer

8. Phase 7
   Wave 7A: Quality and Reliability Lead

## 6. Exact Run Order

### Phase 0 - Audit and Cleanup

Run first:

1. [01_Legacy_Audit_Curator.md](C:\Users\Davib\OneDrive\Área de Trabalho\LALA\parakeet_clone\Codex_Orchestrator\Phase_0_Audit_and_Cleanup\01_Legacy_Audit_Curator.md)
2. [02_Reference_Librarian.md](C:\Users\Davib\OneDrive\Área de Trabalho\LALA\parakeet_clone\Codex_Orchestrator\Phase_0_Audit_and_Cleanup\02_Reference_Librarian.md)

Checkpoint to exit Phase 0:

- preserve/remove/archive matrix approved
- secret and personal data exposure list approved
- screenshot taxonomy approved
- missing reference gaps explicitly listed
- both artifacts shaped with the Phase 0 templates plus handoff packets

### Phase 1 - Rebrand and Naming Cleanup

Run after Phase 0 approval:

1. [03_Brand_System_Architect.md](C:\Users\Davib\OneDrive\Área de Trabalho\LALA\parakeet_clone\Codex_Orchestrator\Phase_1_Rebrand_and_Naming_Cleanup\03_Brand_System_Architect.md)
2. [04_Naming_Migration_Planner.md](C:\Users\Davib\OneDrive\Área de Trabalho\LALA\parakeet_clone\Codex_Orchestrator\Phase_1_Rebrand_and_Naming_Cleanup\04_Naming_Migration_Planner.md)

Checkpoint to exit Phase 1:

- Opencluely brand system approved
- final replacement for LALA approved
- deprecated term blacklist approved
- rename matrix approved
- both artifacts shaped with the Phase 1 templates plus handoff packets

### Phase 2 - Design System and Shell Redesign

Run after Phase 1 approval:

1. [05_Shell_Experience_Designer.md](C:\Users\Davib\OneDrive\Área de Trabalho\LALA\parakeet_clone\Codex_Orchestrator\Phase_2_Design_System_and_Shell_Redesign\05_Shell_Experience_Designer.md)
2. [06_Design_Token_and_Component_Lead.md](C:\Users\Davib\OneDrive\Área de Trabalho\LALA\parakeet_clone\Codex_Orchestrator\Phase_2_Design_System_and_Shell_Redesign\06_Design_Token_and_Component_Lead.md)

Checkpoint to exit Phase 2:

- shell structure approved
- live bar interaction model approved
- design token system approved
- code display and setup surfaces specified
- both artifacts shaped with the Phase 2 templates plus handoff packets

### Phase 3 - Feature Architecture Refactor

Run after Phase 2 approval:

1. [07_Workflow_Architect.md](C:\Users\Davib\OneDrive\Área de Trabalho\LALA\parakeet_clone\Codex_Orchestrator\Phase_3_Feature_Architecture_Refactor\07_Workflow_Architect.md)
2. [08_Context_Vault_Architect.md](C:\Users\Davib\OneDrive\Área de Trabalho\LALA\parakeet_clone\Codex_Orchestrator\Phase_3_Feature_Architecture_Refactor\08_Context_Vault_Architect.md)

Checkpoint to exit Phase 3:

- Launchpad -> Live Bar -> Debrief lifecycle approved
- Session Setup removal plan approved
- Context Vault taxonomy approved
- migration plan from notes and LALA approved
- both artifacts shaped with the Phase 3 templates plus handoff packets

### Phase 4 - Transcription and Backend Hardening

Run after Phase 3 approval:

1. [09_Audio_Pipeline_Engineer.md](C:\Users\Davib\OneDrive\Área de Trabalho\LALA\parakeet_clone\Codex_Orchestrator\Phase_4_Transcription_and_Backend_Hardening\09_Audio_Pipeline_Engineer.md)
2. [10_Provider_Orchestration_Architect.md](C:\Users\Davib\OneDrive\Área de Trabalho\LALA\parakeet_clone\Codex_Orchestrator\Phase_4_Transcription_and_Backend_Hardening\10_Provider_Orchestration_Architect.md)

Checkpoint to exit Phase 4:

- Windows-first audio capture path approved
- Groq turbo chunking strategy approved
- provider capability matrix approved
- secure key handling policy approved
- both artifacts shaped with the Phase 4 templates plus handoff packets

### Phase 5 - Post-Meeting Intelligence Workflows

Run after Phase 4 approval:

1. [11_Post_Meeting_Intelligence_Designer.md](C:\Users\Davib\OneDrive\Área de Trabalho\LALA\parakeet_clone\Codex_Orchestrator\Phase_5_Post_Meeting_Intelligence_Workflows\11_Post_Meeting_Intelligence_Designer.md)

Checkpoint to exit Phase 5:

- Debrief workspace information architecture approved
- summary schema approved
- transcript-grounded chat behavior approved
- export model approved
- artifact shaped with the Phase 5 template plus handoff packet

### Phase 6 - Packaging, Installer, and OSS Readiness

Run after Phase 5 approval:

1. [12_Installer_and_Distribution_Engineer.md](C:\Users\Davib\OneDrive\Área de Trabalho\LALA\parakeet_clone\Codex_Orchestrator\Phase_6_Packaging_Installer_and_OSS_Readiness\12_Installer_and_Distribution_Engineer.md)
2. [14_Documentation_and_Community_Maintainer.md](C:\Users\Davib\OneDrive\Área de Trabalho\LALA\parakeet_clone\Codex_Orchestrator\Phase_6_Packaging_Installer_and_OSS_Readiness\14_Documentation_and_Community_Maintainer.md)

Checkpoint to exit Phase 6:

- installer blueprint approved
- release artifact matrix approved
- OSS documentation map approved
- security and privacy doc requirements approved
- both artifacts shaped with the Phase 6 templates plus handoff packets

### Phase 7 - Polish, QA, Docs, and Launch Readiness

Run last:

1. [13_Quality_and_Reliability_Lead.md](C:\Users\Davib\OneDrive\Área de Trabalho\LALA\parakeet_clone\Codex_Orchestrator\Phase_7_Polish_QA_Docs_and_Launch_Readiness\13_Quality_and_Reliability_Lead.md)

Checkpoint to exit Phase 7:

- QA matrix approved
- release-critical acceptance scenarios approved
- launch blockers list approved
- validation gate signed off
- artifact shaped with the Phase 7 template plus handoff packet

## 7. Parallelism Rules

Use parallel execution only when outputs do not conflict.

Safe parallel patterns:

- Phase 0 Agent 01 can start before Agent 02, but Agent 02 should consume the audit once it exists.
- In later phases, a downstream agent may read an upstream draft, but cannot finalize until the upstream artifact is approved.

Do not run these in parallel as finalizing agents:

- Brand System Architect and Naming Migration Planner without a draft brand spec
- Shell Experience Designer and Workflow Architect as independent final authorities
- Audio Pipeline Engineer and Provider Orchestration Architect without a shared approved workflow model

## 8. Handoff Packet

Every agent handoff must include exactly this structure:

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
Needs Approval:
- ...
```

If an agent output changes a global constraint, the handoff must also include:

```text
Constraint Change:
Old:
New:
Reason:
Blast Radius:
```

The canonical source for this structure is [00_HANDOFF_PACKET_TEMPLATE.md](C:\Users\Davib\OneDrive\Área de Trabalho\LALA\parakeet_clone\Codex_Orchestrator\ARTIFACT_TEMPLATES\00_HANDOFF_PACKET_TEMPLATE.md).

## 9. Required Artifacts By Phase

### Phase 0 artifacts

- legacy audit matrix
- secret and personal data exposure list
- screenshot taxonomy
- reference gaps list

### Phase 1 artifacts

- brand system
- naming rules
- rename matrix
- deprecated terms blacklist

### Phase 2 artifacts

- shell spec
- live bar spec
- token and component system
- accessibility notes

### Phase 3 artifacts

- lifecycle flow map
- screen map
- Context Vault model
- legacy migration notes

### Phase 4 artifacts

- audio pipeline spec
- latency and fallback matrix
- provider contract matrix
- key handling policy

### Phase 5 artifacts

- debrief workspace spec
- summary schema
- grounded chat rules
- export model

### Phase 6 artifacts

- installer blueprint
- release artifact matrix
- README and OSS docs map
- security and privacy doc requirements

### Phase 7 artifacts

- QA matrix
- release gate checklist
- visual validation checklist
- launch blocker registry

### Default template mapping

- Phase 0: `01_LEGACY_AUDIT_MATRIX.md`, `02_REFERENCE_IMAGE_FRAMEWORK.md`
- Phase 1: `03_BRAND_SYSTEM_SPEC.md`, `04_NAMING_MIGRATION_MATRIX.md`
- Phase 2: `05_SHELL_EXPERIENCE_SPEC.md`, `06_DESIGN_TOKEN_AND_COMPONENT_SPEC.md`
- Phase 3: `07_WORKFLOW_ARCHITECTURE_SPEC.md`, `08_CONTEXT_VAULT_SPEC.md`
- Phase 4: `09_AUDIO_PIPELINE_SPEC.md`, `10_PROVIDER_ORCHESTRATION_MATRIX.md`
- Phase 5: `11_POST_MEETING_INTELLIGENCE_SPEC.md`
- Phase 6: `12_INSTALLER_BLUEPRINT.md`, `14_OSS_READINESS_PACK.md`
- Phase 7: `13_QA_MATRIX.md`
- Every phase: `00_HANDOFF_PACKET_TEMPLATE.md`

## 10. Approval Gates

The operator should approve the following before implementation begins:

- Phase 0 artifact bundle
- Phase 1 brand and naming bundle
- Phase 2 shell and design system bundle
- Phase 3 workflow and Context Vault bundle
- Phase 4 audio and provider bundle
- Phase 5 debrief bundle
- Phase 6 release and OSS bundle
- Phase 7 QA gate bundle

Implementation should not start until the first six bundles are stable enough to prevent architectural thrash.

## 11. Recommended Daily Cadence

For fast progress without chaos:

1. Start the day by choosing the current active phase.
2. Run or review no more than one wave at a time.
3. Approve or reject outputs the same day.
4. Convert approved artifacts into implementation tickets before opening the next wave.
5. Only then begin execution work.

For commit discipline later:

- one commit per real artifact-sized implementation unit
- no empty commits
- no “checkpoint” spam
- verify before marking done

## 12. Git and Authorship Readiness

Before official execution starts, confirm:

- `git config user.name` is your intended public name
- `git config user.email` is `davi.bonetto100@gmail.com`
- `.gitignore` excludes logs, caches, secrets, and local app data
- no personal JSON data or root logs are about to be committed

This matters because the current repository still has no commit history and should not start public history in a dirty state.

## 13. Run Procedure For Each Agent

Use this operator loop:

1. Open the relevant prompt file.
2. Attach or reference the required upstream artifacts.
3. Paste the prompt into the execution agent.
4. Wait for structured output.
5. Review against the phase checkpoint.
6. Approve, request revision, or block.
7. Archive the approved artifact in your execution workspace.

If an agent returns vague output:

- reject it
- restate the missing deliverable
- rerun with stricter scope

## 14. Failure Protocol

If a phase stalls:

- stop opening new downstream agents
- document the blocker
- identify whether the blocker is missing context, missing reference images, unresolved naming, or provider uncertainty
- resolve the blocker at the earliest phase that owns it

Never patch over upstream ambiguity by inventing downstream assumptions.

## 15. Definition of Operational Success

This runbook succeeds when:

- every phase has an approved artifact bundle
- every agent has a clean handoff trail
- no later implementation step needs to invent product, architecture, naming, or packaging decisions
- the Opencluely rewrite can begin with confidence and without context loss

## 16. Final Checklist

- Phase order respected
- Dependencies respected
- Screenshot categories respected
- No legacy naming preserved
- Groq transcription rule preserved
- Gemini restriction preserved
- Windows-first rule preserved
- MIT assumption preserved unless changed explicitly
- Verification rule enforced before completion claims
