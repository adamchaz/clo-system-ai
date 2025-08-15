import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import MetricCard, { MetricCardAction } from './MetricCard';

const theme = createTheme();

const mockActions: MetricCardAction[] = [
  {
    icon: () => <span data-testid="info-icon">ℹ️</span>,
    label: 'More Info',
    onClick: jest.fn(),
  },
  {
    icon: () => <span data-testid="export-icon">📊</span>,
    label: 'Export',
    onClick: jest.fn(),
  },
];

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

describe('MetricCard Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders basic metric card', () => {
    renderWithTheme(
      <MetricCard
        title="Total Assets"
        value={1000000}
        prefix="$"
      />
    );

    expect(screen.getByText('Total Assets')).toBeInTheDocument();
    expect(screen.getByText('$1M')).toBeInTheDocument();
  });

  test('renders with subtitle and description', () => {
    renderWithTheme(
      <MetricCard
        title="Portfolio Value"
        subtitle="As of today"
        value={5000000}
        prefix="$"
        description="Total value of all assets in the portfolio"
      />
    );

    expect(screen.getByText('Portfolio Value')).toBeInTheDocument();
    expect(screen.getByText('As of today')).toBeInTheDocument();
    expect(screen.getByText('$5M')).toBeInTheDocument();
    expect(screen.getByText('Total value of all assets in the portfolio')).toBeInTheDocument();
  });

  test('handles different status types', () => {
    const { rerender } = renderWithTheme(
      <MetricCard
        title="System Health"
        value="Healthy"
        status="success"
      />
    );

    expect(screen.getByText('System Health')).toBeInTheDocument();
    expect(screen.getByText('Healthy')).toBeInTheDocument();

    rerender(
      <ThemeProvider theme={theme}>
        <MetricCard
          title="System Health"
          value="Error"
          status="error"
        />
      </ThemeProvider>
    );

    expect(screen.getByText('Error')).toBeInTheDocument();
  });

  test('handles trend indicators', () => {
    renderWithTheme(
      <MetricCard
        title="Monthly Growth"
        value={15.5}
        unit="%"
        trend="up"
        trendValue={2.3}
        showTrendIcon
      />
    );

    expect(screen.getByText('Monthly Growth')).toBeInTheDocument();
    expect(screen.getByText('15.5%')).toBeInTheDocument();
    expect(screen.getByText('+2.3%')).toBeInTheDocument();
  });

  test('handles progress bar', () => {
    renderWithTheme(
      <MetricCard
        title="Goal Progress"
        value="750K"
        prefix="$"
        progress={75}
        showProgress
      />
    );

    expect(screen.getByText('Goal Progress')).toBeInTheDocument();
    expect(screen.getByText('$750K')).toBeInTheDocument();
    expect(screen.getByText('Progress')).toBeInTheDocument();
    expect(screen.getByText('75%')).toBeInTheDocument();
  });

  test('handles target comparison', () => {
    renderWithTheme(
      <MetricCard
        title="Revenue"
        value={1200000}
        target={1000000}
        prefix="$"
        showTarget
      />
    );

    expect(screen.getByText('Revenue')).toBeInTheDocument();
    expect(screen.getByText('$1.2M')).toBeInTheDocument();
    expect(screen.getByText('Target: $1M')).toBeInTheDocument();
    expect(screen.getByText('20.0%')).toBeInTheDocument();
  });

  test('handles loading state', () => {
    renderWithTheme(
      <MetricCard
        title="Loading Metric"
        value={0}
        loading
      />
    );

    expect(screen.getByText('Loading Metric')).toBeInTheDocument();
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  test('handles error state', () => {
    renderWithTheme(
      <MetricCard
        title="Error Metric"
        value={0}
        error
      />
    );

    expect(screen.getByText('Error Metric')).toBeInTheDocument();
    expect(screen.getByText('Error')).toBeInTheDocument();
  });

  test('handles different sizes', () => {
    const { rerender } = renderWithTheme(
      <MetricCard
        title="Small Card"
        value={100}
        size="small"
      />
    );

    expect(screen.getByText('Small Card')).toBeInTheDocument();

    rerender(
      <ThemeProvider theme={theme}>
        <MetricCard
          title="Large Card"
          value={100}
          size="large"
        />
      </ThemeProvider>
    );

    expect(screen.getByText('Large Card')).toBeInTheDocument();
  });

  test('handles different variants', () => {
    const { rerender } = renderWithTheme(
      <MetricCard
        title="Outlined Card"
        value={100}
        variant="outlined"
        status="success"
      />
    );

    expect(screen.getByText('Outlined Card')).toBeInTheDocument();

    rerender(
      <ThemeProvider theme={theme}>
        <MetricCard
          title="Gradient Card"
          value={100}
          variant="gradient"
          status="info"
        />
      </ThemeProvider>
    );

    expect(screen.getByText('Gradient Card')).toBeInTheDocument();
  });

  test('handles click interactions', () => {
    const mockClick = jest.fn();
    renderWithTheme(
      <MetricCard
        title="Clickable Card"
        value={100}
        onClick={mockClick}
      />
    );

    const card = screen.getByText('Clickable Card').closest('.MuiCard-root');
    if (card) {
      fireEvent.click(card);
      expect(mockClick).toHaveBeenCalled();
    }
  });

  test('handles actions', () => {
    renderWithTheme(
      <MetricCard
        title="Card with Actions"
        value={100}
        actions={mockActions}
      />
    );

    expect(screen.getByText('Card with Actions')).toBeInTheDocument();
    expect(screen.getByTestId('info-icon')).toBeInTheDocument();
    expect(screen.getByTestId('export-icon')).toBeInTheDocument();

    // Test action clicks
    const infoButton = screen.getByRole('button', { name: 'More Info' });
    fireEvent.click(infoButton);
    expect(mockActions[0].onClick).toHaveBeenCalled();

    const exportButton = screen.getByRole('button', { name: 'Export' });
    fireEvent.click(exportButton);
    expect(mockActions[1].onClick).toHaveBeenCalled();
  });

  test('handles custom icon', () => {
    const CustomIcon = <span data-testid="custom-icon">🎯</span>;
    
    renderWithTheme(
      <MetricCard
        title="Card with Icon"
        value={100}
        icon={CustomIcon}
      />
    );

    expect(screen.getByText('Card with Icon')).toBeInTheDocument();
    expect(screen.getByTestId('custom-icon')).toBeInTheDocument();
  });

  test('formats large numbers correctly', () => {
    const { rerender } = renderWithTheme(
      <MetricCard
        title="Large Number"
        value={1500000000} // 1.5 billion
      />
    );

    expect(screen.getByText('1.5B')).toBeInTheDocument();

    rerender(
      <ThemeProvider theme={theme}>
        <MetricCard
          title="Million"
          value={2500000} // 2.5 million
        />
      </ThemeProvider>
    );

    expect(screen.getByText('2.5M')).toBeInTheDocument();

    rerender(
      <ThemeProvider theme={theme}>
        <MetricCard
          title="Thousand"
          value={1500} // 1.5 thousand
        />
      </ThemeProvider>
    );

    expect(screen.getByText('1.5K')).toBeInTheDocument();
  });

  test('handles string values', () => {
    renderWithTheme(
      <MetricCard
        title="String Value"
        value="Online"
        status="success"
      />
    );

    expect(screen.getByText('String Value')).toBeInTheDocument();
    expect(screen.getByText('Online')).toBeInTheDocument();
  });

  test('handles percentage values with trend', () => {
    renderWithTheme(
      <MetricCard
        title="Conversion Rate"
        value={4.5}
        unit="%"
        trend="down"
        trendValue={-0.5}
        trendLabel="%"
      />
    );

    expect(screen.getByText('Conversion Rate')).toBeInTheDocument();
    expect(screen.getByText('4.5%')).toBeInTheDocument();
    expect(screen.getByText('-0.5%')).toBeInTheDocument();
  });

  test('prevents action clicks from triggering card click', () => {
    const mockCardClick = jest.fn();
    const mockActionClick = jest.fn();

    const actionWithClick: MetricCardAction = {
      icon: () => <span data-testid="action-icon">🔧</span>,
      label: 'Settings',
      onClick: mockActionClick,
    };

    renderWithTheme(
      <MetricCard
        title="Card with Action"
        value={100}
        onClick={mockCardClick}
        actions={[actionWithClick]}
      />
    );

    // Click on action button should not trigger card click
    const actionButton = screen.getByRole('button', { name: 'Settings' });
    fireEvent.click(actionButton);

    expect(mockActionClick).toHaveBeenCalled();
    expect(mockCardClick).not.toHaveBeenCalled();
  });

  test('handles accessibility attributes', () => {
    renderWithTheme(
      <MetricCard
        title="Accessible Card"
        value={100}
        onClick={jest.fn()}
        actions={mockActions}
      />
    );

    // Check for proper button roles and accessibility
    const actionButtons = screen.getAllByRole('button');
    expect(actionButtons).toHaveLength(2); // Two action buttons

    actionButtons.forEach(button => {
      expect(button).toHaveAttribute('aria-label');
    });
  });
});

describe('MetricCard Performance', () => {
  test('renders efficiently with complex content', () => {
    const startTime = performance.now();

    renderWithTheme(
      <MetricCard
        title="Complex Metric"
        subtitle="With all features"
        value={1234567890}
        prefix="$"
        unit=""
        status="success"
        trend="up"
        trendValue={15.5}
        progress={75}
        target={2000000000}
        showProgress
        showTarget
        showTrendIcon
        actions={mockActions}
        description="This is a complex metric card with all features enabled"
        size="large"
        variant="gradient"
        animated
      />
    );

    const endTime = performance.now();
    const renderTime = endTime - startTime;

    // Should render quickly even with all features
    expect(renderTime).toBeLessThan(100); // 100ms
    expect(screen.getByText('Complex Metric')).toBeInTheDocument();
  });
});

describe('MetricCard Edge Cases', () => {
  test('handles zero values', () => {
    renderWithTheme(
      <MetricCard
        title="Zero Value"
        value={0}
        prefix="$"
      />
    );

    expect(screen.getByText('$0')).toBeInTheDocument();
  });

  test('handles negative values', () => {
    renderWithTheme(
      <MetricCard
        title="Negative Value"
        value={-500000}
        prefix="$"
        trend="down"
        trendValue={-10}
      />
    );

    expect(screen.getByText('$-500K')).toBeInTheDocument();
    expect(screen.getByText('-10%')).toBeInTheDocument();
  });

  test('handles undefined/null values gracefully', () => {
    renderWithTheme(
      <MetricCard
        title="Undefined Value"
        value={undefined}
      />
    );

    expect(screen.getByText('Undefined Value')).toBeInTheDocument();
    // Should not crash and handle gracefully
  });

  test('handles very long text', () => {
    renderWithTheme(
      <MetricCard
        title="Very Long Title That Should Be Handled Gracefully Without Breaking"
        subtitle="Very long subtitle that should also be handled properly"
        value="Very Long Value String"
        description="This is a very long description that should wrap properly and not break the layout of the metric card component"
      />
    );

    expect(screen.getByText('Very Long Title That Should Be Handled Gracefully Without Breaking')).toBeInTheDocument();
  });
});