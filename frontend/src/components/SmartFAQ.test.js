import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import SmartFAQ from './SmartFAQ';

// Mock framer-motion to avoid animation issues in tests
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, className, initial, animate, transition, ...props }) => (
      <div className={className} {...props}>{children}</div>
    ),
    p: ({ children, className, initial, animate, transition, ...props }) => (
      <p className={className} {...props}>{children}</p>
    ),
  },
  AnimatePresence: ({ children }) => <>{children}</>,
}));

describe('SmartFAQ Component', () => {
  describe('Rendering', () => {
    test('renders FAQ title and description', () => {
      render(<SmartFAQ />);
      
      expect(screen.getByText('Часто задаваемые вопросы')).toBeInTheDocument();
      expect(screen.getByText('Ответы на популярные вопросы о нашем AI-юристе')).toBeInTheDocument();
    });

    test('renders all FAQ questions', () => {
      render(<SmartFAQ />);
      
      expect(screen.getByText('Как AI может заменить юриста?')).toBeInTheDocument();
      expect(screen.getByText('Насколько безопасны мои данные?')).toBeInTheDocument();
      expect(screen.getByText('Какие типы документов можно анализировать?')).toBeInTheDocument();
      expect(screen.getByText('Сколько стоит использование сервиса?')).toBeInTheDocument();
      expect(screen.getByText('Как быстро я получу ответ на свой вопрос?')).toBeInTheDocument();
    });

    test('does not render answers initially', () => {
      render(<SmartFAQ />);
      
      // Answers should not be visible initially
      expect(screen.queryByText(/AI не заменяет, а дополняет работу юриста/)).not.toBeInTheDocument();
      expect(screen.queryByText(/Мы используем шифрование данных/)).not.toBeInTheDocument();
    });
  });

  describe('FAQ Expansion/Collapse', () => {
    test('expands FAQ item when clicked', async () => {
      render(<SmartFAQ />);
      
      const firstQuestion = screen.getByText('Как AI может заменить юриста?');
      const button = firstQuestion.closest('button');
      
      // Click to expand
      fireEvent.click(button);
      
      // Answer should now be visible
      await waitFor(() => {
        expect(screen.getByText(/AI не заменяет, а дополняет работу юриста/)).toBeInTheDocument();
      });
    });

    test('collapses FAQ item when clicked again', async () => {
      render(<SmartFAQ />);
      
      const firstQuestion = screen.getByText('Как AI может заменить юриста?');
      const button = firstQuestion.closest('button');
      
      // Click to expand
      fireEvent.click(button);
      
      await waitFor(() => {
        expect(screen.getByText(/AI не заменяет, а дополняет работу юриста/)).toBeInTheDocument();
      });
      
      // Click again to collapse
      fireEvent.click(button);
      
      await waitFor(() => {
        expect(screen.queryByText(/AI не заменяет, а дополняет работу юриста/)).not.toBeInTheDocument();
      });
    });

    test('only one FAQ item is open at a time', async () => {
      render(<SmartFAQ />);
      
      const firstQuestion = screen.getByText('Как AI может заменить юриста?');
      const secondQuestion = screen.getByText('Насколько безопасны мои данные?');
      
      const firstButton = firstQuestion.closest('button');
      const secondButton = secondQuestion.closest('button');
      
      // Open first FAQ
      fireEvent.click(firstButton);
      
      await waitFor(() => {
        expect(screen.getByText(/AI не заменяет, а дополняет работу юриста/)).toBeInTheDocument();
      });
      
      // Open second FAQ
      fireEvent.click(secondButton);
      
      await waitFor(() => {
        expect(screen.getByText(/Мы используем шифрование данных/)).toBeInTheDocument();
      });
      
      // First FAQ should now be closed
      expect(screen.queryByText(/AI не заменяет, а дополняет работу юриста/)).not.toBeInTheDocument();
    });

    test('all FAQ items can be expanded and collapsed independently', async () => {
      render(<SmartFAQ />);
      
      const questions = [
        'Как AI может заменить юриста?',
        'Насколько безопасны мои данные?',
        'Какие типы документов можно анализировать?',
        'Сколько стоит использование сервиса?',
        'Как быстро я получу ответ на свой вопрос?'
      ];
      
      // Test each FAQ item
      for (const questionText of questions) {
        const question = screen.getByText(questionText);
        const button = question.closest('button');
        
        // Expand
        fireEvent.click(button);
        
        // Verify it's expanded by checking aria-expanded
        await waitFor(() => {
          expect(button).toHaveAttribute('aria-expanded', 'true');
        });
        
        // Collapse
        fireEvent.click(button);
        
        // Verify it's collapsed
        await waitFor(() => {
          expect(button).toHaveAttribute('aria-expanded', 'false');
        });
      }
    });
  });

  describe('Accessibility', () => {
    test('FAQ buttons have correct aria-expanded attribute', () => {
      render(<SmartFAQ />);
      
      const buttons = screen.getAllByRole('button');
      
      // All buttons should have aria-expanded="false" initially
      buttons.forEach(button => {
        expect(button).toHaveAttribute('aria-expanded', 'false');
      });
    });

    test('aria-expanded changes when FAQ is opened', async () => {
      render(<SmartFAQ />);
      
      const firstQuestion = screen.getByText('Как AI может заменить юриста?');
      const button = firstQuestion.closest('button');
      
      expect(button).toHaveAttribute('aria-expanded', 'false');
      
      fireEvent.click(button);
      
      await waitFor(() => {
        expect(button).toHaveAttribute('aria-expanded', 'true');
      });
    });

    test('FAQ answers have correct aria-controls relationship', () => {
      render(<SmartFAQ />);
      
      const buttons = screen.getAllByRole('button');
      
      buttons.forEach((button, index) => {
        expect(button).toHaveAttribute('aria-controls');
        const ariaControls = button.getAttribute('aria-controls');
        expect(ariaControls).toMatch(/^faq-answer-\d+$/);
      });
    });
  });

  describe('Styling and Classes', () => {
    test('applies neon-glow-purple class to FAQ cards', () => {
      const { container } = render(<SmartFAQ />);
      
      const faqCards = container.querySelectorAll('.neon-glow-purple');
      expect(faqCards.length).toBeGreaterThan(0);
    });

    test('applies neon-pulse class when FAQ is open', async () => {
      const { container } = render(<SmartFAQ />);
      
      const firstQuestion = screen.getByText('Как AI может заменить юриста?');
      const button = firstQuestion.closest('button');
      
      fireEvent.click(button);
      
      await waitFor(() => {
        const openCard = container.querySelector('.neon-pulse');
        expect(openCard).toBeInTheDocument();
      });
    });

    test('applies glassmorphism classes', () => {
      const { container } = render(<SmartFAQ />);
      
      const glassElements = container.querySelectorAll('.backdrop-blur-md');
      expect(glassElements.length).toBeGreaterThan(0);
    });

    test('applies silver-sparkle class to chevron icons', () => {
      const { container } = render(<SmartFAQ />);
      
      const silverElements = container.querySelectorAll('.silver-sparkle');
      expect(silverElements.length).toBe(5); // One for each FAQ item
    });
  });

  describe('Animation Classes', () => {
    test('FAQ cards have proper animation classes', () => {
      const { container } = render(<SmartFAQ />);
      
      const faqCards = container.querySelectorAll('.transition-all');
      expect(faqCards.length).toBeGreaterThan(0);
    });

    test('hover effect classes are present on buttons', () => {
      const { container } = render(<SmartFAQ />);
      
      const buttons = container.querySelectorAll('button');
      buttons.forEach(button => {
        expect(button.className).toContain('hover:bg-white/5');
      });
    });
  });

  describe('Content Verification', () => {
    test('displays correct answer for first FAQ', async () => {
      render(<SmartFAQ />);
      
      const firstQuestion = screen.getByText('Как AI может заменить юриста?');
      const button = firstQuestion.closest('button');
      
      fireEvent.click(button);
      
      await waitFor(() => {
        expect(screen.getByText(/AI не заменяет, а дополняет работу юриста/)).toBeInTheDocument();
        expect(screen.getByText(/Для сложных случаев всегда рекомендуется консультация с живым специалистом/)).toBeInTheDocument();
      });
    });

    test('displays correct answer for security FAQ', async () => {
      render(<SmartFAQ />);
      
      const securityQuestion = screen.getByText('Насколько безопасны мои данные?');
      const button = securityQuestion.closest('button');
      
      fireEvent.click(button);
      
      await waitFor(() => {
        expect(screen.getByText(/Мы используем шифрование данных на уровне банков/)).toBeInTheDocument();
        expect(screen.getByText(/Ваши данные никогда не передаются третьим лицам/)).toBeInTheDocument();
      });
    });

    test('displays correct answer for pricing FAQ', async () => {
      render(<SmartFAQ />);
      
      const pricingQuestion = screen.getByText('Сколько стоит использование сервиса?');
      const button = pricingQuestion.closest('button');
      
      fireEvent.click(button);
      
      await waitFor(() => {
        expect(screen.getByText(/бесплатный план для базовых консультаций/)).toBeInTheDocument();
        expect(screen.getByText(/профессиональный план от 990₽\/месяц/)).toBeInTheDocument();
      });
    });
  });

  describe('ChevronDown Icon', () => {
    test('renders ChevronDown icons for all FAQ items', () => {
      const { container } = render(<SmartFAQ />);
      
      // lucide-react icons render as SVG elements
      const svgIcons = container.querySelectorAll('svg');
      expect(svgIcons.length).toBe(5); // One for each FAQ item
    });
  });
});
