export interface Scan {
  id: number
  scan_time: string
  market_regime: string
  dist_days: string
  buy_ok: string
  account_balance: string
  risk_per_trade: string
  actionable_count: number
  metadata: Record<string, unknown>
  scan_stocks: ScanStock[]
  headers?: string[]
  stocks?: Record<string, string>[]
}

export interface ScanStock {
  id: number
  scan_id: number
  ticker: string
  pivot: number
  stop: number
  rs_rating: number
  comp_rating: number
  eps_rating: number
  setup_type: string
  notes: string
  metadata: Record<string, unknown>
  Score?: string
  Shares?: string
  Cost?: string
}

export interface Settings {
  account_equity: number
  risk_pct: number
  max_positions: number
}

export interface Alert {
  id: number
  ticker: string
  condition: 'above' | 'below'
  price: number
  triggered: boolean
  created: string
}

export interface Position {
  id: number
  ticker: string
  account: string
  trade_type: 'long' | 'short'
  entry_date: string
  entry_price: number
  shares: number
  cost_basis: number
  stop_price: number
  target_price: number
  setup_type: string
  status: 'open' | 'closed'
  close_date: string | null
  close_price: number | null
  pnl: number | null
  notes: string
}

export interface CoveredCall {
  id: number
  ticker: string
  sell_date: string
  expiry: string
  strike: number
  contracts: number
  premium_per_contract: number
  premium_total: number
  delta: number
  stock_price_at_sell: number
  status: 'open' | 'expired' | 'called_away' | 'rolled' | 'closed'
  close_date: string | null
  close_price: number | null
  pnl: number | null
  notes: string
}

export interface CallsSummary {
  total_premium: number
  total_pnl: number
  total_trades: number
  expired: number
  called_away: number
  open: number
  weekly_avg: number
  annualized_yield: number
  tickers: string[]
  by_ticker: Record<string, CallsSummary>
}

export interface PositionsSummary {
  open_count: number
  closed_count: number
  total_pnl: number
}

export interface Routine {
  date: string
  premarket?: Record<string, string>
  postclose?: Record<string, string>
}

export interface HistoricalScan {
  id: number
  created_at: string
  scan_time: string
  market_regime: string
  actionable_count: number
}
