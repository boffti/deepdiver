import { useState, useEffect } from 'react'
import { Plus, RefreshCw, Target, Shield } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { getPositions, getCoveredCalls } from '@/lib/api'
import type { Position, CoveredCall, CallsSummary, PositionsSummary } from '@/types'

function formatCurrency(num: number | undefined | null): string {
  if (num === undefined || num === null) return '—'
  return `$${num.toLocaleString('en-US', { maximumFractionDigits: 0 })}`
}

function formatCurrencyPrecise(num: number | undefined | null): string {
  if (num === undefined || num === null) return '—'
  return `$${num.toLocaleString('en-US', { maximumFractionDigits: 2 })}`
}

export default function TradeTracker() {
  const [positions, setPositions] = useState<Position[]>([])
  const [posSummary, setPosSummary] = useState<PositionsSummary | null>(null)
  const [calls, setCalls] = useState<CoveredCall[]>([])
  const [callsSummary, setCallsSummary] = useState<CallsSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('stocks')
  const [tickerFilter, setTickerFilter] = useState('ALL')

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    setLoading(true)
    try {
      const [posData, callsData] = await Promise.all([
        getPositions(),
        getCoveredCalls()
      ])
      setPositions(posData.positions)
      setPosSummary(posData.summary)
      setCalls(callsData.trades)
      setCallsSummary(callsData.summary)
    } catch (err) {
      console.error('Failed to load:', err)
    } finally {
      setLoading(false)
    }
  }

  const openPositions = positions.filter(p => p.status === 'open')
  const closedPositions = positions.filter(p => p.status !== 'open')

  const filteredCalls = tickerFilter === 'ALL' 
    ? calls 
    : calls.filter(c => c.ticker === tickerFilter)
  
  const openCalls = filteredCalls.filter(c => c.status === 'open')
  const closedCalls = filteredCalls.filter(c => c.status !== 'open')

  const tickers = [...new Set(calls.map(c => c.ticker))]

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4" style={{ color: 'hsl(350, 82%, 65%)' }} />
          <p className="text-muted-foreground">Loading positions...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Trade Tracker</h1>
          <p className="text-muted-foreground">Stock positions & options income</p>
        </div>
        <Button onClick={loadData}>
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <Card className="bg-card/50">
          <CardContent className="p-4">
            <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Open Positions</p>
            <p className="text-2xl font-bold">{posSummary?.open_count || 0}</p>
          </CardContent>
        </Card>
        <Card className="bg-card/50">
          <CardContent className="p-4">
            <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Capital Deployed</p>
            <p className="text-2xl font-bold">{formatCurrency(posSummary?.total_pnl || 0)}</p>
          </CardContent>
        </Card>
        <Card className="bg-card/50">
          <CardContent className="p-4">
            <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Realized P&L</p>
            <p className="text-2xl font-bold" style={{ color: (posSummary?.total_pnl || 0) >= 0 ? '#34d399' : '#f87171' }}>
              {formatCurrency(posSummary?.total_pnl || 0)}
            </p>
          </CardContent>
        </Card>
        <Card className="bg-card/50">
          <CardContent className="p-4">
            <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Total Premium</p>
            <p className="text-2xl font-bold">{formatCurrency(callsSummary?.total_premium || 0)}</p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="mb-4">
          <TabsTrigger value="stocks">Stocks</TabsTrigger>
          <TabsTrigger value="options">Options</TabsTrigger>
        </TabsList>

        {/* Stocks Tab */}
        <TabsContent value="stocks">
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle>Open Positions</CardTitle>
                <Button size="sm">
                  <Plus className="w-4 h-4 mr-1" />
                  Add Position
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {openPositions.length === 0 ? (
                <p className="text-muted-foreground text-center py-8">No open positions</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="dense-table">
                    <thead>
                      <tr>
                        <th>Ticker</th>
                        <th>Account</th>
                        <th>Entry Date</th>
                        <th>Entry Price</th>
                        <th>Shares</th>
                        <th>Cost</th>
                        <th>Stop</th>
                        <th>Target</th>
                        <th>Setup</th>
                        <th></th>
                      </tr>
                    </thead>
                    <tbody>
                      {openPositions.map(pos => (
                        <tr key={pos.id}>
                          <td className="font-bold" style={{ color: '#e94560' }}>{pos.ticker}</td>
                          <td>
                            <Badge variant={pos.account === 'schwab' ? 'secondary' : 'outline'}>
                              {pos.account}
                            </Badge>
                          </td>
                          <td>{pos.entry_date}</td>
                          <td>{formatCurrencyPrecise(pos.entry_price)}</td>
                          <td>{pos.shares}</td>
                          <td className="font-semibold">{formatCurrency(pos.cost_basis)}</td>
                          <td className="text-red-400">{formatCurrencyPrecise(pos.stop_price)}</td>
                          <td className="text-emerald-400">{formatCurrencyPrecise(pos.target_price)}</td>
                          <td>{pos.setup_type || '—'}</td>
                          <td>
                            <div className="flex gap-1">
                              <Button variant="ghost" size="sm">
                                <Shield className="w-3 h-3" />
                              </Button>
                              <Button variant="ghost" size="sm">
                                <Target className="w-3 h-3" />
                              </Button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>

          {closedPositions.length > 0 && (
            <Card className="mt-4">
              <CardHeader className="pb-3">
                <CardTitle>Closed Trades</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="dense-table">
                    <thead>
                      <tr>
                        <th>Ticker</th>
                        <th>Entry</th>
                        <th>Exit</th>
                        <th>Shares</th>
                        <th>P&L</th>
                        <th>P&L %</th>
                        <th>Notes</th>
                      </tr>
                    </thead>
                    <tbody>
                      {closedPositions.map(pos => (
                        <tr key={pos.id}>
                          <td className="font-bold">{pos.ticker}</td>
                          <td>{pos.entry_date} @ {formatCurrencyPrecise(pos.entry_price)}</td>
                          <td>{pos.close_date} @ {formatCurrencyPrecise(pos.close_price)}</td>
                          <td>{pos.shares}</td>
                          <td className="font-semibold" style={{ color: (pos.pnl || 0) >= 0 ? '#34d399' : '#f87171' }}>
                            {formatCurrency(pos.pnl)}
                          </td>
                          <td style={{ color: (pos.pnl || 0) >= 0 ? '#34d399' : '#f87171' }}>
                            {pos.entry_price ? ((pos.close_price! - pos.entry_price) / pos.entry_price * 100).toFixed(1) : '—'}%
                          </td>
                          <td className="max-w-[150px] truncate">{pos.notes || '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Options Tab */}
        <TabsContent value="options">
          {/* Ticker Filter */}
          <div className="flex gap-2 mb-4 flex-wrap">
            <Button
              variant={tickerFilter === 'ALL' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setTickerFilter('ALL')}
            >
              All
            </Button>
            {tickers.map(t => (
              <Button
                key={t}
                variant={tickerFilter === t ? 'default' : 'outline'}
                size="sm"
                onClick={() => setTickerFilter(t)}
              >
                {t}
              </Button>
            ))}
          </div>

          {/* Options Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <Card className="bg-card/50">
              <CardContent className="p-4">
                <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Total Trades</p>
                <p className="text-xl font-bold">{callsSummary?.total_trades || 0}</p>
              </CardContent>
            </Card>
            <Card className="bg-card/50">
              <CardContent className="p-4">
                <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Expired</p>
                <p className="text-xl font-bold text-emerald-400">{callsSummary?.expired || 0}</p>
              </CardContent>
            </Card>
            <Card className="bg-card/50">
              <CardContent className="p-4">
                <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Called Away</p>
                <p className="text-xl font-bold text-amber-400">{callsSummary?.called_away || 0}</p>
              </CardContent>
            </Card>
            <Card className="bg-card/50">
              <CardContent className="p-4">
                <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Open</p>
                <p className="text-xl font-bold">{callsSummary?.open || 0}</p>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle>Open Positions</CardTitle>
                <Button size="sm">
                  <Plus className="w-4 h-4 mr-1" />
                  Sell Call
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {openCalls.length === 0 ? (
                <p className="text-muted-foreground text-center py-8">No open covered calls</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="dense-table">
                    <thead>
                      <tr>
                        <th>Ticker</th>
                        <th>Sold</th>
                        <th>Expiry</th>
                        <th>Strike</th>
                        <th>Δ</th>
                        <th>Contracts</th>
                        <th>Premium</th>
                        <th>Status</th>
                        <th></th>
                      </tr>
                    </thead>
                    <tbody>
                      {openCalls.map(call => (
                        <tr key={call.id}>
                          <td className="font-bold" style={{ color: '#e94560' }}>{call.ticker}</td>
                          <td>{call.sell_date}</td>
                          <td>{call.expiry}</td>
                          <td>{formatCurrencyPrecise(call.strike)}</td>
                          <td>{call.delta}</td>
                          <td>{call.contracts}</td>
                          <td className="font-semibold text-emerald-400">{formatCurrency(call.premium_total)}</td>
                          <td><Badge variant="success">Open</Badge></td>
                          <td>
                            <Button variant="ghost" size="sm">Close</Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>

          {closedCalls.length > 0 && (
            <Card className="mt-4">
              <CardHeader className="pb-3">
                <CardTitle>Trade History</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="dense-table">
                    <thead>
                      <tr>
                        <th>Ticker</th>
                        <th>Sold</th>
                        <th>Expiry</th>
                        <th>Strike</th>
                        <th>Contracts</th>
                        <th>Premium</th>
                        <th>Status</th>
                        <th>P&L</th>
                      </tr>
                    </thead>
                    <tbody>
                      {closedCalls.map(call => (
                        <tr key={call.id}>
                          <td className="font-bold">{call.ticker}</td>
                          <td>{call.sell_date}</td>
                          <td>{call.expiry}</td>
                          <td>{formatCurrencyPrecise(call.strike)}</td>
                          <td>{call.contracts}</td>
                          <td>{formatCurrency(call.premium_total)}</td>
                          <td>
                            <Badge 
                              variant={
                                call.status === 'expired' ? 'success' : 
                                call.status === 'called_away' ? 'warning' : 
                                'destructive'
                              }
                            >
                              {call.status}
                            </Badge>
                          </td>
                          <td className="font-semibold" style={{ color: (call.pnl || 0) >= 0 ? '#34d399' : '#f87171' }}>
                            {formatCurrency(call.pnl)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}
