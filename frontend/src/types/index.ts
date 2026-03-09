export interface Board {
  id: string
  name: string
  description?: string
  lists?: List[]
  created_at: string
  updated_at: string
}

export interface List {
  id: string
  board_id: string
  name: string
  position: number
  cards?: Card[]
  created_at: string
  updated_at: string
}

export interface Card {
  id: string
  list_id: string
  title: string
  description?: string
  position: number
  due_date?: string
  completed: boolean
  created_at: string
  updated_at: string
}

export interface Monitor {
  id: string
  name: string
  type: string
  url: string
  interval: number
  timeout: number
  status: 'up' | 'down' | 'degraded' | 'paused'
  enabled: boolean
  uptime_24h: number
  last_checked_at?: string
  created_at: string
  updated_at: string
}

export interface StatusData {
  monitors: Monitor[]
  last_updated: string
}

export interface ActivityEntry {
  id: string
  action: string
  entity_type: string
  entity_id: string
  details: string
  timestamp: string
}

export interface Incident {
  id: string
  monitor_id: string
  title: string
  description?: string
  status: 'investigating' | 'identified' | 'monitoring' | 'resolved'
  severity: 'critical' | 'high' | 'medium' | 'low'
  started_at: string
  resolved_at?: string
  acknowledged_at?: string
}

export interface AnalysisResult {
  analysis: string
  analysis_type: string
  incident_id: string
  confidence: number
}
