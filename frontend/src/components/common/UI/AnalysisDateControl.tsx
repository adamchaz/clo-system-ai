/**
 * Compact global analysis-date control for the top bar.
 * Shows the current as-of date; clicking opens the full AnalysisDatePicker in a popover.
 * The choice applies to every page and is mirrored to the URL (?asOf=) by AnalysisDateSync.
 */
import React, { useState } from 'react';
import { Badge, Box, Button, Popover, Tooltip, Typography } from '@mui/material';
import { Event } from '@mui/icons-material';
import { format, isValid, parseISO } from 'date-fns';
import { useAnalysisDate } from '../../../hooks/useAnalysisDate';
import AnalysisDatePicker from './AnalysisDatePicker';

const display = (value: string | null, pattern: string) => {
  if (!value) return '…';
  const d = parseISO(value);
  return isValid(d) ? format(d, pattern) : value;
};

const AnalysisDateControl: React.FC = () => {
  const { analysisDate, defaultDate, minDate, maxDate, isDefault, setAnalysisDate } = useAnalysisDate();
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);

  return (
    <>
      <Tooltip title={isDefault ? 'Analysis date (default)' : 'Analysis date (custom) - applies to all pages'}>
        <Button
          color={isDefault ? 'inherit' : 'primary'}
          variant={isDefault ? 'text' : 'outlined'}
          size="small"
          onClick={(e) => setAnchorEl(e.currentTarget)}
          startIcon={
            <Badge color="primary" variant="dot" invisible={isDefault}>
              <Event fontSize="small" />
            </Badge>
          }
          sx={{ mx: 1, textTransform: 'none', whiteSpace: 'nowrap' }}
          aria-label="Change analysis date"
        >
          As of {display(analysisDate, 'MMM d, yyyy')}
        </Button>
      </Tooltip>

      <Popover
        open={Boolean(anchorEl)}
        anchorEl={anchorEl}
        onClose={() => setAnchorEl(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        transformOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <Box sx={{ p: 2, width: 380 }}>
          <AnalysisDatePicker
            analysisDate={analysisDate ?? ''}
            onDateChange={setAnalysisDate}
            defaultDate={defaultDate}
            minDate={minDate}
            maxDate={maxDate}
            helperText="Applies to all pages"
          />
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1.5 }}>
            Each deal's holdings are a snapshot of its source data. Choosing a different date shifts
            time-based measures (e.g. years to maturity) but does not roll holdings forward; pages show
            a notice when the analysis date differs from the snapshot date.
          </Typography>
        </Box>
      </Popover>
    </>
  );
};

export default AnalysisDateControl;
