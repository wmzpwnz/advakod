# Design Document - Редизайн главной страницы Адвакодекс

## Overview

Полный редизайн главной страницы Адвакодекс с применением современной темной темы, минималистичной эстетики и премиальных визуальных эффектов. Дизайн создает ощущение инновационности и технологичности AI-юриста, используя типографику в стиле Apple, мерцающие серебристые элементы и интерактивные анимации.

## Architecture

### Компонентная структура
- **HomePage** - основной компонент страницы
- **HeroSection** - главный баннер с CTA
- **SmartSearchInput** - интерактивное поле поиска с подсказками
- **SmartFAQ** - умные FAQ с мгновенными ответами
- **TrustBlock** - блок доверия с логотипами партнеров
- **ModernButton** - обновленные кнопки с мерцающими эффектами
- **GlassCard** - карточки с glassmorphism эффектами

### Цветовая палитра

#### Темная тема (основная)
```css
/* Основные цвета */
--bg-primary: #0a0a0a;           /* Глубокий черный */
--bg-secondary: #1a1a1a;         /* Темно-серый */
--bg-tertiary: #2a2a2a;          /* Средний серый */

/* Акцентные цвета */
--accent-blue: #007AFF;          /* Apple Blue */
--accent-blue-light: #40A9FF;    /* Светлый синий */
--accent-silver: #C7C7CC;        /* Серебристый */
--accent-silver-light: #E5E5EA;  /* Светлый серебристый */

/* Неоновое свечение - фиолетово-лазурная гамма */
--neon-purple: #8B5CF6;          /* Фиолетовый неон */
--neon-cyan: #06B6D4;            /* Лазурный неон */
--neon-purple-light: #A78BFA;    /* Светлый фиолетовый */
--neon-cyan-light: #22D3EE;      /* Светлый лазурный */

/* Мерцающие градиенты */
--shimmer-silver: linear-gradient(45deg, #8E8E93, #C7C7CC, #E5E5EA, #C7C7CC, #8E8E93);
--shimmer-blue: linear-gradient(45deg, #007AFF, #40A9FF, #007AFF);
--neon-glow-gradient: linear-gradient(45deg, #8B5CF6, #06B6D4, #A78BFA, #22D3EE);
```

#### Типографика в стиле Apple
```css
/* Шрифты */
--font-primary: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Inter', system-ui, sans-serif;
--font-mono: 'SF Mono', 'Monaco', 'Cascadia Code', monospace;

/* Размеры */
--text-hero: clamp(3rem, 8vw, 6rem);      /* 48-96px */
--text-title: clamp(2rem, 5vw, 3.5rem);   /* 32-56px */
--text-subtitle: clamp(1.25rem, 3vw, 2rem); /* 20-32px */
--text-body: clamp(1rem, 2vw, 1.25rem);   /* 16-20px */

/* Веса */
--weight-light: 300;
--weight-regular: 400;
--weight-medium: 500;
--weight-semibold: 600;
--weight-bold: 700;
```

## Components and Interfaces

### 1. HeroSection

#### Дизайн
- **Фон**: Глубокий градиент от #0a0a0a к #1a1a1a
- **Анимированные частицы**: Плавающие серебристые точки с мерцанием
- **Заголовок**: "АДВАКОД" - крупная типографика с градиентным мерцанием
- **Подзаголовок**: "Ваш персональный AI юрист-консультант"
- **Описание**: Ультра-короткое (максимум 2 предложения)

#### Анимации
```javascript
// Мерцающий эффект заголовка
const shimmerAnimation = {
  backgroundPosition: ['0% 50%', '100% 50%', '0% 50%'],
  transition: { duration: 3, repeat: Infinity, ease: "easeInOut" }
};

// Плавающие частицы
const particleFloat = {
  y: [0, -20, 0],
  opacity: [0.3, 0.8, 0.3],
  transition: { duration: 4, repeat: Infinity, ease: "easeInOut" }
};
```

### 2. SmartSearchInput

#### Дизайн
- **Контейнер**: Glassmorphism с мерцающей серебристой рамкой
- **Размер**: Крупное поле (минимум 60px высота)
- **Плейсхолдер**: "Задайте вопрос AI-юристу..." с анимацией печати
- **Неоновое свечение**: Фиолетово-лазурное свечение с пульсацией
- **Состояния**:
  - **Hover**: Усиленное свечение с градиентным переходом
  - **Focus**: Максимальное свечение с интенсивной пульсацией
  - **Active**: Динамическое свечение, следующее за курсором

#### Интерактивность
```javascript
// Подсказки при вводе
const suggestions = [
  "Как зарегистрировать ИП?",
  "Проверить договор на ошибки",
  "Налоги для самозанятых",
  "Защита авторских прав",
  "Трудовые споры с работодателем"
];

// Анимация появления подсказок
const suggestionAnimation = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -10 }
};
```

### 3. SmartFAQ

#### Структура
```javascript
const faqData = [
  {
    id: 1,
    question: "Как AI может заменить юриста?",
    answer: "AI не заменяет, а дополняет работу юриста...",
    category: "general",
    searchTags: ["ai", "юрист", "замена"]
  },
  // ... другие вопросы
];
```

#### Дизайн элементов
- **Карточка вопроса**: Glassmorphism с мерцающей рамкой и неоновым свечением
- **Иконка**: Серебристая с анимацией поворота при раскрытии
- **Анимация раскрытия**: Плавное увеличение высоты + fade-in контента
- **Неоновые эффекты**:
  - **Hover**: Фиолетово-лазурное свечение по периметру карточки
  - **Active**: Пульсирующее свечение с градиентным переходом
  - **Expanded**: Мягкое внутреннее свечение контента

### 4. TrustBlock

#### Логотипы партнеров
```css
.partner-logo {
  filter: grayscale(100%) brightness(0.7);
  transition: all 0.3s ease;
}

.partner-logo:hover {
  filter: grayscale(0%) brightness(1);
  transform: scale(1.05);
}

/* Мерцающий эффект */
.partner-logo::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(199, 199, 204, 0.3), transparent);
  animation: shimmerSweep 3s infinite;
}
```

#### Отзывы
- **Формат**: Минималистичные карточки с аватарами
- **Анимация**: Автоматическая карусель с паузой при hover
- **Стиль**: Glassmorphism с тонкими тенями

## Data Models

### ThemeConfig
```typescript
interface ThemeConfig {
  mode: 'dark' | 'light';
  colors: {
    primary: ColorPalette;
    accent: ColorPalette;
    background: ColorPalette;
    text: ColorPalette;
  };
  animations: {
    shimmer: AnimationConfig;
    float: AnimationConfig;
    glow: AnimationConfig;
  };
}

interface ColorPalette {
  50: string;
  100: string;
  // ... до 900
  shimmer: string; // Градиент для мерцания
}
```

### ComponentVariants
```typescript
interface ButtonVariant {
  name: string;
  baseClasses: string;
  shimmerEffect: boolean;
  glowEffect: boolean;
  hoverScale: number;
}

interface CardVariant {
  name: string;
  background: string;
  border: string;
  shadow: string;
  backdropBlur: string;
}
```

## Error Handling

### Анимации и производительность
```javascript
// Проверка поддержки анимаций
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

const getAnimationConfig = () => ({
  shimmer: prefersReducedMotion.matches ? false : true,
  particles: prefersReducedMotion.matches ? false : true,
  transitions: prefersReducedMotion.matches ? 'none' : 'all 0.3s ease'
});
```

### Fallback для старых браузеров
```css
/* Fallback для backdrop-filter */
@supports not (backdrop-filter: blur(10px)) {
  .glass-effect {
    background: rgba(255, 255, 255, 0.9);
  }
}

/* Fallback для CSS Grid */
@supports not (display: grid) {
  .grid-layout {
    display: flex;
    flex-wrap: wrap;
  }
}
```

## Testing Strategy

### Визуальное тестирование
1. **Кроссбраузерность**: Chrome, Safari, Firefox, Edge
2. **Адаптивность**: 320px - 2560px
3. **Темы**: Темная (основная) и светлая (fallback)
4. **Анимации**: Проверка плавности на 60fps

### Производительность
```javascript
// Мониторинг FPS анимаций
const performanceMonitor = {
  measureFPS: () => {
    let frames = 0;
    const startTime = performance.now();
    
    function countFrames() {
      frames++;
      if (performance.now() - startTime < 1000) {
        requestAnimationFrame(countFrames);
      } else {
        console.log(`FPS: ${frames}`);
      }
    }
    requestAnimationFrame(countFrames);
  }
};
```

### Accessibility тестирование
1. **Контрастность**: WCAG AA (4.5:1 для обычного текста)
2. **Клавиатурная навигация**: Tab, Enter, Space, Escape
3. **Screen readers**: VoiceOver, NVDA
4. **Reduced motion**: Отключение анимаций по запросу

## Implementation Details

### Неоновые эффекты свечения

#### Базовое неоновое свечение
```css
@keyframes neonPulse {
  0%, 100% { 
    box-shadow: 
      0 0 5px rgba(139, 92, 246, 0.3),
      0 0 10px rgba(139, 92, 246, 0.2),
      0 0 15px rgba(139, 92, 246, 0.1);
  }
  50% {
    box-shadow: 
      0 0 10px rgba(139, 92, 246, 0.6),
      0 0 20px rgba(139, 92, 246, 0.4),
      0 0 30px rgba(139, 92, 246, 0.2),
      0 0 40px rgba(6, 182, 212, 0.1);
  }
}

@keyframes neonGradientGlow {
  0% { 
    box-shadow: 
      0 0 5px rgba(139, 92, 246, 0.4),
      0 0 10px rgba(139, 92, 246, 0.3);
  }
  25% {
    box-shadow: 
      0 0 8px rgba(167, 139, 250, 0.5),
      0 0 15px rgba(167, 139, 250, 0.3),
      0 0 25px rgba(139, 92, 246, 0.2);
  }
  50% {
    box-shadow: 
      0 0 10px rgba(6, 182, 212, 0.6),
      0 0 20px rgba(6, 182, 212, 0.4),
      0 0 30px rgba(6, 182, 212, 0.2);
  }
  75% {
    box-shadow: 
      0 0 8px rgba(34, 211, 238, 0.5),
      0 0 15px rgba(34, 211, 238, 0.3),
      0 0 25px rgba(6, 182, 212, 0.2);
  }
  100% { 
    box-shadow: 
      0 0 5px rgba(139, 92, 246, 0.4),
      0 0 10px rgba(139, 92, 246, 0.3);
  }
}

.neon-glow-base {
  border: 1px solid rgba(139, 92, 246, 0.3);
  animation: neonPulse 3s ease-in-out infinite;
  transition: all 0.3s ease;
}

.neon-glow-base:hover {
  border-color: rgba(139, 92, 246, 0.6);
  animation: neonGradientGlow 2s ease-in-out infinite;
}

.neon-glow-base:focus {
  border-color: rgba(6, 182, 212, 0.8);
  box-shadow: 
    0 0 15px rgba(139, 92, 246, 0.8),
    0 0 25px rgba(6, 182, 212, 0.6),
    0 0 35px rgba(139, 92, 246, 0.4),
    inset 0 0 10px rgba(139, 92, 246, 0.1);
  animation: neonGradientGlow 1.5s ease-in-out infinite;
}
```

#### Интерактивное поле ввода с неоновым свечением
```css
.smart-search-input {
  background: rgba(26, 26, 26, 0.8);
  backdrop-filter: blur(20px);
  border: 2px solid transparent;
  border-radius: 16px;
  padding: 20px 24px;
  font-size: 18px;
  color: #E5E5EA;
  position: relative;
  overflow: hidden;
}

.smart-search-input::before {
  content: '';
  position: absolute;
  top: -2px;
  left: -2px;
  right: -2px;
  bottom: -2px;
  background: linear-gradient(45deg, #8B5CF6, #06B6D4, #A78BFA, #22D3EE);
  background-size: 300% 300%;
  border-radius: 18px;
  z-index: -1;
  animation: neonBorderFlow 4s ease-in-out infinite;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.smart-search-input:hover::before {
  opacity: 0.6;
}

.smart-search-input:focus::before {
  opacity: 1;
  animation: neonBorderFlow 2s ease-in-out infinite;
}

@keyframes neonBorderFlow {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}
```

#### FAQ карточки с неоновым свечением
```css
.faq-card {
  background: rgba(42, 42, 42, 0.6);
  backdrop-filter: blur(15px);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 12px;
  padding: 24px;
  position: relative;
  transition: all 0.4s ease;
}

.faq-card::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border-radius: 12px;
  padding: 1px;
  background: linear-gradient(135deg, 
    rgba(139, 92, 246, 0.3), 
    rgba(6, 182, 212, 0.3),
    rgba(139, 92, 246, 0.3)
  );
  mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  mask-composite: exclude;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.faq-card:hover {
  transform: translateY(-2px);
  box-shadow: 
    0 8px 25px rgba(139, 92, 246, 0.15),
    0 4px 15px rgba(6, 182, 212, 0.1);
}

.faq-card:hover::after {
  opacity: 1;
  animation: neonPulse 2s ease-in-out infinite;
}
```

### Мерцающие эффекты
```css
@keyframes silverShimmer {
  0% { 
    background-position: -200% center;
    box-shadow: 0 0 0 rgba(199, 199, 204, 0);
  }
  50% {
    background-position: 200% center;
    box-shadow: 0 0 20px rgba(199, 199, 204, 0.3);
  }
  100% { 
    background-position: -200% center;
    box-shadow: 0 0 0 rgba(199, 199, 204, 0);
  }
}

.shimmer-silver {
  background: linear-gradient(
    90deg,
    #2a2a2a 0%,
    #8E8E93 25%,
    #C7C7CC 50%,
    #8E8E93 75%,
    #2a2a2a 100%
  );
  background-size: 200% 100%;
  animation: silverShimmer 3s ease-in-out infinite;
}
```

### Glassmorphism компоненты
```css
.glass-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.glass-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.3),
    transparent
  );
}
```

### Адаптивная типографика
```css
.hero-title {
  font-size: clamp(3rem, 8vw, 6rem);
  font-weight: 700;
  line-height: 1.1;
  letter-spacing: -0.02em;
  background: linear-gradient(
    135deg,
    #007AFF 0%,
    #40A9FF 25%,
    #C7C7CC 50%,
    #40A9FF 75%,
    #007AFF 100%
  );
  background-size: 300% 300%;
  background-clip: text;
  -webkit-background-clip: text;
  color: transparent;
  animation: gradientShift 4s ease-in-out infinite;
}
```

#### Кнопки с неоновым свечением
```css
.neon-button {
  background: rgba(26, 26, 26, 0.8);
  backdrop-filter: blur(20px);
  border: 2px solid rgba(139, 92, 246, 0.4);
  border-radius: 12px;
  padding: 16px 32px;
  color: #E5E5EA;
  font-weight: 600;
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
}

.neon-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, 
    transparent, 
    rgba(139, 92, 246, 0.4), 
    rgba(6, 182, 212, 0.4), 
    transparent
  );
  transition: left 0.6s ease;
}

.neon-button:hover {
  border-color: rgba(139, 92, 246, 0.8);
  box-shadow: 
    0 0 15px rgba(139, 92, 246, 0.4),
    0 0 25px rgba(6, 182, 212, 0.2),
    inset 0 0 15px rgba(139, 92, 246, 0.1);
  transform: translateY(-2px);
}

.neon-button:hover::before {
  left: 100%;
}

.neon-button:active {
  transform: translateY(0);
  box-shadow: 
    0 0 20px rgba(139, 92, 246, 0.6),
    0 0 30px rgba(6, 182, 212, 0.4),
    inset 0 0 20px rgba(139, 92, 246, 0.2);
}
```

### Интерактивные элементы
```javascript
// Умное поле поиска с подсказками
const SmartSearchInput = () => {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [isActive, setIsActive] = useState(false);

  const handleInputChange = useCallback(
    debounce((value) => {
      if (value.length > 2) {
        const filtered = suggestionData.filter(item =>
          item.toLowerCase().includes(value.toLowerCase())
        );
        setSuggestions(filtered.slice(0, 5));
      } else {
        setSuggestions([]);
      }
    }, 300),
    []
  );

  return (
    <motion.div
      className="search-container"
      animate={isActive ? "active" : "inactive"}
      variants={searchVariants}
    >
      <input
        className="search-input shimmer-silver"
        placeholder="Задайте вопрос AI-юристу..."
        onChange={(e) => handleInputChange(e.target.value)}
        onFocus={() => setIsActive(true)}
        onBlur={() => setIsActive(false)}
      />
      <AnimatePresence>
        {suggestions.length > 0 && (
          <motion.div
            className="suggestions-dropdown"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
          >
            {suggestions.map((suggestion, index) => (
              <motion.div
                key={index}
                className="suggestion-item"
                whileHover={{ backgroundColor: "rgba(0, 122, 255, 0.1)" }}
              >
                {suggestion}
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};
```

## Performance Optimization

### Lazy Loading анимаций
```javascript
const useIntersectionObserver = (ref, options) => {
  const [isIntersecting, setIsIntersecting] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(([entry]) => {
      setIsIntersecting(entry.isIntersecting);
    }, options);

    if (ref.current) {
      observer.observe(ref.current);
    }

    return () => observer.disconnect();
  }, [ref, options]);

  return isIntersecting;
};

// Использование для анимаций
const AnimatedSection = ({ children }) => {
  const ref = useRef();
  const isVisible = useIntersectionObserver(ref, { threshold: 0.1 });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 50 }}
      animate={isVisible ? { opacity: 1, y: 0 } : { opacity: 0, y: 50 }}
      transition={{ duration: 0.6 }}
    >
      {children}
    </motion.div>
  );
};
```

### Оптимизация мерцающих эффектов
```javascript
// Управление анимациями через CSS переменные
const updateShimmerIntensity = (intensity) => {
  document.documentElement.style.setProperty(
    '--shimmer-opacity',
    intensity.toString()
  );
};

// Адаптация к производительности устройства
const getDevicePerformance = () => {
  const connection = navigator.connection;
  const memory = navigator.deviceMemory;
  
  if (memory && memory < 4) return 'low';
  if (connection && connection.effectiveType === '2g') return 'low';
  return 'high';
};
```