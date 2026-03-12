# Naming Migration Matrix

## Migration Summary

- Scope:
  - Public product language, shell UI, setup flow, runtime labels, docs, config names, and archive references
- Source surfaces:
  - Legacy product UI, runtime file names, shell labels, README copy, launch scripts, and migration documents
- Target surfaces:
  - Opencluely product UI, implementation docs, seed content, runtime naming, and future OSS-facing terminology

## Rename Matrix

| Current Term | Target Term | Surface Type | Priority | Breaking Risk | Notes |
| --- | --- | --- | --- | --- | --- |
| ParakeetAI Clone | Opencluely | UI/docs/bootstrap | P0 | low | Must disappear from all user-facing entry points |
| Parakeet | Opencluely | UI/docs/domain | P0 | low | Retain only inside historical migration docs |
| LALA | Prep Deck | UI/domain/runtime | P0 | medium | Personal legacy concept must not survive in product language |
| LALA Interview Prep | Prep Deck | UI | P0 | low | Direct shell rename |
| AI Help | Assist | UI | P0 | low | Stronger action label |
| Analyze Screen | Screen | UI | P0 | low | Keep compact in top capsule |
| Chat | Ask | UI | P1 | low | Keeps action framing consistent |
| Template | Brief | UI/docs/config | P0 | medium | Internal APIs may transition more slowly |
| Session Setup | Session Launchpad | UI/docs | P0 | low | New canonical launch surface name |
| Default | Blank Brief | UI/config | P1 | low | Better empty-state semantics |
| Interview Assistant | Interview Loop | seed content | P1 | low | Less narrow, more premium |
| LeetCode Helper | Technical Review | seed content | P1 | low | Better brand tone |
| Sales Assistant | Sales Call | seed content | P1 | low | More concrete usage |
| parakeet log prefix | opencluely log prefix | runtime | P0 | low | Update log file generation |
| `src/lala_manager.py` | `src/prep_deck_manager.py` | code | P0 | medium | Update imports before deleting legacy file |
| `src/ui/lala_panel.py` | `src/ui/prep_deck_panel.py` | code | P0 | medium | Same migration order as manager rename |
| `config/lala_prep.json` | quarantined legacy runtime file | runtime/archive | P0 | high | Contains sensitive personal content; do not auto-migrate into OSS state |

## Blacklist

- terms that must not appear:
  - Parakeet
  - ParakeetAI Clone
  - LALA
  - Clone
  - buddy
  - magic
  - parrot
- terms allowed only in archive docs:
  - Parakeet
  - LALA
  - `parakeet_*.log`
  - `config/lala_prep.json`

## Migration Order

1. Brand-visible surfaces
   - top bar wordmark, launch window, launcher text, README headline, button labels
2. Core user flows
   - prep experience, brief selection, seed data, active shell actions
3. Internal config and docs
   - runtime log prefix, manager names, implementation docs, spec artifacts
4. Archive and legacy references
   - quarantine sensitive runtime files, preserve only migration context in orchestrator docs

## Validation Checklist

- [x] No toxic/personal naming remains in target UX
- [x] Rename order minimizes confusion
- [x] Breaking-risk terms are flagged
