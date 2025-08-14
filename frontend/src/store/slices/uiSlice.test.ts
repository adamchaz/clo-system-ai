import uiReducer, {
  setTheme,
  toggleTheme,
  setSidebarOpen,
  toggleSidebar,
  addNotification,
  removeNotification,
} from './uiSlice';

describe('uiSlice', () => {
  const initialState = {
    theme: 'light' as const,
    sidebarOpen: true,
    notifications: [],
    loading: {
      global: false,
    },
    errors: {},
  };

  test('should return the initial state', () => {
    expect(uiReducer(undefined, { type: 'unknown' })).toEqual(initialState);
  });

  test('should handle setTheme', () => {
    const actual = uiReducer(initialState, setTheme('dark'));
    expect(actual.theme).toEqual('dark');
  });

  test('should handle toggleTheme', () => {
    const actual = uiReducer(initialState, toggleTheme());
    expect(actual.theme).toEqual('dark');
    
    const toggledBack = uiReducer(actual, toggleTheme());
    expect(toggledBack.theme).toEqual('light');
  });

  test('should handle setSidebarOpen', () => {
    const actual = uiReducer(initialState, setSidebarOpen(false));
    expect(actual.sidebarOpen).toEqual(false);
  });

  test('should handle toggleSidebar', () => {
    const actual = uiReducer(initialState, toggleSidebar());
    expect(actual.sidebarOpen).toEqual(false);
  });

  test('should handle addNotification', () => {
    const notification = {
      message: 'Test notification',
      severity: 'success' as const,
    };
    
    const actual = uiReducer(initialState, addNotification(notification));
    expect(actual.notifications).toHaveLength(1);
    expect(actual.notifications[0].message).toEqual('Test notification');
    expect(actual.notifications[0].severity).toEqual('success');
  });

  test('should handle removeNotification', () => {
    const stateWithNotification = {
      ...initialState,
      notifications: [
        {
          id: 'test-id',
          message: 'Test',
          severity: 'info' as const,
          timestamp: Date.now(),
        },
      ],
    };
    
    const actual = uiReducer(stateWithNotification, removeNotification('test-id'));
    expect(actual.notifications).toHaveLength(0);
  });
});