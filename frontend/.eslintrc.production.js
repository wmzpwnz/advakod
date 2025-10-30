module.exports = {
  extends: [
    'react-app',
    'react-app/jest'
  ],
  rules: {
    // Prevent console.log in production (strict)
    'no-console': ['error', { 
      allow: ['warn', 'error'] 
    }],
    
    // Prevent debugger statements
    'no-debugger': 'error',
    
    // Prevent alert, confirm, prompt
    'no-alert': 'error',
    
    // Prevent unused variables (helps catch debug code)
    'no-unused-vars': ['error', { 
      vars: 'all', 
      args: 'after-used',
      ignoreRestSiblings: false 
    }],
    
    // Custom rules to prevent localhost usage and hardcoded values
    'no-restricted-syntax': [
      'error',
      {
        selector: 'Literal[value=/localhost|127\\.0\\.0\\.1/]',
        message: 'Localhost references are not allowed in production. Use environment variables or proper service names.'
      },
      {
        selector: 'Literal[value=/advacodex\\.com/]',
        message: 'Hardcoded production URLs are not allowed. Use environment variables (REACT_APP_API_URL, REACT_APP_WS_URL).'
      },
      {
        selector: 'CallExpression[callee.object.name="console"][callee.property.name="log"]',
        message: 'console.log is not allowed in production. Use console.warn or console.error for important messages.'
      },
      {
        selector: 'CallExpression[callee.name="alert"]',
        message: 'alert() is not allowed in production. Use proper UI notifications.'
      },
      {
        selector: 'CallExpression[callee.name="confirm"]',
        message: 'confirm() is not allowed in production. Use proper UI confirmation dialogs.'
      },
      {
        selector: 'CallExpression[callee.name="prompt"]',
        message: 'prompt() is not allowed in production. Use proper UI input forms.'
      }
    ],
    
    // Prevent hardcoded URLs and enforce environment variables
    'no-restricted-globals': [
      'error',
      {
        name: 'location',
        message: 'Use window.location instead of location global.'
      }
    ],
    
    // Enforce proper error handling
    'no-empty-catch': 'error',
    'no-throw-literal': 'error',
    
    // Prevent TODO/FIXME comments in production
    'no-warning-comments': [
      'error',
      {
        terms: ['todo', 'fixme', 'hack', 'bug', 'debug'],
        location: 'anywhere'
      }
    ],
    
    // Enforce consistent return statements
    'consistent-return': 'error',
    
    // Prevent fallback to localhost in logical OR expressions
    'no-restricted-patterns': [
      'error',
      {
        pattern: '\\|\\|.*localhost',
        message: 'Localhost fallbacks are not allowed. Use strict environment variable validation.'
      }
    ]
  },
  
  // Environment-specific overrides
  overrides: [
    {
      // Test files - relax some rules
      files: [
        '**/*.test.js', 
        '**/*.test.ts', 
        '**/*.test.jsx', 
        '**/*.test.tsx',
        '**/__tests__/**/*',
        '**/test/**/*'
      ],
      rules: {
        'no-console': 'off',
        'no-restricted-syntax': 'off',
        'no-warning-comments': 'off',
        'no-unused-vars': 'warn'
      }
    },
    {
      // Development-only files
      files: [
        '**/demo/**/*',
        '**/examples/**/*',
        '**/*.dev.js',
        '**/*.dev.ts'
      ],
      rules: {
        'no-console': 'warn',
        'no-restricted-syntax': 'warn',
        'no-warning-comments': 'warn'
      }
    },
    {
      // Configuration files
      files: [
        '*.config.js',
        '*.config.ts',
        '.eslintrc.js',
        'webpack.config.js'
      ],
      rules: {
        'no-console': 'off',
        'no-restricted-syntax': 'off'
      }
    }
  ],
  
  // Custom parser options for better error detection
  parserOptions: {
    ecmaVersion: 2022,
    sourceType: 'module',
    ecmaFeatures: {
      jsx: true
    }
  },
  
  // Environment settings
  env: {
    browser: true,
    es2022: true,
    node: true
  }
};