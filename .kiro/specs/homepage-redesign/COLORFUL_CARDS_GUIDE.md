# Руководство по цветным карточкам

## 🎨 Проблема
Серые карточки выглядят скучно и не соответствуют яркому Apple Neon стилю.

## ✨ Решение
Яркие цветные карточки с градиентами и неоновыми эффектами!

## 🌈 Доступные цвета карточек

### 1. Blue (Синий) - по умолчанию
```jsx
<div className="card">
  {/* Автоматически голубой градиент */}
</div>
```

### 2. Purple (Фиолетовый)
```jsx
<div className="card card-purple">
  <h3>Заголовок</h3>
  <p>Контент</p>
</div>
```

### 3. Pink (Розовый)
```jsx
<div className="card card-pink">
  <h3>Заголовок</h3>
  <p>Контент</p>
</div>
```

### 4. Cyan (Циан)
```jsx
<div className="card card-cyan">
  <h3>Заголовок</h3>
  <p>Контент</p>
</div>
```

### 5. Orange (Оранжевый)
```jsx
<div className="card card-orange">
  <h3>Заголовок</h3>
  <p>Контент</p>
</div>
```

### 6. Green (Зеленый)
```jsx
<div className="card card-green">
  <h3>Заголовок</h3>
  <p>Контент</p>
</div>
```

## 📊 Пример использования в сетке

```jsx
const features = [
  { title: "Мгновенно", color: "blue", icon: "⚡" },
  { title: "Экспертно", color: "purple", icon: "⚖️" },
  { title: "Безопасно", color: "cyan", icon: "🛡️" },
  { title: "Выгодно", color: "green", icon: "💰" }
];

<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
  {features.map((feature, index) => (
    <div key={index} className={`card card-${feature.color} p-6`}>
      <div className="text-4xl mb-4">{feature.icon}</div>
      <h3 className="text-xl font-bold mb-2">{feature.title}</h3>
      <p className="text-gray-700">Описание</p>
    </div>
  ))}
</div>
```

## 🎯 Рекомендации по использованию

### Для разных типов контента:

**Информационные карточки** → Blue (синий)
```jsx
<div className="card card-blue">
  <h3>Информация</h3>
</div>
```

**Премиум функции** → Purple (фиолетовый)
```jsx
<div className="card card-purple">
  <h3>Премиум</h3>
</div>
```

**Важные уведомления** → Pink (розовый)
```jsx
<div className="card card-pink">
  <h3>Важно!</h3>
</div>
```

**Технические детали** → Cyan (циан)
```jsx
<div className="card card-cyan">
  <h3>Технологии</h3>
</div>
```

**Предупреждения** → Orange (оранжевый)
```jsx
<div className="card card-orange">
  <h3>Внимание</h3>
</div>
```

**Успех/Подтверждение** → Green (зеленый)
```jsx
<div className="card card-green">
  <h3>Успешно</h3>
</div>
```

## 🎨 Цветовая палитра

### Blue (Синий)
- Основной: #007AFF
- Светлый: #64D2FF
- Использование: Информация, основные действия

### Purple (Фиолетовый)
- Основной: #BF5AF2
- Светлый: #AF52DE
- Использование: Премиум, креативность

### Pink (Розовый)
- Основной: #FF2D55
- Светлый: #FF375F
- Использование: Важное, акценты

### Cyan (Циан)
- Основной: #32ADE6
- Светлый: #00C7BE
- Использование: Технологии, инновации

### Orange (Оранжевый)
- Основной: #FF9500
- Светлый: #FF9F0A
- Использование: Предупреждения, энергия

### Green (Зеленый)
- Основной: #34C759
- Светлый: #30D158
- Использование: Успех, подтверждение

## 🌟 Эффекты при hover

Все карточки имеют:
- Подъем на 6px
- Увеличение на 2%
- Яркое неоновое свечение
- Усиление цвета границы

## 📱 Адаптивность

Карточки автоматически адаптируются:
- Desktop: Полные эффекты
- Tablet: Упрощенные эффекты
- Mobile: Минимальные эффекты для производительности

## ✨ Готово!

Теперь вместо скучных серых карточек у вас яркие цветные с неоновыми эффектами! 🎨
