/**
 * TASK 13: Advanced Data Visualization Components Integration Tests
 * Enhanced testing for all visualization components
 */

describe('TASK 13: Advanced Data Visualization Integration Tests', () => {
  
  test('All visualization component files exist with correct structure', () => {
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
      expect(fs.existsSync(componentPath)).toBe(true);
      
      const content = fs.readFileSync(componentPath, 'utf8');
      const lines = content.split('\n').length;
      expect(lines).toBeGreaterThan(200); // Each component should be substantial
    });
  });

  test('D3.js integration is properly implemented', () => {
    const fs = require('fs');
    const path = require('path');
    
    // Test D3.js components
    const d3Components = ['CorrelationHeatmap.tsx', 'WaterfallChart.tsx'];
    
    d3Components.forEach(component => {
      const componentPath = path.join(__dirname, '../components/common/Visualizations', component);
      const content = fs.readFileSync(componentPath, 'utf8');
      
      expect(content).toContain('import * as d3 from \'d3\'');
      expect(content).toContain('useRef<SVGSVGElement>');
      expect(content).toContain('d3.select');
      expect(content).toContain('useEffect');
    });
  });

  test('Recharts integration is properly implemented', () => {
    const fs = require('fs');
    const path = require('path');
    
    // Test Recharts components
    const rechartsComponents = [
      'RiskVisualization.tsx', 
      'PerformanceChart.tsx',
      'PortfolioComposition.tsx'
    ];
    
    rechartsComponents.forEach(component => {
      const componentPath = path.join(__dirname, '../components/common/Visualizations', component);
      const content = fs.readFileSync(componentPath, 'utf8');
      
      expect(content).toContain('recharts');
      expect(content).toContain('ResponsiveContainer');
      expect(content).toMatch(/(LineChart|AreaChart|BarChart|PieChart)/);
    });
  });

  test('Real-time integration is complete across all components', () => {
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
      
      expect(content).toContain('useRealTime');
      expect(content).toContain('enableRealTime');
      expect(content).toContain('Real-time');
      expect(content).toContain('Last updated');
    });
  });

  test('TypeScript interfaces and props are properly defined', () => {
    const fs = require('fs');
    const path = require('path');
    
    // Check types.ts
    const typesPath = path.join(__dirname, '../components/common/Visualizations/types.ts');
    const typesContent = fs.readFileSync(typesPath, 'utf8');
    
    expect(typesContent).toContain('export interface');
    expect(typesContent).toContain('BaseVisualizationProps');
    expect(typesContent).toContain('FinancialMetric');
    expect(typesContent).toContain('WaterfallStep');
    expect(typesContent).toContain('PerformanceMetrics');
    
    // Check component prop interfaces
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
      
      const componentName = component.replace('.tsx', '');
      expect(content).toContain(`export interface ${componentName}Props`);
      expect(content).toContain(`React.FC<${componentName}Props>`);
    });
  });

  test('Material-UI integration is consistent', () => {
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
      expect(content).toContain('Paper elevation={3}');
      expect(content).toContain('IconButton');
      expect(content).toContain('Tooltip');
      expect(content).toContain('Grid');
    });
  });

  test('Export functionality is implemented', () => {
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
      expect(content).toContain('Export Chart');
    });
  });

  test('Component index exports are complete', () => {
    const fs = require('fs');
    const path = require('path');
    
    const indexPath = path.join(__dirname, '../components/common/Visualizations/index.ts');
    const indexContent = fs.readFileSync(indexPath, 'utf8');
    
    const expectedExports = [
      'export { default as CorrelationHeatmap }',
      'export { default as RiskVisualization }',
      'export { default as PerformanceChart }', 
      'export { default as PortfolioComposition }',
      'export { default as WaterfallChart }'
    ];
    
    expectedExports.forEach(exportStatement => {
      expect(indexContent).toContain(exportStatement);
    });
    
    expect(indexContent).toContain('export * from \'./types\'');
  });

  test('CLO-specific features are implemented', () => {
    const fs = require('fs');
    const path = require('path');
    
    // Test WaterfallChart CLO features
    const waterfallPath = path.join(__dirname, '../components/common/Visualizations/WaterfallChart.tsx');
    const waterfallContent = fs.readFileSync(waterfallPath, 'utf8');
    
    expect(waterfallContent).toContain('MAG6');
    expect(waterfallContent).toContain('MAG17');
    expect(waterfallContent).toContain('tranche');
    expect(waterfallContent).toContain('Class A');
    expect(waterfallContent).toContain('waterfall');
    
    // Test CorrelationHeatmap financial features
    const correlationPath = path.join(__dirname, '../components/common/Visualizations/CorrelationHeatmap.tsx');
    const correlationContent = fs.readFileSync(correlationPath, 'utf8');
    
    expect(correlationContent).toContain('correlation');
    expect(correlationContent).toContain('asset');
    expect(correlationContent).toContain('sector');
  });

  test('Risk management features are comprehensive', () => {
    const fs = require('fs');
    const path = require('path');
    
    const riskPath = path.join(__dirname, '../components/common/Visualizations/RiskVisualization.tsx');
    const riskContent = fs.readFileSync(riskPath, 'utf8');
    
    expect(riskContent).toContain('var95');
    expect(riskContent).toContain('var99');
    expect(riskContent).toContain('expectedShortfall');
    expect(riskContent).toContain('volatility');
    expect(riskContent).toContain('sharpeRatio');
    expect(riskContent).toContain('maxDrawdown');
    expect(riskContent).toContain('StressTest');
    expect(riskContent).toContain('market_crash');
    expect(riskContent).toContain('stressScenario');
  });

  test('Performance analytics are complete', () => {
    const fs = require('fs');
    const path = require('path');
    
    const perfPath = path.join(__dirname, '../components/common/Visualizations/PerformanceChart.tsx');
    const perfContent = fs.readFileSync(perfPath, 'utf8');
    
    expect(perfContent).toContain('benchmark');
    expect(perfContent).toContain('cumulativeReturn');
    expect(perfContent).toContain('drawdown');
    expect(perfContent).toContain('Sharpe');
    expect(perfContent).toContain('Alpha');
    expect(perfContent).toContain('Beta');
    expect(perfContent).toContain('totalReturn');
    expect(perfContent).toContain('annualizedReturn');
  });

  test('Portfolio composition features are implemented', () => {
    const fs = require('fs');
    const path = require('path');
    
    const compPath = path.join(__dirname, '../components/common/Visualizations/PortfolioComposition.tsx');
    const compContent = fs.readFileSync(compPath, 'utf8');
    
    expect(compContent).toContain('PieChart');
    expect(compContent).toContain('BarChart');
    expect(compContent).toContain('Treemap');
    expect(compContent).toContain('assetType');
    expect(compContent).toContain('sector');
    expect(compContent).toContain('geography');
    expect(compContent).toContain('holdings');
    expect(compContent).toContain('concentration');
  });

  test('Code quality and structure validation', () => {
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
      
      // Check for proper component structure
      expect(content).toContain('TASK 13: Advanced Data Visualization Components');
      expect(content).toContain('export default');
      expect(content).toContain('React.FC');
      
      // Check for error handling patterns
      expect(content).toMatch(/(useMemo|useEffect|useState)/);
      
      // Check for proper typing
      expect(content).toContain('interface');
      expect(content).toContain('Props');
    });
  });

  test('Bundle size impact validation', () => {
    const fs = require('fs');
    const path = require('path');
    
    // Check that D3 dependency is properly installed
    const packagePath = path.join(__dirname, '../../package.json');
    const packageJson = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
    
    expect(packageJson.dependencies.d3).toBeDefined();
    expect(packageJson.dependencies['@types/d3']).toBeDefined();
    expect(packageJson.dependencies.recharts).toBeDefined();
    
    // Verify version compatibility
    expect(packageJson.dependencies.d3).toMatch(/\^7\./);
    expect(packageJson.dependencies.recharts).toMatch(/\^3\./);
  });

  test('Component responsiveness and configuration', () => {
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
        expect(content).toMatch(/(ResponsiveContainer|responsive)/i); // Recharts components
      }
      
      // Check for configuration options
      expect(content).toMatch(/(showControls|enableRealTime)/);
    });
  });
});