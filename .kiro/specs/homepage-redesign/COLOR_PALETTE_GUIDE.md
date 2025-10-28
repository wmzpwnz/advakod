# Color Palette & CSS Variables Guide

## Overview
This guide documents the new dark theme color palette with neon glow effects in purple-cyan palette, implemented for the homepage redesign.

## CSS Variables

### Dark Theme - Primary Colors
```css
--bg-primary: #0a0a0a;      /* Deep black background */
--bg-secondary: #1a1a1a;    /* Dark gray background */
--bg-tertiary: #2a2a2a;     /* Medium gray background */
```

### Accent Colors - Apple Style
```css
--accent-blue: #007AFF;         /* Apple Blue */
--accent-blue-light: #40A9FF;   /* Light Blue */
--accent-silver: #C7C7CC;       /* Silver */
--accent-silver-light: #E5E5EA; /* Light Silver */
```

### Neon Glow - Purple-Cyan Palette
```css
--neon-purple: #8B5CF6;         /* Purple Neon */
--neon-cyan: #06B6D4;           /* Cyan Neon */
--neon-purple-light: #A78BFA;   /* Light Purple */
--neon-cyan-light: #22D3EE;     /* Light Cyan */
```

### Text Colors
```css
--text-primary: #E5E5EA;    /* Primary text */
--text-secondary: #C7C7CC;  /* Secondary text */
--text-tertiary: #8E8E93;   /* Tertiary text */
```

## Tailwind Classes

### Background Colors
- `bg-dark-primary` - Deep black (#0a0a0a)
- `bg-dark-secondary` - Dark gray (#1a1a1a)
- `bg-dark-tertiary` - Medium gray (#2a2a2a)

### Neon Colors
- `text-neon-purple` - Purple neon text
- `text-neon-cyan` - Cyan neon text
- `bg-neon-purple` - Purple neon background
- `bg-neon-cyan` - Cyan neon background

### Silver Colors
- `text-silver` - Silver text (#C7C7CC)
- `text-silver-light` - Light silver text (#E5E5EA)
- `text-silver-dark` - Dark silver text (#8E8E93)

## Utility Classes

### Neon Glow Effects
```html
<!-- Purple neon glow with pulse animation -->
<div class="neon-glow-purple">Content</div>

<!-- Cyan neon glow -->
<div class="neon-glow-cyan">Content</div>

<!-- Neon border flow effect -->
<div class="neon-border-flow">Content</div>
```

### Shimmer Effects
```html
<!-- Silver shimmer animation -->
<div class="shimmer-silver">Content</div>

<!-- Blue shimmer animation -->
<div class="shimmer-blue">Content</div>
```

## Animations

### Available Animations
- `animate-neon-pulse` - Pulsing neon glow (3s)
- `animate-neon-glow` - Gradient neon glow (2s)
- `animate-neon-border` - Flowing neon border (4s)
- `animate-shimmer-silver` - Silver shimmer effect (3s)
- `animate-shimmer-sweep` - Sweeping shimmer (3s)

### Usage Examples
```html
<!-- Button with neon pulse -->
<button class="animate-neon-pulse border border-neon-purple">
  Click Me
</button>

<!-- Card with shimmer effect -->
<div class="shimmer-silver rounded-lg p-6">
  Card Content
</div>
```

## Background Gradients

### Available Gradients
- `bg-shimmer-silver` - Silver shimmer gradient
- `bg-shimmer-blue` - Blue shimmer gradient
- `bg-neon-glow` - Purple-cyan neon gradient
- `bg-dark-gradient` - Dark theme gradient

### Usage
```html
<div class="bg-neon-glow p-8 rounded-xl">
  Neon gradient background
</div>
```

## Typography

### Font Families
- `font-display` - Apple-style display font (SF Pro Display, Inter)
- `font-mono` - Monospace font (SF Mono, Monaco)

### Responsive Font Sizes
- `text-hero` - clamp(3rem, 8vw, 6rem)
- `text-title` - clamp(2rem, 5vw, 3.5rem)
- `text-subtitle` - clamp(1.25rem, 3vw, 2rem)
- `text-body` - clamp(1rem, 2vw, 1.25rem)

## Complete Example

```html
<div class="bg-dark-primary min-h-screen">
  <!-- Hero Section with Neon Glow -->
  <section class="relative overflow-hidden">
    <div class="neon-border-flow bg-dark-secondary/80 backdrop-blur-lg rounded-2xl p-8">
      <h1 class="text-hero font-display font-bold text-silver-light animate-shimmer-silver">
        АДВАКОД
      </h1>
      <p class="text-subtitle text-silver mt-4">
        Ваш персональный AI юрист-консультант
      </p>
      <button class="neon-glow-purple bg-dark-tertiary text-silver-light px-8 py-4 rounded-xl mt-6 hover:animate-neon-glow">
        Начать работу
      </button>
    </div>
  </section>
  
  <!-- Card with Shimmer Effect -->
  <div class="shimmer-silver bg-dark-secondary rounded-xl p-6 mt-8">
    <h3 class="text-xl font-semibold text-neon-purple">
      Умный поиск
    </h3>
    <p class="text-silver-dark mt-2">
      Найдите ответы на юридические вопросы
    </p>
  </div>
</div>
```

## Browser Support

All effects are optimized for modern browsers:
- Chrome 90+
- Safari 14+
- Firefox 88+
- Edge 90+

Fallbacks are provided for older browsers that don't support `backdrop-filter` and advanced CSS animations.
