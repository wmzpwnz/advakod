# Apple Neon Theme - Концепция дизайна

## 🍎 Философия Apple Design

Современный Apple дизайн сочетает:
- **Минимализм** - чистые линии, много воздуха
- **Яркие неоновые акценты** - как в iOS 16+, macOS Ventura
- **Glassmorphism** - матовое стекло с размытием
- **Живые градиенты** - динамичные, яркие переходы
- **Плавные анимации** - 60 FPS, естественные движения

## 🌈 Цветовая палитра Apple Neon

### Основные фоны
```css
/* Apple Light Theme - Чистые белые фоны */
--apple-bg-primary: #FFFFFF;           /* Чистый белый */
--apple-bg-secondary: #FAFAFA;         /* Почти белый */
--apple-bg-tertiary: #F5F5F7;          /* Светлый серый Apple */
--apple-bg-elevated: #FFFFFF;          /* Приподнятые элементы */
```

### Apple Neon Colors (iOS 16+ стиль)
```css
/* Яркие неоновые цвета Apple */
--apple-blue: #007AFF;                 /* Фирменный синий Apple */
--apple-blue-vibrant: #0A84FF;         /* Яркий синий */
--apple-purple: #AF52DE;               /* Фиолетовый Apple */
--apple-purple-vibrant: #BF5AF2;       /* Яркий фиолетовый */
--apple-pink: #FF2D55;                 /* Розовый Apple */
--apple-pink-vibrant: #FF375F;         /* Яркий розовый */
--apple-cyan: #32ADE6;                 /* Циан Apple */
--apple-cyan-vibrant: #64D2FF;         /* Яркий циан */
--apple-mint: #00C7BE;                 /* Мятный Apple */
--apple-mint-vibrant: #63E6E2;         /* Яркий мятный */
--apple-orange: #FF9500;               /* Оранжевый Apple */
--apple-orange-vibrant: #FF9F0A;       /* Яркий оранжевый */
--apple-yellow: #FFCC00;               /* Желтый Apple */
--apple-green: #34C759;                /* Зеленый Apple */
--apple-indigo: #5856D6;               /* Индиго Apple */
```

### Градиенты Apple
```css
/* Живые градиенты как в iOS/macOS */
--apple-gradient-blue: linear-gradient(135deg, #007AFF 0%, #5856D6 100%);
--apple-gradient-purple: linear-gradient(135deg, #BF5AF2 0%, #FF2D55 100%);
--apple-gradient-cyan: linear-gradient(135deg, #32ADE6 0%, #00C7BE 100%);
--apple-gradient-sunset: linear-gradient(135deg, #FF9500 0%, #FF2D55 100%);
--apple-gradient-ocean: linear-gradient(135deg, #007AFF 0%, #00C7BE 100%);
--apple-gradient-rainbow: linear-gradient(135deg, 
  #FF2D55 0%, 
  #FF9500 20%, 
  #FFCC00 40%, 
  #34C759 60%, 
  #32ADE6 80%, 
  #BF5AF2 100%);
```

### Текст
```css
/* Текст в стиле Apple */
--apple-text-primary: #000000;         /* Чистый черный */
--apple-text-secondary: #86868B;       /* Серый Apple */
--apple-text-tertiary: #C7C7CC;        /* Светлый серый */
--apple-text-link: #007AFF;            /* Синий для ссылок */
```

### Тени Apple
```css
/* Мягкие тени как в macOS */
--apple-shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.04);
--apple-shadow-md: 0 4px 12px rgba(0, 0, 0, 0.08);
--apple-shadow-lg: 0 12px 24px rgba(0, 0, 0, 0.12);
--apple-shadow-xl: 0 24px 48px rgba(0, 0, 0, 0.16);

/* Цветные неоновые тени */
--apple-glow-blue: 0 8px 32px rgba(0, 122, 255, 0.4);
--apple-glow-purple: 0 8px 32px rgba(191, 90, 242, 0.4);
--apple-glow-pink: 0 8px 32px rgba(255, 45, 85, 0.4);
--apple-glow-cyan: 0 8px 32px rgba(50, 173, 230, 0.4);
```

## 🎨 Компоненты в стиле Apple

### 1. Apple Glass Card
```css
.apple-glass-card {
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(40px) saturate(180%);
  -webkit-backdrop-filter: blur(40px) saturate(180%);
  border: 0.5px solid rgba(255, 255, 255, 0.8);
  border-radius: 20px;
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.apple-glass-card:hover {
  transform: translateY(-4px) scale(1.01);
  box-shadow: 
    0 16px 48px rgba(0, 0, 0, 0.12),
    0 0 0 1px rgba(0, 122, 255, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 1);
}
```

### 2. Apple Neon Button
```css
.apple-button-primary {
  background: linear-gradient(180deg, #007AFF 0%, #0051D5 100%);
  color: white;
  font-weight: 600;
  font-size: 17px;
  padding: 12px 24px;
  border-radius: 12px;
  border: none;
  box-shadow: 
    0 4px 16px rgba(0, 122, 255, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
}

.apple-button-primary::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 50%;
  background: linear-gradient(180deg, 
    rgba(255, 255, 255, 0.3) 0%, 
    transparent 100%);
  border-radius: 12px 12px 0 0;
}

.apple-button-primary:hover {
  transform: scale(1.02);
  box-shadow: 
    0 8px 24px rgba(0, 122, 255, 0.4),
    0 0 32px rgba(0, 122, 255, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
}

.apple-button-primary:active {
  transform: scale(0.98);
  box-shadow: 
    0 2px 8px rgba(0, 122, 255, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

/* Gradient button варианты */
.apple-button-purple {
  background: linear-gradient(135deg, #BF5AF2 0%, #AF52DE 100%);
  box-shadow: 0 4px 16px rgba(191, 90, 242, 0.3);
}

.apple-button-purple:hover {
  box-shadow: 
    0 8px 24px rgba(191, 90, 242, 0.4),
    0 0 32px rgba(191, 90, 242, 0.3);
}

.apple-button-gradient {
  background: linear-gradient(135deg, 
    #007AFF 0%, 
    #BF5AF2 50%, 
    #FF2D55 100%);
  background-size: 200% 200%;
  animation: appleGradientShift 3s ease infinite;
  box-shadow: 
    0 4px 16px rgba(0, 122, 255, 0.3),
    0 4px 16px rgba(191, 90, 242, 0.2);
}

.apple-button-gradient:hover {
  box-shadow: 
    0 8px 24px rgba(0, 122, 255, 0.4),
    0 8px 24px rgba(191, 90, 242, 0.3),
    0 0 40px rgba(255, 45, 85, 0.2);
}
```

### 3. Apple Input Field
```css
.apple-input {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 12px;
  padding: 12px 16px;
  font-size: 17px;
  color: #000000;
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.apple-input:focus {
  outline: none;
  border-color: #007AFF;
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 
    0 4px 16px rgba(0, 122, 255, 0.15),
    0 0 0 4px rgba(0, 122, 255, 0.1),
    0 0 24px rgba(0, 122, 255, 0.2);
}

.apple-input::placeholder {
  color: #86868B;
}
```

### 4. Apple Gradient Text
```css
.apple-gradient-text {
  background: linear-gradient(135deg, 
    #007AFF 0%, 
    #BF5AF2 50%, 
    #FF2D55 100%);
  background-size: 200% 200%;
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: appleGradientShift 4s ease-in-out infinite;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.apple-gradient-text-rainbow {
  background: linear-gradient(90deg, 
    #FF2D55 0%, 
    #FF9500 16.67%, 
    #FFCC00 33.33%, 
    #34C759 50%, 
    #32ADE6 66.67%, 
    #BF5AF2 83.33%, 
    #FF2D55 100%);
  background-size: 200% 100%;
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: appleRainbowShift 6s linear infinite;
}
```

### 5. Apple Hero Section
```css
.apple-hero {
  position: relative;
  min-height: 100vh;
  background: linear-gradient(180deg, 
    #FFFFFF 0%, 
    #F5F5F7 100%);
  overflow: hidden;
}

.apple-hero-content {
  position: relative;
  z-index: 10;
  text-align: center;
  padding: 120px 20px;
}

.apple-hero-title {
  font-size: clamp(48px, 8vw, 96px);
  font-weight: 700;
  letter-spacing: -0.03em;
  line-height: 1.05;
  margin-bottom: 24px;
}

.apple-hero-subtitle {
  font-size: clamp(21px, 3vw, 28px);
  font-weight: 400;
  color: #86868B;
  line-height: 1.4;
  margin-bottom: 40px;
}

/* Animated mesh gradient background */
.apple-mesh-gradient {
  position: absolute;
  inset: 0;
  opacity: 0.6;
  background: 
    radial-gradient(circle at 20% 30%, rgba(0, 122, 255, 0.15) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(191, 90, 242, 0.15) 0%, transparent 50%),
    radial-gradient(circle at 40% 70%, rgba(255, 45, 85, 0.15) 0%, transparent 50%),
    radial-gradient(circle at 90% 80%, rgba(50, 173, 230, 0.15) 0%, transparent 50%);
  animation: appleMeshMove 20s ease-in-out infinite;
}
```

### 6. Apple Card Grid
```css
.apple-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 24px;
  padding: 40px 20px;
}

.apple-feature-card {
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(40px) saturate(180%);
  border: 0.5px solid rgba(255, 255, 255, 0.8);
  border-radius: 20px;
  padding: 40px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.apple-feature-card:hover {
  transform: translateY(-8px) scale(1.02);
  box-shadow: 
    0 16px 48px rgba(0, 0, 0, 0.12),
    0 0 0 1px rgba(0, 122, 255, 0.2);
}

.apple-feature-icon {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  background: linear-gradient(135deg, #007AFF 0%, #BF5AF2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 24px;
  box-shadow: 0 8px 24px rgba(0, 122, 255, 0.3);
}

.apple-feature-title {
  font-size: 24px;
  font-weight: 600;
  color: #000000;
  margin-bottom: 12px;
  letter-spacing: -0.01em;
}

.apple-feature-description {
  font-size: 17px;
  color: #86868B;
  line-height: 1.5;
}
```

## 🎬 Анимации Apple

```css
/* Gradient shift animation */
@keyframes appleGradientShift {
  0%, 100% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
}

/* Rainbow shift animation */
@keyframes appleRainbowShift {
  0% {
    background-position: 0% 50%;
  }
  100% {
    background-position: 200% 50%;
  }
}

/* Mesh gradient movement */
@keyframes appleMeshMove {
  0%, 100% {
    transform: translate(0, 0) scale(1);
  }
  33% {
    transform: translate(30px, -30px) scale(1.1);
  }
  66% {
    transform: translate(-20px, 20px) scale(0.9);
  }
}

/* Smooth scale animation */
@keyframes appleScale {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
}

/* Floating animation */
@keyframes appleFloat {
  0%, 100% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-20px);
  }
}

/* Pulse glow animation */
@keyframes applePulseGlow {
  0%, 100% {
    box-shadow: 0 0 20px rgba(0, 122, 255, 0.3);
  }
  50% {
    box-shadow: 0 0 40px rgba(0, 122, 255, 0.6);
  }
}
```

## 📱 Типографика Apple

```css
/* SF Pro Display стиль */
.apple-typography {
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 
               'SF Pro Text', 'Helvetica Neue', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
}

.apple-display-large {
  font-size: clamp(48px, 8vw, 96px);
  font-weight: 700;
  letter-spacing: -0.03em;
  line-height: 1.05;
}

.apple-display-medium {
  font-size: clamp(36px, 6vw, 64px);
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1.1;
}

.apple-title-1 {
  font-size: 28px;
  font-weight: 600;
  letter-spacing: -0.01em;
  line-height: 1.2;
}

.apple-title-2 {
  font-size: 22px;
  font-weight: 600;
  letter-spacing: -0.005em;
  line-height: 1.3;
}

.apple-body {
  font-size: 17px;
  font-weight: 400;
  line-height: 1.5;
}

.apple-body-large {
  font-size: 21px;
  font-weight: 400;
  line-height: 1.4;
}

.apple-caption {
  font-size: 15px;
  font-weight: 400;
  color: #86868B;
  line-height: 1.4;
}
```

## 🎯 Примеры использования

### Hero Section
```jsx
<section className="apple-hero">
  <div className="apple-mesh-gradient" />
  
  <div className="apple-hero-content">
    <h1 className="apple-display-large apple-gradient-text-rainbow">
      АДВАКОД
    </h1>
    <p className="apple-hero-subtitle">
      Ваш персональный AI юрист-консультант
    </p>
    <div className="flex gap-4 justify-center">
      <button className="apple-button-gradient">
        Начать бесплатно
      </button>
      <button className="apple-button-primary">
        Узнать больше
      </button>
    </div>
  </div>
</section>
```

### Feature Cards
```jsx
<div className="apple-card-grid">
  <div className="apple-feature-card">
    <div className="apple-feature-icon">
      <svg className="w-8 h-8 text-white" />
    </div>
    <h3 className="apple-feature-title">
      Умный поиск
    </h3>
    <p className="apple-feature-description">
      Мгновенный поиск по всей базе российского законодательства
    </p>
  </div>
</div>
```

### Search Input
```jsx
<div className="relative max-w-2xl mx-auto">
  <input 
    type="text"
    className="apple-input w-full"
    placeholder="Задайте вопрос AI-юристу..."
  />
</div>
```

## ✨ Ключевые особенности Apple Design

1. **Минимализм** - Чистые линии, много воздуха
2. **Яркие неоновые акценты** - Живые градиенты
3. **Glassmorphism** - Blur 40px, высокая насыщенность
4. **Плавные анимации** - Cubic-bezier easing
5. **SF Pro шрифт** - Или system font stack
6. **Цветные тени** - Неоновые glow эффекты
7. **Mesh градиенты** - Динамичные фоны
8. **Высокий контраст** - Черный текст на белом

## 🎨 Цветовые комбинации

### Для кнопок
- Blue → Purple (классика Apple)
- Purple → Pink (яркий акцент)
- Cyan → Mint (свежий)
- Orange → Pink (закат)
- Rainbow (все цвета)

### Для карточек
- White glass с blue accent
- White glass с purple accent
- White glass с gradient border

### Для текста
- Black (#000000) - основной
- Gray (#86868B) - вторичный
- Gradient - акценты и заголовки

## 🚀 Готово к реализации!

Все компоненты готовы в стиле Apple с яркими неоновыми эффектами! 🍎✨
