import numeral from 'numeral';
import { format, parseISO, isValid } from 'date-fns';

// Number formatting utilities
export const formatCurrency = (value: number, decimals: number = 2): string => {
  return numeral(value).format(`$0,0.${'0'.repeat(decimals)}`);
};

export const formatPercent = (value: number, decimals: number = 2): string => {
  return numeral(value / 100).format(`0,0.${'0'.repeat(decimals)}%`);
};

export const formatNumber = (value: number, decimals: number = 0): string => {
  return numeral(value).format(`0,0.${'0'.repeat(decimals)}`);
};

export const formatLargeNumber = (value: number): string => {
  if (Math.abs(value) >= 1e9) {
    return numeral(value).format('$0.00a').replace('b', 'B');
  } else if (Math.abs(value) >= 1e6) {
    return numeral(value).format('$0.00a').replace('m', 'M');
  } else if (Math.abs(value) >= 1e3) {
    return numeral(value).format('$0.00a').replace('k', 'K');
  }
  return formatCurrency(value);
};

// Date formatting utilities
export const formatDate = (date: string | Date, formatStr: string = 'MM/dd/yyyy'): string => {
  try {
    const dateObj = typeof date === 'string' ? parseISO(date) : date;
    return isValid(dateObj) ? format(dateObj, formatStr) : 'Invalid Date';
  } catch {
    return 'Invalid Date';
  }
};

export const formatDateTime = (date: string | Date): string => {
  return formatDate(date, 'MM/dd/yyyy HH:mm');
};

export const formatDateRange = (startDate: string | Date, endDate: string | Date): string => {
  return `${formatDate(startDate)} - ${formatDate(endDate)}`;
};

// String utilities
export const capitalize = (str: string): string => {
  return str.charAt(0).toUpperCase() + str.slice(1);
};

export const truncate = (str: string, length: number = 50): string => {
  if (str.length <= length) return str;
  return str.slice(0, length) + '...';
};

export const slugify = (str: string): string => {
  return str
    .toLowerCase()
    .replace(/[^\w ]+/g, '')
    .replace(/ +/g, '-');
};

// Array utilities
export const groupBy = <T>(array: T[], key: keyof T): Record<string, T[]> => {
  return array.reduce((groups, item) => {
    const groupKey = String(item[key]);
    if (!groups[groupKey]) {
      groups[groupKey] = [];
    }
    groups[groupKey].push(item);
    return groups;
  }, {} as Record<string, T[]>);
};

export const sortBy = <T>(array: T[], key: keyof T, direction: 'asc' | 'desc' = 'asc'): T[] => {
  return [...array].sort((a, b) => {
    const aVal = a[key];
    const bVal = b[key];
    
    if (aVal < bVal) return direction === 'asc' ? -1 : 1;
    if (aVal > bVal) return direction === 'asc' ? 1 : -1;
    return 0;
  });
};

export const uniqueBy = <T>(array: T[], key: keyof T): T[] => {
  const seen = new Set();
  return array.filter(item => {
    const val = item[key];
    if (seen.has(val)) return false;
    seen.add(val);
    return true;
  });
};

// Object utilities
export const omit = <T extends Record<string, any>, K extends keyof T>(
  obj: T,
  keys: K[]
): Omit<T, K> => {
  const result = { ...obj };
  keys.forEach(key => delete result[key]);
  return result;
};

export const pick = <T extends Record<string, any>, K extends keyof T>(
  obj: T,
  keys: K[]
): Pick<T, K> => {
  const result = {} as Pick<T, K>;
  keys.forEach(key => {
    if (key in obj) {
      result[key] = obj[key];
    }
  });
  return result;
};

// Validation utilities
export const isValidEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

export const isValidUrl = (url: string): boolean => {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
};

// Color utilities for financial data
export const getFinancialColor = (value: number, theme: 'light' | 'dark' = 'light'): string => {
  if (value > 0) {
    return theme === 'light' ? '#2e7d32' : '#66bb6a'; // Green
  } else if (value < 0) {
    return theme === 'light' ? '#d32f2f' : '#f44336'; // Red
  }
  return theme === 'light' ? '#757575' : '#bdbdbd'; // Gray
};

export const getTrendIcon = (value: number): '↑' | '↓' | '→' => {
  if (value > 0) return '↑';
  if (value < 0) return '↓';
  return '→';
};

// File utilities
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export const getFileExtension = (filename: string): string => {
  return filename.slice((filename.lastIndexOf('.') - 1 >>> 0) + 2);
};

// Debounce utility
export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout;
  
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};

// Deep clone utility
export const deepClone = <T>(obj: T): T => {
  return JSON.parse(JSON.stringify(obj));
};

// Generate random ID
export const generateId = (): string => {
  return Date.now().toString(36) + Math.random().toString(36).substr(2);
};

// Local storage utilities with error handling
export const storage = {
  get: (key: string): any => {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : null;
    } catch {
      return null;
    }
  },
  
  set: (key: string, value: any): void => {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
      console.error('Error saving to localStorage:', error);
    }
  },
  
  remove: (key: string): void => {
    try {
      localStorage.removeItem(key);
    } catch (error) {
      console.error('Error removing from localStorage:', error);
    }
  },
  
  clear: (): void => {
    try {
      localStorage.clear();
    } catch (error) {
      console.error('Error clearing localStorage:', error);
    }
  },
};

export default {
  formatCurrency,
  formatPercent,
  formatNumber,
  formatLargeNumber,
  formatDate,
  formatDateTime,
  formatDateRange,
  capitalize,
  truncate,
  slugify,
  groupBy,
  sortBy,
  uniqueBy,
  omit,
  pick,
  isValidEmail,
  isValidUrl,
  getFinancialColor,
  getTrendIcon,
  formatFileSize,
  getFileExtension,
  debounce,
  deepClone,
  generateId,
  storage,
};