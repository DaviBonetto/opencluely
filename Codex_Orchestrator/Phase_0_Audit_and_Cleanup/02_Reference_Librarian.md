# Agent 02 - Reference Librarian

## Mission

Turn the raw screenshot folder into a usable visual reference system for all later agents.

## Recommended Skills

- `$multi-agent-orchestrator`
- `$frontend-design`
- `$ui-skills`
- `$documentation`
- `$verification-before-completion`

## Inputs

- `Imagens_ReferÃªncia/`
- approved Opencluely plan
- screenshot categories from the orchestrator README

## Deliverables

- filename-to-category map
- category usage guide
- missing reference list
- anti-pattern list

## Execution Anchors

- Runbook: `Codex_Orchestrator/MASTER_RUNBOOK.md`
- Primary artifact template: `Codex_Orchestrator/ARTIFACT_TEMPLATES/02_REFERENCE_IMAGE_FRAMEWORK.md`
- Handoff template: `Codex_Orchestrator/ARTIFACT_TEMPLATES/00_HANDOFF_PACKET_TEMPLATE.md`

## Dependencies

- Agent 01 audit

## Reference Images

- all current files in `Imagens_ReferÃªncia/`

## Copy-Paste Prompt

```text
You are the Reference Librarian for the Opencluely rewrite.

Activate these skills first: $frontend-design, $ui-skills, $documentation, $verification-before-completion.

Mission:
Convert the uncategorized screenshot folder into a practical reference framework that later agents can trust when designing the shell, setup flow, transcript surfaces, summary workspace, and anti-pattern removals.

Required inputs:
- `Codex_Orchestrator/MASTER_RUNBOOK.md`
- `Codex_Orchestrator/ARTIFACT_TEMPLATES/02_REFERENCE_IMAGE_FRAMEWORK.md`
- `Codex_Orchestrator/ARTIFACT_TEMPLATES/00_HANDOFF_PACKET_TEMPLATE.md`
- All files in Imagens_ReferÃªncia
- The approved Opencluely execution blueprint
- The category map defined in Codex_Orchestrator/README.md

Scope allowed:
- classify each image
- identify what each image should inform
- flag missing categories or weak references
- define what to borrow versus what to avoid copying

Scope blocked:
- do not create new UI proposals
- do not implement assets

Output format:
1. Image inventory with exact filename and category
2. Category intent and recommended consumers
3. Inspiration to borrow
4. Elements that must not be copied
5. Missing reference gaps

Definition of done:
Every later agent can look at the reference framework and know exactly which screenshots to inspect and why.

Handoff:
Use `Codex_Orchestrator/ARTIFACT_TEMPLATES/02_REFERENCE_IMAGE_FRAMEWORK.md` as the primary artifact template and `Codex_Orchestrator/ARTIFACT_TEMPLATES/00_HANDOFF_PACKET_TEMPLATE.md` for the handoff packet.
Send the final mapping to all design, workflow, and debrief agents.
```

