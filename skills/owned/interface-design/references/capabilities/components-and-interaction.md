# Components And Interaction

Use this module when selecting, composing, or reviewing interactive building blocks.

## Component Choice

Choose the control that matches the behavior:

- icon button for familiar compact tool actions, with accessible name and tooltip when needed;
- checkbox or switch for independent binary state;
- segmented control for a small mutually exclusive mode set;
- select or menu for a longer option set;
- slider, stepper, or numeric input for bounded numeric values;
- tabs for sibling views whose state should remain in context;
- table for comparable records and repeated actions;
- list for scan-first content with variable detail;
- card only for a genuinely independent repeated item;
- modal for focused interruption, not routine navigation or dense workflows.

Consult `assets/patterns/component-patterns.json` for anatomy and required states.

## State Matrix

For each interactive component, cover applicable states:

1. default;
2. hover where a fine pointer exists;
3. focus-visible;
4. active or pressed;
5. selected or expanded;
6. disabled;
7. loading or pending;
8. empty, error, success, or stale data.

State changes must not resize the component or shift nearby layout. Preserve labels and context during loading. Use skeletons only when the final geometry is known; avoid a spinner flash for work that resolves immediately.

## Forms

- Keep visible labels for inputs that need persistent meaning.
- Place helper and error text without moving adjacent fields unexpectedly.
- Validate at a useful time, preserve user input, focus the first actionable error, and summarize multi-field failures when necessary.
- Distinguish required, optional, disabled, read-only, and unavailable.
- Make destructive actions specific, separated from primary actions, and recoverable where possible.

## Navigation And Overlays

Navigation communicates location, hierarchy, and available scope. Keep current location visible and mobile collapse predictable. Modals trap focus, label themselves, restore focus, close by an explicit control, and handle escape only when safe. Popovers and tooltips work for keyboard and pointer users and never contain essential content that cannot be reached otherwise.

## Accessibility Baseline

Use semantic HTML first. Provide accessible names, keyboard order, visible focus, adequate target size, contrast, status announcements, reduced motion, and meaningful alt text. Test zoom and text expansion. Do not hide an unavailable action without explaining the state when that action is important to the workflow.
