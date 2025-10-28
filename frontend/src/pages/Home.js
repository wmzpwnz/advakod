import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { motion } from 'framer-motion';
import { 
  Scale, 
  Zap, 
  Shield, 
  DollarSign,
  ArrowRight,
  Star
} from 'lucide-react';
import ModernButton from '../components/ModernButton';
import GlassCard from '../components/GlassCard';
import TrustBlock from '../components/TrustBlock';
import SmartSearchInput from '../components/SmartSearchInput';
import SmartFAQ from '../components/SmartFAQ';
import AnimatedSection, { AnimatedItem } from '../components/AnimatedSection';
import ThemeToggle from '../components/ThemeToggle';

const Home = () => {
  const { isAuthenticated } = useAuth();

  const features = [
    {
      icon: <Zap className="h-8 w-8 text-blue-500" />,
      title: "Мгновенно",
      description: "Ответ за 60 секунд",
      variant: "neon-blue"
    },
    {
      icon: <Scale className="h-8 w-8 text-purple-500" />,
      title: "Экспертно",
      description: "На основе ГК РФ, НК РФ и ФЗ",
      variant: "neon-purple"
    },
    {
      icon: <Shield className="h-8 w-8 text-cyan-500" />,
      title: "Безопасно",
      description: "Все данные на серверах в РФ",
      variant: "neon-cyan"
    },
    {
      icon: <DollarSign className="h-8 w-8 text-green-500" />,
      title: "Выгодно",
      description: "От 990 ₽/месяц вместо 70 000 ₽ за юриста",
      variant: "neon-green"
    }
  ];

  const howItWorks = [
    {
      step: "1",
      title: "Задайте вопрос",
      description: "Опишите вашу юридическую ситуацию или загрузите документ"
    },
    {
      step: "2",
      title: "ИИ анализирует",
      description: "Saiga Mistral 7B изучает ваш запрос и ищет релевантную информацию в базе знаний"
    },
    {
      step: "3",
      title: "Получите ответ",
      description: "Получите структурированный ответ с ссылками на законы и рекомендациями"
    }
  ];

  const targetAudience = [
    { 
      name: "ИП", 
      icon: "👤",
      description: "Регистрация, налоги, договоры, споры с контрагентами",
      benefits: ["Быстрая регистрация", "Налоговое планирование", "Защита прав"],
      variant: "neon-blue"
    },
    { 
      name: "Самозанятый", 
      icon: "💼",
      description: "Правовой статус, налоги, договоры ГПХ, защита интересов",
      benefits: ["Правовая поддержка", "Налоговые льготы", "Договорная работа"],
      variant: "neon-purple"
    },
    { 
      name: "ООО", 
      icon: "🏢",
      description: "Корпоративное право, трудовые отношения, договоры, споры",
      benefits: ["Корпоративное управление", "Трудовое право", "Договорная работа"],
      variant: "neon-cyan"
    },
    { 
      name: "Стартап", 
      icon: "🚀",
      description: "Интеллектуальная собственность, инвестиции, партнерства",
      benefits: ["Защита ИС", "Инвестиционные сделки", "Партнерские соглашения"],
      variant: "neon-pink"
    },
    { 
      name: "Фрилансер", 
      icon: "💻",
      description: "Договоры с заказчиками, авторские права, налогообложение",
      benefits: ["Договоры ГПХ", "Защита авторских прав", "Налоговое планирование"],
      variant: "neon-orange"
    },
    { 
      name: "Малый бизнес", 
      icon: "🏪",
      description: "Лицензирование, проверки, трудовые отношения, налоги",
      benefits: ["Лицензирование", "Защита от проверок", "Трудовое право"],
      variant: "neon-green"
    }
  ];

  return (
    <div className="min-h-screen">
      {/* Theme Toggle - Fixed position */}
      <div className="fixed top-6 right-6 z-50">
        <ThemeToggle />
      </div>

      {/* Skip to main content link for screen readers */}
      <a 
        href="#main-content" 
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-primary-600 focus:text-white focus:rounded-lg focus:shadow-lg"
      >
        Skip to main content
      </a>

      {/* Hero Section */}
      <section 
        aria-label="Hero banner" 
        role="banner"
        className="relative bg-gradient-to-br from-primary-50 via-white to-accent-purple/10 dark:from-gray-900 dark:via-gray-800 dark:to-accent-purple/20 py-16 sm:py-20 lg:py-24 overflow-hidden"
      >
        {/* Animated background elements */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <motion.div 
            className="absolute -top-40 -right-40 w-60 h-60 sm:w-80 sm:h-80 bg-primary-300/20 rounded-full blur-3xl"
            animate={{ 
              y: [0, -20, 0],
              x: [0, 10, 0]
            }}
            transition={{ 
              duration: 6,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          />
          <motion.div 
            className="absolute -bottom-40 -left-40 w-60 h-60 sm:w-80 sm:h-80 bg-accent-purple/20 rounded-full blur-3xl"
            animate={{ 
              y: [0, 20, 0],
              x: [0, -10, 0]
            }}
            transition={{ 
              duration: 8,
              repeat: Infinity,
              ease: "easeInOut",
              delay: 2
            }}
          />
        </div>
        
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <motion.h1 
              className="heading-1 mb-6 sm:mb-8"
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8 }}
            >
              <span className="gradient-text-modern">АДВАКОД</span>
            </motion.h1>
            
            <motion.h2 
              className="heading-2 mb-6 sm:mb-8"
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.1 }}
            >
              Ваш персональный <span className="gradient-text-modern">AI юрист-консультант</span>
            </motion.h2>
            
            <motion.p 
              className="body-large text-gray-600 dark:text-gray-300 mb-8 sm:mb-10 max-w-4xl mx-auto px-4"
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.2 }}
            >
              Мощь модели Saiga Mistral 7B — для решения ваших российских юридических задач. 
              Проверка договоров, консультации и анализ рисков в разы быстрее и дешевле.
            </motion.p>
            
            {/* Smart Search Input */}
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.3 }}
              className="mb-8 sm:mb-10"
            >
              <SmartSearchInput 
                onSearch={(query) => {
                  // Navigate to chat with the query
                  window.location.href = `/chat?q=${encodeURIComponent(query)}`;
                }}
              />
            </motion.div>

            <motion.div 
              className="flex flex-col sm:flex-row gap-4 sm:gap-6 justify-center items-center px-4"
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.4 }}
            >
              {isAuthenticated ? (
                <ModernButton 
                  variant="glass-primary" 
                  size="lg"
                  icon={<ArrowRight className="w-5 h-5" />}
                  className="w-full sm:w-auto"
                >
                  <Link to="/chat" className="flex items-center space-x-2">
                    <span>Начать чат с ИИ</span>
                  </Link>
                </ModernButton>
              ) : (
                <>
                  <ModernButton 
                    variant="glass-primary" 
                    size="lg"
                    icon={<Star className="w-5 h-5" />}
                    className="w-full sm:w-auto"
                  >
                    <Link to="/register" className="flex items-center space-x-2">
                      <span>Попробовать бесплатно</span>
                    </Link>
                  </ModernButton>
                  <ModernButton 
                    variant="glass-secondary" 
                    size="lg"
                    className="w-full sm:w-auto"
                  >
                    <Link to="/pricing" className="flex items-center space-x-2">
                      <span>Смотреть тарифы</span>
                    </Link>
                  </ModernButton>
                </>
              )}
            </motion.div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section 
        id="main-content"
        aria-label="Key features" 
        role="region"
        className="py-16 sm:py-20 lg:py-24 bg-white dark:bg-gray-900"
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <AnimatedSection animationType="fadeUp" delay={0.2}>
            <div className="text-center mb-12 sm:mb-16">
              <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4 sm:mb-6">
                Почему выбирают <span className="gradient-text">АДВАКОД</span>?
              </h2>
              <p className="text-lg sm:text-xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto">
                Мощная технология для решения ваших юридических задач
              </p>
            </div>
          </AnimatedSection>
          
          <AnimatedSection animationType="stagger" staggerChildren={0.15} delay={0.3}>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 lg:gap-8">
              {features.map((feature, index) => (
                <AnimatedItem key={index} animationType="fadeUp">
                  <GlassCard 
                    variant={feature.variant || "neon-glass"} 
                    className="text-center group h-full hover:neon-glow-intense"
                  >
                    <motion.div 
                      className="flex justify-center mb-4 sm:mb-6"
                      whileHover={{ scale: 1.15, rotate: 5 }}
                      transition={{ duration: 0.3 }}
                    >
                      <div className="text-purple-400 group-hover:text-cyan-400 transition-colors duration-300 neon-icon-glow">
                        {feature.icon}
                      </div>
                    </motion.div>
                    <h3 className="text-lg sm:text-xl lg:text-2xl font-bold text-gray-100 mb-2 sm:mb-3 group-hover:text-purple-300 transition-colors duration-300">
                      {feature.title}
                    </h3>
                    <p className="text-sm sm:text-base text-gray-300 group-hover:text-gray-200 transition-colors duration-300">
                      {feature.description}
                    </p>
                  </GlassCard>
                </AnimatedItem>
              ))}
            </div>
          </AnimatedSection>
        </div>
      </section>

      {/* How It Works Section */}
      <section 
        aria-label="How it works" 
        role="region"
        className="py-16 sm:py-20 lg:py-24 bg-gray-50 dark:bg-gray-800"
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <AnimatedSection animationType="fadeUp" delay={0.2}>
            <div className="text-center mb-12 sm:mb-16">
              <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-gray-900 dark:text-gray-100 mb-4 sm:mb-6">
                Как это работает
              </h2>
              <p className="text-lg sm:text-xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto">
                Простой алгоритм для получения юридической помощи
              </p>
            </div>
          </AnimatedSection>
          
          <AnimatedSection animationType="stagger" staggerChildren={0.2} delay={0.3}>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 sm:gap-12">
              {howItWorks.map((step, index) => (
                <AnimatedItem key={index} animationType="fadeUp">
                  <div className="text-center group relative">
                    <motion.div 
                      className="bg-gradient-to-r from-primary-500 to-primary-600 text-white rounded-full w-20 h-20 sm:w-24 sm:h-24 flex items-center justify-center text-2xl sm:text-3xl font-bold mx-auto mb-6 sm:mb-8 shadow-lg"
                      whileHover={{ 
                        scale: 1.1, 
                        rotate: 360,
                        boxShadow: "0 20px 40px rgba(59, 130, 246, 0.3)"
                      }}
                      transition={{ duration: 0.5 }}
                    >
                      {step.step}
                    </motion.div>
                    <h3 className="heading-3 text-gray-900 dark:text-gray-100 mb-4 sm:mb-6">
                      {step.title}
                    </h3>
                    <p className="body-large text-gray-600 dark:text-gray-300">
                      {step.description}
                    </p>
                    {/* Соединительная линия между шагами */}
                    {index < howItWorks.length - 1 && (
                      <AnimatedSection 
                        animationType="scale" 
                        delay={0.5 + index * 0.2}
                        className="hidden md:block absolute top-12 left-1/2 w-full h-0.5 bg-gradient-to-r from-primary-300 to-transparent transform translate-x-1/2"
                      />
                    )}
                  </div>
                </AnimatedItem>
              ))}
            </div>
          </AnimatedSection>
        </div>
      </section>

      {/* Target Audience Section */}
      <section 
        aria-label="Target audience" 
        role="region"
        className="py-16 sm:py-20 lg:py-24 bg-white dark:bg-gray-900"
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <AnimatedSection animationType="fadeUp" delay={0.2}>
            <div className="text-center mb-12 sm:mb-16">
              <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4 sm:mb-6">
                Для кого создан <span className="gradient-text">АДВАКОД</span>
              </h2>
              <p className="text-lg sm:text-xl text-gray-600 dark:text-gray-300 max-w-4xl mx-auto">
                Решаем юридические задачи для предпринимателей, бизнеса и фрилансеров. 
                От регистрации до защиты прав — все в одном месте.
              </p>
            </div>
          </AnimatedSection>
          
          <AnimatedSection animationType="stagger" staggerChildren={0.12} delay={0.3}>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6 lg:gap-8">
              {targetAudience.map((audience, index) => (
                <AnimatedItem key={index} animationType="scale">
                  <GlassCard 
                    variant={audience.variant || "neon-purple"} 
                    className="group h-full hover:neon-glow-intense"
                  >
                    <div className="text-center mb-4 sm:mb-6">
                      <motion.div 
                        className="text-4xl sm:text-5xl lg:text-6xl mb-3 sm:mb-4 filter grayscale group-hover:grayscale-0 transition-all duration-300"
                        whileHover={{ scale: 1.15, rotate: 5 }}
                        transition={{ duration: 0.3 }}
                      >
                        {audience.icon}
                      </motion.div>
                      <h3 className="text-lg sm:text-xl lg:text-2xl font-bold text-gray-100 mb-2 sm:mb-3 group-hover:text-purple-300 transition-colors duration-300">
                        {audience.name}
                      </h3>
                      <p className="text-sm sm:text-base text-gray-300 group-hover:text-gray-200 transition-colors duration-300">
                        {audience.description}
                      </p>
                    </div>
                    
                    <div className="space-y-2">
                      <h4 className="text-xs sm:text-sm font-semibold text-purple-400 group-hover:text-cyan-400 mb-2 sm:mb-3 transition-colors duration-300">
                        Что получаете:
                      </h4>
                      <ul className="space-y-1.5 sm:space-y-2">
                        {audience.benefits.map((benefit, benefitIndex) => (
                          <li 
                            key={benefitIndex} 
                            className="flex items-center text-xs sm:text-sm text-gray-300 group-hover:text-gray-200 transition-colors duration-300"
                          >
                            <motion.span 
                              className="w-1.5 h-1.5 sm:w-2 sm:h-2 bg-purple-500 group-hover:bg-cyan-400 rounded-full mr-2 sm:mr-3 flex-shrink-0 transition-colors duration-300 neon-dot-glow"
                              whileHover={{ scale: 1.5 }}
                            />
                            {benefit}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </GlassCard>
                </AnimatedItem>
              ))}
            </div>
          </AnimatedSection>
        </div>
      </section>

      {/* Trust Block Section */}
      <TrustBlock />

      {/* FAQ Section */}
      <section 
        aria-label="Frequently asked questions" 
        role="region"
        className="py-16 sm:py-20 lg:py-24 bg-gray-50 dark:bg-gray-800"
      >
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <AnimatedSection animationType="fadeUp" delay={0.2}>
            <SmartFAQ />
          </AnimatedSection>
        </div>
      </section>

      {/* CTA Section */}
      <section 
        aria-label="Call to action" 
        role="region"
        className="py-16 sm:py-20 lg:py-24 bg-gradient-to-r from-primary-600 to-primary-700 dark:from-primary-700 dark:to-primary-800 relative overflow-hidden"
      >
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
        
        <AnimatedSection animationType="fadeUp" delay={0.2} className="relative max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
          <h2 className="heading-1 text-white mb-6 sm:mb-8">
            Готовы начать работу с <span className="text-transparent bg-clip-text bg-gradient-to-r from-white to-primary-200 dark:from-primary-100 dark:to-primary-300">АДВАКОД</span>?
          </h2>
          
          <p className="body-large text-primary-100 dark:text-primary-200 mb-8 sm:mb-10 max-w-3xl mx-auto">
            Присоединяйтесь к тысячам предпринимателей, которые уже экономят время и деньги
          </p>
          
          <div>
            {isAuthenticated ? (
              <ModernButton 
                variant="glass" 
                size="lg"
                icon={<ArrowRight className="w-5 h-5" />}
              >
                <Link to="/chat" className="flex items-center space-x-2">
                  <span>Начать чат</span>
                </Link>
              </ModernButton>
            ) : (
              <ModernButton 
                variant="glass" 
                size="lg"
                icon={<Star className="w-5 h-5" />}
              >
                <Link to="/register" className="flex items-center space-x-2">
                  <span>Попробовать бесплатно</span>
                </Link>
              </ModernButton>
            )}
          </div>
        </AnimatedSection>
      </section>
    </div>
  );
};

export default Home;
