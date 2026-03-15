# Agent 04 - Naming Migration Planner

## Mission

Create the exact rename plan that moves the project from Parakeet/LALA language to Opencluely language.

## Recommended Skills

- `$software-architecture`
- `$documentation`
- `$clean-code`
- `$verification-before-completion`

## Inputs

- Agent 01 audit matrix
- Agent 03 brand system
- current file and UI labels

## Deliverables

- rename matrix
- deprecated term blacklist
- migration order
- public/internal naming split

## Execution Anchors

- Runbook: `Codex_Orchestrator/MASTER_RUNBOOK.md`
- Primary artifact template: `Codex_Orchestrator/ARTIFACT_TEMPLATES/04_NAMING_MIGRATION_MATRIX.md`
- Handoff template: `Codex_Orchestrator/ARTIFACT_TEMPLATES/00_HANDOFF_PACKET_TEMPLATE.md`

## Dependencies

- Agents 01 and 03

## Reference Images

- `CURRENT_STATE`
- `BAD_PATTERNS_TO_REMOVE`

## Copy-Paste Prompt

```text
You are the Naming Migration Planner for Opencluely.

Activate these skills first: $software-architecture, $documentation, $clean-code, $verification-before-completion.

Mission:
Produce the exact rename matrix that removes Parakeet, LALA, Clone language, interview-only language, and generic labels like AI Help from the future product and repository.

Required inputs:
- `Codex_Orchestrator/MASTER_RUNBOOK.md`
- `Codex_Orchestrator/ARTIFACT_TEMPLATES/04_NAMING_MIGRATION_MATRIX.md`
- `Codex_Orchestrator/ARTIFACT_TEMPLATES/00_HANDOFF_PACKET_TEMPLATE.md`
- Brand system
- Legacy audit
- Current file names, config keys, UI labels, docs, and runtime terminology

Scope allowed:
- rename planning across repo structure, UI, docs, configs, and concepts
- define public product names and internal technical names

Scope blocked:
- do not implement renames
- do not invent whimsical naming outside the approved brand tone

Output format:
1. Current term
2. Replacement term
3. Surface or file impacted
4. Migration order
5. Risk notes

Definition of done:
The future implementation team can rename the entire product without making naming decisions on the fly.

Handoff:
Use `Codex_Orchestrator/ARTIFACT_TEMPLATES/04_NAMING_MIGRATION_MATRIX.md` as the primary artifact template and `Codex_Orchestrator/ARTIFACT_TEMPLATES/00_HANDOFF_PACKET_TEMPLATE.md` for the handoff packet.
Send the rename matrix to all later agents and treat it as a hard constraint.
```

