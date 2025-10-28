/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  darkMode: 'class', // Включаем поддержку темной темы через CSS класс
  theme: {
    extend: {
      colors: {
        // Dark Theme Colors
        dark: {
          primary: '#0a0a0a',
          secondary: '#1a1a1a',
          tertiary: '#2a2a2a',
        },
        // Apple-style Blue Accent
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#007AFF', // Apple Blue
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
          light: '#40A9FF',
        },
        // Neon Glow Colors - Purple-Cyan Palette
        neon: {
          purple: '#8B5CF6',
          'purple-light': '#A78BFA',
          cyan: '#06B6D4',
          'cyan-light': '#22D3EE',
        },
        // Silver Accent Colors
        silver: {
          DEFAULT: '#C7C7CC',
          light: '#E5E5EA',
          dark: '#8E8E93',
        },
        accent: {
          emerald: '#10b981',
          purple: '#8b5cf6',
          orange: '#f59e0b',
          pink: '#ec4899',
          cyan: '#06b6d4',
          indigo: '#6366f1',
          blue: '#007AFF',
          'blue-light': '#40A9FF',
        },
        // Module-specific colors for admin panel enhancement
        modules: {
          marketing: {
            50: '#fff7ed',
            100: '#ffedd5',
            200: '#fed7aa',
            300: '#fdba74',
            400: '#fb923c',
            500: '#f97316',
            600: '#ea580c',
            700: '#c2410c',
            800: '#9a3412',
            900: '#7c2d12',
            DEFAULT: '#f97316',
            light: '#fed7aa',
            dark: '#ea580c',
          },
          moderation: {
            50: '#faf5ff',
            100: '#f3e8ff',
            200: '#e9d5ff',
            300: '#d8b4fe',
            400: '#c084fc',
            500: '#a855f7',
            600: '#9333ea',
            700: '#7c3aed',
            800: '#6b21a8',
            900: '#581c87',
            DEFAULT: '#8b5cf6',
            light: '#ddd6fe',
            dark: '#7c3aed',
          },
          project: {
            50: '#ecfdf5',
            100: '#d1fae5',
            200: '#a7f3d0',
            300: '#6ee7b7',
            400: '#34d399',
            500: '#10b981',
            600: '#059669',
            700: '#047857',
            800: '#065f46',
            900: '#064e3b',
            DEFAULT: '#10b981',
            light: '#a7f3d0',
            dark: '#059669',
          },
          analytics: {
            50: '#eff6ff',
            100: '#dbeafe',
            200: '#bfdbfe',
            300: '#93c5fd',
            400: '#60a5fa',
            500: '#3b82f6',
            600: '#2563eb',
            700: '#1d4ed8',
            800: '#1e40af',
            900: '#1e3a8a',
            DEFAULT: '#3b82f6',
            light: '#bfdbfe',
            dark: '#2563eb',
          },
          system: {
            50: '#fef2f2',
            100: '#fee2e2',
            200: '#fecaca',
            300: '#fca5a5',
            400: '#f87171',
            500: '#ef4444',
            600: '#dc2626',
            700: '#b91c1c',
            800: '#991b1b',
            900: '#7f1d1d',
            DEFAULT: '#ef4444',
            light: '#fecaca',
            dark: '#dc2626',
          },
        },
        secondary: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
        },
        success: {
          50: '#f0fdf4',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
        },
        warning: {
          50: '#fffbeb',
          500: '#f59e0b',
          600: '#d97706',
          700: '#b45309',
        },
        error: {
          50: '#fef2f2',
          500: '#ef4444',
          600: '#dc2626',
          700: '#b91c1c',
        },
        info: {
          50: '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['-apple-system', 'BlinkMacSystemFont', 'SF Pro Display', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['SF Mono', 'Monaco', 'Cascadia Code', 'monospace'],
      },
      backgroundImage: {
        'shimmer-silver': 'linear-gradient(90deg, #2a2a2a 0%, #8E8E93 25%, #C7C7CC 50%, #8E8E93 75%, #2a2a2a 100%)',
        'shimmer-blue': 'linear-gradient(90deg, #007AFF 0%, #40A9FF 50%, #007AFF 100%)',
        'neon-glow': 'linear-gradient(45deg, #8B5CF6, #06B6D4, #A78BFA, #22D3EE)',
        'dark-gradient': 'linear-gradient(180deg, #0a0a0a 0%, #1a1a1a 100%)',
      },
      fontSize: {
        'hero': 'clamp(3rem, 8vw, 6rem)',
        'title': 'clamp(2rem, 5vw, 3.5rem)',
        'subtitle': 'clamp(1.25rem, 3vw, 2rem)',
        'body': 'clamp(1rem, 2vw, 1.25rem)',
      },
      backdropBlur: {
        xs: '2px',
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'slide-in-up': 'slideInUp 0.6s ease-out',
        'slide-in-down': 'slideInDown 0.6s ease-out',
        'slide-in-left': 'slideInLeft 0.6s ease-out',
        'slide-in-right': 'slideInRight 0.6s ease-out',
        'scale-in': 'scaleIn 0.4s ease-out',
        'float': 'float 3s ease-in-out infinite',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'bounce-slow': 'bounce 2s infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
        'gradient-shift': 'gradientShift 3s ease-in-out infinite',
        'neon-pulse': 'neonPulse 3s ease-in-out infinite',
        'neon-glow': 'neonGradientGlow 2s ease-in-out infinite',
        'neon-border': 'neonBorderFlow 4s ease-in-out infinite',
        'shimmer-silver': 'silverShimmer 3s ease-in-out infinite',
        'shimmer-sweep': 'shimmerSweep 3s infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideInUp: {
          '0%': { transform: 'translateY(30px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideInDown: {
          '0%': { transform: 'translateY(-30px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideInLeft: {
          '0%': { transform: 'translateX(-30px)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        slideInRight: {
          '0%': { transform: 'translateX(30px)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        scaleIn: {
          '0%': { transform: 'scale(0.9)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        glow: {
          '0%': { boxShadow: '0 0 5px rgba(59, 130, 246, 0.5)' },
          '100%': { boxShadow: '0 0 20px rgba(59, 130, 246, 0.8)' },
        },
        gradientShift: {
          '0%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
          '100%': { backgroundPosition: '0% 50%' },
        },
        neonPulse: {
          '0%, 100%': { 
            boxShadow: '0 0 5px rgba(139, 92, 246, 0.3), 0 0 10px rgba(139, 92, 246, 0.2), 0 0 15px rgba(139, 92, 246, 0.1)'
          },
          '50%': {
            boxShadow: '0 0 10px rgba(139, 92, 246, 0.6), 0 0 20px rgba(139, 92, 246, 0.4), 0 0 30px rgba(139, 92, 246, 0.2), 0 0 40px rgba(6, 182, 212, 0.1)'
          },
        },
        neonGradientGlow: {
          '0%': { 
            boxShadow: '0 0 5px rgba(139, 92, 246, 0.4), 0 0 10px rgba(139, 92, 246, 0.3)'
          },
          '25%': {
            boxShadow: '0 0 8px rgba(167, 139, 250, 0.5), 0 0 15px rgba(167, 139, 250, 0.3), 0 0 25px rgba(139, 92, 246, 0.2)'
          },
          '50%': {
            boxShadow: '0 0 10px rgba(6, 182, 212, 0.6), 0 0 20px rgba(6, 182, 212, 0.4), 0 0 30px rgba(6, 182, 212, 0.2)'
          },
          '75%': {
            boxShadow: '0 0 8px rgba(34, 211, 238, 0.5), 0 0 15px rgba(34, 211, 238, 0.3), 0 0 25px rgba(6, 182, 212, 0.2)'
          },
          '100%': { 
            boxShadow: '0 0 5px rgba(139, 92, 246, 0.4), 0 0 10px rgba(139, 92, 246, 0.3)'
          },
        },
        neonBorderFlow: {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
        silverShimmer: {
          '0%': { 
            backgroundPosition: '-200% center',
            boxShadow: '0 0 0 rgba(199, 199, 204, 0)'
          },
          '50%': {
            backgroundPosition: '200% center',
            boxShadow: '0 0 20px rgba(199, 199, 204, 0.3)'
          },
          '100%': { 
            backgroundPosition: '-200% center',
            boxShadow: '0 0 0 rgba(199, 199, 204, 0)'
          },
        },
        shimmerSweep: {
          '0%': { left: '-100%' },
          '100%': { left: '100%' },
        },
      }
    },
  },
  plugins: [],
}
