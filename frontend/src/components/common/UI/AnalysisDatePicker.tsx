import React from 'react';
import {
  Box,
  TextField,
  InputAdornment,
  IconButton,
  Tooltip,
  Typography,
  Paper,
  Chip,
} from '@mui/material';
import { CalendarToday, RestoreFromTrash } from '@mui/icons-material';
import { format, isValid, parseISO } from 'date-fns';

interface AnalysisDatePickerProps {
  /** Selected date, YYYY-MM-DD. */
  analysisDate: string;
  onDateChange: (date: string) => void;
  /** Server default analysis date (YYYY-MM-DD), from GET /api/v1/config. */
  defaultDate?: string | null;
  label?: string;
  disabled?: boolean;
  helperText?: string;
  showQuickActions?: boolean;
  minDate?: string | null;
  maxDate?: string | null;
}

// parseISO treats YYYY-MM-DD as a local date; new Date('YYYY-MM-DD') would be UTC midnight
// and display as the previous day west of Greenwich.
const toDate = (value?: string | null): Date | null => {
  if (!value) return null;
  const d = parseISO(value);
  return isValid(d) ? d : null;
};

const fmt = (value: string | null | undefined, pattern: string): string => {
  const d = toDate(value);
  return d ? format(d, pattern) : 'Invalid date';
};

/** Quarter-ends of the default date's year plus the prior year-end, within the allowed range. */
const buildQuickDates = (defaultDate?: string | null, minDate?: string | null, maxDate?: string | null) => {
  const base = toDate(defaultDate);
  if (!base || !defaultDate) return [];
  const y = base.getFullYear();
  const candidates = [
    { label: 'Default', date: defaultDate, description: `Default analysis date (${fmt(defaultDate, 'MMM d, yyyy')})` },
    { label: `${y - 1} Year End`, date: `${y - 1}-12-31`, description: `December 31, ${y - 1}` },
    { label: `${y} Q1 End`, date: `${y}-03-31`, description: `March 31, ${y}` },
    { label: `${y} Q2 End`, date: `${y}-06-30`, description: `June 30, ${y}` },
    { label: `${y} Q3 End`, date: `${y}-09-30`, description: `September 30, ${y}` },
    { label: `${y} Year End`, date: `${y}-12-31`, description: `December 31, ${y}` },
  ];
  const seen = new Set<string>();
  return candidates.filter((q) => {
    if (seen.has(q.date)) return false;
    seen.add(q.date);
    return (!minDate || q.date >= minDate) && (!maxDate || q.date <= maxDate);
  });
};

const AnalysisDatePicker: React.FC<AnalysisDatePickerProps> = ({
  analysisDate,
  onDateChange,
  defaultDate,
  label = 'Analysis Date',
  disabled = false,
  helperText = 'Select date for portfolio analysis',
  showQuickActions = true,
  minDate,
  maxDate,
}) => {
  const isDefaultDate = !!defaultDate && analysisDate === defaultDate;
  const quickDates = buildQuickDates(defaultDate, minDate, maxDate);

  const handleDateChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    onDateChange(event.target.value);
  };

  const handleResetClick = () => {
    if (defaultDate) onDateChange(defaultDate);
  };

  const getDateStatus = () => {
    const selected = toDate(analysisDate);
    if (!selected) return { color: 'error' as const, text: 'Invalid date' };
    if (isDefaultDate) return { color: 'primary' as const, text: 'Default' };
    const base = toDate(defaultDate);
    if (base && selected < base) return { color: 'info' as const, text: 'Earlier' };
    if (base && selected > base) return { color: 'warning' as const, text: 'Later' };
    return { color: 'default' as const, text: 'Custom' };
  };

  const status = getDateStatus();
  const resetTooltip = defaultDate ? `Reset to default (${fmt(defaultDate, 'MMMM d, yyyy')})` : 'Reset to default';

  return (
    <Box>
      <TextField
        fullWidth
        type="date"
        label={label}
        value={analysisDate}
        onChange={handleDateChange}
        disabled={disabled}
        helperText={helperText}
        inputProps={{
          min: minDate ?? undefined,
          max: maxDate ?? undefined,
        }}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <CalendarToday color="primary" fontSize="small" />
            </InputAdornment>
          ),
          endAdornment: (
            <InputAdornment position="end">
              <Box sx={{ display: 'flex', gap: 0.5, alignItems: 'center' }}>
                <Chip label={status.text} color={status.color} size="small" variant="outlined" />
                {!isDefaultDate && defaultDate && (
                  <Tooltip title={resetTooltip}>
                    <IconButton size="small" onClick={handleResetClick} disabled={disabled}>
                      <RestoreFromTrash fontSize="small" />
                    </IconButton>
                  </Tooltip>
                )}
              </Box>
            </InputAdornment>
          ),
        }}
        sx={{
          '& .MuiOutlinedInput-root': {
            backgroundColor: isDefaultDate ? 'background.paper' : 'action.hover',
          },
        }}
      />

      {showQuickActions && !disabled && quickDates.length > 0 && (
        <Paper
          variant="outlined"
          sx={{ mt: 2, p: 2, backgroundColor: 'background.default', borderRadius: 2 }}
        >
          <Typography variant="subtitle2" gutterBottom color="text.secondary">
            Quick Actions
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {quickDates.map((quickDate) => (
              <Tooltip key={quickDate.date} title={quickDate.description}>
                <Chip
                  label={quickDate.label}
                  variant={analysisDate === quickDate.date ? 'filled' : 'outlined'}
                  color={analysisDate === quickDate.date ? 'primary' : 'default'}
                  size="small"
                  onClick={() => onDateChange(quickDate.date)}
                  sx={{ cursor: 'pointer', '&:hover': { backgroundColor: 'action.hover' } }}
                />
              </Tooltip>
            ))}
          </Box>

          <Box sx={{ mt: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="caption" color="text.secondary">
              Selected: {fmt(analysisDate, 'EEEE, MMMM do, yyyy')}
            </Typography>
          </Box>
        </Paper>
      )}
    </Box>
  );
};

export default AnalysisDatePicker;
