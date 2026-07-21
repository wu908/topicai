/**
 * Root component with React Router configuration.
 * 12 protected routes (9 V3 sidebar tabs + 3 legacy /tracks /profile /review)
 * + 1 public login route + 1 legacy /ideas alias + 1 catch-all 404 route.
 */
import React, { Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, CssBaseline } from '@mui/material';
import theme from '@/styles/theme';
import AppLayout from '@/components/layout/AppLayout';
import ErrorBoundary from '@/components/common/ErrorBoundary';
import LoadingFallback from '@/components/common/LoadingFallback';
import { useAuthStore } from '@/store/authStore';

// Lazy loaded pages
const LoginPage = React.lazy(() => import('@/pages/Login/LoginPage'));
const HomePage = React.lazy(() => import('@/pages/Home/HomePage'));
const TopicRecommendPage = React.lazy(() => import('@/pages/TopicRecommend/TopicRecommendPage'));
const ViralAnalysisPage = React.lazy(() => import('@/pages/ViralAnalysis/ViralAnalysisPage'));
const WritingPage = React.lazy(() => import('@/pages/Writing/WritingPage'));
const TitleOptimizerPage = React.lazy(() => import('@/pages/TitleOptimizer/TitleOptimizerPage'));
const TrackDiagnosisPage = React.lazy(() => import('@/pages/TrackDiagnosis/TrackDiagnosisPage'));
const CreatorProfilePage = React.lazy(() => import('@/pages/CreatorProfile/CreatorProfilePage'));
const EffectReviewPage = React.lazy(() => import('@/pages/EffectReview/EffectReviewPage'));
const PublishAdvisorPage = React.lazy(() => import('@/pages/PublishAdvisor/PublishAdvisorPage'));
const AnalyticsPage = React.lazy(() => import('@/pages/Analytics/AnalyticsPage'));
const AssetsPage = React.lazy(() => import('@/pages/Assets/AssetsPage'));
const AccountsPage = React.lazy(() => import('@/pages/Accounts/AccountsPage'));
const ContentPage = React.lazy(() => import('@/pages/Content/ContentPage'));
const NotFoundPage = React.lazy(() => import('@/pages/NotFound/NotFoundPage'));

/** Wraps children in Suspense with a loading fallback */
const LazyRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <Suspense fallback={<LoadingFallback />}>{children}</Suspense>
);

/** Protected route wrapper — redirects to login if not authenticated */
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const user = useAuthStore((s) => s.user);
  const fetchCurrentUser = useAuthStore((s) => s.fetchCurrentUser);

  React.useEffect(() => {
    if (isAuthenticated && !user) {
      fetchCurrentUser().catch(() => {});
    }
  }, [isAuthenticated, user, fetchCurrentUser]);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return <AppLayout>{children}</AppLayout>;
};

const App: React.FC = () => {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <ErrorBoundary>
        <BrowserRouter>
          <Routes>
            {/* Public routes */}
            <Route
              path="/login"
              element={
                <LazyRoute>
                  <LoginPage />
                </LazyRoute>
              }
            />

            {/* Protected routes — 9 V3 sidebar tabs */}
            <Route
              path="/"
              element={
                <LazyRoute>
                  <ProtectedRoute>
                    <HomePage />
                  </ProtectedRoute>
                </LazyRoute>
              }
            />
            <Route
              path="/content"
              element={
                <LazyRoute>
                  <ProtectedRoute>
                    <ContentPage />
                  </ProtectedRoute>
                </LazyRoute>
              }
            />
            <Route
              path="/content/:projectId"
              element={
                <LazyRoute>
                  <ProtectedRoute>
                    <ContentPage />
                  </ProtectedRoute>
                </LazyRoute>
              }
            />
            <Route
              path="/topics"
              element={
                <LazyRoute>
                  <ProtectedRoute>
                    <TopicRecommendPage />
                  </ProtectedRoute>
                </LazyRoute>
              }
            />
            <Route
              path="/writing"
              element={
                <LazyRoute>
                  <ProtectedRoute>
                    <WritingPage />
                  </ProtectedRoute>
                </LazyRoute>
              }
            />
            {/* Legacy alias — /ideas redirects to /writing (kept under ProtectedRoute for consistent auth contract) */}
            <Route
              path="/ideas"
              element={
                <LazyRoute>
                  <ProtectedRoute>
                    <Navigate to="/writing" replace />
                  </ProtectedRoute>
                </LazyRoute>
              }
            />
            <Route
              path="/titles"
              element={
                <LazyRoute>
                  <ProtectedRoute>
                    <TitleOptimizerPage />
                  </ProtectedRoute>
                </LazyRoute>
              }
            />
            <Route
              path="/viral"
              element={
                <LazyRoute>
                  <ProtectedRoute>
                    <ViralAnalysisPage />
                  </ProtectedRoute>
                </LazyRoute>
              }
            />
            <Route
              path="/publish"
              element={
                <LazyRoute>
                  <ProtectedRoute>
                    <PublishAdvisorPage />
                  </ProtectedRoute>
                </LazyRoute>
              }
            />
            <Route
              path="/analytics"
              element={
                <LazyRoute>
                  <ProtectedRoute>
                    <AnalyticsPage />
                  </ProtectedRoute>
                </LazyRoute>
              }
            />
            <Route
              path="/assets"
              element={
                <LazyRoute>
                  <ProtectedRoute>
                    <AssetsPage />
                  </ProtectedRoute>
                </LazyRoute>
              }
            />
            <Route
              path="/accounts"
              element={
                <LazyRoute>
                  <ProtectedRoute>
                    <AccountsPage />
                  </ProtectedRoute>
                </LazyRoute>
              }
            />
            <Route
              path="/tracks"
              element={
                <LazyRoute>
                  <ProtectedRoute>
                    <TrackDiagnosisPage />
                  </ProtectedRoute>
                </LazyRoute>
              }
            />
            <Route
              path="/profile"
              element={
                <LazyRoute>
                  <ProtectedRoute>
                    <CreatorProfilePage />
                  </ProtectedRoute>
                </LazyRoute>
              }
            />
            <Route
              path="/review"
              element={
                <LazyRoute>
                  <ProtectedRoute>
                    <EffectReviewPage />
                  </ProtectedRoute>
                </LazyRoute>
              }
            />

            {/* 404 fallback */}
            <Route
              path="*"
              element={
                <LazyRoute>
                  <ProtectedRoute>
                    <NotFoundPage />
                  </ProtectedRoute>
                </LazyRoute>
              }
            />
          </Routes>
        </BrowserRouter>
      </ErrorBoundary>
    </ThemeProvider>
  );
};

export default App;
