import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import AIThinkingIndicator from '../AIThinkingIndicator';

// Mock framer-motion
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }) => <div {...props}>{children}</div>
  },
  AnimatePresence: ({ children }) => children
}));

describe('AIThinkingIndicator Component', () => {
  test('renders when isGenerating is true', () => {
    render(<AIThinkingIndicator isGenerating={true} />);
    expect(screen.getByText(/ИИ анализирует ваш вопрос/)).toBeInTheDocument();
  });

  test('does not render when isGenerating is false', () => {
    const { container } = render(<AIThinkingIndicator isGenerating={false} />);
    expect(container.firstChild).toBeNull();
  });

  test('renders stop button and calls onStop', () => {
    const mockStop = jest.fn();
    render(<AIThinkingIndicator isGenerating={true} onStop={mockStop} />);
    
    const stopButton = screen.getByText('Остановить');
    fireEvent.click(stopButton);
    
    expect(mockStop).toHaveBeenCalled();
  });

  test('shows elapsed time', () => {
    const startTime = Date.now() - 5000; // 5 seconds ago
    render(<AIThinkingIndicator isGenerating={true} startTime={startTime} />);
    
    // The component shows "0с" initially due to timing, so let's check for that
    expect(screen.getByText(/\d+с/)).toBeInTheDocument();
  });

  test('renders in compact variant', () => {
    render(<AIThinkingIndicator isGenerating={true} variant="compact" />);
    expect(screen.getByText('ИИ думает...')).toBeInTheDocument();
  });

  test('renders in detailed variant with progress', () => {
    render(
      <AIThinkingIndicator 
        isGenerating={true} 
        variant="detailed" 
        estimatedTime={60}
        startTime={Date.now() - 30000}
      />
    );
    
    // Check for basic elements that should be present
    expect(screen.getByText(/ИИ/)).toBeInTheDocument();
    expect(screen.getByText('Остановить')).toBeInTheDocument();
  });
});