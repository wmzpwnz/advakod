import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  HelpCircle, 
  Search, 
  BookOpen, 
  Video, 
  MessageCircle,
  ExternalLink,
  ChevronRight,
  ChevronDown,
  Star,
  Clock,
  User,
  Tag,
  X,
  Download,
  Share2,
  Bookmark,
  ThumbsUp,
  ThumbsDown
} from 'lucide-react';
import AdminTourManager from './AdminTourManager';
import VideoGuideLibrary from './VideoGuideLibrary';

const HelpSystem = ({ isOpen, onClose }) => {
  const [activeTab, setActiveTab] = useState('documentation');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [expandedSections, setExpandedSections] = useState(new Set());
  const [bookmarkedItems, setBookmarkedItems] = useState([]);
  const [showTours, setShowTours] = useState(false);
  const [showVideoGuides, setShowVideoGuides] = useState(false);

  // Load bookmarks from localStorage
  useEffect(() => {
    const bookmarks = JSON.parse(localStorage.getItem('helpBookmarks') || '[]');
    setBookmarkedItems(bookmarks);
  }, []);

  // Documentation structure
  const documentation = [
    {
      id: 'getting-started',
      title: 'Начало работы',
      category: 'basics',
      icon: BookOpen,
      description: 'Основы работы с админ-панелью',
      lastUpdated: '2024-10-26',
      readTime: 5,
      rating: 4.8,
      sections: [
        {
          id: 'first-login',
          title: 'Первый вход в систему',
          content: `
## Первый вход в админ-панель

### Получение доступа
1. Получите учетные данные от супер-администратора
2. Перейдите по адресу \`/admin\` или нажмите кнопку "Админ-панель"
3. Введите email и пароль
4. При первом входе рекомендуется сменить пароль

### Настройка профиля
- Обновите личную информацию
- Настройте уведомления
- Выберите тему оформления
- Настройте горячие клавиши

### Знакомство с интерфейсом
- Изучите боковое меню навигации
- Ознакомьтесь с главным дашбордом
- Попробуйте командную палитру (Ctrl+K)
- Пройдите интерактивный тур
          `
        },
        {
          id: 'navigation',
          title: 'Навигация по системе',
          content: `
## Навигация по админ-панели

### Боковое меню
Основной способ навигации между модулями:
- **Дашборд** - обзор системы
- **Пользователи** - управление пользователями
- **Документы** - управление RAG системой
- **Роли** - настройка прав доступа
- **Модерация** - система модерации ИИ
- **Маркетинг** - маркетинговые инструменты
- **Проект** - управление проектом
- **Уведомления** - система алертов
- **Аналитика** - бизнес-аналитика
- **Бэкапы** - резервное копирование
- **Система** - системные настройки

### Горячие клавиши
- \`Ctrl+K\` - командная палитра
- \`Ctrl+B\` - переключить боковую панель
- \`Ctrl+H\` - перейти на главную
- \`Ctrl+Shift+H\` - открыть справку
- \`Escape\` - закрыть модальные окна

### Поиск
Используйте поиск в верхней части боковой панели для быстрого доступа к модулям.
          `
        }
      ]
    },
    {
      id: 'user-management',
      title: 'Управление пользователями',
      category: 'modules',
      icon: User,
      description: 'Полное руководство по работе с пользователями',
      lastUpdated: '2024-10-26',
      readTime: 15,
      rating: 4.9,
      sections: [
        {
          id: 'user-overview',
          title: 'Обзор модуля',
          content: `
## Модуль управления пользователями

### Основные функции
- Просмотр списка всех пользователей
- Детальная информация о каждом пользователе
- Поиск и фильтрация пользователей
- Редактирование профилей пользователей
- Массовые операции
- Экспорт данных пользователей
- Аналитика пользовательской активности

### Интерфейс модуля
Модуль состоит из нескольких основных частей:
1. **Панель поиска и фильтров** - для быстрого поиска пользователей
2. **Список пользователей** - таблица с основной информацией
3. **Панель массовых операций** - для работы с группами пользователей
4. **Модальные окна** - для редактирования и детального просмотра

### Права доступа
- **super_admin**: полный доступ ко всем функциям
- **admin**: доступ ко всем функциям кроме управления другими админами
- **analyst**: только просмотр и аналитика
          `
        },
        {
          id: 'user-search',
          title: 'Поиск и фильтрация',
          content: `
## Поиск и фильтрация пользователей

### Быстрый поиск
Введите в поле поиска:
- Email адрес пользователя
- Имя или фамилию
- ID пользователя

### Расширенные фильтры
Доступны следующие фильтры:
- **Статус**: активные, неактивные, заблокированные
- **Роль**: обычные пользователи, модераторы, администраторы
- **Дата регистрации**: за последний день, неделю, месяц, год
- **Активность**: активные за период, неактивные
- **Подписка**: бесплатные, премиум, корпоративные
- **Регион**: по географическому положению

### Сохранение фильтров
1. Настройте нужные фильтры
2. Нажмите "Сохранить фильтр"
3. Дайте название фильтру
4. Фильтр появится в быстром доступе

### Горячие клавиши
- \`Ctrl+F\` - фокус на поле поиска
- \`Ctrl+Shift+F\` - открыть расширенные фильтры
- \`Escape\` - очистить поиск и фильтры
          `
        }
      ]
    },
    {
      id: 'moderation',
      title: 'Система модерации',
      category: 'modules',
      icon: MessageCircle,
      description: 'Руководство по модерации ответов ИИ',
      lastUpdated: '2024-10-26',
      readTime: 20,
      rating: 4.7,
      sections: [
        {
          id: 'moderation-basics',
          title: 'Основы модерации',
          content: `
## Система модерации АДВАКОД

### Цель модерации
Система модерации предназначена для:
- Контроля качества ответов ИИ
- Обучения и улучшения модели
- Обеспечения безопасности пользователей
- Поддержания высоких стандартов сервиса

### Процесс модерации
1. **Получение задания** из очереди модерации
2. **Анализ вопроса** пользователя и контекста
3. **Оценка ответа ИИ** по установленным критериям
4. **Выставление оценки** от 1 до 10 звезд
5. **Написание комментария** с обоснованием оценки
6. **Отправка результата** для обучения системы

### Критерии оценки
- **Правильность** юридической информации
- **Полнота** ответа на вопрос
- **Понятность** изложения для пользователя
- **Актуальность** ссылок на законодательство
- **Практическая применимость** советов
          `
        },
        {
          id: 'rating-system',
          title: 'Система оценок',
          content: `
## Система оценок модерации

### Шкала оценок (1-10 звезд)
- **1-2 звезды**: Неправильный или вредный ответ
  - Содержит фактические ошибки
  - Может навредить пользователю
  - Противоречит законодательству

- **3-4 звезды**: Частично правильный, но неполный
  - Содержит правильную информацию, но неполную
  - Упускает важные аспекты вопроса
  - Требует значительных дополнений

- **5-6 звезд**: Правильный, но может быть улучшен
  - Основная информация верна
  - Можно добавить детали или примеры
  - Стиль изложения можно улучшить

- **7-8 звезд**: Хороший и полезный ответ
  - Содержит правильную и полную информацию
  - Хорошо структурирован
  - Практически применим

- **9-10 звезд**: Отличный, исчерпывающий ответ
  - Полностью отвечает на вопрос
  - Содержит дополнительные полезные детали
  - Отлично структурирован и понятен

### Обязательные комментарии
Для каждой оценки требуется комментарий:
- Объяснение причин оценки
- Конкретные проблемы или достоинства
- Предложения по улучшению
- Дополнительная информация для ИИ
          `
        }
      ]
    }
  ];

  // FAQ data
  const faqData = [
    {
      id: 'access-denied',
      question: 'Что делать, если появляется ошибка "Доступ запрещен"?',
      answer: `
Ошибка "Доступ запрещен" может возникать по нескольким причинам:

1. **Недостаточные права доступа**
   - Обратитесь к супер-администратору для назначения нужной роли
   - Проверьте свою текущую роль в профиле

2. **Истекшая сессия**
   - Выйдите из системы и войдите заново
   - Проверьте стабильность интернет-соединения

3. **Технические проблемы**
   - Очистите кэш браузера
   - Попробуйте использовать другой браузер
   - Обратитесь в техподдержку
      `,
      category: 'troubleshooting',
      tags: ['доступ', 'права', 'ошибка'],
      helpful: 45,
      notHelpful: 3
    },
    {
      id: 'slow-loading',
      question: 'Почему админ-панель медленно загружается?',
      answer: `
Медленная загрузка может быть вызвана несколькими факторами:

1. **Проблемы с интернетом**
   - Проверьте скорость интернет-соединения
   - Попробуйте перезагрузить роутер

2. **Большой объем данных**
   - Используйте фильтры для уменьшения объема
   - Увеличьте размер страницы в настройках

3. **Кэш браузера**
   - Очистите кэш и cookies
   - Обновите страницу с помощью Ctrl+F5

4. **Высокая нагрузка на сервер**
   - Попробуйте зайти позже
   - Обратитесь к администратору
      `,
      category: 'performance',
      tags: ['скорость', 'загрузка', 'производительность'],
      helpful: 32,
      notHelpful: 8
    },
    {
      id: 'notifications-not-working',
      question: 'Не приходят push-уведомления в браузере',
      answer: `
Для работы push-уведомлений необходимо:

1. **Разрешить уведомления в браузере**
   - Нажмите на иконку замка в адресной строке
   - Выберите "Разрешить" для уведомлений

2. **Проверить настройки в профиле**
   - Перейдите в настройки уведомлений
   - Убедитесь, что нужные типы уведомлений включены

3. **Проверить WebSocket соединение**
   - Индикатор подключения должен быть зеленым
   - При проблемах обновите страницу

4. **Настройки браузера**
   - Проверьте, что уведомления не заблокированы
   - Попробуйте другой браузер для тестирования
      `,
      category: 'notifications',
      tags: ['уведомления', 'push', 'браузер'],
      helpful: 28,
      notHelpful: 5
    }
  ];

  const categories = [
    { id: 'all', name: 'Все разделы' },
    { id: 'basics', name: 'Основы' },
    { id: 'modules', name: 'Модули' },
    { id: 'troubleshooting', name: 'Решение проблем' },
    { id: 'advanced', name: 'Продвинутые функции' }
  ];

  const toggleSection = (sectionId) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(sectionId)) {
      newExpanded.delete(sectionId);
    } else {
      newExpanded.add(sectionId);
    }
    setExpandedSections(newExpanded);
  };

  const toggleBookmark = (itemId) => {
    const newBookmarks = bookmarkedItems.includes(itemId)
      ? bookmarkedItems.filter(id => id !== itemId)
      : [...bookmarkedItems, itemId];
    
    setBookmarkedItems(newBookmarks);
    localStorage.setItem('helpBookmarks', JSON.stringify(newBookmarks));
  };

  const markHelpful = (faqId, helpful) => {
    // In a real app, this would send to the server
    console.log(`FAQ ${faqId} marked as ${helpful ? 'helpful' : 'not helpful'}`);
  };

  // Filter documentation based on search and category
  const filteredDocs = documentation.filter(doc => {
    const matchesSearch = doc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         doc.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || doc.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  // Filter FAQ based on search
  const filteredFAQ = faqData.filter(faq => {
    return faq.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
           faq.answer.toLowerCase().includes(searchQuery.toLowerCase()) ||
           faq.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
  });

  if (!isOpen) return null;

  return (
    <>
      <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-white dark:bg-gray-800 rounded-lg shadow-2xl w-full max-w-6xl h-[90vh] flex flex-col"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                Справочная система
              </h2>
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                Документация, видео-гайды и ответы на частые вопросы
              </p>
            </div>
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <X className="h-6 w-6" />
            </button>
          </div>

          {/* Tabs */}
          <div className="flex border-b border-gray-200 dark:border-gray-700">
            {[
              { id: 'documentation', name: 'Документация', icon: BookOpen },
              { id: 'video-guides', name: 'Видео-гайды', icon: Video },
              { id: 'tours', name: 'Интерактивные туры', icon: HelpCircle },
              { id: 'faq', name: 'FAQ', icon: MessageCircle }
            ].map(tab => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 px-6 py-3 border-b-2 transition-colors ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                      : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span>{tab.name}</span>
                </button>
              );
            })}
          </div>

          {/* Search and Filters */}
          {(activeTab === 'documentation' || activeTab === 'faq') && (
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center space-x-4">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Поиск в справке..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                
                {activeTab === 'documentation' && (
                  <select
                    value={selectedCategory}
                    onChange={(e) => setSelectedCategory(e.target.value)}
                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    {categories.map(category => (
                      <option key={category.id} value={category.id}>
                        {category.name}
                      </option>
                    ))}
                  </select>
                )}
              </div>
            </div>
          )}

          {/* Content */}
          <div className="flex-1 overflow-y-auto">
            {/* Documentation Tab */}
            {activeTab === 'documentation' && (
              <div className="p-6">
                {filteredDocs.length === 0 ? (
                  <div className="text-center py-12">
                    <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                      Документация не найдена
                    </h3>
                    <p className="text-gray-600 dark:text-gray-400">
                      Попробуйте изменить поисковый запрос или категорию
                    </p>
                  </div>
                ) : (
                  <div className="space-y-6">
                    {filteredDocs.map(doc => {
                      const Icon = doc.icon;
                      return (
                        <div key={doc.id} className="bg-gray-50 dark:bg-gray-700 rounded-lg p-6">
                          <div className="flex items-start justify-between mb-4">
                            <div className="flex items-start space-x-3">
                              <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                                <Icon className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                              </div>
                              <div>
                                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                                  {doc.title}
                                </h3>
                                <p className="text-gray-600 dark:text-gray-400 mt-1">
                                  {doc.description}
                                </p>
                                <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500 dark:text-gray-400">
                                  <div className="flex items-center space-x-1">
                                    <Clock className="h-4 w-4" />
                                    <span>{doc.readTime} мин</span>
                                  </div>
                                  <div className="flex items-center space-x-1">
                                    <Star className="h-4 w-4 text-yellow-400" />
                                    <span>{doc.rating}</span>
                                  </div>
                                  <span>Обновлено: {new Date(doc.lastUpdated).toLocaleDateString('ru-RU')}</span>
                                </div>
                              </div>
                            </div>
                            
                            <div className="flex items-center space-x-2">
                              <button
                                onClick={() => toggleBookmark(doc.id)}
                                className={`p-2 rounded-lg transition-colors ${
                                  bookmarkedItems.includes(doc.id)
                                    ? 'bg-yellow-100 dark:bg-yellow-900 text-yellow-600 dark:text-yellow-400'
                                    : 'bg-gray-100 dark:bg-gray-600 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-500'
                                }`}
                              >
                                <Bookmark className="h-4 w-4" />
                              </button>
                              <button className="p-2 bg-gray-100 dark:bg-gray-600 text-gray-600 dark:text-gray-400 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-500 transition-colors">
                                <Share2 className="h-4 w-4" />
                              </button>
                            </div>
                          </div>

                          {/* Sections */}
                          <div className="space-y-2">
                            {doc.sections.map(section => (
                              <div key={section.id}>
                                <button
                                  onClick={() => toggleSection(section.id)}
                                  className="w-full flex items-center justify-between p-3 bg-white dark:bg-gray-800 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors"
                                >
                                  <span className="font-medium text-gray-900 dark:text-white">
                                    {section.title}
                                  </span>
                                  {expandedSections.has(section.id) ? (
                                    <ChevronDown className="h-4 w-4 text-gray-400" />
                                  ) : (
                                    <ChevronRight className="h-4 w-4 text-gray-400" />
                                  )}
                                </button>
                                
                                <AnimatePresence>
                                  {expandedSections.has(section.id) && (
                                    <motion.div
                                      initial={{ height: 0, opacity: 0 }}
                                      animate={{ height: 'auto', opacity: 1 }}
                                      exit={{ height: 0, opacity: 0 }}
                                      className="overflow-hidden"
                                    >
                                      <div className="p-4 bg-white dark:bg-gray-800 rounded-lg mt-2 prose dark:prose-invert max-w-none">
                                        <div dangerouslySetInnerHTML={{ 
                                          __html: section.content.replace(/\n/g, '<br>').replace(/`([^`]+)`/g, '<code>$1</code>')
                                        }} />
                                      </div>
                                    </motion.div>
                                  )}
                                </AnimatePresence>
                              </div>
                            ))}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}

            {/* Video Guides Tab */}
            {activeTab === 'video-guides' && (
              <div className="p-6">
                <div className="text-center">
                  <Video className="h-16 w-16 text-blue-500 mx-auto mb-4" />
                  <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                    Видео-гайды по админ-панели
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400 mb-6">
                    Изучите все возможности системы с помощью подробных видео-инструкций
                  </p>
                  <button
                    onClick={() => setShowVideoGuides(true)}
                    className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                  >
                    Открыть библиотеку видео
                  </button>
                </div>
              </div>
            )}

            {/* Tours Tab */}
            {activeTab === 'tours' && (
              <div className="p-6">
                <div className="text-center">
                  <HelpCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
                  <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                    Интерактивные туры
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400 mb-6">
                    Пошаговое изучение функций админ-панели с интерактивными подсказками
                  </p>
                  <button
                    onClick={() => setShowTours(true)}
                    className="px-6 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
                  >
                    Начать интерактивный тур
                  </button>
                </div>
              </div>
            )}

            {/* FAQ Tab */}
            {activeTab === 'faq' && (
              <div className="p-6">
                {filteredFAQ.length === 0 ? (
                  <div className="text-center py-12">
                    <MessageCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                      Вопросы не найдены
                    </h3>
                    <p className="text-gray-600 dark:text-gray-400">
                      Попробуйте изменить поисковый запрос
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {filteredFAQ.map(faq => (
                      <div key={faq.id} className="bg-gray-50 dark:bg-gray-700 rounded-lg p-6">
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
                          {faq.question}
                        </h3>
                        
                        <div className="prose dark:prose-invert max-w-none mb-4">
                          <div dangerouslySetInnerHTML={{ 
                            __html: faq.answer.replace(/\n/g, '<br>').replace(/`([^`]+)`/g, '<code>$1</code>')
                          }} />
                        </div>

                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            {faq.tags.map(tag => (
                              <span
                                key={tag}
                                className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-xs rounded-full"
                              >
                                {tag}
                              </span>
                            ))}
                          </div>

                          <div className="flex items-center space-x-4">
                            <span className="text-sm text-gray-500 dark:text-gray-400">
                              Полезно?
                            </span>
                            <button
                              onClick={() => markHelpful(faq.id, true)}
                              className="flex items-center space-x-1 text-green-600 hover:text-green-700 transition-colors"
                            >
                              <ThumbsUp className="h-4 w-4" />
                              <span className="text-sm">{faq.helpful}</span>
                            </button>
                            <button
                              onClick={() => markHelpful(faq.id, false)}
                              className="flex items-center space-x-1 text-red-600 hover:text-red-700 transition-colors"
                            >
                              <ThumbsDown className="h-4 w-4" />
                              <span className="text-sm">{faq.notHelpful}</span>
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </motion.div>
      </div>

      {/* Tours Modal */}
      {showTours && (
        <AdminTourManager />
      )}

      {/* Video Guides Modal */}
      {showVideoGuides && (
        <VideoGuideLibrary
          isOpen={true}
          onClose={() => setShowVideoGuides(false)}
        />
      )}
    </>
  );
};

export default HelpSystem;