# Пример реализации Apple Neon Theme

## 🎨 Полный пример Hero Section

```jsx
import React from 'react';
import { motion } from 'framer-motion';
import { ArrowRight, Sparkles, Zap } from 'lucide-react';
import ThemeToggle from '../components/ThemeToggle';

const AppleHeroExample = () => {
  return (
    <div className="apple-hero">
      {/* Animated mesh gradient background */}
      <div className="apple-mesh-gradient" />
      
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Sparkles className="w-6 h-6 text-blue-500" />
            <span className="apple-gradient-text text-2xl font-bold">
              АДВАКОД
            </span>
          </div>
          
          <div className="flex items-center space-x-6">
            <a href="#" className="apple-body text-gray-600 hover:text-black transition-colors">
              Главная
            </a>
            <a href="#" className="apple-body text-gray-600 hover:text-black transition-colors">
              Тарифы
            </a>
            <a href="#" className="apple-body text-gray-600 hover:text-black transition-colors">
              Чат
            </a>
            <ThemeToggle />
            <button className="apple-button-primary">
              Войти
            </button>
          </div>
        </div>
      </nav>
      
      {/* Hero Content */}
      <div className="relative z-10 flex items-center justify-center min-h-screen px-6">
        <div className="max-w-5xl mx-auto text-center">
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="inline-flex items-center space-x-2 px-4 py-2 rounded-full 
                       bg-white/50 backdrop-blur-md border border-white/60 mb-8"
          >
            <Zap className="w-4 h-4 text-blue-500" />
            <span className="text-sm font-medium text-gray-900">
              Новая версия AI-юриста уже доступна
            </span>
          </motion.div>
          
          {/* Main Title */}
          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="apple-display-large apple-gradient-text-rainbow mb-6"
          >
            АДВАКОД
          </motion.h1>
          
          {/* Subtitle */}
          <motion.p
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
            className="apple-body-large mb-12"
          >
            Ваш персональный AI юрист-консультант.<br />
            Мгновенные ответы на юридические вопросы.
          </motion.p>
          
          {/* CTA Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.6 }}
            className="flex flex-col sm:flex-row gap-4 justify-center"
          >
            <button className="apple-button-gradient flex items-center justify-center space-x-2 px-8 py-4">
              <span>Начать бесплатно</span>
              <ArrowRight className="w-5 h-5" />
            </button>
            <button className="apple-button-primary flex items-center justify-center space-x-2 px-8 py-4">
              <span>Смотреть демо</span>
            </button>
          </motion.div>
          
          {/* Search Input */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.8 }}
            className="mt-16 max-w-2xl mx-auto"
          >
            <div className="relative">
              <input
                type="text"
                placeholder="Задайте вопрос AI-юристу..."
                className="apple-input w-full text-lg py-4 px-6 pr-12"
              />
              <button className="absolute right-4 top-1/2 -translate-y-1/2">
                <svg className="w-6 h-6 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </button>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default AppleHeroExample;
```

## 🎯 Пример Feature Cards

```jsx
const AppleFeatures = () => {
  const features = [
    {
      icon: '🔍',
      title: 'Умный поиск',
      description: 'Мгновенный поиск по всей базе российского законодательства',
      gradient: 'from-blue-500 to-cyan-500'
    },
    {
      icon: '📄',
      title: 'Анализ документов',
      description: 'Проверка договоров и юридических документов за секунды',
      gradient: 'from-purple-500 to-pink-500'
    },
    {
      icon: '💬',
      title: 'AI консультант',
      description: 'Персональный юрист доступен 24/7 для ответов на вопросы',
      gradient: 'from-orange-500 to-red-500'
    }
  ];

  return (
    <section className="py-24 px-6">
      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <div className="text-center mb-16">
          <h2 className="apple-display-medium apple-gradient-text mb-4">
            Почему выбирают АДВАКОД?
          </h2>
          <p className="apple-body-large">
            Мощная технология для решения ваших юридических задач
          </p>
        </div>
        
        {/* Feature Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: index * 0.1 }}
              viewport={{ once: true }}
              className="apple-feature-card"
            >
              <div className={`apple-feature-icon bg-gradient-to-br ${feature.gradient}`}>
                <span className="text-3xl">{feature.icon}</span>
              </div>
              <h3 className="apple-title-1 mb-3">
                {feature.title}
              </h3>
              <p className="apple-body text-gray-600">
                {feature.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};
```

## 💳 Пример Pricing Cards

```jsx
const ApplePricing = () => {
  const plans = [
    {
      name: 'Базовый',
      price: '0',
      period: 'бесплатно',
      features: [
        '10 запросов в месяц',
        'Базовые консультации',
        'Email поддержка'
      ],
      gradient: 'from-gray-400 to-gray-500',
      popular: false
    },
    {
      name: 'Профессиональный',
      price: '990',
      period: 'месяц',
      features: [
        'Безлимитные запросы',
        'Анализ документов',
        'Приоритетная поддержка',
        'API доступ'
      ],
      gradient: 'from-blue-500 to-purple-500',
      popular: true
    },
    {
      name: 'Бизнес',
      price: '2990',
      period: 'месяц',
      features: [
        'Все из Профессионального',
        'Персональный менеджер',
        'Интеграция с 1С',
        'SLA 99.9%'
      ],
      gradient: 'from-purple-500 to-pink-500',
      popular: false
    }
  ];

  return (
    <section className="py-24 px-6 bg-gradient-to-b from-white to-gray-50">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="apple-display-medium apple-gradient-text mb-4">
            Выберите свой тариф
          </h2>
          <p className="apple-body-large">
            Начните с бесплатного плана и обновите когда будете готовы
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {plans.map((plan, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: index * 0.1 }}
              viewport={{ once: true }}
              className={`
                apple-glass-card p-8 relative
                ${plan.popular ? 'ring-2 ring-blue-500 scale-105' : ''}
              `}
            >
              {plan.popular && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                  <span className="bg-gradient-to-r from-blue-500 to-purple-500 text-white px-4 py-1 rounded-full text-sm font-semibold">
                    Популярный
                  </span>
                </div>
              )}
              
              <div className="text-center mb-8">
                <h3 className="apple-title-1 mb-4">{plan.name}</h3>
                <div className="flex items-baseline justify-center mb-2">
                  <span className="text-5xl font-bold">{plan.price}</span>
                  <span className="text-gray-600 ml-2">₽</span>
                </div>
                <p className="text-gray-600">/ {plan.period}</p>
              </div>
              
              <ul className="space-y-4 mb-8">
                {plan.features.map((feature, i) => (
                  <li key={i} className="flex items-center space-x-3">
                    <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    <span className="apple-body">{feature}</span>
                  </li>
                ))}
              </ul>
              
              <button className={`
                w-full py-3 rounded-xl font-semibold transition-all
                ${plan.popular 
                  ? 'apple-button-gradient' 
                  : 'apple-button-primary'
                }
              `}>
                Выбрать план
              </button>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};
```

## 🎨 Пример FAQ Section

```jsx
const AppleFAQ = () => {
  const [openIndex, setOpenIndex] = useState(null);
  
  const faqs = [
    {
      question: 'Как работает AI-юрист?',
      answer: 'Наш AI использует передовые модели машинного обучения для анализа юридических документов и предоставления консультаций на основе российского законодательства.'
    },
    {
      question: 'Насколько безопасны мои данные?',
      answer: 'Мы используем шифрование на уровне банков и не передаем ваши данные третьим лицам. Все данные хранятся на серверах в России в соответствии с 152-ФЗ.'
    },
    {
      question: 'Могу ли я отменить подписку?',
      answer: 'Да, вы можете отменить подписку в любое время в личном кабинете. Возврат средств возможен в течение 14 дней.'
    }
  ];

  return (
    <section className="py-24 px-6">
      <div className="max-w-3xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="apple-display-medium apple-gradient-text mb-4">
            Часто задаваемые вопросы
          </h2>
        </div>
        
        <div className="space-y-4">
          {faqs.map((faq, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: index * 0.1 }}
              viewport={{ once: true }}
              className="apple-glass-card overflow-hidden"
            >
              <button
                onClick={() => setOpenIndex(openIndex === index ? null : index)}
                className="w-full text-left p-6 flex items-center justify-between"
              >
                <span className="apple-title-2">{faq.question}</span>
                <motion.svg
                  animate={{ rotate: openIndex === index ? 180 : 0 }}
                  transition={{ duration: 0.3 }}
                  className="w-6 h-6 text-blue-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </motion.svg>
              </button>
              
              <motion.div
                initial={false}
                animate={{
                  height: openIndex === index ? 'auto' : 0,
                  opacity: openIndex === index ? 1 : 0
                }}
                transition={{ duration: 0.3 }}
                className="overflow-hidden"
              >
                <div className="px-6 pb-6">
                  <p className="apple-body text-gray-600">
                    {faq.answer}
                  </p>
                </div>
              </motion.div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};
```

## 🚀 Использование

### 1. Добавить ThemeToggle в навигацию
```jsx
import ThemeToggle from './components/ThemeToggle';

// В компоненте навигации
<ThemeToggle />
```

### 2. Применить классы к существующим компонентам
```jsx
// Вместо обычных классов используйте Apple классы
<div className="apple-glass-card">
  <h3 className="apple-title-1">Заголовок</h3>
  <p className="apple-body">Текст</p>
  <button className="apple-button-gradient">Кнопка</button>
</div>
```

### 3. Использовать градиентный текст
```jsx
<h1 className="apple-gradient-text-rainbow">
  АДВАКОД
</h1>
```

## ✨ Готово!

Все компоненты готовы к использованию в стиле Apple с яркими неоновыми эффектами! 🍎✨
