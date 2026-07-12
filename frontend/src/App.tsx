import { lazy, Suspense, useEffect } from 'react';
import { Routes, Route } from 'react-router-dom';
import WebApp from '@twa-dev/sdk';
import { ThemeProvider } from './context/ThemeContext';
import { ToastProvider } from './context/ToastContext';
import { UserProvider } from './context/UserContext';
import { ToastContainer } from './components/Toast';
import { LanguageModal } from './components/LanguageModal';
import { HomePage } from './pages/HomePage';

const UploadPage = lazy(() => import('./pages/UploadPage').then(module => ({ default: module.UploadPage })));
const EditPage = lazy(() => import('./pages/EditPage').then(module => ({ default: module.EditPage })));
const SupportPage = lazy(() => import('./pages/SupportPage').then(module => ({ default: module.SupportPage })));
const PolicyPage = lazy(() => import('./pages/PolicyPage').then(module => ({ default: module.PolicyPage })));

const RouteLoader = () => (
  <div className="min-h-[var(--tg-viewport-stable-height,100vh)] bg-background flex items-center justify-center">
    <div className="h-8 w-8 animate-spin rounded-full border-2 border-gold/30 border-t-gold" />
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
    WebApp.onEvent('viewportChanged', updateViewportHeight);
    return () => WebApp.offEvent('viewportChanged', updateViewportHeight);
  }, []);

  return (
    <ThemeProvider>
      <ToastProvider>
        <UserProvider>
          <Suspense fallback={<RouteLoader />}>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/upload" element={<UploadPage />} />
              <Route path="/edit/:id" element={<EditPage />} />
              <Route path="/support" element={<SupportPage />} />
              <Route path="/policy" element={<PolicyPage />} />
            </Routes>
          </Suspense>
          <LanguageModal />
          <ToastContainer />
        </UserProvider>
      </ToastProvider>
    </ThemeProvider>
  );
}

export default App;
