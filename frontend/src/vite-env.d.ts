/// <reference types="vite/client" />

interface ImportMetaEnv {
  // where the backend is, e.g. https://api.example.org; defaults to http://localhost:8000
  readonly VITE_API_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
