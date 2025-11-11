import { useQuery } from '@tanstack/react-query'
import { CheckCircle, XCircle, AlertTriangle, Clock } from 'lucide-react'
import { dashboard } from '../lib/api'
import { format } from 'date-fns'

export default function StatusPage() {
  const { data: statusData } = useQuery({
    queryKey: ['status-page'],
    queryFn: () => dashboard.statusPage().then((res) => res.data),
    refetchInterval: 30000, // Refetch every 30 seconds
  })

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'up':
        return <CheckCircle className="w-6 h-6 text-green-500" />
      case 'down':
        return <XCircle className="w-6 h-6 text-red-500" />
      case 'degraded':
        return <AlertTriangle className="w-6 h-6 text-yellow-500" />
      default:
        return <Clock className="w-6 h-6 text-gray-400" />
    }
  }

  const getOverallStatus = () => {
    const monitors = statusData?.monitors || []
    if (monitors.some((m: any) => m.status === 'down')) {
      return { text: 'Service Disruption', color: 'text-red-600', bg: 'bg-red-100' }
    }
    if (monitors.some((m: any) => m.status === 'degraded')) {
      return { text: 'Partial Outage', color: 'text-yellow-600', bg: 'bg-yellow-100' }
    }
    return { text: 'All Systems Operational', color: 'text-green-600', bg: 'bg-green-100' }
  }

  const status = getOverallStatus()

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900">System Status</h1>
          <p className="mt-2 text-gray-600">Real-time status of all monitored services</p>
        </div>

        {/* Overall Status Banner */}
        <div className={`${status.bg} rounded-lg p-6 mb-8`}>
          <div className="flex items-center justify-center">
            <div className={`text-2xl font-semibold ${status.color}`}>
              {status.text}
            </div>
          </div>
        </div>

        {/* Services Status */}
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Monitored Services</h2>
          </div>

          <div className="divide-y divide-gray-200">
            {statusData?.monitors?.map((monitor: any) => (
              <div key={monitor.name} className="px-6 py-4 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex items-center flex-1">
                    {getStatusIcon(monitor.status)}
                    <div className="ml-4">
                      <div className="text-sm font-medium text-gray-900">
                        {monitor.name}
                      </div>
                      <div className="text-sm text-gray-500">
                        {monitor.uptime_24h}% uptime (24h)
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      monitor.status === 'up' ? 'bg-green-100 text-green-800' :
                      monitor.status === 'down' ? 'bg-red-100 text-red-800' :
                      'bg-yellow-100 text-yellow-800'
                    }`}>
                      {monitor.status.toUpperCase()}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-sm text-gray-500">
          Last updated: {statusData?.last_updated ? format(new Date(statusData.last_updated), 'PPpp') : 'N/A'}
        </div>

        {/* Powered By */}
        <div className="mt-4 text-center text-xs text-gray-400">
          Powered by AbleToCompete Monitoring
        </div>
      </div>
    </div>
  )
}
