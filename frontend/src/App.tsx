/**
 * Root component with React Router configuration.
 * All 10 pages are routed here using React.lazy() for code splitting.
 */
import React, { Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, CssBaseline } from '@mui/material';
import theme from '@/styles/theme';
import AppLayout from '@/components/layout/AppLayout';
import ErrorBoundary from '@/components/common/ErrorBoundary';
import LoadingFallback from '@/components/common/LoadingFallback';
import { useAuthStore } from '@/store/authStore';

// Lazy-loaded pages
const LoginPage = React.lazy(() => import('@/pages/Login/LoginPage'));
const HomePage = React.lazy(() => import('@/pages/Home/HomePage'));
const TopicRecommendPage = React.lazy(() => import('@/pages/TopicRecommend/TopicRecommendPage'));
const ViralAnalysisPage = React.lazy(() => import('@/pages/ViralAnalysis/ViralAnalysisPage'));
const IdeaBoosterPage = React.lazy(() => import('@/pages/IdeaBooster/IdeaBoosterPage'));
const TitleOptimizerPage = React.lazy(() => import('@/pages/TitleOptimizer/TitleOptimizerPage'));
const TrackDiagnosisPage = React.lazy(() => import('@/pages/TrackDiagnosis/TrackDiagnosisPage'));
const CreatorProfilePage = React.lazy(() => import('@/pages/CreatorProfile/CreatorProfilePage'));
const EffectReviewPage = React.lazy(() => import('@/pages/EffectReview/EffectReviewPage'));
const PublishAdvisorPage = React.lazy(() => import('@/pages/PublishAdvisor/PublishAdvisorPage'));

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
    // Fetch user info if authenticated but user is not loaded yet
    // (e.g. after page refresh, token exists in localStorage but user is null)
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

            {/* Protected routes */}
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
              path="/ideas"
              element={
                <LazyRoute>
                  <ProtectedRoute>
                    <IdeaBoosterPage />
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

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </ErrorBoundary>
    </ThemeProvider>
  );
};

export default App;
