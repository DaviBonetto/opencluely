# Design Token And Component Spec

## Token Layers

- color
- typography
- spacing
- radius
- shadow
- motion

## Color Tokens

| Token | Value | Usage |
| --- | --- | --- |
| color.primary.500 | #4F86F7 | primary CTA, focus, active controls |
| color.base.0 | #F8F8FF | primary text on dark surfaces |
| color.shell.950 | #08111F | app shell background |
| color.panel.900 | #0D1527 | cards, inputs, floating panes |
| color.panel.850 | #101B31 | elevated panels and button surfaces |
| color.panel.800 | #162544 | hover state for elevated surfaces |
| color.text.muted | #9FB0CC | labels and helper text |
| color.state.success | #4ADE80 | live and ready signals only |
| color.border.subtle | rgba(130, 166, 249, 0.16) | default structural border |
| color.border.focus | rgba(79, 134, 247, 0.34) | focus and selected border |

## Typography Tokens

| Token | Value | Usage |
| --- | --- | --- |
| font.family.ui | Inter | all core UI text |
| font.family.wordmark | Inter | Opencluely wordmark |
| font.weight.regular | 400 | body copy |
| font.weight.medium | 500 | labels |
| font.weight.semibold | 600 | wordmark, titles, primary emphasis |
| font.size.label | 12px | metadata and compact labels |
| font.size.body | 13px | default shell text |
| font.size.body.lg | 14px | setup flow controls |
| font.size.title | 20-24px | setup titles and major headings |
| font.tracking.wordmark | -0.07 | Opencluely wordmark only |

## Core Components

| Component | Variants | States | Accessibility Notes |
| --- | --- | --- | --- |
| action pill | primary/secondary | default/hover/focus/disabled/loading | minimum 30 px height, visible focus ring |
| icon button | utility/danger | default/hover/focus/pressed | tooltip required when icon-only |
| top capsule | compact/expanded | idle/listening/error | drag handle area must remain predictable |
| panel card | shell/setup/response | default/hover/selected | border contrast must stay readable on dark surfaces |
| text input | single-line/multiline | default/hover/focus/error | placeholder contrast cannot fall below helper-text readability |
| combo box | default | default/hover/focus/open | keyboard navigation required |
| response card | assist/screen | default/loading/error | preserve reading rhythm for long-form answers |
| floating utility panel | notes/prep | hidden/open/active | open state must not trap unrelated shell focus |

## Special Surfaces

- transcript rows:
  - transparent background inside the content panel
  - muted text tone for passive history, brighter tone for fresh live lines
- code blocks:
  - use mono font
  - clear inset background on dark navy panel
  - strong spacing between prose and code
  - no neon syntax theme that breaks the calm shell
- summary cards:
  - same radius family as response cards
  - stronger title hierarchy than transcript rows
- setup panels:
  - more generous spacing and larger targets than the live bar

## State And Accessibility Rules

- Hover should change elevation or border intensity, not jump position dramatically.
- Focus must be keyboard-visible on all actionable controls.
- Loading labels should say what is happening: `Thinking...`, `Scanning...`.
- Empty states should be brief and operational.
- Error states should explain the failure plainly and support retry.
- Icon-only controls require descriptive tooltips.
- Green is reserved for live or healthy system states, not generic success celebration.

## Code Display Rules

- Use monospace with 12-14 px body size.
- Keep code blocks visually inset from prose cards with their own dark surface.
- Preserve horizontal padding so copied code is legible and unclipped.
- Use restrained syntax emphasis if later added; readability outranks decoration.
- Complexity summaries and reasoning text should sit above or below code, never mixed into the same visual block.

## Reuse Guidance

- Reuse the same color and radius tokens across Launchpad, Live Bar, Notes, and Prep Deck.
- Do not invent a second accent color family.
- Treat the shell as the reference implementation for dark-surface behavior.
- Any new component should map back to an existing token layer before new values are introduced.

## Implementation Notes

- CSS variable naming:
  - `--oc-color-*`, `--oc-font-*`, `--oc-radius-*`, `--oc-shadow-*`, `--oc-motion-*`
- token export expectations:
  - centralize values in code so PyQt surfaces do not drift
- dependency constraints:
  - keep implementation light and desktop-friendly; avoid decorative animation frameworks
