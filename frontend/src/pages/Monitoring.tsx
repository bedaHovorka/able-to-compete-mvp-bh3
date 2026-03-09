import { useState, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Activity, CheckCircle, XCircle, AlertTriangle, Wifi } from 'lucide-react'
import { monitors } from '../lib/api'
import { useWebSocket } from '../hooks/useWebSocket'
import type { WsMessage } from '../hooks/useWebSocket'
import type { Monitor } from '../types'

export default function Monitoring() {
  const queryClient = useQueryClient()
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newMonitor, setNewMonitor] = useState({ name: '', url: '', interval: 60 })
  const [incidentBanner, setIncidentBanner] = useState<string | null>(null)

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
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['monitors'] })
    },
    onError: (error) => {
      console.error('Failed to trigger check:', error)
    },
  })

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'up':
        return <CheckCircle className="w-5 h-5 text-green-500" />
      case 'down':
        return <XCircle className="w-5 h-5 text-red-500" />
      case 'degraded':
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />
      default:
        return <Activity className="w-5 h-5 text-gray-400" />
    }
  }

  const getStatusBadge = (status: string) => {
    const styles = {
      up: 'bg-green-100 text-green-800',
      down: 'bg-red-100 text-red-800',
      degraded: 'bg-yellow-100 text-yellow-800',
      paused: 'bg-gray-100 text-gray-800',
    }
    return styles[status as keyof typeof styles] || styles.paused
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
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add Monitor
        </button>
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
                  <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusBadge(monitor.status)}`}>
                    {monitor.status}
                  </span>
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
    </div>
  )
}
