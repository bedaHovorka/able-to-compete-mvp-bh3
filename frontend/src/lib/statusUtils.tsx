import { CheckCircle, XCircle, AlertTriangle, Activity } from 'lucide-react'
import type { ReactElement } from 'react'

/**
 * Returns a Lucide icon element for a given monitor status.
 * @param status - Monitor status string ('up' | 'down' | 'degraded' | other)
 * @param size - Tailwind size class for the icon (default: 'w-5 h-5')
 */
export function getStatusIcon(status: string, size = 'w-5 h-5'): ReactElement {
  switch (status) {
    case 'up':
      return <CheckCircle className={`${size} text-green-500`} />
    case 'down':
      return <XCircle className={`${size} text-red-500`} />
    case 'degraded':
      return <AlertTriangle className={`${size} text-yellow-500`} />
    default:
      return <Activity className={`${size} text-gray-400`} />
  }
}

/**
 * Returns Tailwind badge classes for a given monitor status.
 * @param status - Monitor status string ('up' | 'down' | 'degraded' | 'paused' | other)
 */
export function getStatusBadgeClass(status: string): string {
  const styles: Record<string, string> = {
    up: 'bg-green-100 text-green-800',
    down: 'bg-red-100 text-red-800',
    degraded: 'bg-yellow-100 text-yellow-800',
    paused: 'bg-gray-100 text-gray-800',
  }
  return styles[status] ?? styles.paused
}
