import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Layout } from '@/components/Layout'
import ScannerDashboard from '@/pages/Scanner'
import TradeTracker from '@/pages/Trades'

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<ScannerDashboard />} />
          <Route path="/trades" element={<TradeTracker />} />
          <Route path="/routine" element={<div className="p-8 text-center text-muted-foreground">Routine - Coming Soon</div>} />
          <Route path="/calendar" element={<div className="p-8 text-center text-muted-foreground">Calendar - Coming Soon</div>} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}

export default App
