import { lazy, Suspense, useEffect } from 'react';
import { Navigate, Routes, Route } from 'react-router-dom';
import WebApp from '@twa-dev/sdk';
import { ThemeProvider } from './context/ThemeContext';
import { ToastProvider } from './context/ToastContext';
import { UserProvider } from './context/UserContext';
import { ReleaseProvider } from './context/ReleaseContext';
import { ToastContainer } from './components/Toast';
import { LanguageModal } from './components/LanguageModal';
import { HomePage } from './pages/HomePage';
import { DMB_EDIT_ENABLED } from './featureFlags';

const UploadPage = lazy(() => import('./pages/UploadPage').then(module => ({ default: module.UploadPage })));
const EditPage = lazy(() => import('./pages/EditPage').then(module => ({ default: module.EditPage })));
const SupportPage = lazy(() => import('./pages/SupportPage').then(module => ({ default: module.SupportPage })));
const PolicyPage = lazy(() => import('./pages/PolicyPage').then(module => ({ default: module.PolicyPage })));
const ReleasesPage = lazy(() => import('./pages/ReleasesPage').then(module => ({ default: module.ReleasesPage })));

const RouteLoader = () => (
  <div className="min-h-[var(--tg-viewport-stable-height,100vh)] bg-background px-4 pt-20">
    <div className="mx-auto h-8 w-48 animate-pulse rounded-lg bg-card1" />
    <div className="mx-auto mt-6 h-52 max-w-md animate-pulse rounded-2xl bg-card1" />
  </div>
);

function App() {
  useEffect(() => {
    const updateViewportHeight = () => {
      const root = document.documentElement;
      if (WebApp.viewportHeight > 0) {
        root.style.setProperty('--tg-viewport-height', `${WebApp.viewportHeight}px`);
      }
      if (WebApp.viewportStableHeight > 0) {
        root.style.setProperty('--tg-viewport-stable-height', `${WebApp.viewportStableHeight}px`);
      }
    };

    updateViewportHeight();
    window.addEventListener('resize', updateViewportHeight);
    return () => window.removeEventListener('resize', updateViewportHeight);
  }, []);

  return (
    <ThemeProvider>
      <ToastProvider>
        <UserProvider>
          <ReleaseProvider>
            <Suspense fallback={<RouteLoader />}>
              <Routes>
                <Route path="/" element={<HomePage />} />
                <Route path="/upload" element={<UploadPage />} />
                <Route path="/edit/:id" element={DMB_EDIT_ENABLED ? <EditPage /> : <Navigate to="/releases" replace />} />
                <Route path="/releases" element={<ReleasesPage />} />
                <Route path="/support" element={<SupportPage />} />
                <Route path="/policy" element={<PolicyPage />} />
              </Routes>
            </Suspense>
          </ReleaseProvider>
          <LanguageModal />
          <ToastContainer />
        </UserProvider>
      </ToastProvider>
    </ThemeProvider>
  );
}

export default App;
