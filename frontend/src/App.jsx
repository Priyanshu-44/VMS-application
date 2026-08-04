import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import LiveGrid from './pages/LiveGrid'
import PlaybackPage from './pages/PlaybackPage'
import EventsPage from './pages/EventsPage'
import DashboardPage from './pages/DashboardPage'
import AnalyticsPage from './pages/AnalyticsPage'
import ZonesPage from './pages/ZonesPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<LiveGrid />} />
          <Route path="/playback/:cameraId" element={<PlaybackPage />} />
          <Route path="/events" element={<EventsPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/zones" element={<ZonesPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
