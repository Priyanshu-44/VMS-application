import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import LiveGrid from './pages/LiveGrid'
import PlaybackPage from './pages/PlaybackPage'
import EventsPage from './pages/EventsPage'
import ComingSoon from './pages/ComingSoon'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<LiveGrid />} />
          <Route path="/playback/:cameraId" element={<PlaybackPage />} />
          <Route path="/events" element={<EventsPage />} />
          <Route path="/dashboard" element={<ComingSoon title="Dashboard" />} />
          <Route path="/analytics" element={<ComingSoon title="Analytics" />} />
          <Route path="/zones" element={<ComingSoon title="Zone Editor" />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
