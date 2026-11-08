import React from 'react';
import { render, screen } from '@testing-library/react';
import DataSnapshotNotice, { snapshotDatesDiffering } from './DataSnapshotNotice';

describe('snapshotDatesDiffering', () => {
  it('is empty when the analysis date matches or is unknown', () => {
    expect(snapshotDatesDiffering('2016-03-23', '2016-03-23')).toEqual([]);
    expect(snapshotDatesDiffering('2016-03-23', null)).toEqual([]);
    expect(snapshotDatesDiffering(null, '2018-06-30')).toEqual([]);
    expect(snapshotDatesDiffering([], '2018-06-30')).toEqual([]);
  });

  it('returns the distinct snapshot dates that differ, sorted', () => {
    expect(snapshotDatesDiffering(['2016-03-23', null, '2016-03-23', '2015-12-31'], '2018-06-30')).toEqual([
      '2015-12-31',
      '2016-03-23',
    ]);
    expect(snapshotDatesDiffering(['2016-03-23', '2018-06-30'], '2018-06-30')).toEqual(['2016-03-23']);
  });
});

describe('DataSnapshotNotice', () => {
  it('renders nothing when the analysis date is the snapshot date', () => {
    render(<DataSnapshotNotice dataAsOf="2016-03-23" analysisDate="2016-03-23" />);
    expect(screen.queryByTestId('data-snapshot-notice')).toBeNull();
  });

  it('renders nothing while dates are unknown', () => {
    render(<DataSnapshotNotice dataAsOf={undefined} analysisDate="2018-06-30" />);
    render(<DataSnapshotNotice dataAsOf="2016-03-23" analysisDate={null} />);
    expect(screen.queryByTestId('data-snapshot-notice')).toBeNull();
  });

  it('explains the difference for a single deal', () => {
    render(<DataSnapshotNotice dataAsOf="2016-03-23" analysisDate="2018-06-30" subject="MAG16" />);
    const notice = screen.getByTestId('data-snapshot-notice');
    expect(notice).toHaveTextContent('MAG16 holdings are a snapshot as of March 23, 2016');
    expect(notice).toHaveTextContent('Results for June 30, 2018 shift time-based measures');
    expect(notice).toHaveTextContent('do not roll holdings');
  });

  it('lists distinct snapshot dates for many deals', () => {
    render(<DataSnapshotNotice dataAsOf={['2016-03-23', '2016-03-23', null]} analysisDate="2018-06-30" />);
    expect(screen.getByTestId('data-snapshot-notice')).toHaveTextContent(
      'Holdings are a snapshot as of March 23, 2016.'
    );
  });
});
