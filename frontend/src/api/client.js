const API_HOST = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')
const BASE = `${API_HOST}/api/v1`

async function request(path, options = {}) {
  const headers = { ...(options.headers || {}) }
  if (typeof options.body === 'string') headers['Content-Type'] = 'application/json'
  const res = await fetch(`${BASE}${path}`, { ...options, headers })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

export const getAlerts = (params = '') => request(`/alerts${params}`)
export const getAlertSummary = () => request('/alerts/summary')
export const getAlert = (personId) => request(`/alerts/${personId}`)
export const getPersons = (params = '') => request(`/persons${params}`)
export const getPerson = (personId) => request(`/persons/${personId}`)
export const getGraph = () => request('/graph/neo4j/full?limit=2000')
export const getNeighbors = (nodeId) => request(`/graph/nodes/${nodeId}/neighbors`)
export const getFirEntities = () => request('/fir/entities')
export const getFirReports = () => request('/fir/reports')
export const getTransactions = (params = '') => request(`/transactions${params}`)
export const getCases = () => request('/cases')
export const getCase = (caseId) => request(`/cases/${caseId}`)
export const createCase = (payload) => request('/cases', { method: 'POST', body: JSON.stringify(payload) })
export const updateCase = (caseId, payload) => request(`/cases/${caseId}`, { method: 'PATCH', body: JSON.stringify(payload) })
export const addCaseNote = (caseId, payload) => request(`/cases/${caseId}/notes`, { method: 'POST', body: JSON.stringify(payload) })
export const uploadCaseEvidence = (caseId, sourceType, file) => {
  const body = new FormData()
  body.append('source_type', sourceType)
  body.append('file', file)
  return request(`/cases/${caseId}/evidence`, { method: 'POST', body })
}