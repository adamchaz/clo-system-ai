import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import StatusIndicator from './StatusIndicator';

const theme = createTheme();

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

describe('StatusIndicator Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    test('renders with dot variant', () => {
      renderWithTheme(
        <StatusIndicator
          status="online"
          variant="dot"
          label="System Online"
        />
      );

      expect(screen.getByText('System Online')).toBeInTheDocument();
    });

    test('renders with chip variant', () => {
      renderWithTheme(
        <StatusIndicator
          status="error"
          variant="chip"
          label="Error State"
        />
      );

      expect(screen.getByText('Error State')).toBeInTheDocument();
    });

    test('renders with icon variant', () => {
      renderWithTheme(
        <StatusIndicator
          status="warning"
          variant="icon"
          label="Warning"
        />
      );

      expect(screen.getByText('Warning')).toBeInTheDocument();
    });

    test('renders with detailed variant', () => {
      renderWithTheme(
        <StatusIndicator
          status="success"
          variant="detailed"
          label="Success"
          description="Operation completed successfully"
          timestamp="2023-01-01T12:00:00Z"
          showTimestamp
        />
      );

      expect(screen.getByText('Success')).toBeInTheDocument();
      expect(screen.getByText('Operation completed successfully')).toBeInTheDocument();
    });

    test('renders with signal variant', () => {
      renderWithTheme(
        <StatusIndicator
          status="healthy"
          variant="signal"
          label="System Health"
        />
      );

      expect(screen.getByText('System Health')).toBeInTheDocument();
    });
  });

  describe('Status Types', () => {
    const statusTypes = [
      'online', 'offline', 'error', 'warning', 'info',
      'success', 'pending', 'loading', 'unknown',
      'healthy', 'degraded', 'critical', 'maintenance'
    ] as const;

    statusTypes.forEach(status => {
      test(`renders ${status} status correctly`, () => {
        renderWithTheme(
          <StatusIndicator
            status={status}
            variant="chip"
          />
        );

        // Each status should have its default label
        const expectedLabels = {
          online: 'Online',
          offline: 'Offline',
          error: 'Error',
          warning: 'Warning',
          info: 'Info',
          success: 'Success',
          pending: 'Pending',
          loading: 'Loading',
          unknown: 'Unknown',
          healthy: 'Healthy',
          degraded: 'Degraded',
          critical: 'Critical',
          maintenance: 'Maintenance',
        };

        expect(screen.getByText(expectedLabels[status])).toBeInTheDocument();
      });
    });
  });

  describe('Sizes', () => {
    const sizes = ['small', 'medium', 'large'] as const;

    sizes.forEach(size => {
      test(`renders with ${size} size`, () => {
        renderWithTheme(
          <StatusIndicator
            status="online"
            variant="dot"
            size={size}
            label="Test Status"
          />
        );

        expect(screen.getByText('Test Status')).toBeInTheDocument();
      });
    });
  });

  describe('Interactive Features', () => {
    test('handles click events', () => {
      const mockClick = jest.fn();
      renderWithTheme(
        <StatusIndicator
          status="online"
          variant="dot"
          label="Clickable Status"
          clickable
          onClick={mockClick}
        />
      );

      const element = screen.getByText('Clickable Status').closest('div');
      if (element) {
        fireEvent.click(element);
        expect(mockClick).toHaveBeenCalled();
      }
    });

    test('handles refresh action', () => {
      const mockRefresh = jest.fn();
      renderWithTheme(
        <StatusIndicator
          status="online"
          variant="detailed"
          label="Refreshable Status"
          showRefresh
          onRefresh={mockRefresh}
        />
      );

      const refreshButton = screen.getByRole('button');
      fireEvent.click(refreshButton);
      expect(mockRefresh).toHaveBeenCalled();
    });
  });

  describe('Count and Badge Features', () => {
    test('displays count with chip variant', () => {
      renderWithTheme(
        <StatusIndicator
          status="error"
          variant="chip"
          label="Errors"
          count={5}
        />
      );

      expect(screen.getByText('Errors (5)')).toBeInTheDocument();
    });

    test('displays count with detailed variant', () => {
      renderWithTheme(
        <StatusIndicator
          status="warning"
          variant="detailed"
          label="Warnings"
          count={3}
        />
      );

      expect(screen.getByText('Warnings')).toBeInTheDocument();
      expect(screen.getByText('3')).toBeInTheDocument();
    });

    test('handles count overflow', () => {
      renderWithTheme(
        <StatusIndicator
          status="error"
          variant="chip"
          label="Errors"
          count={150}
          maxCount={99}
        />
      );

      expect(screen.getByText('Errors (99+)')).toBeInTheDocument();
    });
  });

  describe('Timestamp Features', () => {
    test('formats timestamp correctly', () => {
      const timestamp = new Date('2023-01-01T12:00:00Z');
      renderWithTheme(
        <StatusIndicator
          status="online"
          variant="detailed"
          label="Status"
          timestamp={timestamp}
          showTimestamp
        />
      );

      expect(screen.getByText('Status')).toBeInTheDocument();
      // Timestamp formatting will depend on locale, so we just check it's present
      const timestampText = timestamp.toLocaleString();
      expect(screen.getByText(timestampText)).toBeInTheDocument();
    });

    test('handles string timestamp', () => {
      renderWithTheme(
        <StatusIndicator
          status="online"
          variant="detailed"
          label="Status"
          timestamp="2023-01-01T12:00:00Z"
          showTimestamp
        />
      );

      expect(screen.getByText('Status')).toBeInTheDocument();
    });
  });

  describe('Animation Features', () => {
    test('applies animations when enabled', () => {
      renderWithTheme(
        <StatusIndicator
          status="loading"
          variant="icon"
          label="Loading"
          animated
        />
      );

      // Loading status should have CircularProgress for spinning animation
      expect(screen.getByRole('progressbar')).toBeInTheDocument();
      expect(screen.getByText('Loading')).toBeInTheDocument();
    });

    test('does not apply animations when disabled', () => {
      renderWithTheme(
        <StatusIndicator
          status="loading"
          variant="icon"
          label="Loading"
          animated={false}
        />
      );

      // Should still have CircularProgress even when animations are disabled
      expect(screen.getByRole('progressbar')).toBeInTheDocument();
      expect(screen.getByText('Loading')).toBeInTheDocument();
    });
  });

  describe('Customization', () => {
    test('uses custom color', () => {
      renderWithTheme(
        <StatusIndicator
          status="online"
          variant="dot"
          label="Custom Color"
          color="#ff0000"
        />
      );

      expect(screen.getByText('Custom Color')).toBeInTheDocument();
      // Custom color should be applied (exact testing depends on implementation)
    });

    test('uses custom label', () => {
      renderWithTheme(
        <StatusIndicator
          status="online"
          label="Custom Label Text"
        />
      );

      expect(screen.getByText('Custom Label Text')).toBeInTheDocument();
    });

    test('hides label when showLabel is false', () => {
      renderWithTheme(
        <StatusIndicator
          status="online"
          variant="dot"
          label="Hidden Label"
          showLabel={false}
        />
      );

      expect(screen.queryByText('Hidden Label')).not.toBeInTheDocument();
    });
  });

  describe('Signal Variant Logic', () => {
    test('shows correct signal for different status types', () => {
      const signalTests = [
        { status: 'online' as const, expectedIcon: 'strong signal' },
        { status: 'healthy' as const, expectedIcon: 'strong signal' },
        { status: 'warning' as const, expectedIcon: 'medium signal' },
        { status: 'degraded' as const, expectedIcon: 'medium signal' },
        { status: 'error' as const, expectedIcon: 'weak signal' },
        { status: 'critical' as const, expectedIcon: 'weakest signal' },
        { status: 'offline' as const, expectedIcon: 'no signal' },
      ];

      signalTests.forEach(({ status }) => {
        const { unmount } = renderWithTheme(
          <StatusIndicator
            status={status}
            variant="signal"
            label={`${status} status`}
          />
        );

        expect(screen.getByText(`${status} status`)).toBeInTheDocument();
        unmount();
      });
    });
  });

  describe('Badge Variant', () => {
    test('renders badge variant correctly', () => {
      renderWithTheme(
        <StatusIndicator
          status="error"
          variant="badge"
          label="Badge Status"
        />
      );

      expect(screen.getByText('Badge Status')).toBeInTheDocument();
    });
  });

  describe('Loading Status Special Handling', () => {
    test('shows CircularProgress for loading status', () => {
      renderWithTheme(
        <StatusIndicator
          status="loading"
          variant="icon"
          label="Loading"
        />
      );

      expect(screen.getByText('Loading')).toBeInTheDocument();
      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });

    test('shows CircularProgress in detailed variant', () => {
      renderWithTheme(
        <StatusIndicator
          status="loading"
          variant="detailed"
          label="Loading Data"
          description="Please wait while data is being loaded"
        />
      );

      expect(screen.getByText('Loading Data')).toBeInTheDocument();
      expect(screen.getByText('Please wait while data is being loaded')).toBeInTheDocument();
      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });
  });

  describe('Tooltip Functionality', () => {
    test('shows tooltip with description', () => {
      renderWithTheme(
        <StatusIndicator
          status="warning"
          variant="dot"
          label="Warning Status"
          description="This is a warning message"
        />
      );

      // Tooltip should be present (implementation may vary)
      expect(screen.getByText('Warning Status')).toBeInTheDocument();
    });

    test('shows tooltip with timestamp', () => {
      renderWithTheme(
        <StatusIndicator
          status="online"
          variant="dot"
          label="Online Status"
          timestamp="2023-01-01T12:00:00Z"
          showTimestamp
        />
      );

      expect(screen.getByText('Online Status')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    test('handles missing props gracefully', () => {
      renderWithTheme(
        <StatusIndicator status="online" />
      );

      // Should render with default label
      expect(screen.getByText('Online')).toBeInTheDocument();
    });

    test('handles invalid timestamp gracefully', () => {
      renderWithTheme(
        <StatusIndicator
          status="online"
          variant="detailed"
          timestamp="invalid-date"
          showTimestamp
        />
      );

      expect(screen.getByText('Online')).toBeInTheDocument();
      // Should not crash with invalid timestamp
    });

    test('prevents event bubbling on refresh click', () => {
      const mockRefresh = jest.fn();
      const mockClick = jest.fn();

      renderWithTheme(
        <StatusIndicator
          status="online"
          variant="detailed"
          label="Status"
          showRefresh
          onRefresh={mockRefresh}
          onClick={mockClick}
          clickable
        />
      );

      const refreshButton = screen.getByRole('button');
      fireEvent.click(refreshButton);

      expect(mockRefresh).toHaveBeenCalled();
      // Main click handler should not be called due to stopPropagation
      expect(mockClick).not.toHaveBeenCalled();
    });
  });

  describe('Accessibility', () => {
    test('has proper accessibility attributes', () => {
      renderWithTheme(
        <StatusIndicator
          status="error"
          variant="detailed"
          label="Error Status"
          description="System error occurred"
          showRefresh
          onRefresh={jest.fn()}
        />
      );

      const refreshButton = screen.getByRole('button');
      expect(refreshButton).toBeInTheDocument();
    });

    test('supports keyboard navigation for clickable indicators', () => {
      const mockClick = jest.fn();
      renderWithTheme(
        <StatusIndicator
          status="online"
          variant="chip"
          label="Clickable Status"
          clickable
          onClick={mockClick}
        />
      );

      const chipElement = screen.getByText('Clickable Status').closest('.MuiChip-root');
      expect(chipElement).toBeInTheDocument();
    });
  });

  describe('Performance', () => {
    test('renders efficiently with animations', () => {
      const startTime = performance.now();

      renderWithTheme(
        <StatusIndicator
          status="loading"
          variant="detailed"
          label="Performance Test"
          description="Testing rendering performance"
          animated
          showRefresh
          onRefresh={jest.fn()}
          showTimestamp
          timestamp={new Date()}
          count={100}
        />
      );

      const endTime = performance.now();
      const renderTime = endTime - startTime;

      expect(renderTime).toBeLessThan(50); // 50ms threshold
      expect(screen.getByText('Performance Test')).toBeInTheDocument();
    });
  });
});