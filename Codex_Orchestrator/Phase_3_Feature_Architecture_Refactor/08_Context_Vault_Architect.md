# Agent 08 - Context Vault Architect

## Mission

Unify notes, files, snippets, and legacy LALA content into one product-grade context system.

## Recommended Skills

- `$software-architecture`
- `$database-design`
- `$file-uploads`
- `$documentation`
- `$verification-before-completion`

## Inputs

- workflow map
- legacy notes and LALA findings
- brand naming rules

## Deliverables

- Context Vault schema
- item type rules
- pinning and retrieval model
- migration notes from notes and LALA

## Execution Anchors

- Runbook: `Codex_Orchestrator/MASTER_RUNBOOK.md`
- Primary artifact template: `Codex_Orchestrator/ARTIFACT_TEMPLATES/08_CONTEXT_VAULT_SPEC.md`
- Handoff template: `Codex_Orchestrator/ARTIFACT_TEMPLATES/00_HANDOFF_PACKET_TEMPLATE.md`

## Dependencies

- Agents 01, 04, and 07

## Reference Images

- `TARGET_TRANSCRIPT_CHAT`
- `TARGET_BUTTONS_AND_CARDS`

## Copy-Paste Prompt

```text
You are the Context Vault Architect for Opencluely.

Activate these skills first: $software-architecture, $database-design, $file-uploads, $documentation, $verification-before-completion.

Mission:
Create the Context Vault model that replaces notes plus LALA with a single reusable system for meeting knowledge.

Required inputs:
- `Codex_Orchestrator/MASTER_RUNBOOK.md`
- `Codex_Orchestrator/ARTIFACT_TEMPLATES/08_CONTEXT_VAULT_SPEC.md`
- `Codex_Orchestrator/ARTIFACT_TEMPLATES/00_HANDOFF_PACKET_TEMPLATE.md`
- Workflow architecture
- Legacy note data and legacy LALA behavior
- Approved naming rules

Scope allowed:
- define vault item types, metadata, pinning, session linking, retrieval, and migration boundaries
- support files, code snippets, text snippets, structured data, and pinned session context

Scope blocked:
- do not preserve the LALA name or its personal-school framing
- do not build embeddings or advanced retrieval beyond what the rewrite needs now

Output format:
1. Vault item taxonomy
2. Session linking model
3. Retrieval behavior during live assist
4. Migration from notes and LALA
5. UX labels and empty states

Definition of done:
The team can build a single context system without keeping fragmented legacy surfaces alive.

Handoff:
Use `Codex_Orchestrator/ARTIFACT_TEMPLATES/08_CONTEXT_VAULT_SPEC.md` as the primary artifact template and `Codex_Orchestrator/ARTIFACT_TEMPLATES/00_HANDOFF_PACKET_TEMPLATE.md` for the handoff packet.
Send the vault spec to the provider, debrief, and installer-facing agents.
```

