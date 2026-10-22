# Reference-led frontend refresh

## References consulted

Read the user's [Developer Resource Library](https://app.notion.com/p/47e1714cc0c8461da4aaae84d9ac0b05) and queried all UI Components, Design Inspiration, Creative Assets, Data Visualization, and icon-related entries. The query returned 31 entries with no remaining page of results. Notion was read only.

- [shadcn/ui — Core / Adopt](https://app.notion.com/p/3bf7001ad23a8131a4b4df2fe036794b): local composable components, clear hierarchy, restrained surfaces. Consulted its official [Command](https://ui.shadcn.com/docs/components/command), [Skeleton](https://ui.shadcn.com/docs/components/skeleton), and [Empty](https://ui.shadcn.com/docs/components/empty) references. Implementations here use existing React and native dialog primitives; they are inspired by these patterns, not installed shadcn registry components.
- [Origin UI](https://app.notion.com/p/3bf7001ad23a810fb4a6d5d1cdab0e1b): the saved reference favors reusable dashboard and form patterns. Its current website presents OriginKit as an animated component library; that distinction was considered, rather than treating the old description as current API documentation.
- [UI Guideline](https://app.notion.com/p/3bf7001ad23a8176a4dfe5d98beff65f): established component conventions and consistent controls. Consulted the [official overview](https://www.uiguideline.com/).
- [Kenney Assets](https://app.notion.com/p/3bf7001ad23a811da33ccf5f94104cad) was the icon-related asset row returned. It describes game/prototype assets; no dedicated product icon library was found in this table. Existing Lucide icons remain consistent, with a book/check brand mark, labeled status feedback, and contextual icons.

## Applied design

Geist is bundled locally with the app, so rendering does not require a font CDN. A blue/navy and neutral light palette, larger labels and table text, tabular numerals, consistent controls, and clearer hover/focus treatment apply across all six pages. Shared components carry skeleton, empty, error, and success states. Reduced-motion preferences disable animation.

The sidebar groups navigation beneath an organization context. A page finder opens with the button or Ctrl/Cmd+K; search filters page destinations, Enter selects the first, Tab selects another, and Escape closes the native dialog. Breadcrumbs and browser titles follow the route.

The dashboard groups six live metrics into one surface, calculates the allowed percentage and decision distribution from database totals, displays initials alongside audit identities, and offers a direct evaluation shortcut. No invented trend or security score is shown. The refresh leaves existing PostgreSQL authorization and API behavior intact.

## Verification

Evidence for this refresh is separate from the academic submission's original screenshots and test outputs, in `docs/evidence/ui-refresh/`. Earlier submission evidence remains a record of its own verification run.

The production TypeScript/Vite build and connected Playwright suite are executed for this change. New browser coverage exercises page search, keyboard navigation, empty search results, focus restoration, mobile layout on all six routes, and employee-dialog operation. Existing connected tests retain registration → assignment → grant → ALLOW → revoke → DENY → historical audit visibility and pending-evaluation identity protection.

Executed results: production TypeScript/Vite build passed; all **5 Playwright tests passed** (41.6 seconds). A separate live-browser check verified audit Apply/Clear behavior and the page finder after the final layout adjustment. Desktop screenshots cover all six pages; mobile and page-finder screenshots are included. No browser page errors occurred during the six-page screenshot capture. The first test run exposed the native-dialog initial-focus issue; the shared modal now focuses the first input after opening and restores the opener on close, verified by the passing rerun. No database/backend changes were made, so the earlier 85-test database/API evidence was retained without being represented as rerun for this frontend change.
