import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown } from 'lucide-react';

const SmartFAQ = () => {
  const [openIndex, setOpenIndex] = useState(null);

  const faqData = [
    {
      id: 1,
      question: "Как AI может заменить юриста?",
      answer: "AI не заменяет, а дополняет работу юриста. Наш AI-ассистент помогает быстро анализировать документы, находить релевантную информацию и предоставлять первичные консультации. Для сложных случаев всегда рекомендуется консультация с живым специалистом.",
      category: "general",
      searchTags: ["ai", "юрист", "замена"]
    },
    {
      id: 2,
      question: "Насколько безопасны мои данные?",
      answer: "Мы используем шифрование данных на уровне банков, все документы хранятся в защищенном облаке с многоуровневой аутентификацией. Ваши данные никогда не передаются третьим лицам и доступны только вам.",
      category: "security",
      searchTags: ["безопасность", "данные", "конфиденциальность"]
    },
    {
      id: 3,
      question: "Какие типы документов можно анализировать?",
      answer: "Наша система работает с договорами, исковыми заявлениями, учредительными документами, трудовыми соглашениями и другими юридическими документами. Поддерживаются форматы PDF, DOCX, TXT.",
      category: "features",
      searchTags: ["документы", "анализ", "форматы"]
    },
    {
      id: 4,
      question: "Сколько стоит использование сервиса?",
      answer: "Мы предлагаем гибкую систему тарифов: бесплатный план для базовых консультаций, профессиональный план от 990₽/месяц и корпоративные решения. Первые 7 дней - бесплатно для всех тарифов.",
      category: "pricing",
      searchTags: ["цена", "тариф", "стоимость"]
    },
    {
      id: 5,
      question: "Как быстро я получу ответ на свой вопрос?",
      answer: "AI-ассистент отвечает мгновенно, обычно в течение 2-5 секунд. Для сложных запросов с анализом больших документов время может увеличиться до 30 секунд.",
      category: "performance",
      searchTags: ["скорость", "время", "ответ"]
    }
  ];

  const toggleFAQ = (index) => {
    setOpenIndex(openIndex === index ? null : index);
  };

  return (
    <div className="w-full max-w-4xl mx-auto px-4 py-12">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="text-center mb-12"
      >
        <h2 className="text-4xl md:text-5xl font-bold mb-4 gradient-text">
          Часто задаваемые вопросы
        </h2>
        <p className="text-lg text-gray-400">
          Ответы на популярные вопросы о нашем AI-юристе
        </p>
      </motion.div>

      <div className="space-y-4">
        {faqData.map((faq, index) => (
          <motion.div
            key={faq.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: index * 0.1 }}
            className={`
              bg-white/10 backdrop-blur-md rounded-2xl overflow-hidden
              border border-purple-500/20 transition-all duration-300
              neon-glow-purple
              ${openIndex === index ? 'neon-pulse' : ''}
            `}
          >
            <button
              onClick={() => toggleFAQ(index)}
              className="w-full px-6 py-5 flex items-center justify-between text-left hover:bg-white/5 active:bg-white/10 transition-all duration-300 min-h-[60px] touch-manipulation"
              aria-expanded={openIndex === index}
              aria-controls={`faq-answer-${faq.id}`}
            >
              <span className="text-lg font-semibold text-gray-100 pr-4">
                {faq.question}
              </span>
              <motion.div
                animate={{ rotate: openIndex === index ? 180 : 0 }}
                transition={{ duration: 0.3, ease: "easeInOut" }}
                className="flex-shrink-0 relative silver-sparkle min-w-[44px] min-h-[44px] flex items-center justify-center"
              >
                <ChevronDown 
                  className="w-6 h-6 md:w-7 md:h-7 transition-all duration-300"
                  style={{ 
                    color: 'var(--accent-silver)',
                    filter: openIndex === index 
                      ? 'drop-shadow(0 0 8px rgba(199, 199, 204, 0.6)) brightness(1.2)' 
                      : 'drop-shadow(0 0 3px rgba(199, 199, 204, 0.3))'
                  }}
                />
              </motion.div>
            </button>

            <AnimatePresence>
              {openIndex === index && (
                <motion.div
                  id={`faq-answer-${faq.id}`}
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.3, ease: "easeInOut" }}
                  className="overflow-hidden"
                >
                  <div className="px-6 pb-5 pt-2">
                    <motion.p
                      initial={{ y: -10, opacity: 0 }}
                      animate={{ y: 0, opacity: 1 }}
                      transition={{ duration: 0.3, delay: 0.1 }}
                      className="text-gray-300 leading-relaxed"
                    >
                      {faq.answer}
                    </motion.p>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

export default SmartFAQ;
