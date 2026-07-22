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
const NotFoundPage = React.lazy(() => import('@/pages/NotFound/NotFoundPage'));

const LazyRoute = ({ children }: { children: React.ReactNode }) => (
  <Suspense fallback={<LoadingFallback />}>{children}</Suspense>
);

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const user = useAuthStore((state) => state.user);
  const fetchCurrentUser = useAuthStore((state) => state.fetchCurrentUser);

  React.useEffect(() => {
    if (isAuthenticated && !user) void fetchCurrentUser().catch(() => undefined);
  }, [fetchCurrentUser, isAuthenticated, user]);

  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <AppLayout>{children}</AppLayout>;
};

const protectedPage = (page: React.ReactNode) => (
  <LazyRoute><ProtectedRoute>{page}</ProtectedRoute></LazyRoute>
);

const legacyRedirect = (to: string) => protectedPage(<Navigate to={to} replace />);

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

            <Route path="/topics" element={legacyRedirect('/opportunities')} />
            <Route path="/assets" element={legacyRedirect('/materials')} />
            <Route path="/profile" element={legacyRedirect('/me')} />
            {['/writing', '/ideas', '/titles', '/viral', '/publish', '/review'].map((path) => (
              <Route key={path} path={path} element={legacyRedirect('/content')} />
            ))}
            <Route path="/analytics" element={legacyRedirect('/')} />
            <Route path="/accounts" element={legacyRedirect('/me')} />
            <Route path="/tracks" element={legacyRedirect('/me')} />
            <Route path="*" element={protectedPage(<NotFoundPage />)} />
          </Routes>
        </BrowserRouter>
      </ErrorBoundary>
    </ThemeProvider>
  );
}
