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
import {
  CalendarToday,
  Today,
  RestoreFromTrash,
} from '@mui/icons-material';
import { format, isValid } from 'date-fns';

interface AnalysisDatePickerProps {
  analysisDate: string;
  onDateChange: (date: string) => void;
  label?: string;
  disabled?: boolean;
  helperText?: string;
  showQuickActions?: boolean;
  minDate?: string;
  maxDate?: string;
}

const AnalysisDatePicker: React.FC<AnalysisDatePickerProps> = ({
  analysisDate,
  onDateChange,
  label = 'Analysis Date',
  disabled = false,
  helperText = 'Select date for portfolio analysis',
  showQuickActions = true,
  minDate,
  maxDate,
}) => {
  const today = format(new Date(), 'yyyy-MM-dd');
  const defaultDate = '2016-03-23';
  const isDefaultDate = analysisDate === defaultDate;
  const isToday = analysisDate === today;

  const handleDateChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newDate = event.target.value;
    onDateChange(newDate);
  };

  const handleTodayClick = () => {
    onDateChange(today);
  };

  const handleResetClick = () => {
    onDateChange(defaultDate);
  };

  const getQuickActionDates = () => {
    const baseDate = new Date(2016, 2, 23); // March 23, 2016 (month is 0-indexed)
    const quickDates = [
      {
        label: 'Default',
        date: '2016-03-23',
        description: 'Default analysis date',
      },
      {
        label: 'Today',
        date: format(new Date(), 'yyyy-MM-dd'),
        description: 'Current date',
      },
      {
        label: '2016 Q1 End',
        date: '2016-03-31',
        description: 'March 31, 2016',
      },
      {
        label: '2016 Q2 End',
        date: '2016-06-30',
        description: 'June 30, 2016',
      },
      {
        label: '2016 Q3 End',
        date: '2016-09-30',
        description: 'September 30, 2016',
      },
      {
        label: '2015 Year End',
        date: '2015-12-31',
        description: 'December 31, 2015',
      },
    ];

    return quickDates;
  };

  const getLastQuarterEnd = (date: Date): Date => {
    const year = date.getFullYear();
    const month = date.getMonth();
    
    if (month >= 9) return new Date(year, 8, 30); // Q3 end: Sep 30
    if (month >= 6) return new Date(year, 5, 30); // Q2 end: Jun 30
    if (month >= 3) return new Date(year, 2, 31); // Q1 end: Mar 31
    return new Date(year - 1, 11, 31); // Previous year end: Dec 31
  };

  const isValidDate = (dateString: string): boolean => {
    if (!dateString) return false;
    const date = new Date(dateString);
    return isValid(date);
  };

  const getDateStatus = () => {
    if (!isValidDate(analysisDate)) {
      return { color: 'error' as const, text: 'Invalid date' };
    }
    
    const selectedDate = new Date(analysisDate);
    const todayDate = new Date(today);
    
    if (analysisDate === defaultDate) {
      return { color: 'primary' as const, text: 'Default' };
    } else if (selectedDate.toDateString() === todayDate.toDateString()) {
      return { color: 'success' as const, text: 'Current' };
    } else if (selectedDate < todayDate) {
      return { color: 'info' as const, text: 'Historical' };
    } else {
      return { color: 'warning' as const, text: 'Future' };
    }
  };

  const status = getDateStatus();

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
          min: minDate,
          max: maxDate || today,
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
                <Chip 
                  label={status.text}
                  color={status.color}
                  size="small"
                  variant="outlined"
                />
                {!isDefaultDate && (
                  <Tooltip title="Reset to default (March 23, 2016)">
                    <IconButton
                      size="small"
                      onClick={handleResetClick}
                      disabled={disabled}
                    >
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
            backgroundColor: isDefaultDate ? 'background.paper' : isToday ? 'success.light' : 'action.hover',
          },
        }}
      />

      {showQuickActions && !disabled && (
        <Paper 
          variant="outlined" 
          sx={{ 
            mt: 2, 
            p: 2,
            backgroundColor: 'background.default',
            borderRadius: 2,
          }}
        >
          <Typography variant="subtitle2" gutterBottom color="text.secondary">
            Quick Actions
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {getQuickActionDates().map((quickDate) => (
              <Tooltip key={quickDate.label} title={quickDate.description}>
                <Chip
                  label={quickDate.label}
                  variant={analysisDate === quickDate.date ? 'filled' : 'outlined'}
                  color={analysisDate === quickDate.date ? 'primary' : 'default'}
                  size="small"
                  onClick={() => onDateChange(quickDate.date)}
                  sx={{ 
                    cursor: 'pointer',
                    '&:hover': {
                      backgroundColor: 'action.hover',
                    },
                  }}
                />
              </Tooltip>
            ))}
          </Box>
          
          <Box sx={{ mt: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="caption" color="text.secondary">
              Selected: {isValidDate(analysisDate) 
                ? format(new Date(analysisDate), 'EEEE, MMMM do, yyyy')
                : 'Invalid date'
              }
            </Typography>
            {!isDefaultDate && (
              <Tooltip title="Reset to default (March 23, 2016)">
                <IconButton size="small" onClick={handleResetClick}>
                  <RestoreFromTrash fontSize="small" />
                </IconButton>
              </Tooltip>
            )}
          </Box>
        </Paper>
      )}
    </Box>
  );
};

export default AnalysisDatePicker;