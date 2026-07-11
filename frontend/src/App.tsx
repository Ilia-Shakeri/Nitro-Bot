import { Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import { ToastProvider } from './context/ToastContext';
import { UserProvider } from './context/UserContext';
import { ToastContainer } from './components/Toast';
import { LanguageModal } from './components/LanguageModal';
import { HomePage } from './pages/HomePage';
import { UploadPage } from './pages/UploadPage';
import { EditPage } from './pages/EditPage';
import { SupportPage } from './pages/SupportPage';
import { PolicyPage } from './pages/PolicyPage';

function App() {
  return (
    <ThemeProvider>
      <ToastProvider>
        <UserProvider>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/upload" element={<UploadPage />} />
            <Route path="/edit/:id" element={<EditPage />} />
            <Route path="/support" element={<SupportPage />} />
            <Route path="/policy" element={<PolicyPage />} />
          </Routes>
          <LanguageModal />
          <ToastContainer />
        </UserProvider>
      </ToastProvider>
    </ThemeProvider>
  );
}

export default App;
