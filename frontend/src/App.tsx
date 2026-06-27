import { Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import { ToastProvider } from './context/ToastContext';
import { UserProvider } from './context/UserContext';
import { ToastContainer } from './components/Toast';
import { HomePage } from './pages/HomePage';
import { UploadPage } from './pages/UploadPage';

function App() {
  return (
    <ThemeProvider>
      <ToastProvider>
        <UserProvider>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/upload" element={<UploadPage />} />
          </Routes>
          <ToastContainer />
        </UserProvider>
      </ToastProvider>
    </ThemeProvider>
  );
}

export default App;
