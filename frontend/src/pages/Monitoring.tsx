import { useState, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Brain, ChevronDown, ChevronUp, Wifi } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { monitors, incidents } from '../lib/api'
import { getStatusIcon, getStatusBadgeClass } from '../lib/statusUtils'
import { useWebSocket } from '../hooks/useWebSocket'
import type { WsMessage } from '../hooks/useWebSocket'
import type { Incident, AnalysisResult, Monitor } from '../types'

type AnalysisType = 'general' | 'root_cause' | 'pattern'

interface IncidentAnalysisState {
  analysisType: AnalysisType
  result: AnalysisResult | null
  error: string | null
  isPending: boolean
}

const DEFAULT_ANALYSIS_STATE: IncidentAnalysisState = {
  analysisType: 'general',
  result: null,
  error: null,
  isPending: false,
}

interface UptimeData {
  uptime_percentage: number
  total_checks: number
  failed_checks: number
  avg_response_time: number | null
}

interface UptimeCellProps {
  monitorId: string
  hours: number
}

function UptimeCell({ monitorId, hours }: UptimeCellProps) {
  const { data: uptime, isLoading } = useQuery<UptimeData>({
    queryKey: ['uptime', monitorId, hours],
    queryFn: () => monitors.uptime(monitorId, hours).then((res) => res.data),
  })

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-1">
        <div className="h-4 w-16 bg-gray-200 rounded-full" />
        <div className="h-3 w-12 bg-gray-100 rounded" />
      </div>
    )
  }

  if (!uptime) return <span className="text-gray-400 text-sm">—</span>

  const pct = uptime.uptime_percentage
  const badgeClass =
    pct >= 99
      ? 'bg-green-100 text-green-800'
      : pct >= 90
      ? 'bg-yellow-100 text-yellow-800'
      : 'bg-red-100 text-red-800'

  return (
    <div>
      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${badgeClass}`}>
        {pct.toFixed(2)}%
      </span>
      <div className="text-xs text-gray-500 mt-1">
        {uptime.avg_response_time != null
          ? `${Math.round(uptime.avg_response_time)}ms avg`
          : 'No data'}
      </div>
    </div>
  )
}

const TIME_RANGE_OPTIONS = [
  { label: 'Last 24h', hours: 24 },
  { label: 'Last 7 days', hours: 7 * 24 },
  { label: 'Last 30 days', hours: 30 * 24 },
]

export default function Monitoring() {
  const queryClient = useQueryClient()
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newMonitor, setNewMonitor] = useState({ name: '', url: '', interval: 60 })
  const [incidentBanner, setIncidentBanner] = useState<string | null>(null)
  const [uptimeHours, setUptimeHours] = useState(24)
  const [expandedIncidents, setExpandedIncidents] = useState<Record<string, boolean>>({})
  const [incidentAnalysis, setIncidentAnalysis] = useState<Record<string, IncidentAnalysisState>>({})

  const handleWsMessage = useCallback(
    (msg: WsMessage) => {
      const { type, data } = msg
      if (type === 'monitor_updated') {
        const updated = data as unknown as Monitor
        queryClient.setQueryData<Monitor[]>(['monitors'], (old) => {
          if (!old) return old
          return old.map((m) => (m.id === updated.id ? { ...m, ...updated } : m))
        })
      } else if (type === 'incident_created') {
        const monitorId = data.monitor_id as string | undefined
        const title = data.title as string | undefined
        const monitorName =
          queryClient
            .getQueryData<Monitor[]>(['monitors'])
            ?.find((m) => m.id === monitorId)?.name ?? 'A monitor'
        setIncidentBanner(`🚨 Incident: ${title ?? `${monitorName} is down`}`)
        queryClient.invalidateQueries({ queryKey: ['monitors'] })
      } else if (type === 'incident_resolved') {
        setIncidentBanner(null)
        queryClient.invalidateQueries({ queryKey: ['monitors'] })
      }
    },
    [queryClient],
  )

  const { connected } = useWebSocket('/ws/monitoring', handleWsMessage)

  const { data: monitorsList } = useQuery({
    queryKey: ['monitors'],
    queryFn: () => monitors.list().then((res) => res.data),
  })

  const { data: incidentsList } = useQuery({
    queryKey: ['incidents'],
    queryFn: () => incidents.list().then((res: { data: Incident[] }) => res.data),
  })

  const createMonitorMutation = useMutation({
    mutationFn: (data: typeof newMonitor) => monitors.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['monitors'] })
      setShowCreateForm(false)
      setNewMonitor({ name: '', url: '', interval: 60 })
    },
    onError: (error) => {
      console.error('Failed to create monitor:', error)
    },
  })

  const triggerCheckMutation = useMutation({
    mutationFn: (id: string) => monitors.check(id),
    onSuccess: (_, monitorId: string) => {
      queryClient.invalidateQueries({ queryKey: ['monitors'] })
      queryClient.invalidateQueries({ queryKey: ['uptime', monitorId] })
    },
    onError: (error) => {
      console.error('Failed to trigger check:', error)
    },
  })

  const getSeverityBadge = (severity: string) => {
    const styles: Record<string, string> = {
      critical: 'bg-red-100 text-red-800',
      high: 'bg-orange-100 text-orange-800',
      medium: 'bg-yellow-100 text-yellow-800',
      low: 'bg-blue-100 text-blue-800',
    }
    return styles[severity] || 'bg-gray-100 text-gray-800'
  }

  const getIncidentStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      investigating: 'bg-red-100 text-red-800',
      identified: 'bg-orange-100 text-orange-800',
      monitoring: 'bg-yellow-100 text-yellow-800',
      resolved: 'bg-green-100 text-green-800',
    }
    return styles[status] || 'bg-gray-100 text-gray-800'
  }

  const getConfidenceBadge = (confidence: number) => {
    if (confidence >= 0.8) return 'bg-green-100 text-green-800'
    if (confidence >= 0.6) return 'bg-yellow-100 text-yellow-800'
    return 'bg-red-100 text-red-800'
  }

  const handleAnalyzeIncident = async (incidentId: string) => {
    const state = incidentAnalysis[incidentId] ?? DEFAULT_ANALYSIS_STATE
    setIncidentAnalysis((prev) => ({
      ...prev,
      [incidentId]: { ...state, isPending: true, error: null, result: null },
    }))
    try {
      const res = await incidents.analyzeWithAI(incidentId, state.analysisType)
      setIncidentAnalysis((prev) => ({
        ...prev,
        [incidentId]: { ...(prev[incidentId] ?? DEFAULT_ANALYSIS_STATE), isPending: false, result: res.data },
      }))
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Analysis failed. Please try again.'
      setIncidentAnalysis((prev) => ({
        ...prev,
        [incidentId]: {
          ...(prev[incidentId] ?? DEFAULT_ANALYSIS_STATE),
          isPending: false,
          error: message,
        },
      }))
    }
  }

  const setAnalysisType = (incidentId: string, type: AnalysisType) => {
    setIncidentAnalysis((prev) => ({
      ...prev,
      [incidentId]: {
        ...(prev[incidentId] ?? DEFAULT_ANALYSIS_STATE),
        analysisType: type,
      },
    }))
  }

  const toggleIncidentExpanded = (incidentId: string) => {
    setExpandedIncidents((prev) => ({ ...prev, [incidentId]: !prev[incidentId] }))
  }

  return (
    <div className="space-y-6">
      {/* Incident banner */}
      {incidentBanner && (
        <div className="flex items-center justify-between rounded-md bg-red-50 px-4 py-3 text-sm text-red-800 shadow">
          <span>{incidentBanner}</span>
          <button
            onClick={() => setIncidentBanner(null)}
            className="ml-4 font-medium hover:text-red-600"
            aria-label="Dismiss"
          >
            ✕
          </button>
        </div>
      )}

      <div className="flex justify-between items-center">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-gray-900">Monitoring</h1>
            {connected ? (
              <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
                <Wifi className="w-3 h-3" />
                Live
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-500">
                <Wifi className="w-3 h-3" />
                Connecting…
              </span>
            )}
          </div>
          <p className="mt-1 text-sm text-gray-600">
            Monitor your services and APIs
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <select
            value={uptimeHours}
            onChange={(e) => setUptimeHours(Number(e.target.value))}
            className="text-sm border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
          >
            {TIME_RANGE_OPTIONS.map((opt) => (
              <option key={opt.hours} value={opt.hours}>
                {opt.label}
              </option>
            ))}
          </select>
          <button
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Monitor
          </button>
        </div>
      </div>

      {/* Create Form */}
      {showCreateForm && (
        <div className="bg-white shadow rounded-lg p-6 animate-slide-in">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Create Monitor</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Name</label>
              <input
                type="text"
                value={newMonitor.name}
                onChange={(e) => setNewMonitor({ ...newMonitor, name: e.target.value })}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                placeholder="Production API"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">URL</label>
              <input
                type="url"
                value={newMonitor.url}
                onChange={(e) => setNewMonitor({ ...newMonitor, url: e.target.value })}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                placeholder="https://api.example.com/health"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Check Interval (seconds)</label>
              <input
                type="number"
                value={newMonitor.interval}
                onChange={(e) => setNewMonitor({ ...newMonitor, interval: parseInt(e.target.value) })}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
              />
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => createMonitorMutation.mutate(newMonitor)}
                disabled={!newMonitor.name || !newMonitor.url}
                className="px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 disabled:opacity-50"
              >
                Create
              </button>
              <button
                onClick={() => setShowCreateForm(false)}
                className="px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Monitors List */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Monitor
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Uptime
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                URL
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Interval
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {monitorsList?.map((monitor) => (
              <tr key={monitor.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    {getStatusIcon(monitor.status)}
                    <div className="ml-3">
                      <div className="text-sm font-medium text-gray-900">
                        {monitor.name}
                      </div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusBadgeClass(monitor.status)}`}>
                    {monitor.status}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <UptimeCell monitorId={monitor.id} hours={uptimeHours} />
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {monitor.url}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {monitor.interval}s
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <button
                    onClick={() => triggerCheckMutation.mutate(monitor.id)}
                    className="text-primary-600 hover:text-primary-900"
                  >
                    Check Now
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Incidents Section */}
      <div className="space-y-2">
        <h2 className="text-xl font-semibold text-gray-900">Incidents</h2>
        {!incidentsList || incidentsList.length === 0 ? (
          <div className="bg-white shadow rounded-lg p-6 text-center text-gray-500">
            No incidents found.
          </div>
        ) : (
          <div className="bg-white shadow rounded-lg divide-y divide-gray-200">
            {incidentsList.map((incident: Incident) => {
              const analysisState = incidentAnalysis[incident.id] ?? DEFAULT_ANALYSIS_STATE
              const isExpanded = !!expandedIncidents[incident.id]

              return (
                <div key={incident.id} className="p-4">
                  {/* Incident header row */}
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2 min-w-0">
                      <button
                        onClick={() => toggleIncidentExpanded(incident.id)}
                        className="text-gray-400 hover:text-gray-600 flex-shrink-0"
                        aria-label={isExpanded ? 'Collapse' : 'Expand'}
                      >
                        {isExpanded ? (
                          <ChevronUp className="w-4 h-4" />
                        ) : (
                          <ChevronDown className="w-4 h-4" />
                        )}
                      </button>
                      <span className="text-sm font-medium text-gray-900 truncate">
                        {incident.title}
                      </span>
                      <span className={`px-2 py-0.5 text-xs font-semibold rounded-full flex-shrink-0 ${getSeverityBadge(incident.severity)}`}>
                        {incident.severity}
                      </span>
                      <span className={`px-2 py-0.5 text-xs font-semibold rounded-full flex-shrink-0 ${getIncidentStatusBadge(incident.status)}`}>
                        {incident.status}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <select
                        value={analysisState.analysisType}
                        onChange={(e) => setAnalysisType(incident.id, e.target.value as AnalysisType)}
                        className="text-sm border border-gray-300 rounded-md px-2 py-1 focus:border-primary-500 focus:ring-primary-500"
                      >
                        <option value="general">General</option>
                        <option value="root_cause">Root Cause</option>
                        <option value="pattern">Pattern</option>
                      </select>
                      <button
                        onClick={() => handleAnalyzeIncident(incident.id)}
                        disabled={analysisState.isPending}
                        className="inline-flex items-center px-3 py-1 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50"
                      >
                        <Brain className="w-4 h-4 mr-1" />
                        {analysisState.isPending ? 'Analyzing…' : 'Analyze with AI'}
                      </button>
                    </div>
                  </div>

                  {/* Expanded incident details */}
                  {isExpanded && (
                    <div className="mt-2 pl-6 text-sm text-gray-600 space-y-1">
                      {incident.description && <p>{incident.description}</p>}
                      <p className="text-xs text-gray-400">
                        Started: {new Date(incident.started_at).toLocaleString()}
                        {incident.resolved_at && (
                          <> · Resolved: {new Date(incident.resolved_at).toLocaleString()}</>
                        )}
                      </p>
                    </div>
                  )}

                  {/* Analysis result panel */}
                  {analysisState.error && (
                    <div className="mt-3 pl-6">
                      <div className="bg-red-50 border border-red-200 rounded-md p-3 text-sm text-red-700">
                        {analysisState.error}
                      </div>
                    </div>
                  )}
                  {analysisState.result && (
                    <div className="mt-3 pl-6">
                      <div className="bg-gray-50 border border-gray-200 rounded-md p-4">
                        <div className="flex items-center justify-between mb-3">
                          <span className="text-sm font-medium text-gray-700">AI Analysis</span>
                          <span className={`px-2 py-0.5 text-xs font-semibold rounded-full ${getConfidenceBadge(analysisState.result.confidence)}`}>
                            Confidence: {Math.round(analysisState.result.confidence * 100)}%
                          </span>
                        </div>
                        <div className="prose prose-sm max-w-none text-gray-800">
                          <ReactMarkdown>{analysisState.result.analysis}</ReactMarkdown>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
