# 内容页 (Content Page) — External Design Methodology Research

**Target surface:** `内容页` — routes `/content` (project list) and `/content/:projectId`
(per-project creation workspace) in TopicAI, a local-first AI content operating system
for 小红书 / RED note knowledge-and-experience creators.

**Deliverable type:** external research only. This document does **not** change application
code, specs, or existing docs. It is an input to a future redesign.

**Governing product rule that constrains everything below:** AI only *proposes*; the human
*confirms* every fact, every publish action, every scope change, and every long-term-memory
decision (creator rule / viewpoint / series).

---

## 0. Method, evidence grading, and reachability

### What was searched

| Channel | Status in this environment | Notes |
|---|---|---|
| Primary design-system docs (Material 3, Apple HIG, IBM Carbon, Shopify Polaris, Atlassian, Ant Design, Microsoft HAX, Google PAIR) | ✅ reached | Fetched directly or via Exa. |
| Nielsen Norman Group | ✅ reached | Multiple full articles fetched. |
| Company craft write-ups (Linear, Notion) | ✅ reached | Full pages. |
| GitHub (repos, code, READMEs) | ✅ reached | `gh` CLI + GitHub API. |
| Hacker News | ✅ reached | Free Algolia API + thread fetch. |
| V2EX | ✅ reached | Public API (hot topics). |
| Bilibili | ⚠️ partial | Search API returned headers but no parsed result rows; not used as evidence. |
| Reddit (r/UXDesign, r/userexperience, r/ProductManagement, r/web_design) | ❌ **not reachable** | No Reddit backend installed (`agent-reach doctor`: `"reddit": "off"`). Not replaced with guesses. |
| 小红书 | ❌ **not reachable** | No Xiaohongshu backend installed (`"xiaohongshu": "off"`). |
| X / Twitter | ❌ **not reachable** | `twitter-cli` not installed (`"twitter": "warn"`). |
| 知乎 / 掘金 | ⚠️ partial | Reached indirectly through Exa search results only. Treat as weak evidence. |
| `web_search` / `web_fetch` tool quota | ⚠️ exhausted mid-research | Later fetches routed through Exa / GitHub API / HN API instead. |

### Evidence grading used in this document

- **[P] Primary** — official design-system documentation, standards body, published HCI
  guideline set, or a first-party company engineering/design write-up.
- **[R] Research-backed** — NN/g articles and peer-reviewed/published HCI work (NN/g articles
  synthesise their own usability studies; treat as strong secondary).
- **[C] Community / craft opinion** — forum threads, practitioner blogs. Useful signal,
  explicitly *not* a rule.
- **[X] Unverified** — could not fetch or confirm. Flagged inline and excluded from
  recommendations.

### Sources that must NOT be cited

A second, independent research pass verified the following. They are recorded so nobody
re-derives them and nobody cites a dead or dead-end source:

- ❌ **`https://www.nngroup.com/articles/split-view/` → HTTP 404.** NN/g publishes **no**
  canonical "split view" / "master-detail" article. Use Material 3 / Android / Apple HIG for
  that decision, and NN/g for hierarchy depth
  ([NN/g flat vs deep hierarchy](https://www.nngroup.com/articles/flat-vs-deep-hierarchy/)).
- ❌ **`https://www.nngroup.com/articles/website-forms/` → 404.** The correct URL is
  [web-form-design](https://www.nngroup.com/articles/web-form-design/).
- ⚠️ **Atlassian `@atlaskit/table` is officially deprecated** — the page itself describes it as
  *"an experiment… not recommended for use in production"*, and `@atlaskit/dynamic-table`
  rendered an empty body. **Treat all Atlassian table guidance here as weak evidence**, and do
  not copy that component. ([Atlassian table](https://atlassian.design/components/table))
- ⚠️ **M3 component pages (Lists, Cards, Data tables) are JavaScript-gated** and returned no
  readable text. Every M3 claim in this document therefore comes **only** from the
  *canonical layouts* and *breakpoints* foundation pages, which are static.
- ⚠️ **`linear.app/docs/views` does not exist** (the docs SPA served its 404 view). Linear's
  saved-view model is therefore cited only indirectly, through Notion's documented per-view
  settings.
- ❌ **NN/g has no article titled "AI as a co-pilot."** Searched directly and via the
  [NN/g AI topic index](https://www.nngroup.com/topic/ai/). Real neighbours:
  [Mental Models for Intelligent Assistants](https://www.nngroup.com/articles/mental-model-ai-assistants/),
  [AI Chat Is Not (Always) the Answer](https://www.nngroup.com/articles/ai-chat-not-the-answer/),
  and the [Designing AI study guide](https://www.nngroup.com/articles/designing-ai-study-guide/).
  Treat "AI as a co-pilot" as a paraphrase, **not a citable NN/g title**.
- ❌ **"Designing for AI: The Risk of Over-Trust" could not be located** under that title. No URL
  invented. Substantive equivalents used instead:
  [NN/g explainable AI](https://www.nngroup.com/articles/explainable-ai/),
  [NN/g Magic-8-Ball thinking](https://www.nngroup.com/articles/ai-magic-8-ball/), and the
  [MSR Aether overreliance review](https://www.microsoft.com/en-us/research/wp-content/uploads/2022/06/Aether-Overreliance-on-AI-Review-Final-6.21.22.pdf).
- ⚠️ **GhostWriter (personalisation + agency in human-AI writing)** surfaced in search but its URL
  came back mangled, so it is **deliberately not cited**. Its reported finding — writers preferred
  choosing from multiple suggestions over writing instructions — is corroborated by
  [Apple HIG Multiple options](https://developer.apple.com/design/human-interface-guidelines/machine-learning)
  and [Beyond Prompts](https://doi.org/10.48550/arxiv.2305.07465), which is what §2.52 rests on.
- ⚠️ **`polaris-react.shopify.com/components/tables/index-table` now redirects** to a generic
  Shopify Dev references page. The **live** equivalents are the
  [App Home index-table pattern](https://shopify.dev/docs/api/app-home/latest/patterns/compositions/index-table)
  and [Polaris IndexFilters](https://polaris.shopify.com/components/selection-and-input/index-filters)
  — the latter was read successfully through a content extract and is the source for §2.17.
- ❌ **`https://linear.app/docs/keyboard-shortcuts` → 404** (as is `/docs/command-menu`). Use
  [Select issues](https://linear.app/docs/select-issues) and
  [Display options](https://linear.app/docs/display-options) for Linear's keyboard model.
- ❌ **`https://www.w3.org/WAI/ARIA/apg/patterns/layoutgrid/` → 404.** "Layout Grid" is a
  sub-section of [APG `/patterns/grid/`](https://www.w3.org/WAI/ARIA/apg/patterns/grid/), not its
  own page.
- ❌ **Superhuman's original design-principles post is dead.** `blog.superhuman.com/superhuman-design-principles/`
  and `superhuman.com/blog/design-principles` both 404. Use the
  [game-design post](https://blog.superhuman.com/game-design-not-gamification/) and the
  [First Round piece](https://review.firstround.com/how-superhuman-built-an-engine-to-find-product-market-fit/).
- ⚠️ **Notion Help pages are client-rendered** and yield no text to a headless fetch. The
  [views/filters/sorts](https://www.notion.com/help/views-filters-and-sorts) content cited in this
  document *was* read (via a content extract), but Notion's **keyboard-shortcuts** page and
  Asana / Airtable / Monday / Height saved-view behaviour were **not** verified from primary
  sources — `height.app` did not resolve (curl 000), `support.monday.com` returned 403,
  `support.airtable.com` 404, and `help.asana.com` served a 1 MB JS shell.
- ⚠️ **No W3C pattern and no NN/g article exists for "command palette" as such.** The APG index
  has no palette pattern and NN/g's sitemap contains no palette article. The correct composition
  is **APG Combobox + Listbox + Dialog (Modal)**. The absence is itself a finding.

### Honest statement of uncertainty

- Exact quantitative thresholds (e.g. "how many rows before filtering is required") were **not**
  found as validated numbers in any primary source reached. Claims of the form "users prefer
  N items" are deliberately not made.
- Several platform discussions (Reddit, 小红书, X) that the brief asked for could **not** be
  reached. Where a question is only answerable from those platforms, this document says so
  instead of substituting a guess.
- Mobile adaptation guidance below is synthesised from generic breakpoint tables
  (Material / Windows / Apple), **not** from a study of Chinese creator behaviour on phones.

### Fast grounding: what the current 内容页 actually renders

> Local code observation (not external research) — `frontend/src/pages/Content/ContentPage.tsx`,
> `frontend/src/features/content/ProjectWorkspace.tsx`, `frontend/src/types/contracts/v2/content.ts`.

- The project list renders each project as a **`<button class="content-project-row">`** showing
  only `title`, an **intent label**, and a **next-action label** (`ContentPage.tsx` ~L338–360).
- `ContentProject` *does* carry `status: ProjectStatus`
  (`'inbox' | 'preparing' | 'creating' | 'ready_to_publish' | 'published' | 'awaiting_review' | 'settled'`,
  `content.ts` L1–8) and `calibration_state` — **neither is surfaced in the list row.**
- There is **no filter, sort, group, search, or saved view** on the list surface.
- The workspace already implements a deliberate *one-action-at-a-time* guide:
  `nextStepGuide()` returns a single title/description/progress/helper and explicitly says
  `'你只需要完成这一个动作，其他步骤会在后面出现。'` (`ProjectWorkspace.tsx` L99–183).
- The workspace has **collapsible** `workspace-outline` (项目进度) and `workspace-suggestions`
  (写作提醒) asides with `aria-hidden` + `data-collapsed` (`ProjectWorkspace.tsx` L431–455, L625).
- The AI inference banner exposes exactly one escape hatch — `「不对，我自己选」` — which clears
  the inference server-side (`ContentPage.tsx` L413–438). This is already a
  HAX-Guideline-9-shaped affordance.

These observations are used below to make each principle concrete; they are **not** external
evidence and are labelled as such wherever cited.

---

## 1. Methodology inventory

Everything found, with the source and what it actually contributes to this page.

### 1.1 Navigation & layout structure (list ↔ detail)

| Name | Source URL | What it gives us |
|---|---|---|
| Material Design 3 — Canonical layouts | https://m3.material.io/foundations/layout/canonical-examples | Three canonical scaffolds: **feed**, **list-detail**, **supporting pane**; the starting vocabulary for `/content` + `/content/:projectId`. [P] |
| Material Design 3 — List-detail | https://m3.material.io/foundations/layout/canonical-examples/list-detail | Breakpoint table (Compact 0–599 dp = **1 pane**; Medium 600–839 = 1 *or* 2; Expanded 840+ = **2 panes**); explicit rule that with no selection the detail pane shows a placeholder/empty state; detail views should retain scroll position across item switches. [P] |
| Android — Canonical layouts (adaptive apps) | https://developer.android.com/develop/adaptive-apps/guides/canonical-layouts | Same three-scaffold model with implementation framing. [P] |
| Apple HIG — Split views | https://developer.apple.com/design/human-interface-guidelines/split-views | *"Persistently highlight the current selection in each pane that leads to the detail view"*; let people **hide a pane** and **provide multiple ways to reveal hidden panes** (toolbar button, menu, **keyboard shortcut**); prefer the thin divider; skip split view in compact environments. [P] |
| Windows — List/details pattern | https://learn.microsoft.com/en-us/windows/apps/develop/ui/controls/list-details | A concrete numeric breakpoint: **stacked (drill-in) at 320–640 epx, side-by-side at 641 epx+**; "use the stacked style when only one pane is visible at a time". [P] |
| Notion — Views, filters, sorts & groups | https://www.notion.com/help/views-filters-and-sorts | The **"Open pages in"** control: *Side peek* (detail opens on the right, **list stays interactive**), *Center peek* (focused modal), *Full page*. Directly answers "how heavy should opening a project feel?". [P] |
| Material Design 3 — Canonical layouts: **supporting pane** | https://m3.material.io/foundations/layout/canonical-examples/supporting-pane | The pattern for secondary content that is **only meaningful relative to the primary** (vs. parent→child, which is list-detail). Fixed **360 dp** pane, below the focus pane on compact/medium and beside it on expanded. [P] |
| Material Design 3 — Breakpoints | https://m3.material.io/foundations/layout/breakpoints | The exact scale (Compact <600 dp, Medium 600–839, Expanded 840–1199, Large 1200–1599, XL 1600+) and the five adaptation questions (reveal / divide / resize / reposition / swap). **Critical caveat: two panes in a medium layout with high information density "can reduce usability."** [P] |
| Material Design 3 — Canonical layouts: feed | https://m3.material.io/foundations/layout/canonical-examples/feed | Grid/feed behaviour — columns increase with breakpoint, and size + position express grouping and emphasis. [P] |
| Shopify — App Home **index-table pattern** | https://shopify.dev/docs/api/app-home/latest/patterns/compositions/index-table | The live canonical index-table composition: search + sort popover in a `filters` slot, **status badges**, `clickDelegate` row→checkbox, row links to detail pages, pagination; the bulk bar ("2 of 3 selected", Bulk edit, Delete) **replaces the filter row**. Introduces `listSlot="primary"/"secondary"` — designating which fields lead a stacked row so a desktop table degrades into a stacked list instead of scrolling horizontally. [P] |
| NN/g — Flat vs. Deep Hierarchy | https://www.nngroup.com/articles/flat-vs-deep-hierarchy/ | Content is more discoverable when not buried; deep hierarchies are harder to use and **deep levels force generic labels**. The source for "don't add a third navigation level". [R] |
| NN/g — Local Navigation | https://www.nngroup.com/articles/local-navigation/ | Verified substitute for the non-existent "split view" article; local navigation patterns for sibling/parent structures. [R] |

### 1.2 Progressive disclosure & multi-stage workflows

| Name | Source URL | What it gives us |
|---|---|---|
| NN/g — Progressive Disclosure | https://www.nngroup.com/articles/progressive-disclosure/ | The canonical definition; the **core/secondary split must be right**; it must be **obvious how to progress**; **more than 2 disclosure levels typically has low usability**; distinguishes *progressive* (hierarchical, rarely needed) from **staged disclosure** (linear, all steps visited). [R] |
| NN/g — Wizards: Definition and Design Recommendations | https://www.nngroup.com/articles/wizards/ | 5 design recommendations, plus the honest list of wizard **disadvantages** (higher interaction cost, hard to compare across steps, not gracefully interruptible, blocks other app areas, limits control). [R] |
| NN/g — 8 Design Guidelines for Complex Applications | https://www.nngroup.com/articles/complex-application-design/ | The single most on-point NN/g article for this page: *promote learning by doing*, *help users adopt more efficient methods*, **provide flexible and fluid pathways** (skipping ahead, looping back), *help users track actions and thought processes*, *reduce clutter without reducing capability*, **ease transition between primary and secondary information**, *make important information visually salient*. [R] |
| Smashing Magazine — Better Form Design: One Thing Per Page (Adam Silver) | https://www.smashingmagazine.com/2017/05/better-form-design-one-thing-per-page/ | The definitive case study for splitting one complex process into one-decision-per-screen. Documents **16 reasons the pattern works**, and the business evidence is unusually concrete: the Boots.com single-page accordion checkout converted poorly, and the Just Eat redesign to one-thing-per-page produced **"an extra 2 million orders a year"**. Reasons that matter here: reduces cognitive load; errors are caught early and easy to fix; **amending details is easier** (going back to a dedicated page beats scrolling within a page); **adds a sense of progression**; **second-time experiences are faster** (skip already-known pages); complements mobile-first; reduces risk of losing data in a long form. Explicitly defines the unit as a *discrete question*, not a single field: *"An address form has multiple fields, but it's a single, discrete question."* [C, with measured outcomes] |
| GOV.UK Design System — Question pages | https://design-system.service.gov.uk/patterns/question-pages/ | Verified specifics: **one question per page**; a **mandatory back link**; a distinct per-page heading that **is** the question; **"Continue" rather than "Next", left-aligned**. Crucially it also **warns against the all-questions + tappable-back progress indicator** (often unnoticed, space-hungry, poor on small screens, hard to label, hard to handle conditional sections) — a direct constraint on how we render the 8-stage rail. [P] |
| GOV.UK Design System — Check answers | https://design-system.service.gov.uk/patterns/check-answers/ | The **summary-list review surface** before committing: each row is a labelled value with its own **"Change"** link. This is the precedent for 发布检查 and 经验确认 — and for presenting **AI-suggested field candidates** as a reviewable list rather than one giant form. [P] |
| GitLab Pajamas — Progressive disclosure | https://design.gitlab.com/patterns/progressive-disclosure/ | Independent corroboration of the two-level rule: *"Avoiding multiple levels of disclosure — 3+ levels is a sign the feature is too complex."* Plus a catalogue of disclosure mechanisms. [P] |
| IBM Carbon — Disclosures pattern | https://carbondesignsystem.com/patterns/disclosures-pattern/ | Design-system treatment of disclosure widgets grouped with filtering/empty states. [P] |

### 1.3 Status, taxonomy, filtering, sorting, grouping, saved views

| Name | Source URL | What it gives us |
|---|---|---|
| NN/g — Filters vs. Facets: Definitions | https://www.nngroup.com/articles/filters-vs-facets/ | Faceted navigation is more powerful but **more expensive to build and carries extra interaction cost**; *"it's wise to make sure that users truly do need faceted navigation"* before investing. [R] |
| IBM Carbon — Filtering pattern | https://carbondesignsystem.com/patterns/filtering/ | Five selection methods (single, multiselect, **multiple categories**, batch-update, instant-update); **multiple filter categories "should never be put within a menu or dropdown"**; when filters are hidden, the closed state must show **the number of applied filters + a clear affordance**; each category needs a clear-all. [P] |
| IBM Carbon — Empty states pattern | https://carbondesignsystem.com/patterns/empty-states-pattern/ | Three empty-state **types** (no-data / user-action / error-management) mapped to goals and when-to-use; empty state must **replace the table including headers and footer**; **multiple simultaneous empty states → use a tertiary button** to avoid competing primary CTAs; left-align the block; decorative images get empty `alt`. [P] |
| Shopify Polaris — Index filters | https://polaris.shopify.com/components/selection-and-input/index-filters | Verified at source. The canonical **list toolbar**: filter + search + sort + **tabs-as-saved-views** + view management in one bar above an index table. Concrete details worth copying: saved views are **tabs**, the default view is **locked** (`isLocked` — cannot be renamed or deleted) while every other view carries **rename / duplicate / delete** actions; there is an explicit *filtering mode* (`useSetIndexFiltersMode`) separating "browse" from "filtering"; and the component documents dedicated **empty filter states** — `With no filters`, `With no search or filters`, `Disabled`, and `With pinned filters`. [P] |
| UX Patterns Guide — Saved view | https://uxpatternsguide.com/patterns/saved-view/ | Saved view as a **first-class named object**; must show **active name, visibility, default status, and a "modified from saved" state**; save the **canonical definition, not the current row IDs**; handle **invalid saved fields** and permission boundaries explicitly; **keep temporary tweaks separate from updating the saved definition**. [C] |
| Notion — Views, filters, sorts & groups | https://www.notion.com/help/views-filters-and-sorts | Layout / property visibility / filter / sort / **group** / **sub-group** per view; each view has independent settings; views appear as nested sidebar items. [P] |
| Atlassian Design System — Table | https://atlassian.design/components/table | ⚠️ **Deprecated and effectively unverified** — the page describes itself as *"an experiment… not recommended for use in production"*, and `@atlaskit/dynamic-table` rendered empty. Listed for completeness; **do not use as guidance.** [X] |
| IBM Carbon — Data table usage | https://carbondesignsystem.com/components/data-table/usage/ | The concrete density/action model: **five row sizes**, the **header row size must match the body**, extra-large reserved for **two-line rows**; toolbar takes **≤5 actions then overflow**; when a row's overflow holds **fewer than three options, keep them inline as icon buttons**; the batch-action bar **disables the inline row actions**; use a **skeleton, not a spinner**; zebra striping aids horizontal scanning. Also: give the table the most width on the page — never cram dense data into a narrow container. [P] |
| IBM Carbon — Structured list | https://carbondesignsystem.com/components/structured-list/usage/ | The **list-vs-table decision rule**: a structured list is for simple grouped data with **no nesting**; if you need nesting/complexity you need a data table; confined space → contained list. Ships `default` and `condensed` sizes. [P] |
| IBM Carbon — Overflow menu | https://carbondesignsystem.com/components/overflow-menu/usage/ | Destructive actions separated by a **divider** and placed below the primary action set. [P] |
| GitLab Pajamas — Table | https://design.gitlab.com/components/table/ | The cleanest available **when-to-use** rule for table vs. semantic list vs. cards vs. tree; striped and **condensed** variants, where condensed is explicitly for *"data heavy and text only"* content. [P] |
| GitLab Pajamas — Filtering | https://design.gitlab.com/patterns/filtering/ | Search-vs-filter decision by user goal (search = find a specific item; filter = narrow by parameters), plus a **1–5 data-complexity ladder** mapping complexity to components: search → +sorting → +tabs → +dropdowns → full filter component. [P] |
| GitLab Pajamas — Empty states / Loading | https://design.gitlab.com/patterns/empty-states/ · https://design.gitlab.com/patterns/loading/ | Loading-more is a one-way action (collapsing needs a different pattern); skeleton loader and spinner are **separate primitives**. Note: GitLab still lists progressive loading as an **open TODO**, so treat "loading more" conventions here as unsettled. [P] |
| UX Patterns — Table vs List vs Card grid | https://uxpatterns.dev/pattern-guide/table-vs-list-vs-cards | Decision guide: table when comparing attributes across items/sorting columns/scanning dense structured data; list when reading down; cards when items are standalone. [C] |
| Ant Design — 数据列表 (Data list spec) | https://ant.design/docs/spec/data-list-cn/ | **Chinese-language** list taxonomy that maps almost 1:1 onto this page: `表格 Table` (浏览性/矩阵, compare attributes) vs `列表 List` (兼顾浏览性与展示性, vertical, fast scanning, good in narrow containers) vs `卡片列表 Card list` (展示性, grid, equal attention); plus 搜寻数据 / 分页 / **导航至详情** / **批量操作** / 新建 / 删除 / 列表工具栏 / 布局 / **空状态**. Design goals stated as *"让列表易于扫读"* and *"快速查找列表中的对象"*. [P] |

### 1.3b Bulk operations and multi-select

| Name | Source URL | What it gives us |
|---|---|---|
| NN/g — Bulk Actions: 3 Design Guidelines | https://www.nngroup.com/videos/bulk-actions-design-guidelines/ | The three essentials: **provide a Select All option**, **use a contextual action bar**, **give clear feedback with undo**. [R] |
| Marigold UI — Bulk Actions pattern | https://www.marigold-ui.io/patterns/user-input/bulk-actions | The most complete treatment found. Governing principle: **"users act only on what they can see."** Mechanics: select-all = current page only; **scope changes (page/filter/search/sort/page-size) clear the selection, visibly**; two-step explicit control if a whole-result-set action is truly required, stating the exact count; confirm dialog names the count; verb-named actions ordered safest→most destructive with destructive last and visually separated; long tail in an overflow menu; **while selection is active, per-row actions are disabled so there is only one pressable scope**; don't offer a bulk action speculatively. [P] |
| Enterprise UX — Rules for editing list rows one-by-one or in bulk | http://www.enterpriseux.co/interacting-with-lists/ | Older but useful framing: bulk multi-select is a **rarely-used** action, so the pattern must be **obvious and consistent across the whole app**; don't hide multi-select entirely (the author criticises Gmail for hiding it until rows are selected); keep the multi-select control near the select-all checkbox. [C] |

### 1.4 Information density

| Name | Source URL | What it gives us |
|---|---|---|
| Matthew Ström — UI Density | https://matthewstrom.com/writing/ui-density/ | The best available framework. Density has **four axes**: *visual* (how much is on screen), *information* (Tufte's data-ink ratio), *design* (ratio of necessary to total Gestalt decisions), *temporal*, and *value*. Defines **UI density = value ÷ (time × space)**. Includes perceptual latency bands: **<100 ms feels simultaneous** (animation here makes apps feel *slower*); **100 ms–1 s** needs animation/visual bridging; **1–10 s** needs an indeterminate indicator (users abandon within 10 s); **10 s–1 min** needs a determinate indicator; **>1 min** should let the user leave and be notified. [C but well-argued and widely cited] |
| HN — "Ask HN: What are good high-information density UIs?" (530 pts / 372 comments, May 2025) | https://news.ycombinator.com/item?id=43925732 | Practitioner consensus thread. Recurring signal: **speed is density** ("their real superpower" is loading with no latency); repeated praise for consistent, purpose-built, low-chrome interfaces (McMaster-Carr); explicit criticism of "everything is spaced out and zoned out gray on gray". Also a documented counter-argument: one commenter prefers DigiKey's **filter-then-apply** pattern over McMaster's instant auto-updating filters. [C] |
| Refactoring UI — *7 Practical Tips for Cheating at Design* (Adam Wathan & Steve Schoger) | https://medium.com/refactoring-ui/7-practical-tips-for-cheating-at-design-40c736799886 | Verbatim tactics verified: **(1) "Use color and weight to create hierarchy instead of size"** — a dark-but-not-black primary, one grey for secondary, a lighter grey for ancillary, and **at most two font weights (≈400/500 and ≈600/700)**; **avoid weights under 400** for UI text at small sizes. **(2) "Don't use grey text on colored backgrounds"** — the real mechanism is *reduced contrast*, not lightness, so on a coloured surface either use white at reduced opacity or hand-pick a same-hue colour. **(3) Offset shadows** rather than increasing blur/spread. [C — de-facto craft standard, now verified at source] |
| Refactoring UI (book/site) | https://www.refactoringui.com/ | Fuller tactical hierarchy toolkit behind the article above. [C] |

### 1.5 AI suggestion / human-in-the-loop UX

| Name | Source URL | What it gives us |
|---|---|---|
| Microsoft HAX — Guidelines for Human-AI Interaction (18 guidelines) | https://www.microsoft.com/en-us/haxtoolkit/ai-guidelines/ | The authoritative evidence-based set (synthesis of 20+ years of research, introduced in the 2019 CHI paper). Full verbatim list below. [P] |
| Microsoft HAX — Design Library | https://www.microsoft.com/en-us/haxtoolkit/library/ | Each of the 18 guidelines with design patterns, organised by phase: *upon initial interaction, during interaction, **when the AI system is wrong**, and over time*. [P] |
| Google PAIR — People + AI Guidebook, "Explainability + Trust" | https://pair.withgoogle.com/chapter/explainability-trust/ | **Calibrated trust** as the design goal (neither blind trust nor aversion); **partial explanations** ("explain what's important", not everything); confidence display formats — **categorical (high/medium/low), n-best alternatives, numeric, data-visualisation** — with the explicit warning that **numeric confidence often misleads** and **if confidence isn't actionable, don't show it**; **tie explanations to user actions**; **account for situational stakes**; progressive increase of automation **under user guidance**. [P] |
| Google PAIR — Feedback + Control | https://pair.withgoogle.com/chapter/feedback-controls/ | Control/automation balance and granular feedback. [P] |
| Google PAIR — Errors + Graceful Failure | https://pair.withgoogle.com/chapter/errors-failing/ | What to do when the model is wrong or low-confidence. [P] |
| Google PAIR — Mental Models | https://pair.withgoogle.com/chapter/mental-models/ | Onboarding users to what the AI can and cannot do. [P] |
| Apple HIG — Machine learning | https://developer.apple.com/design/human-interface-guidelines/machine-learning | Platform guidance for ML-backed features (transparency, correction, avoiding over-trust). [P] |
| NN/g — AI: First New UI Paradigm in 60 Years | https://www.nngroup.com/articles/ai-paradigm/ | Frames AI as **intent-based outcome specification** which **reverses the locus of control**; warns the intent paradigm is *"prone to including erroneous information"*, that when *"users don't know how something was done, it can be harder for them to identify or correct the problem"*, and predicts a **hybrid UI** — GUI + intent — rather than pure chat. Strong argument for keeping a structured, clickable workspace instead of a chat surface. [R] |
| NN/g — Designing AI Products and Features: Study Guide | https://www.nngroup.com/articles/designing-ai-study-guide/ | Curated index into NN/g's AI-UX corpus (useful for a follow-up sweep). [R] |
| Linear — Design for the AI age | https://linear.app/blog/design-for-the-ai-age | The **"workbench"** metaphor: *"AI doesn't replace the workbench, it's a powerful new tool to place on top of it… the place where agents operate with clear guidelines and output is reviewed and approved. Humans stay in the loop."* Also: *"Without form, function gets lost… Unbounded AI, much like a river without banks, becomes powerful but directionless."* [P] |
| Linear Method | https://linear.app/method | Linear's documented product/build principles (direction, scoping, momentum) — context for why Linear's UI reads as it does. [P] |
| **Ant Design X** — AI 交互设计规范 (Chinese) | https://ant-design-x.antgroup.com/docs/spec/introduce-cn | **A Chinese design-system primary source for exactly this product's problem.** Names a four-stage AI interaction lifecycle — 唤醒 / 表达 / **确认** / **反馈** — and publishes dedicated specs on [confirm-generation-process](https://ant-design-x.antgroup.com/docs/spec/confirm-generation-process-cn) and [feedback-result-application](https://ant-design-x.antgroup.com/docs/spec/feedback-result-application-cn): copy, **重新生成 with version switching**, 👍/👎 feedback, **delete with a second confirmation**, and **RAG citations collapsed by default**. The closest published analogue to the 候选内容 / 发布检查 surface found anywhere. [P] |
| HAX — Design Patterns library | https://www.microsoft.com/en-us/haxtoolkit/design-patterns/ | Reusable solutions keyed `G1`…`G18` to each guideline — the "what do I actually build" layer under the 18 guidelines. [P] |
| HAX — Guideline 9: Support efficient correction | https://www.microsoft.com/en-us/haxtoolkit/guideline/support-efficient-correction/ | Concrete patterns: **G9-C undo automated actions**, **G9-B rich edits**, **G9-E batch edits**. [P] |
| HAX — Guideline 16: Convey the consequences of user actions | https://www.microsoft.com/en-us/haxtoolkit/guideline/convey-the-consequences-of-user-actions/ | Splits into **16A feedforward** (state what will happen *before* the click), **16B feedback** (confirm what happened), **16C reconfirm a past action**. The structural answer to "does confirming this write to long-term memory?". [P] |
| Amershi et al., *Guidelines for Human-AI Interaction*, CHI 2019 | https://www.microsoft.com/en-us/research/uploads/prod/2019/01/Guidelines-for-Human-AI-Interaction-camera-ready.pdf | The peer-reviewable source behind the HAX guidelines: codified 150+ recommendations into 18 guidelines, validated with 49 practitioners across 20 products. [P] |
| Horvitz, *Principles of Mixed-Initiative User Interfaces*, CHI 1999 | https://erichorvitz.com/chi99horvitz.pdf · DOI https://dl.acm.org/doi/10.1145/302979.303030 | The foundational 12 principles for systems that both take initiative and defer to the user — the academic root of "AI proposes, human confirms". Key: **P7 explicit invocation/acceptance**, **P8 consider the cost of poor timing and disruption**. [P] |
| Apple HIG — Machine learning | https://developer.apple.com/design/human-interface-guidelines/machine-learning | Names the required affordances directly: **Corrections**, **Multiple options**, **Confidence**, **Attribution**, **Limitations**. Includes the strong warning that *"if you're not sure how your confidence values correlate with quality, it's not a good idea to convey confidence."* [P] |
| Apple HIG — Generative AI | https://developer.apple.com/design/human-interface-guidelines/generative-ai | **"Keep people in control"**, require a **non-AI fallback path**, and **disclose** AI involvement. [P] |
| PAIR Guidebook **v2** (patterns) | https://pair.withgoogle.com/guidebook-v2/patterns/ | ⚠️ **Newer than the v1 chapter URLs used elsewhere in this document** (v1 still resolves and remains accurate). 23 patterns; adopt v2 as canonical going forward. [P] |
| NN/g — Confirmation Dialogs | https://www.nngroup.com/articles/confirmation-dialog/ | The counterweight to a "confirm everything" reading of the product rule: confirmation dialogs **stop working when overused**; never default to "Yes"; restate specifics rather than asking a bare "Are you sure?". [R] |
| NN/g — Explainable AI | https://www.nngroup.com/articles/explainable-ai/ | Two findings that directly shape proposal UI: **citations are rarely clicked**, and **step-by-step "reasoning" implies a false level of certainty**. Burying AI limits in a disclaimer does not work either. [R] |
| NN/g — Accordion Editing and Apple Picking | https://www.nngroup.com/articles/accordion-editing-apple-picking/ | Recommends **compartmentalisation, direct editing, and point-to-select** for AI-assisted editing — i.e. **per-section edit beats whole-document regeneration**. [R] |
| NN/g — AI Chatbots Discourage Error Checking | https://www.nngroup.com/articles/ai-chatbots-discourage-error-checking/ | Evidence that chat framing suppresses verification behaviour — reinforces keeping a structured workspace rather than a chat surface. [R] |
| NN/g — Humanizing AI Is a Trap | https://www.nngroup.com/articles/humanizing-ai/ | Do not give the system a persona or "I think" voice; neutral machine-proposal labelling is safer and more honest. [R] |
| NN/g — The Articulation Barrier | https://www.nngroup.com/articles/ai-articulation-barrier/ | Most users cannot express intent well in prose — the argument for structured, clickable intent capture over prompt boxes. [R] |
| WorkOS — Approval fatigue in agent governance | https://workos.com/blog/approval-fatigue-agent-governance | Industry-side confirmation that high-volume approval prompts produce **rubber-stamping** — the failure mode a confirm-per-sentence design would create. [C] |
| Google Docs — Suggesting mode | https://support.google.com/docs/answer/6033474 | Shipped precedent for per-change **Accept / Reject**, plus accept-all, plus preview-with-and-without. [P] |
| Notion AI for docs | https://www.notion.com/help/guides/notion-ai-for-docs | Shipped precedent for the three-way affordance: *"accept, discard, or ask it to try again"*. [P] |
| Grammarly — How suggestions work | https://www.grammarly.com/blog/engineering/how-suggestions-work-grammarly-editor/ | Two production lessons: a suggestion must be **correct *and* relevant**, and **stale suggestion cards must be hidden**; batch-accept is treated as a separate, riskier operation. [P] |
| GitHub Copilot — code suggestions | https://docs.github.com/en/copilot/concepts/completions/code-suggestions | Ghost-text + next-edit-suggestion UX, and **provenance for public-code matches** — a shipped model of attaching provenance to a proposal. [P] |
| Cursor — Reviewing and testing changes | https://cursor.com/learn/reviewing-testing | Diff-review workflow: watch the diff, **stop mid-flight, revert, small semantic commits**. [P] |
| 人人都是产品经理 — 人工接管 (human takeover) | https://www.woshipm.com/ai/6447314.html | Chinese-language practitioner source stating the long-term-memory rule almost verbatim: **「当前任务纠错和系统长期学习，是两件不同的事」** — an edit inside a task must not silently become permanent system learning. Also offers a five-state handover model (建议 → 预演 → 授权执行 → 暂停接管) and a three-layer handover card. [C] |
| MSR (Aether) — *Overreliance on AI: Literature Review* | https://www.microsoft.com/en-us/research/wp-content/uploads/2022/06/Aether-Overreliance-on-AI-Review-Final-6.21.22.pdf | Mechanism-level account of automation bias, confirmation bias and ordering effects, with concrete mitigations: **recommendations only upon request**, and **asking users to state their own prediction before seeing AI output**. [P] |
| Lyell & Coiera — Automation bias and verification complexity (systematic review) | https://pmc.ncbi.nlm.nih.gov/articles/PMC7651899/ | The load-bearing finding for confirmation design: automation bias is driven by **verification complexity / cognitive load**, not distraction — *the harder the AI is to check, the more it is trusted.* Directly indicts opaque confirmation UI. [P] |
| Romeo & Conti (2025) — automation bias in human–AI collaboration | https://doi.org/10.1007/s00146-025-02422-7 | Explanations alone often **fail** to reduce over-reliance and can backfire; the usable intervention is **user engagement / independent verification**, not more transparency. [P] |
| Dietvorst, Simmons & Massey — *Overcoming Algorithm Aversion* | https://pubsonline.informs.org/doi/10.1287/mnsc.2016.2643 | Giving people the ability to modify an imperfect algorithm **even slightly** raises willingness to use it and satisfaction with the process — the empirical case for editability over explanation. [P] |
| NN/g — When Should We Trust AI? Magic-8-Ball Thinking | https://www.nngroup.com/articles/ai-magic-8-ball/ | How users mis-calibrate trust in AI output; substitute for the non-existent "Risk of Over-Trust" title. [R] |
| NN/g — How AI Literacy Shapes GenAI Use | https://www.nngroup.com/articles/ai-literacy/ | Why disclaimers get skipped and what to do instead — pair the limit statement with an action, placed near the point of use. [R] |
| NN/g — The Core Skill of Design in the AI Era: Critique | https://www.nngroup.com/articles/ai-era-critique/ | The nearest transferable evidence for 盲评: an **F1 ≈ 0.8** bar against human annotation as a usable LLM-judge reliability threshold, with the warning that uncalibrated judges can degrade as easily as improve. [R] |
| NN/g — Mental Models for Intelligent Assistants | https://www.nngroup.com/articles/mental-model-ai-assistants/ | Substitute for the non-existent "AI as a co-pilot" title; how users build a working model of an assistant. [R] |
| NN/g — AI Chat Is Not (Always) the Answer | https://www.nngroup.com/articles/ai-chat-not-the-answer/ | When chat is the wrong container — supports keeping the structured 8-stage workspace. [R] |
| Beyond Prompts — mixed-initiative co-creativity | https://doi.org/10.48550/arxiv.2305.07465 | Research on choosing-from-suggestions vs instructing-with-prompts in creative tools, supporting the "multiple candidate framings" principle (§2.52). [P] |

**The 18 HAX guidelines, verbatim** (source: https://www.microsoft.com/en-us/haxtoolkit/library/):

1. **Make clear what the system can do** — Help the user understand what the AI system is capable of doing.
2. **Make clear how well the system can do what it can do** — Help the user understand how often the AI system may make mistakes.
3. **Time services based on context** — Time when to act or interrupt based on the user's current task and environment.
4. **Show contextually relevant information** — Display information relevant to the user's current task and environment.
5. **Match relevant social norms** — Ensure the experience is delivered in a way that users would expect, given their social and cultural context.
6. **Mitigate social biases** — Ensure the AI system's language and behaviors do not reinforce undesirable and unfair stereotypes and biases.
7. **Support efficient invocation** — Make it easy to invoke or request the AI system's services when needed.
8. **Support efficient dismissal** — Make it easy to dismiss or ignore undesired AI system services.
9. **Support efficient correction** — Make it easy to edit, refine, or recover when the AI system is wrong.
10. **Scope services when in doubt** — Engage in disambiguation or gracefully degrade the AI system's services when uncertain about a user's goals.
11. **Make clear why the system did what it did** — Enable the user to access an explanation of why the AI system behaved as it did.
12. **Remember recent interactions** — Maintain short-term memory and allow the user to make efficient references to that memory.
13. **Learn from user behavior** — Personalize the user's experience by learning from their actions over time.
14. **Update and adapt cautiously** — Limit disruptive changes when updating and adapting the AI system's behaviors.
15. **Encourage granular feedback** — Enable the user to provide feedback indicating their preferences during regular interaction with the AI system.
16. **Convey the consequences of user actions** — Immediately update or convey how user actions will impact future behaviors of the AI system.
17. **Provide global controls** — Allow the user to globally customize what the AI system monitors and how it behaves.
18. **Notify users about changes** — Inform the user when the AI system adds or updates its capabilities.

Guidelines **8, 9, 10, 11, 16, 17** are the ones this product's core rule most directly depends on.

### 1.6 Keyboard, accessibility, and reference libraries

| Name | Source URL | What it gives us |
|---|---|---|
| WAI-ARIA Authoring Practices Guide — Patterns | https://www.w3.org/WAI/ARIA/apg/patterns/ | Required keyboard interaction models for listbox, grid, combobox, toolbar, disclosure — the vocabulary for a keyboard-navigable project list and workspace. [P] |
| WCAG 2.2 | https://www.w3.org/TR/WCAG22/ | Success criteria (focus not obscured, dragging movements, target size, consistent help, redundant entry). [P] |
| NN/g — Status Trackers and Progress Updates: 16 Design Guidelines | https://www.nngroup.com/articles/status-tracker-progress-update/ | **Pull (tracker) vs push (update)**; show the **latest update most prominently**; use **plain language, never backend jargon**; **always show previous updates with dates**; for long processes **send low-granularity updates** rather than silence; a "**Next steps**" panel that is stale is actively harmful. [R] |
| Mobbin | https://mobbin.com/ | Screenshot reference library of real shipped flows — for pattern selection (saved views, list toolbars, empty states) before designing. [C] |
| Figma Community | https://www.figma.com/community | Free M3 / Carbon / Polaris design kits, useful as a token source. [C] |
| Dribbble | https://dribbble.com/ | Visual reference only; **treat as decoration, not interaction evidence**. [C] |
| Google Stitch — DESIGN.md | https://stitch.withgoogle.com/docs/design-md/overview/ | The `DESIGN.md` convention: a plain-text design-system document an AI agent reads to generate consistent UI. Relevant because we want agents to produce consistent screens for this surface. [P] |
| VoltAgent — Awesome DESIGN.md | https://github.com/VoltAgent/awesome-design-md | 73 analysed `DESIGN.md` files from popular brand design systems, drop-in for agent-generated UI. [C] |

### 1.7 Scanning, states, and timing

| Name | Source URL | What it gives us |
|---|---|---|
| NN/g — Visual Indicators to Differentiate Items in a List | https://www.nngroup.com/articles/visual-indicators-differentiators/ | **The only quantified list-scanning finding reached.** NN/g tested four indicator conditions (text only / colour only / icon only / colour + icon) across four mobile pages. Result: **"users are roughly 37% faster at finding items within a list… when visual indicators vary both in color and icon compared to text alone"**; the **text-only condition was 57% slower** than the best condition; **icon-only was marginally faster than colour-only** (p<0.01), and significantly better on 2 of 4 metrics on stock tables. NN/g adds: *"Relying on color alone runs the risk of failing color-blind users."* **Stated limitation, which matters:** the study was run on **mobile screens only** — NN/g did not test desktop and explicitly speculate the advantage might be larger there without measuring it. [R, with a stated scope limit] |
| NN/g — Visual Hierarchy in UX: Definition | https://www.nngroup.com/articles/visual-hierarchy-ux-definition/ | Hierarchy = contrast/colour, scale, and grouping (proximity + common regions); includes the **squint test** as a cheap verification method. [R] |
| NN/g — Skeleton Screens 101 | https://www.nngroup.com/articles/skeleton-screens/ | The timing rule: **<1 s → show nothing; 2–10 s → skeleton for a full page or spinner for a single module; >10 s → explicit progress bar.** Explicitly discourages **frame-display-only skeletons** (header/footer/background with no content wireframe) as "effectively a spinner that teaches nothing". [R] |
| NN/g — Top 10 Application-Design Mistakes | https://www.nngroup.com/articles/top-10-application-design-mistakes/ | Response-time limits restated, plus the **"double-D rule" (differences are difficult)** and an inconsistency catalogue — the reference for "same action, different word, different place". [R] |
| NN/g — Infinite Scrolling: 5 Tips | https://www.nngroup.com/articles/infinite-scrolling-tips/ | The source for **"do not infinite-scroll a work-item list"** — it removes the footer, destroys the sense of "how many are there", and fights Select All / bulk selection. [R] |
| NN/g — "No Results" pages | https://www.nngroup.com/articles/search-no-results-serp/ | The dedicated design for the **filtered-to-nothing** state: explain no match, offer a path forward, never mock the user. [R] |
| NN/g — Accordions on Desktop / Mobile accordions | https://www.nngroup.com/articles/accordions-on-desktop/ · https://www.nngroup.com/articles/mobile-accordions/ | Accordions are *"a mini-IA"*: they shrink scrolling but raise interaction cost and force the user to make a topic decision before seeing content. They pay off on mobile; on desktop they are the wrong tool when users must open most sections. [R] |
| NN/g — Cards component | https://www.nngroup.com/articles/cards-component/ | Cards suit **heterogeneous summary-and-link content** that benefits from a large touch target — the basis for rejecting a card grid for a uniform work queue. [R] |

### 1.8 Community signals — what actually came back

Reported honestly, including where the signal was thin or absent. Treat all of this as **[C]**.

| Channel | What actually came back | Signal strength |
|---|---|---|
| **Hacker News** — [Ask HN: What are good high-information density UIs?](https://news.ycombinator.com/item?id=43925732) (530 pts / 372 comments, May 2025) | The single best community source found. The OP opens with the exact frustration this page faces: *"Search engines are full to the brim with vague articles repeating each other's talking points"*, and links [Matthew Ström's UI Density](https://matthewstrom.com/writing/ui-density/) as the exception. Recurring consensus: **speed is density** (*"loading it with no latency is Terminal's real superpower"*); consistent, purpose-built, low-chrome interfaces win (McMaster-Carr); explicit distaste for *"everything is spaced out and zoned out gray on gray"*. **Counter-signal, also useful:** one commenter prefers DigiKey's **filter-then-apply** over McMaster's instant auto-updating filters — i.e. batch-apply filtering is not universally disliked. | **Strong** (large, on-topic, argumentative in a useful way) |
| **Hacker News** — command-palette discussion (321 pts / 267 comments) | Two substantive pieces surfaced and were read: [Command Palette Interfaces](https://philipcdavis.com/writing/command-palette-interfaces) and [Capiche — command palettes](https://capiche.com/e/consumer-dev-tools-command-palette). The thread's top complaints are concrete: *"I hate this trend. Give me back menus and toolbars"*, and *"I'm okay with command palettes, but hate how they steal ctrl/cmd + k… please make it configurable!"* The best counter-argument for why palettes work: fuzzy search plus *"a feedback mechanism that shows what the command will do before it's run"*. **Correction to a claim in circulation:** GitHub's palette deprecation was **announced and then paused**, not completed — the changelog is titled *"Update: Pausing Command Palette Deprecation"* ([GitHub changelog](https://github.blog/changelog/2025-07-15-upcoming-deprecation-of-github-command-palette-feature-preview/)). Do **not** claim "GitHub killed the command palette". | Moderate |
| **Hacker News** — LLM-assisted writing and ownership (391 pts / 426 comments) | Discussion of a peer-reviewed EEG study finding LLM-assisted writers had the **weakest brain connectivity and the lowest self-reported ownership of their own essay** ([arXiv:2506.08872](https://arxiv.org/abs/2506.08872); [HN thread](https://news.ycombinator.com/item?id=44286277)). The dominant framing was *cognitive offloading*. | **Strong** — this is the empirical case for a mandatory human confirmation step |
| **V2EX** — design / product / create nodes | **Thin, and reported as such.** No thread on list-detail, information density, saved views, or multi-step workspace design was found across the `design`, `product` and `create` nodes. The only adjacent signal is a complaint thread about over-complex tools: [吐槽：为什么网上大多数时间戳转换工具网站都那么难用？又冗余又复杂](https://www.v2ex.com/t/1223137) — *redundant and complicated*. A design-reference thread ([Awwwards 真的好用吗？](https://www.v2ex.com/t/1236772)) points at visual inspiration sites, not interaction methodology. | **Weak** |
| **Reddit** (r/UXDesign, r/userexperience, r/ProductManagement, r/web_design) | ❌ **Not reachable** — no Reddit backend installed (`agent-reach doctor`: `"reddit": "off"`; anonymous `reddit.com/*.json` is blocked and the official API requires manual approval). **No substitute was fabricated.** | **None** |
| **小红书** | ❌ **Not reachable** — `"xiaohongshu": "off"`. Notably, this is the platform whose creator behaviour the page is *for*, so its absence is the most consequential gap in this document. | **None** |
| **X / Twitter** | ❌ **Not reachable** — `twitter-cli` not installed (`"twitter": "warn"`). | **None** |
| **掘金 / 知乎** | ⚠️ Reached only indirectly through Exa search results. Ant Design's spec (above) is the substantive Chinese-language source; 掘金/知乎 yielded nothing primary. | **Weak** |

### 1.9 Hard constraint found late: AI-content disclosure on 小红书

**This is a compliance constraint, not a UX preference, and it is the single most
scope-changing finding in this document.**

- Secondary reporting states that **小红书 requires creators to proactively label
  AI-generated / AI-synthesised content**, and that its AI-governance rules **prohibit using AI
  to substitute for human operation while permitting AI-*assisted* creation.** Environment note:
  小红书 was **not directly reachable** (backend off), so this is **secondary news reporting,
  not a primary platform document** — verify the exact declaration flow in-product before
  relying on it. ([腾讯新闻](https://news.qq.com/rain/a/20260427A05JSU00) · [36氪](https://www.36kr.com/p/3718169027638660))
- The underlying national regulation is primary and verifiable: **《人工智能生成合成内容标识办法》**
  ([gov.cn](https://www.gov.cn/zhengce/zhengceku/202503/content_7014286.htm)).

**Consequences for the 内容页 redesign**

1. **发布检查 must carry an AI-disclosure declaration** as a first-class checklist item — not a
   footer disclaimer. NN/g's explainable-AI research warns specifically that burying AI limits in
   a disclaimer does not work ([NN/g explainable AI](https://www.nngroup.com/articles/explainable-ai/)).
2. The declaration cannot be filled honestly without a **provenance record** — what the creator
   wrote, what AI proposed, and what the creator accepted. That record is also what creates the
   ownership effect documented by HaLLMark (writers' ownership rose **3.39 → 4.92** on a 7-point
   scale when AI-vs-human contribution was externalised) ([HaLLMark](https://www.cs.au.dk/~elm/pdf/hallmark.pdf)).
3. It **strengthens** the existing product rule: "AI proposes, human confirms" becomes the
   mechanism that keeps TopicAI on the *assisted* side of the line rather than the *substituted*
   side — which is why bulk-accepting AI proposals is not merely bad UX but potentially a
   compliance problem.

### 1.10 Work-tool craft signals

Craft write-ups from best-in-class work tools, per the brief. Read as **[C]** unless the vendor
published it (then **[P]**).

| Name | Source URL | What it gives us |
|---|---|---|
| Superhuman — *Rahul Vohra's 7 principles of game design* | https://blog.superhuman.com/game-design-not-gamification/ | First-party craft from a keyboard-first product. Directly relevant principles: **(1) create goals that are concrete, achievable, and rewarding** (their concrete goal is "Inbox Zero", and they *make it achievable* by wiping the slate clean during onboarding); **(2) design for nuanced emotion**; **(3) create rapid and robust controls** — *"In Gmail, if I do this too fast, I end up with 2 drafts… In Superhuman Mail, we pipeline our keystrokes so this can never happen."* They also run **live 1:1 concierge onboarding** to teach shortcuts so users *"never have to touch the mouse"* — an unusually aggressive version of NN/g's "help users adopt more efficient methods". [P] |
| Height — keyboard model and view model | https://1337skills.com/cheatsheets/height/ | ⚠️ **Third-party cheatsheet, not first-party — treat as weak.** Useful nonetheless as a concrete keyboard model for a work-item list: `Ctrl+K` command palette, `J`/`K` next/previous item, `X` select/deselect, `Enter` open, `Escape` back, `L` change list, `S`/`P`/`A`/`D` set status/priority/assignee/due, **`1`/`2`/`3`/`4` switch view (list/board/calendar/spreadsheet)**, `Ctrl+/` show all shortcuts. Also: **"Smart lists" are saved filters** that dynamically match tasks across all lists, and the product exposes list/board/calendar/spreadsheet/Gantt as **lenses on one dataset**. [X — unverified third-party] |
| Linear — *Design is more than code* | https://linear.app/now/design-is-more-than-code | Additional first-party Linear craft writing surfaced (not read in full in this pass — link recorded for follow-up). [X] |

**Two craft lessons worth taking directly from this section**

1. **Pipeline keystrokes so a fast keyboard user cannot create duplicate work.** Superhuman
   treats double-submission under fast input as a *defect class*, not user error. On a list where
   `X` selects and a bulk action follows, this matters. Note the current code already has an
   idempotency-key mechanism (`stableKey` in `ContentPage.tsx`, local observation) — that is the
   server-side half of the same idea; the client-side half (debounce/pipeline) still needs doing.
2. **Teach the accelerator at the moment of use.** Superhuman's answer to the "users plateau at
   mediocre performance" problem was *human* onboarding, not documentation. NN/g's cheaper version
   is in-context tooltips on the control itself ([NN/g complex applications](https://www.nngroup.com/articles/complex-application-design/), guideline 2).

### 1.11 Craft and Chinese-language sources from the third research pass

| Name | Source URL | What it gives us |
|---|---|---|
| Linear — *A calmer interface for a product in motion* | https://linear.app/now/behind-the-latest-design-refresh | First-party design-refresh write-up. Two rules worth stealing verbatim: **"Don't compete for attention you haven't earned"** — they dimmed the sidebar and cut icons so *"the main content area—where users work—[can] take precedence"*; and **"Structure should be felt not seen"** — borders were softened. [P] |
| Linear — *Output isn't design* | https://linear.app/now/output-isn-t-design | Karri Saarinen on why generation ≠ design, via Christopher Alexander's form/context **"fit"**: *"The hard part of design is rarely generating the form. It is understanding the problem well enough to know what and how something should exist at all."* The best intellectual backing for "AI proposes, human confirms". [P] |
| **Linear — How we built Triage Intelligence** | https://linear.app/now/how-we-built-triage-intelligence | **The single most on-point AI-suggestion UX write-up found anywhere.** Three transferable rules: (1) suggestions **reuse the product's own visual language**; (2) *"we're careful not to blur the line between issue metadata set by humans or rules and suggestions"* — **human-set and AI-suggested data must stay visually distinguishable**; (3) hovering a suggestion reveals the model's reasoning in plain language **plus alternative suggestions**, and long AI work gets a **thinking-state timer and a full thinking panel**. [P] |
| Linear — Select issues / Filters / Custom Views / Display options | https://linear.app/docs/select-issues · /docs/filters · /docs/custom-views · /docs/display-options | The canonical dense-list interaction model: `J/K` or `↑/↓` to move, `X` to select, `Shift+↑/↓` to extend, `Cmd/Ctrl A` select-all, `Esc` to clear, `Cmd/Ctrl K` to act, `Alt/Opt ±` to reorder; filters **round-trip into the URL** (*"only the main filters are included"*); `Alt/Opt V` saves the current view as a named object; and display options separate **"modify for my view only"** from **`Set as default`** (workspace-wide) and `Reset to default`. [P] |
| Linear Method — introduction / write-issues / manage-design-projects | https://linear.app/method/introduction · /write-issues-not-user-stories · /manage-design-projects | The philosophy layer: *"Build for the creators"*, *"Simple first, then powerful"*, **"Don't invent terms"**; issue titles written to be scannable **in a list**; and *"verify the problem before designing"* with "explore designs" as a discrete placeholder step — which mirrors the 证据采访 stage. [P] |
| NN/g — Data Tables: Four Major User Tasks | https://www.nngroup.com/articles/data-tables/ | Four core tasks (find, compare, view/edit a row, act on records); **the first column must be a human-readable identifier**; and critically: a **non-modal panel beats a modal for editing a record**, because a modal *"will cover adjacent records… and the user won't be able to reference or copy data from a similar record"* while users genuinely *"refer to existing data in other records while they edit"*. [R] |
| WAI-ARIA APG — Grid (**Layout Grid** sub-section) | https://www.w3.org/WAI/ARIA/apg/patterns/grid/ | The authoritative basis for a keyboard-navigable list: grouping interactive elements so *"only one element in the entire grid is in the tab sequence… can dramatically reduce the number of tab stops"* and prevents users being *"effectively trapped in the list"*. Reinforced by [Developing a Keyboard Interface](https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/): a composite widget is **one** tab stop. [P] |
| NN/g — Keyboard-Only Navigation | https://www.nngroup.com/articles/keyboard-accessibility/ | Tab order must follow visual order; **never remove the focus indicator** (*"catastrophic for keyboard users"* — replace it, don't delete it); every interactive element tabbable; provide skip-nav. [R] |
| **Ant Design — 列表页 (list page spec)** | https://ant.design/docs/spec/research-list-cn | The **official Chinese design-system answer to "too many filters"**: the 双栏布局 places the filter module in a **side rail** — *"将数据过滤模块放置在侧栏，**当过滤条件过多**，横向空间充裕时使用"*. The direct, citable resolution of the filter-placement question for a Chinese product. [P] |
| 人人都是产品经理 — 工作项状态机设计 | https://www.woshipm.com/ai/6453231.html | A **three-question test for whether something deserves to be a status** (is it a stable stage rather than an action; is it mutually exclusive; does it change allowed actions/owner/metrics?), plus the crucial rule **状态 ≠ 结果** — *"状态负责定位，结果负责解释，角色负责归责"*. Directly governs the 状态 / 意图 / 进度 three-axis model. [C] |
| 人人都是产品经理 — 九类B端筛选组件 | https://www.woshipm.com/ucd/6294415.html | Separates **搜索 (输入类字段: user id, phone, nickname)** from **筛选 (选择类字段: status, owner, type)**; states AND is the B2B default; and requires condition groups to be **visually** grouped — *"避免依赖抽象的优先级规则"*. [C] |
| 掘金 — 得物商品状态体系 | https://juejin.cn/post/7320169913030574132 | The best real precedent for **draft isolation**: editing a live listing creates a 草稿 whose status is isolated from the live object — *"草稿状态与商品状态隔离，草稿状态变更不影响商品状态"* — and the list marks record type. [C] |
| 掘金 — B端筛选设计 | https://juejin.cn/post/7249179953357717564 | Collapsible / overlay / header filters **must** carry an "active filter" marker, otherwise *"用户可能遗忘当前有筛选条件"*; filter values must be remembered and personal filters saveable. [C] |
| 掘金 — 分步表单的迷思 | https://juejin.cn/post/7173561697247068191 | **step vs tab is a semantic conflict**, and the deciding criterion is **data dependency, not aesthetics** — a step bar implies *"用户无法跳过某个步骤"*, so purely parallel content should use visual sections instead. [C] |
| Todoist — Introduction to filters | https://www.todoist.com/help/todoist/features/introduction-to-filters-V98wIH | Saved filters as named queries, plus **Filter Assist**: *"describe what you want in plain language, and it'll write the query for you."* And a vendor-documented failure mode: *"If you rename a project, any filters that reference the old project name will stop working."* [P] |
| Superhuman — How to build a remarkable command palette · Built for speed | https://blog.superhuman.com/how-to-build-a-remarkable-command-palette/ · https://blog.superhuman.com/superhuman-is-built-for-speed/ | The best engineering write-ups of palette **latency, ranking and action modelling**, plus the **100 ms interaction-latency budget** for a keyboard-first tool. [P] |
| NN/g — "Powered by AI" Is Not a Value Proposition | https://www.nngroup.com/articles/powered-by-ai-is-not-a-value-proposition/ | Naming AI as the selling point does not communicate value to users. [R] |
| NN/g — Designing AI Agents | https://www.nngroup.com/articles/designing-ai-agents/ | Four lessons from studying an agent: discoverability, reuse of familiar patterns, care with personal data, and **protect user autonomy**. [R] |
| arXiv:2506.08872 — cognitive debt in LLM-assisted writing | https://arxiv.org/abs/2506.08872 | Peer-reviewed EEG study: LLM-assisted writers showed the **weakest brain connectivity and the lowest self-reported ownership of their own essay**. The empirical case for forcing an explicit human confirmation step — what is being protected is **ownership**, not just accuracy. [P] |

---

## 2. Applicable principles & patterns

74 principles, grouped by surface so a reader can work one area at a time. If you read only one
thing, read these twelve:

| # | The change | Principle |
|---|---|---|
| 0 | **发布检查 must carry an AI-disclosure declaration** — 小红书 reportedly requires proactive AI-content labelling, and the national labelling rule is primary law. Not a footer disclaimer. | §1.9, §2.54 |
| 1 | Make `/content` a real two-pane list-detail at ≥840 px, single-pane below — and never two dense panes at 600–839 px. | §2.1, §2.36–37 |
| 2 | Put **status + current stage + last activity** in every row; today they are in the contract but unrendered. | §2.9 |
| 3 | Render a **designed placeholder detail pane** when no project is selected, not blank space. | §2.2 |
| 4 | Group by stage by default; status tabs + search + sort first; **no facet grid yet**. | §2.18, §2.41 |
| 5 | Encode status as **icon + label + colour**, never colour alone. | §2.38 |
| 6 | Cap the list pane at ~320–360 dp and give the width to the workspace. | §2.40 |
| 7 | **Two disclosure levels max**: row → current stage. Prior stages become read-only summaries. | §2.7, §2.42 |
| 8 | Unify every AI proposal into **one proposal-card component**: proposed value + one-line why + 确认 / 改一下 / 不用. | §2.21, §2.42 |
| 9 | Drive the surface from a **four-way request state** (`loading / empty / error / data`), never `items.length === 0`. | §2.43 |
| 10 | Confirm per **fact / scope / publish / long-term-memory decision** — **never per AI sentence** — and make each confirmation *checkable*. | §2.48–49 |
| 11 | Bulk actions: **contextual bar, page-scoped select-all, scope changes clear selection, never confirm AI output**. | §2.20 |

### A. Structure: list ↔ detail

**1. Make `/content` a genuine list-detail surface on wide screens and a drill-in surface on narrow ones — not a route change dressed up as both.**
Material 3 specifies exactly this: 1 pane below 600 dp, 2 panes at 840 dp+, with a *placeholder/empty detail pane* when nothing is selected (https://m3.material.io/foundations/layout/canonical-examples/list-detail). Windows gives the same rule with a different number — stacked at ≤640 epx, side-by-side at ≥641 ([Windows list/details](https://learn.microsoft.com/en-us/windows/apps/develop/ui/controls/list-details)).
→ **So we should** keep `/content/:projectId` as a real URL (deep-linkable, as today) but on ≥~1000 px render it as the right pane of a two-pane layout, and reserve the full-page route for narrow viewports instead of always navigating away from the list.

**2. When nothing is selected in the two-pane layout, the detail pane must show a purposeful placeholder — never blank space.**
Material: *"If no item is selected… the detail pane displays an empty state."* ([M3 list-detail](https://m3.material.io/foundations/layout/canonical-examples/list-detail)). Carbon requires the empty state to **replace** the element that would have rendered, including headers ([Carbon empty states](https://carbondesignsystem.com/patterns/empty-states-pattern/)).
→ **So we should** design a real "select a project" / "start your first project" pane that carries the primary CTA, rather than an empty grey rectangle.

**3. Always show which project is selected, and keep that selection visible in the list pane.**
Apple: *"To support navigation, persistently highlight the current selection in each pane that leads to the detail view"* ([HIG split views](https://developer.apple.com/design/human-interface-guidelines/split-views)). Material notes selection state appears **only in the list view of a two-pane layout** and a back button appears **only in single-pane** ([M3](https://m3.material.io/foundations/layout/canonical-examples/list-detail)).
→ **So we should** add an explicit selected/current row state, and stop rendering a "返回" affordance in the two-pane case where it is meaningless.

**4. Let creators open a project without losing their place — prefer a side peek over a full-page navigation for lightweight inspection.**
Notion's *"Open pages in"* offers **side peek** (detail on the right, *"the rest of the database view continues to be interactive"*), **center peek**, or **full page** ([Notion](https://www.notion.com/help/views-filters-and-sorts)).
→ **So we should** make row click a **side-peek preview** by default and require a deliberate "打开工作台" action to enter the full multi-stage workspace — the workspace is heavy enough (7-stage loop) that accidental entry is costly.

**5. Preserve per-project workspace state (scroll position, which stage panel is open) when switching projects.**
Material: *"In most cases, a state should be saved when navigating between detail views… Detail views should retain their scroll position when navigating to other items"* ([M3](https://m3.material.io/foundations/layout/canonical-examples/list-detail)).
→ **So we should** key workspace UI state by project id and restore it, instead of remounting cold — the current code remounts via `key={workspace.current_version?.id ?? ...}` (`ContentPage.tsx` L440).

**6. Assume the creation loop is NOT linear, and design navigation that admits it.**
NN/g's complex-application guideline 3 is *"Provide flexible and fluid pathways"* — avoid rigid linear workflows; let users **skip ahead, loop back, and move from any step to any other** ([NN/g](https://www.nngroup.com/articles/complex-application-design/)). NN/g's wizard guidance says wizards suit *occasional* processes and become *"annoying and overly controlling"* on repeat use, and are *"not gracefully interruptible"* ([NN/g wizards](https://www.nngroup.com/articles/wizards/)).
→ **So we should** keep `nextStepGuide()`'s single recommended action as the **default path**, but expose the full stage list as a **persistent, clickable outline** with clear completed/current/locked marks — the current collapsible `workspace-outline` (`ProjectWorkspace.tsx` L454) is the right seed; it needs stage status, not just collapse.

**7. Do not exceed two disclosure levels in the workspace — and make each stage screen answer exactly one discrete question.**
NN/g: *"designs that go beyond 2 disclosure levels typically have low usability because users often get lost when moving between the levels"* ([progressive disclosure](https://www.nngroup.com/articles/progressive-disclosure/)). The "One Thing Per Page" pattern defines the unit precisely: not one field, but **one discrete question** — *"An address form has multiple fields, but it's a single, discrete question that is being asked of the user"* — and it reports **"an extra 2 million orders a year"** after Just Eat split a single-page accordion checkout into per-step screens ([Smashing](https://www.smashingmagazine.com/2017/05/better-form-design-one-thing-per-page/)). The same article's reason #9 is directly relevant: **amending a detail is easier when it lives on its own addressed page** than when the user is dropped halfway down a long page.
→ **So we should** audit the current workspace for depth (project list → workspace → stage panel → candidate segment → per-segment action → modal is already ≥4 levels), collapse the inner levels by rendering candidate segments **inline with their own confirm/reject/replace actions**, and make each stage screen answer one question — which is exactly what `nextStepGuide()` already promises but the surrounding UI does not yet enforce (`ProjectWorkspace.tsx` L99–183, local observation).

**8. Every disclosure must advertise what is behind it.**
NN/g: it must be *"obvious how users progress"* and the trigger must *"set clear expectations"* — strong information scent ([progressive disclosure](https://www.nngroup.com/articles/progressive-disclosure/)). The current code uses 展开/收起 `<span className="caret">` toggles (`ProjectWorkspace.tsx` L440, L449).
→ **So we should** replace generic 展开/收起 with labels naming the content ("查看 5 个阶段" / "查看写作提醒 (2)"), so the control itself is informative.

### B. Information hierarchy & density for a list of work items

**9. Put `status` and progress *in the row*, because they are the creator's primary question.**
Today the row shows title + intent label + next-action label only, while `status` and `calibration_state` exist in the contract and are unused (`content.ts` L120; `ContentPage.tsx` L338–360 — local observation). Ant Design states the list's design goals as *"让列表易于扫读"* (make the list easy to scan) and *"快速查找列表中的对象"* ([Ant Design 数据列表](https://ant.design/docs/spec/data-list-cn/)); NN/g's complex-app guideline 8 is *"Make important information visually salient"*, and notes that **removing** non-essential elements is often more effective than adding emphasis ([NN/g](https://www.nngroup.com/articles/complex-application-design/)).
→ **So we should** show a compact **status chip + current-stage indicator + last-updated** per row, and drop decorative row chrome to pay for it.

**10. Prefer a List (row) layout over cards for the default project list, and offer Table only if creators actually compare projects.**
Ant Design: `表格 Table` emphasises 浏览性 (matrix/comparison), `列表 List` balances browsing and display for fast vertical scanning and is right for constrained containers, `卡片列表 Card list` emphasises 展示性 with a grid and no particular reading order ([Ant Design](https://ant.design/docs/spec/data-list-cn/)). The independent decision guide agrees: table for attribute comparison/sortable columns, list for reading down, cards for standalone items ([uxpatterns.dev](https://uxpatterns.dev/pattern-guide/table-vs-list-vs-cards)).
→ **So we should** keep the existing row list as the default (it is already the right shape), add a **density toggle**, and *not* convert to cards — cards would waste the vertical space that status and next-action need.

**11. Design for information density, not visual density — and treat latency as a density feature.**
Ström separates visual density from information density and defines overall density as **value ÷ (time × space)**; the HN thread's most repeated praise was responsiveness ("Bloomberg's Terminal… loads data almost instantaneously… that's Terminal's real superpower") ([Ström](https://matthewstrom.com/writing/ui-density/); [HN](https://news.ycombinator.com/item?id=43925732)).
→ **So we should** optimise the list for *scanning speed* (one line of status truth per row, instant filter/sort with no spinner) rather than for whitespace, and budget the redesign's effort toward perceived latency, not decoration.

**12. Create hierarchy with colour and weight, not size — and never use grey text on a coloured surface.**
Refactoring UI's tactic #1: *"Use color and weight to create hierarchy instead of size."* Concretely: a dark-but-not-black colour for primary content, **one** grey for secondary, a lighter grey for ancillary, and **at most two font weights**; avoid weights under 400 for small UI text ([Refactoring UI tip #1](https://medium.com/refactoring-ui/7-practical-tips-for-cheating-at-design-40c736799886)). Tactic #2 warns that *"making text a lighter grey is a great way to de-emphasize it on white backgrounds, but it doesn't look so great on colored backgrounds"* — the working mechanism is reduced contrast, so on a coloured chip use white at reduced opacity or a hand-picked same-hue colour instead ([Refactoring UI](https://medium.com/refactoring-ui/7-practical-tips-for-cheating-at-design-40c736799886)). NN/g corroborates the de-emphasis approach: *"making important information stand out does not always mean adding emphasis… Removing nonessential elements can be equally or even more effective"* ([NN/g](https://www.nngroup.com/articles/complex-application-design/)).
→ **So we should** build the status chip and metadata tiers from a fixed 3-grey + 2-weight scale (never font-size alone), and if status chips carry colour, de-emphasise their secondary text by contrast/opacity — never by dropping to a light grey on the tinted chip.

**13. Be honest about "how many steps are left", and use the creator's words, not backend words.**
NN/g's wizard recommendation 2 is to *"communicate a clear mental model… displaying a list or a diagram of the steps"*; recommendation 4 says generic labels like *Next* have weak information scent ([NN/g wizards](https://www.nngroup.com/articles/wizards/)). NN/g's status-tracker guideline 3 is *"status updates should use plain language… backend codes and internal jargon… mean nothing to the user"* ([NN/g](https://www.nngroup.com/articles/status-tracker-progress-update/)). The current code already does this well (`'第 1 步，共 5 步'`, `ProjectWorkspace.tsx` L115) and explicitly maps internal refs via `readableRef` (L104–107).
→ **So we should** keep and extend that discipline to the **list** surface (a stage name like "等待观察窗口" rather than a `next_action` enum), never emitting raw contract values.

### C. State model: filtering, sorting, grouping, saved views

**14. Start with *simple* filters, and only add facets if creator research proves the need.**
NN/g: faceted navigation is *"more expensive to create and maintain"* and *"adds interaction cost by presenting users with more options to comprehend and manipulate"*, so *"it's wise to make sure that users truly do need faceted navigation"* ([NN/g filters vs facets](https://www.nngroup.com/articles/filters-vs-facets/)).
→ **So we should** begin with **status tabs** (进行中 / 待复盘 / 已发布 / 已归档) plus intent as a secondary filter, not a full facet panel — and measure before expanding.

**15. Never bury multi-category filters inside a menu, and always show that filters are applied.**
Carbon: *"Multiple categories should never be put within a menu or dropdown"*; if filters are hidden behind a drawer/dropdown, the **closed state must show the number of applied filters and offer clearing without reopening** ([Carbon filtering](https://carbondesignsystem.com/patterns/filtering/)).
→ **So we should** render status/intent filters as visible chips or a filter bar, and if we ever collapse them, show `已筛选 2 项 · 清除` persistently.

**16. Use batch-apply filtering for slow/compound narrowing, instant-apply for single-category narrowing.**
Carbon: batch filtering suits multiple selections across categories and slow data return; instant updates suit one category or a single expected selection ([Carbon filtering](https://carbondesignsystem.com/patterns/filtering/)).
→ **So we should** make status tabs instant (local/cheap) but any multi-field advanced filter batch-applied with an explicit 应用 button, so a local-first app never flickers through five queries.

**17. Treat "saved view" as a named, inspectable object with an explicit modified state — not a hidden filter preset.**
The saved-view pattern requires: expose **active name, visibility, default status, and modified-from-saved state in text, not only tab styling**; keep **temporary tweaks separate from updating the saved definition**; store the **canonical definition, not row IDs**; and handle **invalid fields / permission-denied filters** explicitly ([UX Patterns Guide](https://uxpatternsguide.com/patterns/saved-view/)). Polaris implements exactly this as "view management" inside index filters ([Polaris](https://polaris.shopify.com/components/selection-and-input/index-filters)).
→ **So we should** ship a small set of **built-in default views** (未被 AI 阻断 / 需要我确认 / 等待观察窗口 / 本月已发布) before allowing user-created views, and always show the view name + a "已修改" marker when the current settings drift. Adopt Polaris's concrete shape: views rendered as **tabs**, with the default view **locked** (not renamable/deletable) and every user view carrying rename / duplicate / delete, plus explicit "no filters" and "no results" states ([Polaris](https://polaris.shopify.com/components/selection-and-input/index-filters)).

**18. Grouping is often better than filtering for a status-heavy list, and Notion-style sub-grouping is a cheap second axis.**
Notion supports independent group *and* **sub-group** per view ([Notion](https://www.notion.com/help/views-filters-and-sorts)). Carbon separates grouping/filtering concerns in its data-table guidance ([Carbon data table](https://carbondesignsystem.com/components/data-table/usage/)).
→ **So we should** default the list to **grouped by stage** (inbox → preparing → creating → ready_to_publish → published → awaiting_review → settled, matching `ProjectStatus` in `content.ts` L1–8) with counts per group, since "where is this stuck?" is the real question, and let status filtering be an override.

### D. Actions, CTAs, and bulk operations

**19. Exactly one primary CTA per surface; everything else is secondary, tertiary, or overflow.**
Carbon's empty-state guidance warns that multiple simultaneous empty states should use a **tertiary** button *"to avoid scenarios with multiple primary action buttons in the UI"* ([Carbon](https://carbondesignsystem.com/patterns/empty-states-pattern/)). Ant Design's data-list spec separates 新建 / 批量操作 / 导航至详情 / 删除 as distinct action families ([Ant Design](https://ant.design/docs/spec/data-list-cn/)).
→ **So we should** keep 「新建项目」 as the single primary on `/content`, make 「打开工作台」 the row-level primary, and demote 归档/删除/素材 into a row overflow menu.

**20. Add bulk operations only after selection is a first-class, keyboard-reachable state — and never let them mutate AI-proposed content.**
NN/g's three bulk-action guidelines are: **provide a Select All option, use a contextual action bar, and give clear feedback with the option to undo** ([NN/g](https://www.nngroup.com/videos/bulk-actions-design-guidelines/)). Ant Design treats 批量操作 as a named, separate concern with its own list toolbar ([Ant Design](https://ant.design/docs/spec/data-list-cn/)). The Marigold bulk-actions pattern states the governing principle as **"users act only on what they can see"**, and derives concrete mechanics from it: the header checkbox selects **the current page only** (never the whole result set behind pagination); **changing page, filter, search, sort, or page size clears the selection**; a confirmation dialog **names the exact count**; a result toast reports precisely what happened; actions are **verb-named** ("Publish", "Delete") never "Apply"/"OK"; actions are ordered **safest → most consequential with destructive last and visually separated**; and **while a selection exists, per-row actions are disabled so the bar holds the only pressable scope** ([Marigold UI](https://www.marigold-ui.io/patterns/user-input/bulk-actions)). HAX Guideline 16 requires conveying the consequences of user actions ([HAX](https://www.microsoft.com/en-us/haxtoolkit/library/)).
→ **So we should** allow only **low-risk bulk actions** (归档、打标签、加入系列), with a floating action bar showing the count and a clear-selection control; bulk actions must **never** auto-confirm evidence, publish, or promote a candidate rule/viewpoint/series into long-term memory, because those are exactly the confirmations the product rule reserves for a human, one at a time.

### E. AI suggestion UX (the core rule)

**21. Every AI proposal must render as a proposal, not as content — with the confirmation affordance adjacent and the dismissal affordance equally available.**
HAX Guideline 8 is *"Support efficient dismissal"* and Guideline 9 is *"Support efficient correction"* ([HAX](https://www.microsoft.com/en-us/haxtoolkit/library/)). PAIR: *"Give users a way forward, according to the severity of possible outcomes… give users the opportunity to teach the system the prediction that they were expecting"* ([PAIR](https://pair.withgoogle.com/chapter/explainability-trust/)). The current `start-inference` banner already does this with `「不对，我自己选」` (`ContentPage.tsx` L413–438 — local observation).
→ **So we should** generalise that exact pattern into a reusable **proposal card** (proposed value + why + 确认 / 改一下 / 不用) and use it for field candidates, series, viewpoints, sections, and publish checks, instead of one-off UIs per stage.

**22. Show *why* on demand, keep it short, and never dump a model's full reasoning.**
HAX Guideline 11: *"Enable the user to access an explanation of why the AI system behaved as it did"* ([HAX](https://www.microsoft.com/en-us/haxtoolkit/library/)). PAIR: prefer **partial explanations** and *"just the aspects that impact user trust and decision-making"*; **specific-output explanations** ("why this output, now") connect explanations to actions ([PAIR](https://pair.withgoogle.com/chapter/explainability-trust/)).
→ **So we should** put a one-line, task-specific reason next to every proposal (the current `inference.reason` is the model), and gate the longer rationale behind a disclosure.

**23. Prefer categorical confidence — or n-best alternatives — over percentages.**
PAIR explicitly warns that **numeric confidence presumes statistical literacy** and that a *"misleadingly high confidence… may cause users to blindly accept a result"*, recommending **categorical buckets** (with a clear action per bucket) or **n-best alternatives** which *"prompt the user to rely on their own judgement"* ([PAIR](https://pair.withgoogle.com/chapter/explainability-trust/)). It also says: **if confidence isn't actionable, don't show it.**
→ **So we should** render `start_inference_confidence: 'high' | 'medium' | 'low'` (`content.ts` L133) as an **action-shaped label** ("我先按这个准备，你可以随时改" vs "我不确定——你选一个"), and never show raw probabilities.

**24. When the AI is unsure, it must say so and degrade — not guess.**
HAX Guideline 10: *"Engage in disambiguation or gracefully degrade the AI system's services when uncertain about a user's goals"* ([HAX](https://www.microsoft.com/en-us/haxtoolkit/library/)). The current product already encodes this in copy (`nextStepGuide`: *"数据不足时，系统会明确告诉你还不能下结论"*, `ProjectWorkspace.tsx` L143).
→ **So we should** make low-confidence proposals visually and interactionally distinct (e.g. present 2–3 alternatives as choices rather than one pre-filled value) rather than styling them like high-confidence ones.

**25. Tell the creator what their confirmation *does* — especially when it writes to long-term memory.**
HAX Guideline 16: *"Immediately update or convey how user actions will impact future behaviors of the AI system"*; Guideline 13 is *"Learn from user behavior"* and Guideline 17 is *"Provide global controls"* ([HAX](https://www.microsoft.com/en-us/haxtoolkit/library/)). Current copy does this (*"只有你确认过的结论，才会进入长期经验"*, `ProjectWorkspace.tsx` L159).
→ **So we should** label every long-term-memory action with its blast radius — e.g. 「确认后：以后每条内容都会参考这条经验」 — plus a visible, findable place to review and revoke what has been confirmed (the HAX "global controls" analogue).

**26. Keep a structured workbench; do not replace the workspace with chat.**
NN/g argues AI's intent paradigm reverses the locus of control and is error-prone, that *"clicking or tapping things on a screen is an intuitive and essential aspect of user interaction that should not be overlooked"*, and predicts a **hybrid** UI ([NN/g AI paradigm](https://www.nngroup.com/articles/ai-paradigm/)). Linear's own framing is the **workbench** where *"agents operate with clear guidelines and output is reviewed and approved"* ([Linear](https://linear.app/blog/design-for-the-ai-age)).
→ **So we should** keep the intent-driven stage workspace as the primary surface and confine any conversational AI to a **scoped, stage-bound** assistant that fills the current form — never a global chat that can silently advance state.

**27. Never let an AI proposal pass through a loading state that looks like a confirmed value.**
NN/g's empty-state research documents the failure mode directly: a system that shows **"No records"** and then replaces it with content *"creates severe distrust… trigger-happy users never see the relevant content"* ([NN/g empty states](https://www.nngroup.com/articles/empty-state-interface-design/)).
→ **So we should** render AI-suggested fields in a visibly *unconfirmed* style (proposal chrome + 待确认 label) from the first frame, so a pending suggestion is never mistakable for saved truth.

### F. States: empty, loading, error, partial

**28. Design four distinct empty/partial states for the list surface, not one.**
Carbon names three types — **no data**, **user action** (no search results), **error management** (permissions / systems / configuration / unsupported action) — and maps each to a goal ([Carbon empty states](https://carbondesignsystem.com/patterns/empty-states-pattern/)). NN/g's three guidelines are: communicate system status, provide learning cues (pull revelations), and provide direct pathways to key tasks ([NN/g](https://www.nngroup.com/articles/empty-state-interface-design/)).
→ **So we should** implement: (a) **no projects yet**, (b) **filters returned nothing** → *"没有符合条件的内容，试试清除筛选"* + a clear-filters action, (c) **load failed** → retry + reason, (d) **partial data** (e.g. workspace loaded but snapshot metrics missing) → show what exists and name exactly what is missing. Today only (a) and (c) exist (`ContentPage.tsx` L308–321, L391).

**29. An empty state must replace the list wholesale — never leave the table header/footer with nothing under it.**
Carbon: *"Empty states should replace the element that would ordinarily show. For example, an empty state for a table would replace the table and the column headers and footer should not be present"* — this also prevents screen readers announcing the whole table before the message ([Carbon](https://carbondesignsystem.com/patterns/empty-states-pattern/)).
→ **So we should** swap the whole list region (toolbar, group headers, count) for the empty state, keeping the toolbar only when it is needed to *undo* the filter that caused emptiness.

**30. Match feedback style to duration — animation under 100 ms makes the app feel slower, not faster.**
Ström's perceptual bands: **<100 ms** should have no animation (it breaks the illusion of simultaneity); **100 ms–1 s** needs visual bridging; **1–10 s** needs an indeterminate indicator; **10 s–1 min** needs a determinate one; **>1 min** should let the user leave and be notified ([Ström](https://matthewstrom.com/writing/ui-density/)).
→ **So we should** remove transition animations from list selection and tab switching, and reserve progress UI for the genuinely slow operations (publish check, LLM-backed candidate generation).

**31. For long, silent stages, publish low-granularity progress rather than nothing.**
NN/g guideline 9: *"For processes that take a long time, provide regular updates, even if they are of low granularity"* — the passport-office example ("Joined the processing queue") *"helps users feel that their application is in progress"*; silence makes users *"lose trust in the status tracker"* ([NN/g](https://www.nngroup.com/articles/status-tracker-progress-update/)).
→ **So we should** make 等待观察窗口 (the observation window) a first-class, dated timeline visible on both the list row and the workspace, with an explicit "下次检查时间", so a waiting project never looks abandoned.

**32. Show the history, newest-first, in the creator's language — and delete stale "next steps".**
NN/g guidelines 2 and 11: prioritise the latest update, and **show previous updates with dates**; also remove content that is no longer relevant, because a stale *Next steps* panel actively damages trust ([NN/g](https://www.nngroup.com/articles/status-tracker-progress-update/)).
→ **So we should** render the project's stage history as a reverse-chronological, plain-language log in the workspace, and ensure any "下一步" text is derived from current state (as `nextStepGuide()` does) rather than persisted copy that can go stale.

### G. Keyboard & mobile

**33. Make the list and the workspace fully operable by keyboard, following ARIA APG patterns — and make shortcuts discoverable.**
WAI-ARIA APG defines required keyboard interaction for listbox/grid/combobox/toolbar ([APG patterns](https://www.w3.org/WAI/ARIA/apg/patterns/)). NN/g's complex-app guideline 2 is *"Help users adopt more efficient methods"* — users *"plateau at mediocre performance"* and **satisface**, so accelerators must be surfaced **in context** ([NN/g](https://www.nngroup.com/articles/complex-application-design/)).
→ **So we should** implement ↑/↓ + Enter to move through projects, `/` to focus search, and Cmd/Ctrl+K for a command palette, then surface shortcuts **inside** the UI (tooltips on the relevant controls), not only in a help page.

**34. A command palette is worth adding for *actions*, not just search — but it must not become the only path.**
The pattern write-up documents four non-search uses: **quick entry**, **contextual insert**, **grouping/nesting**, and **palettes inside palettes** ([Command Palette Interfaces](https://philipcdavis.com/writing/command-palette-interfaces)).
→ **So we should** scope the palette to navigation + low-risk actions ("打开下一条需要我确认的内容", "记录发布", "回填表现"), keeping every one of them reachable by mouse too — accessibility and discoverability both require the visible path to exist.

**35. Mobile is a single-pane drill-in, not a squeezed two-pane — and dense surfaces must not be truncated into illegibility.**
Apple: *"Prefer using a split view in a regular — not a compact — environment… it's difficult to display multiple panes without wrapping or truncating the content, making it less legible"* ([HIG](https://developer.apple.com/design/human-interface-guidelines/split-views)). Material/Windows agree on the stacked fallback ([M3](https://m3.material.io/foundations/layout/canonical-examples/list-detail); [Windows](https://learn.microsoft.com/en-us/windows/apps/develop/ui/controls/list-details)).
→ **So we should** on mobile show the list full-screen, navigate to the workspace full-screen with a back button, and **collapse each workspace stage to one decision per screen** (aligning with the existing "one action" copy); do not attempt a mini two-pane.

### H. Structural rules verified in a second research pass

**36. Never combine a back button with a selected-list state — they belong to different layouts.**
Material 3: the back button appears **only in single-pane** layouts; the selection highlight appears **only in two-pane** layouts ([M3 list-detail](https://m3.material.io/foundations/layout/canonical-examples/list-detail)).
→ **So we should** render a back affordance and *no* row highlight on mobile, and a highlighted row with *no* back button on desktop — the current page shows 返回 in both modes (`ProjectWorkspace.tsx` `onBack`, local observation).

**37. On resize, keep the detail and hide the list when collapsing; restore both when expanding.**
Android's window-size-class rules: narrowing an expanded list-detail view **keeps the detail pane and hides the list**; widening restores both **with the item still selected** ([Android canonical layouts](https://developer.android.com/develop/adaptive-apps/guides/canonical-layouts)).
→ **So we should** make `/content/:projectId` the single source of truth for "which project is open" so a resize, rotation, or split-screen change never drops a creator out of stage 6.

**38. Encode status with colour *and* icon — never colour alone.**
NN/g's controlled comparison found users **~37% faster** finding list items when indicators varied in **both colour and icon** versus text alone; text-only was **57% slower** than the best condition, and **icon-only was marginally faster than colour-only**. NN/g also warns that *"relying on color alone runs the risk of failing color-blind users."* **Scope caveat:** all four tested pages were **mobile**; NN/g did not measure desktop and only speculates the effect would hold or grow there ([NN/g](https://www.nngroup.com/articles/visual-indicators-differentiators/)).
→ **So we should** render 状态 and 意图 as **icon + label + colour** chips, never bare coloured dots — and treat this as an accessibility requirement, not only a speed optimisation. Treat the **解决 / 分享 / 记录** axis as product-specific vocabulary needing its own documented legend, since **no design-system precedent for it was found**.

**39. Density is a set of discrete sizes with matching rules, not a slider.**
Carbon ships **five row sizes**, requires the **header row size to match the body**, and reserves extra-large for **two-line rows** ([Carbon data table](https://carbondesignsystem.com/components/data-table/usage/)); GitLab ships a **condensed** variant explicitly for *"data heavy and text only"* content ([GitLab Table](https://design.gitlab.com/components/table/)).
→ **So we should** pick one row height that fits a two-line content item and apply it consistently, then expose a **comfortable/compact toggle** rather than an always-expanded page.

**40. Give the primary work surface the majority of the width and cap the list pane.**
Carbon: give the table the most width on the page and never cram dense data into a narrow container ([Carbon](https://carbondesignsystem.com/components/data-table/usage/)); M3's supporting pane is a fixed **360 dp** ([M3 supporting pane](https://m3.material.io/foundations/layout/canonical-examples/supporting-pane)).
→ **So we should** cap the project list pane at roughly **320–360 dp** and give the remaining width to the multi-stage workspace — the current page gives the workspace the full width and the list none, which is the other extreme.

**41. Match filter machinery to data complexity, not to ambition.**
GitLab's **1–5 complexity ladder** maps data complexity to components: search → +sorting → +tabs → +dropdowns → full filter component ([GitLab filtering](https://design.gitlab.com/patterns/filtering/)). GitLab also separates the jobs: **search for finding a specific known item, filters for narrowing by parameters**.
→ **So we should** ship **status tab-strip + search + sort (≈complexity 3)** first, and add the 意图 × 阶段 facet grid only once the list regularly exceeds one screen — which matches NN/g's "establish real need first" warning ([NN/g facets](https://www.nngroup.com/articles/filters-vs-facets/)).

**42. Present AI field candidates as a reviewable summary list with per-row "Change" — not as a pre-filled form.**
GOV.UK's *Check answers* pattern is exactly this: a summary list of labelled values, each with its own **Change** link, shown before committing ([GOV.UK check answers](https://design-system.service.gov.uk/patterns/check-answers/)). GOV.UK's question-page guidance supplies the surrounding rules: a heading that **is** the question, a mandatory back link, and **"Continue" rather than "Next"**, left-aligned ([GOV.UK question pages](https://design-system.service.gov.uk/patterns/question-pages/)).
→ **So we should** replace the "AI 把这条读成「…」" inline banner plus separate edit field with a **proposal summary list** — each AI-suggested field as a row with its proposed value, a one-line reason, and 确认 / 改一下 — which unifies 意图确认, 字段候选, 发布检查, and 经验确认 under one reusable component.

**43. Choose skeleton vs. spinner vs. progress bar by measured duration, and never render a "no data" state during a request.**
NN/g: **<1 s → nothing; 2–10 s → skeleton (full page) or spinner (one module); >10 s → explicit progress bar**; **frame-only skeletons are discouraged** ([NN/g skeleton screens](https://www.nngroup.com/articles/skeleton-screens/)). Carbon agrees on skeleton-not-spinner for tables ([Carbon](https://carbondesignsystem.com/components/data-table/usage/)).
→ **So we should** drive the list and workspace from a **four-way request state** — `loading | empty | error | data` — never from `items.length === 0`, and render the project-list skeleton while the first fetch is in flight.

**44. Cap the toolbar, and push row actions into overflow only when there are three or more.**
Carbon: the toolbar takes **≤5 actions then overflow**; when a row's overflow would hold **fewer than three options, keep them inline as icon buttons**; a batch bar **disables** the inline row actions ([Carbon data table](https://carbondesignsystem.com/components/data-table/usage/), [Carbon overflow menu](https://carbondesignsystem.com/components/overflow-menu/usage/)). NN/g warns that hiding **key** actions in a kebab hurts usability but the icon itself is well recognised ([NN/g](https://www.nngroup.com/videos/overflow-menu-icons/)).
→ **So we should** keep the row's one true next action (继续创作 / 查看) as a **visible button** and place 归档 / 复制 / 删除 in a kebab with the destructive item below a divider.

**45. Declare which two fields survive on mobile.**
Shopify's `listSlot="primary"/"secondary"` designates which fields lead a stacked row so a desktop table **degrades into a stacked list** instead of becoming a horizontally scrolling table ([Shopify index-table](https://shopify.dev/docs/api/app-home/latest/patterns/compositions/index-table)).
→ **So we should** commit now to **title + status** as the mobile row, and render 意图 / 进度 / 素材 / series only inside the opened project.

**46. Do not add a third navigation level for series and viewpoints.**
NN/g: deep hierarchies are harder to use and **deep levels force generic labels** ([NN/g flat vs. deep hierarchy](https://www.nngroup.com/articles/flat-vs-deep-hierarchy/)).
→ **So we should** keep 系列 / 观点 / 观察清单 **inside** the project workspace — ideally as an M3 **supporting pane** ([M3](https://m3.material.io/foundations/layout/canonical-examples/supporting-pane)) rather than as routes like `/content/:projectId/series/:id`. **Caveat:** verify by task analysis that these panels are genuinely *contextual*; some are peers in the eight-stage loop, not supporting material, and forcing them into a pane would be wrong.

**47. Separate list rows with space and grouping, not with a border on every row.**
Refactoring UI's published chapter list includes *"Use fewer borders"*, *"De-emphasize to emphasize"*, *"Separate visual hierarchy from document hierarchy"*, *"Avoid ambiguous spacing"*, and *"Don't overlook empty states"* ([Refactoring UI](https://www.refactoringui.com/)). NN/g defines hierarchy as **contrast + scale + grouping**, verifiable with the **squint test** ([NN/g visual hierarchy](https://www.nngroup.com/articles/visual-hierarchy-ux-definition/)).
→ **So we should** make the project title the only high-contrast element per row, drop the per-row border, and verify the whole page with a squint test before shipping.

### I. Confirmation architecture (how to make "human confirms" actually work)

**48. Confirmation weight scales with stakes and reversibility — never with frequency.**
NN/g: confirmation dialogs *"stop working"* when overused, routine actions must not get one, and there should be **no default "Yes"** ([NN/g confirmation dialogs](https://www.nngroup.com/articles/confirmation-dialog/)). Agent-governance writing documents the mechanism: at volume *"the requests blur together and the brain does the sensible thing under repetitive load: it stops treating each one as a fresh decision"* ([WorkOS](https://workos.com/blog/approval-fatigue-agent-governance)).
→ **So we should** confirm per **fact**, per **scope change**, per **publish**, and per **long-term-memory decision** — and **never per AI-proposed sentence**. Rank by *consequence → reversibility → blast radius* ([practitioner ladder, weak source](https://jishuzhan.net/article/2058027233772146689)).

**49. Make the confirmation *checkable*, because opaque confirmation UI is what causes over-trust.**
This is the sharpest finding of the pass. A systematic review finds automation bias is driven by **verification complexity and cognitive load**, not by distraction: *the harder the AI output is to check, the more it is trusted* ([Lyell & Coiera](https://pmc.ncbi.nlm.nih.gov/articles/PMC7651899/)). Related: explanations alone often **fail** to reduce over-reliance and can backfire, so the usable lever is **user engagement / independent verification** ([Romeo & Conti 2025](https://doi.org/10.1007/s00146-025-02422-7)); and *"recommendations only upon request"* plus **asking users to commit to their own prediction first** mitigate overreliance ([MSR Aether review](https://www.microsoft.com/en-us/research/wp-content/uploads/2022/06/Aether-Overreliance-on-AI-Review-Final-6.21.22.pdf)).
→ **So we should** design 证据采访 and 意图确认 so the creator **states their own view before the AI reveals its proposal**, and make every proposal verifiable against a specific evidence record in one click. A confirm button over an unexplained blob is not a human check — it is a rubber stamp.

**50. Give every proposal a factual, non-anthropomorphic attribution linked to the real evidence record.**
Apple HIG requires an **Attribution** affordance, factual and objective, balancing too-specific against too-general ([Apple HIG](https://developer.apple.com/design/human-interface-guidelines/machine-learning)). Counterweight: NN/g finds **citations are rarely clicked** and are sometimes hallucinated, producing *"a false sense of reliability"* ([NN/g explainable AI](https://www.nngroup.com/articles/explainable-ai/)).
→ **So we should** write the reason **inline and unclickable-first** ("因为你在证据采访 #3 里说过…"), with the click only *deepening* to the source record — never a bare citation chip the creator must trust.

**51. Never print a raw confidence score; translate confidence into a consequence.**
Apple: *"If you're not sure how your confidence values correlate with the quality of your results, it's not a good idea to convey confidence to people"* ([Apple HIG](https://developer.apple.com/design/human-interface-guidelines/machine-learning)). PAIR reaches the same conclusion from the other direction ([PAIR](https://pair.withgoogle.com/chapter/explainability-trust/)).
→ **So we should** replace any percentage with actionable language: *"这个日期没有出现在你的证据采访里——确认或修正"*, and only ever show `high/medium/low` as an **action-shaped label**.

**52. Offer 2–3 genuinely different framings, not one oracle answer.**
Apple HIG's **Multiple options** pattern: multiple options *"give people a greater sense of control and can help bridge the gap between your model's predictions and what people actually want"* ([Apple HIG](https://developer.apple.com/design/human-interface-guidelines/machine-learning)). PAIR's **n-best** framing makes the same argument for low-confidence cases ([PAIR](https://pair.withgoogle.com/chapter/explainability-trust/)).
→ **So we should** in low-confidence states present **alternatives to choose between** rather than a single pre-filled value — which also satisfies HAX Guideline 10 (*scope services when in doubt*).

**53. Show the consequence *before* the click, confirm it *after*, and re-confirm past decisions separately.**
HAX Guideline 16 decomposes into **16A feedforward**, **16B feedback**, and **16C remind-of-a-past-action-and-reconfirm** ([HAX G16](https://www.microsoft.com/en-us/haxtoolkit/guideline/convey-the-consequences-of-user-actions/)).
→ **So we should** label the button with what it does — *"设为项目意图——之后所有草稿都要符合它"* — not "确定"; then state what it now constrains. **16C** is the missing piece for long-term memory: a returning creator should be *reminded* what a confirmed rule does before changing it.

**54. Keep a visible provenance trail so the creator can claim authorship — it is also the disclosure input.**
HaLLMark raised writers' ownership from **3.39 → 4.92** on a 7-point scale by externalising what AI vs human generated ([HaLLMark](https://www.cs.au.dk/~elm/pdf/hallmark.pdf)). This is also exactly the record 发布检查 needs for the AI-disclosure declaration (§1.9).
→ **So we should** mark, per section, **creator-written / AI-proposed / creator-accepted**, and surface that rollup at publish time.

**55. Make rejection a first-class, recorded, acted-on signal.**
PAIR: *"ask the user for feedback if they repeatedly reject AI outputs"*; explicit feedback should be acted on and persisted ([PAIR errors](https://pair.withgoogle.com/chapter/errors-failing/)). Grammarly's production lesson is the complement: a suggestion must be **correct *and* relevant**, and **stale cards must be hidden immediately** once the human fixes it themselves ([Grammarly](https://www.grammarly.com/blog/engineering/how-suggestions-work-grammarly-editor/)).
→ **So we should** record per-section reject/replace with a reason, **show what that signal changed**, and stop re-proposing a rejected angle within the same project.

**56. Prefer undo and versioning over more dialogs.**
NN/g: *"do go to great lengths to provide undo, because some user errors will remain despite even the best of confirmation dialogs"*, and users need a *"clearly marked emergency exit"* ([NN/g user control & freedom](https://www.nngroup.com/articles/user-control-and-freedom/)). Providing even slight modification ability raises adoption of an imperfect algorithm ([Dietvorst et al.](https://pubsonline.informs.org/doi/10.1287/mnsc.2016.2643)).
→ **So we should** keep superseded drafts and previously-confirmed facts versioned so a correction never orphans 发布记录 / 表现快照 evidence — and treat version restore as the primary safety net, with confirmation dialogs reserved for the irreversible.

**57. Keep a fully manual, non-AI path at every gate.**
Apple HIG Generative AI: **"Keep people in control… ensure they remain in charge of decision making"**, offer a **non-AI fallback**, and **disclose** where AI is used ([Apple HIG](https://developer.apple.com/design/human-interface-guidelines/generative-ai)). PAIR: the manual method is *"a safe and useful fallback"* and you must *"not create dead-ends when an AI feature fails"* ([PAIR](https://pair.withgoogle.com/chapter/feedback-controls/)).
→ **So we should** make 意图确认, 证据采访 and 候选内容 each **completable by typing from scratch**, with AI as an optional accelerator — and label that path plainly, as the current 「不对，我自己选」 already does.

**58. Do not humanise the system, and state what it cannot verify.**
NN/g: *"humanizing AI is a trap"*; users trust an AI **more** when it seems smart and **less** when it seems emotional ([NN/g humanizing AI](https://www.nngroup.com/articles/humanizing-ai/), [NN/g smarts over sentience](https://www.nngroup.com/articles/smarts-emotion-trust-ai/)). NN/g also finds **chat framing actively discourages error checking** ([NN/g](https://www.nngroup.com/articles/ai-chatbots-discourage-error-checking/)).
→ **So we should** label proposals as machine proposals in neutral copy — no persona, no "I think" — and state plainly what TopicAI cannot verify. ([Apple HIG](https://developer.apple.com/design/human-interface-guidelines/generative-ai) adds: never imply the content was authored by a human.)

### J. Keyboard and craft details from shipped work tools

**59. Pipeline keystrokes so fast keyboard input cannot create duplicate work.**
Superhuman treats accidental double-submission under fast input as a **defect class, not user error**: *"In Gmail, if I do this too fast, I end up with 2 drafts… In Superhuman Mail, we pipeline our keystrokes so this can never happen"* ([Superhuman](https://blog.superhuman.com/game-design-not-gamification/)).
→ **So we should** debounce/pipeline rapid keyboard actions on the list and the workspace. The server-side half already exists as the idempotency-key mechanism (`stableKey`, `ContentPage.tsx` — local observation); the client-side half (prevent duplicate dispatch) still needs building.

**60. Adopt a compact, well-known keyboard model rather than inventing one.**
Height's work-item model is a good template: `Ctrl+K` palette, `J`/`K` next/previous, `X` select/deselect, `Enter` open, `Escape` back, `L` change list, `1`/`2`/`3`/`4` switch view, `Ctrl+/` show all shortcuts ([Height cheatsheet — ⚠️ third-party, unverified](https://1337skills.com/cheatsheets/height/)). WAI-ARIA APG defines the required interaction contracts underneath ([APG](https://www.w3.org/WAI/ARIA/apg/patterns/)).
→ **So we should** map `J`/`K` + `X` + `Enter` onto the project list, use `1`/`2`/`3` for view/tab switching, and bind `Ctrl/Cmd+/` to a shortcut reference — reusing conventions creators may already know from other tools rather than inventing new ones.

**61. Make the goal concrete, achievable, and rewarding — and make it achievable by clearing the path.**
Superhuman's first game-design principle is goals that are *"concrete, achievable, and rewarding"*; notably, when a user is far from "Inbox Zero" during onboarding they **wipe the slate clean to make the goal achievable** ([Superhuman](https://blog.superhuman.com/game-design-not-gamification/)). NN/g's complex-app guideline 1 (*promote learning by doing*) and guideline 2 (*help users adopt more efficient methods*) point the same way ([NN/g](https://www.nngroup.com/articles/complex-application-design/)).
→ **So we should** express the per-project goal as one concrete, finishable statement (the existing 「第 N 步，共 5 步」 already does this well) and offer a **safe, consequence-free trial path** for a first project — the current 「还不知道第一篇做什么？」 starter panel (`ContentPage.tsx` L309–321) is a good seed for this.

### K. Craft rules from the third research pass

**62. Keep human-set and AI-suggested data visually distinguishable — including *after* acceptance.**
Linear states this as a deliberate discipline: *"we're careful not to blur the line between issue metadata set by humans or rules and suggestions from Triage Intelligence"*, and its suggestions reuse the product's own visual language rather than a special "AI" skin ([Linear Triage Intelligence](https://linear.app/now/how-we-built-triage-intelligence)).
→ **So we should** carry a **provenance chip that survives acceptance**, not just an "unconfirmed" highlight that disappears the moment the creator clicks 确认. This is the same record §1.9 needs for the disclosure declaration — one component, two jobs.

**63. Put the reasoning and the alternatives behind a hover, and give long AI work a real progress affordance.**
Linear: hovering a suggestion *"reveals the model's reasoning in plain language along with alternative suggestions"*, and long-running work shows a **thinking-state timer** plus a full thinking panel ([Linear](https://linear.app/now/how-we-built-triage-intelligence)). This is PAIR's "partial explanation on demand" made concrete, and it satisfies HAX Guideline 11 without cluttering the default view.
→ **So we should** show a one-line reason inline, reveal the fuller rationale + alternatives on hover/expand, and give 候选内容 generation a **timer**, not a bare spinner.

**64. Don't compete for attention you haven't earned; structure should be felt, not seen.**
Linear's refresh dimmed the navigation and reduced icon usage so the work area takes precedence, and softened borders on the principle that *"structure should be felt not seen"* ([Linear](https://linear.app/now/behind-the-latest-design-refresh)).
→ **So we should** mute the 状态/意图/进度 chips relative to the project title, and replace per-row borders with spacing — the same conclusion NN/g and Refactoring UI reach from other directions (§2.12, §2.47).

**65. A dense list is a composite widget with exactly ONE tab stop — never one per row.**
APG's Layout Grid exists precisely so that *"only one element in the entire grid is in the tab sequence"*, which *"can dramatically reduce the number of tab stops"* and prevents users being *"effectively trapped in the list"* ([APG Grid](https://www.w3.org/WAI/ARIA/apg/patterns/grid/), [APG keyboard interface](https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/)). Note this is also a **keyboard-trap** risk on a list that grows long.
→ **So we should** implement the project list with **roving tabindex** (one tab stop; arrows or `J`/`K` to move), and never give every row its own tab stop.

**66. Never delete or restyle away the focus indicator — replace it.**
NN/g: *"Removing the keyboard focus indicator is catastrophic for keyboard users"*; tab order must follow visual order ([NN/g keyboard-only navigation](https://www.nngroup.com/articles/keyboard-accessibility/)).
→ **So we should** keep a visible, high-contrast focus ring on every row, chip, and stage control — the current CSS defines `:focus-visible` for rows (`ContentPage.css` L77–78, local observation), which must be preserved and extended, not trimmed during the redesign.

**67. Edit in a non-modal panel; keep adjacent records visible.**
NN/g's table research: users *"refer to existing data in other records while they edit a record (as that helps them recognize, rather than recall reasonable value ranges)"*, and a modal *"will cover adjacent records"* ([NN/g data tables](https://www.nngroup.com/articles/data-tables/)). The list's first column must also be a **human-readable identifier**.
→ **So we should** open a project into the **side-by-side master-detail** layout (§2.1) rather than a dialog over the list, and make the project title the first, unambiguously readable field.

**68. Saved views must reference entities by id, and an invalid view must say so in-list.**
Todoist documents the exact bug: *"If you rename a project, any filters that reference the old project name will stop working"* ([Todoist](https://www.todoist.com/help/todoist/features/introduction-to-filters-V98wIH)). This is the same class of failure the saved-view pattern calls out for removed fields ([UX Patterns Guide](https://uxpatternsguide.com/patterns/saved-view/)).
→ **So we should** store view rules as ids/field references, and when a view becomes invalid, render *"这个视图引用的字段已失效"* rather than silently returning zero results.

**69. Filters belong in a side rail once there are many; and 搜索 must stay distinct from 筛选.**
Ant Design's list-page spec gives the official Chinese answer: put the filtering module in the **side rail** — *"当过滤条件过多，横向空间充裕时使用"* ([Ant Design 列表页](https://ant.design/docs/spec/research-list-cn)). Chinese practitioner guidance separates **搜索 (input-type fields: id, phone, nickname)** from **筛选 (selection-type fields: status, owner, type)**, and requires AND/OR to be shown as **visible condition groups** rather than implicit precedence ([woshipm](https://www.woshipm.com/ucd/6294415.html)).
→ **So we should** give 内容页 a collapsible left filter rail for the 状态 × 意图 × 进度 axes, keep the search box for free-text title lookup only, and never mix the two.

**70. Keep 状态, 意图, and 进度 as three orthogonal dimensions — and make 状态 earn its place.**
The three-question test for a status: is it a **stable stage** (not an action), is it **mutually exclusive**, and does it **change allowed actions / owner / metrics**? Plus the rule **状态 ≠ 结果** — *"状态负责定位，结果负责解释"* ([woshipm](https://www.woshipm.com/ai/6453231.html)). This maps cleanly onto the existing contract, where `status: ProjectStatus`, `content_intent: ContentIntent`, and `calibration_state` are already three separate fields (`content.ts` L1–18, L120 — local observation).
→ **So we should** render them as **three separate affordances**, never merge them into one badge, and resist adding new statuses that fail the three-question test.

**71. Editing a live/published record must create an isolated draft branch.**
得物's production model: editing a listed item produces a 草稿 whose status is isolated — *"草稿状态与商品状态隔离，草稿状态变更不影响商品状态"* ([掘金](https://juejin.cn/post/7320169913030574132)). The product's own 发布记录 / 表现快照 evidence depends on the published version staying frozen.
→ **So we should** make the workspace a **draft branch off the published record**, with the published snapshot immutable until an explicit publish action — which the `locked_publish_version_id` field already anticipates (`content.ts` L~140, local observation).

**72. Show the plain-language query, and let the natural-language entry produce the structured filter.**
Todoist's **Filter Assist** lets users *"describe what you want in plain language, and it'll write the query for you"* ([Todoist](https://www.todoist.com/help/todoist/features/introduction-to-filters-V98wIH)). This converts prompt-style input into a reviewable structured object rather than hiding the logic.
→ **So we should** keep the structured filter builder as the source of truth and, if we add natural-language filtering, **show the resulting structured filter for confirmation before applying it** — the same propose-then-confirm rule as the rest of the product.

**73. Numbered actions should follow action order, and no AI confidence score may gate a human step.**
Linear ordered Triage shortcuts by action order (1 accepts, 2 declines, 3 marks duplicate) ([Linear changelog](https://linear.app/changelog)). On gating: Chinese practitioner guidance citing the NIST AI RMF human-AI appendix is explicit — *"什么时候必须停下来，不能只看模型置信度"* ([woshipm](https://www.woshipm.com/ai/6447314.html)).
→ **So we should** bind 1/2/3 to 确认 / 改一下 / 不用, and **never** let a threshold on the model's confidence decide whether the human is asked — stakes decide that, not the score (§2.48).

**74. Don't sell the AI; sell what it lets the creator finish.**
NN/g: naming AI as the value proposition does not communicate value to users ([NN/g](https://www.nngroup.com/articles/powered-by-ai-is-not-a-value-proposition/)). NN/g's agent research adds: reuse familiar patterns and **protect user autonomy** ([NN/g designing AI agents](https://www.nngroup.com/articles/designing-ai-agents/)).
→ **So we should** keep the interface vocabulary about the creator's content (「先写下你真正经历过的一件事」) and never about the model — which the existing copy already does well.

---

## 3. Anti-patterns

| # | Anti-pattern | Why it is wrong here | Source |
|---|---|---|---|
| 1 | **A "no data" message shown while data is still loading.** | NN/g documents this as *"particularly harmful"*: users either wait and *"develop a severe distrust"*, or never see the content at all. With an LLM-backed workspace this is a live risk. | [NN/g empty states](https://www.nngroup.com/articles/empty-state-interface-design/) |
| 2 | **Three or more levels of progressive disclosure.** | *"Designs that go beyond 2 disclosure levels typically have low usability."* The current workspace stack (list → workspace → stage → segment → modal) is already deeper. | [NN/g progressive disclosure](https://www.nngroup.com/articles/progressive-disclosure/) |
| 3 | **Burying multi-category filters inside a dropdown.** | Carbon is explicit: *"Multiple categories should never be put within a menu or dropdown"*, and a hidden filter's closed state must still show the applied count. | [Carbon filtering](https://carbondesignsystem.com/patterns/filtering/) |
| 4 | **Shipping faceted navigation because it is impressive, not because it is needed.** | Facets add build/maintenance cost **and** interaction cost; NN/g says establish real need first. | [NN/g filters vs facets](https://www.nngroup.com/articles/filters-vs-facets/) |
| 5 | **Showing numeric model confidence ("87% confident") to non-technical creators.** | PAIR: numeric confidence presumes statistical literacy; a misleadingly high number *"may cause users to blindly accept a result"*; if confidence isn't actionable, don't show it. | [PAIR](https://pair.withgoogle.com/chapter/explainability-trust/) |
| 6 | **A wizard that cannot be exited and resumed, or that blocks access to information needed to finish it.** | NN/g lists exactly these as wizard disadvantages — including the documented case of a wizard blocking the very credit score the user needed. | [NN/g wizards](https://www.nngroup.com/articles/wizards/) |
| 7 | **A forced linear sequence with no skipping or looping back.** | Complex-app guideline 3 warns against rigid linear workflows with no escape hatches; expert users' mental models diverge from the designer's. | [NN/g complex applications](https://www.nngroup.com/articles/complex-application-design/) |
| 8 | **A persistent "Next steps" panel containing stale content.** | NN/g's USCIS example: the panel *"isn't relevant anymore"* and damages trust in the whole tracker. | [NN/g status trackers](https://www.nngroup.com/articles/status-tracker-progress-update/) |
| 9 | **Backend jargon in status labels** (`ready_to_publish`, `awaiting_review`, `calibration_invalid`). | NN/g guideline 3: internal codes *"mean nothing to the user"* and drive support contacts. `readableRef` already exists — this is an ongoing discipline, not a one-off fix. | [NN/g status trackers](https://www.nngroup.com/articles/status-tracker-progress-update/) |
| 10 | **Multiple primary action buttons visible at once** (common when several empty states or several stage panels render simultaneously). | Carbon recommends a **tertiary** button for repeated empty states precisely to avoid *"multiple primary action buttons in the UI"*. | [Carbon empty states](https://carbondesignsystem.com/patterns/empty-states-pattern/) |
| 11 | **A saved view that silently overwrites a shared/default definition when the user tweaks one column.** | The saved-view pattern names this as a failure mode; temporary changes must create a *modified* state until the user explicitly updates or saves a copy. | [UX Patterns Guide](https://uxpatternsguide.com/patterns/saved-view/) |
| 12 | **A saved view that stores row IDs instead of the view definition.** | Named as a canonical failure: saving must store the canonical definition so it re-renders *current* data through that state. | [UX Patterns Guide](https://uxpatternsguide.com/patterns/saved-view/) |
| 13 | **Decorative animation on sub-100 ms interactions.** | Ström: for the smallest temporal gaps, *"animations and transitions can make the app feel slower"*. Directly relevant to row selection and tab switching. | [Ström](https://matthewstrom.com/writing/ui-density/) |
| 14 | **Bulk operations that can confirm AI output.** | HAX Guideline 16 requires conveying consequences; the product rule requires per-item human confirmation for facts/publish/scope/long-term memory. Bulk-confirming proposals would convert "AI proposes" into "AI decides" at scale. | [HAX](https://www.microsoft.com/en-us/haxtoolkit/library/) |
| 14a | **A "select all" checkbox whose scope is ambiguous (current page vs all matching rows).** | Marigold: *"Users guess wrong in both directions, and either wrong guess is expensive."* The header checkbox must select the current page only. | [Marigold UI](https://www.marigold-ui.io/patterns/user-input/bulk-actions) |
| 14b | **Silently carrying a selection across a page, filter, or sort change.** | Named as the thing that must never happen: rows checked on page one invisibly remain selected while the user looks at page two, so the next press reaches hidden rows. | [Marigold UI](https://www.marigold-ui.io/patterns/user-input/bulk-actions) |
| 14c | **Per-row actions remaining live while a bulk selection exists.** | *"A row-level delete next to a bulk delete makes it unclear which scope a press affects."* While rows are selected, row actions should disable. | [Marigold UI](https://www.marigold-ui.io/patterns/user-input/bulk-actions) |
| 14d | **Vague bulk labels ("应用", "确定", "OK") and destructive actions placed beside routine ones.** | Actions should be verb-named so the effect is obvious before pressing, ordered safest-first with destructive last and visually separated. | [Marigold UI](https://www.marigold-ui.io/patterns/user-input/bulk-actions) |
| 14e | **Hiding multi-select entirely until the user has already selected something.** | The author of the enterprise list-pattern rules criticises Gmail for exactly this — *"it makes it nearly impossible to discover"* — and notes bulk selection is rare enough that the pattern must be obvious and consistent. | [Enterprise UX](http://www.enterpriseux.co/interacting-with-lists/) |
| 15 | **Replacing the structured workspace with a chat box.** | NN/g: the intent paradigm reverses the locus of control and is *"prone to including erroneous information"*, and users find it *"harder… to identify or correct the problem"*; the predicted future is a **hybrid** UI. Linear's own model keeps AI as a tool *on* the workbench. | [NN/g AI paradigm](https://www.nngroup.com/articles/ai-paradigm/); [Linear](https://linear.app/blog/design-for-the-ai-age) |
| 16 | **Treating a generic chat interface as "the AI-native standard".** | Linear's essay calls chat *"a very weak and generic form"* and argues for a functional application complemented by AI functions. | [Linear](https://linear.app/blog/design-for-the-ai-age) |
| 17 | **Cards-as-default for a scanning list.** | Ant Design assigns `卡片列表` to *展示性* (showcase, no particular reading order); a status-driven work queue is a scanning task, which is `列表`/`表格` territory. Cards also cost the vertical space status needs. | [Ant Design](https://ant.design/docs/spec/data-list-cn/); [uxpatterns.dev](https://uxpatterns.dev/pattern-guide/table-vs-list-vs-cards) |
| 18 | **Uniform, spaced-out "gray on gray" layout with no information advantage.** | Repeated complaint in the HN density thread; density must be bought and spent deliberately (Ström's *value ÷ time × space*). | [HN](https://news.ycombinator.com/item?id=43925732); [Ström](https://matthewstrom.com/writing/ui-density/) |
| 19 | **A two-pane layout forced into a compact viewport.** | Apple explicitly warns the content becomes less legible and harder to interact with; Material and Windows both switch to a single pane. | [Apple HIG](https://developer.apple.com/design/human-interface-guidelines/split-views) |
| 20 | **A pane in a two-pane layout with no selected-item indication.** | Apple: persistent selection highlight *"helps people stay oriented"*; Material places selection state only in the two-pane list. | [Apple HIG](https://developer.apple.com/design/human-interface-guidelines/split-views); [M3](https://m3.material.io/foundations/layout/canonical-examples/list-detail) |
| 21 | **Illustration-heavy repeated empty states across many small regions.** | Carbon: with many simultaneous failing widgets, *"an empty state that uses just text may be preferable"*; decorative images must be `alt=""`. | [Carbon](https://carbondesignsystem.com/patterns/empty-states-pattern/) |
| 22 | **Hiding an advanced pane with no discoverable way to bring it back.** | Apple requires **multiple** reveal paths including a keyboard shortcut. The current 展开/收起 caret is mouse-only unless a shortcut is added. | [Apple HIG](https://developer.apple.com/design/human-interface-guidelines/split-views) |
| 23 | **Colour-only status encoding (bare coloured dots).** | Both a usability loss (NN/g measured text-only lists ~57% slower than colour+icon; ~37% faster with both than text alone — *mobile-tested*) and an accessibility failure: *"relying on color alone runs the risk of failing color-blind users."* | [NN/g visual indicators](https://www.nngroup.com/articles/visual-indicators-differentiators/) |
| 24 | **Frame-display skeletons** (header/footer/background only, no content wireframe). | NN/g: effectively a spinner that teaches nothing. | [NN/g skeleton screens](https://www.nngroup.com/articles/skeleton-screens/) |
| 25 | **A skeleton or spinner for a sub-second load.** | The flash is worse than nothing. | [NN/g skeleton screens](https://www.nngroup.com/articles/skeleton-screens/) |
| 26 | **A spinner past 10 seconds, or a spinner where a skeleton belongs.** | >10 s needs an explicit percent-done progress bar; a full-page load wants a skeleton. | [NN/g skeleton screens](https://www.nngroup.com/articles/skeleton-screens/); [NN/g top-10 mistakes](https://www.nngroup.com/articles/top-10-application-design-mistakes/) |
| 27 | **Infinite scroll on a work-item list.** | It removes the footer, destroys the sense of "how many are there", and fights Select All and bulk selection. | [NN/g infinite scrolling](https://www.nngroup.com/articles/infinite-scrolling-tips/) |
| 28 | **Accordions on desktop when users must open most sections.** | The per-heading decision cost exceeds the scrolling saved; accordions are *"a mini-IA"* and pay off on mobile. | [NN/g accordions](https://www.nngroup.com/articles/accordions-on-desktop/) |
| 29 | **Two panes at a medium breakpoint (600–839 dp) with high-density content.** | M3 states explicitly that this *"can reduce usability"* — and the per-project workspace is information-dense. | [M3 breakpoints](https://m3.material.io/foundations/layout/breakpoints) |
| 30 | **Nesting lists.** | Carbon: structured lists are for simple grouped data; the moment you need nesting you need a data table (or a different component). | [Carbon structured list](https://carbondesignsystem.com/components/structured-list/usage/) |
| 31 | **Same action, different word, different place.** | NN/g's inconsistency catalogue (the "double-D rule: differences are difficult"). Especially risky across 8 stages built at different times. | [NN/g top-10 mistakes](https://www.nngroup.com/articles/top-10-application-design-mistakes/) |
| 32 | **Treating a deprecated component as guidance.** | Atlassian's `@atlaskit/table` is officially *"not recommended for use in production"*; copying it imports a dead pattern. | [Atlassian table](https://atlassian.design/components/table) |
| 33 | **An "all questions + tappable back" progress indicator.** | GOV.UK calls this out by name: often unnoticed, space-hungry, poor on small screens, hard to label, and hard to handle conditional sections. | [GOV.UK question pages](https://design-system.service.gov.uk/patterns/question-pages/) |
| 34 | **Hiding a primary or destructive action inside a kebab menu.** | NN/g: the icon is recognised, but hiding *key* actions hurts usability. Only secondary actions belong in overflow. | [NN/g overflow menu icons](https://www.nngroup.com/videos/overflow-menu-icons/) |
| 35 | **A third level of navigation for series/viewpoints/observations.** | Deep hierarchies cost discoverability and force generic labels; these panels are contextual to the project, so they belong inside the workspace. | [NN/g flat vs deep](https://www.nngroup.com/articles/flat-vs-deep-hierarchy/) |
| 36 | **Silent commitment** — machine output entering the project record without a discrete human action (autosave, page load, retry). | HAX's *feedforward* pattern exists precisely because silent state change is the failure; Apple: *"never trick someone into thinking they're interacting with… content authored by a human."* | [HAX G16](https://www.microsoft.com/en-us/haxtoolkit/guideline/convey-the-consequences-of-user-actions/); [Apple HIG](https://developer.apple.com/design/human-interface-guidelines/generative-ai) |
| 37 | **Confirmation as a formality** — "Are you sure?" with no restated specifics. | A confirmation *"must restate the user's request and explain what the computer is about to do, with specific information."* | [NN/g confirmation dialogs](https://www.nngroup.com/articles/confirmation-dialog/) |
| 38 | **Confirm-everything / approval fatigue.** | At volume *"the requests blur together… it stops treating each one as a fresh decision."* This is the main risk of over-reading "the human confirms every fact". | [WorkOS](https://workos.com/blog/approval-fatigue-agent-governance); [NN/g](https://www.nngroup.com/articles/confirmation-dialog/) |
| 39 | **A default "Accept"** on any AI-proposal confirmation. | NN/g: *"Avoid giving confirmation dialogs a default Yes answer."* | [NN/g confirmation dialogs](https://www.nngroup.com/articles/confirmation-dialog/) |
| 40 | **An opaque confirmation surface the creator cannot actually check.** | The sharpest evidence in this document: automation bias is driven by **verification complexity**, so the *harder* the AI is to check, the *more* it is trusted. A confirm button over an unexplained blob is a rubber stamp, not a human check. | [Lyell & Coiera](https://pmc.ncbi.nlm.nih.gov/articles/PMC7651899/); [Romeo & Conti 2025](https://doi.org/10.1007/s00146-025-02422-7) |
| 41 | **Confidence theatre** — printing a precision that does not map to result quality. | Apple: *"If you're not sure how your confidence values correlate with the quality of your results, it's not a good idea to convey confidence to people."* | [Apple HIG](https://developer.apple.com/design/human-interface-guidelines/machine-learning) |
| 42 | **Decorative provenance** — a citation that is hallucinated, or real but unrelated. | Users *"rarely click"* citations, so a plausible-looking chip creates *"a false sense of reliability"* rather than a check. | [NN/g explainable AI](https://www.nngroup.com/articles/explainable-ai/) |
| 43 | **Fake step-by-step reasoning** presented as transparency. | Such walkthroughs are often *"rationalizations generated after the fact"*; designers *"should avoid using step-by-step explanations that imply certainty."* | [NN/g explainable AI](https://www.nngroup.com/articles/explainable-ai/) |
| 44 | **Stale proposals that outlive their target** — a suggestion card still visible after the human already fixed it themselves. | Grammarly's production rule: hide the card *"ASAP"* once the user resolves it themselves. | [Grammarly engineering](https://www.grammarly.com/blog/engineering/how-suggestions-work-grammarly-editor/) |
| 45 | **Relying on user corrections to compensate for poor AI output.** | Apple: *"Never rely on corrections to make up for low-quality results… depending on them may erode people's trust."* | [Apple HIG](https://developer.apple.com/design/human-interface-guidelines/machine-learning) |
| 46 | **Burying the AI's limits in a footer disclaimer.** | Footers, help icons and vague language get skipped; the fix is prominent, plain-language placement near the point of use, paired with an action. | [NN/g explainable AI](https://www.nngroup.com/articles/explainable-ai/); [NN/g AI literacy](https://www.nngroup.com/articles/ai-literacy/) |
| 47 | **A chat-only surface for a multi-stage creation loop.** | Chat framing *"discourages error checking"*, and NN/g finds most users cannot articulate intent well enough for prose prompting (the articulation barrier). | [NN/g](https://www.nngroup.com/articles/ai-chatbots-discourage-error-checking/); [NN/g articulation barrier](https://www.nngroup.com/articles/ai-articulation-barrier/) |
| 48 | **Editing a record in a modal over the list.** | A modal *"will cover adjacent records… and the user won't be able to reference or copy data from a similar record"* — yet users routinely reference other records to recognise reasonable values. | [NN/g data tables](https://www.nngroup.com/articles/data-tables/) |
| 49 | **One tab stop per row in a dense list.** | APG's Layout Grid exists specifically to avoid users being *"effectively trapped in the list"*; a long list with per-row tab stops is a keyboard trap in practice. | [APG Grid](https://www.w3.org/WAI/ARIA/apg/patterns/grid/) |
| 50 | **Removing or restyling away the focus indicator.** | *"Catastrophic for keyboard users"* — replace it, never delete it. | [NN/g keyboard-only navigation](https://www.nngroup.com/articles/keyboard-accessibility/) |
| 51 | **Gating a required human review on the model's confidence score.** | *"什么时候必须停下来，不能只看模型置信度"* — confidence is not a proxy for stakes. | [woshipm](https://www.woshipm.com/ai/6447314.html) |
| 52 | **Merging status, outcome, and archive into one badge.** | *"已完成" ≠ "成功交付"*; 状态负责定位，结果负责解释. The contract already keeps these separate and the UI should too. | [woshipm](https://www.woshipm.com/ai/6453231.html) |
| 53 | **Collapsible/overlay filters with no persistent "active" marker.** | Without a marker *"用户可能遗忘当前有筛选条件"* — the user misreads a filtered list as the whole list. | [掘金 B端筛选设计](https://juejin.cn/post/7249179953357717564) |
| 54 | **A saved view that references entities by name.** | Vendor-documented: renaming a project silently breaks every saved filter that named it. | [Todoist](https://www.todoist.com/help/todoist/features/introduction-to-filters-V98wIH) |
| 55 | **Using a step indicator for content that is merely parallel.** | A step bar implies steps cannot be skipped; if there is no data dependency, use visual sections. | [掘金 分步表单的迷思](https://juejin.cn/post/7173561697247068191) |
| 56 | **Conflating 搜索 and 筛选.** | 搜索 is for input-type fields, 筛选 for selection-type; mixing them breaks consistency between the form and the list. | [woshipm](https://www.woshipm.com/ucd/6294415.html) |
| 57 | **Expressing AND/OR precedence without a visible condition group.** | *"避免依赖抽象的优先级规则"* — grouping must be visible (brackets, indentation, dashed boxes). | [woshipm](https://www.woshipm.com/ucd/6294415.html) |
| 58 | **Hard-coding a palette shortcut over an OS/browser convention without a remap.** | The top HN complaint about command palettes is that they *"steal ctrl/cmd + k"*; make the binding configurable. | [HN 29373536](https://news.ycombinator.com/item?id=29373536) |
| 59 | **"Powered by AI" as a value proposition.** | NN/g: naming AI as the selling point does not communicate value. | [NN/g](https://www.nngroup.com/articles/powered-by-ai-is-not-a-value-proposition/) |

---

## 4. Skill directory — public agent-skill / design-skill repositories worth adopting

> ⚠️ **Read this before acting on any install command below.**
>
> **These are third-party code.** Review the source and pin a commit before installing anything
> into this repository, per the workspace's own supply-chain caution.
>
> **Install-path reality, verified against the local DSH checkout — do not follow install
> commands blindly:**
>
> - ❌ **`dsh plugin add OWNER/REPO` is NOT a valid way to install a GitHub skills repo.**
>   `dsh plugin add <pkg>` requires `--profile <name>` and forwards verbatim to `pnpm` in that
>   profile directory — i.e. it installs **npm packages**, not GitHub skill repositories. DSH
>   core in this version has no `SKILL.md` handling in `lib/`; the session skill catalog is
>   supplied by a plugin. Any instruction in this document that reads "install as a DSH plugin"
>   should be treated as **unverified**.
> - ✅ **The working routes are:** `npx skills add OWNER/REPO` (the `skills` CLI is
>   `vercel-labs/skills`), a Claude Code marketplace (`/plugin marketplace add OWNER/REPO`), or
>   simply **copying the `SKILL.md` folder into a skills directory**.
> - ✅ **The only repo in this document verified as DSH-native** is `pbakaus/impeccable`, which
>   ships `.dsh/skills/impeccable/SKILL.md`.
> - ⚠️ **`docs.claude.com` and `platform.claude.com` are geo-blocked from this network** (HTTP 200
>   with a Webflow "App unavailable in region" body), so Claude-specific install docs could not
>   be read here. The vendor-neutral spec at **https://agentskills.io/specification.md** *is*
>   readable and was read in full — prefer it as the format contract.
> - ⚠️ None of the `npx skills add` / `/plugin marketplace add` commands in this document were
>   independently executed. They are quoted from each repo's README. **Nothing was installed.**

### 4.1 First-party / official skill collections

| Repo | URL | What it does | Install note |
|---|---|---|---|
| `anthropics/skills` | https://github.com/anthropics/skills | Anthropic's official Agent Skills. Contains `frontend-design` (distinctive visual design guidance, anti-templated-default checks, two-pass plan→critique workflow, copywriting-in-UI rules), `canvas-design`, `brand-guidelines`, `web-artifacts-builder`, `skill-creator`. | Official skills; the safest starting point. `/plugin marketplace add anthropics/skills` in Claude Code, or vendor the individual `SKILL.md` into `.claude/skills/`. **Directly relevant**: `frontend-design`'s "avoid default typographic treatments" and "structural devices encode information rather than decorate" rules map onto the status/density work above. |
| `obra/superpowers` | https://github.com/obra/superpowers | Agentic skills framework + development methodology. Skills include `brainstorming`, `writing-plans`, `subagent-driven-development`, `verification-before-completion`, `receiving-code-review`. | `npx skills add obra/superpowers` or clone into the skills dir. Process skills, not design skills — useful for running the redesign itself (plan → execute → verify). |
| `VoltAgent/awesome-agent-skills` | https://github.com/VoltAgent/awesome-agent-skills | 1000+ curated agent skills from official teams and community; has dedicated **Figma** and **product-manager** sections in addition to the Anthropic design skills (`canvas-design`, `frontend-design`, `web-artifacts-builder`, `brand-guidelines`, `skill-creator`). | Browse-only index; install the individual skill from its own repo. Best used as a discovery surface. |
| `ComposioHQ/awesome-claude-skills` | https://github.com/ComposioHQ/awesome-claude-skills | Large curated index of Claude Skills, resources and tooling. | Browse-only. Use to find candidates, then vet individually. |
| `travisvn/awesome-claude-skills` | https://github.com/travisvn/awesome-claude-skills | Curated Claude Skills focused on Claude Code workflows. | Browse-only. |
| `VoltAgent/awesome-design-md` | https://github.com/VoltAgent/awesome-design-md | 73 analysed `DESIGN.md` files derived from popular brand design systems (Linear, Stripe, Apple, Vercel, Spotify…). Drop one into a project so an agent generates visually consistent UI. | Copy the chosen `DESIGN.md` into the project root. Pairs with Google Stitch's `DESIGN.md` convention: https://stitch.withgoogle.com/docs/design-md/overview/ . **Useful here**: gives the redesign a written token/rule contract that agents must follow, which is exactly what a 58 KB hand-written page currently lacks. |
| `aaldere1/awesome-design-systems` | https://github.com/aaldere1/awesome-design-systems | Repackages `awesome-design-md` as a single Paperclip skill with routing logic + categorisation across 58 design systems. | Paperclip-specific import; use as a **source of design-system reference documents**, or take the upstream `awesome-design-md` instead if not on Paperclip. |

### 4.2 Design-review / UX-audit skills (directly usable on this page)

| Repo | URL | What it does | Install note |
|---|---|---|---|
| `gregorymm/design-review-plugin` | https://github.com/gregorymm/design-review-plugin | UI/UX design review skill for Claude Code: reviews against professional standards for **visual hierarchy, spacing, typography, colour theory, layout** (derived from FormFactor design-school lectures). | Low star count (~6) — **read the whole skill before adopting**. Clone into the plugin/skills directory. |
| `EliaAlberti/ux-audit-skill` | https://github.com/EliaAlberti/ux-audit-skill | Heuristic UX audits **from screenshots** for Claude Code / Codex, with severity-rated findings, **heuristic citations**, annotated screenshots, structured reports. | ~18 stars, highest-traction UX-audit skill found. Best fit for auditing the current 内容页 screenshots against Nielsen heuristics before redesigning. |
| `AslanMazhidov/design-review-skill` | https://github.com/AslanMazhidov/design-review-skill | Uses Playwright MCP to capture desktop/tablet/mobile screenshots, then audits typography, contrast, rhythm, hierarchy and **proposes concrete CSS fixes**. Bilingual EN/RU. | Very low stars (3) — treat as a reference implementation; the Playwright-MCP + CSS-fix loop is the valuable idea, and this repo already exists in-repo as `vision-skills`-style tooling. |
| `paulunemoon/ux-audit-skill` | https://github.com/paulunemoon/ux-audit-skill | Audits an existing product (web/mobile/desktop) across **16 dimensions**, every finding carrying evidence, severity and confidence. | Low stars. The "every finding carries evidence + confidence" contract is worth copying even if the skill isn't adopted. |
| `dmsakamoto/ux-audit-skill` | https://github.com/dmsakamoto/ux-audit-skill | Task-based UX audits "from the user's seat — journeys not pages, counts not vibes". | Low stars; conceptually aligned with this page's stage-journey framing. |
| `Jacobinwwey/frontend-law-auditor` | https://github.com/Jacobinwwey/frontend-law-auditor | Human-centred frontend quality gate + theory-based UX audit with measurable fast-gate checks, weighted scoring, and **CI strict mode**. | The CI-strict-mode angle is interesting given this repo's ≥80% coverage gates, but verify it doesn't fight existing lint/type gates before enabling. |
| `sandian1016/design-review-skill` | https://github.com/sandian1016/design-review-skill | 设计走查 Skill (Chinese): locally compares a design mock against the implemented screenshot, annotates visible differences, exports an acceptance checklist. | Chinese-language workflow; useful because this product's copy and review process are Chinese. Low stars. |
| `Ilm-Alan/frontend-design` | https://github.com/Ilm-Alan/frontend-design | Frontend design skill: eight aesthetic anchors locking palette / type / texture to CSS tokens (~121 ★). | ⚠️ Third-party. The `design-taste-frontend` skill already in this session's catalog may share lineage — **deduplicate before installing**. |
| `rongiladco/web-accessibility-audit` | https://github.com/rongiladco/web-accessibility-audit | WCAG audits combining headless-browser **axe-core** with heuristic HTML analysis, cited criteria, and dashboard reports (0 ★). | Low-star, but one of only two axe-core-backed a11y skills found. Audit the source before trusting. |
| `creativedeals/free-claude-skill-accessibility-audit` | https://github.com/creativedeals/free-claude-skill-accessibility-audit | WCAG 2.2 AA audit skill: dependency-free contrast + static HTML scanners, structured screen-reader/keyboard judgement, prioritized fixes (4 ★). | Node 18+, no build step. Good low-risk first audit pass; **not** a conformance guarantee. |
| `zuocharles/vibe-coded-website-review` | https://github.com/zuocharles/vibe-coded-website-review | Design-review checklist targeting generic "AI-generated site" failure modes, derived from a YC design review (0 ★). | ⚠️ Unproven and opinionated; complements the anti-pattern table above rather than replacing it. |

### 4.2b Skill-authoring and structure references

| Repo | URL | What it does | Install note |
|---|---|---|---|
| `asgard-ai-platform/skills` | https://github.com/asgard-ai-platform/skills | 301 agent skills across 22 domains (~236 ★), packaged with methodology + gotchas — the **best structural template found** for writing our own MUI/内容页 review skill. | Use as a **structural pattern**, not as content. |
| `spences10/claude-skills-cli` | https://github.com/spences10/claude-skills-cli | CLI for authoring skills with **progressive-disclosure validation** (~90 ★) — it enforces the same two-level rule NN/g prescribes for UIs. | Dev-only local CLI; low risk. |
| `daymade/claude-code-skills` | https://github.com/daymade/claude-code-skills | Production-ready Claude Code skills marketplace (~1.4k ★). | Cherry-pick individual skills; review each first. |
| `nexu-io/open-design` | https://github.com/nexu-io/open-design | DSH design plugin that turns a coding agent into a design engine producing real prototype/dashboard files with HTML/PDF/PPTX export (~97k ★). | Install as a DSH plugin. Runs locally — **confirm it does not write into the source tree**, per this repo's rule against generated output in the tree. |
| `tt-a1i/archify` | https://github.com/tt-a1i/archify | Renders architecture / workflow / sequence / data-flow / lifecycle diagrams as self-contained HTML (~67k ★) — useful for documenting the 8-stage loop before redesigning it. | Self-contained HTML output; no runtime dependency. |

**Negative result worth recording:** `find_dsh_plugin` returned **no** matches for UI/UX /
design-system / accessibility queries, and GitHub searches for `ui ux audit skill`,
`web design review agent skill`, `design system skill agent`, and `wcag accessibility skill`
all returned empty. **There is no mature, high-signal public skill for dense list-detail
dashboard review.** Authoring an in-repo review skill from the principle list in §2 is likely
a better move than adopting one.

### 4.2c Highest-value repos found in the AI-UX research pass

| Repo | URL | What it does | Install note |
|---|---|---|---|
| **`pbakaus/impeccable`** | https://github.com/pbakaus/impeccable | **The flagship find, and the answer to the "is `impeccable` real?" question.** ~69k ★, Apache-2.0. A design language for AI harnesses: 1 skill + 24 commands, audit / critique / polish workflow, anti-pattern detection. | `npx impeccable install` (then `/impeccable init`), or `/plugin marketplace add pbakaus/impeccable`. **DSH-native**: ships `.dsh/skills/impeccable/SKILL.md`. |
| **`plugin87/ux-ui-agent-skills`** | https://github.com/plugin87/ux-ui-agent-skills | ~1.4k ★, MIT. `design-review`, `design-qa`, `a11y-audit`, `design-doctrine` + DTCG tokens, WCAG 2.2 AA–AAA, **43 objective gates**. The best UX-review × accessibility combination found. | `/plugin marketplace add plugin87/ux-ui-agent-skills` then `/plugin install ux-ui-agent-skills@ux-ui-agent-skills`. |
| **`imsaif/aiux-skills`** | https://github.com/imsaif/aiux-skills | **The only human-AI / HITL skill library found.** 38 pattern skills incl. `aiux-human-in-the-loop`, `aiux-explainable-ai`, `aiux-trust-calibration`, `aiux-confidence-visualization`, `aiux-autonomy-spectrum`, `aiux-mixed-initiative-control`. Content was **directly inspected** (approval queues, override/reject design, routing review by stakes, rubber-stamp anti-pattern) and is strong. | `npx skills add imsaif/aiux-skills`. ⚠️ **0 stars** (auto-generated from aiuxdesign.guide) — evaluate before trusting. |
| `addyosmani/web-quality-skills` | https://github.com/addyosmani/web-quality-skills | ~2.8k ★, MIT. Lighthouse / Core Web Vitals with dedicated `web-quality-audit` and `accessibility` skills. Best-maintained quality gate. | `npx skills add addyosmani/web-quality-skills`. |
| `cuellarfr/design-skills` | https://github.com/cuellarfr/design-skills | ~55 ★, MIT. Explicit `design-critique`, `accessibility-audit`, `design-elevation`, `interaction-design`, `ux-research`, `journey-mapping`. | `npx skills add cuellarfr/design-skills`. |
| `deanpeters/Product-Manager-Skills` | https://github.com/deanpeters/Product-Manager-Skills | ~7k ★. `prd-development`, `discovery-process`, `lean-ux-canvas` — covers the PRD/spec side of the 内容页 loop. | `claude /plugin marketplace add deanpeters/Product-Manager-Skills`. |
| `mgifford/accessibility-skills` | https://github.com/mgifford/accessibility-skills | ~47 ★. Deep a11y library: axe-rules, ARIA, keyboard, contrast, `cli-audit`, `ci-cd`. | `npx skills add mgifford/accessibility-skills`. ⚠️ **AGPL-3.0 — viral licence; check fit before adopting.** |
| `narenkatakam/ux-audit` | https://github.com/narenkatakam/ux-audit | ~9 ★, Apache-2.0. Anti-generic UX audit: 12 principles, 13 reference docs, 7 component checklists. | `cp -r skills/ux-audit/* ~/.claude/skills/ux-audit/`. |
| `vercel-labs/web-interface-guidelines` | https://github.com/vercel-labs/web-interface-guidelines | ~882 ★. Concise, opinionated web-interface rules — cheap house-style context for MUI work. | **No skill manifest** — vendor as a context file; do not install as a skill. |
| `agentskills/agentskills` | https://github.com/agentskills/agentskills | ~25.5k ★. The open **Agent Skills specification**. | Spec repo — **conform to it**, do not install. Readable vendor-neutral copy: https://agentskills.io/specification.md |

**Two negative results that should shape the plan:**

1. **No credible agent skill exists for HAX / human-AI-interaction guidelines.** Searches for
   `HAX guidelines`, `human-AI interaction guidelines`, and `human-in-the-loop skill` returned
   empty or 0-star results; `imsaif/aiux-skills` (0 ★) is the only real match. There is likewise
   **no credible heuristic-evaluation skill** (every NN/g-specific repo found was 0–1 ★) and no
   focused PRD/spec-critique skill. **If TopicAI wants a HAX-grounded review skill with
   provenance, that is a build, not an adopt.**
2. **No mature public skill exists for dense list-detail dashboard review** (independent
   confirmation from the layout research pass). Same conclusion: **author it in-repo from the
   principle list in §2.**

### 4.2d Additional verified repos (third research pass)

Each of these had at least one `SKILL.md` confirmed in its git tree, and star/licence data was read
via `gh repo view --json`.

| Repo | URL | What it does | Install note |
|---|---|---|---|
| **`addyosmani/agent-skills`** | https://github.com/addyosmani/agent-skills | 25 production skills. `skills/frontend-ui-engineering/SKILL.md` is arguably the **strongest single file for this brief**: an explicit anti-"AI aesthetic" table, keyboard navigation, ARIA, focus management, empty/error/loading states, plus `references/accessibility-checklist.md`. | `npx skills add addyosmani/agent-skills --skill frontend-ui-engineering` |
| **`smukh/a11y-agent-skills`** | https://github.com/smukh/a11y-agent-skills | **The only repo found with an explicit `skills/keyboard-navigation-review/SKILL.md`** — directly relevant to §2.65–66. Also accessible-component-review, accessible-data-tables-and-grids, accessible-combobox-and-autocomplete, dialog-accessibility. Ships a CLI + MCP + GitHub Action. | `npx --yes @a11y-agent/cli scan <url>` |
| `vercel-labs/agent-skills` | https://github.com/vercel-labs/agent-skills | `skills/web-design-guidelines/SKILL.md` is a UI/UX/a11y **review** skill that fetches its rules live from `vercel-labs/web-interface-guidelines`. | `npx skills add vercel-labs/agent-skills` |
| `vercel-labs/skills` | https://github.com/vercel-labs/skills | **This is the `npx skills add` CLI itself** — the de-facto installer for most rows in this section. | Already the mechanism. |
| `google-labs-code/design.md` | https://github.com/google-labs-code/design.md | The `DESIGN.md` **format spec** — a visual-identity contract for coding agents. Pairs with §4.1's `awesome-design-md`. | Spec + tooling; conform rather than install. |
| `Intopia/intopia-web-accessibility-skill` | https://github.com/Intopia/intopia-web-accessibility-skill | Build + review a11y skill with ~30 component acceptance-criteria files (Combobox, Menu Button, Accordion, Landmark…). | Install mechanism not verified. |
| `Owl-Listener/designer-skills` | https://github.com/Owl-Listener/designer-skills | `design-ops/` includes design-critique, design-review-process, design-qa-checklist, design-debt-audit. | `/plugin marketplace add Owl-Listener/designer-skills` |
| `Tranz007/ux-skills` | https://github.com/Tranz007/ux-skills | `skills/critique/`, `skills/accessibility/`, `skills/blindspots/`. | `npx skills add Tranz007/ux-skills --all` |
| `Gesso-Build/skills` | https://github.com/Gesso-Build/skills | Deterministic design critique for HTML/CSS: 73 "slop guards", idempotent auto-fixes, `/gesso-critique`. | `npx -y @gessobuild/anti-slop install` |
| `Nutlope/hallmark` | https://github.com/Nutlope/hallmark | Anti-AI-slop design skill, single `SKILL.md`. Note: this is a *different* project from the [HaLLMark provenance research](https://www.cs.au.dk/~elm/pdf/hallmark.pdf) cited in §1.9 — do not conflate them. | `npx skills add nutlope/hallmark` |

**Rejected as thin listicles** (no `SKILL.md` in tree, description-only): `wilwaldon/Claude-Code-Frontend-Design-Toolkit`,
`bergside/awesome-design-skills`, `tomaszboloz/WCAG-Accessibility-Skills`.

**Agent Skills spec constraints** (from https://agentskills.io/specification.md, read in full):
required `name` (≤64 chars, lowercase + hyphens, must match the directory name) and `description`
(≤1024 chars); progressive disclosure across 3 stages; keep `SKILL.md` under 500 lines. Validate with
`skills-ref validate ./my-skill`. **This matters if we author the in-repo review skill §4.3 recommends.**

### 4.3 Not recommended as-is

- `aaldere1/awesome-design-systems`, `sharadvermasv/design-intelligence`, `tizsabrine/claude-skills-design`,
  `guilhermefriol/claude-skills-design` — found but effectively unvetted (0–10 stars, no visible
  methodology). Listed only so the next researcher does not re-discover them. **[X]**
- `Win1011/apple-design-reviewer.skill` — Apple-platform specific; this is a web app, so its HIG
  rules apply only partially. **[X]**

### 4.4 Suggested adoption order for this redesign

1. `anthropics/skills` → `frontend-design` (design direction + anti-default critique).
2. `VoltAgent/awesome-design-md` → adopt a `DESIGN.md` for TopicAI so the redesign has a written
   token/interaction contract instead of one 58 KB component.
3. `EliaAlberti/ux-audit-skill` → run a severity-rated heuristic audit over current 内容页 screenshots
   **before** redesigning, so the redesign has a baseline.
4. `obra/superpowers` → use `writing-plans` + `verification-before-completion` to run the redesign
   itself with an explicit verification gate.

---

## 5. Direct answers to the brief's questions

| Question | Answer, with the strongest source |
|---|---|
| list-detail vs master-detail vs drill-in — which? | They are the same pattern at different widths. Use **two-pane at 840 dp+**, **single-pane drill-in below 600 dp**, and at **600–839 dp stay single-pane** because M3 warns that two panes with high-density content *"can reduce usability"* — and this workspace is dense. ([M3 list-detail](https://m3.material.io/foundations/layout/canonical-examples/list-detail); [M3 breakpoints](https://m3.material.io/foundations/layout/breakpoints); [Windows](https://learn.microsoft.com/en-us/windows/apps/develop/ui/controls/list-details)) |
| Which pane pattern for the side panels? | If a panel is *only* meaningful relative to the open project (contextual), use M3's **supporting pane** (fixed 360 dp). If it is a peer step in the loop, it is not a pane — it is part of the workspace. Verify by task analysis. ([M3 supporting pane](https://m3.material.io/foundations/layout/canonical-examples/supporting-pane)) |
| Information hierarchy & density for a list of work items with status | Surface **status + current stage + next action + last activity**, de-emphasise the rest, and measure density as **value ÷ (time × space)**. ([Ström](https://matthewstrom.com/writing/ui-density/); [NN/g complex apps](https://www.nngroup.com/articles/complex-application-design/); [Ant Design](https://ant.design/docs/spec/data-list-cn/)) |
| Progressive disclosure for a long multi-stage workspace | Two levels max; make each disclosure **self-describing**; use *staged disclosure* for the linear parts but always allow skipping and looping back. ([NN/g](https://www.nngroup.com/articles/progressive-disclosure/); [NN/g wizards](https://www.nngroup.com/articles/wizards/)) |
| Status taxonomy, filtering, sorting, grouping, saved views | Group by stage by default; simple status tabs first, facets only if proven; batch-apply for cross-category filters; saved views as named objects with a modified state. ([Carbon filtering](https://carbondesignsystem.com/patterns/filtering/); [NN/g facets](https://www.nngroup.com/articles/filters-vs-facets/); [saved view pattern](https://uxpatternsguide.com/patterns/saved-view/)) |
| Card vs table vs row | **Row/List** for the default scanning list; **Table** only if creators genuinely compare projects across attributes; **Cards** are for showcase, not a work queue. ([Ant Design](https://ant.design/docs/spec/data-list-cn/); [uxpatterns.dev](https://uxpatterns.dev/pattern-guide/table-vs-list-vs-cards)) |
| Action placement & bulk ops | One primary CTA per surface; row-level primary = open; destructive/rare actions behind overflow; bulk ops limited to non-confirming, low-risk mutations. ([Carbon](https://carbondesignsystem.com/patterns/empty-states-pattern/); [HAX](https://www.microsoft.com/en-us/haxtoolkit/library/)) |
| Empty / loading / error / partial states | Four distinct states; empty states **replace** the region; never show "no data" while loading; match feedback to Ström's latency bands. ([Carbon](https://carbondesignsystem.com/patterns/empty-states-pattern/); [NN/g](https://www.nngroup.com/articles/empty-state-interface-design/); [Ström](https://matthewstrom.com/writing/ui-density/)) |
| Keyboard nav & command palette | Follow WAI-ARIA APG keyboard models; teach accelerators **in context**; scope the palette to navigation + low-risk actions and keep mouse paths. ([APG](https://www.w3.org/WAI/ARIA/apg/patterns/); [NN/g](https://www.nngroup.com/articles/complex-application-design/); [command palettes](https://philipcdavis.com/writing/command-palette-interfaces)) |
| Mobile adaptation of a dense list-detail surface | Full-screen list → full-screen workspace with back; one decision per screen; never force two panes. ([Apple HIG](https://developer.apple.com/design/human-interface-guidelines/split-views); [M3](https://m3.material.io/foundations/layout/canonical-examples/list-detail)) |
| AI-suggestion UX under "AI proposes, human confirms" | Proposal chrome + adjacent confirm/dismiss; short *why*; categorical or n-best confidence; explicit blast-radius copy for long-term memory; never a chat-only surface. ([HAX](https://www.microsoft.com/en-us/haxtoolkit/library/); [PAIR](https://pair.withgoogle.com/chapter/explainability-trust/); [Linear](https://linear.app/blog/design-for-the-ai-age)) |
| How often may the human be asked to confirm? | Per **fact**, per **scope change**, per **publish**, per **long-term-memory decision** — **never per AI sentence**. Overused confirmation degrades to rubber-stamping, and automation bias grows when the thing being confirmed is hard to check. ([NN/g](https://www.nngroup.com/articles/confirmation-dialog/); [WorkOS](https://workos.com/blog/approval-fatigue-agent-governance); [Lyell & Coiera](https://pmc.ncbi.nlm.nih.gov/articles/PMC7651899/)) |
| Is there a legal/platform constraint on this page? | **Yes — AI-content disclosure.** 小红书 reportedly requires proactive labelling of AI-generated/polished content while banning fully AI-operated accounts, implementing the national 《人工智能生成合成内容标识办法》. 发布检查 needs a disclosure item fed by a provenance record. ([腾讯新闻](https://news.qq.com/rain/a/20260427A05JSU00); [gov.cn](https://www.gov.cn/zhengce/zhengceku/202503/content_7014286.htm)) |

---

## 6. Gaps, uncertainty, and what to research next

1. **Reddit, 小红书 and X were unreachable in this environment.** The brief asked for
   r/UXDesign, r/userexperience, r/ProductManagement, r/web_design and X design threads.
   `agent-reach doctor` reports `reddit: off`, `xiaohongshu: off`, `twitter: warn`. **No
   substitute sources were fabricated.** The full list of platforms that failed, with the
   specific failure, is in **§Sources that must NOT be cited** and §1.8 — additionally unreachable
   were 知乎 (hard 403 on every path), 少数派 (JS shells), Arco Design / TDesign spec pages
   (JS-only), Height (`height.app` did not resolve), Monday (403 WAF), Airtable (404 slug),
   Asana (JS shell), Anthropic first-party docs (`docs.claude.com`, `platform.claude.com`
   geo-blocked), HN item pages and V2EX thread pages (bot-blocked to `curl`; data obtained via
   their APIs instead), and W3C "Understanding" pages (403 WAF). To close the social gap, install
   a backend (`agent-reach install --channels opencli`, which reuses Chrome login state) and re-run.
2. **No Chinese-language creator-tool usability study was found.** Ant Design's spec
   (https://ant.design/docs/spec/data-list-cn/) is a *design-system* source, not creator
   research. Whether Chinese 小红书 creators prefer grouped-by-stage or a flat chronological
   feed is **unanswered** and should be tested, not assumed.
3. **No validated thresholds exist in the sources reached** for "how many projects before
   filtering becomes necessary" or "how many rows is too many". Treat any such number in a
   redesign proposal as an assumption to test.
4. **The observation-window wait is the biggest unsolved UX risk.** NN/g's guidance is clear
   ([status trackers](https://www.nngroup.com/articles/status-tracker-progress-update/)) but
   nothing found addresses a **multi-day, non-blocking** wait inside a personal content tool.
   This needs its own design spike.
5. **`web_search` / `web_fetch` hit a shared quota mid-research** (HTTP 429 then HTTP 402); one
   `web_fetch` route also failed to reach `r.jina.ai` from this network. Most later fetches were
   rerouted through **Exa** (`mcporter call exa.web_search_exa` / `exa.web_fetch_exa`), the
   **GitHub API**, and the **HN Algolia API**. Two sources that initially appeared only as
   search-result metadata were subsequently **fetched in full and verified** and are no longer
   flagged: Smashing Magazine's one-thing-per-page article and the Refactoring UI tips article.
6. **One citation still rests on a search-result extract rather than a full read** and should be
   re-verified before being treated as authoritative: `uxpatterns.dev`'s table-vs-list-vs-cards
   guide. (The Shopify Polaris index-filters citation, previously flagged here, was subsequently
   verified at source — `polaris.shopify.com` redirects plain fetches to a generic landing page,
   so it had to be read through the Exa content extract.)
7. **⚠️ Security observation worth escalating, not just noting:** every `web_fetch` HTTP 402
   payload contained an **auto-generated `username` / `password` / `api_key` block rendered
   directly into agent context**. None of the three research agents used those credentials, but if
   the key material is genuine it is being **leaked into model context on every failed search**.
   This is a harness-level issue, not a research one — it should be investigated independently of
   this document.
8. **No primary source was found for three behaviours this page needs**, so they must be decided
   from the app's own latency profile rather than cited:
   **optimistic UI vs. spinner conventions**; **partial/stale-data rendering** (e.g. refreshing
   one project field while the rest is cached); and any **role-based status taxonomy**. GitLab's
   loading pattern defers progressive loading to an open TODO, and no design system states a
   partial-data convention.
9. **Explicitly out of scope in this pass**, flagged so nobody assumes it was covered:
   accessibility mechanics of the list itself (**focus management on stage transitions,
   `aria-live` for AI candidate updates, keyboard operation of bulk selection**),
   **virtualization of a very long project list**, and **Chinese copy / i18n rules for the
   status vocabulary**. The `解决 / 分享 / 记录` intent axis in particular has **no
   design-system precedent** — it is product vocabulary and needs its own documented legend,
   not an imported pattern.
10. **Provenance caveat on session skills — partially resolved.** `impeccable` **is now verified**:
    it corresponds to `pbakaus/impeccable` (~69k ★, Apache-2.0, and the only repo in this
    document confirmed DSH-native). The skill named `design-taste-frontend` still has **no
    verified high-star public upstream** under that name (`Zouyq-GitHub/design-taste-frontend-skill`
    ≈0 ★ is plausibly related but unconfirmed) — **do not cite that name as authoritative.**
11. **No peer-reviewed work was found on 盲评 (blind review) inside consumer creator tools.**
    The nearest transferable evidence is on LLM-as-judge calibration: NN/g reports an **F1 ≈ 0.8**
    bar against human annotation as a usable reliability threshold, and warns uncalibrated judges
    *"may degrade performance as easily as it can improve it"*
    ([NN/g — critique in the AI era](https://www.nngroup.com/articles/ai-era-critique/)).
    Treat the 盲评 step's scoring design as **under-researched and needing its own validation**.
12. **The 证据采访 (evidence interview) interaction design is also under-researched.** No
    authoritative source was found on interviews that *force factual confirmation*. The closest
    primitives are Apple's Corrections/Calibration patterns and the Chinese three-layer handover
    card — treat this step as needing its own user testing.
13. **Claim that could not be verified in the wider literature:** 小红书's AI-content labelling
    duty is **secondary-sourced only** (its creator rules page is behind login). The national
    regulation underneath it *is* primary. Verify the exact declaration flow in-product before
    building the 发布检查 checkbox.
