import { configureStore } from '@reduxjs/toolkit';
import { setupListeners } from '@reduxjs/toolkit/query';
import { cloApi } from './api/cloApi';
import authReducer from './slices/authSlice';
import uiReducer from './slices/uiSlice';
import { optimisticUpdatesMiddleware } from './middleware/optimisticUpdates';

export const store = configureStore({
  reducer: {
    // API slice
    [cloApi.reducerPath]: cloApi.reducer,
    
    // Feature slices
    auth: authReducer,
    ui: uiReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE'],
      },
    })
    .concat(cloApi.middleware)
    .prepend(optimisticUpdatesMiddleware.middleware),
  devTools: process.env.NODE_ENV !== 'production',
});

// Enable listener behavior for the store
setupListeners(store.dispatch);

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

// Export pre-typed hooks
export { useAppSelector, useAppDispatch } from './hooks';