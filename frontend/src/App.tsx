/** Root router for the five-node intent-driven product. */
import React, { Suspense } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { CssBaseline, ThemeProvider } from '@mui/material';
import AppLayout from '@/components/layout/AppLayout';
import ErrorBoundary from '@/components/common/ErrorBoundary';
import LoadingFallback from '@/components/common/LoadingFallback';
import { useAuthStore } from '@/store/authStore';
import theme from '@/styles/theme';

const LoginPage = React.lazy(() => import('@/pages/Login/LoginPage'));
const HomePage = React.lazy(() => import('@/pages/Home/HomePage'));
const ContentPage = React.lazy(() => import('@/pages/Content/ContentPage'));
const OpportunitiesPage = React.lazy(() => import('@/pages/Opportunities/OpportunitiesPage'));
const MaterialsPage = React.lazy(() => import('@/pages/Materials/MaterialsPage'));
const MePage = React.lazy(() => import('@/pages/Me/MePage'));
const StarterPage = React.lazy(() => import('@/pages/Starter/StarterPage'));
const GrowthOnboardingPage = React.lazy(() => import('@/pages/GrowthOnboarding/GrowthOnboardingPage'));
const NotFoundPage = React.lazy(() => import('@/pages/NotFound/NotFoundPage'));

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

const protectedPage = (page: React.ReactNode) => (
  <LazyRoute><ProtectedRoute>{page}</ProtectedRoute></LazyRoute>
);

export default function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <ErrorBoundary>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LazyRoute><LoginPage /></LazyRoute>} />
            <Route path="/" element={protectedPage(<HomePage />)} />
            <Route path="/content" element={protectedPage(<ContentPage />)} />
            <Route path="/content/:projectId" element={protectedPage(<ContentPage />)} />
            <Route path="/opportunities" element={protectedPage(<OpportunitiesPage />)} />
            <Route path="/materials" element={protectedPage(<MaterialsPage />)} />
            <Route path="/me" element={protectedPage(<MePage />)} />
            <Route path="/onboarding/assessment" element={protectedPage(<StarterPage />)} />
            <Route path="/onboarding/directions" element={protectedPage(<StarterPage />)} />
            <Route path="/onboarding/sprint" element={protectedPage(<StarterPage />)} />
            <Route path="/onboarding/growth" element={protectedPage(<GrowthOnboardingPage />)} />
            {/* 404 stays outside the auth guard: unknown paths should show
                the not-found page, not redirect unauthenticated visitors. */}
            <Route path="*" element={<LazyRoute><NotFoundPage /></LazyRoute>} />
          </Routes>
        </BrowserRouter>
      </ErrorBoundary>
    </ThemeProvider>
  );
}
