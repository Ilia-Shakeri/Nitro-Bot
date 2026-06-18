import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import './index.css'
import './i18n'
import App from './App.tsx'
import WebApp from '@twa-dev/sdk'

// Safely verify the WebApp object exists before calling its methods
if (WebApp.ready) {
  WebApp.ready();
  WebApp.expand(); // Forces the Mini App to full height for a premium feel
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
)