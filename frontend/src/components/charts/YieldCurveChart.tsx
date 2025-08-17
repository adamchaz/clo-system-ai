import React, { useMemo } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Typography,
  Chip,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Tooltip,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  Brush,
  Area,
  ComposedChart,
} from 'recharts';
import { format, parseISO } from 'date-fns';

import { YieldCurve } from '../../store/api/cloApi';

interface YieldCurveChartProps {
  curves: YieldCurve[];
  loading?: boolean;
  error?: string;
  height?: number;
  showControls?: boolean;
  defaultCurveIds?: number[];
  onCurveSelectionChange?: (selectedIds: number[]) => void;
}

interface ChartDataPoint {
  maturity_months: number;
  maturity_display: string;
  maturity_years: number;
  [key: string]: number | string; // Dynamic curve data
}

const YieldCurveChart: React.FC<YieldCurveChartProps> = ({
  curves,
  loading = false,
  error,
  height = 500,
  showControls = true,
  defaultCurveIds = [],
  onCurveSelectionChange,
}) => {
  const [selectedCurveIds, setSelectedCurveIds] = React.useState<number[]>(
    defaultCurveIds.length > 0 ? defaultCurveIds : curves.map(c => c.curve_id)
  );
  const [showInterpolated, setShowInterpolated] = React.useState(true);
  const [yAxisFormat, setYAxisFormat] = React.useState<'percentage' | 'bps'>('percentage');
  const [maturityUnit, setMaturityUnit] = React.useState<'months' | 'years'>('years');

  // Generate distinct colors for curves
  const curveColors = [
    '#2196F3', '#FF9800', '#4CAF50', '#F44336', '#9C27B0',
    '#00BCD4', '#8BC34A', '#FF5722', '#607D8B', '#E91E63'
  ];

  // Prepare chart data
  const chartData = useMemo(() => {
    if (!curves.length) return [];

    // Get all unique maturity points from all curves
    const allMaturities = new Set<number>();
    curves.forEach(curve => {
      curve.rates.forEach(rate => {
        if (showInterpolated || !rate.is_interpolated) {
          allMaturities.add(rate.maturity_month);
        }
      });
    });

    // Sort maturities
    const sortedMaturities = Array.from(allMaturities).sort((a, b) => a - b);

    // Create data points
    const data: ChartDataPoint[] = sortedMaturities.map(months => {
      const dataPoint: ChartDataPoint = {
        maturity_months: months,
        maturity_display: months < 12 ? `${months}M` : `${(months / 12).toFixed(1)}Y`,
        maturity_years: months / 12,
      };

      // Add rate data for each selected curve
      curves.forEach((curve, index) => {
        if (selectedCurveIds.includes(curve.curve_id)) {
          const rate = curve.rates.find(r => r.maturity_month === months);
          if (rate && (showInterpolated || !rate.is_interpolated)) {
            const rateValue = yAxisFormat === 'percentage' 
              ? rate.spot_rate * 100 
              : rate.spot_rate * 10000;
            dataPoint[`curve_${curve.curve_id}`] = rateValue;
            dataPoint[`curve_${curve.curve_id}_name`] = curve.curve_name;
          }
        }
      });

      return dataPoint;
    });

    return data;
  }, [curves, selectedCurveIds, showInterpolated, yAxisFormat]);

  // Handle curve selection change
  const handleCurveSelectionChange = (curveId: number, selected: boolean) => {
    const newSelection = selected
      ? [...selectedCurveIds, curveId]
      : selectedCurveIds.filter(id => id !== curveId);
    
    setSelectedCurveIds(newSelection);
    onCurveSelectionChange?.(newSelection);
  };

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <Card sx={{ p: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Maturity: {label}
          </Typography>
          {payload.map((entry: any, index: number) => (
            <Box key={index} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Box
                sx={{
                  width: 12,
                  height: 12,
                  backgroundColor: entry.color,
                  borderRadius: '50%',
                }}
              />
              <Typography variant="body2">
                {entry.name}: {entry.value?.toFixed(4)}{yAxisFormat === 'percentage' ? '%' : ' bps'}
              </Typography>
            </Box>
          ))}
        </Card>
      );
    }
    return null;
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        {error}
      </Alert>
    );
  }

  if (!curves.length) {
    return (
      <Alert severity="info" sx={{ m: 2 }}>
        No yield curves available to display.
      </Alert>
    );
  }

  return (
    <Card>
      <CardHeader
        title="Yield Curve Visualization"
        subheader={`Displaying ${selectedCurveIds.length} of ${curves.length} curves`}
      />
      <CardContent>
        {/* Controls */}
        {showControls && (
          <Grid container spacing={2} sx={{ mb: 3 }}>
            {/* Curve Selection */}
            <Grid size={{ xs: 12 }}>
              <Typography variant="subtitle2" gutterBottom>
                Select Curves to Display:
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {curves.map((curve, index) => (
                  <Chip
                    key={curve.curve_id}
                    label={`${curve.curve_name} (${curve.currency})`}
                    onClick={() => handleCurveSelectionChange(
                      curve.curve_id,
                      !selectedCurveIds.includes(curve.curve_id)
                    )}
                    color={selectedCurveIds.includes(curve.curve_id) ? 'primary' : 'default'}
                    variant={selectedCurveIds.includes(curve.curve_id) ? 'filled' : 'outlined'}
                    sx={{
                      borderColor: selectedCurveIds.includes(curve.curve_id)
                        ? curveColors[index % curveColors.length]
                        : undefined,
                    }}
                  />
                ))}
              </Box>
            </Grid>

            {/* Display Options */}
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={showInterpolated}
                    onChange={(e) => setShowInterpolated(e.target.checked)}
                  />
                }
                label="Show Interpolated Points"
              />
            </Grid>

            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <FormControl fullWidth size="small">
                <InputLabel>Y-Axis Format</InputLabel>
                <Select
                  value={yAxisFormat}
                  onChange={(e) => setYAxisFormat(e.target.value as 'percentage' | 'bps')}
                  label="Y-Axis Format"
                >
                  <MenuItem value="percentage">Percentage (%)</MenuItem>
                  <MenuItem value="bps">Basis Points (bps)</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <FormControl fullWidth size="small">
                <InputLabel>Maturity Unit</InputLabel>
                <Select
                  value={maturityUnit}
                  onChange={(e) => setMaturityUnit(e.target.value as 'months' | 'years')}
                  label="Maturity Unit"
                >
                  <MenuItem value="months">Months</MenuItem>
                  <MenuItem value="years">Years</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        )}

        {/* Chart */}
        <Box sx={{ width: '100%', height }}>
          <ResponsiveContainer>
            <LineChart
              data={chartData}
              margin={{
                top: 20,
                right: 30,
                left: 20,
                bottom: 60,
              }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis
                dataKey={maturityUnit === 'years' ? 'maturity_years' : 'maturity_months'}
                tick={{ fontSize: 12 }}
                tickLine={{ stroke: '#ddd' }}
                axisLine={{ stroke: '#ddd' }}
                label={{
                  value: `Maturity (${maturityUnit === 'years' ? 'Years' : 'Months'})`,
                  position: 'insideBottom',
                  offset: -10,
                }}
                tickFormatter={(value) => {
                  if (maturityUnit === 'years') {
                    return value < 1 ? `${Math.round(value * 12)}M` : `${value}Y`;
                  }
                  return value < 12 ? `${value}M` : `${Math.round(value / 12)}Y`;
                }}
              />
              <YAxis
                tick={{ fontSize: 12 }}
                tickLine={{ stroke: '#ddd' }}
                axisLine={{ stroke: '#ddd' }}
                label={{
                  value: `Interest Rate (${yAxisFormat === 'percentage' ? '%' : 'bps'})`,
                  angle: -90,
                  position: 'insideLeft',
                }}
                domain={['dataMin - 0.5', 'dataMax + 0.5']}
                tickFormatter={(value) => `${value.toFixed(2)}`}
              />
              <RechartsTooltip content={<CustomTooltip />} />
              <Legend
                wrapperStyle={{ paddingTop: '20px' }}
                formatter={(value: string) => {
                  const curveId = parseInt(value.replace('curve_', ''));
                  const curve = curves.find(c => c.curve_id === curveId);
                  return curve?.curve_name || value;
                }}
              />

              {/* Render lines for selected curves */}
              {curves.map((curve, index) => {
                if (!selectedCurveIds.includes(curve.curve_id)) return null;
                
                return (
                  <Line
                    key={curve.curve_id}
                    type="monotone"
                    dataKey={`curve_${curve.curve_id}`}
                    stroke={curveColors[index % curveColors.length]}
                    strokeWidth={2}
                    dot={{ r: 4, strokeWidth: 2 }}
                    activeDot={{ r: 6, strokeWidth: 2 }}
                    name={curve.curve_name}
                    connectNulls={false}
                  />
                );
              })}

              {/* Reference lines for common benchmarks */}
              {yAxisFormat === 'percentage' && (
                <>
                  <ReferenceLine y={2} stroke="#ff9800" strokeDasharray="5 5" />
                  <ReferenceLine y={5} stroke="#f44336" strokeDasharray="5 5" />
                </>
              )}

              {/* Brush for zooming */}
              <Brush
                dataKey={maturityUnit === 'years' ? 'maturity_years' : 'maturity_months'}
                height={30}
                stroke="#8884d8"
              />
            </LineChart>
          </ResponsiveContainer>
        </Box>

        {/* Chart Summary */}
        <Box sx={{ mt: 2 }}>
          <Grid container spacing={2}>
            {selectedCurveIds.map((curveId) => {
              const curve = curves.find(c => c.curve_id === curveId);
              if (!curve) return null;

              const minRate = Math.min(...curve.rates.map(r => r.spot_rate));
              const maxRate = Math.max(...curve.rates.map(r => r.spot_rate));

              return (
                <Grid size={{ xs: 12, sm: 6, md: 4 }} key={curveId}>
                  <Card variant="outlined" sx={{ p: 2 }}>
                    <Typography variant="subtitle2" noWrap>
                      {curve.curve_name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {curve.currency} • {format(parseISO(curve.analysis_date), 'MMM dd, yyyy')}
                    </Typography>
                    <Box sx={{ mt: 1 }}>
                      <Typography variant="body2">
                        Range: {(minRate * 100).toFixed(2)}% - {(maxRate * 100).toFixed(2)}%
                      </Typography>
                      <Typography variant="body2">
                        Points: {curve.rates.length} ({curve.rates.filter(r => !r.is_interpolated).length} original)
                      </Typography>
                    </Box>
                  </Card>
                </Grid>
              );
            })}
          </Grid>
        </Box>
      </CardContent>
    </Card>
  );
};

export default YieldCurveChart;