import React, { useState } from 'react';
import { FileText, Scale, Building, User, CreditCard, Shield, Lightbulb, ChevronDown, ChevronUp, X } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';

const QuestionTemplates = ({ onTemplateSelect, isVisible, onToggle, onClose }) => {
  const [expandedCategory, setExpandedCategory] = useState(null);
  const { isDark } = useTheme();
  
  // Поддержка обоих вариантов: onToggle и onClose
  const handleClose = () => {
    if (onClose) {
      onClose();
    } else if (onToggle) {
      onToggle();
    }
  };

  const templates = {
    'Уголовное право': {
      icon: <Shield className="h-4 w-4" />,
      color: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300',
      questions: [
        'Статья 105 УК РФ - Убийство',
        'Статья 158 УК РФ - Кража',
        'Статья 159 УК РФ - Мошенничество',
        'Статья 228 УК РФ - Незаконный оборот наркотиков',
        'Статья 264 УК РФ - Нарушение ПДД',
        'Какие наказания предусмотрены за кражу?',
        'Что такое условное осуждение?',
        'Как оспорить приговор суда?'
      ]
    },
    'Гражданское право': {
      icon: <Scale className="h-4 w-4" />,
      color: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300',
      questions: [
        'Как составить договор купли-продажи?',
        'Статья 151 ГК РФ - Компенсация морального вреда',
        'Статья 395 ГК РФ - Ответственность за неисполнение обязательств',
        'Как взыскать долг через суд?',
        'Что такое исковая давность?',
        'Как оформить наследство?',
        'Права потребителя при покупке товара',
        'Как расторгнуть договор?'
      ]
    },
    'Трудовое право': {
      icon: <User className="h-4 w-4" />,
      color: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300',
      questions: [
        'Статья 77 ТК РФ - Основания прекращения трудового договора',
        'Статья 81 ТК РФ - Расторжение по инициативе работодателя',
        'Как оформить увольнение?',
        'Права работника при сокращении',
        'Как рассчитать компенсацию за отпуск?',
        'Что такое испытательный срок?',
        'Права беременных женщин на работе',
        'Как оспорить дисциплинарное взыскание?'
      ]
    },
    'Налоговое право': {
      icon: <CreditCard className="h-4 w-4" />,
      color: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300',
      questions: [
        'Как зарегистрировать ИП?',
        'Какие налоги платит ИП?',
        'Статья 122 НК РФ - Неуплата налогов',
        'Как подать налоговую декларацию?',
        'Что такое НДС?',
        'Льготы по налогу на имущество',
        'Как вернуть налоговый вычет?',
        'Ответственность за налоговые правонарушения'
      ]
    },
    'Корпоративное право': {
      icon: <Building className="h-4 w-4" />,
      color: 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300',
      questions: [
        'Как зарегистрировать ООО?',
        'Уставный капитал ООО',
        'Права и обязанности участников ООО',
        'Как провести собрание участников?',
        'Выход из состава участников ООО',
        'Ликвидация ООО',
        'Корпоративные споры',
        'Управление в акционерном обществе'
      ]
    },
    'Семейное право': {
      icon: <FileText className="h-4 w-4" />,
      color: 'bg-pink-100 dark:bg-pink-900/30 text-pink-700 dark:text-pink-300',
      questions: [
        'Статья 25 СК РФ - Расторжение брака',
        'Как подать на развод?',
        'Раздел имущества при разводе',
        'Алименты на детей',
        'Как определить место жительства ребенка?',
        'Усыновление ребенка',
        'Брачный договор',
        'Лишение родительских прав'
      ]
    }
  };

  const handleTemplateClick = (question) => {
    if (onTemplateSelect) {
      onTemplateSelect(question);
    }
    setExpandedCategory(null);
    // Закрываем панель после выбора шаблона
    if (onClose) {
      onClose();
    }
  };

  const toggleCategory = (category) => {
    setExpandedCategory(expandedCategory === category ? null : category);
  };

  if (!isVisible) return null;

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-end justify-center"
      onClick={handleClose}
    >
      <div 
        className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 p-4 animate-slide-in-up w-full max-w-2xl max-h-[80vh] overflow-y-auto rounded-t-lg"
        onClick={(e) => e.stopPropagation()}
      >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 flex items-center">
          <Lightbulb className="h-5 w-5 mr-2 text-yellow-500" />
          Шаблоны вопросов
        </h3>
        <button
          onClick={handleClose}
          className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 p-1"
          aria-label="Закрыть"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      <div className="space-y-3">
        {Object.entries(templates).map(([category, data]) => (
          <div key={category} className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
            <button
              onClick={() => toggleCategory(category)}
              className={`w-full px-4 py-3 flex items-center justify-between ${data.color} hover:opacity-80 transition-opacity`}
            >
              <div className="flex items-center space-x-2">
                {data.icon}
                <span className="font-medium">{category}</span>
              </div>
              {expandedCategory === category ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </button>
            
            {expandedCategory === category && (
              <div className="p-4 bg-gray-50 dark:bg-gray-700 space-y-2 animate-slide-in-down">
                {data.questions.map((question, index) => (
                  <button
                    key={index}
                    onClick={() => handleTemplateClick(question)}
                    className="w-full text-left p-3 rounded-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 hover:border-primary-300 dark:hover:border-primary-600 hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-all duration-200 text-sm text-gray-700 dark:text-gray-300 hover:text-primary-700 dark:hover:text-primary-300"
                  >
                    {question}
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
        <p className="text-sm text-blue-700 dark:text-blue-300">
          💡 <strong>Совет:</strong> Выберите шаблон вопроса или создайте свой собственный. 
          ИИ-юрист даст подробный ответ с ссылками на статьи законов.
        </p>
      </div>
      </div>
    </div>
  );
};

export default QuestionTemplates;
