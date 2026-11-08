/**
 * Keeps the global analysis date in step with the server config and the URL.
 *
 * - Loads GET /api/v1/config and stores the default date and allowed range.
 * - Mirrors the selected date to `?asOf=YYYY-MM-DD` on every page, so views can be shared,
 *   bookmarked and reloaded. A non-default date is kept in the URL when navigating; the
 *   parameter is removed when the default is in use.
 * - An `asOf` the app didn't write itself (initial load, pasted link, back button) wins
 *   over the current selection.
 *
 * Renders nothing. Mount once inside the router (AppLayout).
 */
import { useEffect, useRef } from 'react';
import { useStore } from 'react-redux';
import { useSearchParams } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../../../hooks/reduxHooks';
import type { RootState } from '../../../store';
import { useGetAppConfigQuery } from '../../../store/api/cloApi';
import {
  AS_OF_PARAM,
  isIsoDate,
  setAnalysisDate,
  setAnalysisDateConfig,
} from '../../../store/slices/analysisDateSlice';

const AnalysisDateSync: React.FC = () => {
  const dispatch = useAppDispatch();
  const store = useStore<RootState>();
  const { data: config } = useGetAppConfigQuery();
  const selected = useAppSelector((state) => state.analysisDate.selected);
  const [searchParams, setSearchParams] = useSearchParams();
  // Last value on which the URL and the store agreed.
  const synced = useRef<string | null>(null);

  useEffect(() => {
    if (config) {
      dispatch(
        setAnalysisDateConfig({
          defaultDate: config.analysis_date.default,
          minDate: config.analysis_date.min,
          maxDate: config.analysis_date.max,
        })
      );
    }
  }, [config, dispatch]);

  useEffect(() => {
    const urlValue = searchParams.get(AS_OF_PARAM);
    let want = selected;

    // URL -> store: a valid asOf we didn't write ourselves.
    if (urlValue !== synced.current && urlValue && isIsoDate(urlValue)) {
      if (urlValue !== selected) {
        dispatch(setAnalysisDate(urlValue));
        // The reducer may reject it (out of range) or normalize it (default -> null).
        want = store.getState().analysisDate.selected;
      }
      if (want === urlValue) {
        synced.current = urlValue;
        return;
      }
    }

    // store -> URL: add, update or remove asOf to match the selection.
    if (urlValue !== want) {
      const next = new URLSearchParams(searchParams);
      if (want) {
        next.set(AS_OF_PARAM, want);
      } else {
        next.delete(AS_OF_PARAM);
      }
      setSearchParams(next, { replace: true });
    }
    synced.current = want;
  }, [searchParams, selected, dispatch, setSearchParams, store]);

  return null;
};

export default AnalysisDateSync;
