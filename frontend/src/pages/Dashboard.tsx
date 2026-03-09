import { useQuery, useQueries } from '@tanstack/react-query'
import { formatDistanceToNow } from 'date-fns'
import { Activity, TrendingUp, AlertCircle, CheckCircle2, Plus, Eye, Zap, ArrowRight, type LucideIcon } from 'lucide-react'
import { dashboard, boards as boardsApi } from '../lib/api'
import { Link } from 'react-router-dom'
import { Row, Col, Card, Alert, Badge, Placeholder } from 'react-bootstrap'
import type { ActivityEntry } from '../types'

function getActivityMeta(entry: ActivityEntry): {
  icon: LucideIcon
  bgClass: string
  iconClass: string
} {
  const { action, entity_type } = entry
  if (action === 'board_created') {
    return { icon: Plus, bgClass: 'bg-primary', iconClass: 'text-primary' }
  }
  if (action === 'card_created') {
    return { icon: Activity, bgClass: 'bg-primary', iconClass: 'text-primary' }
  }
  if (action === 'card_moved') {
    return { icon: ArrowRight, bgClass: 'bg-warning', iconClass: 'text-warning' }
  }
  if (entity_type === 'monitor') {
    if (action.includes('down')) {
      return { icon: AlertCircle, bgClass: 'bg-danger', iconClass: 'text-danger' }
    }
    return { icon: CheckCircle2, bgClass: 'bg-success', iconClass: 'text-success' }
  }
  return { icon: Activity, bgClass: 'bg-secondary', iconClass: 'text-secondary' }
}

export default function Dashboard() {
  const { data: metrics } = useQuery({
    queryKey: ['dashboard-metrics'],
    queryFn: () => dashboard.metrics().then((res) => res.data),
  })

  const { data: boardsList, isLoading: boardsLoading, isError: boardsError } = useQuery({
    queryKey: ['boards'],
    queryFn: () => boardsApi.list().then((res) => res.data),
  })

  const activityQueries = useQueries({
    queries: (boardsList ?? []).map((board) => ({
      queryKey: ['activity', board.id],
      queryFn: () => boardsApi.activity(board.id).then((r) => r.data),
      enabled: !!board.id,
    })),
  })

  const activityLoading = boardsLoading || activityQueries.some((q) => q.isLoading)

  const allActivity: ActivityEntry[] = activityQueries
    .flatMap((q) => q.data ?? [])
    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
    .slice(0, 5)

  const stats = [
    {
      name: 'Total Monitors',
      value: metrics?.total_monitors || 0,
      icon: Activity,
      colorClass: 'primary',
      borderClass: 'stat-card-primary',
    },
    {
      name: 'Monitors Up',
      value: metrics?.monitors_up || 0,
      icon: CheckCircle2,
      colorClass: 'success',
      borderClass: 'stat-card-success',
    },
    {
      name: 'Monitors Down',
      value: metrics?.monitors_down || 0,
      icon: AlertCircle,
      colorClass: 'danger',
      borderClass: 'stat-card-danger',
    },
    {
      name: 'Average Uptime',
      value: `${metrics?.avg_uptime?.toFixed(1) || 0}%`,
      icon: TrendingUp,
      colorClass: 'info',
      borderClass: 'stat-card-info',
    },
  ]

  return (
    <div className="animate-fade-in">
      {/* Page Header */}
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h1 className="h2 mb-1 fw-bold">Welcome back! 👋</h1>
          <p className="text-muted mb-0">Here's an overview of your tasks and monitoring status</p>
        </div>
      </div>

      {/* Active Incidents Alert */}
      {metrics?.active_incidents > 0 && (
        <Alert variant="danger" className="d-flex align-items-center mb-4 animate-slide-in">
          <AlertCircle className="me-3" size={24} />
          <div>
            <h5 className="alert-heading mb-1">Attention Required!</h5>
            <p className="mb-0">
              You have {metrics.active_incidents} active incident{metrics.active_incidents > 1 ? 's' : ''} requiring immediate attention.
            </p>
          </div>
        </Alert>
      )}

      {/* Stats Cards */}
      <Row className="g-4 mb-4">
        {stats.map((stat, index) => (
          <Col key={stat.name} xs={12} sm={6} lg={3}>
            <Card className={`stat-card ${stat.borderClass} h-100 animate-slide-in`} style={{ animationDelay: `${index * 100}ms` }}>
              <Card.Body>
                <div className="d-flex justify-content-between align-items-start mb-3">
                  <div className={`stat-icon bg-${stat.colorClass} bg-opacity-10 text-${stat.colorClass}`}>
                    <stat.icon size={32} />
                  </div>
                  <Zap className={`text-${stat.colorClass}`} size={20} />
                </div>
                <h6 className="text-muted text-uppercase fw-bold mb-1" style={{ fontSize: '0.75rem' }}>
                  {stat.name}
                </h6>
                <h2 className="mb-0 fw-bold">{stat.value}</h2>
              </Card.Body>
            </Card>
          </Col>
        ))}
      </Row>

      {/* Quick Actions */}
      <Card className="mb-4">
        <Card.Header className="d-flex justify-content-between align-items-center">
          <h5 className="mb-0 fw-bold">Quick Actions</h5>
          <Zap className="text-warning" size={20} />
        </Card.Header>
        <Card.Body>
          <Row className="g-3">
            <Col xs={12} md={4}>
              <Link to="/tasks" className="text-decoration-none">
                <Card className="card-gradient-primary h-100 border-0">
                  <Card.Body className="d-flex justify-content-between align-items-center">
                    <div>
                      <h5 className="fw-bold mb-1">Create Board</h5>
                      <p className="mb-0 opacity-75 small">Start a new project</p>
                    </div>
                    <Plus size={32} />
                  </Card.Body>
                </Card>
              </Link>
            </Col>

            <Col xs={12} md={4}>
              <Link to="/monitoring" className="text-decoration-none">
                <Card className="card-gradient-success h-100 border-0">
                  <Card.Body className="d-flex justify-content-between align-items-center">
                    <div>
                      <h5 className="fw-bold mb-1">Add Monitor</h5>
                      <p className="mb-0 opacity-75 small">Track uptime</p>
                    </div>
                    <Activity size={32} />
                  </Card.Body>
                </Card>
              </Link>
            </Col>

            <Col xs={12} md={4}>
              <Link to="/status" className="text-decoration-none">
                <Card className="card-gradient-info h-100 border-0">
                  <Card.Body className="d-flex justify-content-between align-items-center">
                    <div>
                      <h5 className="fw-bold mb-1">Status Page</h5>
                      <p className="mb-0 opacity-75 small">View all services</p>
                    </div>
                    <Eye size={32} />
                  </Card.Body>
                </Card>
              </Link>
            </Col>
          </Row>
        </Card.Body>
      </Card>

      {/* Recent Activity & System Status */}
      <Row className="g-4">
        <Col xs={12} lg={6}>
          <Card>
            <Card.Header>
              <h5 className="mb-0 fw-bold">Recent Activity</h5>
            </Card.Header>
            <Card.Body>
              {boardsError ? (
                <div className="text-center text-muted py-4">
                  <AlertCircle size={40} className="mb-2 text-danger opacity-75" />
                  <p className="mb-0">Failed to load activity. Please try again later.</p>
                </div>
              ) : activityLoading ? (
                <>
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="d-flex align-items-start mb-3">
                      <Placeholder as="div" animation="glow" className="me-3">
                        <Placeholder style={{ width: 40, height: 40, borderRadius: '50%' }} />
                      </Placeholder>
                      <div className="flex-grow-1">
                        <Placeholder as="p" animation="glow" className="mb-1">
                          <Placeholder xs={8} />
                        </Placeholder>
                        <Placeholder as="p" animation="glow" className="mb-0">
                          <Placeholder xs={4} size="sm" />
                        </Placeholder>
                      </div>
                    </div>
                  ))}
                </>
              ) : allActivity.length === 0 ? (
                <div className="text-center text-muted py-4">
                  <Activity size={40} className="mb-2 opacity-50" />
                  <p className="mb-0">No activity yet. Create a board or add a monitor to get started.</p>
                </div>
              ) : (
                allActivity.map((entry, index) => {
                  const { icon: Icon, bgClass, iconClass } = getActivityMeta(entry)
                  return (
                    <div key={entry.id} className={`d-flex align-items-start${index < allActivity.length - 1 ? ' mb-3' : ''}`}>
                      <div className={`${bgClass} bg-opacity-10 rounded-circle p-2 me-3 flex-shrink-0`}>
                        <Icon className={iconClass} size={20} />
                      </div>
                      <div className="flex-grow-1">
                        <h6 className="mb-1">{entry.details}</h6>
                        <small className="text-muted">
                          {formatDistanceToNow(new Date(entry.timestamp), { addSuffix: true })}
                        </small>
                      </div>
                    </div>
                  )
                })
              )}

              <div className="text-center mt-3">
                <Link to="/tasks" className="btn btn-outline-primary btn-sm">
                  View All Activity <ArrowRight size={16} className="ms-1" />
                </Link>
              </div>
            </Card.Body>
          </Card>
        </Col>

        <Col xs={12} lg={6}>
          <Card>
            <Card.Header>
              <h5 className="mb-0 fw-bold">System Status</h5>
            </Card.Header>
            <Card.Body>
              <div className="d-flex justify-content-between align-items-center mb-3 pb-3 border-bottom">
                <div>
                  <h6 className="mb-1">API Server</h6>
                  <small className="text-muted">api.abletocompete.com</small>
                </div>
                <Badge bg="success" className="px-3 py-2">
                  <CheckCircle2 size={14} className="me-1" />
                  Operational
                </Badge>
              </div>

              <div className="d-flex justify-content-between align-items-center mb-3 pb-3 border-bottom">
                <div>
                  <h6 className="mb-1">Database</h6>
                  <small className="text-muted">PostgreSQL 15</small>
                </div>
                <Badge bg="success" className="px-3 py-2">
                  <CheckCircle2 size={14} className="me-1" />
                  Operational
                </Badge>
              </div>

              <div className="d-flex justify-content-between align-items-center">
                <div>
                  <h6 className="mb-1">Redis Cache</h6>
                  <small className="text-muted">Redis 7</small>
                </div>
                <Badge bg="success" className="px-3 py-2">
                  <CheckCircle2 size={14} className="me-1" />
                  Operational
                </Badge>
              </div>

              <div className="text-center mt-3">
                <Link to="/status" className="btn btn-outline-primary btn-sm">
                  View Status Page <ArrowRight size={16} className="ms-1" />
                </Link>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </div>
  )
}
