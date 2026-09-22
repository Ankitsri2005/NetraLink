export const NODE_COLORS = {
  Person: '#e60023',
  Phone: '#ff7a3d',
  Account: '#12b76a',
  Vehicle: '#8b5cf6',
  Location: '#f59e0b',
  Fir: '#ec4899',
  Incident: '#f43f5e',
  default: '#9aa0a6',
}

export const PRIORITY_COLORS = {
  High: '#e60023',
  Medium: '#ff7a00',
  Low: '#12b76a',
}

export const RELATION_COLORS = {
  OWNS: '#12b76a',
  CALLED: '#e60023',
  TRANSFERRED_TO: '#8b5cf6',
  MENTIONED_IN: '#ec4899',
  REPORTED_AT: '#f59e0b',
  SEEN_AT: '#f59e0b',
  ASSOCIATED_WITH: '#f43f5e',
  default: '#9aa0a6',
}

export function fmtMoney(v) {
  if (v == null || Number.isNaN(Number(v))) return '—'
  return '₹' + Number(v).toLocaleString('en-IN')
}

export function fmtNum(v) {
  if (v == null || Number.isNaN(Number(v))) return '—'
  return Number(v).toLocaleString('en-IN')
}