# Руководство по использованию тем

## 🎨 Две темы

### 🌙 Темная тема (по умолчанию)
- **НЕ ТРОГАЕМ!** Уже реализована и работает отлично
- Глубокий черный фон (#0a0a0a)
- Яркие фиолетово-циановые неоновые эффекты
- Серебристый текст
- Интенсивное свечение

### ☀️ Светлая тема (Apple Neon Style)
- **НОВАЯ!** Только что добавлена
- Чистый белый фон (#FFFFFF)
- Яркие неоновые цвета Apple (Blue, Purple, Pink, Cyan)
- Черный текст для максимального контраста
- Glassmorphism с blur 40px
- Живые градиенты

## 🔄 Переключение тем

### Автоматическое переключение
Добавлен компонент `ThemeToggle` в правый верхний угол главной страницы.

**Как это работает:**
1. Пользователь кликает на переключатель
2. Тема меняется с анимацией
3. Выбор сохраняется в localStorage
4. При следующем визите применяется сохраненная тема

### Добавить переключатель на другие страницы

```jsx
import ThemeToggle from '../components/ThemeToggle';

// В любом месте компонента
<ThemeToggle />
```

## 🎨 Как работают стили

### Темная тема (по умолчанию)
```css
/* Применяется автоматически */
:root,
.dark {
  --bg-primary: #0a0a0a;
  --neon-purple: #8B5CF6;
  /* ... остальные переменные */
}
```

### Светлая тема
```css
/* Применяется когда добавлен класс .light */
.light {
  --apple-bg-primary: #FFFFFF;
  --apple-blue: #007AFF;
  /* ... остальные переменные */
}
```

## 📦 Готовые компоненты для светлой темы

### Кнопки
```jsx
// Синяя кнопка Apple
<button className="apple-button-primary">
  Кнопка
</button>

// Градиентная кнопка
<button className="apple-button-gradient">
  Градиент
</button>

// Фиолетовая кнопка
<button className="apple-button-purple">
  Фиолетовая
</button>
```

### Карточки
```jsx
// Стеклянная карточка
<div className="apple-glass-card">
  <h3>Заголовок</h3>
  <p>Контент</p>
</div>

// Карточка с фичей
<div className="apple-feature-card">
  <div className="apple-feature-icon">
    <Icon />
  </div>
  <h3 className="apple-feature-title">Заголовок</h3>
  <p className="apple-feature-description">Описание</p>
</div>
```

### Input поля
```jsx
// Apple стиль input
<input 
  type="text"
  className="apple-input"
  placeholder="Введите текст..."
/>
```

### Градиентный текст
```jsx
// Обычный градиент
<h1 className="apple-gradient-text">
  АДВАКОД
</h1>

// Радужный градиент
<h1 className="apple-gradient-text-rainbow">
  АДВАКОД
</h1>
```

### Типографика
```jsx
// Большой заголовок
<h1 className="apple-display-large">Заголовок</h1>

// Средний заголовок
<h2 className="apple-display-medium">Подзаголовок</h2>

// Заголовок 1
<h3 className="apple-title-1">Заголовок</h3>

// Основной текст
<p className="apple-body">Текст</p>

// Большой текст
<p className="apple-body-large">Большой текст</p>
```

## 🎬 Анимации

### Градиентный сдвиг
```jsx
<div className="animate-gradient-shift">
  Анимированный градиент
</div>
```

### Mesh градиент фон
```jsx
<div className="apple-hero">
  <div className="apple-mesh-gradient" />
  {/* Контент */}
</div>
```

## 🚀 Примеры использования

### Hero Section
```jsx
<section className="apple-hero">
  <div className="apple-mesh-gradient" />
  
  <div className="relative z-10 text-center py-24">
    <h1 className="apple-display-large apple-gradient-text-rainbow mb-6">
      АДВАКОД
    </h1>
    <p className="apple-body-large mb-8">
      Ваш персональный AI юрист-консультант
    </p>
    <button className="apple-button-gradient">
      Начать бесплатно
    </button>
  </div>
</section>
```

### Feature Cards Grid
```jsx
<div className="grid grid-cols-1 md:grid-cols-3 gap-8">
  {features.map((feature, index) => (
    <div key={index} className="apple-feature-card">
      <div className="apple-feature-icon bg-gradient-to-br from-blue-500 to-purple-500">
        {feature.icon}
      </div>
      <h3 className="apple-feature-title">{feature.title}</h3>
      <p className="apple-feature-description">{feature.description}</p>
    </div>
  ))}
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
  <button className="absolute right-4 top-1/2 -translate-y-1/2">
    <SearchIcon className="w-6 h-6 text-blue-500" />
  </button>
</div>
```

## ✅ Чек-лист для адаптации страниц

### Для каждой страницы:

1. **Добавить ThemeToggle**
```jsx
import ThemeToggle from '../components/ThemeToggle';

// В компоненте
<div className="fixed top-6 right-6 z-50">
  <ThemeToggle />
</div>
```

2. **Обновить классы для светлой темы**
- Карточки: добавить `apple-glass-card` или оставить `card` (работает автоматически)
- Кнопки: добавить `apple-button-*` или оставить `btn-*` (работает автоматически)
- Input: добавить `apple-input` или оставить `input-field` (работает автоматически)

3. **Добавить градиентный текст для заголовков**
```jsx
<h1 className="apple-gradient-text">Заголовок</h1>
```

4. **Проверить контрастность**
- Текст должен быть читаемым в обеих темах
- Используйте `text-gray-900 dark:text-gray-100` для адаптивного текста

## 🎯 Текущий статус

### ✅ Готово:
- [x] CSS стили для светлой темы
- [x] Компонент ThemeToggle
- [x] Добавлен на главную страницу (Home)
- [x] Все компоненты адаптированы автоматически

### 📝 Нужно добавить ThemeToggle на:
- [ ] Chat page
- [ ] Pricing page
- [ ] Login page
- [ ] Register page
- [ ] Profile page
- [ ] Admin pages

### 💡 Как добавить на другие страницы:

**Вариант 1: Фиксированная позиция (как на Home)**
```jsx
<div className="fixed top-6 right-6 z-50">
  <ThemeToggle />
</div>
```

**Вариант 2: В навигации**
```jsx
<nav className="flex items-center justify-between">
  <div>Logo</div>
  <div className="flex items-center gap-4">
    <Link to="/pricing">Тарифы</Link>
    <ThemeToggle />
    <button>Войти</button>
  </div>
</nav>
```

## 🎨 Цветовая палитра

### Темная тема (НЕ ТРОГАЕМ)
- Фон: #0a0a0a, #1a1a1a, #2a2a2a
- Неон: #8B5CF6 (purple), #06B6D4 (cyan)
- Текст: #E5E5EA, #C7C7CC, #8E8E93

### Светлая тема (Apple Neon)
- Фон: #FFFFFF, #FAFAFA, #F5F5F7
- Неон: #007AFF (blue), #BF5AF2 (purple), #FF2D55 (pink), #32ADE6 (cyan)
- Текст: #000000, #86868B, #C7C7CC

## 🚀 Готово к использованию!

Светлая тема полностью готова! Просто кликните на переключатель в правом верхнем углу главной страницы и наслаждайтесь Apple Neon дизайном! 🍎✨
