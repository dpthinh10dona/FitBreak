import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist', 'scr']),
  {
    files: ['**/*.{js,jsx}'],
    extends: [
      js.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      globals: globals.browser,
      parserOptions: { ecmaFeatures: { jsx: true } },
    },
    rules: {
      // React 19 no longer requires the React identifier in JSX files. Keep
      // legacy imports harmless while components are migrated incrementally.
      'no-unused-vars': ['error', {
        varsIgnorePattern: '^React$',
        argsIgnorePattern: '^(_|user$|activeTab$)',
        caughtErrorsIgnorePattern: '^e$',
      }],
      'no-empty': ['error', { allowEmptyCatch: true }],
      // Data-fetching effects intentionally update loading/data state.
      'react-hooks/set-state-in-effect': 'off',
    },
  },
])
