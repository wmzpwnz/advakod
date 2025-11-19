# Neon Effects Implementation Guide

## Overview
This document describes the neon effects system implemented for the homepage redesign. The system includes CSS animations, utility classes, and mobile-optimized variants.

## Task 2.1: CSS Animations for Neon Glow

### Implemented Animations

#### 1. **neonPulse** (3s)
Basic pulsating neon effect with purple glow
```css
animation: neonPulse 3s ease-in-out infinite;
```

#### 2. **neonPulseIntense** (2.5s)
Intense pulsating effect with stronger glow
```css
animation: neonPulseIntense 2.5s ease-in-out infinite;
```

#### 3. **neonGradientGlow** (2s)
Gradient transition between purple and cyan
```css
animation: neonGradientGlow 2s ease-in-out infinite;
```

#### 4. **neonGradientFlow** (3s)
Smooth gradient flow with border color changes
```css
animation: neonGradientFlow 3s ease-in-out infinite;
```

#### 5. **neonRotatingGlow** (4s)
Rotating hue effect with brightness variation
```css
animation: neonRotatingGlow 4s linear infinite;
```

#### 6. **neonBreathing** (4s)
Subtle breathing effect for ambient glow
```css
animation: neonBreathing 4s ease-in-out infinite;
```

#### 7. **neonFlicker** (3s)
Dramatic flickering effect
```css
animation: neonFlicker 3s ease-in-out infinite;
```

#### 8. **neonBorderFlow** (4s)
Animated gradient border flow
```css
animation: neonBorderFlow 4s ease-in-out infinite;
```

#### 9. **silverShimmer** (3s)
Silver shimmer effect with glow
```css
animation: silverShimmer 3s ease-in-out infinite;
```

#### 10. **silverShimmerGlow** (3s)
Enhanced silver shimmer with brightness
```css
animation: silverShimmerGlow 3s ease-in-out infinite;
```

#### 11. **neonTextGlow** (3s)
Text shadow glow animation
```css
animation: neonTextGlow 3s ease-in-out infinite;
```

## Task 2.2: Utility Classes

### Base Neon Classes

#### Basic Glow
```html
<div class="neon-base">Base neon glow</div>
<div class="neon-purple-base">Purple neon</div>
<div class="neon-cyan-base">Cyan neon</div>
```

### Animated Classes

```html
<div class="neon-pulse">Pulsating glow</div>
<div class="neon-pulse-intense">Intense pulse</div>
<div class="neon-breathing">Breathing effect</div>
<div class="neon-gradient-flow">Gradient flow</div>
<div class="neon-rotating">Rotating glow</div>
<div class="neon-flicker">Flickering effect</div>
```

### Interactive States

#### Hover Effects
```html
<button class="neon-hover">Hover me</button>
<button class="neon-hover-intense">Intense hover</button>
<button class="neon-hover-cyan">Cyan hover</button>
```

#### Focus Effects
```html
<input class="neon-focus" />
<input class="neon-focus-ring" />
```

#### Active Effects
```html
<button class="neon-active">Click me</button>
```

#### Combined Interactive
```html
<button class="neon-interactive">All states</button>
```

### Shimmer Effects

```html
<div class="shimmer-silver-base">Static shimmer</div>
<div class="shimmer-silver-animated">Animated shimmer</div>
<div class="shimmer-silver-glow">Shimmer with glow</div>
<div class="shimmer-silver-hover">Shimmer on hover</div>
<div class="silver-sparkle">Sparkle effect</div>
```

### Text Effects

```html
<h1 class="neon-text">Purple neon text</h1>
<h1 class="neon-text-animated">Animated neon text</h1>
<h1 class="neon-text-cyan">Cyan neon text</h1>
```

### Button Variants

```html
<button class="neon-button-primary">Primary Neon Button</button>
<button class="neon-button-secondary">Secondary Neon Button</button>
```

Features:
- Glassmorphism background
- Animated border glow
- Shimmer sweep on hover
- Enhanced glow on active

### Card Variants

```html
<div class="neon-card">
  <h3>Neon Card</h3>
  <p>Content here</p>
</div>

<div class="neon-card-glow">
  <h3>Breathing Neon Card</h3>
  <p>With breathing animation</p>
</div>
```

## Mobile Optimization

### Automatic Adjustments

1. **Reduced Animation Duration** (768px and below)
   - All animations extended to 4s for smoother performance

2. **Simplified Hover Effects**
   - Transform effects disabled on mobile
   - Reduced glow intensity

3. **Touch-Friendly Sizing**
   - Minimum 44px touch targets
   - Increased padding on buttons

4. **Reduced Motion Support**
   ```css
   @media (prefers-reduced-motion: reduce) {
     /* All animations disabled */
   }
   ```

5. **Touch Device Detection**
   ```css
   @media (hover: none) and (pointer: coarse) {
     /* Touch-specific styles */
   }
   ```

6. **High Contrast Mode**
   ```css
   @media (prefers-contrast: high) {
     /* Enhanced borders and no text shadows */
   }
   ```

## Usage Examples

### Search Input with Neon Glow
```jsx
<input 
  className="neon-border-flow neon-focus bg-gray-900/80 backdrop-blur-lg 
             rounded-xl px-6 py-4 text-white"
  placeholder="Search..."
/>
```

### FAQ Card with Hover Effect
```jsx
<div className="neon-card hover:neon-hover p-6 rounded-2xl">
  <h3 className="neon-text-animated">Question?</h3>
  <p>Answer content...</p>
</div>
```

### CTA Button with Full Effects
```jsx
<button className="neon-button-primary px-8 py-4 rounded-xl font-semibold">
  Get Started
</button>
```

### Hero Title with Gradient Glow
```jsx
<h1 className="text-6xl font-bold neon-text-animated">
  АДВАКОД
</h1>
```

## Color Palette

### Neon Colors (from CSS variables)
- `--neon-purple`: #8B5CF6
- `--neon-purple-light`: #A78BFA
- `--neon-cyan`: #06B6D4
- `--neon-cyan-light`: #22D3EE

### Silver Colors
- `--accent-silver`: #C7C7CC
- `--accent-silver-light`: #E5E5EA
- Silver dark: #8E8E93

### Background Colors
- `--bg-primary`: #0a0a0a
- `--bg-secondary`: #1a1a1a
- `--bg-tertiary`: #2a2a2a

## Performance Considerations

1. **GPU Acceleration**: All animations use `transform` and `opacity` for optimal performance
2. **Will-change**: Applied automatically for animated elements
3. **Reduced Motion**: Respects user preferences
4. **Mobile Optimization**: Reduced complexity on smaller devices
5. **Backdrop Filter Fallback**: Graceful degradation for unsupported browsers

## Browser Support

- Chrome/Edge: Full support
- Firefox: Full support
- Safari: Full support (with backdrop-filter)
- Mobile browsers: Optimized with reduced effects

## Requirements Satisfied

✅ **Requirement 6.4**: Мерцающий серебристый серый с тонкой анимацией блеска
✅ **Requirement 6.5**: Усиленный мерцающий эффект при hover
✅ **Requirement 6.6**: Градиент от темно-серого к светло-серебристому с периодичностью 2-3 секунды
✅ **Requirement 5.3**: Микроанимации с изменением цвета и масштаба
✅ **Requirement 8.4**: Оптимизация анимаций для производительности на мобильных
