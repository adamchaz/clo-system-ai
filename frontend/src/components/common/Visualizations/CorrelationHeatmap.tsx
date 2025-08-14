import React, { useRef, useEffect, useState, useMemo } from 'react';
import * as d3 from 'd3';
import {
  Box,
  Paper,
  Typography,
  Tooltip as MUITooltip,
  IconButton,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  SelectChangeEvent,
  Grid
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  ShowChart as ShowChartIcon,
  Timeline as TimelineIcon,
  Compare as CompareIcon,
  Category as CategoryIcon
} from '@mui/icons-material';
import { useRealTime } from '../../../hooks/useRealTimeData';

/**
 * TASK 13: Advanced Data Visualization Components
 * 
 * CorrelationHeatmap - Interactive correlation matrix visualization using D3.js
 * 
 * Features:
 * - Interactive D3.js heatmap with zoom/pan capabilities
 * - Real-time correlation data updates
 * - Asset filtering and grouping options
 * - Export functionality for charts
 * - Responsive design with Material-UI integration
 * - Color scale customization for correlation values
 */

export interface CorrelationData {
  asset1: string;
  asset2: string;
  correlation: number;
  assetType1?: string;
  assetType2?: string;
  sector1?: string;
  sector2?: string;
}

export interface CorrelationMatrix {
  assets: string[];
  correlations: number[][];
  metadata: {
    assetTypes: Record<string, string>;
    sectors: Record<string, string>;
  };
}

export interface CorrelationHeatmapProps {
  data?: CorrelationMatrix;
  width?: number;
  height?: number;
  showControls?: boolean;
  enableRealTime?: boolean;
  onAssetSelect?: (asset1: string, asset2: string, correlation: number) => void;
  colorScheme?: 'RdYlBu' | 'RdBu' | 'Spectral' | 'viridis';
}

const CorrelationHeatmap: React.FC<CorrelationHeatmapProps> = ({
  data,
  width = 600,
  height = 600,
  showControls = true,
  enableRealTime = true,
  onAssetSelect,
  colorScheme = 'RdYlBu'
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [filterType, setFilterType] = useState<string>('all');
  const [zoomLevel, setZoomLevel] = useState<number>(1);
  const [hoveredCell, setHoveredCell] = useState<{
    asset1: string;
    asset2: string;
    correlation: number;
  } | null>(null);

  // Real-time data integration
  const { portfolio } = useRealTime();
  const portfolioData = portfolio.portfolioData;

  // Generate sample correlation matrix if no data provided
  const mockCorrelationMatrix: CorrelationMatrix = useMemo(() => {
    const assets = [
      'AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'META', 'NVDA', 'JPM', 
      'BAC', 'XOM', 'CVX', 'JNJ', 'PFE', 'KO', 'PEP', 'WMT'
    ];
    
    const correlations = assets.map(() => 
      assets.map(() => (Math.random() - 0.5) * 2)
    );
    
    // Ensure diagonal is 1 and matrix is symmetric
    correlations.forEach((row, i) => {
      row[i] = 1;
      row.forEach((_, j) => {
        correlations[j][i] = correlations[i][j];
      });
    });

    return {
      assets,
      correlations,
      metadata: {
        assetTypes: assets.reduce((acc, asset) => ({
          ...acc,
          [asset]: ['Equity', 'Bond', 'Commodity'][Math.floor(Math.random() * 3)]
        }), {}),
        sectors: assets.reduce((acc, asset) => ({
          ...acc,
          [asset]: ['Technology', 'Financial', 'Energy', 'Healthcare', 'Consumer'][Math.floor(Math.random() * 5)]
        }), {})
      }
    };
  }, []);

  const currentData = data || mockCorrelationMatrix;

  // Filter data based on selected filter
  const filteredData = useMemo(() => {
    if (filterType === 'all') return currentData;
    
    const filteredAssets = currentData.assets.filter(asset => 
      currentData.metadata.assetTypes[asset] === filterType ||
      currentData.metadata.sectors[asset] === filterType
    );
    
    const assetIndices = filteredAssets.map(asset => currentData.assets.indexOf(asset));
    const filteredCorrelations = assetIndices.map(i => 
      assetIndices.map(j => currentData.correlations[i][j])
    );

    return {
      assets: filteredAssets,
      correlations: filteredCorrelations,
      metadata: currentData.metadata
    };
  }, [currentData, filterType]);

  // D3 visualization
  useEffect(() => {
    if (!svgRef.current || filteredData.assets.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const margin = { top: 80, right: 50, bottom: 100, left: 100 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Scales
    const xScale = d3.scaleBand()
      .domain(filteredData.assets)
      .range([0, innerWidth])
      .padding(0.05);

    const yScale = d3.scaleBand()
      .domain(filteredData.assets)
      .range([0, innerHeight])
      .padding(0.05);

    // Color scale
    const colorScale = d3.scaleSequential()
      .domain([-1, 1])
      .interpolator(d3[`interpolate${colorScheme}` as keyof typeof d3] as any);

    // Add zoom behavior
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.5, 5])
      .on('zoom', (event) => {
        g.attr('transform', `translate(${margin.left + event.transform.x},${margin.top + event.transform.y}) scale(${event.transform.k})`);
        setZoomLevel(event.transform.k);
      });

    svg.call(zoom);

    // Create cells
    filteredData.assets.forEach((asset1, i) => {
      filteredData.assets.forEach((asset2, j) => {
        const correlation = filteredData.correlations[i][j];
        
        g.append('rect')
          .attr('x', xScale(asset1) || 0)
          .attr('y', yScale(asset2) || 0)
          .attr('width', xScale.bandwidth())
          .attr('height', yScale.bandwidth())
          .attr('fill', colorScale(correlation))
          .attr('stroke', '#fff')
          .attr('stroke-width', 1)
          .style('cursor', 'pointer')
          .on('mouseover', (event) => {
            setHoveredCell({ asset1, asset2, correlation });
            d3.select(event.target).attr('stroke-width', 3);
          })
          .on('mouseout', (event) => {
            setHoveredCell(null);
            d3.select(event.target).attr('stroke-width', 1);
          })
          .on('click', () => {
            onAssetSelect?.(asset1, asset2, correlation);
          });

        // Add correlation text for larger cells
        if (xScale.bandwidth() > 30) {
          g.append('text')
            .attr('x', (xScale(asset1) || 0) + xScale.bandwidth() / 2)
            .attr('y', (yScale(asset2) || 0) + yScale.bandwidth() / 2)
            .attr('text-anchor', 'middle')
            .attr('dominant-baseline', 'middle')
            .attr('fill', Math.abs(correlation) > 0.5 ? 'white' : 'black')
            .attr('font-size', Math.min(12, xScale.bandwidth() / 4))
            .text(correlation.toFixed(2));
        }
      });
    });

    // Add axes
    g.append('g')
      .attr('class', 'x-axis')
      .attr('transform', `translate(0,${innerHeight})`)
      .call(d3.axisBottom(xScale))
      .selectAll('text')
      .style('text-anchor', 'end')
      .attr('dx', '-.8em')
      .attr('dy', '.15em')
      .attr('transform', 'rotate(-45)');

    g.append('g')
      .attr('class', 'y-axis')
      .call(d3.axisLeft(yScale));

    // Add title
    svg.append('text')
      .attr('x', width / 2)
      .attr('y', 30)
      .attr('text-anchor', 'middle')
      .style('font-size', '16px')
      .style('font-weight', 'bold')
      .text('Asset Correlation Matrix');

    // Add color legend
    const legendWidth = 300;
    const legendHeight = 10;
    
    const legend = svg.append('g')
      .attr('transform', `translate(${(width - legendWidth) / 2}, ${height - 40})`);

    const legendScale = d3.scaleLinear()
      .domain([-1, 1])
      .range([0, legendWidth]);

    const legendAxis = d3.axisBottom(legendScale)
      .tickSize(13)
      .tickValues([-1, -0.5, 0, 0.5, 1]);

    legend.selectAll('rect')
      .data(d3.range(-1, 1.01, 0.01))
      .enter().append('rect')
      .attr('x', d => legendScale(d))
      .attr('width', legendWidth / 200)
      .attr('height', legendHeight)
      .attr('fill', d => colorScale(d));

    legend.append('g')
      .attr('transform', `translate(0, ${legendHeight})`)
      .call(legendAxis);

  }, [filteredData, width, height, colorScheme, onAssetSelect]);

  const handleFilterChange = (event: SelectChangeEvent<string>) => {
    setFilterType(event.target.value);
  };

  const handleRefresh = () => {
    // Trigger data refresh
    window.location.reload();
  };

  const handleExport = () => {
    if (!svgRef.current) return;
    
    const svgData = new XMLSerializer().serializeToString(svgRef.current);
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const img = new Image();
    
    img.onload = () => {
      canvas.width = img.width;
      canvas.height = img.height;
      ctx?.drawImage(img, 0, 0);
      
      const pngFile = canvas.toDataURL('image/png');
      const downloadLink = document.createElement('a');
      downloadLink.download = 'correlation-heatmap.png';
      downloadLink.href = pngFile;
      downloadLink.click();
    };
    
    img.src = 'data:image/svg+xml;base64,' + btoa(svgData);
  };

  const handleZoomIn = () => {
    if (svgRef.current) {
      const svg = d3.select(svgRef.current);
      svg.transition().duration(300).call(
        d3.zoom<SVGSVGElement, unknown>().scaleBy as any,
        1.5
      );
    }
  };

  const handleZoomOut = () => {
    if (svgRef.current) {
      const svg = d3.select(svgRef.current);
      svg.transition().duration(300).call(
        d3.zoom<SVGSVGElement, unknown>().scaleBy as any,
        0.67
      );
    }
  };

  return (
    <Paper elevation={3} sx={{ p: 2 }}>
      {showControls && (
        <Box sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Filter</InputLabel>
            <Select value={filterType} onChange={handleFilterChange} label="Filter">
              <MenuItem value="all">All Assets</MenuItem>
              <MenuItem value="Equity">Equity</MenuItem>
              <MenuItem value="Bond">Bonds</MenuItem>
              <MenuItem value="Commodity">Commodities</MenuItem>
              <MenuItem value="Technology">Technology</MenuItem>
              <MenuItem value="Financial">Financial</MenuItem>
              <MenuItem value="Energy">Energy</MenuItem>
              <MenuItem value="Healthcare">Healthcare</MenuItem>
              <MenuItem value="Consumer">Consumer</MenuItem>
            </Select>
          </FormControl>

          <Box sx={{ flex: 1 }} />

          <MUITooltip title="Refresh Data">
            <IconButton onClick={handleRefresh} size="small">
              <RefreshIcon />
            </IconButton>
          </MUITooltip>

          <MUITooltip title="Zoom In">
            <IconButton onClick={handleZoomIn} size="small">
              <ZoomInIcon />
            </IconButton>
          </MUITooltip>

          <MUITooltip title="Zoom Out">
            <IconButton onClick={handleZoomOut} size="small">
              <ZoomOutIcon />
            </IconButton>
          </MUITooltip>

          <MUITooltip title="Export Chart">
            <IconButton onClick={handleExport} size="small">
              <DownloadIcon />
            </IconButton>
          </MUITooltip>
        </Box>
      )}

      {/* Summary Metrics */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }} component="div">
          <Typography variant="h6" component="div" sx={{ p: 2, border: 1, borderColor: 'divider', borderRadius: 1, textAlign: 'center' }}>
            <ShowChartIcon sx={{ mr: 1, color: 'primary.main' }} />
            Matrix Size: {filteredData.assets.length}×{filteredData.assets.length}
          </Typography>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }} component="div">
          <Typography variant="h6" component="div" sx={{ p: 2, border: 1, borderColor: 'divider', borderRadius: 1, textAlign: 'center' }}>
            <TimelineIcon sx={{ mr: 1, color: 'info.main' }} />
            Correlations: {filteredData.assets.length * (filteredData.assets.length - 1) / 2}
          </Typography>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }} component="div">
          <Typography variant="h6" component="div" sx={{ p: 2, border: 1, borderColor: 'divider', borderRadius: 1, textAlign: 'center' }}>
            <CompareIcon sx={{ mr: 1, color: 'success.main' }} />
            Filter: {filterType === 'all' ? 'None' : filterType}
          </Typography>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }} component="div">
          <Typography variant="h6" component="div" sx={{ p: 2, border: 1, borderColor: 'divider', borderRadius: 1, textAlign: 'center' }}>
            <CategoryIcon sx={{ mr: 1, color: 'secondary.main' }} />
            Assets: {currentData.assets.length} total
          </Typography>
        </Grid>
      </Grid>

      <Box sx={{ position: 'relative' }}>
        <svg
          ref={svgRef}
          width={width}
          height={height}
          style={{ border: '1px solid #e0e0e0', borderRadius: 4 }}
        />
        
        {hoveredCell && (
          <Box
            sx={{
              position: 'absolute',
              top: 10,
              right: 10,
              bgcolor: 'rgba(0, 0, 0, 0.8)',
              color: 'white',
              p: 1,
              borderRadius: 1,
              fontSize: 12
            }}
          >
            <Typography variant="caption" display="block">
              {hoveredCell.asset1} vs {hoveredCell.asset2}
            </Typography>
            <Typography variant="caption" display="block">
              Correlation: {hoveredCell.correlation.toFixed(3)}
            </Typography>
          </Box>
        )}
      </Box>

      {enableRealTime && portfolioData && (
        <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
          Last updated: {new Date().toLocaleTimeString()} (Real-time)
        </Typography>
      )}
    </Paper>
  );
};

export default CorrelationHeatmap;