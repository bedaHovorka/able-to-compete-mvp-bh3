import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom'
import { LayoutDashboard, Trello, Activity, LogOut, User, Bell } from 'lucide-react'
import { useAuthStore } from '../store/authStore'
import { Navbar, Container, Nav, NavDropdown } from 'react-bootstrap'

export default function Layout() {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuthStore()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const isActive = (path: string) => location.pathname === path

  return (
    <div className="min-vh-100 d-flex flex-column">
      {/* Top Navbar */}
      <Navbar expand="lg" sticky="top" className="bg-white shadow-sm border-bottom">
        <Container fluid>
          <Navbar.Brand as={Link} to="/" className="d-flex align-items-center">
            <span className="text-gradient-primary fw-bold fs-4">AbleToCompete</span>
          </Navbar.Brand>

          <Navbar.Toggle aria-controls="navbar-nav" />

          <Navbar.Collapse id="navbar-nav">
            <Nav className="mx-auto">
              <Nav.Link
                as={Link}
                to="/"
                className={isActive('/') || isActive('/dashboard') ? 'active' : ''}
              >
                <LayoutDashboard size={18} className="me-2" style={{ verticalAlign: 'sub' }} />
                Dashboard
              </Nav.Link>
              <Nav.Link
                as={Link}
                to="/tasks"
                className={isActive('/tasks') ? 'active' : ''}
              >
                <Trello size={18} className="me-2" style={{ verticalAlign: 'sub' }} />
                Task Board
              </Nav.Link>
              <Nav.Link
                as={Link}
                to="/monitoring"
                className={isActive('/monitoring') ? 'active' : ''}
              >
                <Activity size={18} className="me-2" style={{ verticalAlign: 'sub' }} />
                Monitoring
              </Nav.Link>
            </Nav>

            <Nav className="align-items-center">
              <Nav.Link href="#notifications" className="position-relative me-2">
                <Bell size={20} />
                <span className="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger" style={{ fontSize: '0.65rem' }}>
                  3
                </span>
              </Nav.Link>

              <NavDropdown
                title={
                  <span>
                    <User size={18} className="me-1" style={{ verticalAlign: 'sub' }} />
                    {user?.email || 'User'}
                  </span>
                }
                id="user-dropdown"
                align="end"
              >
                <NavDropdown.Item href="#profile">
                  <User size={16} className="me-2" />
                  Profile
                </NavDropdown.Item>
                <NavDropdown.Item href="#settings">
                  Settings
                </NavDropdown.Item>
                <NavDropdown.Divider />
                <NavDropdown.Item onClick={handleLogout}>
                  <LogOut size={16} className="me-2" />
                  Logout
                </NavDropdown.Item>
              </NavDropdown>
            </Nav>
          </Navbar.Collapse>
        </Container>
      </Navbar>

      {/* Main Content */}
      <main className="flex-grow-1 py-4 animate-fade-in">
        <Container fluid>
          <Outlet />
        </Container>
      </main>

      {/* Footer */}
      <footer className="footer text-center">
        <Container>
          <small className="text-muted">
            © 2025 AbleToCompete MVP - Built with ❤️ for the 100K Challenge
          </small>
        </Container>
      </footer>
    </div>
  )
}
