# Shell Experience Spec

## Shell Summary

- Primary surfaces:
  - Session Launchpad
  - Live Bar capsule
  - Expanded live sheet with `Ask` and `Transcript`
  - Session Notes utility panel
  - Prep Deck floating utility panel
- Window model:
  - Always-on-top floating shell with a compact collapsed state and a glassy expanded sheet below the capsule
- Navigation model:
  - `Launchpad -> Live Bar -> Debrief`
  - Launchpad is the entry surface, Live Bar is the persistent live control surface, Debrief is the post-session destination

## Surface Breakdown

| Surface | Purpose | Always Visible | Key Interactions | Notes |
| --- | --- | --- | --- | --- |
| Session Launchpad | Configure the next live session | no | choose brief, language, context, launch | Must feel visually related to the shell but remain a separate flow |
| Live Bar capsule | Persistent command surface during a session | yes | listen/stop, expand/collapse, open notes, open Prep Deck, overflow, close | Compact-first, premium, and calm |
| Expanded live sheet | Main live working area | no | switch between `Ask` and `Transcript`, use suggestions, read outputs, type prompts | Opens directly under the capsule |
| Ask surface | Grounded assistance workspace | no | Assist, What should I say next, Follow-up, Recap, Screen, composer send | Evidence-informed suggestions, not generic chat chrome |
| Transcript surface | Review live transcript | no | read, clear, load context | Transcript-led, low-noise layout |
| Session Notes | Persistent scratchpad | no | select note, edit, rename, delete, hide | Utility surface only, never primary navigation |
| Prep Deck | Curated live-prep material | no | open floating panel, browse items, edit items | Secondary support panel, not part of the top-level shell hierarchy |

## Live Bar Anatomy

- Left zone:
  - `Opencluely` wordmark only
  - Inter Semibold
  - tracking `-0.07`
  - no icon, mascot, avatar, or chip attached to the wordmark
- Session zone:
  - separate session chip fed by `brief_name` or `profile_name`
  - optional live indicator and timer appear beside it while recording
- Control zone:
  - `Listen` / `Stop`
  - `Open` / `Hide`
  - grouped inside a segmented capsule block
- Utility zone:
  - `Notes`
  - `Prep Deck`
  - overflow
  - close
- Expanded sheet:
  - header strip with `Ask` and `Transcript`
  - active tab styling must stay quiet and legible
- Suggestion rail:
  - visible only on `Ask`
  - order:
    - `Assist`
    - `What should I say next?`
    - `Follow-up`
    - `Recap`
    - `Screen`
- Composer behavior:
  - one-line field anchored at the bottom of `Ask`
  - circular send CTA on the right
  - prompt tone stays operational, not playful

## State Model

| State | Trigger | Visual Change | User Action |
| --- | --- | --- | --- |
| idle | shell opened | capsule calm, sheet hidden, no pulse | expand or start listening |
| listening | microphone active | live badge visible, timer visible, `Listen` becomes `Stop` | continue or stop capture |
| expanded.ask | user opens the sheet into Ask | suggestion rail, response stack, composer appear | request guidance or type prompt |
| expanded.transcript | user switches to Transcript | transcript surface becomes primary | review evidence, clear, or load context |
| thinking | Assist request running | Assist becomes `Working...`, rail actions and send CTA disable | wait for grounded output |
| scanning | Screen request running | Screen becomes `Scanning...`, sheet stays open | wait for returned result |
| notes-open | Notes toggled | notes utility panel appears below the sheet | edit notes or hide |
| prep-open | Prep Deck toggled | floating panel opens centered on screen | browse or edit deck items |
| error | provider or runtime failure | stable inline error card, no shake animation | retry or continue manually |

## Motion Rules

- Entry:
  - shell enters with soft opacity and slight scale only
  - no bounce
- Hover:
  - use border intensity and panel brightness changes, not positional jumps
- Focus:
  - visible blue focus treatment on all actionable controls
  - focus must remain legible on dark glass
- Expand/collapse:
  - calm reveal of the sheet below the capsule
  - no large travel distances
- Error:
  - plain state swap and explanatory copy
  - never shake or flash

## Desktop-Native Rules

- Hit targets:
  - capsule controls: 36-40 px minimum
  - expanded surfaces: 40-44 px minimum
- Dragging:
  - drag only from non-interactive space inside the top capsule
  - never drag from buttons, inputs, or dropdowns
- Window behavior:
  - always on top
  - compact-first
  - expands downward rather than becoming a large floating dashboard immediately
- Glass treatment:
  - simulated material only
  - dark navy body
  - frosted blue border
  - restrained shadow
  - readability wins over blur spectacle
- Hierarchy:
  - capsule first
  - sheet header second
  - suggestion rail third
  - transcript evidence fourth
  - generated response cards fifth
  - utilities last

## Accessibility And Focus Behavior

- Icon-only controls must expose tooltip and accessible name
- Wordmark is not in the tab order
- Keyboard order:
  - session chip
  - listen/stop
  - expand/collapse
  - `Ask`
  - `Transcript`
  - suggestion rail
  - composer
  - notes
  - Prep Deck
  - overflow
  - close
- `Escape` behavior:
  - first closes Prep Deck if open
  - then hides Notes if open
  - then collapses the expanded sheet
  - does not abruptly end the session

## Open Questions

- none
