import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'

export default tseslint.config(
  { ignores: ['dist', '.vite'] },
  {
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
    },
    plugins: {
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      'react-refresh/only-export-components': [
        'warn',
        { allowConstantExport: true },
      ],
    },
  },
  // only apiClient talks to the backend
  {
    files: ['src/**/*.{ts,tsx}'],
    ignores: ['src/apiClient.ts'],
    rules: {
      'no-restricted-globals': ['error', { name: 'fetch', message: 'Only src/apiClient.ts may make network requests.' }],
    },
  },
  // the plain TypeScript modules: no React (and the store and index no D3 either)
  {
    files: ['src/mapGeometry.ts'],
    rules: {
      'no-restricted-imports': ['error', { patterns: [{ group: ['react', 'react-*', 'react/*'], message: 'mapGeometry must not import React.' }] }],
    },
  },
  {
    files: ['src/routeStore.ts', 'src/stationIndex.ts'],
    rules: {
      'no-restricted-imports': [
        'error',
        {
          // plain 'zustand' pulls in React; the store uses 'zustand/vanilla'
          paths: [{ name: 'zustand', message: "Use 'zustand/vanilla'; components read the store through useRouteStore." }],
          patterns: [
            { group: ['react', 'react-*', 'react/*'], message: 'This module must not import React.' },
            { group: ['d3', 'd3-*'], message: 'This module must not import D3.' },
          ],
        },
      ],
    },
  },
)
