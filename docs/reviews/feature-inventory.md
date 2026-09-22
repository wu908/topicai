# TopicAI — Feature Inventory & User-Flow Map

> **Purpose.** Single source of truth for a manual / automated-browser regression run of TopicAI.
> Everything below is derived **read-only** from the working tree at
> `G:\codex_project\topicAI\mvp` (branch state as of this analysis). No application code,
> test, or existing doc was modified — this file is the only artifact created.
>
> **How to read citations.** `path:line` is a 1-based line number in the file at that path,
> relative to the repository root. Where a control is rendered inside a `.map()` over a
> collection, the cited line is the JSX that produces one instance of the control.
>
> **Scope.** 18 `<Route>` entries (17 concrete paths + wildcard), 15 page modules,
> 110 `/api/v2` route decorators, and every interactive control in
> `frontend/src/pages/**` and `frontend/src/features/**`.

---

## 0. Inventory summary

| Dimension | Count | Source of truth |
|---|---|---|
| Frontend `<Route>` entries | **18** (17 concrete paths + `*` wildcard) | `frontend/src/App.tsx:64-85` |
| Distinct page modules | **15** | `frontend/src/pages/**` (excluding `__tests__`) |
| Distinct route paths a tester can reach | **17** | see §1 |
| Auth-guarded routes | **16** of 17 concrete paths | `App.tsx:53-55`, `App.tsx:32-51` |
| Nav entries (desktop) | **10** links in 2 groups | `frontend/src/components/layout/Sidebar.tsx:35-48` |
| Nav entries (mobile bottom bar) | **4** links + 1 sheet trigger | `Sidebar.tsx:49-54`, `Sidebar.tsx:114-123` |
| Nav entries (mobile 「更多」 sheet) | **6** links + 1 logout | `Sidebar.tsx:55-62`, `Sidebar.tsx:129-145` |
| Logout paths | **2** | `Sidebar.tsx:129-145` (sheet), `Sidebar.tsx:164-179` (desktop footer) |
| Interactive controls inventoried | **333** distinct controls (sum of the per-file tally in §3.25) | §3 |
| `/api/v2` route decorators | **110** (109 in 20 sub-routers + `GET /api/v2/health`) | §4 |
| HTTP method split | POST 66 · GET 33 · PUT 6 · DELETE 4 · PATCH 1 | §4.1 |
| Routers | **21** modules (20 sub-routers + root `router.py`) | `backend/app/api/v2/router.py:5-24` |

Everything in `frontend/src/pages/**` and `frontend/src/features/**` renders inside the
single `AppLayout` shell (`frontend/src/components/layout/AppLayout.tsx:16-42`), which also
mounts the global `Sidebar` (`AppLayout.tsx:22`) and the global floating-ball
`CompanionDialog` (`AppLayout.tsx:24`) — so those two control sets are reachable from **every**
authenticated page and should be exercised once per session rather than per page.

---

## 1. Route inventory

All routes are declared in a single `<Routes>` block in `frontend/src/App.tsx:64-85`.
Pages are `React.lazy` imports (`App.tsx:12-26`) wrapped in a `Suspense` fallback
(`App.tsx:28-30`). Auth guarding is applied by the `protectedPage()` helper
(`App.tsx:53-55`) → `ProtectedRoute` (`App.tsx:32-51`).

`ProtectedRoute` semantics a tester must know:

- While `isLoading && !user`, it renders `<LoadingFallback />` instead of the page (`App.tsx:48`).
- If `!isAuthenticated`, it redirects to `/login` with `replace` (`App.tsx:49`).
- Otherwise it renders `<AppLayout>{children}</AppLayout>` (`App.tsx:50`) — i.e. the sidebar
  and floating-ball companion only exist on guarded routes.
- `isAuthenticated` is seeded synchronously from `localStorage.access_token`
  (`frontend/src/store/authStore.ts:41`), so a stale token shows the shell first and then
  drops to `/login` when `/auth/me` fails (`authStore.ts:124-136`) — see ambiguity A1.

| # | Path | Page component | Purpose | Auth-guarded | Citation |
|---|---|---|---|---|---|
| 1 | `/login` | `LoginPage` | Email+password login, and registration via an inline mode switch | **No** (public) | `App.tsx:65` |
| 2 | `/` | `HomePage` | 晨报 (daily brief): the single next best action of the day + quiet counters | Yes | `App.tsx:66` |
| 3 | `/content` | `ContentPage` | Content-project list; empty state funnels into starter / reference onboarding | Yes | `App.tsx:67` |
| 4 | `/content/:projectId` | `ContentPage` | Project workspace (editor, stage action card, observations, viewpoints, series) | Yes | `App.tsx:68` |
| 5 | `/opportunities` | `OpportunitiesPage` | 机会: explainable content opportunities, source verification and adoption | Yes | `App.tsx:69` |
| 6 | `/materials` | `MaterialsPage` | 素材: reusable evidence library (text/link/image/document/audio/video) | Yes | `App.tsx:70` |
| 7 | `/loop` | `AsyncLoopPage` | 产出架 (shelf) + 灵感池 (inspiration pool), pickup / discard / restore | Yes | `App.tsx:71` |
| 8 | `/loop/inbox` | `InboxPage` | 收件箱: capture material, consent flag, digest into deliverables, loop metrics | Yes | `App.tsx:72` |
| 9 | `/loop/review` | `ReviewPage` | 周复盘: read-only weekly judgement-vs-actual rows with stage pills | Yes | `App.tsx:73` |
| 10 | `/urgent` | `UrgentPage` | 急稿: three-step synchronous path that creates a project and lands in the workspace | Yes | `App.tsx:74` |
| 11 | `/growth` | `GrowthPage` | 成长: capability counters, paired milestones, trust panel | Yes | `App.tsx:75` |
| 12 | `/me` | `MePage` | 我的: goals/settings, password, AI capability status, export, account deletion | Yes | `App.tsx:76` |
| 13 | `/onboarding/assessment` | `StarterPage` | Starter experiment step 1 (self-assessment) — *route is decorative, see A2* | Yes | `App.tsx:77` |
| 14 | `/onboarding/directions` | `StarterPage` | Starter experiment step 2 (choose a direction) — *decorative, see A2* | Yes | `App.tsx:78` |
| 15 | `/onboarding/sprint` | `StarterPage` | Starter experiment step 3 (run/review the sprint) — *decorative, see A2* | Yes | `App.tsx:79` |
| 16 | `/onboarding/growth` | `GrowthOnboardingPage` | Growth onboarding: import history, correct the creator profile | Yes | `App.tsx:80` |
| 17 | `/onboarding/reference` | `ReferenceAnchorPage` | Reference anchor: paste 2–3 references, read back topic range / style / audience | Yes | `App.tsx:81` |
| 18 | `*` | `NotFoundPage` | 404 fallback | **No** (deliberately outside the guard) | `App.tsx:82-84` |

### 1.1 Route-level notes

- **No route is nested under another layout.** Every guarded route gets the same `AppLayout`
  except for a width tweak: `AppLayout.tsx:18` detects `location.pathname.startsWith('/content/')`
  and drops the max-width/padding constraint for the project workspace (`AppLayout.tsx:29-35`).
- **`/content` and `/content/:projectId` share one component.** `ContentPage` branches on
  `useParams().projectId` (`ContentPage.tsx:116`) — one code path renders the project list
  (`ContentPage.tsx:292-365`) and another the workspace (`ContentPage.tsx:388-576`).
- **There is no route for `/onboarding/starter`, `/loop/pool`, or a pool deep link.** The
  inspiration pool is a tab inside `/loop` (`AsyncLoopPage.tsx:59`), not a URL.
- **`/materials` and `/content/:projectId` both surface materials**, but only `/materials`
  can create them (`MaterialsPage.tsx:204`); the workspace drawer only links existing ones
  (`ContentPage.tsx:627-634`).

### 1.2 Ambiguities in routing (stated explicitly, not guessed)

- **A1 — guard flips after first paint.** `authStore.isAuthenticated` is `true` whenever
  `localStorage.access_token` exists (`authStore.ts:41`), and `ProtectedRoute` only redirects
  once `/auth/me` has failed (`App.tsx:38-49`). An expired token therefore renders the
  sidebar briefly before bouncing to `/login`. A tester should check for this flash rather
  than assume it is a bug.
- **A2 — `/onboarding/assessment|directions|sprint` do not control the visible step.**
  `StarterPage` ignores `useLocation()` entirely and picks the step from
  `workspace.assessment` / `workspace.next_step` (`StarterPage.tsx:124-130`). All three URLs
  render whatever step the server says. The E2E suite navigates only to
  `/onboarding/assessment` (`frontend/e2e/starter-flow.spec.ts:25`) and relies on this.
  It is **not** stated anywhere in the code that the three URLs are aliases — treat as an
  intentional-but-undocumented shortcut, and verify each of the three URLs renders the same
  step for the same account.
- **A3 — no client-side route for resetting a forgotten password.** `/login` has no "forgot
  password" affordance (`LoginPage.tsx` in full). Password change only exists inside `/me`
  and requires the current password (`MePage.tsx:239-263`).

---

## 2. Navigation inventory

All navigation lives in `frontend/src/components/layout/Sidebar.tsx`. Both the desktop and
mobile DOM are **always mounted** and switched with CSS (`Sidebar.tsx:6-8`, `.v3-nav-desktop`
/ `.v3-nav-mobile` at `Sidebar.tsx:107` / `Sidebar.tsx:112`), so in a DOM-based test every
nav link is present even when not visible — assert on visibility, not existence.
`NavLink` sets `end` for `/` and `/loop` (`Sidebar.tsx:71`) so those two do not stay
highlighted on child paths, and exposes `aria-label={item.label}` (`Sidebar.tsx:75`).

### 2.1 Desktop sidebar

| Group | Label (visible text) | `aria-label` | Target route | Icon | Citation |
|---|---|---|---|---|---|
| Brand (not a link) | `T` + `TopicAI` | — | — | — | `Sidebar.tsx:101-104` |
| 创作 (create, rendered first) | 晨报 | 晨报 | `/` | `HomeOutlined` | `Sidebar.tsx:36` |
| 创作 | 产出架 | 产出架 | `/loop` | `GridViewOutlined` | `Sidebar.tsx:37` |
| 创作 | 收件箱 | 收件箱 | `/loop/inbox` | `RssFeedOutlined` | `Sidebar.tsx:38` |
| 创作 | 急稿 | 急稿 | `/urgent` | `EditNoteOutlined` | `Sidebar.tsx:39` |
| 创作 | 周复盘 | 周复盘 | `/loop/review` | `InsightsOutlined` | `Sidebar.tsx:40` |
| 创作 | 成长 | 成长 | `/growth` | `EmojiEventsOutlined` | `Sidebar.tsx:41` |
| Group caption | 管理 | — (aria-hidden, non-interactive) | — | — | `Sidebar.tsx:109` |
| 管理 | 内容 | 内容 | `/content` | `ArticleOutlined` | `Sidebar.tsx:44` |
| 管理 | 机会 | 机会 | `/opportunities` | `LightbulbOutlined` | `Sidebar.tsx:45` |
| 管理 | 素材 | 素材 | `/materials` | `FolderOutlined` | `Sidebar.tsx:46` |
| 管理 | 我的 | 我的 | `/me` | `PersonOutline` | `Sidebar.tsx:47` |

Rendered in order: `CREATE_ITEMS` (`Sidebar.tsx:108`) → 管理 caption → `MANAGE_ITEMS`
(`Sidebar.tsx:110`). The nav container carries `aria-label="主导航"` (`Sidebar.tsx:106`).

### 2.2 Desktop sidebar footer (always visible on desktop)

| Label | `aria-label` | Action | Citation |
|---|---|---|---|
| `AI 正常 · 本地编排` | — (static status text, **not** bound to real AI state — see A4) | none | `Sidebar.tsx:153` |
| `{user?.username \|\| 'TopicAI MVP'}` | — | none | `Sidebar.tsx:155` |
| 资料 | 个人资料 | `navigate('/me')` | `Sidebar.tsx:157-163` |
| 退出 | 退出登录 | `logout()` then `navigate('/login')` | `Sidebar.tsx:164-179` |

**Logout path 1 (desktop footer).** `Sidebar.tsx:164-179`: calls
`useAuthStore.logout` (`authStore.ts:97-101`, clears `access_token` + `refresh_token` and
resets `user`/`isAuthenticated`) inside a `try/catch` that swallows storage failures
(`Sidebar.tsx:168-173`), then unconditionally `navigate('/login')`. Expected observable:
sidebar disappears, URL is `/login`, and a manual `GET /api/v2/auth/me` with the old token
returns 401.

### 2.3 Mobile bottom bar (≤720px per `Sidebar.tsx:6`)

| Label | `aria-label` | Target | Citation |
|---|---|---|---|
| 晨报 | 晨报 | `/` | `Sidebar.tsx:50` |
| 产出架 | 产出架 | `/loop` | `Sidebar.tsx:51` |
| 收件箱 | 收件箱 | `/loop/inbox` | `Sidebar.tsx:52` |
| 我的 | 我的 | `/me` | `Sidebar.tsx:53` |
| 更多 | 更多导航 | toggles the 「更多」 sheet (`setMoreOpen`) | `Sidebar.tsx:114-123` |

The 「更多」 trigger has `aria-expanded={moreOpen}` (`Sidebar.tsx:117`) and gets the `active`
class while open (`Sidebar.tsx:116`).

### 2.4 Mobile 「更多」 sheet

Rendered through `createPortal(..., document.body)` only while `moreOpen`
(`Sidebar.tsx:125-149`); the container has `aria-label="更多导航面板"`
(`Sidebar.tsx:127`). Items come from `MOBILE_MORE_ITEMS` (`Sidebar.tsx:55-62`):

| Label | `aria-label` | Target | Citation |
|---|---|---|---|
| 急稿 | 急稿 | `/urgent` | `Sidebar.tsx:56` |
| 周复盘 | 周复盘 | `/loop/review` | `Sidebar.tsx:57` |
| 成长 | 成长 | `/growth` | `Sidebar.tsx:58` |
| 内容 | 内容 | `/content` | `Sidebar.tsx:59` |
| 机会 | 机会 | `/opportunities` | `Sidebar.tsx:60` |
| 素材 | 素材 | `/materials` | `Sidebar.tsx:61` |
| 退出登录 | 退出登录 | `logout()` then `navigate('/login')` | `Sidebar.tsx:129-145` |

**Logout path 2 (mobile sheet).** `Sidebar.tsx:132-140`: identical semantics to the desktop
footer — `try { logout() } catch {}` then `navigate('/login')`.

**Auto-close behaviour a tester must verify.** The sheet closes on any route change via a
render-phase state adjustment (`Sidebar.tsx:93-97`) — *not* an effect. Because the mobile bar
and sheet share `close`-less links, clicking a sheet item must both navigate **and** remove
`.v3-more-sheet` from the DOM. There is **no backdrop, no Escape handler, and no
outside-click handler** anywhere in `Sidebar.tsx` — the only ways to dismiss the sheet are
picking an item or toggling 「更多」 again. Treat that as a known limitation.

**A4 — the sidebar AI status string is hard-coded.** `AI 正常 · 本地编排`
(`Sidebar.tsx:153`) is static JSX and does not read `settings.ai.configured`, even though the
real AI availability flag exists and `/me` renders it (`MePage.tsx:269-271`). A tester
comparing the sidebar claim against `/me` while the model is unconfigured will see a
contradiction. Flag this as a product-truth defect, not a test failure.

**A5 — unauthenticated 404.** `*` is outside the guard (`App.tsx:82-84`), so a logged-out
visitor sees `NotFoundPage` without a sidebar. That page's only action is 「返回首页」
(`NotFoundPage.tsx:21` → `navigate('/')`), which then bounces to `/login`. Expected, but
worth an explicit test.

---

## 3. Per-page & per-feature interactive control inventory

This is the exhaustive list that a manual run must exercise. Columns:

- **Label** — the visible text, or the `aria-label` / `placeholder` / `id` when the control is
  icon-only. `{…}` marks a value that varies at runtime.
- **What it does** — the user-visible effect.
- **Handler / API** — the function and, where it leaves the browser, the HTTP call.
- **file:line** — where the control is rendered.

Notation: `→` means "calls"; the API paths are the `/api/v2`-relative paths resolved by
`frontend/src/services/api/client.ts:17` (`API_PREFIX = '/api/v2'`).

### 3.1 `frontend/src/pages/Login/LoginPage.tsx` — 6 controls

| Label | What it does | Handler / API | file:line |
|---|---|---|---|
| 邮箱 (`#login-email`) | Email field, `required`, `type=email` | local state `email` | `LoginPage.tsx:71-79` |
| 你的姓名 (`#login-username`) | Register-only name field, `maxLength=50` | local state `username` | `LoginPage.tsx:80-91` |
| 密码 (`#login-password`) | Password field | local state `password` | `LoginPage.tsx:92-100` |
| 再输入一次密码 (`#login-confirm-password`) | Register-only confirmation | local state `confirmPassword` | `LoginPage.tsx:101-112` |
| 进入 / 创建账号 (`{isLoading ? '处理中…' : …}`) | Submits the form; label depends on mode and pending state; disabled while loading | `handleSubmit` (`LoginPage.tsx:29`) → `store.login` (`authStore.ts:45` → `POST /auth/login`) or `store.register` (`authStore.ts:67` → `POST /auth/register`); on success `navigate('/')` (`LoginPage.tsx:53`) | `LoginPage.tsx:113-115` |
| 没有账号？注册 / 已有账号？登录 | Switches login↔register mode and clears both store and form errors | `switchMode` (`LoginPage.tsx:23-27`) | `LoginPage.tsx:119-125` |

Client-side register validation (all produce `role="alert"` text, none hit the network):
name `< 2` chars (`LoginPage.tsx:34-37`), password `< 8` chars (`LoginPage.tsx:38-41`),
mismatched confirmation (`LoginPage.tsx:42-45`).

> Note: `LoginPage.tsx:118` renders the static hint `素材授权默认最小 · 数据随时可导出带走`;
> it is copy, not a control.

### 3.2 `frontend/src/pages/Home/HomePage.tsx` (晨报) — 15 controls

| Label | What it does | Handler / API | file:line |
|---|---|---|---|
| Whole primary card (`.acard`) — click **or** `Enter` | Navigates to the resolved destination of today's action | `startAction` (`HomePage.tsx:142`) → `resolveActionPath` (`HomePage.tsx:134`) → `navigate` | `HomePage.tsx:235` |
| `{primaryLabel}` primary button (`开始一条内容` / `确认内容想产生的影响` / … / `手动继续` / `回到对应页面` / `查看并确认机会`) | Same navigation as the card | `startAction` | `HomePage.tsx:241` |
| 暂不做 | Defers today's action with reason `user_deferred_from_today` | `deferAction()` (`HomePage.tsx:152`) → `POST /actions/{id}:respond` (`decision: 'defer'`) | `HomePage.tsx:242` |
| 不适合我 | Opens the rejection textarea | `setShowReject(true)` | `HomePage.tsx:243` |
| 手动继续 | Navigates to the action path; falls back to `/content` when the path is `/` itself | `navigate(continuePath)` (`HomePage.tsx:150`) | `HomePage.tsx:244` |
| 问它 | Opens the floating-ball companion scoped to `晨报 · 当前行动` | `openCompanion` (`frontend/src/features/companion/openCompanion.ts:2`) | `HomePage.tsx:245` |
| 为什么这条建议不适合你 (textarea) | Free-text rejection reason, min 1 char to enable the confirm button | local state `rejectReason` | `HomePage.tsx:256-263` |
| 停止这条建议 | Rejects the action; disabled until the reason is non-blank | `rejectAction` (`HomePage.tsx:172`) → `POST /actions/{id}:respond` (`decision: 'reject'`) | `HomePage.tsx:265` |
| 返回 | Closes the rejection textarea | `setShowReject(false)` | `HomePage.tsx:266` |
| 重试 (error banner) | Re-runs the whole page load | `load` (`HomePage.tsx:86`) | `HomePage.tsx:221` |
| 有灵感？先丢进收件箱，其他交给它… (read-only input) | An input that is `readOnly` and navigates on click — visual affordance, not a field | `onClick → navigate('/loop/inbox')` | `HomePage.tsx:280-287` |
| 去收件箱 ↗ | Navigates to the inbox | `navigate('/loop/inbox')` | `HomePage.tsx:288` |
| 另一条先放着，别催我 | Defers with reason `another_deferred_no_rush` | `deferAction('another_deferred_no_rush')` | `HomePage.tsx:293` |
| 周五晚再拾取 | Defers with reason `scheduled_pickup_friday` | `deferAction('scheduled_pickup_friday')` | `HomePage.tsx:296` |
| 查看内容项目 | Navigates to the content list | `navigate('/content')` | `HomePage.tsx:305` |

Data loaded on mount: `GET /today`, plus best-effort `GET /loop/inbox`,
`GET /loop/deliverables?status=ready`, `GET /loop/metrics?metric=weekly_minutes`,
`GET /loop/weekly?days=7` — each of the four side calls is wrapped in
`.catch(() => ({items: [], total: 0}))` (`HomePage.tsx:92-98`), so a failure there degrades
the quiet counters to 0 **without** surfacing an error. That is deliberate; a tester must
not report a silent 0 as a crash, but should report it if the *primary* `GET /today` fails
without the error banner.

### 3.3 `frontend/src/pages/Inbox/InboxPage.tsx` (收件箱) — 13 controls

| Label | What it does | Handler / API | file:line |
|---|---|---|---|
| 丢个灵感、想法，或一句真实经历… (textarea) | Draft material body | local state `draft` | `InboxPage.tsx:147-154` |
| 📸 选照片 | Sets draft kind to `image`; highlighted via `btn-primary` when active | `setDraftKind('image')` | `InboxPage.tsx:156` |
| 🎙 录语音 | Sets draft kind to `voice` | `setDraftKind('voice')` | `InboxPage.tsx:157` |
| ✎ 写一句 | Sets draft kind to `idea` (the default-highlight state also covers `text`) | `setDraftKind('idea')` | `InboxPage.tsx:158` |
| 🔗 贴链接 | Sets draft kind to `link` | `setDraftKind('link')` | `InboxPage.tsx:159` |
| 丢进去 | Adds the draft to the inbox; disabled when busy or the draft is blank | `addDraft` (`InboxPage.tsx:78`) → `POST /loop/inbox`; success notice `已丢进收件箱。` | `InboxPage.tsx:162` |
| 消化生产 / `消化中 第 {k} 条 · 已用 {n} 秒` | Produces deliverables one at a time in a loop until `remaining === 0` or a batch yields nothing | `digest` (`InboxPage.tsx:91`) → repeated `POST /loop/inbox/digest?limit=1` | `InboxPage.tsx:163-167` |
| 家人入镜？标记私密 | Toggles the consent flag between `private` and `publishable` | `setIsPrivate(!isPrivate)`; consumed by `addInboxItem({consent})` (`InboxPage.tsx:83`) | `InboxPage.tsx:171` |
| 去看产出架 → (appears only when the notice contains 产出了) | Navigates to the shelf | `navigate('/loop')` | `InboxPage.tsx:132` |
| 记一笔本周维护时长 | Reveals the minutes input | `setLoggingMinutes(true)` | `InboxPage.tsx:251-258` |
| 本周维护分钟数 (number input, `min=1 max=600`) | Minutes value | local state `minutesInput` | `InboxPage.tsx:210-221` |
| 记下 | Records the weekly maintenance minutes, clamped to 1..600 | inline handler (`InboxPage.tsx:226`) → `recordLoopMetric({metric:'weekly_minutes'})` → `POST /loop/metrics` | `InboxPage.tsx:222-238` |
| 取消 | Closes the minutes input and clears it | `setLoggingMinutes(false); setMinutesInput('')` | `InboxPage.tsx:239-248` |

Read-only regions: the 最近丢进来的 list (`InboxPage.tsx:177-193`) with per-item consent lock
and status text (待消化 / 已消化 / 消化失败, `InboxPage.tsx:188`), and 证伪线度量
(`InboxPage.tsx:195-206`, first 8 metrics via `loopMetricLabel`).

### 3.4 `frontend/src/pages/AsyncLoop/AsyncLoopPage.tsx` (产出架 / 灵感池) — 21 controls

| Label | What it does | Handler / API | file:line |
|---|---|---|---|
| Tab 待决定 ({n}) | Switches to the shelf view (`role="tab"`, `aria-selected`) | `setTab('shelf')` | `AsyncLoopPage.tsx:154-161` |
| Tab 灵感池 ({n}) | Switches to the pool view (`role="tab"`) | `setTab('pool')` | `AsyncLoopPage.tsx:163-171` |
| 重新上架 (pool card) | Re-shelves a pooled deliverable and resets its 7-day window | `restore` (`AsyncLoopPage.tsx:113`) → `POST /loop/deliverables/{id}:restore`; notice `已重新上架，观察窗重新计 7 天。` | `AsyncLoopPage.tsx:194-200` |
| 永久删除 (pool card) | `window.confirm` then irreversibly deletes the pooled deliverable | `removeFromPool` (`AsyncLoopPage.tsx:119`) → `DELETE /loop/deliverables/{id}`; notice `已永久删除。` | `AsyncLoopPage.tsx:202-213` |
| 问它 (pool card) | Opens companion with `灵感池 · {title}` | `openCompanion` | `AsyncLoopPage.tsx:214-220` |
| 去收件箱丢素材 → (empty shelf) | Navigate to the inbox | `navigate('/loop/inbox')` | `AsyncLoopPage.tsx:233` |
| Shelf card (click) | Selects the deliverable and seeds the pickup panel from its judgement | `setSelectedId` + seed `audience_change` / `content_intent` (`AsyncLoopPage.tsx:246`) | `AsyncLoopPage.tsx:243-247` |
| 拾取 (shelf card) | Toggles selection of that card | inline handler (`AsyncLoopPage.tsx:272`) | `AsyncLoopPage.tsx:269-275` |
| 问它 (shelf card) | Opens companion with `产出架 · {title}` | `openCompanion` | `AsyncLoopPage.tsx:276` |
| 希望读者的变化（必填） (textarea, 3 rows) | The audience-change statement that pickup will confirm; picking a card pre-fills it from `judgment.audience_change` | local state `audienceChange`; seeded at `AsyncLoopPage.tsx:132-137` | `AsyncLoopPage.tsx:332-339` |
| 教方法 (`solve`) chip | Sets the machine-mode intent; `aria-pressed` reflects selection | `setIntent('solve')` | `AsyncLoopPage.tsx:341-352` |
| 讲经历 (`share`) chip | Sets the intent to `share` | `setIntent('share')` | `AsyncLoopPage.tsx:341-352` |
| 记过程 (`record`) chip | Sets the intent to `record` | `setIntent('record')` | `AsyncLoopPage.tsx:341-352` |
| 认领 | Claims the deliverable → creates a ContentProject; disabled until the audience-change text is non-blank | `pickup` (`AsyncLoopPage.tsx:93`) → `POST /loop/deliverables/{id}:pickup`; notice `已认领。这条产出会在 7 天观察窗内等你发布。` | `AsyncLoopPage.tsx:357-364` |
| 问它 (pickup panel) | Opens companion with `产出架 · {title}` | `openCompanion` | `AsyncLoopPage.tsx:365` |
| 不选了 | Discards with reason `换换口味` | `discard(active, '换换口味')` (`AsyncLoopPage.tsx:104`) → `POST /loop/deliverables/{id}:discard`; notice `已回到灵感池。` | `AsyncLoopPage.tsx:368-375` |
| 太俗 | Discards with attribution `太俗` | `discard(active, '太俗')` | `AsyncLoopPage.tsx:379-383` |
| 选题不对 | Discards with attribution `选题不对` | `discard(active, '选题不对')` | `AsyncLoopPage.tsx:379-383` |
| 换换口味 | Discards with attribution `换换口味` | `discard(active, '换换口味')` | `AsyncLoopPage.tsx:379-383` |
| 时机不对 | Discards with attribution `时机不对` | `discard(active, '时机不对')` | `AsyncLoopPage.tsx:379-383` |

`DISCARD_REASONS` is declared at `AsyncLoopPage.tsx:32`. Read-only regions: the pickup
panel's 框架大纲 (`AsyncLoopPage.tsx:291-301`), 事实清单 with per-fact provenance
(`AsyncLoopPage.tsx:302-312`), and 发布判断草案 (`AsyncLoopPage.tsx:313-322`).

**Trap:** the shelf and pool tabs are local state, not URLs. Reloading on the pool tab always
returns to the shelf.

### 3.5 `frontend/src/pages/Urgent/UrgentPage.tsx` (急稿) — 8 controls

| Label | What it does | Handler / API | file:line |
|---|---|---|---|
| `刚发现阳台辣椒结果了…` (input) | Step-1 title/what-this-is-about | local state `title` | `UrgentPage.tsx:83-88` |
| `早上浇水时发现…` (textarea) | Step-2 one true experience; also becomes the key-question answer | local state `experience` | `UrgentPage.tsx:97-102` |
| 记过程 chip | Intent `record` | `setIntent('record')` | `UrgentPage.tsx:112-121` |
| 讲经历 chip | Intent `share` | `setIntent('share')` | `UrgentPage.tsx:112-121` |
| 教方法 chip | Intent `solve` | `setIntent('solve')` | `UrgentPage.tsx:112-121` |
| 让它判断 chip | Intent `''` — skips `confirmProjectIntent` entirely | `setIntent('')` | `UrgentPage.tsx:112-121` |
| 生成成品，进入发布检查 | Creates the project, optionally confirms intent, best-effort back-fills the key question, then lands in the workspace; disabled until **both** title and experience are non-blank | `submit` (`UrgentPage.tsx:27`) → `POST /projects` → conditional `POST /projects/{id}/intent:confirm` → `GET /projects/{id}/next-action` → conditional `POST /actions/{id}:respond` → `navigate('/content/{id}')` | `UrgentPage.tsx:132-139` |
| 存回收件箱，不急 | Abandons the urgent path and goes to the inbox | `navigate('/loop/inbox')` | `UrgentPage.tsx:140-142` |

The step-3 「结构预检」 block (`UrgentPage.tsx:123-126`) is static copy, not a control.
The back-fill in `UrgentPage.tsx:51-63` is wrapped in its own `try/catch` — a failure there
silently costs only the pre-filled answer (`UrgentPage.tsx:61-62`).

### 3.6 `frontend/src/pages/Review/ReviewPage.tsx` (周复盘) — 3 controls

| Label | What it does | Handler / API | file:line |
|---|---|---|---|
| `{row.title}` (Link) | Opens the project workspace for that row | `<Link to={`/content/${row.project_id}`}>` | `ReviewPage.tsx:61` |
| 问 | Opens companion with `周复盘 · {title}` | `openCompanion` | `ReviewPage.tsx:87` |
| 去项目工作台确认 (Link, styled as a button) | Navigates to `/content` — this page cannot confirm anything itself | `ReviewPage.tsx:96` | `ReviewPage.tsx:96` |

Stage pills (`ReviewPage.tsx:83-85`) are **non-interactive** indicators; the five stages are
defined at `ReviewPage.tsx:11-17` (`needs_snapshot` 待回填数据, `needs_review` 待盲评,
`review_insufficient` 数据不足, `ready_to_confirm` 待确认结论, `confirmed` 已确认), each with
a note at `ReviewPage.tsx:19-25`. Data comes from `GET /loop/weekly?days=60`
(`ReviewPage.tsx:32`).

### 3.7 `frontend/src/pages/Growth/GrowthPage.tsx` (成长) — 3 controls

| Label | What it does | Handler / API | file:line |
|---|---|---|---|
| 自主准备开关 (`aria-label="自主准备开关（即将开放）"`) | **Does nothing but show a notice.** Sets `trustNote` to `该能力将随后续版本开放，当前为展示状态。` and never calls an API | `onClick={() => setTrustNote(...)}` | `GrowthPage.tsx:101-109` |
| 探索位开关 (`aria-label="探索位开关"`) | Same: notice only, no API | `onClick={() => setTrustNote(...)}` | `GrowthPage.tsx:111-113` |
| 私密素材参与生产开关 (`aria-label="私密素材参与生产开关（保持关闭）"`) | **Has no `onClick` at all** — permanently `aria-pressed={false}` and inert | none | `GrowthPage.tsx:115-118` |

`trustNote` is rendered at `GrowthPage.tsx:119`. All counters come from
`GET /creator-state` + `GET /projects` + `GET /creator-viewpoints` + `GET /creator-series`
(`GrowthPage.tsx:26-31`); the last two are individually `.catch()`-guarded
(`GrowthPage.tsx:29-30`).

> **A6 — the trust panel is decorative.** Three toggles at `GrowthPage.tsx:99-118` render as
> switches but two only print a sentence and one is inert. `/me` has the *real*
> capability-trust read-out (`MePage.tsx:278-299`). A tester must record these as
> "display-only" rather than as failing controls, and must not expect an API call.

### 3.8 `frontend/src/pages/Me/MePage.tsx` (我的) — 20 controls

| Label | What it does | Handler / API | file:line |
|---|---|---|---|
| 每周发布目标 (number, `min=1 max=7`, required) | Weekly publish goal; clearing it sets `null` and disables save | local state `weeklyGoal`; `goalValid` at `MePage.tsx:81` | `MePage.tsx:220` |
| 内容策略 (multiline, required) | Free-text strategy; a known goal enum is humanised on load | local state `contentStrategy`; `humanizeGoal` at `MePage.tsx:88` | `MePage.tsx:221` |
| 小红书账号备注 | Account label only; helper text forbids passwords/tokens | local state `accountReference` | `MePage.tsx:222` |
| 每晚自动整理收件箱（03:00） (Switch) | Toggles the nightly auto-digest flag | local state `autoDigest` | `MePage.tsx:224-227` |
| 保存设置 | Persists settings with optimistic-concurrency `expected_version`; disabled unless the goal is a whole number 1..7 and the strategy is non-blank | `saveSettings` (`MePage.tsx:149`) → `PUT /settings`; notice `设置已保存` | `MePage.tsx:232` |
| 查看条件说明 / 收起条件说明 | Expands/collapses the auto-prepare explanation | `setShowTrustDetail` | `MePage.tsx:281` |
| 当前密码 | Current password | local state `currentPassword` | `MePage.tsx:239` |
| 新密码（至少 8 位） | New password; inline warning if identical to current | local state `newPassword` | `MePage.tsx:240-246` |
| 再输入一次新密码 | Confirmation; `error` styling when mismatched | local state `confirmNewPassword` | `MePage.tsx:247-254` |
| 更新密码 | Changes the password; disabled unless all three fields are valid and the new one differs | `submitPasswordChange` (`MePage.tsx:130`) → `POST /auth/password` | `MePage.tsx:257-263` |
| 重试 (error alert action) | Re-loads creator state, projects and settings | `load` (`MePage.tsx:93`) | `MePage.tsx:206` |
| 导出个人数据 | Opens the export human gate | `prepareExport` (`MePage.tsx:166`) → `POST /account/data-export:request` | `MePage.tsx:311` |
| 确认并下载 (inside the export Alert) | Decides the gate then downloads a JSON file client-side | `confirmExport` (`MePage.tsx:170`) → `POST /human-gates/{id}:decide` → `GET /account/data-export` → `saveJson` (`MePage.tsx:41-48`); notice `个人数据已导出` | `MePage.tsx:302` |
| 删除账户 | Opens the deletion human gate and clears any stale confirmation text | `prepareDeletion` (`MePage.tsx:182`) → `POST /account/deletion:request` | `MePage.tsx:312` |
| 删除确认 (TextField) | Must equal exactly `永久删除` | local state `deletionConfirmation`; constant at `MePage.tsx:38` | `MePage.tsx:306` |
| 永久删除账户 | Decides the gate, deletes the account, logs out and redirects | `confirmDeletion` (`MePage.tsx:189`) → `POST /human-gates/{id}:decide` → `DELETE /account?gate_id=…` → `logout()` → `navigate('/login')` | `MePage.tsx:307` |
| 导入历史内容并校对画像 | Navigate to growth onboarding | `navigate('/onboarding/growth')` | `MePage.tsx:316` |
| 贴参考，读出你想做成什么样 | Navigate to the reference anchor | `navigate('/onboarding/reference')` | `MePage.tsx:317` |
| 查看内容项目 | Navigate to the content list | `navigate('/content')` | `MePage.tsx:318` |
| 重试 (fallback alert when state/settings missing) | Re-loads | `load` | `MePage.tsx:321` |

Read-only panels worth asserting: the three summary stats (`MePage.tsx:208-212`), the current
goal + trust-level chip (`MePage.tsx:214`), the AI capability section
(`MePage.tsx:267-277`, including the explicit degradation paragraph at `MePage.tsx:274`), and
the per-capability trust list built from `AUTO_PREPARE_CAPABILITIES`
(`MePage.tsx:32-35`) with threshold `REQUIRED_ACCEPTED = 3` (`MePage.tsx:36`).

### 3.9 `frontend/src/pages/Starter/StarterPage.tsx` (起步实验, 3 routes) — 20 controls

**Shared**

| Label | What it does | Handler / API | file:line |
|---|---|---|---|
| 返回内容 | Leaves the starter flow | `navigate('/content')` | `StarterPage.tsx:119-121` |
| 重试 (error alert) | Re-fetches the workspace | `load` (`StarterPage.tsx:72`) → `GET /starter` | `StarterPage.tsx:122` |

**`AssessmentStep` (step 1 / 3)**

| Label | What it does | Handler / API | file:line |
|---|---|---|---|
| 为什么想开始 (select) | Motivation: 想试试看 / 为职业积累影响力 / 想表达和记录 / 其他 | `setMotivation` | `StarterPage.tsx:174-179` |
| 每周可投入小时 (number, 0..40) | Hours per week; kept as text so a cleared field stays editable | `setHoursText`; `hoursValid` at `StarterPage.tsx:152` | `StarterPage.tsx:180` |
| 你亲自经历过什么 (multiline) | One experience per line | `setExperiences`; split by `splitItems` (`StarterPage.tsx:40-41`) | `StarterPage.tsx:182` |
| 你愿意持续探索什么 (multiline) | One interest per line | `setInterests` | `StarterPage.tsx:183` |
| 你会做什么 (multiline) | One skill per line | `setSkills` | `StarterPage.tsx:184` |
| 哪些内容不要使用 (multiline) | Privacy limits | `setPrivacy` | `StarterPage.tsx:185` |
| 我愿意在 14 天内至少发布一篇 (Checkbox) | Publish commitment | `setPublish` | `StarterPage.tsx:187` |
| 我知道这只是一次实验，不是永久定位结论 (Checkbox) | Experiment acceptance | `setAcceptExperiment` | `StarterPage.tsx:188` |
| 保存并继续 | Saves the assessment; disabled without a valid hours value or at least one asset | `run` → `submitStarterAssessment` → `POST /starter/assessment`; notice text depends on commitment (`StarterPage.tsx:213-215`) | `StarterPage.tsx:192-220` |

**`DirectionStep` (step 2 / 3)**

| Label | What it does | Handler / API | file:line |
|---|---|---|---|
| 查看候选方向 | Generates the three direction candidates; disabled while busy | `generateStarterDirections` → `POST /starter/directions:generate` | `StarterPage.tsx:236-244` |
| 选择并创建三篇实验 (one per candidate, `DirectionOption`) | Selects that direction and creates the 3-project sprint | `selectStarterDirection(candidate.id, …)` → `POST /starter/directions/{id}:select` | `StarterPage.tsx:267-275` |

**`SprintStep` (step 3 / 3)**

| Label | What it does | Handler / API | file:line |
|---|---|---|---|
| `{index}. {project.title}` row (one per project) | Opens that project's workspace | `onOpenProject(project.id)` → `navigate('/content/{id}')` (`StarterPage.tsx:129`) | `StarterPage.tsx:293-297` |
| 继续当前实验 | Opens the first project that is not already published/awaiting_review/settled | `onOpenProject(firstOpenProject.id)`; selection at `StarterPage.tsx:286` | `StarterPage.tsx:303` |
| 这轮实际发生了什么 (multiline) | Sprint review summary; min 5 chars to enable submit | `setSummary` | `StarterPage.tsx:308` |
| 主要阻碍（最多 3 条） (multiline) | Blockers, truncated to 3 by `slice(0,3)` | `setBlockers` | `StarterPage.tsx:309` |
| 下一轮想测试什么（最多 3 条） (multiline) | Next topics, truncated to 3 | `setNextTopics` | `StarterPage.tsx:310` |
| 完成本轮复盘 | Closes the sprint review; only rendered once `published_count >= 1` | `reviewStarterSprint(sprint.id, …)` → `POST /starter/sprints/{id}:review` | `StarterPage.tsx:311-325` |

The 「本轮实验已完成」 success alert (`StarterPage.tsx:299-301`) appears once
`sprint.graduation_state === 'graduated'` and replaces the review form.

> **A7 — the three `/onboarding/*` URLs share one step machine** (see A2). Also note that
> `projectStatus` labels (`StarterPage.tsx:46-54`) include `inbox: '还未开始'` etc., so the
> per-project row's subtitle is driven by project status, not by the URL.

### 3.10 `frontend/src/pages/GrowthOnboarding/GrowthOnboardingPage.tsx` — 18 controls

| Label | What it does | Handler / API | file:line |
|---|---|---|---|
| 返回我的 | Leaves onboarding | `navigate('/me')` | `GrowthOnboardingPage.tsx:153` |
| 重试 (error alert) | Re-loads context + profile | `load` (`GrowthOnboardingPage.tsx:73`) → `GET /onboarding` + `GET /creator-profile` | `GrowthOnboardingPage.tsx:154` |
| 使用历史内容开始 | Switches the product into `growth` mode — only rendered while `context.mode !== 'growth'` | `selectProductMode('growth', version)` → `PUT /onboarding/mode` | `GrowthOnboardingPage.tsx:158-161` |
| 手动 (ToggleButton) | Import method = manual (one title per line) | `setMethod('manual')` | `GrowthOnboardingPage.tsx:167-171` |
| CSV (ToggleButton) | Import method = CSV (`title,body_excerpt,tags`) | `setMethod('csv')` | `GrowthOnboardingPage.tsx:167-171` |
| JSON (ToggleButton) | Import method = JSON array | `setMethod('json')` | `GrowthOnboardingPage.tsx:167-171` |
| 历史内容 (multiline, 7 rows) | The pasted history; placeholder changes per method (`GrowthOnboardingPage.tsx:178`) | `setHistoryText` | `GrowthOnboardingPage.tsx:172-179` |
| 导入历史内容 | Parses and imports; throws a visible error when nothing parses | `handleImport` (`GrowthOnboardingPage.tsx:109`) → `POST /history-imports`; result panel `成功 {n} 条，失败 {n} 条` (`GrowthOnboardingPage.tsx:181-192`) | `GrowthOnboardingPage.tsx:180` |
| 贴参考 (Alert action) | Jumps to the reference anchor as an alternative to filling the profile blind | `navigate('/onboarding/reference')` | `GrowthOnboardingPage.tsx:207` |
| 创作方向 (required) | Niche | `setNiche` | `GrowthOnboardingPage.tsx:212` |
| 成长目标 (select) | 稳定发布 / 粉丝增长学习 / 两者兼顾 | `setGrowthGoal` | `GrowthOnboardingPage.tsx:213-217` |
| 目标读者 (multiline, required) | Target audience | `setAudience` | `GrowthOnboardingPage.tsx:220` |
| 内容支柱 (multiline, required, max 5) | Content pillars, deduped and truncated by `splitValues(pillars, 5)` (`GrowthOnboardingPage.tsx:125`) | `setPillars` | `GrowthOnboardingPage.tsx:222` |
| 表达特点 (multiline) | Voice traits | `setVoiceTraits` | `GrowthOnboardingPage.tsx:226` |
| 明确避免 (multiline) | Avoid-traits | `setAvoidTraits` | `GrowthOnboardingPage.tsx:230` |
| 确认画像并继续 | Confirms the profile and returns home; disabled until niche, audience and ≥1 pillar are filled | `handleConfirm` (`GrowthOnboardingPage.tsx:122`) → `PUT /creator-profile` (with a computed `rejected` list, `GrowthOnboardingPage.tsx:127-134`) → `navigate('/')` | `GrowthOnboardingPage.tsx:231-236` |

Read-only: the per-attribute evidence rows built by `AttributeEvidence`
(`GrowthOnboardingPage.tsx:245-257`) showing status + confidence + evidence count, and the
`limitationLabel` mapping (`GrowthOnboardingPage.tsx:259-263`).

### 3.11 `frontend/src/pages/Onboarding/ReferenceAnchorPage.tsx` — 16 controls

| Label | What it does | Handler / API | file:line |
|---|---|---|---|
| 返回我的 | Leaves the page | `navigate('/me')` | `ReferenceAnchorPage.tsx:181-183` |
| 重试 (error alert) | Re-reads the anchor | `load` (`ReferenceAnchorPage.tsx:68`) → `GET /reference-anchor` | `ReferenceAnchorPage.tsx:185` |
| 参考内容 (multiline, 8 rows) | Pasted references; parsed live by `parseReferences` (`ReferenceAnchorPage.tsx:66`) | `setText` | `ReferenceAnchorPage.tsx:208-216` |
| 读这些参考 | Imports the parsed references and re-reads the anchor; disabled while busy, when nothing parsed, or when parse problems exist | `handleRead` (`ReferenceAnchorPage.tsx:88`) → `POST /reference-imports` then `GET /reference-anchor` | `ReferenceAnchorPage.tsx:237-244` |
| 收起 | Hides the composer when an anchor already exists | `setComposing(false)` | `ReferenceAnchorPage.tsx:246` |
| 不对 (one per anchor item, `AnchorBlock`) | Rejects one derived statement — never auto-derives it again | `reject(item.value)` (`ReferenceAnchorPage.tsx:141`) → `PUT /reference-anchor` with `rejected:[value]` | `ReferenceAnchorPage.tsx:384-392` |
| 都不对？我自己写 | Opens the manual rewrite form seeded from the current anchor | `openRewrite` (`ReferenceAnchorPage.tsx:146-151`) | `ReferenceAnchorPage.tsx:299-301` |
| 再贴几条 | Re-opens the composer to add more references | `setComposing(true)` | `ReferenceAnchorPage.tsx:302` |
| 选题范围 (multiline, max 5) | Manual topic list | `setDraftTopics` | `ReferenceAnchorPage.tsx:307-314` |
| 这类内容怎么写 (multiline, max 5) | Manual structure habits | `setDraftHabits` | `ReferenceAnchorPage.tsx:315-322` |
| 谁在看这类内容 | Manual audience | `setDraftAudience` | `ReferenceAnchorPage.tsx:323-327` |
| 以我说的为准 | Saves the manual override (user edits win over later auto-derivation) | `submitRewrite` (`ReferenceAnchorPage.tsx:153`) → `PUT /reference-anchor` | `ReferenceAnchorPage.tsx:332-334` |
| 取消 | Closes the rewrite form | `setRewriting(false)` | `ReferenceAnchorPage.tsx:335` |
| 开始写第一条内容 | Leaves onboarding for the content list | `navigate('/content')` | `ReferenceAnchorPage.tsx:344-346` |

Read-only: the parsed-reference preview chips and count hint (`ReferenceAnchorPage.tsx:217-232`),
the parsing-problem alerts (`ReferenceAnchorPage.tsx:233-235`), the capability chip
(`ReferenceAnchorPage.tsx:257`, labels at `ReferenceAnchorPage.tsx:29-33`), `source_handles`
(`ReferenceAnchorPage.tsx:259-261`), per-item `supportLabel` evidence counts
(`ReferenceAnchorPage.tsx:36-40`, rendered `ReferenceAnchorPage.tsx:379`), limitations
(`ReferenceAnchorPage.tsx:292-296`), and the reading progress block
(`ReferenceAnchorPage.tsx:190-200`).

**Timing contract:** the read itself is the slow step. `ReferenceAnchorPage.tsx:196-198`
tells the user it takes "十几秒". The reading state is driven by `setReading(true/false)`
(`ReferenceAnchorPage.tsx:94`, `:118`). A tester must wait rather than assume a hang.

### 3.12 `frontend/src/pages/Opportunities/OpportunitiesPage.tsx` — 30 controls

**Toolbar / page level**

| Label | What it does | Handler / API | file:line |
|---|---|---|---|
| 全部 | Status filter = all | `setFilter('all')` | `OpportunitiesPage.tsx:363-365` |
| 待确认 | Filter = `proposed` | `setFilter('proposed')` | `OpportunitiesPage.tsx:363-365` |
| 已收藏 | Filter = `saved` | `setFilter('saved')` | `OpportunitiesPage.tsx:363-365` |
| 已采用 | Filter = `accepted` | `setFilter('accepted')` | `OpportunitiesPage.tsx:363-365` |
| 已放弃 | Filter = `rejected` | `setFilter('rejected')` | `OpportunitiesPage.tsx:363-365` |
| 筛选 / 收起筛选 | Mobile-only toggle that reveals the two selects (hidden at `sm`+) | `setFiltersOpen` | `OpportunitiesPage.tsx:370-378` |
| 来源类型筛选 (select) | Filters by `opportunity_type`: 全部来源 / 历史内容 / 受众问题 / 个人素材 / 确认洞察 / 系列延展 / 常青需求 / 手动来源 | `setSourceFilter` | `OpportunitiesPage.tsx:379-395` |
| 时效筛选 (select) | Filters by `dimensions.timeliness` | `setTimelinessFilter` | `OpportunitiesPage.tsx:396-410` |
| 生成内容机会 / 生成中... | Generates up to 6 opportunities and merges them to the top of the list | `generate` (`OpportunitiesPage.tsx:304`) → `POST /content-opportunities:generate`; notice explains the empty case (`OpportunitiesPage.tsx:314-316`) | `OpportunitiesPage.tsx:411-413` |
| 手动添加来源 | Toggles the manual-source form | `setManualOpen` | `OpportunitiesPage.tsx:414-416` |
| 关键词或原始内容 (multiline) | The only manual-source field; trigger is fixed to `user_keyword` | `setManualText`; `manualTrigger` at `OpportunitiesPage.tsx:271` | `OpportunitiesPage.tsx:422` |
| 保存并等待核验 | Creates a user-sourced opportunity that still needs verification; disabled while blank/submitting | `submitManual` (`OpportunitiesPage.tsx:323`) → `POST /content-opportunities/source-verification` | `OpportunitiesPage.tsx:424` |
| 重试 (error alert) | Re-lists opportunities | `load` (`OpportunitiesPage.tsx:285`) → `GET /content-opportunities` | `OpportunitiesPage.tsx:359` |
| 查看内容项目 (empty state) | Navigate to the content list | `navigate('/content')` | `OpportunitiesPage.tsx:433` |
| 打开此来源 / 查看原始来源 (`SourceLink` anchors) | Opens the source URL **only** when the protocol is http/https; otherwise renders as inert text with a warning | `isSafeExternalUrl` (`OpportunitiesPage.tsx:59-66`), render at `OpportunitiesPage.tsx:68-73` | `OpportunitiesPage.tsx:190`, `:193` |

**Per opportunity row (`OpportunityRow`, `OpportunitiesPage.tsx:75-257`)**

| Label | What it does | Handler / API | file:line |
|---|---|---|---|
| 原始链接 | Source URL for verification | `setSourceUrl` | `OpportunitiesPage.tsx:219` |
| 发布时间 | Source publish timestamp (placeholder `2026-07-31T00:00:00Z`) | `setPublishedAt` | `OpportunitiesPage.tsx:220` |
| 权威来源 | Who published it | `setSourceAuthority` | `OpportunitiesPage.tsx:221` |
| 当前时效 (select) | 当前有效 / 即将过期 / 已过期; defaults to `expired` when the required action is `source_expired` (`OpportunitiesPage.tsx:94-96`) | `setTimeliness` | `OpportunitiesPage.tsx:222-226` |
| 确认来源信息 | Verifies the source; disabled until all three text fields are non-blank | `verifySource('verified')` (`OpportunitiesPage.tsx:131`) → `POST /content-opportunities/{id}:verify-source` | `OpportunitiesPage.tsx:229` |
| 标记来源不足 | Records an insufficient-source verdict | `verifySource('insufficient')` | `OpportunitiesPage.tsx:230` |
| 保留原始输入 | Saves the opportunity as-is (only shown while `status === 'proposed'`) | `decide('save')` (`OpportunitiesPage.tsx:103`) → `POST /content-opportunities/{id}:decide` | `OpportunitiesPage.tsx:231` |
| 这篇内容的标题 | Confirmed title (only after verification succeeds) | `setTitle` | `OpportunitiesPage.tsx:239` |
| 希望读者看完发生什么变化 (multiline) | Confirmed audience change | `setAudienceChange` | `OpportunitiesPage.tsx:240` |
| 需要的真实素材（每行一项） (multiline) | Confirmed material requirements, split on newlines | `setMaterials` | `OpportunitiesPage.tsx:241` |
| 采用并创建内容 | Adopts the opportunity and creates the project; disabled without title + audience change | `decide('accept')` | `OpportunitiesPage.tsx:244` |
| 稍后再做 | Saves for later (only while `proposed`) | `decide('save')` | `OpportunitiesPage.tsx:245` |
| 这次不做 | Rejects the opportunity | `decide('reject')` | `OpportunitiesPage.tsx:246` |
| 继续这条内容 | Opens the project created from this opportunity | `navigate('/content/{created_project_id}')` | `OpportunitiesPage.tsx:250-254` |

The warning alert above the verification form has three distinct strings depending on state
(`OpportunitiesPage.tsx:209-216`) — a tester can distinguish 来源已过期 / 来源信息不足 /
来源尚未核验 by the exact text.

### 3.13 `frontend/src/pages/Materials/MaterialsPage.tsx` — 16 controls

| Label | What it does | Handler / API | file:line |
|---|---|---|---|
| 添加素材 | Toggles the create form | `setShowCreate` | `MaterialsPage.tsx:204-206` |
| 素材类型 (select) | 文字 / 链接 / 图片 / 文档 / 音频 / 视频 | `setKind`; labels at `MaterialsPage.tsx:26-34` | `MaterialsPage.tsx:211-213` |
| 素材标题 (required) | Title | `setTitle` | `MaterialsPage.tsx:214` |
| 选择文件 / `{file.name}` | File picker; only for image/document/audio/video, accept-filtered per kind (`MaterialsPage.tsx:35-39`) | `setFile` | `MaterialsPage.tsx:216-219` |
| 素材内容 (multiline for text, `type=url` for link) | Inline content for text/link kinds | `setContent` | `MaterialsPage.tsx:221` |
| 隐私级别 (select) | 公开 / 私密 / 敏感 | `setPrivacy`; labels at `MaterialsPage.tsx:25` | `MaterialsPage.tsx:223-225` |
| 关联项目 (select) | Optional immediate project link; only non-settled projects are listed (`MaterialsPage.tsx:87`) | `setProjectId` | `MaterialsPage.tsx:226-229` |
| 保存素材 | Creates the material; disabled until title + (file or content) are present | `save` (`MaterialsPage.tsx:100`) → `POST /materials`; notice `素材已保存。` | `MaterialsPage.tsx:231` |
| 取消 | Closes the create form | `setShowCreate(false)` | `MaterialsPage.tsx:232` |
| 重试 (error alert) | Re-loads materials + projects | `load` (`MaterialsPage.tsx:82`) | `MaterialsPage.tsx:237` |
| 复用到项目 (select, per material) | Picks a project not already using this material | `setReuseProject` | `MaterialsPage.tsx:280-290` |
| 关联 (per material) | Records a material usage; disabled until a project is picked | `link(material.id)` (`MaterialsPage.tsx:136`) → `POST /materials/{id}/usages`; notice `素材已关联到所选项目。` | `MaterialsPage.tsx:291` |
| 识别内容 / 重新识别 (audio & video only) | Sends the material to the multimodal model and writes the text back | `analyze(material.id)` (`MaterialsPage.tsx:183`) → `POST /materials/{id}:analyze`; notice `识别完成：…` | `MaterialsPage.tsx:292-300` |
| 删除 (per material) | First delete attempt; a reference conflict renders the impact alert instead of an error | `remove(material)` (`MaterialsPage.tsx:164`) → `DELETE /materials/{id}?confirmed=false` | `MaterialsPage.tsx:301` |
| 保留引用快照并删除 (impact alert) | Force-deletes while keeping reference snapshots | `remove(material, true)` → `DELETE /materials/{id}?confirmed=true`; notice `素材已删除。` | `MaterialsPage.tsx:270` |
| 取消 (impact alert) | Clears the pending delete impact | `setDeleteImpact({[id]: []})` | `MaterialsPage.tsx:272` |

Model-provenance copy a tester must verify: when `material.analysis` exists the page says the
text was read by a model and may be wrong (`MaterialsPage.tsx:249-254`); for audio/video with
no content yet it warns the file will be sent to an external model and that sensitive
materials are not sent (`MaterialsPage.tsx:255-261`).

### 3.14 `frontend/src/pages/NotFound/NotFoundPage.tsx` — 1 control

| Label | What it does | Handler / API | file:line |
|---|---|---|---|
| 返回首页 | `EmptyState` action → home | `navigate('/')` (`NotFoundPage.tsx:22`) | `NotFoundPage.tsx:21` |

### 3.15 `frontend/src/pages/Content/ContentPage.tsx` — 36 controls

**A. Project-list view (no `:projectId`, `ContentPage.tsx:292-365`)**

| Label | What it does | Handler / API | file:line |
|---|---|---|---|
| 新建项目 | Opens the `ProjectStartPanel`; **not rendered when the list is empty** | `setShowCreate(true)` | `ContentPage.tsx:302-304` |
| 重试 (error alert) | Re-loads the list | `load` (`ContentPage.tsx:178`) | `ContentPage.tsx:308` |
| 开始起步实验 | Enters the bounded starter experiment (empty state only) | `navigate('/onboarding/assessment')` | `ContentPage.tsx:317` |
| 贴参考，读方向 | Enters the reference anchor (empty state only) | `navigate('/onboarding/reference')` | `ContentPage.tsx:318` |
| `{project.title}` row (one per project) | Opens that project's workspace; right side shows the short next-action label | `navigate('/content/{id}')` | `ContentPage.tsx:339-359` |

**B. Workspace-view shell (`ContentPage.tsx:388-576`)**

| Label | What it does | Handler / API | file:line |
|---|---|---|---|
| 重试 (error alert) | Re-loads the workspace | `load` | `ContentPage.tsx:391` |
| 项目素材 | Opens the right-hand materials drawer | `setMaterialsOpen(true)` | `ContentPage.tsx:393-399` |
| 不对，我自己选 (AI-inference banner) | Discards the AI-inferred intent, clears the nav state and drops the project back to manual intent confirmation | `navigate(location.pathname, {replace:true, state:null})` + `dismissStartInference(projectId)` → `POST /projects/{id}:dismiss-inference` | `ContentPage.tsx:421-435` |
| 管理全部 (drawer) | Navigates to the full materials page | `navigate('/materials')` (`ContentPage.tsx:407`) | `ContentPage.tsx:608` |
| 关联到当前项目 / 已关联当前项目 (drawer, per material) | Links an existing material to this project; disabled when already linked | `addMaterialUsage` → `POST /materials/{id}/usages` (`ContentPage.tsx:408-411`) | `ContentPage.tsx:627-634` |
| 添加素材 (drawer empty state) | Navigates to the materials page | `navigate('/materials')` (`ContentPage.tsx:407`) | `ContentPage.tsx:639` |
| 重试 (not-found alert) | Re-loads | `load` | `ContentPage.tsx:373` |
| 返回项目列表 (not-found alert) | Back to the list | `navigate('/content')` | `ContentPage.tsx:377` |

**C. `IntentActionPanel` (`ContentPage.tsx:668-905`)**

| Label | What it does | Handler / API | file:line |
|---|---|---|---|
| 回溯意图 (select) | Retrospective classification for legacy published content | `setIntent` | `ContentPage.tsx:731-735` |
| 判断依据 (multiline) | Why the user classified it that way; required | `setClassificationBasis` | `ContentPage.tsx:736` |
| 确认回溯分类 | Writes the retrospective intent only; disabled without a basis | `classifyRetrospectiveIntent` → `POST /projects/{id}/intent:classify-retrospective` | `ContentPage.tsx:738` |
| 希望读者发生的变化 (multiline) | The open question "what does the reader take away"; pre-filled with the intent-specific generic line | `setAudienceChange`; seed at `ContentPage.tsx:686-688` | `ContentPage.tsx:763-773` |
| 处理方式 (select) | 教方法 / 讲经历 / 记过程 — explicitly framed as machine routing, not content taxonomy | `setIntent` | `ContentPage.tsx:775-785` |
| 确认这个方向 | Confirms intent, audience change, material requirements, expected responses and signals | `confirmProjectIntent` → `POST /projects/{id}/intent:confirm` | `ContentPage.tsx:787` |
| 确认并准备候选内容 (evidence gate) | Confirms the quoted user fact so AI may use it | `decideHumanGate(gate.id, {decision:'confirm', decision_payload:{evidence_confirmed:true}})` → `POST /human-gates/{id}:decide` | `ContentPage.tsx:805-817` |
| 不使用这段经历 (evidence gate) | Rejects the fact for this project | `decideHumanGate(…, {evidence_confirmed:false})` | `ContentPage.tsx:818-829` |
| 你的回答 (multiline, 6 rows) | The answer to the AI's key question; needs ≥10 chars | `setAnswer`; guard at `ContentPage.tsx:851` | `ContentPage.tsx:850` |
| 让 AI 准备候选内容 | Accepts the action and submits the answer | `respondToAction(action.id, {decision:'accept', response_payload:{answer}})` → `POST /actions/{id}:respond` | `ContentPage.tsx:851` |
| 下一步 (select, unknown-outcome branch) | Follow-up option when the result is unknown | `setSelectedFollowUp`; options from `plan.follow_up_options` | `ContentPage.tsx:948-957` |
| 确认未知结果和下一步 | Records the unknown outcome + chosen follow-up; **never** writes verified learning | `decideHumanGate(…, {intent_outcome:'unknown', review_follow_up})` | `ContentPage.tsx:959-973` |
| 重试 (learning gate error) | Re-attempts `openHumanGate` | `retryGate` (`ContentPage.tsx:712-715`) | `ContentPage.tsx:975`, `:1023` |
| 确认并保存下一轮实验 | Confirms the learning plan (one continue / stop / experiment) | `decideHumanGate(…, {learning_confirmed:true})` | `ContentPage.tsx:997-1008` |
| 暂不保存 | Rejects the learning plan | `decideHumanGate(…, {learning_confirmed:false})` | `ContentPage.tsx:1009-1020` |
| 确认候选内容并进入发布准备 | Confirms facts + expression + public scope in one gate payload | `decideHumanGate(…, {facts_confirmed, expression_confirmed, public_scope_confirmed})` | `ContentPage.tsx:899` |

**D. `CandidateReviewPanel` (`ContentPage.tsx:1041-1182`)**

| Label | What it does | Handler / API | file:line |
|---|---|---|---|
| 替换这一段 (multiline) | Replacement text, shown only for a rejected segment | `setReplacements` | `ContentPage.tsx:1106-1113` |
| 提交替换内容 | Submits the replacement | `decide(segment,'replace')` → `decideCandidateSegment` → `POST /projects/{id}/candidate-review/segments/{seg}:decide` | `ContentPage.tsx:1114` |
| 重新修改这一段 | Re-opens a segment that already has a decision | `setReopenIds` | `ContentPage.tsx:1120` |
| 确认保留 | Accepts a segment | `decide(segment,'accept')` | `ContentPage.tsx:1124` |
| 拒绝这一段 | Rejects a segment (then offers replacement) | `decide(segment,'reject')` | `ContentPage.tsx:1125` |
| 生成确认后的新版本 | Produces a revision from all segment decisions; only when `can_prepare_revision` | `reviseCandidate` → `POST /projects/{id}/candidate-review:revise` | `ContentPage.tsx:1145-1155` |
| 恢复上一版并重新确认 | Restores the parent version; only when `parent_version` exists | `restoreCandidateVersion` → `POST /projects/{id}/candidate-review:restore` | `ContentPage.tsx:1158-1170` |

Segment rows carry `data-testid="candidate-segment"` and `data-status` ∈
`pending|accepted|rejected|replaced` (`ContentPage.tsx:1093-1094`), which is exactly what the
E2E suites loop on (`frontend/e2e/intent-driven-loop.spec.ts:87-96`). Use these hooks in an
automated run instead of matching Chinese labels.

**E. `StageAction` routing (`ContentPage.tsx:1191-1245`)**

`StageAction` is a pure switch on `workspace.next_action` and renders exactly one form:

| `next_action` | Form rendered | Citation |
|---|---|---|
| `create_version` | `VersionForm` | `ContentPage.tsx:1204-1205` |
| `lock_hypothesis` | `HypothesisForm` | `ContentPage.tsx:1206-1207` |
| `record_publication` | `PublicationForm` | `ContentPage.tsx:1208-1209` |
| `await_observation_window` | deadline alert + `SnapshotForm` | `ContentPage.tsx:1210-1227` |
| `add_snapshot` | `SnapshotForm` | `ContentPage.tsx:1228-1229` |
| `run_blind_review` | `BlindReviewAction` | `ContentPage.tsx:1230-1231` |
| `create_observation` | `ObservationForm` | `ContentPage.tsx:1232-1233` |
| `add_comparable_snapshot` | `SnapshotForm` | `ContentPage.tsx:1234-1235` |
| `review_calibration_issue` | a static error alert (no controls) | `ContentPage.tsx:1236-1237` |
| `manage_observations` | `null` (the observation list below carries the actions) | `ContentPage.tsx:1238-1239` |
| unknown | `null` | `ContentPage.tsx:1240-1243` |

Which panel actually wins is decided at `ContentPage.tsx:443-457`: a cancelled AI action shows
`StageAction` with an 「AI 已停止这条建议」 notice; `confirm_intent`, `answer_key_question`,
`review_candidate` (and `confirm_learning` when the next action is `create_observation`) route
to `IntentActionPanel`; everything else falls through to `StageAction`.

### 3.16 `frontend/src/features/content/ProjectWorkspace.tsx` — 11 controls

| Label | What it does | Handler / API | file:line |
|---|---|---|---|
| 返回内容列表 (icon button, `aria-label`) | Back to the project list | `onBack` → `navigate('/content')` (`ContentPage.tsx:458`) | `ProjectWorkspace.tsx:392-394` |
| 刷新 | Re-fetches the workspace | `onRefresh` → `load()` (`ContentPage.tsx:459`) | `ProjectWorkspace.tsx:406-409` |
| 进度 · {n}/{5} 步 | Toggles the progress outline column; `aria-expanded` | `setShowProgress` | `ProjectWorkspace.tsx:433-441` |
| 参考与提醒 · {n} 条 | Toggles the right-hand suggestions column; `aria-expanded`; **expanded by default** | `setShowTips` (initial `true`, `ProjectWorkspace.tsx:223`) | `ProjectWorkspace.tsx:442-450` |
| 当前内容标题 (`aria-label`) | Title editor; disabled while busy | `setTitle` | `ProjectWorkspace.tsx:555-561` |
| 当前内容正文 (`aria-label`) | Body editor; disabled while busy | `setBodyText` | `ProjectWorkspace.tsx:562-570` |
| 保存修改 | Saves a new version; disabled offline, while busy, or when title/body are blank | `saveVersion` (`ProjectWorkspace.tsx:304`) → `onSaveVersion` → `createContentVersion` (`ContentPage.tsx:460-472`) → `POST /projects/{id}/versions` | `ProjectWorkspace.tsx:573-581` |
| 恢复 (draft alert) | Restores the locally persisted draft | `restoreDraft` (`ProjectWorkspace.tsx:292`) | `ProjectWorkspace.tsx:518` |
| 丢弃 (draft alert) | Deletes the local draft | `discardDraft` (`ProjectWorkspace.tsx:299`) | `ProjectWorkspace.tsx:519` |
| 知道了 / 已保留 (per suggestion) | Marks a suggestion as accepted (local state only — never persisted) | `setAcceptedSuggestions` | `ProjectWorkspace.tsx:709-711` |
| 忽略 (per suggestion) | Marks a suggestion as ignored (local state only) | `setRejectedSuggestions` | `ProjectWorkspace.tsx:712-714` |

Non-control behaviour a tester must verify:
- **Offline draft protection.** Editing while offline writes the draft to `localStorage`
  (`ProjectWorkspace.tsx:251-269`) and shows 「当前离线，修改已保存在此设备」 only when there
  are unsaved changes (`ProjectWorkspace.tsx:526-528`). A `beforeunload` guard is registered
  while dirty (`ProjectWorkspace.tsx:282-290`). This is exactly what
  `frontend/e2e/intent-driven-loop.spec.ts:114-125` exercises.
- **Suggestion count.** `suggestions` is always `[]` at construction
  (`ProjectWorkspace.tsx:317`) and never pushed to, so `参考与提醒` never shows a count and the
  right column always renders 「现在没有需要提醒你的事情。」 (`ProjectWorkspace.tsx:699`). The
  two push sites (`ProjectWorkspace.tsx:331-354`) are dead code — flag as a likely regression.
- **Content lock label.** `发布版本已保留` vs `可继续修改` (`ProjectWorkspace.tsx:509`) is
  derived from `locked_publish_version_id === current_version.id`
  (`ProjectWorkspace.tsx:356`).

### 3.17 `frontend/src/features/content/StageForms.tsx` — 48 controls

**`ProjectCreateForm` (`StageForms.tsx:163-276`) — 7 controls, currently unreferenced**

| Label | What it does | Handler / API | file:line |
|---|---|---|---|
| 项目标题 (required) | Title | `setTitle` | `StageForms.tsx:201-208` |
| 更多选项（读者、方向、目标——都可以留空，AI 会先判断） / 收起更多选项 | Toggles the advanced fields; `aria-expanded` | `setShowAdvanced` | `StageForms.tsx:210-219` |
| 你想到的读者（可留空） (multiline) | Target audience | `setAudience` | `StageForms.tsx:222-230` |
| 处理方式 (select) | 不确定，让 AI 先判断 / 教方法 / 讲经历 / 记过程 | `setIntent` | `StageForms.tsx:231-242` |
| 希望读者发生什么变化（可留空） (multiline) | Audience change | `setAudienceChange` | `StageForms.tsx:243-250` |
| 本轮目标 (select) | 稳定更新 / 涨粉验证 / 内容实验 | `setGoal` | `StageForms.tsx:251-260` |
| 创建项目 | Creates the project; disabled without a title | `submit` (`StageForms.tsx:179`) → `onCommand(createProject)` → `POST /projects` | `StageForms.tsx:264-271` |

> **A8 — `ProjectCreateForm` is exported but never imported.** The only references are its own
> definition (`StageForms.tsx:163`) and its test (`frontend/src/features/content/__tests__/StageForms.test.tsx`).
> The live creation path is `ProjectStartPanel`. A tester cannot reach these seven controls
> through the UI; they exist as dead code. Do not spend manual-run time on them, but do report
> the orphan.

**`VersionForm` (`StageForms.tsx:292-350`) — 3 controls**

| Label | What it does | Handler / API | file:line |
|---|---|---|---|
| 笔记标题 | Version title, seeded from the project title | `setTitle`; re-seeded on project switch (`StageForms.tsx:303-308`) | `StageForms.tsx:318` |
| 你想分享的真实经历 (multiline, 8 rows) | The body | `setBody` | `StageForms.tsx:319-326` |
| 保存并继续 | Saves the version; disabled without title + body | `createVersion(projectId, …)` → `POST /projects/{id}/versions` | `StageForms.tsx:328-345` |

**`HypothesisForm` (`StageForms.tsx:361-636`) — 18 controls**

| Label | What it does | Handler / API | file:line |
|---|---|---|---|
| AI direction chips + 换一批 (audience_change) | `FieldSuggestions` instance; see §3.19 | `POST /projects/{id}/field-suggestions` | `StageForms.tsx:425-431` |
| 预期受众变化 (multiline) | Primary hypothesis field | `setAudienceChange` | `StageForms.tsx:432-439` |
| AI direction chips (audience_problem) | `solve` only | `FieldSuggestions` | `StageForms.tsx:441-447` |
| 读者遇到什么问题 (multiline) | `solve` only | `setProblem` | `StageForms.tsx:448-455` |
| AI direction chips (reader_promise) | `solve` only | `FieldSuggestions` | `StageForms.tsx:456-462` |
| 你准备给出的答案 (multiline) | `solve` only | `setPromise` | `StageForms.tsx:463-470` |
| AI direction chips (viewpoint_anchor) | `share` only | `FieldSuggestions` | `StageForms.tsx:474-480` |
| 创作者视角或经历锚点 (multiline) | `share` only | `setViewpoint` | `StageForms.tsx:481-488` |
| AI direction chips (continuation_promise) | `record` only | `FieldSuggestions` | `StageForms.tsx:493-499` |
| 读者可持续关注的过程或变化 (multiline) | `record` only | `setContinuation` | `StageForms.tsx:500-507` |
| 主要反应 (select) | 收藏 / 评论 / 主页访问 / 关注; selecting one removes it from the supporting set | `setPrimaryResponse` (`StageForms.tsx:514-518`); options from `PRIMARY_RESPONSE_LABELS` (`frontend/src/features/content/labels.ts:13-18`) | `StageForms.tsx:510-524` |
| 高级（可选）：附加反应与判断依据 / 收起高级选项 | Toggles advanced fields; `aria-expanded` | `setShowAdvanced` | `StageForms.tsx:526-534` |
| 附加反应 (max 2 checkboxes) | Supporting responses; extra boxes disable at 2 | `setSupportingResponses` (`StageForms.tsx:551-557`) | `StageForms.tsx:543-561` |
| 你为什么这样判断（可选） (multiline) | `basis_refs`, one per line | `setBasis` | `StageForms.tsx:564-571` |
| 你还不确定什么（可选） (multiline) | `uncertainties`, one per line | `setUncertainties` | `StageForms.tsx:572-579` |
| 观察窗口（天） (number, 1..365) | Observation window; submit disabled outside 1..365 | `setObservationWindow`; guard at `StageForms.tsx:594-598` | `StageForms.tsx:582-589` |
| 锁定发布意图 | Locks the hypothesis | `lockHypothesis(projectId, …)` → `POST /projects/{id}/publish-hypothesis:lock` | `StageForms.tsx:591-631` |

**`PublicationForm` (`StageForms.tsx:660-929`) — 9 controls**

| Label | What it does | Handler / API | file:line |
|---|---|---|---|
| 复制正文 / 正文已复制 | Copies `version.body_text` to the clipboard | `copyBody` (`StageForms.tsx:771-783`); errors when the clipboard API is unavailable | `StageForms.tsx:829-831` |
| 下载正文 / 正文已下载 | Downloads the body as a `.txt` file | `downloadArtifact('body')` (`StageForms.tsx:785`) → `saveText` (`StageForms.tsx:101-103`) | `StageForms.tsx:832-834` |
| 导出配图 PNG / 配图已导出 | Renders the cover plan + image plan to a 1080px-wide canvas and downloads a PNG | `downloadArtifact('images')` → `saveImagePlan` (`StageForms.tsx:127-152`) | `StageForms.tsx:835-837` |
| 运行检查 / 重新检查 | Runs the version-bound publish check | `runCheck` (`StageForms.tsx:752`) → `POST /projects/{id}/publish-checks` | `StageForms.tsx:853-855` |
| 我已了解 (per finding) | Acknowledges one finding | `acknowledge(finding.id)` (`StageForms.tsx:762`) → `PUT /publish-checks/{id}/resolution` | `StageForms.tsx:868` |
| 小红书笔记链接 | Note URL | `setUrl` | `StageForms.tsx:873-879` |
| 发布时间 (datetime-local) | Publish timestamp | `setPublishedAt`; validated at `StageForms.tsx:893` | `StageForms.tsx:880-888` |
| 确认已发布 | Decides the publication gate then records the publish; disabled unless the check is `clear`, current and bound to the locked version | `decideHumanGate` then `recordPublication` → `POST /projects/{id}/publish-records` (`StageForms.tsx:894-921`); `checkReady` at `StageForms.tsx:744-749` | `StageForms.tsx:890-924` |
| 重试 (gate error alert) | Retries `openHumanGate` | `setGateAttempt` (`StageForms.tsx:816`) | `StageForms.tsx:816` |

Check-status chip states a tester must distinguish (`StageForms.tsx:844-852`): 可以发布
(`clear`, not stale, bound to the locked version), 检查已过期 (`stale`), 需要确认
(open findings), 正在读取检查结果… (loading), 先运行发布前检查 (no check exists).

**`SnapshotForm` (`StageForms.tsx:953-1143`) — 14 controls**

| Label | What it does | Handler / API | file:line |
|---|---|---|---|
| 数据时间 (datetime-local, required) | Snapshot timestamp | `setCapturedAt` | `StageForms.tsx:1019-1027` |
| 最终无法取得这次结果 (Checkbox) | Switches into the "unavailable" branch; clears metrics and any proposal | `setUnavailable(true)` (`StageForms.tsx:1033-1040`) | `StageForms.tsx:1028-1043` |
| 无法取得的原因 (multiline, required in this branch) | Reason text; required for the submit button | `setUnavailableReason` | `StageForms.tsx:1045-1054` |
| 选择数据截图 / `{screenshot.name}` | Screenshot picker (`image/*`); resets material id and proposal | `setScreenshot` (`StageForms.tsx:1060-1065`) | `StageForms.tsx:1058-1066` |
| 识别截图数据 | Uploads the screenshot as a `sensitive` image material and asks the vision model for metrics | `extractScreenshot` (`StageForms.tsx:981`) → `POST /materials` then `POST /snapshots:extract` | `StageForms.tsx:1067` |
| 6 metric fields (浏览 / 点赞 / 收藏 / 评论 / 分享 / 新增关注) | Performance metrics; each `aria-label` is the Chinese label; `min=0` is only a hint, and every entered value must be a finite non-negative integer (`StageForms.tsx:975-979`) | `setValues`; labels from `METRIC_LABELS` (`labels.ts:4-11`) | `StageForms.tsx:1075-1086` |
| 我已逐项核对截图识别结果 (Checkbox) | Mandatory confirmation before saving a screenshot-derived snapshot | `setProposalConfirmed` | `StageForms.tsx:1089-1092` |
| 保存数据快照 / 确认结果不可用 | Appends the snapshot; label and payload depend on the unavailable branch | `appendSnapshot(record.id, …)` → `POST /publish-records/{id}/snapshots` (`StageForms.tsx:1105-1135`); guard at `StageForms.tsx:1100-1104` | `StageForms.tsx:1097-1138` |

The screenshot proposal is explicitly labelled as an unconfirmed draft
(`StageForms.tsx:1069-1073`), and the saved payload records `source: 'screenshot'` vs
`'manual'` and `result_availability: 'unavailable'` vs `'observed'`
(`StageForms.tsx:1117-1118`).

> **A9 — `FormControlLabel` without a wrapping form.** The 「我已逐项核对截图识别结果」
> checkbox at `StageForms.tsx:1089-1092` is fine, but note the metric grid renders
> `TextField`s with `type="number"` and no `required`, so an entirely empty snapshot is
> rejected by the button guard rather than by validation messaging. Expected.

**`BlindReviewAction` (`StageForms.tsx:1153-1189`) — 1 control**

| Label | What it does | Handler / API | file:line |
|---|---|---|---|
| 查看这次结果 | Creates the blind review from the latest snapshot; disabled when no snapshot exists | `createBlindReview` → `POST /projects/{id}/blind-reviews` | `StageForms.tsx:1169-1186` |

**`ObservationForm` (`StageForms.tsx:1201-1262`) — 3 controls**

| Label | What it does | Handler / API | file:line |
|---|---|---|---|
| 这次看到了什么 (multiline) | Observation statement | `setStatement` | `StageForms.tsx:1220-1226` |
| 下一次怎么验证 (multiline) | Next test | `setNextTest` | `StageForms.tsx:1227-1233` |
| 保存观察 | Creates the observation; disabled without both fields | `createObservation(review.id, {statement, scope:{platform:'xiaohongshu',format:'graphic_note'}, next_test})` → `POST /blind-reviews/{id}/observations` | `StageForms.tsx:1238-1257` |

### 3.18 `frontend/src/features/content/ObservationList.tsx` — 16 controls

| Label | What it does | Handler / API | file:line |
|---|---|---|---|
| 继续验证 | Moves the observation to `pending_validation` | `onTransition(observation,'pending_validation','继续收集可比较项目样本')` → `POST /observations/{id}/transitions` (`ContentPage.tsx:275-281`) | `ObservationList.tsx:111-125` |
| 吸收 | Moves to `absorbed`; **disabled unless the observation is already `pending_validation`** | `onTransition(…,'absorbed',…)`; `canAbsorb` at `ObservationList.tsx:77` | `ObservationList.tsx:126-137` |
| 证伪 | Moves to `refuted` | `onTransition(…,'refuted','反例推翻当前观察')` | `ObservationList.tsx:138-149` |
| 归档 | Moves to `archived` | `onTransition(…,'archived','当前观察不再相关')` | `ObservationList.tsx:150-160` |
| 尝试形成经验候选 | Proposes a creator-rule candidate from this observation; hidden once `refuted` | `onProposeRule(observation)` → `POST /observations/{id}/rule-candidates` (`ContentPage.tsx:474-477`) | `ObservationList.tsx:161-170` |
| 确认经验 (per proposed rule version) | Confirms the rule candidate | `onDecideRule(version,'confirm')` → `POST /creator-rule-versions/{id}:decide` (`ContentPage.tsx:478-482`) | `ObservationList.tsx:256` |
| 拒绝 (per proposed rule version) | Rejects the rule candidate | `onDecideRule(version,'reject')` | `ObservationList.tsx:257` |
| 保留为例外 (per open conflict) | Resolves a rule conflict by keeping the exception | `onResolveConflict(rule, conflict, 'keep_exception')` → `POST /creator-rules/{id}/conflicts/{other}:resolve` (`ContentPage.tsx:488-495`) | `ObservationList.tsx:278-280` |
| 缩小适用范围 (per open conflict) | Opens the scope-narrowing dialog | `openNarrowing` (`ObservationList.tsx:217-231`) | `ObservationList.tsx:281-283` |
| 停用当前规则 (per open conflict) | Resolves a conflict by deactivating the rule | `onResolveConflict(rule, conflict, 'deactivate')` | `ObservationList.tsx:284-286` |
| 回滚到版本 {n} (per retired version) | Rolls the rule back to a historical version | `onRollbackRule(rule, version)` → `POST /creator-rules/{id}:rollback` (`ContentPage.tsx:483-487`) | `ObservationList.tsx:299-301` |
| 实验或内容主题 (dialog) | Scope patch field | `setScopeDraft` | `ObservationList.tsx:315` |
| 适用受众 (dialog) | Scope patch field | `setScopeDraft` | `ObservationList.tsx:316` |
| 适用形式 (dialog) | Scope patch field | `setScopeDraft` | `ObservationList.tsx:317` |
| 取消 (dialog) | Closes the dialog | `setNarrowing(null)` | `ObservationList.tsx:321` |
| 保存范围并应用 (dialog) | Submits only the fields the user actually changed; requires at least one non-blank field | `onResolveConflict(currentRule, conflict, 'narrow_scope', {...existing, ...patch})` (`ObservationList.tsx:322-344`) | `ObservationList.tsx:322-344` |

Terminal states hide all transition buttons (`ObservationList.tsx:74-76`, `:109`);
`statusLabels` at `ObservationList.tsx:49-55`.

### 3.19 `frontend/src/features/content/FieldSuggestions.tsx` — 3 control kinds (per instance)

| Label | What it does | Handler / API | file:line |
|---|---|---|---|
| 重试 (error state only) | Re-requests candidates | `load` (`FieldSuggestions.tsx:46`) → `POST /projects/{id}/field-suggestions` | `FieldSuggestions.tsx:85` |
| 换一批 | Re-requests a fresh batch | `load` | `FieldSuggestions.tsx:106` |
| `{candidate.text}` chip (+ `{candidate.why}` as a `title`) | Fills the parent field with the candidate text; the text stays editable | `onPick(candidate.text)` | `FieldSuggestions.tsx:112-124` |

Header text depends on the source: `AI 给的方向` when `source === 'ai'`, otherwise
`先给你几个方向` (`FieldSuggestions.tsx:103`) — this is the observable AI-vs-fallback signal.
`limitations[0]` is rendered as the footer note (`FieldSuggestions.tsx:126`), which is where the
degradation sentence appears. One `load()` happens automatically on mount per
`projectId:field` pair (`FieldSuggestions.tsx:74-79`).

Field keys in use: `audience_change`, `answer`, `audience_problem`, `reader_promise`,
`viewpoint_anchor`, `continuation_promise` (sites at `ContentPage.tsx:754-760`, `:842-849`,
`StageForms.tsx:425`, `:441`, `:456`, `:474`, `:493`).

### 3.20 `frontend/src/features/content/ViewpointPanel.tsx` — 5 controls

| Label | What it does | Handler / API | file:line |
|---|---|---|---|
| 提炼候选 / 等待确认 | Proposes a viewpoint from the currently usable evidence; disabled when there is no `evidence:` ref, when one is already pending, or when blocked | `onPropose(sourceIds)` → `POST /projects/{id}/viewpoint-candidates` (`ContentPage.tsx:496-504`); guard at `ViewpointPanel.tsx:67-69` | `ViewpointPanel.tsx:64-74` |
| 观点候选 (textarea, `aria-label`) | Editable candidate statement | `setDrafts` | `ViewpointPanel.tsx:89-97` |
| 确认是我的观点 | Confirms the (possibly edited) statement | `onDecide(viewpoint,'confirm',value)` → `POST /creator-viewpoints/{id}:decide` (`ContentPage.tsx:505-514`) | `ViewpointPanel.tsx:101-111` |
| 不是我的观点 | Rejects the candidate | `onDecide(viewpoint,'reject')` | `ViewpointPanel.tsx:112-123` |
| 撤销观点 | Revokes a confirmed viewpoint | `onRevoke(viewpoint)` → `POST /creator-viewpoints/{id}:revoke` (`ContentPage.tsx:515-522`) | `ViewpointPanel.tsx:136-144` |

Blocked-reason copy a tester must read: with no confirmed evidence the panel shows
`确认一段真实素材后，才能提炼观点候选。` (`ViewpointPanel.tsx:79`); with an unconfirmed intent
it shows `先确认这条内容的处理方式，才能提炼观点候选。`
(`ProjectWorkspace.tsx:675-677`).

### 3.21 `frontend/src/features/content/SeriesPanel.tsx` — 16 controls

| Label | What it does | Handler / API | file:line |
|---|---|---|---|
| 发现系列 / 等待确认 | Proposes a series from the checked projects; disabled with fewer than 2 selected or when one is pending | `onPropose(selected)` → `POST /creator-series-candidates` (`ContentPage.tsx:524-530`); guard at `SeriesPanel.tsx:172` | `SeriesPanel.tsx:169-177` |
| `{project.title}` (checkbox, one per eligible project) | Selects/deselects a source project; all eligible projects are pre-selected on first render (`SeriesPanel.tsx:106-108`) and newly arriving ones are auto-selected (`SeriesPanel.tsx:114-123`); disabled while a candidate is pending | `toggleProject` (`SeriesPanel.tsx:154-160`) | `SeriesPanel.tsx:185-194` |
| 系列名称 (input) | Confirmed series name | `update('name', …)` | `SeriesPanel.tsx:217-222` |
| 系列共同价值 (textarea) | Confirmed shared reader promise | `update('promise', …)` | `SeriesPanel.tsx:223-229` |
| 下一篇延展方向 (textarea) | Confirmed continuation prompt | `update('continuationPrompt', …)` | `SeriesPanel.tsx:230-236` |
| 确认这个系列 | Confirms the series with the edited values; disabled until all three are non-blank | `onDecide(item,'confirm',{name,promise,continuationPrompt})` → `POST /creator-series/{id}:decide` (`ContentPage.tsx:531-542`); `valid` at `SeriesPanel.tsx:212` | `SeriesPanel.tsx:240-251` |
| 不是一个系列 | Rejects the candidate | `onDecide(item,'reject')` | `SeriesPanel.tsx:252-259` |
| 下一篇处理方式 (select) | Intent for the next episode | `updateOpportunity('contentIntent', …)` | `SeriesPanel.tsx:319-330` |
| 下一篇内容格式 (select) | `graphic_note` 图文笔记 / `vlog_plan` 视频脚本 | `updateOpportunity('contentFormat', …)` | `SeriesPanel.tsx:331-341` |
| 下一篇标题 (input) | Title for the extension opportunity | `updateOpportunity('title', …)` | `SeriesPanel.tsx:342-347` |
| 下一篇读者变化 (textarea) | Audience change | `updateOpportunity('audienceChange', …)` | `SeriesPanel.tsx:348-354` |
| 下一篇所需素材 (textarea) | Material requirements, one per line | `updateOpportunity('materials', …)` | `SeriesPanel.tsx:355-361` |
| 确认并创建项目 | Accepts the extension opportunity; disabled unless title, audience change and ≥1 material are present | `onDecideOpportunity(related,'accept',{…})` → `POST /content-opportunities/{id}:decide` (`ContentPage.tsx:558-571`) | `SeriesPanel.tsx:364-377` |
| 这篇不合适 | Rejects the extension opportunity | `onDecideOpportunity(related,'reject')` | `SeriesPanel.tsx:378-385` |
| 打开下一篇项目 | Opens the project created from an accepted extension | `onOpenProject(newId)` → `navigate('/content/{id}')` (`ContentPage.tsx:572`) | `SeriesPanel.tsx:391-399` |
| 准备下一篇 | Proposes a series-extension opportunity; only when no pending/accepted opportunity blocks it | `onProposeOpportunity(item)` → `POST /creator-series/{id}/extension-opportunities` (`ContentPage.tsx:551-557`); `canPrepare` at `SeriesPanel.tsx:276-278` | `SeriesPanel.tsx:403-411` |
| 撤销系列 | Revokes the confirmed series | `onRevoke(item)` → `POST /creator-series/{id}:revoke` (`ContentPage.tsx:543-550`) | `SeriesPanel.tsx:413-421` |

Series relevance is computed from member intent/format sets, not scalars
(`SeriesPanel.tsx:71-81`, `:139-149`) — a mixed series must still appear. The
「至少发布两篇内容后，才能发现系列关系。」 hint appears while fewer than 2 eligible projects
exist (`SeriesPanel.tsx:180-181`).

### 3.22 `frontend/src/features/content/ProjectStartPanel.tsx` — 3 controls

| Label | What it does | Handler / API | file:line |
|---|---|---|---|
| 一句话说说你想做什么 (multiline, 2 rows) | Free-text seed; disabled while a start is pending | `setDraft` | `ProjectStartPanel.tsx:73-83` |
| 开始 / 正在理解… | Starts from the free text; disabled when the draft is blank or a start is pending | `run({rawInput}, 'self')` → `onStart` → `startProject` → `POST /projects/start` → navigates with the inference in router state (`ContentPage.tsx:324-334`) | `ProjectStartPanel.tsx:85-98` |
| `{preview}` material row (up to 3, one per `intake` inbox item) | Starts from that inbox item instead of free text | `run({inboxItemId}, item.id)` → `POST /projects/start` | `ProjectStartPanel.tsx:105-117` |

The intake list is fetched with `listInbox()` and filtered to `status === 'intake'`, sliced to
3 (`ProjectStartPanel.tsx:43-45`); a failure there is swallowed and simply hides the list.

### 3.23 `frontend/src/features/content/ReviewSummary.tsx`, `labels.ts`, `projectDraft.ts`, `parseReferences.ts`

**No interactive controls.** `ReviewSummary` renders an alert + behaviour comparison rows
(`ReviewSummary.tsx:38-64`); `labels.ts` is a pure label map (`labels.ts:4-35`);
`projectDraft.ts` is `localStorage` read/write helpers (`projectDraft.ts:13-58`);
`parseReferences.ts` is a pure parser (`parseReferences.ts:26-69`).

### 3.24 `frontend/src/features/companion/**` — 5 controls

Mounted globally on every guarded route (`AppLayout.tsx:24`), rendered into `document.body`
via a portal (`CompanionDialog.tsx:166`, `:273`).

| Label | What it does | Handler / API | file:line |
|---|---|---|---|
| 对话悬浮球 (`aria-label`), click | Opens the panel, or closes it when already open | `onClick={() => (open ? close() : setOpen(true))}` | `CompanionDialog.tsx:169-193` |
| 渐隐 / 唤醒 | Toggles the "zen" chrome fade | `setZen` | `CompanionDialog.tsx:230-232` |
| 关闭 | Closes the panel and clears zen | `close` (`CompanionDialog.tsx:161-164`) | `CompanionDialog.tsx:233-235` |
| `问它，或说你的想法…` (input) | Question text; `Enter` submits | `setDraft`; `onKeyDown` at `CompanionDialog.tsx:263` | `CompanionDialog.tsx:259-267` |
| ↑ (send button) | Submits the question; disabled while asking or blank | `submit` (`CompanionDialog.tsx:139`) → `askCompanion` → `POST /companion/ask` | `CompanionDialog.tsx:268` |

Behaviour a tester must verify:
- **Context chip.** `openCompanion(context)` dispatches a `topicai:companion-open` event
  (`openCompanion.ts:2-4`); `CompanionDialog` listens (`CompanionDialog.tsx:103-115`) and shows
  the context as a chip (`CompanionDialog.tsx:226-228`) and in the footer
  (`CompanionDialog.tsx:252`). Call sites exist on `/` (`HomePage.tsx:245`), `/loop`
  (`AsyncLoopPage.tsx:217`, `:276`, `:365`) and `/loop/review` (`ReviewPage.tsx:87`).
- **Two proactive demo messages.** On first open, two hard-coded "gap" messages are pushed
  after 2.2s and 14s (`CompanionDialog.tsx:127-137`), both explicitly suffixed `（演示）`.
  These are **static strings, not model output** — the comment at `CompanionDialog.tsx:125`
  says so. A tester must not treat them as AI answers.
- **Honest failure.** When `/companion/ask` fails, the error text is pushed as the reply
  (`CompanionDialog.tsx:154-157`) rather than a canned answer — this is the observable
  degradation for the companion.
- **Entrance animation plays once**, tracked in `sessionStorage` under
  `topicai-companion-booted` (`CompanionDialog.tsx:22`, `:46`, `:63`), and is skipped entirely
  under `prefers-reduced-motion` (`CompanionDialog.tsx:45`).
- `CompanionMotion.tsx` only injects keyframes (`CompanionMotion.tsx:6-23`); `index.ts` and
  `openCompanion.ts` have no controls.

### 3.25 Control tally

| Area | Controls |
|---|---|
| `pages/Login/LoginPage.tsx` | 6 |
| `pages/Home/HomePage.tsx` | 15 |
| `pages/Inbox/InboxPage.tsx` | 13 |
| `pages/AsyncLoop/AsyncLoopPage.tsx` | 21 |
| `pages/Urgent/UrgentPage.tsx` | 8 |
| `pages/Review/ReviewPage.tsx` | 3 |
| `pages/Growth/GrowthPage.tsx` | 3 |
| `pages/Me/MePage.tsx` | 20 |
| `pages/Starter/StarterPage.tsx` | 20 |
| `pages/GrowthOnboarding/GrowthOnboardingPage.tsx` | 18 |
| `pages/Onboarding/ReferenceAnchorPage.tsx` | 16 |
| `pages/Opportunities/OpportunitiesPage.tsx` | 30 |
| `pages/Materials/MaterialsPage.tsx` | 16 |
| `pages/NotFound/NotFoundPage.tsx` | 1 |
| `pages/Content/ContentPage.tsx` | 36 |
| `features/content/ProjectWorkspace.tsx` | 11 |
| `features/content/StageForms.tsx` | 48 |
| `features/content/ObservationList.tsx` | 16 |
| `features/content/FieldSuggestions.tsx` | 3 (per instance; 7 instances rendered) |
| `features/content/ViewpointPanel.tsx` | 5 |
| `features/content/SeriesPanel.tsx` | 16 |
| `features/content/ProjectStartPanel.tsx` | 3 |
| `features/companion/CompanionDialog.tsx` | 5 |
| `features/content/ReviewSummary.tsx`, `labels.ts`, `projectDraft.ts`, `reference/parseReferences.ts` | 0 |
| **Total distinct controls** | **333** |

Repeating controls (per-row / per-segment / per-item) count once; the multiplicity is called
out per row above. Nav controls (§2) are counted separately: 10 desktop links + 2 desktop
footer buttons + 4 mobile links + 1 sheet trigger + 6 sheet links + 1 sheet logout = **24**
nav controls, all in `Sidebar.tsx`.

---

## 4. Backend API surface — every `/api/v2` endpoint

**Mount point.** `backend/main.py:213` → `app.include_router(api_v2_router, prefix="/api/v2", tags=["ContentProject v2"])`.
**Root router.** `backend/app/api/v2/router.py:27` → `api_v2_router = APIRouter()` (no prefix, no tags of its own).
**Composition.** 21 modules are enumerated under `backend/app/api/v2/` (excluding `__init__.py`):
20 sub-router modules plus `router.py`, all wired at `backend/app/api/v2/router.py:28-47`.

### 4.1 Counts (verified by regex, not estimated)

Pattern: `^\s*@(router|api_v2_router)\.(get|post|put|patch|delete)\(` over all `.py` files in
`backend/app/api/v2/`.

| Method | Count |
|---|---|
| POST | 66 |
| GET | 33 |
| PUT | 6 |
| DELETE | 4 |
| PATCH | 1 |
| **TOTAL** | **110** |

109 of these live in the 20 sub-router modules; the 110th is `GET /api/v2/health`
(`router.py:50`). The repository brief said "~109 route decorators across ~21 router modules";
the exact figures are **110** and **21 modules (20 sub-routers + `router.py`)**.

### 4.2 Router registration map

| Module | Router prefix | `tags=` | `APIRouter(` file:line | `include_router` file:line |
|---|---|---|---|---|
| `account_data.py` | `/account` | `Account data v2` | `account_data.py:14` | `router.py:41` |
| `async_loop.py` | `/loop` | `AsyncLoop v2` | `async_loop.py:24` | `router.py:28` |
| `auth.py` | `/auth` | `Authentication` | `auth.py:9` | `router.py:29` |
| `calibration.py` | *(none)* | `Calibration v2` | `calibration.py:31` | `router.py:31` |
| `candidate_review.py` | *(none)* | `Candidate review v2` | `candidate_review.py:15` | `router.py:33` |
| `companion.py` | `/companion` | `Companion` | `companion.py:10` | `router.py:46` |
| `content_genome.py` | *(none)* | `ContentGenome v2` | `content_genome.py:12` | `router.py:35` |
| `content_opportunities.py` | *(none)* | `Content opportunities v2` | `content_opportunities.py:22` | `router.py:38` |
| `creator_rules.py` | *(none)* | `Creator rules v2` | `creator_rules.py:16` | `router.py:34` |
| `creator_series.py` | *(none)* | `Creator series v2` | `creator_series.py:16` | `router.py:37` |
| `creator_viewpoints.py` | *(none)* | `Creator viewpoints v2` | `creator_viewpoints.py:16` | `router.py:36` |
| `experiment_metrics.py` | `/internal/validation` | `Internal MVP validation` | `experiment_metrics.py:19` | `router.py:39` |
| `intent_actions.py` | *(none)* | `Intent orchestration v2` | `intent_actions.py:28` | `router.py:32` |
| `materials.py` | `/materials` | `Materials v2` | `materials.py:18` | `router.py:43` |
| `onboarding.py` | *(none)* | `Growth onboarding v2` | `onboarding.py:21` | `router.py:42` |
| `projects.py` | `/projects` | `ContentProject v2` | `projects.py:28` | `router.py:30` |
| `publish_checks.py` | *(none)* | `Publish checks v2` | `publish_checks.py:15` | `router.py:45` |
| `reference_anchor.py` | `/reference-anchor` | `Reference anchor v2` | `reference_anchor.py:11` | `router.py:47` |
| `router.py` (root) | *(none)* | inherits `ContentProject v2` from `main.py:213` | `router.py:27` | `main.py:213` |
| `settings.py` | `/settings` | `Settings v2` | `settings.py:11` | `router.py:44` |
| `starter.py` | `/starter` | `Starter v2` | `starter.py:18` | `router.py:40` |

No `include_router(..., prefix=...)` adds a second prefix, and no `APIRouter(...)` passes
`dependencies=`.

### 4.3 Auth model (applies to the whole table below)

- `JWTAuthMiddleware` (`backend/app/middleware/auth_middleware.py:28`) **never rejects**; it only
  sets `request.state.user_id`.
- Enforcement is per endpoint through `Depends(get_current_user)`
  (`backend/app/api/deps.py:6`), which raises **401** when `user_id` is absent, or when the user
  is missing or `credentials_revoked_at` is non-null.
- The **only** public paths are listed at `auth_middleware.py:18-21`: `/api/v2/health`,
  `/api/v2/auth/register`, `/api/v2/auth/login`, `/api/v2/auth/refresh`.
- **Every other route below requires a Bearer token.** No route uses another auth dependency
  and no router applies a router-level dependency.
- **Rate limiting is middleware, not a dependency** (`app/middleware/rate_limit.py:10-14`) and
  covers only `/api/v2/auth/login`, `/api/v2/auth/register`, `/api/v2/auth/refresh`, keyed per
  client IP per minute (429, `meta.error_code = AUTH_RATE_LIMIT_EXCEEDED`). No other `/api/v2`
  route is rate-limited.
- **Idempotency replay:** 43 POST/PUT routes declare `status_code=201` but set
  `response.status_code = 200` and add `meta={"idempotency_replayed": true}` when the
  `idempotency_key` replays. Test both codes on those paths.

### 4.4 `account_data.py` — 4 routes

`router = APIRouter(prefix="/account", tags=["Account data v2"])` — `account_data.py:14`

| Method | Full path | Handler | Purpose | Request model | Auth | file:line |
|---|---|---|---|---|---|---|
| POST | `/api/v2/account/data-export:request` | `request_data_export` | Open or replay a PRIVACY human gate for a data-export request | `AccountGateRequest` | required | `account_data.py:17` |
| GET | `/api/v2/account/data-export` | `export_account_data` | Return the export bundle for a completed gate (`?gate_id=`) | — | required | `account_data.py:39` |
| POST | `/api/v2/account/deletion:request` | `request_account_deletion` | Open or replay a DELETION human gate | `AccountGateRequest` | required | `account_data.py:48` |
| DELETE | `/api/v2/account` | `delete_account` | Execute deletion for a completed gate (`?gate_id=`), returns **202** | — | required | `account_data.py:70` |

### 4.5 `async_loop.py` — 11 routes

`router = APIRouter(prefix="/loop", tags=["AsyncLoop v2"])` — `async_loop.py:24`

| Method | Full path | Handler | Purpose | Request model | Auth | file:line |
|---|---|---|---|---|---|---|
| POST | `/api/v2/loop/inbox` | `add_inbox_item` | Capture a raw idea/material into the inbox (idempotent, 201) | `InboxItemCreate` | required | `async_loop.py:27` |
| GET | `/api/v2/loop/inbox` | `list_inbox` | List the owner's inbox items | — | required | `async_loop.py:43` |
| POST | `/api/v2/loop/inbox/digest` | `digest_inbox` | Drain the inbox through production; `?limit=` produces one item at a time and returns the remaining count | — | required | `async_loop.py:52` |
| GET | `/api/v2/loop/deliverables` | `list_deliverables` | List deliverables by comma-separated `?status=` (default `ready`) | — | required | `async_loop.py:71` |
| POST | `/api/v2/loop/deliverables/{deliverable_id}:restore` | `restore_deliverable` | Re-shelve a pooled deliverable, resetting the 7-day window | — | required | `async_loop.py:83` |
| DELETE | `/api/v2/loop/deliverables/{deliverable_id}` | `delete_deliverable` | Permanently delete a pooled (expired/discarded) deliverable | — | required | `async_loop.py:99` |
| POST | `/api/v2/loop/deliverables/{deliverable_id}:pickup` | `pickup_deliverable` | Claim a deliverable into a project (idempotent) | `PickupRequest` | required | `async_loop.py:113` |
| POST | `/api/v2/loop/deliverables/{deliverable_id}:discard` | `discard_deliverable` | Discard with an attribution reason | `DiscardRequest` | required | `async_loop.py:133` |
| GET | `/api/v2/loop/weekly` | `weekly_rows` | Weekly review rows for the last `?days=` | — | required | `async_loop.py:148` |
| POST | `/api/v2/loop/metrics` | `record_metric` | Record a loop metric sample (201) | `MetricsRecord` | required | `async_loop.py:158` |
| GET | `/api/v2/loop/metrics` | `list_metrics` | List metric samples, optionally `?metric=` | — | required | `async_loop.py:167` |

### 4.6 `auth.py` — 5 routes

`router = APIRouter(prefix="/auth", tags=["Authentication"])` — `auth.py:9`

| Method | Full path | Handler | Purpose | Request model | Auth | file:line |
|---|---|---|---|---|---|---|
| POST | `/api/v2/auth/register` | `register` | Create a user, return user + tokens (201) | `RegisterRequest` | **public**, rate-limited | `auth.py:28` |
| POST | `/api/v2/auth/login` | `login` | Authenticate by email/password, return user + tokens | `LoginRequest` | **public**, rate-limited | `auth.py:61` |
| POST | `/api/v2/auth/refresh` | `refresh_token` | Rotate an access token from a refresh token | `RefreshRequest` | **public**, rate-limited | `auth.py:93` |
| GET | `/api/v2/auth/me` | `me` | Return the current authenticated user | — | required | `auth.py:111` |
| POST | `/api/v2/auth/password` | `change_password` | Change the password (422 when new == current) | `PasswordChangeRequest` | required | `auth.py:126` |

Handlers read `req.app.state.db` directly (`auth.py:34`, `:67`, `:99`, `:139`) instead of the
`get_db` dependency used everywhere else.

### 4.7 `calibration.py` — 12 routes

`router = APIRouter(tags=["Calibration v2"])` — `calibration.py:31` (no prefix)

| Method | Full path | Handler | Purpose | Request model | Auth | file:line |
|---|---|---|---|---|---|---|
| GET | `/api/v2/projects/{project_id}/calibration` | `get_calibration_workspace` | Assemble the project calibration workspace (the workspace payload the UI renders) | — | required | `calibration.py:43` |
| GET | `/api/v2/publish-hypotheses/{hypothesis_id}/amendments` | `list_hypothesis_amendments` | List amendments to a locked hypothesis | — | required | `calibration.py:53` |
| POST | `/api/v2/publish-hypotheses/{hypothesis_id}/amendments` | `amend_publish_hypothesis` | Append an amendment (idempotent, 201) | `PublishHypothesisAmendmentCreate` | required | `calibration.py:65` |
| GET | `/api/v2/benchmark-samples` | `list_benchmark_samples` | List benchmark samples | — | required | `calibration.py:79` |
| POST | `/api/v2/benchmark-samples` | `create_benchmark_sample` | Create a benchmark sample (201) | `BenchmarkSampleCreate` | required | `calibration.py:87` |
| POST | `/api/v2/benchmark-samples/{sample_id}/inclusion` | `set_benchmark_sample_inclusion` | Include/exclude a sample from calibration (201) | `BenchmarkSampleInclusionUpdate` | required | `calibration.py:98` |
| POST | `/api/v2/projects/{project_id}/publish-records` | `record_publication` | Record that a locked version was published (201) | `PublishRecordCreate` | required | `calibration.py:112` |
| POST | `/api/v2/publish-records/{publish_record_id}/snapshots` | `append_snapshot` | Append a performance snapshot (201) | `PerformanceSnapshotCreate` | required | `calibration.py:124` |
| POST | `/api/v2/snapshots:extract` | `extract_snapshot_metrics` | Extract metrics from a screenshot material into a proposal (201) | `SnapshotExtractionCreate` | required | `calibration.py:138` |
| POST | `/api/v2/projects/{project_id}/blind-reviews` | `create_blind_review` | Create a blind-review round (201) | `BlindReviewCreate` | required | `calibration.py:153` |
| POST | `/api/v2/blind-reviews/{blind_review_id}/observations` | `create_observation` | Add an observation to a review (201) | `ObservationCreate` | required | `calibration.py:167` |
| POST | `/api/v2/observations/{observation_id}/transitions` | `transition_observation` | Transition the observation lifecycle (201) | `ObservationTransition` | required | `calibration.py:181` |

All 12 POSTs go through a local `_response()` helper that downgrades 201→200 on idempotency replay.

### 4.8 `candidate_review.py` — 4 routes

`router = APIRouter(tags=["Candidate review v2"])` — `candidate_review.py:15` (no prefix)

| Method | Full path | Handler | Purpose | Request model | Auth | file:line |
|---|---|---|---|---|---|---|
| GET | `/api/v2/projects/{project_id}/candidate-review` | `get_candidate_review` | Read the immutable candidate review for a project | — | required | `candidate_review.py:27` |
| POST | `/api/v2/projects/{project_id}/candidate-review/segments/{segment_id}:decide` | `decide_candidate_segment` | Accept/reject/replace one segment (201) | `SegmentDecisionInput` | required | `candidate_review.py:36` |
| POST | `/api/v2/projects/{project_id}/candidate-review:revise` | `revise_candidate` | Create a revised candidate from reviewer input (201) | `CandidateRevisionInput` | required | `candidate_review.py:51` |
| POST | `/api/v2/projects/{project_id}/candidate-review:restore` | `restore_candidate` | Restore a previous candidate version (201) | `CandidateRestoreInput` | required | `candidate_review.py:63` |

### 4.9 `companion.py` — 1 route

`router = APIRouter(prefix="/companion", tags=["Companion"])` — `companion.py:10`

| Method | Full path | Handler | Purpose | Request model | Auth | file:line |
|---|---|---|---|---|---|---|
| POST | `/api/v2/companion/ask` | `ask` | Answer one floating-ball question, scoped by `context` (real LLM call) | `CompanionAskRequest` | required | `companion.py:25` |

### 4.10 `content_genome.py` — 2 routes

`router = APIRouter(tags=["ContentGenome v2"])` — `content_genome.py:12` (no prefix)

| Method | Full path | Handler | Purpose | Request model | Auth | file:line |
|---|---|---|---|---|---|---|
| GET | `/api/v2/content-genome` | `search_content_genome` | Search the cross-project genome by `?content_intent=&audience=&content_format=&experiment=` | — | required | `content_genome.py:15` |
| GET | `/api/v2/projects/{project_id}/content-genome` | `get_project_content_genome` | Genome read model for one project (`?experiment=`) | — | required | `content_genome.py:34` |

### 4.11 `content_opportunities.py` — 6 routes

`router = APIRouter(tags=["Content opportunities v2"])` — `content_opportunities.py:22` (no prefix)

| Method | Full path | Handler | Purpose | Request model | Auth | file:line |
|---|---|---|---|---|---|---|
| GET | `/api/v2/content-opportunities` | `list_content_opportunities` | List opportunities filtered by `?type=` (`alias="type"`), `?decision=`, `?timeliness=` | — | required | `content_opportunities.py:48` |
| POST | `/api/v2/content-opportunities:generate` | `generate_content_opportunities` | Deterministically generate up to `desired_count` opportunities (**no LLM**) | `OpportunityGenerateRequest` | required | `content_opportunities.py:79` |
| POST | `/api/v2/creator-series/{series_id}/extension-opportunities` | `propose_series_extension` | Propose a next-episode opportunity for a confirmed series (LLM-backed, 201) | `SeriesExtensionCreate` | required | `content_opportunities.py:97` |
| POST | `/api/v2/content-opportunities/source-verification` | `create_source_verification_opportunity` | Create a user-sourced opportunity pending verification (201) | `UserSourceOpportunityCreate` | required | `content_opportunities.py:115` |
| POST | `/api/v2/content-opportunities/{opportunity_id}:decide` | `decide_content_opportunity` | Adopt / save / reject an opportunity (201) | `OpportunityDecision` | required | `content_opportunities.py:132` |
| POST | `/api/v2/content-opportunities/{opportunity_id}:verify-source` | `verify_content_opportunity_source` | Record the source-verification verdict (201) | `OpportunitySourceVerification` | required | `content_opportunities.py:150` |

### 4.12 `creator_rules.py` — 5 routes

`router = APIRouter(tags=["Creator rules v2"])` — `creator_rules.py:16` (no prefix)

| Method | Full path | Handler | Purpose | Request model | Auth | file:line |
|---|---|---|---|---|---|---|
| GET | `/api/v2/creator-rules` | `list_creator_rules` | List the owner's cross-project creator rules | — | required | `creator_rules.py:24` |
| POST | `/api/v2/observations/{observation_id}/rule-candidates` | `propose_rule_candidate` | Propose a rule candidate from an observation (201) | `RuleCandidateCreate` | required | `creator_rules.py:29` |
| POST | `/api/v2/creator-rule-versions/{version_id}:decide` | `decide_rule_candidate` | Accept/reject a rule version (201) | `RuleCandidateDecision` | required | `creator_rules.py:41` |
| POST | `/api/v2/creator-rules/{rule_id}:rollback` | `rollback_creator_rule` | Roll a rule back to an earlier version (201) | `RuleRollback` | required | `creator_rules.py:53` |
| POST | `/api/v2/creator-rules/{rule_id}/conflicts/{conflict_rule_id}:resolve` | `resolve_creator_rule_conflict` | Resolve a conflict between two rules (201) | `RuleConflictResolutionCreate` | required | `creator_rules.py:65` |

### 4.13 `creator_series.py` — 4 routes

`router = APIRouter(tags=["Creator series v2"])` — `creator_series.py:16` (no prefix)

| Method | Full path | Handler | Purpose | Request model | Auth | file:line |
|---|---|---|---|---|---|---|
| GET | `/api/v2/creator-series` | `list_creator_series` | List confirmed series | — | required | `creator_series.py:40` |
| POST | `/api/v2/creator-series-candidates` | `propose_series_candidate` | Propose a series from existing content (LLM-backed, 201) | `SeriesCandidateCreate` | required | `creator_series.py:47` |
| POST | `/api/v2/creator-series/{series_id}:decide` | `decide_series_candidate` | Confirm/reject a candidate series (201) | `SeriesDecision` | required | `creator_series.py:58` |
| POST | `/api/v2/creator-series/{series_id}:revoke` | `revoke_creator_series` | Revoke a confirmed series (201) | `SeriesRevocation` | required | `creator_series.py:70` |

### 4.14 `creator_viewpoints.py` — 4 routes

`router = APIRouter(tags=["Creator viewpoints v2"])` — `creator_viewpoints.py:16` (no prefix)

| Method | Full path | Handler | Purpose | Request model | Auth | file:line |
|---|---|---|---|---|---|---|
| GET | `/api/v2/creator-viewpoints` | `list_creator_viewpoints` | List confirmed viewpoints | — | required | `creator_viewpoints.py:40` |
| POST | `/api/v2/projects/{project_id}/viewpoint-candidates` | `propose_viewpoint_candidate` | Distil a viewpoint candidate (LLM-backed, 201) | `ViewpointCandidateCreate` | required | `creator_viewpoints.py:47` |
| POST | `/api/v2/creator-viewpoints/{viewpoint_id}:decide` | `decide_viewpoint_candidate` | Confirm/reject a viewpoint (201) | `ViewpointDecision` | required | `creator_viewpoints.py:61` |
| POST | `/api/v2/creator-viewpoints/{viewpoint_id}:revoke` | `revoke_creator_viewpoint` | Revoke a confirmed viewpoint (201) | `ViewpointRevocation` | required | `creator_viewpoints.py:75` |

### 4.15 `experiment_metrics.py` — 2 routes

`router = APIRouter(prefix="/internal/validation", tags=["Internal MVP validation"])` — `experiment_metrics.py:19`

| Method | Full path | Handler | Purpose | Request model | Auth | file:line |
|---|---|---|---|---|---|---|
| PUT | `/api/v2/internal/validation/experiments/{experiment_id}/assignment` | `assign_experiment` | Upsert the owner's cohort assignment (idempotent, 201) | `ExperimentAssignmentUpsert` | required | `experiment_metrics.py:22` |
| GET | `/api/v2/internal/validation/action-metrics` | `export_action_metrics` | Export owner-scoped action metrics for a window/cohort | — | required | `experiment_metrics.py:45` |

"Internal" is naming only — these are normal authenticated, owner-scoped endpoints.

### 4.16 `intent_actions.py` — 13 routes

`router = APIRouter(tags=["Intent orchestration v2"])` — `intent_actions.py:28` (no prefix)

| Method | Full path | Handler | Purpose | Request model | Auth | file:line |
|---|---|---|---|---|---|---|
| GET | `/api/v2/today` | `get_today_action` | Today's orchestrator workspace (the 晨报 payload) | — | required | `intent_actions.py:51` |
| GET | `/api/v2/creator-state` | `get_creator_state` | Refresh and return creator trust/state | — | required | `intent_actions.py:59` |
| GET | `/api/v2/projects/{project_id}/evidence` | `list_project_evidence` | List evidence attached to a project | — | required | `intent_actions.py:67` |
| POST | `/api/v2/evidence/{evidence_id}:decide` | `decide_evidence` | Confirm or reject a piece of evidence (201) | `EvidenceDecision` | required | `intent_actions.py:76` |
| POST | `/api/v2/evidence/{evidence_id}:revoke` | `revoke_evidence` | Revoke confirmed evidence (201) | `EvidenceRevocation` | required | `intent_actions.py:93` |
| GET | `/api/v2/projects/{project_id}/next-action` | `get_project_next_action` | Ensure and return the project's next suggested action | — | required | `intent_actions.py:105` |
| POST | `/api/v2/projects/{project_id}/intent:confirm` | `confirm_project_intent` | Confirm the user's content intent (201) | `IntentConfirmation` | required | `intent_actions.py:115` |
| POST | `/api/v2/projects/{project_id}/intent:classify-retrospective` | `classify_retrospective_intent` | Retrospectively classify an already-published project (201) | `RetrospectiveIntentClassification` | required | `intent_actions.py:129` |
| POST | `/api/v2/actions/{action_id}:respond` | `respond_to_action` | Record the user's response to a suggested action (LLM-assisted, 201) | `ActionResponse` | required | `intent_actions.py:145` |
| POST | `/api/v2/actions/{action_id}:transition` | `transition_action` | Drive the action lifecycle state machine (201) | `ActionLifecycleCommand` | required | `intent_actions.py:159` |
| POST | `/api/v2/projects/{project_id}/automation` | `set_project_automation` | Set the project-level automation preference (201) | `AutomationPreference` | required | `intent_actions.py:173` |
| POST | `/api/v2/actions/{action_id}/human-gate` | `open_human_gate` | Open (or return) the human gate for an action (201; 200 when the gate is not `pending`) | — | required | `intent_actions.py:187` |
| POST | `/api/v2/human-gates/{gate_id}:decide` | `decide_human_gate` | Record the human's decision on a gate (LLM-assisted, 201) | `HumanGateDecision` | required | `intent_actions.py:199` |

### 4.17 `materials.py` — 8 routes

`router = APIRouter(prefix="/materials", tags=["Materials v2"])` — `materials.py:18`

| Method | Full path | Handler | Purpose | Request model | Auth | file:line |
|---|---|---|---|---|---|---|
| GET | `/api/v2/materials` | `list_materials` | List materials, optionally `?kind=` | — | required | `materials.py:21` |
| POST | `/api/v2/materials` | `create_material` | Create a material from text or base64 (idempotent, 201) | `MaterialCreate` | required | `materials.py:31` |
| POST | `/api/v2/materials/{material_id}:analyze` | `analyze_material` | User-triggered multimodal read of an audio/video material; explicit refusal when no model is configured | — | required | `materials.py:47` |
| GET | `/api/v2/materials/{material_id}` | `get_material` | Fetch one material's metadata | — | required | `materials.py:65` |
| GET | `/api/v2/materials/{material_id}/content` | `get_material_content` | Return stored bytes as an attachment — **raw `Response`, not an `ApiResponse` envelope** | — | required | `materials.py:74` |
| PATCH | `/api/v2/materials/{material_id}` | `update_material` | Partially update a material | `MaterialUpdate` | required | `materials.py:93` |
| POST | `/api/v2/materials/{material_id}/usages` | `add_material_usage` | Record reuse in a project (idempotent, 201) | `MaterialUsageCreate` | required | `materials.py:105` |
| DELETE | `/api/v2/materials/{material_id}` | `delete_material` | Delete a material; requires `?confirmed=true`; returns **204** | — | required | `materials.py:128` |

### 4.18 `onboarding.py` — 6 routes

`router = APIRouter(tags=["Growth onboarding v2"])` — `onboarding.py:21` (no prefix)

| Method | Full path | Handler | Purpose | Request model | Auth | file:line |
|---|---|---|---|---|---|---|
| GET | `/api/v2/onboarding` | `get_onboarding_context` | Return the onboarding / product-mode context | — | required | `onboarding.py:24` |
| PUT | `/api/v2/onboarding/mode` | `select_mode` | Select the product mode (version-checked) | `ProductModeUpdate` | required | `onboarding.py:29` |
| POST | `/api/v2/history-imports` | `import_history` | Bulk-import past notes into the creator profile (idempotent, 201) | `HistoryImportCreate` | required | `onboarding.py:40` |
| POST | `/api/v2/reference-imports` | `import_references` | Import "I want to make it like this" references; each row needs a source and these never feed the "who you are" profile (201) | `HistoryImportCreate` with `ReferenceNoteInput` items | required | `onboarding.py:60` |
| GET | `/api/v2/creator-profile` | `get_creator_profile` | Get-or-build the correctable creator profile | — | required | `onboarding.py:87` |
| PUT | `/api/v2/creator-profile` | `update_creator_profile` | Correct the creator profile | `CreatorProfileUpdate` | required | `onboarding.py:94` |

### 4.19 `projects.py` — 10 routes

`router = APIRouter(prefix="/projects", tags=["ContentProject v2"])` — `projects.py:28`

| Method | Full path | Handler | Purpose | Request model | Auth | file:line |
|---|---|---|---|---|---|---|
| GET | `/api/v2/projects` | `list_projects` | List the owner's content projects | — | required | `projects.py:31` |
| POST | `/api/v2/projects` | `create_project` | Create a ContentProject explicitly (title/intent/audience supplied) (201) | `ContentProjectCreate` | required | `projects.py:40` |
| POST | `/api/v2/projects/{project_id}/field-suggestions` | `suggest_field_candidates` | Propose fill-in candidates for one field (LLM; degrades to generic skeletons + `limitations`) | `FieldSuggestionRequest` | required | `projects.py:69` |
| POST | `/api/v2/projects/start` | `start_project` | One sentence or one material → AI-inferred intent → project (201) | `ProjectStartRequest` | required | `projects.py:88` |
| POST | `/api/v2/projects/{project_id}:dismiss-inference` | `dismiss_start_inference` | Discard the inferred intent and return to manual confirmation (**200**) | — | required | `projects.py:103` |
| GET | `/api/v2/projects/{project_id}` | `get_project` | Fetch one project | — | required | `projects.py:117` |
| POST | `/api/v2/projects/{project_id}/transitions` | `transition_project` | Drive the project state machine (idempotent, 201) | `ProjectTransition` | required | `projects.py:127` |
| DELETE | `/api/v2/projects/{project_id}` | `delete_project` | Delete a project — **204** | — | required | `projects.py:146` |
| POST | `/api/v2/projects/{project_id}/versions` | `create_version` | Create a content version (idempotent, 201) | `ContentVersionCreate` | required | `projects.py:156` |
| POST | `/api/v2/projects/{project_id}/publish-hypothesis:lock` | `lock_publish_hypothesis` | Lock the publish hypothesis (idempotent, 201) | `PublishHypothesisLock` | required | `projects.py:175` |

### 4.20 `publish_checks.py` — 3 routes

`router = APIRouter(tags=["Publish checks v2"])` — `publish_checks.py:15` (no prefix)

| Method | Full path | Handler | Purpose | Request model | Auth | file:line |
|---|---|---|---|---|---|---|
| POST | `/api/v2/projects/{project_id}/publish-checks` | `run_publish_check` | Run a version-bound pre-publish check (idempotent, 201) | `PublishCheckCreate` | required | `publish_checks.py:27` |
| GET | `/api/v2/projects/{project_id}/publish-checks/latest` | `get_latest_publish_check` | Return the newest check, or `null` | — | required | `publish_checks.py:43` |
| PUT | `/api/v2/publish-checks/{check_id}/resolution` | `resolve_publish_check` | Acknowledge/resolve individual findings (idempotent, 201) | `PublishCheckResolution` | required | `publish_checks.py:55` |

### 4.21 `reference_anchor.py` — 2 routes

`router = APIRouter(prefix="/reference-anchor", tags=["Reference anchor v2"])` — `reference_anchor.py:11`

| Method | Full path | Handler | Purpose | Request model | Auth | file:line |
|---|---|---|---|---|---|---|
| GET | `/api/v2/reference-anchor` | `get_reference_anchor` | Read the derived "what you want to become" anchor; cached unless the reference set changed; empty is normal | — | required | `reference_anchor.py:14` |
| PUT | `/api/v2/reference-anchor` | `update_reference_anchor` | Override the anchor with the user's own words (user wins over later auto-derivation) | `ReferenceAnchorUpdate` | required | `reference_anchor.py:28` |

### 4.22 `router.py` — 1 route

`api_v2_router = APIRouter()` — `router.py:27` (no prefix, no tags; mounted at `/api/v2` in `main.py:213`)

| Method | Full path | Handler | Purpose | Request model | Auth | file:line |
|---|---|---|---|---|---|---|
| GET | `/api/v2/health` | `health` | Report shell availability (`status`, `api_version`, `product`) | — | **public** | `router.py:50` |

### 4.23 `settings.py` — 2 routes

`router = APIRouter(prefix="/settings", tags=["Settings v2"])` — `settings.py:11`

| Method | Full path | Handler | Purpose | Request model | Auth | file:line |
|---|---|---|---|---|---|---|
| GET | `/api/v2/settings` | `get_settings` | Return the owner's settings | — | required | `settings.py:14` |
| PUT | `/api/v2/settings` | `update_settings` | Update goal / strategy / consents / auto-digest with `expected_version` | `UserSettingsUpdate` | required | `settings.py:21` |

### 4.24 `starter.py` — 5 routes

`router = APIRouter(prefix="/starter", tags=["Starter v2"])` — `starter.py:18`

| Method | Full path | Handler | Purpose | Request model | Auth | file:line |
|---|---|---|---|---|---|---|
| GET | `/api/v2/starter` | `get_starter_workspace` | Return the bounded starter-experiment workspace | — | required | `starter.py:21` |
| POST | `/api/v2/starter/assessment` | `submit_assessment` | Submit the readiness assessment, return the next step (201) | `StarterAssessmentCreate` | required | `starter.py:28` |
| POST | `/api/v2/starter/directions:generate` | `generate_directions` | Generate direction candidates (deterministic, 201) | `DirectionGenerate` | required | `starter.py:44` |
| POST | `/api/v2/starter/directions/{direction_id}:select` | `select_direction` | Select a direction and create the sprint (201) | `DirectionSelect` | required | `starter.py:60` |
| POST | `/api/v2/starter/sprints/{sprint_id}:review` | `review_sprint` | Review the sprint (**no explicit 201 — default 200**) | `StarterSprintReview` | required | `starter.py:79` |

### 4.25 Endpoints not reachable from any frontend client function

Diffed against `frontend/src/services/api/v2/*.ts` + `frontend/src/services/api/auth.ts`
(test files excluded). These 15 routes have **no** frontend caller and therefore cannot be
exercised through the UI — drive them with `curl`/`httpie` instead:

| Method | Full path | Module | file:line |
|---|---|---|---|
| GET | `/api/v2/publish-hypotheses/{hypothesis_id}/amendments` | `calibration.py` | `calibration.py:53` |
| POST | `/api/v2/publish-hypotheses/{hypothesis_id}/amendments` | `calibration.py` | `calibration.py:65` |
| GET | `/api/v2/benchmark-samples` | `calibration.py` | `calibration.py:79` |
| POST | `/api/v2/benchmark-samples` | `calibration.py` | `calibration.py:87` |
| POST | `/api/v2/benchmark-samples/{sample_id}/inclusion` | `calibration.py` | `calibration.py:98` |
| PUT | `/api/v2/internal/validation/experiments/{experiment_id}/assignment` | `experiment_metrics.py` | `experiment_metrics.py:22` |
| GET | `/api/v2/internal/validation/action-metrics` | `experiment_metrics.py` | `experiment_metrics.py:45` |
| POST | `/api/v2/projects/{project_id}/automation` | `intent_actions.py` | `intent_actions.py:173` |
| GET | `/api/v2/materials/{material_id}` | `materials.py` | `materials.py:65` |
| GET | `/api/v2/materials/{material_id}/content` | `materials.py` | `materials.py:74` |
| PATCH | `/api/v2/materials/{material_id}` | `materials.py` | `materials.py:93` |
| GET | `/api/v2/projects/{project_id}` | `projects.py` | `projects.py:117` |
| POST | `/api/v2/projects/{project_id}/transitions` | `projects.py` | `projects.py:127` |
| DELETE | `/api/v2/projects/{project_id}` | `projects.py` | `projects.py:146` |
| GET | `/api/v2/health` | `router.py` | `router.py:50` |

The remaining **95 routes** are reachable from a named frontend client function. Caveat: this
diff covers only the frontend client layer; Playwright specs and non-SPA consumers were not
included, so "unused by the frontend client" is not the same as dead code.

### 4.26 Endpoint-level notes & hazards for the test plan

1. **Non-201/204 responses to expect** — `DELETE /api/v2/account` → **202** (`account_data.py:70`);
   `DELETE /api/v2/materials/{id}` → **204** (`materials.py:128`);
   `DELETE /api/v2/projects/{id}` → **204** (`projects.py:146`);
   `POST /api/v2/projects/{id}:dismiss-inference` → **200** (`projects.py:103`);
   `POST /api/v2/starter/sprints/{id}:review` → **200** (`starter.py:79`).
2. **No streaming anywhere.** There is no `StreamingResponse` and no `FileResponse` in
   `backend/app/api/v2/`. `GET /api/v2/materials/{id}/content` (`materials.py:74-90`) builds a
   plain Starlette `Response(content=…)` with `Content-Disposition: attachment` and
   `X-Content-Type-Options: nosniff`, buffering the whole payload in memory.
3. **47 routes omit `response_model`**, so OpenAPI shows an unconstrained body. Any test that
   validates responses against `/openapi.json` must exempt them.
4. **Route-ordering hazards** (verified safe today, worth a regression test):
   `content_opportunities.py:79` (`…:generate`) and `:115` (`…/source-verification`) precede
   `:132` (`…/{opportunity_id}:decide`); `creator_series.py:47` (`/creator-series-candidates`)
   coexists with `:58` (`/creator-series/{series_id}:decide`); `projects.py:88`
   (`/projects/start`) coexists with `:103` (`/projects/{project_id}:dismiss-inference`);
   `materials.py:47` (`POST …:analyze`) precedes `:65` (`GET …{id}`) — different methods, safe.
5. **`GET /api/v2/materials/{id}/content` breaks the `ApiResponse` envelope convention.** Any
   generic envelope assertion must exempt it.
6. **`settings.py:15` defines a handler named `get_settings`**, shadowing the name of
   `config.settings.get_settings` inside that module (which it does not import). Harmless today.
7. **Root-router tags.** `api_v2_router` declares no tags; `main.py:213` supplies
   `tags=["ContentProject v2"]`, which therefore applies only to `GET /api/v2/health`.

---

## 5. End-to-end user journeys

Journeys below are derived from `README.md`, `CONTEXT.md`, `DESIGN.md`,
`docs/ai-native-async-creation-plan-2026-08-29.md`, `specs/008-…`–`specs/013-…`,
`docs/dogfood/tester-brief-2026-09-15.md`, `docs/testing/dogfood-falsification-protocol.md`,
`docs/reviews/async-loop-*-2026-09-15.md`, `docs/reviews/reference-anchor-r6-r7-2026-09-15.md`,
and the three Playwright specs under `frontend/e2e/`. Where the docs and the shipped code
disagree, the **code is authoritative for testing** and the disagreement is called out.

**Spec-directory reality check (verified by listing):** `specs/013-async-creation-loop/`
contains only `data-model.md`, `spec.md`, `tasks.md`. There is **no** `plan.md`, **no**
`quickstart.md`, and **no** `contracts/` in that directory. The de-facto plan is
`specs/013-async-creation-loop/tasks.md` plus
`docs/ai-native-async-creation-plan-2026-08-29.md`; the async-loop endpoint shapes must be read
from `backend/app/api/v2/async_loop.py` (§4.5).

### J1 — Registration / login (注册/登录)

- **Route:** `/login` (`App.tsx:65`). **Actor:** new or returning visitor.
- **Steps:** open `/login` → either fill 邮箱 + 密码 and press 进入, or press 没有账号？注册,
  fill 你的姓名 (≥2 chars), 密码 (≥8), 再输入一次密码, then press 创建账号.
- **Expected:** success lands on `/` with a heading matching `/^你好，/`
  (`HomePage.tsx:225`); tokens are written to `localStorage`
  (`authStore.ts:57-58`). Client-side failures render inline `role="alert"` text
  (`LoginPage.tsx:66-68`) for short name, short password and mismatch.
- **Returning path:** `/me` → 账户 section → 更新密码 → `POST /auth/password`; expected
  notice `密码已更新，下次登录请使用新密码。` (`MePage.tsx:138`).
- **Logout:** desktop footer 退出 (`Sidebar.tsx:164-179`) or mobile sheet 退出登录
  (`Sidebar.tsx:129-145`); both must land on `/login` and clear tokens.
- **Ambiguity:** no doc defines where a brand-new account is routed after registration. The
  code goes straight to `/` — there is **no first-run onboarding gate** in `App.tsx`.

### J2 — Growth onboarding (成长引导)

- **Route:** `/onboarding/growth` (`App.tsx:80`), entered from `/me` via
  「导入历史内容并校对画像」 (`MePage.tsx:316`). **Precondition:** signed in, mode not yet `growth`.
- **Steps:** press 使用历史内容开始 (`PUT /onboarding/mode`) → choose 手动 / CSV / JSON →
  paste 历史内容 → 导入历史内容 (`POST /history-imports`) → confirm the reported
  `成功 N 条，失败 M 条` → fill 创作方向, 目标读者, 内容支柱 (max 5), optionally 表达特点 /
  明确避免 / 成长目标 → 确认画像并继续 (`PUT /creator-profile`) → lands on `/`.
- **Expected:** the read-out panel shows per-attribute status + confidence + evidence count
  (`GrowthOnboardingPage.tsx:245-257`); with fewer than 10 imported notes the chip reads
  待确认/资料不足，暂定 and an info alert explains the provisional state
  (`GrowthOnboardingPage.tsx:200-202`).
- **E2E-confirmed variant:** `frontend/e2e/intent-driven-loop.spec.ts:34-52` performs exactly
  this and asserts a `role="status"` element containing `成功 3 条` (`:47`).
- **Ambiguity:** the 2026-07-19 IA doc prescribes `/onboarding/history`,
  `/onboarding/profile-review` and `/onboarding/readiness` sub-routes; only
  `/onboarding/growth` exists.

### J3 — Starter experiment (起步实验, three routes)

- **Routes:** `/onboarding/assessment`, `/onboarding/directions`, `/onboarding/sprint`
  (`App.tsx:77-79`) — **all render the same component, and the visible step is chosen by the
  server payload, not the URL** (see A2).
- **Steps:** 每周可投入小时 + at least one of 你亲自经历过什么 / 你愿意持续探索什么 /
  你会做什么 → 保存并继续 → 查看候选方向 → 选择并创建三篇实验 → open a project row →
  (in the workspace: 确认这个方向 → 你的回答 → 让 AI 准备候选内容 → 确认并准备候选内容 →
  confirm each segment → 确认候选内容并进入发布准备 → fill the intent-required field →
  锁定发布意图 → 运行检查 → 确认已发布) → back to `/onboarding/assessment` → fill the three
  sprint-review fields → 完成本轮复盘.
- **Expected:** 3 project rows in `.starter-project-list`
  (`frontend/e2e/starter-flow.spec.ts:43`), `0 / 3 已发布` initially (`:42`), and after a
  publish `1 / 3 已发布` (`:89`); a completed review renders 本轮实验已完成 (`:94`).
- **Ambiguity:** step 3's review form only appears once `sprint.published_count >= 1`
  (`StarterPage.tsx:304`); before that an info alert explains why
  (`StarterPage.tsx:327`). No doc states this threshold explicitly.

### J4 — Reference anchor (参考锚点)

- **Route:** `/onboarding/reference` (`App.tsx:81`), reachable from `/me`
  (`MePage.tsx:317`), from the growth-onboarding profile alert
  (`GrowthOnboardingPage.tsx:207`), and from the empty content list
  (`ContentPage.tsx:318`).
- **Steps:** paste 2–3 blocks separated by blank lines, each starting with `@账号名` or
  `来源：` → observe `已识别 N 条参考` and any parse problems → 读这些参考 → wait
  (「正在读这 N 条参考…」, typically 十几秒) → review 选题范围 / 这类内容怎么写 /
  谁在看这类内容 → press 不对 on any wrong item, or 都不对？我自己写 → edit the three fields →
  以我说的为准 → 开始写第一条内容.
- **Expected:** the capability chip reads 读懂了内容 (structured_llm) or
  只数了标签，没读懂内容 (deterministic_fallback) or 以你说的为准 (user_edited)
  (`ReferenceAnchorPage.tsx:29-33`, `:257`); each item shows a support count
  (`只有 1 条参考这么说` / `N 条参考里都有`, `ReferenceAnchorPage.tsx:36-40`); a
  user-authored anchor is never overwritten by a later reference set
  (`ReferenceAnchorPage.tsx:329`).
- **Live evidence:** `docs/reviews/reference-anchor-r6-r7-2026-09-15.md:52-66` documents the
  three conclusions, the support counts and the reject/rewrite distinction.
- **Ambiguities flagged in that review:** no per-item reference deletion exists
  (`:158-159`); `structure_habits` is optional so a partial read is partially used (`:63-65`);
  the route lives under `/onboarding/` despite being reachable post-onboarding.

### J5 — 晨报 / Today (single NextBestAction)

- **Route:** `/` (`App.tsx:66`).
- **Steps:** open `/` → read the one action card (title, reason, 依据/还不知道, mode chip,
  expiry) → press the primary button, or 暂不做, or 不适合我 → type a reason → 停止这条建议,
  or 手动继续, or 问它.
- **Expected:** exactly one primary action rendered; `暂不做` produces the notice banner
  via `respondToAction(decision:'defer')` (`HomePage.tsx:157-163`); `停止这条建议` requires a
  non-blank reason and issues `decision:'reject'` (`HomePage.tsx:172-191`); the quiet counter
  card always renders four rows plus the completed-project count (`HomePage.tsx:271-277`).
- **Degradation:** the four side-counter calls are individually `.catch()`-guarded
  (`HomePage.tsx:94-97`) so they silently read 0; only `GET /today` failures show the error
  banner.
- **Ambiguity:** the IA doc renames this screen to `/today`; the implementation keeps `/`.

### J6 — 收件箱 → 生产线程 → 产出架 → 拾取 (flagship async loop)

This is the journey the whole product is organised around (`README.md:12`, `README.md:28-43`).
Steps and expectations:

1. **收件箱 `/loop/inbox`** (`App.tsx:72`). Paste text, pick a kind chip
   (📸 选照片 / 🎙 录语音 / ✎ 写一句 / 🔗 贴链接), optionally press 家人入镜？标记私密, then
   press 丢进去. **Expected:** `POST /loop/inbox`, notice `已丢进收件箱。`, and the item appears
   under 最近丢进来的 with its consent label and status (`InboxPage.tsx:178-190`).
   `frontend/e2e/async-loop.spec.ts:30-33` asserts this exact sequence.
2. **消化生产.** Press 消化生产. The page loops `POST /loop/inbox/digest?limit=1`
   (`InboxPage.tsx:105`) and shows `消化中 第 k 条 · 已用 N 秒`. **Expected:** notice
   `产出了 N 条新内容（用时 M 秒）。` plus a 去看产出架 → button
   (`InboxPage.tsx:116-120`, `:132-135`). Real model generation takes seconds to tens of
   seconds (`docs/dogfood/tester-brief-2026-09-15.md:39`).
3. **Privacy invariant.** A material marked 私密 must never appear as a deliverable
   (`specs/013-async-creation-loop/spec.md:13`). **Test:** add a private item, digest, and
   assert the shelf count is unchanged.
4. **Structural precheck is load-bearing.** If the produced draft fails the hook/points/ending,
   title, length or fact-traceability check, the deliverable does **not** become `ready`; the
   material stays in the inbox and a `needs_input` production event is recorded
   (`backend/app/services/async_loop.py:468-476`). **Test:** confirm the shelf count does not
   increase and the inbox item is not marked 已消化.
5. **产出架 `/loop`** (`App.tsx:71`). **Expected:** one card per ready deliverable with
   `{content_form}` or the three-value intent label, an 探索位 · 尝试 tag when
   `is_exploration`, a 结构预检通过 tag when the precheck passed, `事实 ×N 已溯源`, the
   suggested publish day, the fact count, and the window days
   (`AsyncLoopPage.tsx:248-267`).
6. **拾取.** Press 拾取 on a card, then in the right-hand panel fill 希望读者的变化（必填）,
   choose 教方法 / 讲经历 / 记过程, and press 认领. **Expected:** notice
   `已认领。这条产出会在 7 天观察窗内等你发布。` (`AsyncLoopPage.tsx:102`) and the card leaves
   the shelf (`frontend/e2e/async-loop.spec.ts:52-57`).
7. **Pickup hand-off (verified in code).** `AsyncLoopService.pickup`
   (`backend/app/services/async_loop.py:616-676`) calls `ContentProjectService.create`
   (`:638`), `IntentConfirmationService.confirm` (`:650`) and `_hand_over_produced_work`
   (`:660`, defined at `:678-714`), which **attaches the source inbox materials as
   `private` materials** (`:716-745`) and **seeds the produced draft as the project's first
   content version with `change_origin="ai"`** (`:702-714`). No `evidence_items` are fabricated
   (comment at `:687-689`). **Test:** after pickup, `GET /projects/{id}/calibration` must report
   a current version whose body equals the deliverable body, and the workspace must open on
   「逐段确认」 rather than 「先写下真实经历」.
   - Background: `docs/reviews/async-loop-pickup-handoff-gap-2026-09-15.md:33-74` documents the
     gap this fixed; `docs/reviews/async-loop-walkthrough-round3-2026-09-15.md:15-26` documents
     the fix landing.
8. **落选 / 过期 → 灵感池.** Press 不选了 or one of the four attribution buttons
   (太俗 / 选题不对 / 换换口味 / 时机不对) → notice `已回到灵感池。`
   (`AsyncLoopPage.tsx:104-111`; asserted by `frontend/e2e/async-loop.spec.ts:87-93`). Then in
   the 灵感池 tab, 重新上架 resets the 7-day window and 永久删除 asks for a `window.confirm`
   first (`AsyncLoopPage.tsx:194-213`).
9. **Metrics.** Back in the inbox, press 记一笔本周维护时长 → enter minutes → 记下 →
   `POST /loop/metrics` with `metric: 'weekly_minutes'` (`InboxPage.tsx:226-238`).
10. **Publish + review.** Continues in the content-project loop (J8) and weekly review (J9).

- **Explicit non-goals to assert:** the app never publishes to Xiaohongshu and never reads
  platform data; 「定时」 is only a reminder (`README.md:98`).
- **Ambiguities:** `README.md:52` still describes production as
  "确定性骨架生产（无模型可用…）" while `docs/reviews/ux-audit-2026-09-13/round6-promises-delivered.md:15`
  records the upgrade to real model generation with deterministic fallback. Both paths exist
  in code (`async_loop.py:431-458`). Also, `specs/013-…/spec.md:24` lists 周复盘批量接口 and
  急稿前端 as out of scope for Phase 1, yet both are shipped — treat that exclusion list as
  stale.

### J7 — 急稿 (urgent draft)

- **Route:** `/urgent` (`App.tsx:74`). **Actor:** any signed-in creator with a "publish now"
  impulse.
- **Steps:** type 这篇想说什么？ → type 一句真实经历（它只基于这个写，不编） → pick one of
  记过程 / 讲经历 / 教方法 / 让它判断 → press 生成成品，进入发布检查 → land in
  `/content/{newProjectId}`.
- **Expected:** `POST /projects` then (only when an intent chip was chosen)
  `POST /projects/{id}/intent:confirm`; then a best-effort
  `GET /projects/{id}/next-action` + `POST /actions/{id}:respond` that pre-fills the
  experience as the key-question answer (`UrgentPage.tsx:49-63`). This pre-fill is exactly the
  fix described at `docs/reviews/ux-audit-2026-09-13/round4-p1-fixes.md:12`.
- **Failure mode to test:** the pre-fill block is wrapped in a swallowed `try/catch`
  (`UrgentPage.tsx:61-62`) — a failure must still land the user in the workspace with a
  manual answer box, never a stuck screen.
- **Alternative exit:** 存回收件箱，不急 → `/loop/inbox`.
- **Ambiguity:** the plan says the urgent entry shares a screen with the inbox
  (`docs/ai-native-async-creation-plan-2026-08-29.md:62`); it is actually a separate page.

### J8 — Content project loop (内容项目闭环)

- **Routes:** `/content` (`App.tsx:67`) and `/content/:projectId` (`App.tsx:68`).
- **Entry points:** 新建项目 in the list (`ContentPage.tsx:302`); a starter project row or
  继续当前实验 (`StarterPage.tsx:294`, `:303`); 继续这条内容 from an adopted opportunity
  (`OpportunitiesPage.tsx:252`); 打开下一篇项目 from a series extension
  (`SeriesPanel.tsx:391`); the urgent path (J7); a picked-up deliverable (J6).
- **Step sequence (the order the UI itself enforces, via `next_action`):**
  `create_version` → `lock_hypothesis` → `record_publication` →
  `await_observation_window`/`add_snapshot` → `run_blind_review` → `create_observation` →
  `manage_observations` (`ContentPage.tsx:1204-1239`).
  1. **Start.** In `ProjectStartPanel`, type 一句话说说你想做什么 → 开始, or pick one of up to
     three inbox items. **Expected:** `POST /projects/start`, then navigation to
     `/content/{id}` carrying the inference in router state
     (`ContentPage.tsx:325-334`).
  2. **AI inference banner.** When `inference.source === 'ai'` the workspace shows
     `我按「{label}」来准备这条` with a reason and 不对，我自己选
     (`ContentPage.tsx:413-438`). Pressing it calls
     `POST /projects/{id}:dismiss-inference` and clears the banner.
  3. **Confirm the working intent.** Either the open question 希望读者发生的变化
     (+ 处理方式 select) → 确认这个方向 (`ContentPage.tsx:787`), or the retrospective
     classification branch for legacy published content (`ContentPage.tsx:726-742`).
  4. **Answer the key question.** With a `user_fact` gate, decide 确认并准备候选内容 /
     不使用这段经历 (`ContentPage.tsx:805-829`); without a gate, 你的回答 (≥10 chars) →
     让 AI 准备候选内容 (`ContentPage.tsx:851`).
  5. **Segment-by-segment confirmation.** Each segment renders with
     `data-testid="candidate-segment"` and `data-status`; press 确认保留 / 拒绝这一段, and for
     a rejected segment fill 替换这一段 → 提交替换内容. When nothing is pending the page shows
     `所有段落都已确认，可以进入发布前检查。` and reveals
     确认候选内容并进入发布准备 (`ContentPage.tsx:1085`, `:899`).
     `frontend/e2e/intent-driven-loop.spec.ts:87-99` and
     `frontend/e2e/starter-flow.spec.ts:58-69` both drive this loop.
  6. **Lock the publish judgment.** Fill the intent-specific required field
     (solve → 读者遇到什么问题 + 你准备给出的答案; share → 创作者视角或经历锚点;
     record → 读者可持续关注的过程或变化), plus 预期受众变化, 主要反应, 观察窗口（天） →
     锁定发布意图 (`StageForms.tsx:591-631`). The button is disabled until the required field
     for the project's intent is filled (`StageForms.tsx:393-397`).
     **Legacy-content branch:** a published legacy project with no `content_intent` cannot lock
     and shows an explanatory alert instead (`StageForms.tsx:402-414`).
  7. **Publish check + manual publish.** Press 运行检查 → `POST /projects/{id}/publish-checks`;
     press 我已了解 on each finding until none remain; the chip then reads 可以发布. Enter
     小红书笔记链接 and 发布时间 → 确认已发布
     (`StageForms.tsx:890-924`). The submit button requires a `clear`, non-stale check bound to
     the locked version (`StageForms.tsx:744-749`).
  8. **Back-fill performance.** 数据时间 + the six metric fields → 保存数据快照, or tick
     最终无法取得这次结果 and give a reason → 确认结果不可用
     (`StageForms.tsx:1097-1138`). Screenshot path: 选择数据截图 → 识别截图数据 → review the
     proposal → tick 我已逐项核对截图识别结果 → save.
  9. **Blind review.** 查看这次结果 → `POST /projects/{id}/blind-reviews`
     (`StageForms.tsx:1169-1186`). The result appears as `ReviewSummary` with a calibration
     alert and per-claim comparison rows (`ReviewSummary.tsx:38-64`).
  10. **Observation → learning.** Either the learning gate panel (下一步 select →
     确认未知结果和下一步, or 确认并保存下一轮实验 / 暂不保存,
     `ContentPage.tsx:948-1020`) or `ObservationForm` (这次看到了什么 + 下一次怎么验证 →
     保存观察, `StageForms.tsx:1238-1257`), then the 观察工作台 actions (继续验证 / 吸收 /
     证伪 / 归档 / 尝试形成经验候选, `ObservationList.tsx:111-170`).
  11. **Workspace editing anywhere.** 当前内容标题 + 当前内容正文 + 保存修改 creates a new
     version (`ProjectWorkspace.tsx:573-581`). Offline edits persist to `localStorage` and
     produce a 恢复 / 丢弃 alert after reload
     (`ProjectWorkspace.tsx:513-528`; driven end-to-end by
     `frontend/e2e/intent-driven-loop.spec.ts:114-125`).
- **Expected cross-cutting invariants:** a locked version is never overwritten; a stale publish
  check blocks publication; only user-confirmed insights enter long-term context
  (`README.md:23-26`).

### J9 — 周复盘 (weekly review)

- **Route:** `/loop/review` (`App.tsx:73`). **Precondition:** at least one published project in
  the queried window.
- **Steps:** open the page → read each row's `判断 · {primary response} ｜ 实际 · {metrics}` →
  read the stage pill → press 问 to ask the companion about that row → press the row title or
  去项目工作台确认 to go confirm in the workspace.
- **Expected:** rows render `{weekday} day` links to `/content/{project_id}`
  (`ReviewPage.tsx:61`); an unavailable result renders 截图缺失 rather than 0
  (`ReviewPage.tsx:72-73`); an empty result set shows
  `本周期还没有已发布的内容。发布并回填数据后，这里会出现对照行。`
  (`ReviewPage.tsx:55`). `frontend/e2e/async-loop.spec.ts:64-74` asserts the heading and that
  one of the five stage strings is visible.
- **Confirmed by code:** the page is read-only — there is no confirmation control on it, and
  the footer explicitly says 确认后，有效经验才会进入它的成长 (`ReviewPage.tsx:97`).
- **Ambiguity (important):** the page requests `listWeekly(60)` (`ReviewPage.tsx:32`) while the
  API default and all product docs say 7 days (`backend/app/api/v2/async_loop.py:148`,
  `docs/ai-native-async-creation-plan-2026-08-29.md:24`). A tester must decide which window the
  product intends before asserting row counts.

### J10 — 成长 (growth page)

- **Route:** `/growth` (`App.tsx:75`).
- **Steps:** open the page → read 它的积累 counters (已确认经验 / 已确认观点 / 持续系列 /
  内容项目 / 今日 AI 调用) → read 成对里程碑 → read 信任面板 → press the switches.
- **Expected:** all counters come from real server data
  (`GrowthPage.tsx:26-31`); the milestone card states
  `里程碑只在真实行为满足时点亮——不作表演性进度。当前均为「待达成」。` (`GrowthPage.tsx:93`);
  the trust panel lists three capabilities with the ≥3-accepted rule
  (`GrowthPage.tsx:100`).
- **Documented behaviour:** the switches are **display-only** (A6) — 自主准备 and 探索位 only
  print 该能力将随后续版本开放，当前为展示状态。, and 私密素材参与生产 has no handler at all.
  `docs/reviews/ux-audit-2026-09-13/round2-pm-analysis.md:19,51` records this as audit item D6
  (unresponsive switches with internal-spec accessible names), and any write API is gated behind
  a new spec. **Test it as read-only and report the copy, not a broken toggle.**

### J11 — 机会 (opportunities)

- **Route:** `/opportunities` (`App.tsx:69`).
- **Steps:** press 生成内容机会 → read the notice → optionally use 筛选 + the two selects →
  press 手动添加来源 → fill 关键词或原始内容 → 保存并等待核验 → for a pending item fill
  原始链接 / 发布时间 / 权威来源 / 当前时效 → 确认来源信息 (or 标记来源不足) → fill
  这篇内容的标题 / 希望读者看完发生什么变化 / 需要的真实素材 → 采用并创建内容 →
  继续这条内容.
- **Expected:** the notice distinguishes the two outcomes — `生成了 N 条新机会，请在下方逐条确认。`
  vs `暂时没有生成新的机会。可能是 AI 服务未配置完整，或你的历史内容与画像还不够；也可以手动添加来源。`
  (`OpportunitiesPage.tsx:314-316`). Verification and adoption are gated: the adoption form
  only renders once `verification_status === 'verified'` and the required-action is not
  `source_expired` (`OpportunitiesPage.tsx:235-237`).
- **Explainability contract:** each row shows source class, rationale, source excerpt,
  `readableRef`-transformed source refs, evidence refs, and eight qualitative dimensions
  (`OpportunitiesPage.tsx:164-207`). No row may claim realtime/trending/viral likelihood
  (`specs/008-content-project-mvp/spec.md:169`).
- **Security behaviour to test:** a `javascript:` or `data:` source URL must render as inert
  text ending in `（不可信链接，已禁用跳转）` (`OpportunitiesPage.tsx:68-73`).
- **E2E-confirmed manual path:** `frontend/e2e/intent-driven-loop.spec.ts:54-74`.
- **Ambiguity:** the spec-008 contract documents `/opportunities`,
  `/opportunities:generate`, `PUT /opportunities/{id}/decision`; the implementation exposes
  `/content-opportunities*` (§4.11). Use the implemented paths.

### J12 — 素材 (materials)

- **Route:** `/materials` (`App.tsx:70`), also reachable from the workspace drawer
  (`ContentPage.tsx:608`, `:639`) and the mobile 更多 sheet.
- **Steps:** 添加素材 → choose 素材类型 → 素材标题 → for text/link fill 素材内容, for
  image/document/audio/video pick a file → 隐私级别 → optional 关联项目 → 保存素材. Then per
  material: pick 复用到项目 → 关联; for audio/video press 识别内容 / 重新识别; press 删除 and
  handle the impact alert.
- **Expected:** notice `素材已保存。` / `素材已关联到所选项目。` / `识别完成：文字已写进这条素材…`
  / `素材已删除。` (`MaterialsPage.tsx:127`, `:155`, `:189`, `:171`).
- **Delete-impact contract:** a material referenced by a locked version must render
  `将影响：{project titles}` with 保留引用快照并删除 and 取消 rather than a plain error
  (`MaterialsPage.tsx:265-278`).
- **Model-provenance contract:** once analysed, the card must state the text was read by a model
  and may be wrong (`MaterialsPage.tsx:249-254`); an unanalysed audio/video card must warn that
  recognition sends the file to an external model and that sensitive material is not sent
  (`MaterialsPage.tsx:255-261`).
- **Refusal to test:** pressing 识别内容 on a `sensitive` material must produce the readable
  refusal from `material_analysis.py:62-66`, not a 500.

### J13 — 我的 (settings / export / delete)

- **Route:** `/me` (`App.tsx:76`).
- **Settings:** edit 每周发布目标 / 内容策略 / 小红书账号备注 / 每晚自动整理收件箱（03:00） →
  保存设置 → `PUT /settings` → notice `设置已保存`. Round-trip the nightly toggle and confirm
  it defaults to off (`MePage.tsx:61`, `:90`).
- **Password:** 当前密码 + 新密码（至少 8 位）+ 再输入一次新密码 → 更新密码.
- **Export:** 导出个人数据 → an info alert appears → 确认并下载 → a
  `topicai-account-data-{date}.json` download plus notice `个人数据已导出`
  (`MePage.tsx:166-180`, `:302`).
- **Delete:** 删除账户 → an error alert with the irreversibility warning → type exactly
  `永久删除` → 永久删除账户 → gate decision, `DELETE /account` (202), logout, redirect to
  `/login` (`MePage.tsx:189-200`, `:303-313`).
- **Expected invariants:** export requires the privacy gate first; deletion requires both the
  gate and the exact typed phrase (`MePage.tsx:190`); the data-export button is disabled while
  an export gate is already open (`MePage.tsx:311`).
- **Live evidence of a completed deletion:** `docs/reviews/reference-anchor-r6-r7-2026-09-15.md:133-134`
  records 申请 → 人工门确认 → 删除 with no reference/anchor residue and a 401 on the old login.
- **Ambiguity (blocking for a validation assertion):** the UI accepts a weekly goal of **1–7**
  (`MePage.tsx:220`) while `CONTEXT.md:50-53`, the plan and
  `docs/testing/dogfood-falsification-protocol.md:61` all say **1–4**. Decide before asserting.

### J14 — 悬浮球对话 (companion, global)

- **Route:** none — mounted on every guarded route (`AppLayout.tsx:24`).
- **Steps:** click the 对话悬浮球 → type a question → press ↑ or Enter → read the answer →
  press 渐隐 then 唤醒 → press 关闭. Also reach it from a card's 问它 / 问 button to verify the
  context chip.
- **Expected:** the context chip matches the injected string (`产出架 · {title}`,
  `周复盘 · {title}`, `灵感池 · {title}`, `晨报 · 当前行动`); the panel is fully on-screen at
  390px; a model failure surfaces the error text as the reply rather than a canned answer
  (`CompanionDialog.tsx:154-157`).
- **Do not treat as AI output:** the two proactive messages pushed at 2.2s and 14s are
  hard-coded demo strings, suffixed `（演示）` (`CompanionDialog.tsx:127-137`). The header
  comment says they await the orchestrator.
- **Ambiguity:** the plan says the first release has **no free-form chat**
  (`docs/ai-native-async-creation-plan-2026-08-29.md:25`), yet `/companion/ask` is a live
  free-text model call. The zen fade timing is 12s in code (`CompanionDialog.tsx:23`) and 8s in
  `docs/handoffs/topicai-handoff-2026-09-02-lumen-visual-acceptance.md:68`.

### J15 — Personalisation assets (series / viewpoints / rules)

- **Where:** `/content/:projectId` → the 参考与提醒 column
  (`ProjectWorkspace.tsx:625-698`), plus `/growth` for the counts.
- **Series:** tick ≥2 eligible published projects → 发现系列 → edit 系列名称 /
  系列共同价值 / 下一篇延展方向 → 确认这个系列 → 准备下一篇 → fill the next-episode fields →
  确认并创建项目 → 打开下一篇项目 (`SeriesPanel.tsx:169-421`).
- **Viewpoints:** confirm an intent, then in 你的观点 press 提炼候选 → edit 观点候选 →
  确认是我的观点 (or 不是我的观点), and 撤销观点 to revoke
  (`ViewpointPanel.tsx:64-144`).
- **Rules:** in 观察工作台 press 尝试形成经验候选 → 确认经验 / 拒绝; resolve conflicts with
  保留为例外 / 缩小适用范围 / 停用当前规则; roll back with 回滚到版本 {n}
  (`ObservationList.tsx:240-306`).
- **Expected invariants:** a series with mixed member intents/formats must still appear
  (matching uses `scope.member_intents` / `member_formats`, `SeriesPanel.tsx:71-81`, `:139-149`);
  the 吸收 observation action stays disabled until the observation is `pending_validation`
  (`ObservationList.tsx:77`, `:131`), which matches the 1-sample threshold described at
  `docs/reviews/creation-flow-rework-r1-r5-2026-09-14.md:33`.
- **Ambiguity:** `content_form` (the AI-named open content form) is a plan item; the shipped
  code reads and displays it (`AsyncLoopPage.tsx:251-253`, `ProjectWorkspace.tsx:376-381`) but
  `specs/011-creator-series-scope/spec.md` still treats the three-value enum as authoritative.
  Test the displayed value, not a taxonomy.

### 5.1 User journeys the docs describe but the code does not implement

| Documented | Status | Evidence |
|---|---|---|
| `POST /projects/{id}/interview:generate` and `…/interview-answers` | **Not implemented.** No `interview` route exists under `backend/app/api/v2/` (verified by grep). The closest shipped equivalent is `POST /projects/{id}/field-suggestions`. | `specs/008-content-project-mvp/contracts/api-v2.md:36-37` vs §4.19 |
| `?view=overview\|brief\|create\|publish\|review` workspace sub-views and deep links | **Not implemented.** One route with internal step state. | `docs/frontend-reconstruction-audit-2026-07-19/new-information-architecture.md:53-58` vs `App.tsx:68` |
| `/today`, `/me/state`, `/me/strategy`, `/me/account`, `/me/ai`, `/me/privacy`, `/opportunities/:id`, `/materials/:id`, `/onboarding/history`, `/onboarding/profile-review`, `/onboarding/readiness` | **Not implemented.** Only the paths in §1 exist. | `docs/frontend-reconstruction-audit-2026-07-19/new-information-architecture.md:157-170` vs `App.tsx:65-84` |
| Weekly review with in-page batch confirmation | **Not implemented** — read-only aggregation plus a deep link. | `docs/ai-native-async-creation-plan-2026-08-29.md:24,58` vs `ReviewPage.tsx` |
| Trust-panel write APIs, level up/down, drift proposals, exploration-slot panel, milestone lighting | **Not implemented** (Phase 4, evidence-gated). | `docs/ai-native-async-creation-plan-2026-08-29.md:157`; A6 |
| Automated publishing / platform data sync / scheduled publishing | **Explicit non-goals.** | `README.md:96-103` |
| v4.1 multi-platform, hot-topic, viral-score, team/MCN features | **Historical documents, not the product.** `docs/product-functional-document.md` even carries inline `删掉这个功能` notes (`:45`, `:284`). Do not derive journeys from `docs/product-introduction-user.md` or `docs/product-functional-document.md`. | `README.md:96-103`; `specs/008-content-project-mvp/spec.md:169-193` |
| `/api/v1` legacy routes | **Must 404 without redirect.** | `specs/008-content-project-mvp/spec.md:193` |

---

## 6. AI-dependent features and their degradation behaviour

### 6.1 The vocabulary actually used (no `data_source` field exists)

The brief asks about `data_source`. **There is no field, column, or TypeScript property named
`data_source` anywhere in this codebase** — verified by grepping `backend/app/**/*.py` and
`frontend/src/**/*.ts*` for `data_source`: zero matches. The v2 product replaced that v4.1
concept with three concrete, per-feature fields:

| Field | Where | Values | Meaning |
|---|---|---|---|
| `source` | field suggestions (`backend/app/models/v2/field_suggestion.py:43`), project start (`backend/app/models/v2/project_start.py:47`) | `ai` \| `deterministic_fallback` | whether this payload came from a real model call |
| `proposal_source` | content opportunities (`backend/app/models/v2/content_opportunity.py:167`) | `ai` \| `deterministic_fallback` | same, for opportunity proposals |
| `capability` | reference anchor (`backend/app/models/v2/reference_anchor.py:44-45`) | `structured_llm` \| `deterministic_fallback` \| `user_edited` | includes the "the user overrode the model" case |
| `AITrace.capability` / `outcome` | every production/review trace (`app/services/ai_trace.py`) | `text` \| `vision` \| `omni_media` \| `deterministic_fallback` / `success` \| `fallback` | the audit record |

The "AI is available" predicate is `LLMClient.is_available(capability)`
(`backend/app/core/llm.py:45-52`): `settings.ai_enabled AND the OpenAI-compatible client was
constructed AND the capability is in `llm_capabilities``; `vision` additionally requires
`settings.vision_enabled` (`llm.py:46`). `/me` surfaces the same booleans at
`MePage.tsx:267-277` via `GET /settings` (`backend/app/services/settings.py:47-56`).

### 6.2 AI-dependent surface, one row per feature

| # | Feature / trigger | Model call | Fallback when unavailable or erroring | Degradation state surfaced to the user | Citation |
|---|---|---|---|---|---|
| 1 | **Inbox digest** — 消化生产 → `POST /loop/inbox/digest` | `ProductionService._draft_from_ai` → `LLMClient.generate_structured(DIGEST_SYSTEM_PROMPT, _Draft, temperature=0.3)` | `_draft_from_ai` returns `None` on **any** exception (logged as a warning); `_produce` then uses a deterministic skeleton: title from the item, body = title + raw content + the bracket `[请在发布前补充并确认具体细节：…]`, the constant `OUTLINE`, and a judgement with `audience_problem`, `reader_promise`, `content_form` all `None` | `deliverables` row is still produced, tagged `source = "deterministic_fallback"` in the `ready` production event (`draft_source`); an `AITrace` is written with `capability="deterministic_fallback"`, `outcome="fallback"`, `policy_version="async-loop-deterministic-v1"`, and the limitation `模型不可用；确定性骨架产出` (or `其中 N 条降级为确定性骨架` when a batch is mixed) | `backend/app/services/async_loop.py:387-424`, `:426-504`, `:519-569` |
| 2 | **Digest — privacy refusal path** | n/a | `consent='private'` material is excluded before any call | item stays in the inbox; never becomes a deliverable | `specs/013-async-creation-loop/spec.md:13` |
| 3 | **Digest — structural precheck failure** | n/a | the deliverable is not inserted; a `needs_input` production event is written with `{"reason": "precheck_failed", "issues": [...]}` | shelf count does not increase; material remains 待消化 | `backend/app/services/async_loop.py:468-476` |
| 4 | **Start a piece of content** — `POST /projects/start` | `ProjectStartService._infer` → `generate_structured(_START_SYSTEM_PROMPT, _StartInference, temperature=0.3)` | on exception: `intent=None`, `intent_label=""`, `reason="这次没判断出来——不猜，你说了算。"`, `confidence="low"`, a generic next question, `audience_change=None`, `source="deterministic_fallback"` | the workspace **hides** the inference banner entirely because it only renders when `inference.source === 'ai' && inference.intent` (`ContentPage.tsx:413`); the project is created without an intent and `intent_status` stays `candidate`, so the normal 确认内容目的 step runs | `backend/app/services/project_start.py:90-129`; `frontend/src/pages/Content/ContentPage.tsx:413-438` |
| 5 | **Field suggestions** — every `FieldSuggestions` panel → `POST /projects/{id}/field-suggestions` | `FieldSuggestionService._draft` → `generate_structured(…, temperature=0.4)` | `_fallback_candidates` returns generic directions / fillable skeletons, and the limitation `AI 暂时不可用：下面这些是通用方向或写法骨架，不是针对这条内容的判断，请按你的实际情况改。` is appended | the panel header reads `AI 给的方向` when `source === 'ai'` and `先给你几个方向` otherwise; `limitations[0]` renders as the footer note | `backend/app/services/field_suggestions.py:75-115`, `:143-189`, `:244`; `frontend/src/features/content/FieldSuggestions.tsx:103`, `:126` |
| 6 | **Candidate content drafting** — respond to `answer_key_question` / confirm evidence → `POST /actions/{id}:respond`, `POST /human-gates/{id}:decide` | `CandidateDraftService._draft` → `generate_structured(…, "你是证据约束型内容编辑…")` | deterministic skeleton built from the user's own answer plus the intent's material list, ending in `[请在发布前补充并确认具体细节：对照上方建议结构逐条写下你亲身经历的内容，写不出的条目直接删除；当前版本不会虚构缺失经历。]`; `evidence_refs=["user_confirmed_answer"]` | the bracket text is visible inside the candidate segments and **is** asserted by `frontend/e2e/intent-driven-loop.spec.ts:85`; segment confirmation still gates the next step | `backend/app/services/intent_actions.py:594-629` |
| 7 | **Publish check** — 运行检查 → `POST /projects/{id}/publish-checks` | deterministic rules **always** run first (`_deterministic_findings`); AI findings are appended only if `is_available("text")` | exceptions are caught and only recorded: `Optional AI assistance was unavailable: {ExceptionType}.`; when unconfigured: `Optional AI assistance was not configured; deterministic rules ran.` | the check still returns findings and a status; the limitations array is part of the check payload, and the UI always shows the disclaimer `本检查仅提供辅助，不保证平台审核通过。` | `backend/app/services/publish_check.py:55-104`; `frontend/src/features/content/StageForms.tsx:857` |
| 8 | **Screenshot metric extraction** — 识别截图数据 → `POST /snapshots:extract` | `SnapshotExtractionService` → `LLMClient.vision_generate` | **no fallback**: `is_available("vision")` false raises `AICapabilityMissingException("vision")` → **HTTP 422** `AI_CAPABILITY_MISSING`; unparseable output raises `LLMStructuredOutputException` → **HTTP 502** `LLM_STRUCTURED_OUTPUT_FAILURE` | the error surfaces through the workspace error banner (`runCommand` catch, `ContentPage.tsx:261`); manual metric entry remains available because the six number fields are always rendered | `backend/app/services/snapshot_extraction.py:50-51`, `:76-87`; `backend/app/core/exceptions.py:85-114` |
| 9 | **Audio/video material analysis** — 识别内容 → `POST /materials/{id}:analyze` | `MaterialAnalysisService` → `OmniClient.describe_media` | `OmniNotConfiguredException` and `OmniMediaRejectedException` are re-raised as `UserActionRequiredException` (HTTP 400 with the original message); an empty transcription raises `模型这次没有读出内容（可能是素材太短或格式问题），可以换个片段再试。` | the message lands in the page error alert (`MaterialsPage.tsx:237`); `sensitive` material is refused **before** the call with `这条素材标着「敏感」…`; a successful analysis renders the provenance sentence naming the model | `backend/app/services/material_analysis.py:51-94`; `frontend/src/pages/Materials/MaterialsPage.tsx:183-196`, `:249-261` |
| 10 | **Companion ask** — 悬浮球 → `POST /companion/ask` | `CompanionService.answer` → `llm.generate(..., temperature=0.4, max_tokens=400)` — **no try/except** | a missing/unavailable model raises `AINotConfiguredException` → **HTTP 503** `AI_NOT_CONFIGURED`; a timeout → **504** `LLM_TIMEOUT`; anything else → **503** `LLM_ERROR` | the dialog pushes the error text as the assistant reply (`extractErrorMessage(err, 'AI 暂时无法回答，请稍后再试。')`) — explicitly "honest failure" rather than a canned answer | `backend/app/services/companion.py:18-42`; `backend/app/core/llm.py:70-73`, `:93-102`; `frontend/src/features/companion/CompanionDialog.tsx:145-158` |
| 11 | **Reference anchor read** — 读这些参考 → `POST /reference-imports` + `GET /reference-anchor` | `ReferenceAnchorService._read_references` → `generate_structured(_ANCHOR_SYSTEM_PROMPT, _AnchorDraft, temperature=0.3)` | on any exception `_read_deterministically`: topics = tag frequency (top 5), `structure_habits=[]`, `audience=None`, capability `deterministic_fallback`, limitations `模型不可用，当前只用了可数的信号（参考里的标签），没有读懂内容本身` and a "no audience" note | the capability chip renders 只数了标签，没读懂内容; the limitations render as a list; the 谁在看这类内容 block is replaced by an explicit empty-state telling the user to fill it themselves | `backend/app/services/reference_anchor.py:221-293`; `frontend/src/pages/Onboarding/ReferenceAnchorPage.tsx:29-33`, `:257`, `:285-296` |
| 12 | **Content opportunity generation** — 生成内容机会 → `POST /content-opportunities:generate` | **No model call at all.** `ContentOpportunityService.generate` is deterministic from profile + imported history + materials + confirmed insights + series | when `content_pillars`, `niche` or `target_audience` are missing it returns `[]`; every row is written with `proposal_source='deterministic_fallback'` | zero results produce the explanatory notice naming AI configuration and insufficient history as the likely causes; every opportunity carries the limitation `仅使用用户历史、个人素材、已确认洞察和当前有效画像，不代表实时趋势或效果预测` | `backend/app/services/content_opportunity.py:95-111`, `:364-366`, `:450`; `frontend/src/pages/Opportunities/OpportunitiesPage.tsx:314-316` |
| 13 | **Series-extension opportunity** — 准备下一篇 → `POST /creator-series/{id}/extension-opportunities` | `_draft` → `generate_structured(…, SeriesExtensionDraft)` | deterministic draft built from the series' own confirmed continuation prompt and promise; limitations `模型不可用；候选直接来自用户已确认的系列延展方向` (+ a mixed-intent warning) | `proposal_source` = `deterministic_fallback`; the candidate still requires the user's 确认并创建项目 | `backend/app/services/content_opportunity.py:1174-1219`; `frontend/src/features/content/SeriesPanel.tsx:364-377` |
| 14 | **Series detection** — 发现系列 → `POST /creator-series-candidates` | `CreatorSeriesService._draft` → `generate_structured(…, SeriesDraft)` | fallback name `{first title}等N篇内容`, rationale `模型不可用，仅保留用户选中的项目关系，没有推断共同主题。`, a placeholder continuation prompt, and two limitations | the candidate renders in the 内容系列 panel with its rationale and still needs 确认这个系列 | `backend/app/services/creator_series.py:346-384` |
| 15 | **Viewpoint extraction** — 提炼候选 → `POST /projects/{id}/viewpoint-candidates` | `CreatorViewpointService._draft` → `generate_structured(…, ViewpointDraft)` | fallback statement = the user's own first confirmed evidence statement verbatim, rationale `直接保留用户已确认的陈述，没有扩写为新的长期主张。`, limitations `模型不可用；当前候选为原文保守降级` | the candidate textarea is pre-filled with the raw confirmed statement and still needs 确认是我的观点 | `backend/app/services/creator_viewpoint.py:330-359` |
| 16 | **Next-best-action orchestration** — `GET /today`, project `next_action` | **No model call.** Rule-based orchestration | n/a — deterministic by design | an `AITrace` is still written with `capability="deterministic_fallback"` and the limitation `未调用生成模型；当前行动由可审计规则产生` | `backend/app/services/intent_orchestrator.py:710-744` |
| 17 | **Starter direction generation** — 查看候选方向 → `POST /starter/directions:generate` | **No model call.** Deterministic copy from the assessment assets | n/a | `capability="deterministic_fallback"`, limitations include `未调用生成模型，当前为可审计的确定性降级结果` | `backend/app/services/direction_candidate.py:81-139` |
| 18 | **Growth onboarding profile** — 导入历史内容 → `POST /history-imports` | **No model call.** `creator_profile_v2` infers attributes from imported notes deterministically | attributes are labelled `provisional` below 10 notes | per-attribute chips show 暂定/已确认/已拒绝 + 低/中/高置信 + evidence count + human-readable limitation strings (`Fewer than 10…` → 历史内容少于 10 条，判断仍可能变化) | `frontend/src/pages/GrowthOnboarding/GrowthOnboardingPage.tsx:200-202`, `:245-263` |

### 6.3 Degradation states a tester must be able to read off the screen

| Observable | Where | Meaning |
|---|---|---|
| `AI 给的方向` vs `先给你几个方向` | `FieldSuggestions.tsx:103` | model-backed vs deterministic field candidates |
| footer note `AI 暂时不可用：下面这些是通用方向或写法骨架…` | `FieldSuggestions.tsx:126` | explicit field-suggestion fallback |
| capability chip 读懂了内容 / 只数了标签，没读懂内容 / 以你说的为准 | `ReferenceAnchorPage.tsx:257` | reference-anchor read quality |
| notice `暂时没有生成新的机会。可能是 AI 服务未配置完整…` | `OpportunitiesPage.tsx:316` | zero-opportunity outcome |
| limitation `模型不可用；候选直接来自用户已确认的系列延展方向` | `SeriesPanel.tsx:362` | series-extension fallback rationale |
| 这段文字是模型（{model}）读出来的，可能听错或漏读 | `MaterialsPage.tsx:250-253` | model-produced material text |
| 这条音频/视频还没有识别过；识别会把它发给外部模型（敏感素材不会被发送）。 | `MaterialsPage.tsx:257-260` | pre-analysis disclosure |
| AI 能力状态 chip 可用/不可用 + `需要管理员先完成 AI 服务配置…` | `MePage.tsx:269-275` | account-level AI availability |
| 文本能力：{可用/不可用} · 截图识别：{可用/不可用} | `MePage.tsx:276` | per-capability availability |
| assistant bubble containing an error message | `CompanionDialog.tsx:154-157` | companion honest failure |
| `AI 正常 · 本地编排` | `Sidebar.tsx:153` | **hard-coded and NOT bound to AI state — see A4; a tester must not use this as an availability signal** |

### 6.4 AI-transparency invariants worth asserting

1. **Every AI path writes an `AITrace`** with evidence refs, visibility boundary, contamination
   check, calibration state and limitations — see the trace writers at
   `async_loop.py:519-569`, `field_suggestions.py:105-107`, `publish_check.py:86-100`,
   `snapshot_extraction.py:92-111`, `material_analysis.py:96-129`, `reference_anchor.py:513`,
   `intent_orchestrator.py:710-744`, `direction_candidate.py:98-136`.
2. **Fact traceability is never relaxed by AI.** Digest facts always come from the source
   material, never from the model (`async_loop.py:465-467`; the comment at `:390-391` states
   this explicitly). On pickup each fact's `source_inbox_id` becomes a linked material
   (`async_loop.py:716-745`).
3. **No path claims model authorship when no call happened.** The deterministic branches set
   `source`/`policy_version`/`model_identifier` to the fallback values, and
   `model_identifier` is written as `None` rather than a model name
   (`async_loop.py:545-553`; `creator_series.py:104`; `creator_viewpoint.py:129`).
4. **`/api/v2` never returns `data_source="ai_inference"`** — that v4.1 value does not exist in
   the codebase at all (see §6.1).

---

## 7. Manual test checklist

Format: one row per exercisable feature. "Steps" give the literal visible labels or
`aria-label`s so an automated browser agent can follow them. Run each row against a fresh
account unless stated otherwise. `✓` in the **AI?** column marks a row whose behaviour changes
when the model is unconfigured — run it twice (with and without `LLM_*` set) where the release
process requires it.

### 7.1 Authentication and shell

| # | Feature | Steps | Expected observable result | AI? | Citation |
|---|---|---|---|---|---|
| T01 | Register | `/login` → 没有账号？注册 → fill `#login-username` (2+ chars), `#login-email`, `#login-password` (8+), `#login-confirm-password` → press 创建账号 | Redirect to `/`; heading matches `/^你好，/`; `localStorage.access_token` and `refresh_token` set | | `LoginPage.tsx:80-115`, `:53`; `authStore.ts:67-95` |
| T02 | Register validation | Repeat T01 with a 1-char name / 7-char password / mismatched confirmation | Inline `role="alert"` with the corresponding message; no network request | | `LoginPage.tsx:34-45`, `:66-68` |
| T03 | Login | `/login` → `#login-email` + `#login-password` → 进入 | Redirect to `/` with the sidebar rendered | | `LoginPage.tsx:71-115` |
| T04 | Logout (desktop) | At ≥1000px, sidebar footer → 退出 | URL `/login`; `access_token` removed; `GET /api/v2/auth/me` with the old token → 401 | | `Sidebar.tsx:164-179` |
| T05 | Logout (mobile) | At ≤390px, press 更多导航 → press 退出登录 | Same as T04; the sheet must disappear | | `Sidebar.tsx:114-145` |
| T06 | 更多 sheet auto-close | At ≤390px open 更多导航, pick 急稿 | URL `/urgent`; `.v3-more-sheet` removed from the DOM | | `Sidebar.tsx:93-97` |
| T07 | All 10 nav targets | For each of 晨报/产出架/收件箱/急稿/周复盘/成长/内容/机会/素材/我的 press the link and assert the page heading | Each reaches its route with the expected heading; no horizontal overflow at 1440×900 and 390×844 | | `frontend/e2e/intent-driven-loop.spec.ts:164-224` |
| T08 | Guard redirect | Log out, then open `/content` directly | Redirect to `/login` with `replace`; no sidebar flash beyond the hydration gate | | `App.tsx:48-49` |
| T09 | 404 outside guard | Log out, then open `/no-such-page` | `NotFoundPage` renders **without** a sidebar; 返回首页 → `/` → then `/login` | | `App.tsx:82-84`; `NotFoundPage.tsx:21` |
| T10 | Password change | `/me` → 当前密码, 新密码（至少 8 位）, 再输入一次新密码 → 更新密码 | Notice `密码已更新，下次登录请使用新密码。`; fields clear; re-login works with the new password | | `MePage.tsx:130-147`, `:257-263` |
| T11 | Password-change guard | Enter a new password equal to the current one, or mismatched confirmation | 更新密码 stays disabled; inline helper text explains | | `MePage.tsx:245`, `:252-259` |

### 7.2 晨报 `/`

| # | Feature | Steps | Expected observable result | AI? | Citation |
|---|---|---|---|---|---|
| T12 | Load the action | Open `/` | One action card with title, 约 N 分钟, outcome sentence, 依据/还不知道 line, mode chip, and an expiry date when present | | `HomePage.tsx:234-253` |
| T13 | Primary action | Press the primary button (or the card) | Navigates to the resolved destination (`/content`, `/content/{id}` or `/opportunities`) | | `HomePage.tsx:134-145`, `:235`, `:241` |
| T14 | 暂不做 | Press 暂不做 | Card text switches to 这件事已暂缓; the reject/defer buttons disappear; a `POST /actions/{id}:respond` with `decision=defer` was sent | | `HomePage.tsx:152-170`, `:230`, `:242` |
| T15 | 不适合我 + reason | Press 不适合我 → leave the reason blank | 停止这条建议 is disabled | | `HomePage.tsx:265` |
| T16 | 停止这条建议 | Press 不适合我 → type a reason → 停止这条建议 | `decision=reject` sent; card switches to the cancelled copy with the reason; buttons collapse | | `HomePage.tsx:172-191`, `:227-228` |
| T17 | 手动继续 | Press 手动继续 | Navigates to the same destination as the primary button; when that would be `/`, it goes to `/content` instead | | `HomePage.tsx:150`, `:244` |
| T18 | 去收件箱 | Press the read-only pseudo-input or 去收件箱 ↗ | `/loop/inbox` | | `HomePage.tsx:286-288` |
| T19 | Quick defer chips | Press 另一条先放着，别催我, then reload and repeat with 周五晚再拾取 | Each sends a defer with its own reason; the card shows the deferred state | | `HomePage.tsx:293-298` |
| T20 | Quiet counters | Read the 安静数据 card | Rows for 本周已发 / 本周维护时长 / 产出架待决定 / 收件箱待消化 / 已完成发布项目 | | `HomePage.tsx:271-277` |
| T21 | 查看内容项目 | Press it in the footer | `/content` | | `HomePage.tsx:305` |

### 7.3 收件箱 `/loop/inbox` and 产出架 `/loop`

| # | Feature | Steps | Expected observable result | AI? | Citation |
|---|---|---|---|---|---|
| T22 | Add material | Paste text → 丢进去 | Notice `已丢进收件箱。`; the item appears in 最近丢进来的 with the 可发布类 label and 待消化 status | ✓ | `InboxPage.tsx:78-87`, `:178-190` |
| T23 | Kind chips | Press 选照片 / 录语音 / 写一句 / 贴链接 in turn | The pressed chip becomes `btn-primary` | | `InboxPage.tsx:156-159` |
| T24 | Private consent | Press 家人入镜？标记私密 → add an item → digest | The consent line reads 私密 · 不出本地; the item never becomes a deliverable | ✓ | `InboxPage.tsx:169-174`; `spec.md:13` |
| T25 | Digest (one or more) | Press 消化生产 and watch | Progress text `消化中 第 k 条 · 已用 N 秒`; final notice `产出了 N 条新内容（用时 M 秒）。` with a 去看产出架 → button | ✓ | `InboxPage.tsx:91-121`, `:163-167` |
| T26 | Digest with nothing to do | Press 消化生产 on an empty inbox | Notice `没有可消化的新素材。` | ✓ | `InboxPage.tsx:116-120` |
| T27 | Shelf card contents | Open `/loop` after T25 | Card shows a content-form tag or intent label, 探索位 · 尝试 when applicable, 结构预检通过 when the precheck passed, `事实 ×N 已溯源`, the suggested day, fact count and window days | ✓ | `AsyncLoopPage.tsx:248-267` |
| T28 | 拾取 selection | Press 拾取 on a card | The right-hand panel title becomes `拾取 · 选择即确认` and its 希望读者的变化 field is pre-filled from the judgement | | `AsyncLoopPage.tsx:269-275`, `:287-339` |
| T29 | Intent chips | Press 教方法, then 讲经历, then 记过程 | `aria-pressed` follows the selection; only one chip is `.on` at a time | | `AsyncLoopPage.tsx:341-353` |
| T30 | 认领 guard | Clear 希望读者的变化 | 认领 becomes disabled | | `AsyncLoopPage.tsx:360` |
| T31 | 认领 | Fill 希望读者的变化 → 认领 | Notice `已认领。这条产出会在 7 天观察窗内等你发布。`; the card leaves the shelf; `GET /loop/deliverables?status=ready` no longer contains it | ✓ | `AsyncLoopPage.tsx:93-102` |
| T32 | Pickup hand-off | After T31, open `/content/{newId}` | The workspace opens on the candidate-confirmation step (not 先写下真实经历); 当前内容 shows the deliverable's title and body; the project-material drawer lists the source material | ✓ | `backend/app/services/async_loop.py:660-714` |
| T33 | 落选 attribution | 拾取 → 不选了 → then repeat and press each of 太俗 / 选题不对 / 换换口味 / 时机不对 | Notice `已回到灵感池。`; the deliverable appears in the 灵感池 tab with the attribution as its reason tag | ✓ | `AsyncLoopPage.tsx:104-111`, `:379-383`; `:38-40` |
| T34 | 灵感池 tabs | Press 灵感池 ({n}) then 待决定 ({n}) | Heading and kicker change; card sets change | | `AsyncLoopPage.tsx:143-150`, `:154-171` |
| T35 | 重新上架 | In the pool, press 重新上架 | Notice `已重新上架，观察窗重新计 7 天。`; the item moves back to the shelf | | `AsyncLoopPage.tsx:113-117`, `:194-200` |
| T36 | 永久删除 | In the pool, press 永久删除 → confirm the browser dialog | Notice `已永久删除。`; the item is gone after reload | | `AsyncLoopPage.tsx:119-123`, `:202-213` |
| T37 | Pool 问它 | In the pool, press 问它 | The companion opens with the chip `灵感池 · {title}` | | `AsyncLoopPage.tsx:214-220` |
| T38 | Empty shelf CTA | Pick up or discard everything, then open `/loop` | `架子上还没有待决定的内容。丢点素材，点「消化生产」。` plus 去收件箱丢素材 → | | `AsyncLoopPage.tsx:226-237` |
| T39 | Record weekly minutes | `/loop/inbox` → 记一笔本周维护时长 → enter 30 → 记下 | Notice `已记下本周维护时长。`; 30 appears in 证伪线度量 | | `InboxPage.tsx:222-260` |
| T40 | Minutes validation | Enter 0 or 700 | 记下 is disabled for 0; the value is clamped to 1..600 on submit | | `InboxPage.tsx:225-231` |
| T41 | Cancel minutes | Press 取消 | The input collapses and clears | | `InboxPage.tsx:239-248` |

### 7.4 急稿 `/urgent`

| # | Feature | Steps | Expected observable result | AI? | Citation |
|---|---|---|---|---|---|
| T42 | Submit guard | Fill only step 1 | 生成成品，进入发布检查 is disabled | | `UrgentPage.tsx:135` |
| T43 | Intent chips | Press 记过程 / 讲经历 / 教方法 / 让它判断 | The chosen chip highlights; 让它判断 deselects the others | | `UrgentPage.tsx:112-121` |
| T44 | Urgent with intent | Fill both fields, choose 教方法, submit | Lands on `/content/{id}`; the intent is confirmed; the experience is pre-filled as the key-question answer | ✓ | `UrgentPage.tsx:27-64` |
| T45 | Urgent with 让它判断 | Fill both fields, choose 让它判断, submit | Lands on `/content/{id}` with an unconfirmed intent, so 这篇要读者拿走什么？ is shown | ✓ | `UrgentPage.tsx:35-48` |
| T46 | Urgent abort | Press 存回收件箱，不急 | `/loop/inbox`; no project created | | `UrgentPage.tsx:140-142` |

### 7.5 内容项目 `/content`, `/content/:projectId`

| # | Feature | Steps | Expected observable result | AI? | Citation |
|---|---|---|---|---|---|
| T47 | Empty list | Open `/content` on a fresh account | Empty state with 开始起步实验 and 贴参考，读方向; 新建项目 is **not** rendered | | `ContentPage.tsx:301-321` |
| T48 | Start from free text | 新建项目 → type a sentence → 开始 | Button shows 正在理解…; then navigates to `/content/{id}` | ✓ | `ProjectStartPanel.tsx:85-98` |
| T49 | Start from inbox material | 新建项目 → press a material row (up to 3 shown) | Same navigation; the material becomes the project's source | ✓ | `ProjectStartPanel.tsx:43-45`, `:105-117` |
| T50 | Inference banner | After T48 with a model configured | Banner `我按「{label}」来准备这条` with a reason and 不对，我自己选 | ✓ | `ContentPage.tsx:413-438` |
| T51 | Dismiss inference | Press 不对，我自己选 | Banner disappears; `POST /projects/{id}:dismiss-inference` sent; the intent-confirmation step is shown | ✓ | `ContentPage.tsx:421-435` |
| T52 | Confirm intent | In 这篇要读者拿走什么？ fill 希望读者发生的变化, pick 处理方式 → 确认这个方向 | The panel advances; the outline's 处理方式 item becomes confirmed | ✓ | `ContentPage.tsx:763-787` |
| T53 | Evidence gate | When 这段真实经历可以用于这篇内容吗？ is shown, press 确认并准备候选内容 | A candidate is prepared; the next panel is either the segment review or the publication form | ✓ | `ContentPage.tsx:805-817` |
| T54 | Reject evidence | Same gate → 不使用这段经历 | The gate closes as rejected; the item is not used | | `ContentPage.tsx:818-829` |
| T55 | Answer guard | Leave 你的回答 with fewer than 10 characters | 让 AI 准备候选内容 is disabled | | `ContentPage.tsx:851` |
| T56 | Answer + prepare | Type ≥10 characters → 让 AI 准备候选内容 | The segment-review panel appears (or a prepare spinner first) | ✓ | `ContentPage.tsx:851` |
| T57 | Segment accept | Press 确认保留 on each `[data-testid="candidate-segment"][data-status="pending"]` | Each row flips to `data-status="accepted"` with the chip 已保留; the pending count decreases | ✓ | `ContentPage.tsx:1124`, `:1099` |
| T58 | Segment reject + replace | Press 拒绝这一段 on one segment | The chip reads 需替换; 替换这一段 appears | ✓ | `ContentPage.tsx:1125`, `:1104-1116` |
| T59 | Submit replacement | Type replacement text → 提交替换内容 | The chip reads 已替换; the segment no longer blocks the gate | ✓ | `ContentPage.tsx:1114` |
| T60 | All confirmed | Confirm every segment | `所有段落都已确认，可以进入发布前检查。` and 确认候选内容并进入发布准备 appears | ✓ | `ContentPage.tsx:1084-1086`, `:899` |
| T61 | Revision | Press 生成确认后的新版本 (when `can_prepare_revision`) | A new version is created and the review reloads | ✓ | `ContentPage.tsx:1145-1155` |
| T62 | Restore previous | Press 恢复上一版并重新确认 | The previous version becomes current again | | `ContentPage.tsx:1158-1170` |
| T63 | Reopen a segment | Press 重新修改这一段 | 确认保留 / 拒绝这一段 reappear for that segment | | `ContentPage.tsx:1120` |
| T64 | Lock hypothesis (solve) | Fill 读者遇到什么问题 + 你准备给出的答案 + 预期受众变化 + 主要反应 + 观察窗口 → 锁定发布意图 | Advances to the publication form; the section headings show 已确认 | ✓ | `StageForms.tsx:448-470`, `:591-631` |
| T65 | Lock guard | Clear the intent-required field | 锁定发布意图 stays disabled | | `StageForms.tsx:393-397`, `:594-598` |
| T66 | Lock window bounds | Set 观察窗口（天） to 0 or 400 | The button stays disabled | | `StageForms.tsx:596-597` |
| T67 | Legacy lock refusal | Open a legacy published project with no `content_intent` | `这条内容无法锁定发布前判断` with the explanation alert; no lock button | | `StageForms.tsx:402-414` |
| T68 | Retrospective classification | On legacy published content, fill 判断依据 → 确认回溯分类 | The banner/step advances; the publication intent stays empty | | `ContentPage.tsx:726-742` |
| T69 | Workspace edit + save | Change 当前内容标题 and 当前内容正文 → 保存修改 | The section meta flips 未保存 → 已保存; a new version is created | | `ProjectWorkspace.tsx:553`, `:573-581` |
| T70 | Offline draft | Go offline → edit the body → reload after going online | 当前离线，修改已保存在此设备 was shown while offline; 保存修改 disabled offline; after reload a `发现这篇内容尚未保存的本地草稿` alert with 恢复 / 丢弃 | | `ProjectWorkspace.tsx:513-528`; `frontend/e2e/intent-driven-loop.spec.ts:114-125` |
| T71 | Draft restore | Press 恢复 | The editor body equals the offline text | | `ProjectWorkspace.tsx:292-297`, `:518` |
| T72 | Draft discard | Press 丢弃 | The alert disappears and stays gone after a reload | | `ProjectWorkspace.tsx:299-302`, `:519` |
| T73 | Progress / tips strips | Press 进度 · n/5 步 and 参考与提醒 | Both toggle `aria-expanded` and show/hide their columns | | `ProjectWorkspace.tsx:433-450` |
| T74 | 项目素材 drawer | Press 项目素材 | Right drawer opens; 管理全部 → `/materials`; per-material 关联到当前项目 links it and then reads 已关联当前项目 | | `ContentPage.tsx:393-399`, `:608`, `:627-634` |
| T75 | 返回 / 刷新 | Press 返回内容列表, then reopen and press 刷新 | Back to `/content`; refresh re-fetches without losing the current step | | `ProjectWorkspace.tsx:392`, `:406-409` |
| T76 | Note-not-found path | Open `/content/{random-uuid}` | `未找到内容项目` with 重试 and 返回项目列表 | | `ContentPage.tsx:367-386` |

### 7.6 发布、检查、回填、复盘

| # | Feature | Steps | Expected observable result | AI? | Citation |
|---|---|---|---|---|---|
| T77 | Artifacts | In the publication form press 复制正文, 下载正文, 导出配图 PNG | Clipboard holds the body; a `.txt` download; a `.png` download | | `StageForms.tsx:771-802`, `:829-837` |
| T78 | Check states | Before running a check, read the chip | 正在读取检查结果… while loading, then 先运行发布前检查 when none exists | | `StageForms.tsx:844-852` |
| T79 | Run check | Press 运行检查 | Findings render with severity chip, 第 x–y 字, excerpt, reason, 规则来源 and 规则更新于; the chip reads 需要确认 while findings are open | ✓ | `StageForms.tsx:859-871` |
| T80 | Acknowledge findings | Press 我已了解 on every open finding | Each flips to 已确认/已解决; when none remain the chip reads 可以发布 | ✓ | `StageForms.tsx:868` |
| T81 | Stale check | Edit the version after a passing check, then return | The chip reads 检查已过期; 确认已发布 is disabled until 重新检查 | | `StageForms.tsx:845`, `:893` |
| T82 | Publish guard | Leave 发布时间 empty or clear the check | 确认已发布 is disabled | | `StageForms.tsx:893` |
| T83 | Publish | Fill 小红书笔记链接 + 发布时间 → 确认已发布 | Advances to the snapshot form; the project status becomes 已发布 | ✓ | `StageForms.tsx:890-924` |
| T84 | Snapshot by hand | Fill 数据时间 and some of 浏览/点赞/收藏/评论/分享/新增关注 → 保存数据快照 | Advances to blind review | | `StageForms.tsx:1075-1086`, `:1097-1138` |
| T85 | Snapshot guard | Leave every metric empty (or type a negative / fractional value) | 保存数据快照 is disabled | | `StageForms.tsx:975-979`, `:1100-1104` |
| T86 | Unavailable result | Tick 最终无法取得这次结果 → leave the reason blank, then fill it → 确认结果不可用 | The metric grid is replaced by the reason field; submit is disabled until the reason is non-blank; the saved snapshot records `result_availability='unavailable'` | | `StageForms.tsx:1028-1054`, `:1118-1120` |
| T87 | Screenshot path (vision on) | 选择数据截图 → 识别截图数据 | The proposal warning appears; the six metric fields are pre-filled; 我已逐项核对截图识别结果 must be ticked before saving | ✓ | `StageForms.tsx:1058-1093` |
| T88 | Screenshot path (vision off) | Same with `vision` unavailable | A user-facing error appears (422 `AI_CAPABILITY_MISSING`); manual entry still works | ✓ | `backend/app/services/snapshot_extraction.py:50-51` |
| T89 | Blind review | Press 查看这次结果 | `盲评结果` section with a calibration alert and per-claim comparison rows | | `StageForms.tsx:1169-1186`; `ReviewSummary.tsx:38-64` |
| T90 | Learning plan | In 确认下一轮只做一个实验, read the five sections | 这次实际看到的事实 / 仍然可能的原因 / 继续一项 / 停止一项 / 实验一项 all render | | `ContentPage.tsx:989-993` |
| T91 | Confirm learning | Press 确认并保存下一轮实验 | The 观察工作台 appears with the new observation | | `ContentPage.tsx:997-1008` |
| T92 | Reject learning | Press 暂不保存 | No learning is saved; the gate closes as rejected | | `ContentPage.tsx:1009-1020` |
| T93 | Unknown outcome | When the plan says 结果未知, pick a 下一步 → 确认未知结果和下一步 | The alert states that only the unknown outcome and the follow-up are recorded, never verified learning | | `ContentPage.tsx:938-973` |
| T94 | Observation form | Fill 这次看到了什么 + 下一次怎么验证 → 保存观察 | The observation appears in 观察工作台 as 观察中 | | `StageForms.tsx:1238-1257` |
| T95 | Observation transitions | Press 继续验证, then 证伪 on one observation and 归档 on another | Each transition lands and the status label changes; terminal observations lose all buttons | | `ObservationList.tsx:111-160`, `:74-76`, `:109` |
| T96 | 吸收 threshold | On a fresh 观察中 observation, press 吸收 | Disabled — only available once the observation is 待继续验证 | | `ObservationList.tsx:77`, `:131` |
| T97 | Rule candidate | Press 尝试形成经验候选, then 确认经验 / 拒绝 | The candidate appears as 待确认经验候选 with 来自 N 条可比较观察; confirming moves it to 当前使用的经验 | | `ObservationList.tsx:161-170`, `:244-259`, `:290-295` |
| T98 | Rule conflict resolution | With two conflicting rules, press 保留为例外, then 缩小适用范围 in a second conflict | 保留为例外 resolves it; 缩小适用范围 opens the dialog | | `ObservationList.tsx:262-289` |
| T99 | Narrow-scope dialog | Fill one of 实验或内容主题 / 适用受众 / 适用形式 → 保存范围并应用 | The dialog closes and the rule scope is narrowed; 取消 closes without change | | `ObservationList.tsx:308-346` |
| T100 | Rule rollback | Press 回滚到版本 {n} on a rule with retired versions | The active version changes to the chosen historical version | | `ObservationList.tsx:296-304` |
| T101 | Viewpoint propose | After confirming the intent, press 提炼候选 | A 观点候选 card appears with an editable statement | ✓ | `ViewpointPanel.tsx:64-74`, `:84-127` |
| T102 | Viewpoint block | Before confirming the intent, read the panel | `先确认这条内容的处理方式，才能提炼观点候选。` and 提炼候选 disabled | | `ProjectWorkspace.tsx:675-677` |
| T103 | Viewpoint decide | Edit the text → 确认是我的观点; then 撤销观点 | It moves to 已确认, then is revoked | ✓ | `ViewpointPanel.tsx:101-111`, `:136-144` |
| T104 | Series propose | With ≥2 eligible projects ticked, press 发现系列 | A 已确认系列 / AI 候选 card appears | ✓ | `SeriesPanel.tsx:169-177`, `:198-263` |
| T105 | Series confirm | Edit 系列名称 / 系列共同价值 / 下一篇延展方向 → 确认这个系列 | It becomes 已确认系列 with 成员处理方式 and 成员格式 lines | ✓ | `SeriesPanel.tsx:240-251`, `:305-314` |
| T106 | Series extension | Press 准备下一篇 → edit the next-episode fields → 确认并创建项目 → 打开下一篇项目 | A new project opens in the workspace | ✓ | `SeriesPanel.tsx:403-411`, `:364-377`, `:391-399` |
| T107 | Series revoke | Press 撤销系列 | The series leaves the confirmed list | | `SeriesPanel.tsx:413-421` |
| T108 | 写作提醒 empty | Read the right column | `现在没有需要提醒你的事情。` — the suggestion list is always empty in the shipped build (see A10) | | `ProjectWorkspace.tsx:317`, `:699` |

### 7.7 周复盘 / 成长 / 机会 / 素材 / 我的

| # | Feature | Steps | Expected observable result | AI? | Citation |
|---|---|---|---|---|---|
| T109 | Weekly rows | Open `/loop/review` with a published project | One row per project with 判断 · {label} ｜ 实际 · {metrics}, the stage pill set, and 问 | | `ReviewPage.tsx:57-91` |
| T110 | Weekly unavailable | Open a row whose result was marked unavailable | 实际 · 截图缺失 (never 0) | | `ReviewPage.tsx:72-73` |
| T111 | Weekly empty | Open `/loop/review` with nothing published | `本周期还没有已发布的内容。发布并回填数据后，这里会出现对照行。` | | `ReviewPage.tsx:55` |
| T112 | Weekly deep link | Press a row title, then 去项目工作台确认 | Both reach the right project / the content list; the page itself has no confirm control | | `ReviewPage.tsx:61`, `:96` |
| T113 | Weekly companion | Press 问 on a row | Companion opens with `周复盘 · {title}` | | `ReviewPage.tsx:87` |
| T114 | Growth counters | Open `/growth` | Four capability rows + 今日 AI 调用, all from real data | | `GrowthPage.tsx:26-31`, `:68-78` |
| T115 | Growth milestones | Read 成对里程碑 | Two paired milestones and the 待达成 note | | `GrowthPage.tsx:83-94` |
| T116 | Growth trust switches | Press all three switches | 自主准备 and 探索位 print 该能力将随后续版本开放，当前为展示状态。; 私密素材参与生产 does nothing (no handler) — record as display-only, not a failure | | `GrowthPage.tsx:99-119` |
| T117 | Opportunity generate | `/opportunities` → 生成内容机会 | Either `生成了 N 条新机会…` with rows, or the explanatory zero-result notice | ✓ | `OpportunitiesPage.tsx:304-322` |
| T118 | Status filters | Press 全部 / 待确认 / 已收藏 / 已采用 / 已放弃 | The visible list changes; the pressed filter is `contained` | | `OpportunitiesPage.tsx:363-365` |
| T119 | Source + timeliness filters | Change 来源类型筛选 and 时效筛选 | The list narrows; the two selects are collapsed behind 筛选 at ≤600px | | `OpportunitiesPage.tsx:370-410` |
| T120 | Manual source | Press 手动添加来源 → fill 关键词或原始内容 → 保存并等待核验 | The new row appears with the 待核验 chip and the verification form | | `OpportunitiesPage.tsx:323-347`, `:414-427` |
| T121 | Verify source | Fill 原始链接 / 发布时间 / 权威来源 / 当前时效 → 确认来源信息 | The chip changes and the adoption form appears | | `OpportunitiesPage.tsx:229`, `:235-249` |
| T122 | Insufficient source | Press 标记来源不足 | The chip reads 来源不足 and the warning alert switches copy | | `OpportunitiesPage.tsx:230`, `:212-214` |
| T123 | Adopt opportunity | Fill 这篇内容的标题 + 希望读者看完发生什么变化 (+ 需要的真实素材) → 采用并创建内容 → 继续这条内容 | The project is created and opens; the opportunity chip reads 已采用 | ✓ | `OpportunitiesPage.tsx:244`, `:250-254` |
| T124 | Adopt guards | Clear the title or the audience change | 采用并创建内容 is disabled | | `OpportunitiesPage.tsx:244` |
| T125 | Reject / save | Press 这次不做, then on another row 稍后再做 | The first flips to 已放弃, the second to 已收藏 | | `OpportunitiesPage.tsx:245-246` |
| T126 | Unsafe source URL | Create an opportunity whose `source_url` is `javascript:alert(1)` | It renders as inert text ending in `（不可信链接，已禁用跳转）`; nothing executes | | `OpportunitiesPage.tsx:59-73` |
| T127 | Add material (text) | `/materials` → 添加素材 → 素材类型 文字 → 素材标题 + 素材内容 → 隐私级别 私密 → 保存素材 | Notice `素材已保存。`; the card renders with the 私密 chip | | `MaterialsPage.tsx:100-134`, `:211-231` |
| T128 | Add material (image) | 素材类型 图片 → 选择文件 → pick a PNG → 保存素材 | The card renders with the size in KB | | `MaterialsPage.tsx:102-105`, `:216-219`, `:244` |
| T129 | Image guard | 素材类型 图片 with no file → 保存素材 | Inline error `请先选择要上传的文件`; 保存素材 disabled | | `MaterialsPage.tsx:101-105`, `:231` |
| T130 | Link material | 素材类型 链接 → fill a URL as 素材内容 → 保存素材 | Saved; the content is rendered as text | | `MaterialsPage.tsx:221` |
| T131 | Link material to project | On a material card pick 复用到项目 → 关联 | Notice `素材已关联到所选项目。`; 正在用于：{project} appears; the select resets | | `MaterialsPage.tsx:136-162`, `:291` |
| T132 | 关联 guard | Leave 复用到项目 as 选择项目 | 关联 is disabled | | `MaterialsPage.tsx:291` |
| T133 | Delete unreferenced | Press 删除 on a material not used by any locked version | Notice `素材已删除。`; the card disappears | | `MaterialsPage.tsx:164-181`, `:301` |
| T134 | Delete referenced | Press 删除 on a material used by a locked version | The warning alert `将影响：{projects}` with 保留引用快照并删除 and 取消 | | `MaterialsPage.tsx:265-278` |
| T135 | Keep snapshot and delete | Press 保留引用快照并删除 | The material is deleted; the project keeps its reference | | `MaterialsPage.tsx:270` |
| T136 | Cancel delete impact | Press 取消 in the impact alert | The alert disappears and the material remains | | `MaterialsPage.tsx:272` |
| T137 | Analyze media (configured) | On an audio/video card press 识别内容 | Notice `识别完成：文字已写进这条素材，可以在项目里引用它。`; the card then shows the model-provenance sentence | ✓ | `MaterialsPage.tsx:183-196`, `:249-254` |
| T138 | Analyze media (sensitive) | Set 隐私级别 敏感 on an audio/video material, then 识别内容 | The refusal message from the backend, no external call | ✓ | `backend/app/services/material_analysis.py:62-66` |
| T139 | Analyze media (unconfigured) | Same as T137 with no omni model configured | A readable refusal message, not a 500 | ✓ | `backend/app/services/material_analysis.py:77-78` |
| T140 | Settings round-trip | `/me` → set 每周发布目标 3, 内容策略 text, 小红书账号备注, toggle 每晚自动整理收件箱 → 保存设置 | Notice `设置已保存`; reload restores all four values | | `MePage.tsx:149-164`, `:220-232` |
| T141 | Settings guards | Clear 每周发布目标 or 内容策略 | 保存设置 is disabled | | `MePage.tsx:81`, `:232` |
| T142 | Export data | 导出个人数据 → 确认并下载 | A `topicai-account-data-{YYYY-MM-DD}.json` download; notice `个人数据已导出`; the gate alert closes | | `MePage.tsx:166-180`, `:302` |
| T143 | Export gate guard | After opening the export gate, look at 导出个人数据 | Disabled while the gate is open | | `MePage.tsx:311` |
| T144 | Deletion guard | 删除账户 → leave 删除确认 blank | 永久删除账户 is disabled | | `MePage.tsx:307` |
| T145 | Deletion typed phrase | Type `永久删除` (exact) → 永久删除账户 | `DELETE /account` returns 202; logout; redirect to `/login`; the old credentials no longer work | | `MePage.tsx:189-200`, `:303-313` |
| T146 | Deletion wrong phrase | Type `永久删除 ` (trailing space) or a different phrase | The button stays disabled | | `MePage.tsx:190`, `:307` |
| T147 | Me shortcuts | Press 导入历史内容并校对画像, 贴参考，读出你想做成什么样, 查看内容项目 | `/onboarding/growth`, `/onboarding/reference`, `/content` | | `MePage.tsx:316-318` |
| T148 | AI capability card | Read the AI 能力状态 section with the model unconfigured | Chip 不可用, the explanation sentence about admin configuration, and 文本能力/截图识别 both 不可用 | ✓ | `MePage.tsx:267-277` |

### 7.8 引导 paths

| # | Feature | Steps | Expected observable result | AI? | Citation |
|---|---|---|---|---|---|
| T149 | Starter assessment guard | `/onboarding/assessment` → fill only 每周可投入小时 | 保存并继续 disabled and the `至少填写一条…` info alert shows | | `StarterPage.tsx:191-196` |
| T150 | Starter assessment | Fill hours + at least one asset line + both checkboxes → 保存并继续 | Notice `评估已保存，接下来可以生成实验方向。`; the step advances | ✓ | `StarterPage.tsx:196-220` |
| T151 | Starter directions | Press 查看候选方向 | `选择一条先做 14 天` with exactly three candidate articles, each listing three first topics | ✓ | `StarterPage.tsx:236-244`, `:261-277` |
| T152 | Starter sprint | Press 选择并创建三篇实验 | `完成三篇内容实验` with `0 / 3 已发布` and three project rows | ✓ | `StarterPage.tsx:267-275`, `:291-297` |
| T153 | Starter sprint review | Publish one project, return, fill the three review fields → 完成本轮复盘 | `本轮实验已完成` alert with the review summary | ✓ | `StarterPage.tsx:311-325`, `:299-301` |
| T154 | Sprint review guard | Leave 这轮实际发生了什么 with fewer than 5 characters | 完成本轮复盘 disabled; the info alert explains the ≥1 publication requirement | | `StarterPage.tsx:311`, `:327` |
| T155 | Starter route aliasing | Open all three of `/onboarding/assessment`, `/onboarding/directions`, `/onboarding/sprint` for the same account | All three render the **same** server-determined step (A2) | | `StarterPage.tsx:124-130` |
| T156 | Growth mode switch | `/onboarding/growth` on an account not yet in growth mode → 使用历史内容开始 | The import section appears; `GET /onboarding` now reports `mode: growth` | | `GrowthOnboardingPage.tsx:155-162` |
| T157 | History import (manual) | Method 手动 → paste three titles → 导入历史内容 | `成功 3 条，失败 0 条` with a per-item list | | `GrowthOnboardingPage.tsx:109-120`, `:181-192` |
| T158 | History import (CSV) | Method CSV → paste a header row + one row | Imported; a CSV with only a header throws `CSV 需要表头和至少一条内容` | | `GrowthOnboardingPage.tsx:276-289` |
| T159 | History import (JSON) | Method JSON → paste `[{"title":"x"}]` | Imported; a non-array payload throws `JSON 必须是内容数组` | | `GrowthOnboardingPage.tsx:271-274` |
| T160 | Empty import | Press 导入历史内容 with an empty textarea | Error `请至少提供一条历史内容` | | `GrowthOnboardingPage.tsx:110-111` |
| T161 | Profile provisional | Import fewer than 10 notes, then read the 校对创作画像 header | Chip 资料不足，暂定 plus the info alert | | `GrowthOnboardingPage.tsx:200-202` |
| T162 | Profile confirm guard | Clear 创作方向, 目标读者 or 内容支柱 | 确认画像并继续 disabled | | `GrowthOnboardingPage.tsx:234` |
| T163 | Profile confirm | Fill all three → 确认画像并继续 | Redirect to `/`; `GET /creator-profile` reports `confirmation_state: confirmed` | | `GrowthOnboardingPage.tsx:122-147` |
| T164 | Reference parse echo | `/onboarding/reference` → paste one block without a source line | `第 1 条没写来源（在第一行加 @账号名）`; 读这些参考 disabled | | `ReferenceAnchorPage.tsx:233-244`; `parseReferences.ts:52` |
| T165 | Reference parse count | Paste two valid blocks | `已识别 2 条参考` with one chip per block and the count hint | | `ReferenceAnchorPage.tsx:217-231`; `parseReferences.ts:65-68` |
| T166 | Reference read (model on) | Press 读这些参考 | `正在读这 N 条参考…`, then the three conclusion blocks with the 读懂了内容 chip | ✓ | `ReferenceAnchorPage.tsx:88-120`, `:190-200` |
| T167 | Reference read (model off) | Same with no model | 只数了标签，没读懂内容 chip; topics from tags; the audience block replaced by the explicit 需要你自己定 empty state; limitation list rendered | ✓ | `ReferenceAnchorPage.tsx:257`, `:285-296` |
| T168 | Reject a conclusion | Press 不对 on one item | The item disappears and does not return after a reload | ✓ | `ReferenceAnchorPage.tsx:141-144`, `:384-392` |
| T169 | Manual rewrite | Press 都不对？我自己写 → edit the three fields → 以我说的为准 | The chip reads 以你说的为准; a later reference read does not overwrite it | | `ReferenceAnchorPage.tsx:146-163`, `:332-334` |
| T170 | Add more references | Press 再贴几条 → paste a third block → 读这些参考 | `reference_count` increases and the read reruns | ✓ | `ReferenceAnchorPage.tsx:302` |
| T171 | Anchor exit | Press 开始写第一条内容 | `/content` | | `ReferenceAnchorPage.tsx:344-346` |

### 7.9 Companion, shell and negative cases

| # | Feature | Steps | Expected observable result | AI? | Citation |
|---|---|---|---|---|---|
| T172 | Companion open/close | Press the 对话悬浮球, then 关闭 | Panel opens with the entrance animation (first time only per `sessionStorage`), then closes cleanly | | `CompanionDialog.tsx:169-193`, `:233-235` |
| T173 | Companion ask (model on) | Type a question → ↑ | A real answer bubble appears; the input clears | ✓ | `CompanionDialog.tsx:139-159`, `:268` |
| T174 | Companion ask (model off) | Same with no model | The reply bubble contains an error message, never a canned answer | ✓ | `CompanionDialog.tsx:154-157` |
| T175 | Companion zen | Press 渐隐, then 唤醒 | Chrome fades then returns; the label flips | | `CompanionDialog.tsx:230-232` |
| T176 | Companion context injection | Press 问它 on a shelf card, then 问 on a weekly row | The context chip reads `产出架 · {title}` then `周复盘 · {title}` | | `AsyncLoopPage.tsx:365`; `ReviewPage.tsx:87` |
| T177 | Companion demo messages | Open the companion and wait 15s | Two messages appear, each ending in `（演示）` — these are **static**, not model output | | `CompanionDialog.tsx:127-137` |
| T178 | Mobile layout | At 390×844, visit every route | No horizontal overflow; the companion ball does not cover the bottom bar or a card's discard buttons | | `frontend/e2e/intent-driven-loop.spec.ts:22-28`, `:164-224` |
| T179 | Legacy API absent | `curl -i /api/v1/projects` | 404 with no redirect | | `specs/008-content-project-mvp/spec.md:193` |
| T180 | Health | `curl /api/v2/health` without a token | `{"status":"ok","api_version":"v2","product":"content_project"}` | | `router.py:50-58` |
| T181 | Auth required | `curl /api/v2/projects` without a token | 401 | | `app/api/deps.py:6` |
| T182 | Rate limit | POST `/api/v2/auth/login` >N times in a minute from one IP | 429 with `meta.error_code = AUTH_RATE_LIMIT_EXCEEDED` | | `app/middleware/rate_limit.py:10-14` |
| T183 | Idempotency replay | Repeat any 201-declaring POST with the same `idempotency_key` | 200 with `meta.idempotency_replayed = true`, and no duplicate row | | §4.3 |
| T184 | Auth-expiry handling | Delete `access_token` from `localStorage` but keep `refresh_token`, then interact | The token refreshes transparently, or the user is dropped to `/login` — never a stuck shell | | `authStore.ts:103-136` |
| T185 | Whole flow with no model | Unset `LLM_*`, restart, and run T22→T95 end to end | Every step reachable; no dead ends; every AI-derived artifact is visibly labelled as a deterministic fallback; nothing claims model authorship | ✓ | `specs/013-async-creation-loop/spec.md:29`; `specs/008-content-project-mvp/quickstart.md:76-97` |

### 7.10 The 10 journeys a tester must run first

If time is limited, these give the broadest coverage per minute:

1. **T01–T03, T06–T09** — auth, nav, guard, 404 (the shell everything else sits on).
2. **T22–T26** — inbox capture, consent, digest, precheck gate.
3. **T27–T33** — shelf review, pickup, the pickup hand-off into the workspace, discard-to-pool.
4. **T47–T63** — start a piece, intent confirmation, answer, segment-by-segment candidate
   confirmation.
5. **T64–T72, T77–T84** — lock the publish judgment, publish check + acknowledgement, record
   publication, back-fill data.
6. **T89–T100** — blind review, learning confirmation, observation transitions, rule candidate.
7. **T42–T46** — 急稿 end to end.
8. **T109–T113** — 周复盘 rows, stage pills, deep link.
9. **T117–T126** — 机会 generate, filter, manual source, verify, adopt.
10. **T140–T146, T164–T171** — 我的 settings/export/delete plus the reference-anchor read and
    override.

### 7.11 Ambiguities that can change expected results (resolve before the run)

| # | Ambiguity | Where it bites | Evidence |
|---|---|---|---|
| A1 | Guard flips after first paint when the stored token is stale | T08 | `authStore.ts:41` vs `App.tsx:38-49` |
| A2 | The three `/onboarding/*` starter URLs are aliases; the URL does not select the step | T149–T155 | `StarterPage.tsx:124-130` |
| A3 | No forgot-password path exists | T01–T03 | `LoginPage.tsx` (no such control) |
| A4 | Sidebar claims `AI 正常 · 本地编排` unconditionally | T148, T185 | `Sidebar.tsx:153` |
| A5 | 404 is reachable while logged out | T09 | `App.tsx:82-84` |
| A6 | Three growth-page trust switches are display-only | T116 | `GrowthPage.tsx:99-119` |
| A7 | Starter step selection is server-driven | T149–T155 | as A2 |
| A8 | `ProjectCreateForm` is dead code (7 controls, unreachable) | not testable via UI | `StageForms.tsx:163`; no importer |
| A9 | Weekly-review window is 60 days in the UI vs 7 days in the docs/API default | T109, T111 | `ReviewPage.tsx:32` vs `async_loop.py:148` |
| A10 | The 写作提醒 column can never contain a suggestion (dead push sites) | T108 | `ProjectWorkspace.tsx:317`, `:331-354`, `:699` |
| A11 | Weekly publish goal accepted as 1–7 in the UI vs 1–4 in the docs | T140 | `MePage.tsx:220` vs `CONTEXT.md:50-53` |
| A12 | Companion zen fade is 12s in code vs 8s in a handoff doc | T175 | `CompanionDialog.tsx:23` vs `docs/handoffs/topicai-handoff-2026-09-02-lumen-visual-acceptance.md:68` |
| A13 | Free-form companion chat shipped despite "no free dialogue in v1" in the plan | T173 | `companion.py:25` vs `docs/ai-native-async-creation-plan-2026-08-29.md:25` |
| A14 | `specs/013` excludes the weekly-review batch UI and the urgent front end, both of which shipped | T42–T46, T109–T113 | `specs/013-async-creation-loop/spec.md:24` |
| A15 | The three Playwright specs still assert some pre-rename UI copy (e.g. 「让 AI 对照发布前判断和真实结果」 at `frontend/e2e/intent-driven-loop.spec.ts:146` vs the shipped 「对照你发布前的判断和实际结果」 at `ProjectWorkspace.tsx:149`; 「发布后，把笔记链接留在这里」 at `:105` vs 「告诉我们你已经发布」 at `StageForms.tsx:807`) | any run that reuses the E2E text selectors | cited lines |
| A16 | `docs/product-introduction-user.md` and `docs/product-functional-document.md` describe a v4.1 multi-platform product that this codebase explicitly forbids | journey derivation | `README.md:96-103`; `specs/008-content-project-mvp/spec.md:169-193` |
| A17 | `POST /projects/{id}/interview:generate` appears in the spec-008 contract but is not implemented | any API-level test copied from the contract | `specs/008-content-project-mvp/contracts/api-v2.md:36-37` vs §4.19 |
| A18 | `data_source` does not exist as a field name anywhere | any test asserting on a `data_source` value | grep of `backend/app` + `frontend/src` returns zero matches |

---

## 8. Confidence and method notes

- **Read directly and cited line-by-line** by the author of this report: `frontend/src/App.tsx`,
  all 15 files under `frontend/src/pages/**`, all files under `frontend/src/features/**`,
  `frontend/src/components/**`, `frontend/src/store/authStore.ts`,
  `frontend/src/services/api/**`, `frontend/e2e/*.spec.ts`, `backend/app/api/v2/router.py`,
  `backend/app/core/llm.py`, `backend/app/core/exceptions.py`, and the AI-relevant regions of
  `backend/app/services/{async_loop,companion,field_suggestions,project_start,snapshot_extraction,
  material_analysis,publish_check,direction_candidate,content_opportunity,creator_viewpoints,
  creator_series,intent_actions,intent_orchestrator,reference_anchor}.py`.
- **Backend endpoint inventory** was produced by regex enumeration over all 22 `.py` files in
  `backend/app/api/v2/` and **independently re-verified**: per-module counts and the
  method split (POST 66 / GET 33 / PUT 6 / DELETE 4 / PATCH 1 = 110) match an independent
  recount. Every `file:line` in §4 is the decorator line.
- **Journeys** come from the project's own docs plus the three Playwright specs; every
  code-level claim they make about implemented behaviour was spot-checked against the source
  (pickup hand-off at `async_loop.py:616-745`, the weekly window at `ReviewPage.tsx:32`, the
  missing `interview` endpoints, the missing `data_source` field, the absent `specs/013`
  `plan.md`/`quickstart.md`/`contracts/`).
- **Interactive-control counts** count a control once even when rendered N times in a list;
  the multiplicity is stated per row. They are derived from reading the JSX, so a control that
  exists only in a branch that is never reached at runtime is still counted (for example the
  seven `ProjectCreateForm` controls, which are unreachable — A8).
- **Not verified by running anything.** No server was started, no test suite was executed, and
  no browser session was driven. Every "expected observable result" above is derived from
  reading code and docs, not from observation. Where the docs contradict the code, the
  contradiction is recorded rather than resolved.


