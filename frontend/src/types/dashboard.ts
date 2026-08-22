export type DashboardResponse = {
  trading_mode: string;
  environment: string;
  market: { status: string; segment: string; note: string };
  broker: { status: string; broker: string | null; note: string };
  capital: {
    mock_labeled: boolean;
    currency: string;
    available: string;
    margin_used: string;
    day_pnl: string;
    exposure: string;
  };
  ip_details: {
    application_ip: string;
    broker_api_ip: string;
    connection_status: string;
    last_verified: string | null;
    environment: string;
  };
  signals: Array<{
    ticker: string;
    segment: string;
    ai_trend: string;
    confidence: string;
    strategy_state: string;
    entry: string;
    sl: string;
    target: string;
    status: string;
  }>;
  positions: Array<{
    symbol: string;
    exchange: string;
    quantity: number;
    average_price: string;
    unrealized_pnl: string;
  }>;
  orders: Array<{
    id: string;
    symbol: string;
    side: string;
    order_type: string;
    quantity: number;
    status: string;
    source: string;
  }>;
  order_book: {
    symbol: string;
    source: string;
    bids: Array<{ price: string; quantity: number }>;
    asks: Array<{ price: string; quantity: number }>;
  };
};
