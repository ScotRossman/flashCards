import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { configureCognitoAuth } from './services/auth'
import './index.css'
import App from './App.tsx'

configureCognitoAuth()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
