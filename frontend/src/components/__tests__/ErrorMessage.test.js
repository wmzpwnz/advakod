import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import ErrorMessage from '../ErrorMessage';

describe('ErrorMessage Component', () => {
  test('renders basic error message', () => {
    render(<ErrorMessage error="Test error message" />);
    expect(screen.getByText('Test error message')).toBeInTheDocument();
  });

  test('renders retry button and calls onRetry', () => {
    const mockRetry = jest.fn();
    render(<ErrorMessage error="Test error" onRetry={mockRetry} />);
    
    const retryButton = screen.getByText('Повторить');
    fireEvent.click(retryButton);
    
    expect(mockRetry).toHaveBeenCalled();
  });

  test('handles WebSocket error codes correctly', () => {
    const error = { code: 1008, message: 'Auth failed' };
    render(<ErrorMessage error={error} />);
    
    expect(screen.getByText('Ошибка аутентификации')).toBeInTheDocument();
    expect(screen.getByText('Ваша сессия истекла. Пожалуйста, войдите в систему заново.')).toBeInTheDocument();
  });

  test('handles HTTP error codes correctly', () => {
    const error = { response: { status: 503 } };
    render(<ErrorMessage error={error} />);
    
    expect(screen.getByText('Сервер перегружен')).toBeInTheDocument();
    expect(screen.getByText('Сервер временно перегружен. Подождите немного и попробуйте снова.')).toBeInTheDocument();
  });

  test('renders in toast variant', () => {
    const { container } = render(
      <ErrorMessage error="Test error" variant="toast" />
    );
    
    expect(container.firstChild).toHaveClass('fixed', 'top-4', 'right-4');
  });

  test('renders in inline variant', () => {
    const { container } = render(
      <ErrorMessage error="Test error" variant="inline" />
    );
    
    expect(container.firstChild).toHaveClass('flex', 'items-center');
  });
});