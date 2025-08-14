import { createTheme, Theme } from '@mui/material/styles';
import { ThemeMode } from '../store/slices/uiSlice';

// Define custom palette colors for financial application
declare module '@mui/material/styles' {
  interface Palette {
    financial: {
      positive: string;
      negative: string;
      neutral: string;
      warning: string;
      accent: string;
    };
    chart: {
      primary: string;
      secondary: string;
      tertiary: string;
      quaternary: string;
      background: string;
      grid: string;
    };
  }

  interface PaletteOptions {
    financial?: {
      positive: string;
      negative: string;
      neutral: string;
      warning: string;
      accent: string;
    };
    chart?: {
      primary: string;
      secondary: string;
      tertiary: string;
      quaternary: string;
      background: string;
      grid: string;
    };
  }
}

// Base theme configuration shared between light and dark modes
const baseTheme = {
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontWeight: 600,
      fontSize: '2.5rem',
    },
    h2: {
      fontWeight: 600,
      fontSize: '2rem',
    },
    h3: {
      fontWeight: 600,
      fontSize: '1.75rem',
    },
    h4: {
      fontWeight: 600,
      fontSize: '1.5rem',
    },
    h5: {
      fontWeight: 600,
      fontSize: '1.25rem',
    },
    h6: {
      fontWeight: 600,
      fontSize: '1rem',
    },
    subtitle1: {
      fontWeight: 500,
    },
    subtitle2: {
      fontWeight: 500,
    },
    body1: {
      fontSize: '0.875rem',
    },
    body2: {
      fontSize: '0.75rem',
    },
    button: {
      fontWeight: 600,
      textTransform: 'none' as const,
    },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none' as const,
          fontWeight: 600,
          padding: '8px 16px',
        },
        containedPrimary: {
          boxShadow: 'none',
          '&:hover': {
            boxShadow: 'none',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          border: '1px solid rgba(0,0,0,0.05)',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
      },
    },
    MuiDataGrid: {
      styleOverrides: {
        root: {
          border: 'none',
          '& .MuiDataGrid-cell': {
            borderColor: 'rgba(0,0,0,0.05)',
          },
          '& .MuiDataGrid-columnHeaders': {
            backgroundColor: 'rgba(0,0,0,0.02)',
            borderColor: 'rgba(0,0,0,0.05)',
          },
        },
      },
    },
  },
};

// Light theme configuration
const lightTheme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1565c0', // Deep blue for primary actions
      light: '#5e92f3',
      dark: '#003c8f',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#757575', // Neutral gray for secondary actions
      light: '#a4a4a4',
      dark: '#494949',
      contrastText: '#ffffff',
    },
    error: {
      main: '#d32f2f',
      light: '#ef5350',
      dark: '#c62828',
    },
    warning: {
      main: '#ed6c02',
      light: '#ff9800',
      dark: '#e65100',
    },
    info: {
      main: '#0288d1',
      light: '#03a9f4',
      dark: '#01579b',
    },
    success: {
      main: '#2e7d32',
      light: '#4caf50',
      dark: '#1b5e20',
    },
    background: {
      default: '#f8f9fa',
      paper: '#ffffff',
    },
    text: {
      primary: '#1a1a1a',
      secondary: '#6c757d',
    },
    financial: {
      positive: '#2e7d32', // Green for gains
      negative: '#d32f2f', // Red for losses
      neutral: '#757575', // Gray for neutral
      warning: '#ed6c02', // Orange for warnings
      accent: '#1565c0', // Blue for highlights
    },
    chart: {
      primary: '#1565c0',
      secondary: '#2e7d32',
      tertiary: '#d32f2f',
      quaternary: '#ed6c02',
      background: '#ffffff',
      grid: '#e0e0e0',
    },
  },
  ...baseTheme,
});

// Dark theme configuration
const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#90caf9', // Lighter blue for dark mode
      light: '#bbdefb',
      dark: '#42a5f5',
      contrastText: '#000000',
    },
    secondary: {
      main: '#bdbdbd',
      light: '#e0e0e0',
      dark: '#9e9e9e',
      contrastText: '#000000',
    },
    error: {
      main: '#f44336',
      light: '#ef5350',
      dark: '#d32f2f',
    },
    warning: {
      main: '#ff9800',
      light: '#ffb74d',
      dark: '#f57c00',
    },
    info: {
      main: '#29b6f6',
      light: '#4fc3f7',
      dark: '#0288d1',
    },
    success: {
      main: '#66bb6a',
      light: '#81c784',
      dark: '#388e3c',
    },
    background: {
      default: '#121212',
      paper: '#1e1e1e',
    },
    text: {
      primary: '#ffffff',
      secondary: '#aaaaaa',
    },
    financial: {
      positive: '#66bb6a', // Lighter green for dark mode
      negative: '#f44336', // Slightly lighter red
      neutral: '#bdbdbd', // Light gray
      warning: '#ff9800', // Orange
      accent: '#90caf9', // Light blue
    },
    chart: {
      primary: '#90caf9',
      secondary: '#66bb6a',
      tertiary: '#f44336',
      quaternary: '#ff9800',
      background: '#1e1e1e',
      grid: '#404040',
    },
  },
  ...baseTheme,
});

export const getTheme = (mode: ThemeMode): Theme => {
  return mode === 'light' ? lightTheme : darkTheme;
};

export { lightTheme, darkTheme };