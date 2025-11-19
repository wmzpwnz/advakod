import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const TrustBlock = () => {
  // Partner logos - using placeholder images with company names
  const partners = [
    { id: 1, name: 'Сбербанк', logo: 'https://via.placeholder.com/150x60/2a2a2a/C7C7CC?text=Сбербанк' },
    { id: 2, name: 'ВТБ', logo: 'https://via.placeholder.com/150x60/2a2a2a/C7C7CC?text=ВТБ' },
    { id: 3, name: 'Газпром', logo: 'https://via.placeholder.com/150x60/2a2a2a/C7C7CC?text=Газпром' },
    { id: 4, name: 'Роснефть', logo: 'https://via.placeholder.com/150x60/2a2a2a/C7C7CC?text=Роснефть' },
    { id: 5, name: 'Яндекс', logo: 'https://via.placeholder.com/150x60/2a2a2a/C7C7CC?text=Яндекс' },
    { id: 6, name: 'МТС', logo: 'https://via.placeholder.com/150x60/2a2a2a/C7C7CC?text=МТС' },
  ];

  // Testimonials data
  const testimonials = [
    {
      id: 1,
      name: 'Алексей Петров',
      position: 'Генеральный директор, ООО "ТехноСтрой"',
      text: 'AI-юрист помог нам быстро разобраться в сложных договорных вопросах. Экономия времени и денег очевидна.',
      avatar: 'https://via.placeholder.com/80/8B5CF6/FFFFFF?text=АП'
    },
    {
      id: 2,
      name: 'Мария Соколова',
      position: 'Юрист, Финансовая группа "Альфа"',
      text: 'Отличный инструмент для первичного анализа документов. Значительно ускорил нашу работу с контрактами.',
      avatar: 'https://via.placeholder.com/80/06B6D4/FFFFFF?text=МС'
    },
    {
      id: 3,
      name: 'Дмитрий Волков',
      position: 'Предприниматель, ИП Волков Д.А.',
      text: 'Простой и понятный интерфейс. Получил квалифицированную консультацию за считанные минуты.',
      avatar: 'https://via.placeholder.com/80/A78BFA/FFFFFF?text=ДВ'
    },
    {
      id: 4,
      name: 'Елена Кузнецова',
      position: 'Руководитель юридического отдела, "МегаКорп"',
      text: 'Инновационное решение для юридической поддержки. Рекомендую всем, кто ценит свое время.',
      avatar: 'https://via.placeholder.com/80/22D3EE/FFFFFF?text=ЕК'
    }
  ];

  const [currentTestimonial, setCurrentTestimonial] = useState(0);
  const [isPaused, setIsPaused] = useState(false);

  // Auto-rotate testimonials
  useEffect(() => {
    if (!isPaused) {
      const interval = setInterval(() => {
        setCurrentTestimonial((prev) => (prev + 1) % testimonials.length);
      }, 5000); // Change every 5 seconds

      return () => clearInterval(interval);
    }
  }, [isPaused, testimonials.length]);

  return (
    <section className="py-16 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Section Title */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-12"
        >
          <h2 className="text-3xl md:text-4xl font-bold mb-4 gradient-text">
            Нам доверяют
          </h2>
          <p className="text-lg text-blue-600 dark:text-cyan-400 max-w-2xl mx-auto font-medium">
            Ведущие компании России выбирают наш AI-юрист для решения правовых вопросов
          </p>
        </motion.div>

        {/* Partner Logos Container with Glassmorphism */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="relative bg-white/5 backdrop-blur-md border border-white/10 rounded-3xl p-8 md:p-12 shadow-2xl mb-16"
        >
          {/* Decorative gradient overlay */}
          <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 via-transparent to-cyan-500/5 rounded-3xl pointer-events-none" />
          
          {/* Partner Logos Grid */}
          <div className="relative grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-8 items-center justify-items-center">
            {partners.map((partner, index) => (
              <motion.div
                key={partner.id}
                initial={{ opacity: 0, scale: 0.8 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="partner-logo-wrapper relative group overflow-hidden rounded-lg"
              >
                {/* Shimmer effect overlay using shimmer-silver class */}
                <div className="shimmer-effect absolute inset-0 pointer-events-none">
                  <div className="absolute top-0 left-[-100%] w-full h-full bg-gradient-to-r from-transparent via-white/30 to-transparent" 
                       style={{ animation: 'shimmerSweep 3s ease-in-out infinite' }} />
                </div>
                
                {/* Logo Image with silver filters */}
                <img
                  src={partner.logo}
                  alt={`${partner.name} - trusted partner logo`}
                  role="img"
                  aria-label={`${partner.name} company logo`}
                  className="partner-logo w-full h-auto max-w-[120px] md:max-w-[150px] grayscale brightness-75 hover:grayscale-0 hover:brightness-100 transition-all duration-500 ease-in-out transform group-hover:scale-110 relative z-10"
                  loading="lazy"
                />
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Testimonials Section */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, delay: 0.4 }}
          className="max-w-4xl mx-auto"
        >
          <h3 className="text-2xl md:text-3xl font-semibold text-center mb-8 gradient-text">
            Отзывы клиентов
          </h3>

          {/* Testimonial Carousel */}
          <div
            className="relative"
            onMouseEnter={() => setIsPaused(true)}
            onMouseLeave={() => setIsPaused(false)}
            aria-live="polite"
            aria-atomic="true"
            role="region"
            aria-label="Customer testimonials"
          >
            <AnimatePresence mode="wait">
              <motion.div
                key={currentTestimonial}
                initial={{ opacity: 0, x: 50 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -50 }}
                transition={{ duration: 0.5 }}
                className="testimonial-card relative bg-gradient-to-br from-purple-500/15 via-blue-500/10 to-cyan-500/15 backdrop-blur-lg rounded-2xl p-8 md:p-10 border border-purple-400/40 shadow-2xl"
              >
                {/* Neon glow effect */}
                <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-purple-400/20 via-blue-400/15 to-cyan-400/20 pointer-events-none" />
                <div className="neon-glow-border absolute inset-0 rounded-2xl opacity-0 transition-opacity duration-300" />

                <div className="relative z-10">
                  {/* Avatar and Info */}
                  <div className="flex items-center mb-6">
                    <img
                      src={testimonials[currentTestimonial].avatar}
                      alt={testimonials[currentTestimonial].name}
                      className="w-16 h-16 md:w-20 md:h-20 rounded-full border-2 border-purple-500/30 shadow-lg"
                    />
                    <div className="ml-4">
                      <h4 className="text-lg md:text-xl font-semibold text-white dark:text-white">
                        {testimonials[currentTestimonial].name}
                      </h4>
                      <p className="text-sm md:text-base text-cyan-300 dark:text-cyan-300">
                        {testimonials[currentTestimonial].position}
                      </p>
                    </div>
                  </div>

                  {/* Testimonial Text */}
                  <p className="text-base md:text-lg text-white dark:text-white leading-relaxed italic">
                    "{testimonials[currentTestimonial].text}"
                  </p>
                </div>
              </motion.div>
            </AnimatePresence>

            {/* Navigation Dots */}
            <div className="flex justify-center mt-6 space-x-3 md:space-x-2" role="tablist" aria-label="Testimonial navigation">
              {testimonials.map((_, index) => (
                <button
                  key={index}
                  onClick={() => setCurrentTestimonial(index)}
                  className={`rounded-full transition-all duration-300 touch-manipulation min-w-[44px] min-h-[44px] flex items-center justify-center md:min-w-0 md:min-h-0 ${
                    index === currentTestimonial
                      ? 'bg-gradient-to-r from-purple-500 to-cyan-500 shadow-lg shadow-purple-500/50'
                      : 'bg-blue-500/30 hover:bg-blue-500/50 active:bg-blue-500/70 border border-blue-400/40'
                  }`}
                  aria-label={`Go to testimonial ${index + 1}`}
                  aria-current={index === currentTestimonial ? 'true' : 'false'}
                  role="tab"
                  aria-selected={index === currentTestimonial}
                >
                  <span className={`block rounded-full ${
                    index === currentTestimonial
                      ? 'w-8 h-2 md:w-8 md:h-2'
                      : 'w-2 h-2 md:w-2 md:h-2'
                  }`} />
                </button>
              ))}
            </div>
          </div>
        </motion.div>
      </div>

      <style jsx>{`
        .partner-logo-wrapper {
          position: relative;
        }

        .partner-logo {
          display: block;
          transition: all 0.5s ease-in-out;
        }

        /* Shimmer effect on hover - intensifies the shimmer */
        .partner-logo-wrapper:hover .shimmer-effect > div {
          animation: shimmerSweep 1.5s ease-in-out infinite;
        }

        /* Testimonial card neon glow on hover */
        .testimonial-card:hover .neon-glow-border {
          opacity: 1;
          box-shadow: 
            0 0 20px rgba(139, 92, 246, 0.4),
            0 0 40px rgba(139, 92, 246, 0.2),
            0 0 60px rgba(6, 182, 212, 0.1);
          animation: neonPulseGlow 2s ease-in-out infinite;
        }

        @keyframes neonPulseGlow {
          0%, 100% {
            box-shadow: 
              0 0 15px rgba(139, 92, 246, 0.3),
              0 0 30px rgba(139, 92, 246, 0.2);
          }
          50% {
            box-shadow: 
              0 0 25px rgba(139, 92, 246, 0.5),
              0 0 50px rgba(139, 92, 246, 0.3),
              0 0 75px rgba(6, 182, 212, 0.2);
          }
        }

        /* Responsive adjustments */
        @media (max-width: 768px) {
          .testimonial-card {
            padding: 1.5rem;
          }
        }

        /* Reduced motion support */
        @media (prefers-reduced-motion: reduce) {
          .shimmer-effect > div,
          .neon-glow-border {
            animation: none !important;
          }
        }
      `}</style>
    </section>
  );
};

export default TrustBlock;
