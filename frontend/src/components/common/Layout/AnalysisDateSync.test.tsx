// src/__mocks__/react-router-dom.js stubs the router for most tests; URL syncing needs the real
// one. Jest 27 can't resolve react-router-dom v7 by name (its "main" points to a file that
// doesn't exist and Jest 27 ignores "exports"), so load the CommonJS build directly.
jest.mock(
  'react-router/dom',
  () => jest.requireActual('../../../../node_modules/react-router/dist/development/dom-export.js'),
  { virtual: true }
);
jest.mock('react-router-dom', () => {
  // React Router 7 needs TextEncoder at load time; jsdom doesn't provide it.
  const { TextEncoder, TextDecoder } = require('util');
  Object.assign(global, { TextEncoder, TextDecoder });
  return jest.requireActual('../../../../node_modules/react-router-dom/dist/index.js');
});

import React from 'react';
import { act, render, screen } from '@testing-library/react';
import { configureStore } from '@reduxjs/toolkit';
import { Provider } from 'react-redux';
import { MemoryRouter, useLocation, useNavigate } from 'react-router-dom';
import AnalysisDateSync from './AnalysisDateSync';
import analysisDateReducer, { resetAnalysisDate, setAnalysisDate } from '../../../store/slices/analysisDateSlice';

const mockConfig = { analysis_date: { default: '2016-03-23', min: '2010-01-01', max: '2035-12-31' } };
jest.mock('../../../store/api/cloApi', () => ({
  useGetAppConfigQuery: () => ({ data: mockConfig }),
}));

const LocationProbe: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  return (
    <>
      <div data-testid="location">{location.pathname + location.search}</div>
      <button onClick={() => navigate('/portfolios/details/MAG17')}>go</button>
    </>
  );
};

const setup = (initialUrl: string) => {
  const store = configureStore({ reducer: { analysisDate: analysisDateReducer } });
  render(
    <Provider store={store}>
      <MemoryRouter initialEntries={[initialUrl]}>
        <AnalysisDateSync />
        <LocationProbe />
      </MemoryRouter>
    </Provider>
  );
  const location = () => screen.getByTestId('location').textContent;
  const selected = () => store.getState().analysisDate.selected;
  return { store, location, selected };
};

describe('AnalysisDateSync', () => {
  it('loads the server config', () => {
    const { store } = setup('/dashboard');
    expect(store.getState().analysisDate.defaultDate).toBe('2016-03-23');
  });

  it('adopts a valid ?asOf from the URL', () => {
    const { location, selected } = setup('/portfolios?asOf=2018-06-30');
    expect(selected()).toBe('2018-06-30');
    expect(location()).toBe('/portfolios?asOf=2018-06-30');
  });

  it.each([
    ['the default date', '2016-03-23'],
    ['an out-of-range date', '2050-01-01'],
    ['a malformed date', 'junk'],
  ])('drops ?asOf when it is %s', (_label, value) => {
    const { location, selected } = setup(`/portfolios?asOf=${value}`);
    expect(selected()).toBeNull();
    expect(location()).toBe('/portfolios');
  });

  it('writes a newly selected date to the URL, keeping other parameters', () => {
    const { store, location } = setup('/portfolios?tab=2');
    act(() => {
      store.dispatch(setAnalysisDate('2017-12-31'));
    });
    expect(location()).toBe('/portfolios?tab=2&asOf=2017-12-31');
  });

  it('keeps the date when navigating to a link without ?asOf', () => {
    const { location, selected } = setup('/portfolios?asOf=2018-06-30');
    act(() => {
      screen.getByText('go').click();
    });
    expect(selected()).toBe('2018-06-30');
    expect(location()).toBe('/portfolios/details/MAG17?asOf=2018-06-30');
  });

  it('removes ?asOf when reset to the default', () => {
    const { store, location } = setup('/portfolios?asOf=2018-06-30');
    act(() => {
      store.dispatch(resetAnalysisDate());
    });
    expect(location()).toBe('/portfolios');
  });
});
