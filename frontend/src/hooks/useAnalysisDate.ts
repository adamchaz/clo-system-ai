/**
 * Read and change the global analysis (as-of) date.
 *
 * - analysisDate: date to display (user's choice, else server default; null until the
 *   server config has loaded and nothing was chosen)
 * - analysisDateParam: date to send to the API (undefined = let the server default apply)
 */
import { useCallback } from 'react';
import { useAppDispatch, useAppSelector } from './reduxHooks';
import {
  resetAnalysisDate as resetAction,
  selectAnalysisDateParam,
  selectEffectiveAnalysisDate,
  setAnalysisDate as setAction,
} from '../store/slices/analysisDateSlice';

export const useAnalysisDate = () => {
  const dispatch = useAppDispatch();
  const analysisDate = useAppSelector(selectEffectiveAnalysisDate);
  const analysisDateParam = useAppSelector(selectAnalysisDateParam);
  const { defaultDate, minDate, maxDate, selected } = useAppSelector((state) => state.analysisDate);

  const setAnalysisDate = useCallback((date: string) => dispatch(setAction(date)), [dispatch]);
  const resetAnalysisDate = useCallback(() => dispatch(resetAction()), [dispatch]);

  return {
    analysisDate,
    analysisDateParam,
    defaultDate,
    minDate,
    maxDate,
    isDefault: selected === null,
    setAnalysisDate,
    resetAnalysisDate,
  };
};

export default useAnalysisDate;
