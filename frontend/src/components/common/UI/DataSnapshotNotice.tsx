/**
 * Warns when the analysis date differs from the date the holdings data is a snapshot of.
 *
 * Choosing another analysis date shifts time-based measures (years to maturity, long-dated
 * tests, reinvestment status) but does not roll holdings, ratings or prices forward, so the
 * results are not a projection. Renders nothing when the dates match or are unknown.
 */
import React from 'react';
import { Alert, AlertTitle } from '@mui/material';
import { format, isValid, parseISO } from 'date-fns';

interface DataSnapshotNoticeProps {
  /** Snapshot date(s) of the holdings shown (YYYY-MM-DD); several when listing many deals. */
  dataAsOf?: string | null | Array<string | null | undefined>;
  /** Analysis date in use (YYYY-MM-DD). */
  analysisDate?: string | null;
  /** Optional subject, e.g. "MAG16". */
  subject?: string;
  sx?: object;
}

const pretty = (value: string) => {
  const d = parseISO(value);
  return isValid(d) ? format(d, 'MMMM d, yyyy') : value;
};

export const snapshotDatesDiffering = (
  dataAsOf: DataSnapshotNoticeProps['dataAsOf'],
  analysisDate?: string | null
): string[] => {
  if (!analysisDate) return [];
  const dates = (Array.isArray(dataAsOf) ? dataAsOf : [dataAsOf]).filter(
    (d): d is string => typeof d === 'string' && d.length > 0
  );
  return Array.from(new Set(dates.filter((d) => d !== analysisDate))).sort();
};

const DataSnapshotNotice: React.FC<DataSnapshotNoticeProps> = ({ dataAsOf, analysisDate, subject, sx }) => {
  const differing = snapshotDatesDiffering(dataAsOf, analysisDate);
  if (!analysisDate || differing.length === 0) return null;

  const snapshotText = differing.map(pretty).join(', ');
  const holdings = subject ? `${subject} holdings are` : 'Holdings are';

  return (
    <Alert severity="info" variant="outlined" sx={{ mb: 2, ...sx }} data-testid="data-snapshot-notice">
      <AlertTitle>Analysis date differs from the data snapshot</AlertTitle>
      {holdings} a snapshot as of {snapshotText}. Results for {pretty(analysisDate)} shift
      time-based measures (e.g. years to maturity, long-dated tests) but do not roll holdings,
      ratings or prices forward.
    </Alert>
  );
};

export default DataSnapshotNotice;
