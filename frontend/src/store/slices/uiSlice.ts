import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export type ThemeMode = 'light' | 'dark';
export type NotificationSeverity = 'success' | 'info' | 'warning' | 'error';

interface Notification {
  id: string;
  message: string;
  severity: NotificationSeverity;
  timestamp: number;
  autoHideDuration?: number;
}

export interface UIState {
  theme: ThemeMode;
  sidebarOpen: boolean;
  notifications: Notification[];
  loading: {
    global: boolean;
    [key: string]: boolean;
  };
  errors: {
    [key: string]: string | null;
  };
}

const initialState: UIState = {
  theme: (localStorage.getItem('clo_theme') as ThemeMode) || 'light',
  sidebarOpen: true,
  notifications: [],
  loading: {
    global: false,
  },
  errors: {},
};

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    setTheme: (state, action: PayloadAction<ThemeMode>) => {
      state.theme = action.payload;
      localStorage.setItem('clo_theme', action.payload);
    },

    toggleTheme: (state) => {
      state.theme = state.theme === 'light' ? 'dark' : 'light';
      localStorage.setItem('clo_theme', state.theme);
    },

    setSidebarOpen: (state, action: PayloadAction<boolean>) => {
      state.sidebarOpen = action.payload;
    },

    toggleSidebar: (state) => {
      state.sidebarOpen = !state.sidebarOpen;
    },

    addNotification: (state, action: PayloadAction<Omit<Notification, 'id' | 'timestamp'>>) => {
      const notification: Notification = {
        ...action.payload,
        id: Date.now().toString(),
        timestamp: Date.now(),
      };
      state.notifications.push(notification);
    },

    removeNotification: (state, action: PayloadAction<string>) => {
      state.notifications = state.notifications.filter(
        (notification) => notification.id !== action.payload
      );
    },

    clearAllNotifications: (state) => {
      state.notifications = [];
    },

    setLoading: (state, action: PayloadAction<{ key: string; loading: boolean }>) => {
      const { key, loading } = action.payload;
      state.loading[key] = loading;
    },

    setGlobalLoading: (state, action: PayloadAction<boolean>) => {
      state.loading.global = action.payload;
    },

    setError: (state, action: PayloadAction<{ key: string; error: string | null }>) => {
      const { key, error } = action.payload;
      state.errors[key] = error;
    },

    clearError: (state, action: PayloadAction<string>) => {
      delete state.errors[action.payload];
    },

    clearAllErrors: (state) => {
      state.errors = {};
    },

    // Real-time notification helper - TASK 12
    showNotification: (state, action: PayloadAction<{
      message: string;
      type?: NotificationSeverity;
      autoHide?: boolean;
    }>) => {
      const notification: Notification = {
        id: Date.now().toString(),
        message: action.payload.message,
        severity: action.payload.type || 'info',
        timestamp: Date.now(),
        autoHideDuration: action.payload.autoHide ? 5000 : undefined,
      };
      state.notifications.push(notification);
    },
  },
});

export const {
  setTheme,
  toggleTheme,
  setSidebarOpen,
  toggleSidebar,
  addNotification,
  removeNotification,
  clearAllNotifications,
  setLoading,
  setGlobalLoading,
  setError,
  clearError,
  clearAllErrors,
  showNotification,
} = uiSlice.actions;

// Selectors
export const selectTheme = (state: { ui: UIState }) => state.ui.theme;
export const selectSidebarOpen = (state: { ui: UIState }) => state.ui.sidebarOpen;
export const selectNotifications = (state: { ui: UIState }) => state.ui.notifications;
export const selectLoading = (key: string) => (state: { ui: UIState }) => state.ui.loading[key] || false;
export const selectGlobalLoading = (state: { ui: UIState }) => state.ui.loading.global;
export const selectError = (key: string) => (state: { ui: UIState }) => state.ui.errors[key];

export default uiSlice.reducer;