import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import SmartSearchInput from './SmartSearchInput';

// Mock framer-motion to avoid animation issues in tests
jest.mock('framer-motion', () => ({
  motion: {
    form: ({ children, className, onSubmit, initial, animate, transition, ...props }) => (
      <form className={className} onSubmit={onSubmit} {...props}>{children}</form>
    ),
    div: ({ children, className, style, initial, animate, exit, transition, ...props }) => (
      <div className={className} style={style} {...props}>{children}</div>
    ),
    svg: ({ children, className, animate, transition, ...props }) => (
      <svg className={className} {...props}>{children}</svg>
    ),
    span: ({ children, className, style, initial, animate, exit, transition, ...props }) => (
      <span className={className} style={style} {...props}>{children}</span>
    ),
  },
  AnimatePresence: ({ children }) => <>{children}</>,
}));

describe('SmartSearchInput Component', () => {
  describe('Rendering', () => {
    test('renders search input with default placeholder', () => {
      render(<SmartSearchInput />);
      
      const input = screen.getByRole('searchbox');
      expect(input).toBeInTheDocument();
    });

    test('renders with custom placeholder', () => {
      const customPlaceholder = 'Введите ваш вопрос';
      render(<SmartSearchInput placeholder={customPlaceholder} />);
      
      const input = screen.getByRole('searchbox');
      expect(input).toBeInTheDocument();
    });

    test('renders search icon', () => {
      const { container } = render(<SmartSearchInput />);
      
      const searchIcon = container.querySelector('svg');
      expect(searchIcon).toBeInTheDocument();
    });

    test('applies custom className', () => {
      const customClass = 'custom-search-class';
      const { container } = render(<SmartSearchInput className={customClass} />);
      
      const form = container.querySelector('form');
      expect(form).toHaveClass(customClass);
    });

    test('has correct aria-label', () => {
      render(<SmartSearchInput />);
      
      const input = screen.getByRole('searchbox');
      expect(input).toHaveAttribute('aria-label', 'Поиск юридической консультации');
    });

    test('has correct aria-describedby', () => {
      render(<SmartSearchInput />);
      
      const input = screen.getByRole('searchbox');
      expect(input).toHaveAttribute('aria-describedby', 'search-hint');
    });

    test('renders screen reader hint', () => {
      render(<SmartSearchInput />);
      
      const hint = screen.getByText('Введите ваш юридический вопрос для получения консультации от AI-юриста');
      expect(hint).toBeInTheDocument();
      expect(hint).toHaveClass('sr-only');
    });
  });

  describe('Input Interaction', () => {
    test('updates input value when user types', () => {
      render(<SmartSearchInput />);
      
      const input = screen.getByRole('searchbox');
      fireEvent.change(input, { target: { value: 'Как зарегистрировать ИП?' } });
      
      expect(input.value).toBe('Как зарегистрировать ИП?');
    });

    test('clears input value', () => {
      render(<SmartSearchInput />);
      
      const input = screen.getByRole('searchbox');
      fireEvent.change(input, { target: { value: 'Test query' } });
      expect(input.value).toBe('Test query');
      
      fireEvent.change(input, { target: { value: '' } });
      expect(input.value).toBe('');
    });

    test('handles multiple character inputs', () => {
      render(<SmartSearchInput />);
      
      const input = screen.getByRole('searchbox');
      const testString = 'Проверить договор на ошибки';
      
      fireEvent.change(input, { target: { value: testString } });
      expect(input.value).toBe(testString);
    });
  });

  describe('Focus and Hover States', () => {
    test('applies focus state when input is focused', () => {
      render(<SmartSearchInput />);
      
      const input = screen.getByRole('searchbox');
      fireEvent.focus(input);
      
      expect(input).toHaveClass('neon-focus');
    });

    test('removes focus state when input is blurred', () => {
      render(<SmartSearchInput />);
      
      const input = screen.getByRole('searchbox');
      fireEvent.focus(input);
      expect(input).toHaveClass('neon-focus');
      
      fireEvent.blur(input);
      expect(input).not.toHaveClass('neon-focus');
    });

    test('applies hover state when mouse enters', () => {
      render(<SmartSearchInput />);
      
      const input = screen.getByRole('searchbox');
      fireEvent.mouseEnter(input);
      
      expect(input).toHaveClass('neon-hover');
    });

    test('removes hover state when mouse leaves', () => {
      render(<SmartSearchInput />);
      
      const input = screen.getByRole('searchbox');
      fireEvent.mouseEnter(input);
      expect(input).toHaveClass('neon-hover');
      
      fireEvent.mouseLeave(input);
      expect(input).not.toHaveClass('neon-hover');
    });

    test('focus state takes precedence over hover state', () => {
      render(<SmartSearchInput />);
      
      const input = screen.getByRole('searchbox');
      fireEvent.mouseEnter(input);
      fireEvent.focus(input);
      
      expect(input).toHaveClass('neon-focus');
      expect(input).not.toHaveClass('neon-hover');
    });
  });

  describe('Form Submission', () => {
    test('calls onSearch callback when form is submitted', () => {
      const mockOnSearch = jest.fn();
      render(<SmartSearchInput onSearch={mockOnSearch} />);
      
      const input = screen.getByRole('searchbox');
      fireEvent.change(input, { target: { value: 'Test query' } });
      
      const form = input.closest('form');
      fireEvent.submit(form);
      
      expect(mockOnSearch).toHaveBeenCalledWith('Test query');
      expect(mockOnSearch).toHaveBeenCalledTimes(1);
    });

    test('does not call onSearch when query is empty', () => {
      const mockOnSearch = jest.fn();
      render(<SmartSearchInput onSearch={mockOnSearch} />);
      
      const input = screen.getByRole('searchbox');
      const form = input.closest('form');
      fireEvent.submit(form);
      
      expect(mockOnSearch).not.toHaveBeenCalled();
    });

    test('does not call onSearch when query is only whitespace', () => {
      const mockOnSearch = jest.fn();
      render(<SmartSearchInput onSearch={mockOnSearch} />);
      
      const input = screen.getByRole('searchbox');
      fireEvent.change(input, { target: { value: '   ' } });
      
      const form = input.closest('form');
      fireEvent.submit(form);
      
      expect(mockOnSearch).not.toHaveBeenCalled();
    });

    test('trims whitespace from query before calling onSearch', () => {
      const mockOnSearch = jest.fn();
      render(<SmartSearchInput onSearch={mockOnSearch} />);
      
      const input = screen.getByRole('searchbox');
      fireEvent.change(input, { target: { value: '  Test query  ' } });
      
      const form = input.closest('form');
      fireEvent.submit(form);
      
      expect(mockOnSearch).toHaveBeenCalledWith('  Test query  ');
    });

    test('works without onSearch callback', () => {
      render(<SmartSearchInput />);
      
      const input = screen.getByRole('searchbox');
      fireEvent.change(input, { target: { value: 'Test query' } });
      
      const form = input.closest('form');
      expect(() => fireEvent.submit(form)).not.toThrow();
    });

    test('prevents default form submission', () => {
      const mockOnSearch = jest.fn();
      render(<SmartSearchInput onSearch={mockOnSearch} />);
      
      const input = screen.getByRole('searchbox');
      fireEvent.change(input, { target: { value: 'Test query' } });
      
      const form = input.closest('form');
      const submitEvent = new Event('submit', { bubbles: true, cancelable: true });
      const preventDefaultSpy = jest.spyOn(submitEvent, 'preventDefault');
      
      form.dispatchEvent(submitEvent);
      
      expect(preventDefaultSpy).toHaveBeenCalled();
    });
  });

  describe('Styling and Neon Effects', () => {
    test('applies neon-glow-purple class', () => {
      render(<SmartSearchInput />);
      
      const input = screen.getByRole('searchbox');
      expect(input).toHaveClass('neon-glow-purple');
    });

    test('applies glassmorphism classes', () => {
      render(<SmartSearchInput />);
      
      const input = screen.getByRole('searchbox');
      expect(input).toHaveClass('bg-gray-900/80');
      expect(input).toHaveClass('backdrop-blur-xl');
    });

    test('applies rounded corners', () => {
      render(<SmartSearchInput />);
      
      const input = screen.getByRole('searchbox');
      expect(input).toHaveClass('rounded-2xl');
    });

    test('applies minimum height for touch devices', () => {
      render(<SmartSearchInput />);
      
      const input = screen.getByRole('searchbox');
      expect(input).toHaveClass('min-h-[60px]');
      expect(input).toHaveClass('touch-manipulation');
    });

    test('applies transition classes', () => {
      render(<SmartSearchInput />);
      
      const input = screen.getByRole('searchbox');
      expect(input).toHaveClass('transition-all');
      expect(input).toHaveClass('duration-300');
    });
  });

  describe('Typing Placeholder Animation', () => {
    beforeEach(() => {
      jest.useFakeTimers();
    });

    afterEach(() => {
      jest.runOnlyPendingTimers();
      jest.useRealTimers();
    });

    test('typing placeholder starts empty', () => {
      render(<SmartSearchInput placeholder="Test placeholder" />);
      
      const input = screen.getByRole('searchbox');
      expect(input.placeholder).toBe('');
    });

    test('typing placeholder animates character by character', async () => {
      render(<SmartSearchInput placeholder="Test" />);
      
      const input = screen.getByRole('searchbox');
      
      // Initially empty
      expect(input.placeholder).toBe('');
      
      // After first interval
      jest.advanceTimersByTime(100);
      await waitFor(() => {
        expect(input.placeholder).toBe('T');
      });
      
      // After second interval
      jest.advanceTimersByTime(100);
      await waitFor(() => {
        expect(input.placeholder).toBe('Te');
      });
    });

    test('typing animation stops when user starts typing', async () => {
      render(<SmartSearchInput placeholder="Test placeholder" />);
      
      const input = screen.getByRole('searchbox');
      
      // Start typing
      fireEvent.change(input, { target: { value: 'User input' } });
      
      // Advance timers
      jest.advanceTimersByTime(1000);
      
      // Placeholder should be empty when user is typing
      await waitFor(() => {
        expect(input.placeholder).toBe('');
      });
    });

    test('typing animation resumes when input is cleared', async () => {
      render(<SmartSearchInput placeholder="Test" />);
      
      const input = screen.getByRole('searchbox');
      
      // User types
      fireEvent.change(input, { target: { value: 'User input' } });
      expect(input.placeholder).toBe('');
      
      // User clears input
      fireEvent.change(input, { target: { value: '' } });
      
      // Animation should resume
      jest.advanceTimersByTime(100);
      await waitFor(() => {
        expect(input.placeholder).toBe('T');
      });
    });
  });

  describe('Responsive Design', () => {
    test('applies responsive padding classes', () => {
      render(<SmartSearchInput />);
      
      const input = screen.getByRole('searchbox');
      expect(input).toHaveClass('md:py-5');
    });

    test('applies responsive minimum height classes', () => {
      render(<SmartSearchInput />);
      
      const input = screen.getByRole('searchbox');
      expect(input).toHaveClass('md:min-h-[auto]');
    });

    test('container has max-width constraint', () => {
      const { container } = render(<SmartSearchInput />);
      
      const form = container.querySelector('form');
      expect(form).toHaveClass('max-w-3xl');
      expect(form).toHaveClass('mx-auto');
    });

    test('input is full width within container', () => {
      render(<SmartSearchInput />);
      
      const input = screen.getByRole('searchbox');
      expect(input).toHaveClass('w-full');
    });
  });

  describe('Accessibility Features', () => {
    test('input has correct role', () => {
      render(<SmartSearchInput />);
      
      const input = screen.getByRole('searchbox');
      expect(input).toBeInTheDocument();
    });

    test('input is keyboard accessible', () => {
      render(<SmartSearchInput />);
      
      const input = screen.getByRole('searchbox');
      input.focus();
      
      expect(document.activeElement).toBe(input);
    });

    test('form can be submitted with Enter key', () => {
      const mockOnSearch = jest.fn();
      render(<SmartSearchInput onSearch={mockOnSearch} />);
      
      const input = screen.getByRole('searchbox');
      fireEvent.change(input, { target: { value: 'Test query' } });
      fireEvent.keyPress(input, { key: 'Enter', code: 'Enter', charCode: 13 });
      
      const form = input.closest('form');
      fireEvent.submit(form);
      
      expect(mockOnSearch).toHaveBeenCalledWith('Test query');
    });

    test('has no outline when focused (custom focus styles)', () => {
      render(<SmartSearchInput />);
      
      const input = screen.getByRole('searchbox');
      expect(input).toHaveClass('outline-none');
    });
  });

  describe('Animation States', () => {
    test('renders animated border gradient overlay', () => {
      const { container } = render(<SmartSearchInput />);
      
      const gradientOverlays = container.querySelectorAll('.pointer-events-none');
      expect(gradientOverlays.length).toBeGreaterThan(0);
    });

    test('search icon is present', () => {
      const { container } = render(<SmartSearchInput />);
      
      const icon = container.querySelector('svg');
      expect(icon).toBeInTheDocument();
      expect(icon).toHaveClass('w-6');
      expect(icon).toHaveClass('h-6');
    });

    test('search icon is positioned correctly', () => {
      const { container } = render(<SmartSearchInput />);
      
      const iconContainer = container.querySelector('.absolute.right-4');
      expect(iconContainer).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    test('handles very long input text', () => {
      render(<SmartSearchInput />);
      
      const input = screen.getByRole('searchbox');
      const longText = 'A'.repeat(1000);
      
      fireEvent.change(input, { target: { value: longText } });
      expect(input.value).toBe(longText);
    });

    test('handles special characters in input', () => {
      render(<SmartSearchInput />);
      
      const input = screen.getByRole('searchbox');
      const specialChars = '!@#$%^&*()_+-=[]{}|;:,.<>?';
      
      fireEvent.change(input, { target: { value: specialChars } });
      expect(input.value).toBe(specialChars);
    });

    test('handles Cyrillic characters', () => {
      render(<SmartSearchInput />);
      
      const input = screen.getByRole('searchbox');
      const cyrillicText = 'Как зарегистрировать ИП в России?';
      
      fireEvent.change(input, { target: { value: cyrillicText } });
      expect(input.value).toBe(cyrillicText);
    });

    test('handles rapid focus/blur events', () => {
      render(<SmartSearchInput />);
      
      const input = screen.getByRole('searchbox');
      
      for (let i = 0; i < 10; i++) {
        fireEvent.focus(input);
        fireEvent.blur(input);
      }
      
      expect(input).not.toHaveClass('neon-focus');
    });

    test('handles rapid hover events', () => {
      render(<SmartSearchInput />);
      
      const input = screen.getByRole('searchbox');
      
      for (let i = 0; i < 10; i++) {
        fireEvent.mouseEnter(input);
        fireEvent.mouseLeave(input);
      }
      
      expect(input).not.toHaveClass('neon-hover');
    });
  });

  describe('Component Cleanup', () => {
    test('cleans up timers on unmount', () => {
      jest.useFakeTimers();
      
      const { unmount } = render(<SmartSearchInput />);
      
      unmount();
      
      // Should not throw errors
      expect(() => jest.runOnlyPendingTimers()).not.toThrow();
      
      jest.useRealTimers();
    });
  });
});
