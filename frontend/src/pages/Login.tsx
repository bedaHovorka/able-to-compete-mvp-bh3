import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { auth } from '../lib/api'
import { Sparkles, Lock, Mail, ArrowRight, Zap, AlertCircle } from 'lucide-react'
import { Container, Row, Col, Card, Form, Button, Alert, Spinner } from 'react-bootstrap'

export default function Login() {
  const navigate = useNavigate()
  const setAuth = useAuthStore((state) => state.setAuth)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const response = await auth.login(email, password)
      const { access_token } = response.data

      setAuth(access_token, { email, id: 'demo-user-id' })
      navigate('/')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-container">
      <Container>
        <Row className="justify-content-center">
          <Col xs={12} sm={10} md={8} lg={5}>
            <div className="text-center mb-4 animate-scale-in">
              <div className="d-inline-flex align-items-center justify-content-center bg-white rounded-circle shadow-lg mb-3" style={{ width: '80px', height: '80px' }}>
                <Sparkles className="text-primary" size={40} />
              </div>
              <h1 className="text-white fw-bold mb-2" style={{ fontSize: '2.5rem' }}>
                AbleToCompete
              </h1>
              <p className="text-white-50 mb-0 fs-5">Welcome to the 100K Challenge</p>
            </div>

            <Card className="login-card shadow-lg animate-fade-in" style={{ animationDelay: '0.2s' }}>
              <Card.Body className="p-5">
                <h3 className="text-center mb-2 fw-bold">Sign In</h3>
                <p className="text-center text-muted mb-4">Enter your credentials to access your account</p>

                <Form onSubmit={handleSubmit}>
                  {error && (
                    <Alert variant="danger" className="d-flex align-items-center">
                      <AlertCircle size={20} className="me-2" />
                      {error}
                    </Alert>
                  )}

                  <Form.Group className="mb-3">
                    <Form.Label className="fw-semibold">Email Address</Form.Label>
                    <div className="position-relative">
                      <Mail className="position-absolute text-muted" size={20} style={{ left: '1rem', top: '50%', transform: 'translateY(-50%)', zIndex: 10 }} />
                      <Form.Control
                        type="email"
                        placeholder="demo@example.com"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                        className="ps-5"
                        style={{ height: '50px' }}
                      />
                    </div>
                  </Form.Group>

                  <Form.Group className="mb-4">
                    <Form.Label className="fw-semibold">Password</Form.Label>
                    <div className="position-relative">
                      <Lock className="position-absolute text-muted" size={20} style={{ left: '1rem', top: '50%', transform: 'translateY(-50%)', zIndex: 10 }} />
                      <Form.Control
                        type="password"
                        placeholder="Enter any password (demo)"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                        className="ps-5"
                        style={{ height: '50px' }}
                      />
                    </div>
                  </Form.Group>

                  <Button
                    variant="primary"
                    type="submit"
                    disabled={loading}
                    className="w-100 d-flex align-items-center justify-content-center"
                    style={{ height: '50px', fontSize: '1.1rem' }}
                  >
                    {loading ? (
                      <>
                        <Spinner animation="border" size="sm" className="me-2" />
                        Signing in...
                      </>
                    ) : (
                      <>
                        Sign in
                        <ArrowRight size={20} className="ms-2" />
                      </>
                    )}
                  </Button>
                </Form>

                <Alert variant="info" className="mt-4 mb-0 border-0 bg-primary bg-opacity-10">
                  <div className="d-flex align-items-start">
                    <Zap className="text-primary me-2 flex-shrink-0" size={20} />
                    <div>
                      <strong className="text-primary d-block mb-1">Demo Mode Active</strong>
                      <small className="text-muted">
                        Use any email and password combination to login and explore the application.
                      </small>
                    </div>
                  </div>
                </Alert>
              </Card.Body>
            </Card>

            <p className="text-center text-white-50 mt-4 mb-0">
              Built with 💙 for the Able to Compete Challenge
            </p>
          </Col>
        </Row>
      </Container>
    </div>
  )
}
