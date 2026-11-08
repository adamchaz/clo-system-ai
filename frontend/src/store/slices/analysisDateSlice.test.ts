import reducer, {
  AnalysisDateState,
  isIsoDate,
  resetAnalysisDate,
  selectAnalysisDateParam,
  selectEffectiveAnalysisDate,
  setAnalysisDate,
  setAnalysisDateConfig,
} from './analysisDateSlice';

const config = setAnalysisDateConfig({ defaultDate: '2016-03-23', minDate: '2010-01-01', maxDate: '2035-12-31' });
const withConfig = (): AnalysisDateState => reducer(undefined, config);
const select = (state: AnalysisDateState) => ({
  param: selectAnalysisDateParam({ analysisDate: state }),
  effective: selectEffectiveAnalysisDate({ analysisDate: state }),
});

describe('isIsoDate', () => {
  it.each(['2016-03-23', '2016-02-29', '2035-12-31'])('accepts %s', (v) => expect(isIsoDate(v)).toBe(true));
  it.each(['2015-02-29', '2016-13-01', '2016-3-23', 'junk', '', null, 20160323])('rejects %p', (v) =>
    expect(isIsoDate(v)).toBe(false)
  );
});

describe('analysisDateSlice', () => {
  it('starts with nothing selected and no config', () => {
    const state = reducer(undefined, { type: 'init' });
    expect(state).toEqual({ selected: null, defaultDate: null, minDate: null, maxDate: null });
    expect(select(state)).toEqual({ param: undefined, effective: null });
  });

  it('uses the server default for display but sends no date', () => {
    expect(select(withConfig())).toEqual({ param: undefined, effective: '2016-03-23' });
  });

  it('selects a valid in-range date', () => {
    const state = reducer(withConfig(), setAnalysisDate('2018-06-30'));
    expect(state.selected).toBe('2018-06-30');
    expect(select(state)).toEqual({ param: '2018-06-30', effective: '2018-06-30' });
  });

  it('stores the default date as null so requests stay parameter-free', () => {
    const state = reducer(reducer(withConfig(), setAnalysisDate('2018-06-30')), setAnalysisDate('2016-03-23'));
    expect(state.selected).toBeNull();
  });

  it.each(['junk', '2016-13-01', '2009-12-31', '2036-01-01'])('ignores invalid or out-of-range %s', (v) => {
    const state = reducer(reducer(withConfig(), setAnalysisDate('2018-06-30')), setAnalysisDate(v));
    expect(state.selected).toBe('2018-06-30');
  });

  it('accepts a date before the config loads, then re-validates it', () => {
    const early = reducer(undefined, setAnalysisDate('2050-01-01'));
    expect(early.selected).toBe('2050-01-01');
    expect(reducer(early, config).selected).toBeNull(); // out of range once the range is known

    const earlyDefault = reducer(undefined, setAnalysisDate('2016-03-23'));
    expect(reducer(earlyDefault, config).selected).toBeNull(); // normalized to "default"

    const earlyValid = reducer(undefined, setAnalysisDate('2018-06-30'));
    expect(reducer(earlyValid, config).selected).toBe('2018-06-30');
  });

  it('resets to the default', () => {
    const state = reducer(reducer(withConfig(), setAnalysisDate('2018-06-30')), resetAnalysisDate());
    expect(state.selected).toBeNull();
  });
});
