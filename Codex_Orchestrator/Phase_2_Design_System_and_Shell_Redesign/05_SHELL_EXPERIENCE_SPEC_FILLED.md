# Shell Experience Spec

## Shell Summary

- Primary surfaces:
  - Session Launchpad
  - Live Bar
  - Transcript and response stack
  - Notes panel
  - Prep Deck panel
- Window model:
  - Always-on-top floating shell with expandable content region and independent supporting panels
- Navigation model:
  - Launchpad enters the live session, then the live bar becomes the persistent control surface

## Surface Breakdown

| Surface | Purpose | Always Visible | Key Interactions | Notes |
| --- | --- | --- | --- | --- |
| Session Launchpad | Configure the next live session | no | choose brief, language, context, launch | Entry point only |
| Live Bar | Persistent command capsule during a session | yes | record, assist, screen scan, ask, open notes, open Prep Deck | Premium compact shell |
| Transcript region | Show live captured text | no | expand, read, clear | Must stay readable at small heights |
| Response stack | Show Assist and Screen output cards | no | scroll, copy, compare | Cards sit below transcript |
| Notes panel | Quick persistent scratchpad | no | open, edit, hide | Utility panel, not primary nav |
| Prep Deck panel | Curated pre-session material | no | open, reorder, edit, complete | Independent floating surface |

## Live Bar Anatomy

- Left zone:
  - Opencluely wordmark only
  - recording indicator
  - microphone control
- Center zone:
  - primary action pills: `Assist`, `Screen`, `Ask`
  - these are the behavioral center of gravity
- Right zone:
  - clear transcript
  - notes
  - Prep Deck
  - timer
  - close
- Secondary rail:
  - expanded transcript, response cards, and chat composer
- Composer behavior:
  - hidden when collapsed
  - one-line prompt field with immediate send affordance
  - prompt tone must stay operational, not conversationally cute

## State Model

| State | Trigger | Visual Change | User Action |
| --- | --- | --- | --- |
| idle | shell opened | capsule calm, no pulse | start capture or expand shell |
| listening | microphone active | red live indicator, timer running | continue or stop capture |
| thinking | Assist running | primary action disabled, label reflects work | wait or read prior cards |
| scanning | Screen analysis running | Screen action disabled, transcript placeholder updates | wait for returned card |
| expanded | user opens content | transcript and cards appear | ask follow-up or review output |
| notes-open | notes toggled | notes panel expands below shell | type or collapse |
| prep-open | Prep Deck toggled | floating panel appears centered | review or edit prompts |
| error | provider failure | inline copy explains failure without theatrics | retry or continue manually |

## Motion Rules

- entry:
  - shell appears without bounce; soft opacity and scale only
- hover:
  - buttons lift subtly through border intensity and panel brightness, not large movement
- focus:
  - focus states use blue outline and contrast shift, never glow spam
- error:
  - no shake animation; use clear state swap and stable messaging

## Desktop-Native Rules

- hit targets:
  - minimum 30 px in live bar, 40 px in launch surfaces
- window behavior:
  - drag only from the top capsule
  - support compact always-on-top behavior without stealing focus aggressively
- blur limits:
  - use restrained glass treatment; readability wins over spectacle
- always-on-top behavior:
  - shell stays available during other workflows but must not feel invasive

## Open Questions

- question:
  - Should future versions add a contextual suggestion rail beneath the main action pills, or keep the current shell density fixed for focus?
