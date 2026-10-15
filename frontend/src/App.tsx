/** Root router for the five-node intent-driven product. */
import React, { Suspense } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { CssBaseline, ThemeProvider } from '@mui/material';
import AppLayout from '@/components/layout/AppLayout';
import ErrorBoundary from '@/components/common/ErrorBoundary';
import LumenBackground from '@/components/common/LumenBackground';
import LoadingFallback from '@/components/common/LoadingFallback';
import { useAuthStore } from '@/store/authStore';
import theme from '@/styles/theme';

const LoginPage = React.lazy(() => import('@/pages/Login/LoginPage'));
const HomePage = React.lazy(() => import('@/pages/Home/HomePage'));
const ContentPage = React.lazy(() => import('@/pages/Content/ContentPage'));
const PathPage = React.lazy(() => import('@/pages/Path/PathPage'));
const SettingsPage = React.lazy(() => import('@/pages/Settings/SettingsPage'));
const OpportunitiesPage = React.lazy(() => import('@/pages/Opportunities/OpportunitiesPage'));
const MaterialsPage = React.lazy(() => import('@/pages/Materials/MaterialsPage'));
const ReviewPage = React.lazy(() => import('@/pages/Review/ReviewPage'));
const GrowthPage = React.lazy(() => import('@/pages/Growth/GrowthPage'));
const MePage = React.lazy(() => import('@/pages/Me/MePage'));
const GrowthOnboardingPage = React.lazy(() => import('@/pages/GrowthOnboarding/GrowthOnboardingPage'));
const ReferenceAnchorPage = React.lazy(() => import('@/pages/Onboarding/ReferenceAnchorPage'));
const NotFoundPage = React.lazy(() => import('@/pages/NotFound/NotFoundPage'));

/** P0 导航收敛：旧一级入口重定向到新六入口对应处，功能不丢。 */
const Redirect = ({ to }: { to: string }) => <Navigate to={to} replace />;

const LazyRoute = ({ children }: { children: React.ReactNode }) => (
  <Suspense fallback={<LoadingFallback />}>{children}</Suspense>
);

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const isLoading = useAuthStore((state) => state.isLoading);
  const user = useAuthStore((state) => state.user);
  const fetchCurrentUser = useAuthStore((state) => state.fetchCurrentUser);

  React.useEffect(() => {
    if (isAuthenticated && !user) void Promise.resolve(fetchCurrentUser()).catch(() => undefined);
  }, [fetchCurrentUser, isAuthenticated, user]);

  // Wait for the initial session hydration before deciding — otherwise a
  // verified user flashes the login redirect / empty shell for a moment.
  // Gate only while there is no user yet: once a session exists, pages like
  // HomePage re-run fetchCurrentUser on every mount, and blanking the whole
  // layout on isLoading would unmount the page and re-trigger the fetch in
  // an endless remount loop.
  if (isLoading && !user) return <LoadingFallback />;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <AppLayout>{children}</AppLayout>;
};

// Suspense 必须在 AppLayout 之内：包在外面的话，懒加载 chunk 的几秒里
// 侧栏与布局会被整页 spinner 顶掉（用户验收 F5「外壳闪断」）。
const protectedPage = (page: React.ReactNode) => (
  <ProtectedRoute>
    <LazyRoute>{page}</LazyRoute>
  </ProtectedRoute>
);

export default function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <LumenBackground />
      <ErrorBoundary>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LazyRoute><LoginPage /></LazyRoute>} />
            <Route path="/" element={protectedPage(<HomePage />)} />
            <Route path="/content" element={protectedPage(<ContentPage />)} />
            <Route path="/content/:projectId" element={protectedPage(<ContentPage />)} />
            <Route path="/review" element={protectedPage(<ReviewPage />)} />
            <Route path="/path" element={protectedPage(<PathPage />)} />
            <Route path="/settings" element={protectedPage(<SettingsPage />)} />
            <Route path="/settings/:section" element={protectedPage(<SettingsPage />)} />
            <Route path="/materials" element={protectedPage(<MaterialsPage />)} />
            <Route path="/me" element={protectedPage(<MePage />)} />
            {/* 旧入口收容（方案 §4.3）：功能已迁，路由重定向，不再挂独立页。
                急稿 → 今日快速开始；产出架 → 内容；收件箱 → 素材；
                starter 三步/历史校准 → 路径设定；对标锚保留（路径深链）。 */}
            <Route path="/loop" element={protectedPage(<Redirect to="/content" />)} />
            <Route path="/loop/inbox" element={protectedPage(<Redirect to="/materials" />)} />
            <Route path="/loop/review" element={protectedPage(<Redirect to="/review" />)} />
            <Route path="/urgent" element={protectedPage(<Redirect to="/" />)} />
            <Route path="/opportunities" element={protectedPage(<OpportunitiesPage />)} />
            <Route path="/growth" element={protectedPage(<GrowthPage />)} />
            <Route path="/onboarding/assessment" element={protectedPage(<Redirect to="/path" />)} />
            <Route path="/onboarding/directions" element={protectedPage(<Redirect to="/path" />)} />
            <Route path="/onboarding/sprint" element={protectedPage(<Redirect to="/path" />)} />
            {/* 历史校准：方案「保留·改」，作为路径的锚点入口 */}
            <Route path="/onboarding/growth" element={protectedPage(<GrowthOnboardingPage />)} />
            <Route path="/onboarding/reference" element={protectedPage(<ReferenceAnchorPage />)} />
            {/* 404 stays outside the auth guard: unknown paths should show
                the not-found page, not redirect unauthenticated visitors. */}
            <Route path="*" element={<LazyRoute><NotFoundPage /></LazyRoute>} />
          </Routes>
        </BrowserRouter>
      </ErrorBoundary>
    </ThemeProvider>
  );
}
