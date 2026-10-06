import { Routes, Route } from 'react-router-dom'
import SiteLayout from './components/SiteLayout'
import Home from './pages/Home'
import Support from './pages/Support'
import PrivacyPolicy from './pages/PrivacyPolicy'

function App() {
  return (
    <SiteLayout>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/support" element={<Support />} />
        <Route path="/privacy-policy" element={<PrivacyPolicy />} />
      </Routes>
    </SiteLayout>
  )
}

export default App
