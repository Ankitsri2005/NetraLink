import { Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Alerts from './pages/Alerts'
import AlertDetail from './pages/AlertDetail'
import Graph from './pages/Graph'
import PersonDetail from './pages/PersonDetail'
import Cases from './pages/Cases'
import CaseDetail from './pages/CaseDetail'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/alerts" element={<Alerts />} />
        <Route path="/alerts/:personId" element={<AlertDetail />} />
        <Route path="/graph" element={<Graph />} />
        <Route path="/persons/:personId" element={<PersonDetail />} />
        <Route path="/cases" element={<Cases />} />
        <Route path="/cases/:caseId" element={<CaseDetail />} />
        <Route path="*" element={<Dashboard />} />
      </Route>
    </Routes>
  )
}