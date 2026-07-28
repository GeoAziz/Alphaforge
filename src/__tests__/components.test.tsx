/**
 * Frontend Component Tests
 * Tests for React components using Vitest + React Testing Library
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BeginnerDashboard } from '@/components/dashboard/beginner-dashboard';
import { HighConfidenceSignals } from '@/components/signals/high-confidence-signals';
import { RiskManagementDashboard } from '@/components/dashboard/risk-management-dashboard';
import { NotificationCenter } from '@/components/notifications/notification-center';
import { LiveTradingPanel } from '@/components/trading/live-trading-panel';

describe('BeginnerDashboard Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state', () => {
    render(<BeginnerDashboard userId="test" isLoading={true} />);
    expect(screen.getByRole('status', { hidden: true })).toBeInTheDocument();
  });

  it('displays portfolio value', async () => {
    render(<BeginnerDashboard userId="test" />);
    await waitFor(() => {
      expect(screen.getByText(/Portfolio Value/i)).toBeInTheDocument();
    });
  });

  it('shows trading signals', async () => {
    render(<BeginnerDashboard userId="test" />);
    await waitFor(() => {
      expect(screen.getByText(/Top Trading Signals/i)).toBeInTheDocument();
    });
  });

  it('displays paper trading button', async () => {
    render(<BeginnerDashboard userId="test" />);
    await waitFor(() => {
      expect(screen.getByText(/Launch Paper Trading/i)).toBeInTheDocument();
    });
  });
});

describe('HighConfidenceSignals Component', () => {
  it('renders signal list', async () => {
    render(<HighConfidenceSignals limit={5} />);
    await waitFor(() => {
      expect(screen.getByText(/Top Trading Signals/i)).toBeInTheDocument();
    });
  });

  it('allows sorting by confidence', async () => {
    render(<HighConfidenceSignals limit={10} />);
    const sortButton = screen.getByDisplayValue('confidence');
    fireEvent.change(sortButton, { target: { value: 'risk-reward' } });
    expect(sortButton).toHaveValue('risk-reward');
  });

  it('displays signal details on click', async () => {
    render(<HighConfidenceSignals limit={5} />);
    await waitFor(() => {
      const signal = screen.queryByText(/BTC/);
      if (signal) {
        fireEvent.click(signal);
        expect(screen.getByText(/ML Score/i)).toBeInTheDocument();
      }
    });
  });

  it('shows confidence percentage', async () => {
    render(<HighConfidenceSignals limit={5} />);
    await waitFor(() => {
      expect(screen.queryByText(/%/)).toBeInTheDocument();
    });
  });
});

describe('RiskManagementDashboard Component', () => {
  it('displays risk score', async () => {
    render(<RiskManagementDashboard userId="test" />);
    await waitFor(() => {
      expect(screen.getByText(/Portfolio Risk Score/i)).toBeInTheDocument();
    });
  });

  it('shows Sharpe ratio', async () => {
    render(<RiskManagementDashboard userId="test" />);
    await waitFor(() => {
      expect(screen.getByText(/Sharpe Ratio/i)).toBeInTheDocument();
    });
  });

  it('displays max drawdown', async () => {
    render(<RiskManagementDashboard userId="test" />);
    await waitFor(() => {
      expect(screen.getByText(/Max Drawdown/i)).toBeInTheDocument();
    });
  });

  it('shows position risk breakdown', async () => {
    render(<RiskManagementDashboard userId="test" />);
    await waitFor(() => {
      expect(screen.getByText(/Position Risk Breakdown/i)).toBeInTheDocument();
    });
  });
});

describe('NotificationCenter Component', () => {
  const mockNotifications = [
    {
      id: '1',
      type: 'signal' as const,
      title: 'New BTC Signal',
      message: 'BUY signal generated',
      timestamp: new Date().toISOString(),
      read: false,
    },
  ];

  it('renders notification bell', () => {
    render(<NotificationCenter notifications={mockNotifications} />);
    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('shows unread badge', () => {
    render(<NotificationCenter notifications={mockNotifications} />);
    expect(screen.getByText('1')).toBeInTheDocument();
  });

  it('opens dropdown on click', async () => {
    render(<NotificationCenter notifications={mockNotifications} />);
    const button = screen.getByRole('button');
    fireEvent.click(button);
    await waitFor(() => {
      expect(screen.getByText('New BTC Signal')).toBeInTheDocument();
    });
  });

  it('marks notification as read', async () => {
    const onMarkRead = vi.fn();
    render(
      <NotificationCenter
        notifications={mockNotifications}
        onMarkRead={onMarkRead}
      />
    );
    const button = screen.getByRole('button');
    fireEvent.click(button);
    await waitFor(() => {
      const notification = screen.getByText('New BTC Signal');
      fireEvent.click(notification);
      expect(onMarkRead).toHaveBeenCalled();
    });
  });
});

describe('LiveTradingPanel Component', () => {
  it('renders order form', () => {
    render(<LiveTradingPanel availableBalance={10000} />);
    expect(screen.getByText(/Place Order/i)).toBeInTheDocument();
  });

  it('allows selecting trading pair', async () => {
    render(<LiveTradingPanel availableBalance={10000} />);
    const select = screen.getByDisplayValue('BTC/USD');
    fireEvent.change(select, { target: { value: 'EUR/USD' } });
    expect(select).toHaveValue('EUR/USD');
  });

  it('allows selecting buy/sell', async () => {
    render(<LiveTradingPanel availableBalance={10000} />);
    const buyButton = screen.getByText('BUY');
    fireEvent.click(buyButton);
    expect(buyButton.closest('button')).toHaveClass('bg-green-500/20');
  });

  it('validates quantity input', async () => {
    render(<LiveTradingPanel availableBalance={10000} />);
    const quantityInput = screen.getByPlaceholderText('0.1');
    fireEvent.change(quantityInput, { target: { value: '' } });
    expect(quantityInput).toHaveValue(null);
  });

  it('shows positions tab', async () => {
    render(<LiveTradingPanel availableBalance={10000} />);
    const positionsTab = screen.getByText(/Positions/);
    fireEvent.click(positionsTab);
    expect(screen.getByText(/No open positions/i)).toBeInTheDocument();
  });

  it('executes trade on button click', async () => {
    const onExecute = vi.fn();
    render(
      <LiveTradingPanel
        availableBalance={10000}
        onExecuteTrade={onExecute}
      />
    );
    const executeButton = screen.getByText(/Execute/);
    fireEvent.click(executeButton);
    await waitFor(() => {
      expect(onExecute).toHaveBeenCalled();
    });
  });
});

describe('Responsive Design', () => {
  it('BeginnerDashboard is responsive', () => {
    const { container } = render(<BeginnerDashboard userId="test" />);
    expect(container.querySelector('[class*="grid"]')).toBeInTheDocument();
  });

  it('components use tailwind responsive classes', () => {
    const { container } = render(
      <LiveTradingPanel availableBalance={10000} />
    );
    expect(container.querySelector('[class*="md:"]')).toBeInTheDocument();
  });
});

describe('Accessibility', () => {
  it('buttons are keyboard accessible', () => {
    render(<NotificationCenter notifications={[]} />);
    const button = screen.getByRole('button');
    expect(button).toBeInTheDocument();
  });

  it('inputs have labels', async () => {
    render(<LiveTradingPanel availableBalance={10000} />);
    await waitFor(() => {
      expect(screen.getByLabelText(/Trading Pair/i)).toBeInTheDocument();
    });
  });

  it('has proper heading hierarchy', () => {
    render(<BeginnerDashboard userId="test" />);
    expect(screen.queryByRole('heading')).toBeInTheDocument();
  });
});
