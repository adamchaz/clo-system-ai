import {
  formatCurrency,
  formatPercent,
  formatNumber,
  capitalize,
  isValidEmail,
  getFinancialColor,
} from './index';

describe('Utility Functions', () => {
  describe('formatCurrency', () => {
    test('formats currency correctly', () => {
      expect(formatCurrency(1234.56)).toBe('$1,234.56');
      expect(formatCurrency(1000000)).toBe('$1,000,000.00');
      expect(formatCurrency(0)).toBe('$0.00');
    });
  });

  describe('formatPercent', () => {
    test('formats percentage correctly', () => {
      expect(formatPercent(25.5)).toBe('25.50%');
      expect(formatPercent(100)).toBe('100.00%');
      expect(formatPercent(0)).toBe('0.00%');
    });
  });

  describe('formatNumber', () => {
    test('formats numbers correctly', () => {
      expect(formatNumber(1234.56)).toBe('1,235');
      expect(formatNumber(1234.56, 2)).toBe('1,234.56');
    });
  });

  describe('capitalize', () => {
    test('capitalizes strings correctly', () => {
      expect(capitalize('hello')).toBe('Hello');
      expect(capitalize('WORLD')).toBe('WORLD');
      expect(capitalize('')).toBe('');
    });
  });

  describe('isValidEmail', () => {
    test('validates emails correctly', () => {
      expect(isValidEmail('test@example.com')).toBe(true);
      expect(isValidEmail('user+tag@domain.co.uk')).toBe(true);
      expect(isValidEmail('invalid-email')).toBe(false);
      expect(isValidEmail('')).toBe(false);
    });
  });

  describe('getFinancialColor', () => {
    test('returns correct colors for financial values', () => {
      expect(getFinancialColor(100)).toBe('#2e7d32'); // Green for positive
      expect(getFinancialColor(-100)).toBe('#d32f2f'); // Red for negative
      expect(getFinancialColor(0)).toBe('#757575'); // Gray for zero
    });

    test('returns correct colors for dark theme', () => {
      expect(getFinancialColor(100, 'dark')).toBe('#66bb6a');
      expect(getFinancialColor(-100, 'dark')).toBe('#f44336');
      expect(getFinancialColor(0, 'dark')).toBe('#bdbdbd');
    });
  });
});