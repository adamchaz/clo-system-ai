/**
 * Global analysis (as-of) date.
 *
 * `selected` is the date the user picked, or null to use the server default. Keeping null
 * for "default" means requests omit `analysis_date` and the backend applies its own default
 * (DEFAULT_ANALYSIS_DATE), so the frontend never hard-codes a date.
 *
 * The default and the allowed range come from GET /api/v1/config (see AnalysisDateSync).
 * The value is mirrored to the URL as `?asOf=YYYY-MM-DD`.
 */
import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export const AS_OF_PARAM = 'asOf';

export interface AnalysisDateState {
  /** User-selected date (YYYY-MM-DD), or null for the server default. */
  selected: string | null;
  /** Server default and allowed range; null until the config has loaded. */
  defaultDate: string | null;
  minDate: string | null;
  maxDate: string | null;
}

const initialState: AnalysisDateState = {
  selected: null,
  defaultDate: null,
  minDate: null,
  maxDate: null,
};

/** True for a real calendar date written as YYYY-MM-DD. */
export const isIsoDate = (value: unknown): value is string => {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const [y, m, d] = value.split('-').map(Number);
  const dt = new Date(Date.UTC(y, m - 1, d));
  return dt.getUTCFullYear() === y && dt.getUTCMonth() === m - 1 && dt.getUTCDate() === d;
};

// ISO dates compare correctly as strings.
const inRange = (value: string, state: AnalysisDateState): boolean =>
  (!state.minDate || value >= state.minDate) && (!state.maxDate || value <= state.maxDate);

/** Store null when the value is the server default, so default requests stay parameter-free. */
const normalize = (value: string | null, state: AnalysisDateState): string | null => {
  if (value === null || !isIsoDate(value) || !inRange(value, state)) return null;
  return value === state.defaultDate ? null : value;
};

const analysisDateSlice = createSlice({
  name: 'analysisDate',
  initialState,
  reducers: {
    /** Select a date. Invalid or out-of-range values are ignored. */
    setAnalysisDate(state, action: PayloadAction<string>) {
      if (isIsoDate(action.payload) && inRange(action.payload, state)) {
        state.selected = normalize(action.payload, state);
      }
    },
    resetAnalysisDate(state) {
      state.selected = null;
    },
    /** Apply GET /api/v1/config; re-validates a date picked (e.g. from the URL) before it loaded. */
    setAnalysisDateConfig(
      state,
      action: PayloadAction<{ defaultDate: string; minDate: string; maxDate: string }>
    ) {
      state.defaultDate = action.payload.defaultDate;
      state.minDate = action.payload.minDate;
      state.maxDate = action.payload.maxDate;
      state.selected = normalize(state.selected, state);
    },
  },
});

export const { setAnalysisDate, resetAnalysisDate, setAnalysisDateConfig } = analysisDateSlice.actions;

type WithAnalysisDate = { analysisDate: AnalysisDateState };

/** Date to send to the API: the user's choice, or undefined to let the server default apply. */
export const selectAnalysisDateParam = (state: WithAnalysisDate): string | undefined =>
  state.analysisDate.selected ?? undefined;

/** Date to show in the UI: the user's choice, else the server default (null until loaded). */
export const selectEffectiveAnalysisDate = (state: WithAnalysisDate): string | null =>
  state.analysisDate.selected ?? state.analysisDate.defaultDate;

export default analysisDateSlice.reducer;
