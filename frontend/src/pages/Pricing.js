import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { motion } from 'framer-motion';
import { Check, Star, Zap, Building, Crown, ArrowRight, Clock } from 'lucide-react';
import ModernButton from '../components/ModernButton';
import GlassCard from '../components/GlassCard';

const Pricing = () => {
  const { isAuthenticated } = useAuth();

  const plans = [
    {
      name: "Самозанятый",
      price: "990",
      period: "месяц",
      description: "Для индивидуальных предпринимателей и самозанятых",
      icon: <Zap className="h-8 w-8 text-blue-600" />,
      features: [
        "50 запросов в месяц",
        "Консультации по налогам",
        "Проверка простых договоров",
        "База знаний по ИП",
        "Email поддержка",
        "Мобильное приложение"
      ],
      popular: false,
      color: "blue"
    },
    {
      name: "Малый бизнес",
      price: "2990",
      period: "месяц",
      description: "Для ООО и малого бизнеса",
      icon: <Building className="h-8 w-8 text-green-600" />,
      features: [
        "200 запросов в месяц",
        "Полный анализ договоров",
        "Консультации по трудовому праву",
        "Шаблоны документов",
        "Приоритетная поддержка",
        "API доступ",
        "Экспорт документов"
      ],
      popular: true,
      color: "green"
    },
    {
      name: "Бизнес+",
      price: "5990",
      period: "месяц",
      description: "Для среднего и крупного бизнеса",
      icon: <Crown className="h-8 w-8 text-purple-600" />,
      features: [
        "Безлимитные запросы",
        "Персональный менеджер",
        "Интеграция с 1С",
        "Анализ больших документов",
        "Приоритетная обработка",
        "Белый лейбл",
        "SLA 99.9%"
      ],
      popular: false,
      color: "purple"
    }
  ];

  const faqs = [
    {
      question: "Что входит в один запрос?",
      answer: "1 запрос = 1 вопрос + 1 ответ от ИИ, или анализ 1 документа. Загрузка файла и получение результата считается одним запросом."
    },
    {
      question: "Можно ли изменить тариф?",
      answer: "Да, вы можете изменить тариф в любое время в личном кабинете. Изменения вступают в силу с следующего периода оплаты."
    },
    {
      question: "Есть ли пробный период?",
      answer: "Да, мы предоставляем 14 дней бесплатного использования для всех новых пользователей. Никаких ограничений по функционалу."
    },
    {
      question: "Что если не понравится?",
      answer: "Мы вернем деньги в течение 14 дней, если сервис не подойдет. Без вопросов и условий."
    },
    {
      question: "Где хранятся мои данные?",
      answer: "Все данные хранятся на серверах в России в соответствии с 152-ФЗ. Мы не передаем информацию третьим лицам."
    },
    {
      question: "Можно ли использовать API?",
      answer: "API доступен в тарифе 'Малый бизнес' и выше. Документация предоставляется после регистрации."
    }
  ];

  const getColorClasses = (color, popular) => {
    const colors = {
      blue: {
        bg: "bg-blue-50 dark:bg-blue-900/20",
        border: "border-blue-200 dark:border-blue-700",
        button: "bg-blue-600 hover:bg-blue-500 dark:bg-blue-500 dark:hover:bg-blue-400",
        text: "text-blue-600 dark:text-blue-400",
        icon: "text-blue-600 dark:text-blue-400"
      },
      green: {
        bg: "bg-green-50 dark:bg-green-900/20",
        border: "border-green-200 dark:border-green-700",
        button: "bg-green-600 hover:bg-green-500 dark:bg-green-500 dark:hover:bg-green-400",
        text: "text-green-600 dark:text-green-400",
        icon: "text-green-600 dark:text-green-400"
      },
      purple: {
        bg: "bg-purple-50 dark:bg-purple-900/20",
        border: "border-purple-200 dark:border-purple-700",
        button: "bg-purple-600 hover:bg-purple-500 dark:bg-purple-500 dark:hover:bg-purple-400",
        text: "text-purple-600 dark:text-purple-400",
        icon: "text-purple-600 dark:text-purple-400"
      }
    };
    
    return colors[color];
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-200">
      {/* Header */}
      <section className="bg-white dark:bg-gray-800 py-16 transition-colors duration-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <motion.h1 
            className="heading-1 text-gray-900 dark:text-gray-100 mb-4"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            Выберите подходящий тариф
          </motion.h1>
          <motion.p 
            className="body-large text-gray-600 dark:text-gray-300 mb-8"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
          >
            Начните с бесплатного пробного периода и выберите план, который подходит вашему бизнесу
          </motion.p>
          
          <motion.div 
            className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-lg p-4 max-w-2xl mx-auto"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.4 }}
          >
            <div className="flex items-center justify-center space-x-2">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
              >
                <Check className="h-5 w-5 text-green-600 dark:text-green-400" />
              </motion.div>
              <span className="text-green-800 dark:text-green-200 font-medium">
                14 дней бесплатно для всех новых пользователей
              </span>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Pricing Cards */}
      <section className="py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {plans.map((plan, index) => {
              const colors = getColorClasses(plan.color, plan.popular);
              
              return (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 30 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: index * 0.1 }}
                  whileHover={{ y: -10 }}
                >
                  <GlassCard 
                    variant={plan.popular ? "neon" : "default"}
                    className={`relative ${
                      plan.popular
                        ? `${colors.bg} ${colors.border} ring-2 ring-green-500 dark:ring-green-400`
                        : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700'
                    }`}
                  >
                    {plan.popular && (
                      <motion.div 
                        className="absolute -top-4 left-1/2 transform -translate-x-1/2"
                        initial={{ opacity: 0, scale: 0 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ duration: 0.5, delay: 0.3 }}
                      >
                        <div className="bg-green-500 dark:bg-green-600 text-white px-4 py-1 rounded-full text-sm font-medium flex items-center space-x-1">
                          <motion.div
                            animate={{ rotate: 360 }}
                            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                          >
                            <Star className="h-4 w-4" />
                          </motion.div>
                          <span>Популярный</span>
                        </div>
                      </motion.div>
                    )}

                    <div className="text-center mb-8">
                      <motion.div 
                        className="flex justify-center mb-4"
                        whileHover={{ scale: 1.1, rotate: 5 }}
                        transition={{ duration: 0.3 }}
                      >
                        <div className={colors.icon}>
                          {plan.icon}
                        </div>
                      </motion.div>
                      <h3 className="heading-3 text-gray-900 dark:text-gray-100 mb-2">
                        {plan.name}
                      </h3>
                      <p className="body-medium text-gray-600 dark:text-gray-300 mb-6">
                        {plan.description}
                      </p>
                      
                      <div className="mb-6">
                        <span className="text-4xl font-bold text-gray-900 dark:text-gray-100">
                          {plan.price} ₽
                        </span>
                        <span className="text-gray-600 dark:text-gray-400 ml-2">
                          / {plan.period}
                        </span>
                      </div>
                    </div>

                    <ul className="space-y-4 mb-8">
                      {plan.features.map((feature, featureIndex) => (
                        <motion.li 
                          key={featureIndex} 
                          className="flex items-start space-x-3"
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ duration: 0.4, delay: index * 0.1 + featureIndex * 0.1 }}
                        >
                          <motion.div
                            whileHover={{ scale: 1.2 }}
                            transition={{ duration: 0.2 }}
                          >
                            <Check className="h-5 w-5 text-green-500 dark:text-green-400 mt-0.5 flex-shrink-0" />
                          </motion.div>
                          <span className="text-gray-700 dark:text-gray-300">{feature}</span>
                        </motion.li>
                      ))}
                    </ul>

                    <ModernButton
                      variant={plan.popular ? "success" : "primary"}
                      size="lg"
                      className="w-full"
                      icon={<ArrowRight className="w-5 h-5" />}
                    >
                      <Link 
                        to={isAuthenticated ? "/profile" : "/register"}
                        className="flex items-center justify-center space-x-2 w-full"
                      >
                        <span>{isAuthenticated ? "Изменить тариф" : "Начать бесплатно"}</span>
                      </Link>
                    </ModernButton>
                  </GlassCard>
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-16 bg-white dark:bg-gray-800 transition-colors duration-200">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div 
            className="text-center mb-12"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <h2 className="heading-2 text-gray-900 dark:text-gray-100 mb-4">
              Часто задаваемые вопросы
            </h2>
            <p className="body-large text-gray-600 dark:text-gray-300">
              Ответы на популярные вопросы о тарифах и использовании
            </p>
          </motion.div>

          <div className="space-y-8">
            {faqs.map((faq, index) => (
              <motion.div 
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                whileHover={{ y: -2 }}
              >
                <GlassCard 
                  variant="default"
                  className="group"
                >
                  <h3 className="heading-3 text-gray-900 dark:text-gray-100 mb-3">
                    {faq.question}
                  </h3>
                  <p className="body-medium text-gray-700 dark:text-gray-300">
                    {faq.answer}
                  </p>
                </GlassCard>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 bg-primary-600 dark:bg-primary-700 relative overflow-hidden">
        {/* Animated background */}
        <div className="absolute inset-0 overflow-hidden">
          <motion.div 
            className="absolute -top-20 -right-20 w-40 h-40 bg-white/10 rounded-full blur-3xl"
            animate={{ 
              y: [0, -20, 0],
              x: [0, 20, 0]
            }}
            transition={{ 
              duration: 8,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          />
          <motion.div 
            className="absolute -bottom-20 -left-20 w-40 h-40 bg-white/10 rounded-full blur-3xl"
            animate={{ 
              y: [0, 20, 0],
              x: [0, -20, 0]
            }}
            transition={{ 
              duration: 10,
              repeat: Infinity,
              ease: "easeInOut",
              delay: 2
            }}
          />
        </div>
        
        <div className="relative max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
          <motion.h2 
            className="heading-1 text-white mb-6"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            Готовы начать?
          </motion.h2>
          <motion.p 
            className="body-large text-primary-100 dark:text-primary-200 mb-8"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
          >
            Присоединяйтесь к тысячам предпринимателей, которые уже экономят время и деньги
          </motion.p>
          
          <motion.div 
            className="flex flex-col sm:flex-row gap-4 justify-center"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
          >
            <ModernButton
              variant="glass"
              size="lg"
              icon={<ArrowRight className="w-5 h-5" />}
            >
              <Link 
                to={isAuthenticated ? "/chat" : "/register"}
                className="flex items-center space-x-2"
              >
                <span>{isAuthenticated ? "Начать чат" : "Попробовать бесплатно"}</span>
              </Link>
            </ModernButton>
            <ModernButton
              variant="ghost"
              size="lg"
              icon={<Clock className="w-5 h-5" />}
              className="border-2 border-white text-white hover:bg-white hover:text-primary-600"
            >
              <Link 
                to="/chat"
                className="flex items-center space-x-2"
              >
                <span>Посмотреть демо</span>
              </Link>
            </ModernButton>
          </motion.div>
        </div>
      </section>
    </div>
  );
};

export default Pricing;
