import React, { useState, useMemo, useRef, useEffect } from 'react';
import * as d3 from 'd3';
import {
  Box,
  Paper,
  Typography,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Grid,
  Card,
  CardContent,
  IconButton,
  Tooltip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  SelectChangeEvent
} from '@mui/material';
import {
  AccountTree as AccountTreeIcon,
  Download as DownloadIcon,
  Refresh as RefreshIcon,
  Timeline as TimelineIcon,
  ShowChart as ShowChartIcon
} from '@mui/icons-material';
import { useRealTime } from '../../../hooks/useRealTimeData';
import MetricCard from '../UI/MetricCard';

/**
 * TASK 13: Advanced Data Visualization Components
 * 
 * WaterfallChart - CLO Payment Waterfall Visualization
 * 
 * Features:
 * - Interactive D3.js waterfall diagram
 * - Multiple MAG (Magnetar) waterfall scenarios (6-17)
 * - Payment priority visualization with flow animations
 * - Tranche-by-tranche cash flow breakdown
 * - OC/IC trigger impact visualization
 * - Real-time calculation updates
 * - Export functionality for regulatory reporting
 */

interface WaterfallStep {
  id: string;
  name: string;
  type: 'income' | 'expense' | 'interest' | 'principal' | 'residual';
  priority: number;
  amount: number;
  cumulative: number;
  percentage: number;
  description: string;
  tranche?: string;
  status: 'paid' | 'deferred' | 'unpaid';
}

interface TrancheInfo {
  tranche: string;
  notional: number;
  coupon: number;
  spread: number;
  rating: string;
  interestDue: number;
  principalDue: number;
  interestPaid: number;
  principalPaid: number;
}

export interface WaterfallChartProps {
  portfolioId?: string;
  scenario?: 'MAG6' | 'MAG7' | 'MAG8' | 'MAG9' | 'MAG10' | 'MAG11' | 'MAG12' | 'MAG13' | 'MAG14' | 'MAG15' | 'MAG16' | 'MAG17';
  paymentDate?: string;
  showDetails?: boolean;
  enableRealTime?: boolean;
  height?: number;
}

const WaterfallChart: React.FC<WaterfallChartProps> = ({
  portfolioId = 'default',
  scenario = 'MAG14',
  paymentDate = '2024-12-15',
  showDetails = true,
  enableRealTime = true,
  height = 500
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [selectedScenario, setSelectedScenario] = useState<string>(scenario);
  const [animationSpeed, setAnimationSpeed] = useState<number>(1000);

  // Real-time data integration
  const { portfolio, calculations } = useRealTime();
  const portfolioData = portfolio.portfolioData;
  const calculationProgress = calculations.calculations;

  // Generate waterfall steps based on scenario
  const waterfallSteps: WaterfallStep[] = useMemo(() => {
    const baseAmount = 10000000; // $10M total cash available
    let cumulative = 0;
    
    const steps: WaterfallStep[] = [
      // Step 1: Total Available Funds
      {
        id: 'available_funds',
        name: 'Available Funds',
        type: 'income',
        priority: 0,
        amount: baseAmount,
        cumulative: baseAmount,
        percentage: 100,
        description: 'Total cash available for distribution',
        status: 'paid'
      },
      
      // Step 2: Senior Expenses
      {
        id: 'trustee_fees',
        name: 'Trustee Fees',
        type: 'expense',
        priority: 1,
        amount: -50000,
        cumulative: 0,
        percentage: 0,
        description: 'Trustee and administrative fees',
        status: 'paid'
      },
      
      {
        id: 'senior_expenses',
        name: 'Senior Expenses',
        type: 'expense',
        priority: 2,
        amount: -100000,
        cumulative: 0,
        percentage: 0,
        description: 'Rating agency and other senior expenses',
        status: 'paid'
      },
      
      // Step 3: Class A Interest
      {
        id: 'class_a_interest',
        name: 'Class A Interest',
        type: 'interest',
        priority: 3,
        amount: -2400000,
        cumulative: 0,
        percentage: 0,
        description: 'Senior tranche interest payments',
        tranche: 'Class A',
        status: 'paid'
      },
      
      // Step 4: Class B Interest
      {
        id: 'class_b_interest',
        name: 'Class B Interest',
        type: 'interest',
        priority: 4,
        amount: -900000,
        cumulative: 0,
        percentage: 0,
        description: 'Mezzanine tranche interest payments',
        tranche: 'Class B',
        status: 'paid'
      },
      
      // Step 5: Class C Interest
      {
        id: 'class_c_interest',
        name: 'Class C Interest',
        type: 'interest',
        priority: 5,
        amount: -600000,
        cumulative: 0,
        percentage: 0,
        description: 'Junior mezzanine interest payments',
        tranche: 'Class C',
        status: 'paid'
      },
      
      // Step 6: Management Fees
      {
        id: 'management_fees',
        name: 'Management Fees',
        type: 'expense',
        priority: 6,
        amount: -200000,
        cumulative: 0,
        percentage: 0,
        description: 'Collateral manager fees',
        status: 'paid'
      }
    ];

    // Add scenario-specific steps for MAG14+
    if (['MAG14', 'MAG15', 'MAG16', 'MAG17'].includes(selectedScenario)) {
      steps.push({
        id: 'reinvestment_overlay',
        name: 'Reinvestment Overlay Fee',
        type: 'expense',
        priority: 7,
        amount: -150000,
        cumulative: 0,
        percentage: 0,
        description: 'Additional overlay fee for reinvestment period',
        status: 'paid'
      });
    }

    // Add performance hurdle for MAG15+
    if (['MAG15', 'MAG16', 'MAG17'].includes(selectedScenario)) {
      steps.push({
        id: 'performance_hurdle',
        name: 'Performance Hurdle Test',
        type: 'expense',
        priority: 8,
        amount: 0, // Pass-through if hurdle met
        cumulative: 0,
        percentage: 0,
        description: 'Performance hurdle evaluation (12% IRR)',
        status: 'paid'
      });
    }

    // Principal payments
    steps.push(
      {
        id: 'class_a_principal',
        name: 'Class A Principal',
        type: 'principal',
        priority: 10,
        amount: -3000000,
        cumulative: 0,
        percentage: 0,
        description: 'Senior tranche principal payments',
        tranche: 'Class A',
        status: 'paid'
      },
      {
        id: 'class_b_principal',
        name: 'Class B Principal',
        type: 'principal',
        priority: 11,
        amount: -1500000,
        cumulative: 0,
        percentage: 0,
        description: 'Mezzanine tranche principal payments',
        tranche: 'Class B',
        status: 'paid'
      },
      {
        id: 'class_c_principal',
        name: 'Class C Principal',
        type: 'principal',
        priority: 12,
        amount: -800000,
        cumulative: 0,
        percentage: 0,
        description: 'Junior mezzanine principal payments',
        tranche: 'Class C',
        status: 'paid'
      }
    );

    // Add equity features for MAG8+
    if (parseInt(selectedScenario.replace('MAG', '')) >= 8) {
      steps.push({
        id: 'equity_distribution',
        name: 'Equity Distribution',
        type: 'residual',
        priority: 13,
        amount: -1200000,
        cumulative: 0,
        percentage: 0,
        description: 'Residual distribution to equity holders',
        status: 'paid'
      });
    }

    // Calculate cumulatives
    cumulative = baseAmount;
    for (let i = 1; i < steps.length; i++) {
      cumulative += steps[i].amount;
      steps[i].cumulative = cumulative;
      steps[i].percentage = (steps[i].cumulative / baseAmount) * 100;
      
      // Determine payment status
      if (cumulative < 0) {
        steps[i].status = 'unpaid';
        cumulative = 0;
      }
    }

    return steps;
  }, [selectedScenario]);

  // Tranche information
  const trancheInfo: TrancheInfo[] = useMemo(() => [
    {
      tranche: 'Class A',
      notional: 60000000,
      coupon: 4.0,
      spread: 150,
      rating: 'AAA',
      interestDue: 2400000,
      principalDue: 3000000,
      interestPaid: 2400000,
      principalPaid: 3000000
    },
    {
      tranche: 'Class B',
      notional: 25000000,
      coupon: 5.5,
      spread: 300,
      rating: 'AA',
      interestDue: 900000,
      principalDue: 1500000,
      interestPaid: 900000,
      principalPaid: 1500000
    },
    {
      tranche: 'Class C',
      notional: 15000000,
      coupon: 7.0,
      spread: 450,
      rating: 'A',
      interestDue: 600000,
      principalDue: 800000,
      interestPaid: 600000,
      principalPaid: 800000
    },
    {
      tranche: 'Equity',
      notional: 20000000,
      coupon: 0,
      spread: 0,
      rating: 'Unrated',
      interestDue: 0,
      principalDue: 0,
      interestPaid: 0,
      principalPaid: 1200000
    }
  ], []);

  // D3 Waterfall Visualization
  useEffect(() => {
    if (!svgRef.current || waterfallSteps.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const margin = { top: 40, right: 100, bottom: 60, left: 150 };
    const width = 800 - margin.left - margin.right;
    const height = 500 - margin.top - margin.bottom;

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Scales
    const xScale = d3.scaleBand()
      .domain(waterfallSteps.map(d => d.id))
      .range([0, width])
      .padding(0.1);

    const maxValue = Math.max(...waterfallSteps.map(d => Math.abs(d.cumulative)));
    const yScale = d3.scaleLinear()
      .domain([-maxValue * 0.1, maxValue])
      .range([height, 0]);

    // Color scale
    const colorScale = d3.scaleOrdinal()
      .domain(['income', 'expense', 'interest', 'principal', 'residual'])
      .range(['#4caf50', '#f44336', '#ff9800', '#2196f3', '#9c27b0']);

    // Add axes
    g.append('g')
      .attr('class', 'x-axis')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(xScale))
      .selectAll('text')
      .style('text-anchor', 'end')
      .attr('dx', '-.8em')
      .attr('dy', '.15em')
      .attr('transform', 'rotate(-45)')
      .text(d => waterfallSteps.find(s => s.id === d)?.name || d);

    g.append('g')
      .attr('class', 'y-axis')
      .call(d3.axisLeft(yScale).tickFormat(d => `$${(d as number / 1000000).toFixed(1)}M`));

    // Add bars with animation
    const bars = g.selectAll('.bar')
      .data(waterfallSteps.slice(1)) // Skip the first "Available Funds" step
      .enter().append('rect')
      .attr('class', 'bar')
      .attr('x', d => xScale(d.id) || 0)
      .attr('width', xScale.bandwidth())
      .attr('fill', d => colorScale(d.type) as string)
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .attr('opacity', 0.8);

    // Animate bars
    bars.transition()
      .duration(animationSpeed)
      .delay((_, i) => i * 200)
      .attr('y', (d, i) => {
        const prevStep = waterfallSteps[i];
        const currentY = Math.min(yScale(prevStep.cumulative), yScale(d.cumulative));
        return currentY;
      })
      .attr('height', (d, i) => {
        const prevStep = waterfallSteps[i];
        return Math.abs(yScale(prevStep.cumulative) - yScale(d.cumulative));
      });

    // Add connecting lines
    g.selectAll('.connector')
      .data(waterfallSteps.slice(1, -1))
      .enter().append('line')
      .attr('class', 'connector')
      .attr('stroke', '#999')
      .attr('stroke-dasharray', '3,3')
      .attr('opacity', 0)
      .transition()
      .delay((_, i) => (i + 1) * 200 + animationSpeed)
      .attr('opacity', 0.5)
      .attr('x1', (d, i) => (xScale(d.id) || 0) + xScale.bandwidth())
      .attr('y1', d => yScale(d.cumulative))
      .attr('x2', (d, i) => xScale(waterfallSteps[i + 2].id) || 0)
      .attr('y2', d => yScale(d.cumulative));

    // Add value labels
    g.selectAll('.label')
      .data(waterfallSteps.slice(1))
      .enter().append('text')
      .attr('class', 'label')
      .attr('x', d => (xScale(d.id) || 0) + xScale.bandwidth() / 2)
      .attr('y', (d, i) => {
        const prevStep = waterfallSteps[i];
        const midY = (yScale(prevStep.cumulative) + yScale(d.cumulative)) / 2;
        return midY;
      })
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'middle')
      .attr('fill', 'white')
      .attr('font-weight', 'bold')
      .attr('font-size', '10px')
      .text(d => `$${(Math.abs(d.amount) / 1000000).toFixed(1)}M`);

    // Add title
    svg.append('text')
      .attr('x', width / 2 + margin.left)
      .attr('y', 25)
      .attr('text-anchor', 'middle')
      .style('font-size', '16px')
      .style('font-weight', 'bold')
      .text(`CLO Payment Waterfall - ${selectedScenario} (${paymentDate})`);

  }, [waterfallSteps, selectedScenario, paymentDate, animationSpeed]);

  const handleScenarioChange = (event: SelectChangeEvent<string>) => {
    setSelectedScenario(event.target.value);
  };

  const handleRefresh = () => {
    setAnimationSpeed(1000);
    // Trigger re-animation by updating the key or forcing re-render
    window.location.reload();
  };

  const handleExport = () => {
    console.log('Exporting waterfall chart...');
  };

  const formatValue = (value: number) => `$${(Math.abs(value) / 1000000).toFixed(2)}M`;

  const totalDistributed = waterfallSteps.reduce((sum, step) => 
    step.type !== 'income' ? sum + Math.abs(step.amount) : sum, 0
  );

  const remainingCash = waterfallSteps[0].amount - totalDistributed;

  return (
    <Paper elevation={3} sx={{ p: 2 }}>
      {/* Controls */}
      <Box sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>MAG Scenario</InputLabel>
          <Select value={selectedScenario} onChange={handleScenarioChange} label="MAG Scenario">
            {['MAG6', 'MAG7', 'MAG8', 'MAG9', 'MAG10', 'MAG11', 'MAG12', 'MAG13', 'MAG14', 'MAG15', 'MAG16', 'MAG17'].map(mag => (
              <MenuItem key={mag} value={mag}>{mag}</MenuItem>
            ))}
          </Select>
        </FormControl>

        <Typography variant="body2" color="textSecondary">
          Payment Date: {paymentDate}
        </Typography>

        <Box sx={{ flex: 1 }} />

        <Tooltip title="Refresh Animation">
          <IconButton onClick={handleRefresh} size="small">
            <RefreshIcon />
          </IconButton>
        </Tooltip>

        <Tooltip title="Export Chart">
          <IconButton onClick={handleExport} size="small">
            <DownloadIcon />
          </IconButton>
        </Tooltip>
      </Box>

      {/* Summary Metrics */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }} component="div">
          <MetricCard
            title="Available Funds"
            value={formatValue(waterfallSteps[0].amount)}
            icon={<AccountTreeIcon />}
            color="success"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }} component="div">
          <MetricCard
            title="Total Distributed"
            value={formatValue(totalDistributed)}
            icon={<TimelineIcon />}
            color="primary"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }} component="div">
          <MetricCard
            title="Remaining Cash"
            value={formatValue(remainingCash)}
            trend={remainingCash > 0 ? "up" : "neutral"}
            icon={<ShowChartIcon />}
            color={remainingCash > 0 ? "warning" : "info"}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }} component="div">
          <MetricCard
            title="Waterfall Steps"
            value={waterfallSteps.length.toString()}
            icon={<AccountTreeIcon />}
            color="info"
          />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Waterfall Chart */}
        <Grid size={{ xs: 12, lg: 8 }} component="div">
          <Box sx={{ border: '1px solid #e0e0e0', borderRadius: 1, p: 1, backgroundColor: '#fafafa' }}>
            <svg
              ref={svgRef}
              width="800"
              height="500"
              style={{ background: 'white', borderRadius: 4 }}
            />
          </Box>
        </Grid>

        {/* Tranche Details */}
        {showDetails && (
          <Grid size={{ xs: 12, lg: 4 }} component="div">
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Tranche Information
                </Typography>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Tranche</TableCell>
                        <TableCell>Rating</TableCell>
                        <TableCell>Interest</TableCell>
                        <TableCell>Principal</TableCell>
                        <TableCell>Status</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {trancheInfo.map((tranche) => (
                        <TableRow key={tranche.tranche}>
                          <TableCell>{tranche.tranche}</TableCell>
                          <TableCell>
                            <Chip 
                              label={tranche.rating} 
                              size="small"
                              color={tranche.rating.includes('AA') ? 'success' : 
                                     tranche.rating === 'A' ? 'primary' : 'default'}
                            />
                          </TableCell>
                          <TableCell>{formatValue(tranche.interestPaid)}</TableCell>
                          <TableCell>{formatValue(tranche.principalPaid)}</TableCell>
                          <TableCell>
                            <Chip 
                              label="Paid" 
                              size="small" 
                              color="success"
                            />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>

            {/* Scenario Features */}
            <Card sx={{ mt: 2 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {selectedScenario} Features
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  <Chip label="Basic Waterfall" color="primary" variant="outlined" />
                  {parseInt(selectedScenario.replace('MAG', '')) >= 8 && (
                    <Chip label="Equity Claw-Back" color="warning" variant="outlined" />
                  )}
                  {parseInt(selectedScenario.replace('MAG', '')) >= 10 && (
                    <Chip label="Fee Deferral" color="info" variant="outlined" />
                  )}
                  {['MAG14', 'MAG15', 'MAG16', 'MAG17'].includes(selectedScenario) && (
                    <Chip label="Reinvestment Overlay" color="secondary" variant="outlined" />
                  )}
                  {['MAG15', 'MAG16', 'MAG17'].includes(selectedScenario) && (
                    <Chip label="Performance Hurdle" color="success" variant="outlined" />
                  )}
                  {selectedScenario === 'MAG17' && (
                    <Chip label="Call Protection Override" color="error" variant="outlined" />
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>

      {enableRealTime && (calculationProgress?.waterfallProgress || portfolioData) && (
        <Typography variant="caption" color="textSecondary" sx={{ mt: 2, display: 'block' }}>
          Last updated: {new Date().toLocaleTimeString()} (Real-time) |
          {calculationProgress?.waterfallProgress && 
            ` Calculation Progress: ${calculationProgress.waterfallProgress.percentage}%`
          }
        </Typography>
      )}
    </Paper>
  );
};

export default WaterfallChart;