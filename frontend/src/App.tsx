import React, { useEffect } from 'react';
import { Provider } from 'react-redux';
import { ThemeProvider } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';
import { store } from './store';
import { getTheme } from './theme';
import { useAppDispatch, useAppSelector } from './hooks/reduxHooks';
import { selectTheme } from './store/slices/uiSlice';
import { initializeAuth } from './store/slices/authSlice';
import AppRouter from './routing/AppRouter';
import './App.css';

// App content component (needs to be inside Provider to use hooks)
const AppContent: React.FC = () => {
  const dispatch = useAppDispatch();
  const themeMode = useAppSelector(selectTheme);
  const theme = getTheme(themeMode);

  useEffect(() => {
    // Initialize authentication state from localStorage on app start
    dispatch(initializeAuth());
  }, [dispatch]);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AppRouter />
    </ThemeProvider>
  );
};

function App() {
  return (
    <Provider store={store}>
      <AppContent />
    </Provider>
  );
}

export default App;
