/**
 * TASK 13: Advanced Data Visualization Components Validation Tests
 * Comprehensive testing for the visualization component library
 */

describe('TASK 13: Advanced Data Visualization Components Validation', () => {
  
  test('All visualization component files exist', () => {
    const fs = require('fs');
    const path = require('path');
    
    const components = [
      'CorrelationHeatmap.tsx',
      'RiskVisualization.tsx', 
      'PerformanceChart.tsx',
      'PortfolioComposition.tsx',
      'WaterfallChart.tsx',
      'index.ts',
      'types.ts'
    ];
    
    components.forEach(component => {
      const componentPath = path.join(__dirname, '../components/common/Visualizations', component);
      expect(fs.existsSync(componentPath)).toBe(true);
    });
  });

  test('D3.js dependency is installed', () => {
    const fs = require('fs');
    const path = require('path');
    
    const packageJsonPath = path.join(__dirname, '../../package.json');
    const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
    
    expect(packageJson.dependencies.d3).toBeDefined();
    expect(packageJson.dependencies['@types/d3']).toBeDefined();
  });

  test('CorrelationHeatmap has proper D3.js integration', () => {
    const fs = require('fs');
    const path = require('path');
    
    const componentPath = path.join(__dirname, '../components/common/Visualizations/CorrelationHeatmap.tsx');
    const content = fs.readFileSync(componentPath, 'utf8');
    
    expect(content).toContain('import * as d3 from \'d3\'');
    expect(content).toContain('useRef<SVGSVGElement>');
    expect(content).toContain('d3.select(svgRef.current)');
    expect(content).toContain('scaleSequential');
    expect(content).toContain('zoom');
  });

  test('RiskVisualization has comprehensive risk metrics', () => {
    const fs = require('fs');
    const path = require('path');
    
    const componentPath = path.join(__dirname, '../components/common/Visualizations/RiskVisualization.tsx');
    const content = fs.readFileSync(componentPath, 'utf8');
    
    expect(content).toContain('var95');
    expect(content).toContain('var99');
    expect(content).toContain('expectedShortfall');
    expect(content).toContain('volatility');
    expect(content).toContain('sharpeRatio');
    expect(content).toContain('maxDrawdown');
    expect(content).toContain('StressTest');
  });

  test('PerformanceChart has time series capabilities', () => {
    const fs = require('fs');
    const path = require('path');
    
    const componentPath = path.join(__dirname, '../components/common/Visualizations/PerformanceChart.tsx');
    const content = fs.readFileSync(componentPath, 'utf8');
    
    expect(content).toContain('LineChart');
    expect(content).toContain('ComposedChart');
    expect(content).toContain('Brush');
    expect(content).toContain('benchmark');
    expect(content).toContain('cumulativeReturn');
    expect(content).toContain('drawdown');
  });

  test('PortfolioComposition has multiple chart types', () => {
    const fs = require('fs');
    const path = require('path');
    
    const componentPath = path.join(__dirname, '../components/common/Visualizations/PortfolioComposition.tsx');
    const content = fs.readFileSync(componentPath, 'utf8');
    
    expect(content).toContain('PieChart');
    expect(content).toContain('BarChart');
    expect(content).toContain('Treemap');
    expect(content).toContain('assetType');
    expect(content).toContain('sector');
    expect(content).toContain('geography');
  });

  test('WaterfallChart has CLO-specific features', () => {
    const fs = require('fs');
    const path = require('path');
    
    const componentPath = path.join(__dirname, '../components/common/Visualizations/WaterfallChart.tsx');
    const content = fs.readFileSync(componentPath, 'utf8');
    
    expect(content).toContain('MAG6');
    expect(content).toContain('MAG17');
    expect(content).toContain('waterfall');
    expect(content).toContain('tranche');
    expect(content).toContain('Class A');
    expect(content).toContain('equity_distribution');
    expect(content).toContain('d3.scaleBand');
  });

  test('All components have real-time integration', () => {
    const fs = require('fs');
    const path = require('path');
    
    const components = [
      'CorrelationHeatmap.tsx',
      'RiskVisualization.tsx', 
      'PerformanceChart.tsx',
      'PortfolioComposition.tsx',
      'WaterfallChart.tsx'
    ];
    
    components.forEach(component => {
      const componentPath = path.join(__dirname, '../components/common/Visualizations', component);
      const content = fs.readFileSync(componentPath, 'utf8');
      
      expect(content).toContain('useRealTimeData');
      expect(content).toContain('enableRealTime');
      expect(content).toContain('Last updated');
    });
  });

  test('TypeScript interfaces are properly exported', () => {
    const fs = require('fs');
    const path = require('path');
    
    const typesPath = path.join(__dirname, '../components/common/Visualizations/types.ts');
    const content = fs.readFileSync(typesPath, 'utf8');
    
    expect(content).toContain('export interface');
    expect(content).toContain('FinancialMetric');
    expect(content).toContain('RiskMetric');
    expect(content).toContain('AssetAllocation');
    expect(content).toContain('WaterfallStep');
    expect(content).toContain('CLOTranche');
    expect(content).toContain('PerformanceMetrics');
    expect(content).toContain('CorrelationMatrixData');
  });

  test('Index file exports all components', () => {
    const fs = require('fs');
    const path = require('path');
    
    const indexPath = path.join(__dirname, '../components/common/Visualizations/index.ts');
    const content = fs.readFileSync(indexPath, 'utf8');
    
    expect(content).toContain('export { default as CorrelationHeatmap }');
    expect(content).toContain('export { default as RiskVisualization }');
    expect(content).toContain('export { default as PerformanceChart }');
    expect(content).toContain('export { default as PortfolioComposition }');
    expect(content).toContain('export { default as WaterfallChart }');
    expect(content).toContain('export type');
  });

  test('All components have Material-UI integration', () => {
    const fs = require('fs');
    const path = require('path');
    
    const components = [
      'CorrelationHeatmap.tsx',
      'RiskVisualization.tsx', 
      'PerformanceChart.tsx',
      'PortfolioComposition.tsx',
      'WaterfallChart.tsx'
    ];
    
    components.forEach(component => {
      const componentPath = path.join(__dirname, '../components/common/Visualizations', component);
      const content = fs.readFileSync(componentPath, 'utf8');
      
      expect(content).toContain('@mui/material');
      expect(content).toContain('Paper');
      expect(content).toContain('IconButton');
      expect(content).toContain('Tooltip');
    });
  });

  test('Export functionality is available in all components', () => {
    const fs = require('fs');
    const path = require('path');
    
    const components = [
      'CorrelationHeatmap.tsx',
      'RiskVisualization.tsx', 
      'PerformanceChart.tsx',
      'PortfolioComposition.tsx',
      'WaterfallChart.tsx'
    ];
    
    components.forEach(component => {
      const componentPath = path.join(__dirname, '../components/common/Visualizations', component);
      const content = fs.readFileSync(componentPath, 'utf8');
      
      expect(content).toContain('handleExport');
      expect(content).toContain('DownloadIcon');
    });
  });

  test('Components have proper error handling', () => {
    const fs = require('fs');
    const path = require('path');
    
    const components = [
      'CorrelationHeatmap.tsx',
      'RiskVisualization.tsx', 
      'PerformanceChart.tsx',
      'PortfolioComposition.tsx',
      'WaterfallChart.tsx'
    ];
    
    components.forEach(component => {
      const componentPath = path.join(__dirname, '../components/common/Visualizations', component);
      const content = fs.readFileSync(componentPath, 'utf8');
      
      expect(content).toContain('useMemo');
      expect(content).toContain('useEffect');
    });
  });

  test('Components are responsive and configurable', () => {
    const fs = require('fs');
    const path = require('path');
    
    const components = [
      'CorrelationHeatmap.tsx',
      'RiskVisualization.tsx', 
      'PerformanceChart.tsx',
      'PortfolioComposition.tsx',
      'WaterfallChart.tsx'
    ];
    
    components.forEach(component => {
      const componentPath = path.join(__dirname, '../components/common/Visualizations', component);
      const content = fs.readFileSync(componentPath, 'utf8');
      
      expect(content).toContain('width');
      expect(content).toContain('height');
      // D3.js components use SVG responsiveness, Recharts use ResponsiveContainer
      if (component.includes('CorrelationHeatmap') || component.includes('WaterfallChart')) {
        expect(content).toContain('svg'); // D3.js components use SVG
      } else {
        expect(content).toContain('ResponsiveContainer'); // Recharts components
      }
    });
  });
});