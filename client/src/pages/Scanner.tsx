import { useState, useEffect, useMemo } from 'react'
import { 
  TrendingUp, 
  RefreshCw, 
  Download, 
  Copy, 
  Star,
  Bell,
  Settings,
  ExternalLink,
  Search,
  ChevronUp,
  ChevronDown
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { getScanData, getSettings, getAlerts, getEarnings } from '@/lib/api'
import type { Scan, Settings as SettingsType, Alert } from '@/types'

function cn(...classes: (string | undefined | false)[]) {
  return classes.filter(Boolean).join(' ')
}

function getScoreClass(score: string | undefined): string {
  if (!score) return ''
  const num = parseFloat(score)
  if (num > 20) return 'score-high'
  if (num > 15) return 'score-med'
  return 'score-low'
}

function getRSClass(rs: string | undefined): string {
  if (!rs) return ''
  const num = parseFloat(rs)
  if (num > 80) return 'rs-high'
  if (num >= 60) return 'rs-med'
  return 'rs-low'
}

function getRegimeClass(regime: string): string {
  if (regime.includes('🟢')) return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
  if (regime.includes('🟡')) return 'bg-amber-500/20 text-amber-400 border-amber-500/30'
  if (regime.includes('🔴')) return 'bg-red-500/20 text-red-400 border-red-500/30'
  if (regime.includes('🟠')) return 'bg-orange-500/20 text-orange-400 border-orange-500/30'
  return 'bg-muted text-muted-foreground'
}

export default function ScannerDashboard() {
  const [scan, setScan] = useState<Scan | null>(null)
  const [_settings, setSettings] = useState<SettingsType | null>(null)
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [_earnings, setEarnings] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [sortColumn, setSortColumn] = useState<string | null>(null)
  const [sortAsc, setSortAsc] = useState(true)
  const [watchlist, setWatchlist] = useState<string[]>([])
  const [showWatchlistOnly, setShowWatchlistOnly] = useState(false)
  const [showAlerts, setShowAlerts] = useState(false)

  useEffect(() => {
    loadData()
    const saved = localStorage.getItem('canslim_watchlist')
    if (saved) {
      try {
        setWatchlist(JSON.parse(saved))
      } catch {}
    }
  }, [])

  async function loadData() {
    setLoading(true)
    setError(null)
    try {
      const [scanData, settingsData, alertsData, earningsData] = await Promise.all([
        getScanData(),
        getSettings(),
        getAlerts(),
        getEarnings()
      ])
      setScan(scanData)
      setSettings(settingsData)
      setAlerts(alertsData)
      setEarnings(earningsData)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data')
    } finally {
      setLoading(false)
    }
  }

  const stocks = useMemo(() => {
    if (!scan?.stocks) return []
    let result = [...scan.stocks]
    
    if (searchTerm) {
      result = result.filter(s => 
        (s.Ticker || '').toLowerCase().includes(searchTerm.toLowerCase())
      )
    }
    
    if (showWatchlistOnly) {
      result = result.filter(s => watchlist.includes(s.Ticker))
    }
    
    if (sortColumn) {
      result.sort((a, b) => {
        const aVal = a[sortColumn] || ''
        const bVal = b[sortColumn] || ''
        const aNum = parseFloat(aVal)
        const bNum = parseFloat(bVal)
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
          return sortAsc ? aNum - bNum : bNum - aNum
        }
        return sortAsc 
          ? String(aVal).localeCompare(String(bVal))
          : String(bVal).localeCompare(String(aVal))
      })
    }
    
    return result
  }, [scan?.stocks, searchTerm, sortColumn, sortAsc, watchlist, showWatchlistOnly])

  const topByScore = useMemo(() => {
    return [...(scan?.stocks || [])]
      .filter(s => s.Score && !isNaN(parseFloat(s.Score)))
      .sort((a, b) => parseFloat(b.Score || '0') - parseFloat(a.Score || '0'))
      .slice(0, 5)
  }, [scan?.stocks])

  const topByRS = useMemo(() => {
    return [...(scan?.stocks || [])]
      .filter(s => s['RS%'] && !isNaN(parseFloat(s['RS%'])))
      .sort((a, b) => parseFloat(b['RS%'] || '0') - parseFloat(a['RS%'] || '0'))
      .slice(0, 5)
  }, [scan?.stocks])

  function handleSort(column: string) {
    if (sortColumn === column) {
      setSortAsc(!sortAsc)
    } else {
      setSortColumn(column)
      setSortAsc(true)
    }
  }

  function toggleWatchlist(ticker: string) {
    const newWatchlist = watchlist.includes(ticker)
      ? watchlist.filter(t => t !== ticker)
      : [...watchlist, ticker]
    setWatchlist(newWatchlist)
    localStorage.setItem('canslim_watchlist', JSON.stringify(newWatchlist))
  }

  function copySymbols() {
    const symbols = stocks.map(s => s.Ticker).join(', ')
    navigator.clipboard.writeText(symbols)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4 text-primary" />
          <p className="text-muted-foreground">Loading scan data...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <p className="text-red-400 mb-4">{error}</p>
          <Button onClick={loadData}>Retry</Button>
        </div>
      </div>
    )
  }

  if (!scan) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <p className="text-muted-foreground mb-4">No scan data available</p>
          <p className="text-sm text-muted-foreground">Run the scanner to generate results</p>
        </div>
      </div>
    )
  }

  const market = {
    regime: scan.market_regime || '',
    dist_days: scan.dist_days?.replace('Dist Days: ', '') || '0',
    buy_ok: scan.buy_ok || ''
  }

  const account = {
    balance: scan.account_balance?.replace('Account: ', '') || '$0',
    risk_per_trade: scan.risk_per_trade?.replace('Risk/Trade: ', '') || '$0',
    actionable: scan.actionable_count || 0
  }

  const headers = scan.headers || Object.keys(scan.stocks?.[0] || {})

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card/50 backdrop-blur sticky top-0 z-50">
        <div className="container mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-primary/20 flex items-center justify-center">
                <TrendingUp className="w-5 h-5 text-primary" />
              </div>
              <div>
                <h1 className="text-lg font-semibold">CANSLIM Scanner</h1>
                <p className="text-xs text-muted-foreground">Market Analysis Dashboard</p>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="sm" onClick={loadData}>
                <RefreshCw className="w-4 h-4 mr-1" />
                Refresh
              </Button>
              <Button variant="ghost" size="sm" onClick={copySymbols}>
                <Copy className="w-4 h-4 mr-1" />
                Copy
              </Button>
              <Button variant="ghost" size="sm">
                <Download className="w-4 h-4 mr-1" />
                Export
              </Button>
              <Button 
                variant="ghost" 
                size="sm"
                onClick={() => setShowAlerts(!showAlerts)}
              >
                <Bell className="w-4 h-4 mr-1" />
                {alerts.length > 0 && (
                  <Badge variant="destructive" className="ml-1 px-1.5 py-0">
                    {alerts.length}
                  </Badge>
                )}
              </Button>
              <Button variant="ghost" size="sm">
                <Settings className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6">
        {/* Market Overview Cards */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
          <Card className="bg-card/50">
            <CardContent className="p-4">
              <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Market Regime</p>
              <div className={cn('inline-flex items-center px-3 py-1.5 rounded-lg border text-sm font-medium', getRegimeClass(market.regime))}>
                {market.regime || '—'}
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-card/50">
            <CardContent className="p-4">
              <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Dist Days</p>
              <p className="text-2xl font-bold">{market.dist_days}</p>
            </CardContent>
          </Card>
          
          <Card className="bg-card/50">
            <CardContent className="p-4">
              <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Buy Signal</p>
              <Badge variant={market.buy_ok.includes('True') ? 'success' : 'destructive'}>
                {market.buy_ok.includes('True') ? '✅ YES' : '❌ NO'}
              </Badge>
            </CardContent>
          </Card>
          
          <Card className="bg-card/50">
            <CardContent className="p-4">
              <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Account</p>
              <p className="text-xl font-bold">{account.balance}</p>
            </CardContent>
          </Card>
          
          <Card className="bg-card/50">
            <CardContent className="p-4">
              <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Risk/Trade</p>
              <p className="text-xl font-bold">{account.risk_per_trade}</p>
            </CardContent>
          </Card>
        </div>

        {/* Top Lists */}
        <div className="grid md:grid-cols-2 gap-4 mb-6">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">🏆 Top 5 by Score</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {topByScore.map((stock, i) => (
                  <div key={stock.Ticker} className="flex items-center justify-between p-2 rounded hover:bg-muted/50">
                    <div className="flex items-center gap-2">
                      <span className="text-muted-foreground text-xs w-4">{i + 1}</span>
                      <button
                        onClick={() => toggleWatchlist(stock.Ticker)}
                        className="hover:text-amber-400 transition-colors"
                      >
                        {watchlist.includes(stock.Ticker) ? (
                          <Star className="w-4 h-4 fill-amber-400 text-amber-400" />
                        ) : (
                          <Star className="w-4 h-4 text-muted-foreground" />
                        )}
                      </button>
                      <a 
                        href={`https://finance.yahoo.com/quote/${stock.Ticker}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="font-medium hover:text-primary flex items-center gap-1"
                      >
                        {stock.Ticker}
                        <ExternalLink className="w-3 h-3 text-muted-foreground" />
                      </a>
                    </div>
                    <span className={getScoreClass(stock.Score)}>{stock.Score || '—'}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">💪 Top 5 by RS%</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {topByRS.map((stock, i) => (
                  <div key={stock.Ticker} className="flex items-center justify-between p-2 rounded hover:bg-muted/50">
                    <div className="flex items-center gap-2">
                      <span className="text-muted-foreground text-xs w-4">{i + 1}</span>
                      <button
                        onClick={() => toggleWatchlist(stock.Ticker)}
                        className="hover:text-amber-400 transition-colors"
                      >
                        {watchlist.includes(stock.Ticker) ? (
                          <Star className="w-4 h-4 fill-amber-400 text-amber-400" />
                        ) : (
                          <Star className="w-4 h-4 text-muted-foreground" />
                        )}
                      </button>
                      <a 
                        href={`https://finance.yahoo.com/quote/${stock.Ticker}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="font-medium hover:text-primary flex items-center gap-1"
                      >
                        {stock.Ticker}
                        <ExternalLink className="w-3 h-3 text-muted-foreground" />
                      </a>
                    </div>
                    <span className={getRSClass(stock['RS%'])}>{stock['RS%'] || '—'}%</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Search and Filters */}
        <div className="flex items-center gap-3 mb-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search by ticker..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9"
            />
          </div>
          <Button
            variant={showWatchlistOnly ? 'default' : 'outline'}
            size="sm"
            onClick={() => setShowWatchlistOnly(!showWatchlistOnly)}
          >
            <Star className="w-4 h-4 mr-1" />
            Watchlist
          </Button>
          <Badge variant="outline" className="ml-auto">
            {stocks.length} stocks
          </Badge>
        </div>

        {/* Data Table */}
        <Card>
          <div className="overflow-x-auto">
            <table className="dense-table">
              <thead>
                <tr>
                  {headers.map((header) => (
                    <th 
                      key={header}
                      onClick={() => handleSort(header)}
                      className="cursor-pointer hover:bg-muted/80 select-none"
                    >
                      <div className="flex items-center gap-1">
                        {header}
                        {sortColumn === header && (
                          sortAsc ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />
                        )}
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {stocks.map((stock) => (
                  <tr key={stock.Ticker} className="group">
                    {headers.map((header) => {
                      const value = stock[header]
                      
                      if (header === 'Ticker') {
                        return (
                          <td key={header} className="font-medium">
                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => toggleWatchlist(value)}
                                className="opacity-0 group-hover:opacity-100 transition-opacity"
                              >
                                {watchlist.includes(value) ? (
                                  <Star className="w-4 h-4 fill-amber-400 text-amber-400" />
                                ) : (
                                  <Star className="w-4 h-4 text-muted-foreground hover:text-amber-400" />
                                )}
                              </button>
                              <a 
                                href={`https://finance.yahoo.com/quote/${value}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-primary hover:underline flex items-center gap-1"
                              >
                                {value}
                                <ExternalLink className="w-3 h-3 opacity-50" />
                              </a>
                            </div>
                          </td>
                        )
                      }
                      
                      if (header === 'Score') {
                        return (
                          <td key={header} className={getScoreClass(value)}>
                            {value}
                          </td>
                        )
                      }
                      
                      if (header === 'RS%') {
                        return (
                          <td key={header} className={getRSClass(value)}>
                            {value}
                          </td>
                        )
                      }
                      
                      if (header === 'Cost') {
                        return (
                          <td key={header} className="font-semibold text-emerald-400">
                            {value}
                          </td>
                        )
                      }
                      
                      if (header === 'Shares') {
                        return (
                          <td key={header} className="font-medium">
                            {value}
                          </td>
                        )
                      }
                      
                      return (
                        <td key={header}>
                          {value || '—'}
                        </td>
                      )
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        {stocks.length === 0 && (
          <div className="text-center py-12 text-muted-foreground">
            No stocks found matching your criteria
          </div>
        )}
      </main>
    </div>
  )
}
