// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

// Mock framer-motion
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }) => <div {...props}>{children}</div>,
    span: ({ children, ...props }) => <span {...props}>{children}</span>
  },
  AnimatePresence: ({ children }) => <>{children}</>
}));

// Mock window.statusNotifications
global.window.statusNotifications = {
  showError: jest.fn(),
  showSuccess: jest.fn(),
  showInfo: jest.fn(),
  showModelUnavailable: jest.fn(),
  removeNotification: jest.fn()
};