import { useState } from 'react'
import { Container, Card, Form, Button, Alert, Spinner, Badge, ButtonGroup } from 'react-bootstrap'
import { Bot, FileText, TestTube2, Code2, ChevronRight, Copy, Check, Play, RotateCcw } from 'lucide-react'
import { agents } from '../lib/api'

type SpecType = 'general' | 'user_story' | 'bdd'
type TestType = 'unit' | 'integration' | 'bdd'
type DevType = 'api' | 'service' | 'general' | 'model' | 'util'

function createAgentHandler(
  apiCall: () => Promise<string>,
  setResult: (result: string) => void,
  setLoading: (loading: boolean) => void,
  setError: (error: string | null) => void,
  errorMessage: string,
  logLabel: string,
) {
  return async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await apiCall()
      setResult(result)
    } catch (err) {
      console.error(logLabel, err)
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <Button variant="outline-secondary" size="sm" onClick={handleCopy} title="Copy to clipboard">
      {copied ? <Check size={14} className="text-success" /> : <Copy size={14} />}
    </Button>
  )
}

export default function Agents() {
  // Spec agent state
  const [requirements, setRequirements] = useState('')
  const [specType, setSpecType] = useState<SpecType>('general')
  const [specification, setSpecification] = useState('')
  const [specLoading, setSpecLoading] = useState(false)
  const [specError, setSpecError] = useState<string | null>(null)

  // Test agent state
  const [testSpec, setTestSpec] = useState('')
  const [testType, setTestType] = useState<TestType>('unit')
  const [testCode, setTestCode] = useState('')
  const [testLoading, setTestLoading] = useState(false)
  const [testError, setTestError] = useState<string | null>(null)

  // Dev agent state
  const [devSpec, setDevSpec] = useState('')
  const [devType, setDevType] = useState<DevType>('api')
  const [devCode, setDevCode] = useState('')
  const [devLoading, setDevLoading] = useState(false)
  const [devError, setDevError] = useState<string | null>(null)

  // Pipeline state
  const [pipelineLoading, setPipelineLoading] = useState(false)
  const [pipelineError, setPipelineError] = useState<string | null>(null)

  const handleGenerateSpec = async () => {
    if (!requirements.trim()) return
    await createAgentHandler(
      async () => {
        const res = await agents.spec({ requirements: requirements.trim(), type: specType })
        return res.data.specification
      },
      (spec) => { setSpecification(spec); setTestSpec(spec); setDevSpec(spec) },
      setSpecLoading,
      setSpecError,
      'Failed to generate specification. Please try again.',
      'Spec agent error:',
    )()
  }

  const handleGenerateTests = async () => {
    if (!testSpec.trim()) return
    await createAgentHandler(
      async () => {
        const res = await agents.test({ specification: testSpec.trim(), type: testType })
        return res.data.test_code
      },
      setTestCode,
      setTestLoading,
      setTestError,
      'Failed to generate tests. Please try again.',
      'Test agent error:',
    )()
  }

  const handleGenerateCode = async () => {
    if (!devSpec.trim()) return
    await createAgentHandler(
      async () => {
        const res = await agents.dev({ specification: devSpec.trim(), type: devType })
        return res.data.code
      },
      setDevCode,
      setDevLoading,
      setDevError,
      'Failed to generate code. Please try again.',
      'Dev agent error:',
    )()
  }

  const handleRunPipeline = async () => {
    if (!requirements.trim()) return
    setPipelineLoading(true)
    setPipelineError(null)
    setSpecError(null)
    setTestError(null)
    setDevError(null)
    try {
      const res = await agents.pipeline({
        requirements: requirements.trim(),
        run_steps: ['spec', 'test', 'dev'],
      })
      const { spec, tests, code, errors } = res.data
      if (spec) {
        setSpecification(spec)
        setTestSpec(spec)
        setDevSpec(spec)
      }
      if (tests) setTestCode(tests)
      if (code) setDevCode(code)
      if (errors.spec) setSpecError(errors.spec)
      if (errors.test) setTestError(errors.test)
      if (errors.dev) setDevError(errors.dev)
    } catch (err) {
      console.error('Pipeline error:', err)
      setPipelineError('Pipeline run failed. Please try again.')
    } finally {
      setPipelineLoading(false)
    }
  }

  const handleReset = () => {
    setRequirements('')
    setSpecification('')
    setSpecError(null)
    setTestSpec('')
    setTestCode('')
    setTestError(null)
    setDevSpec('')
    setDevCode('')
    setDevError(null)
    setPipelineError(null)
  }

  const hasSpec = specification.trim().length > 0
  const anyLoading = specLoading || testLoading || devLoading || pipelineLoading

  return (
    <Container className="py-4">
      {/* Page Header */}
      <div className="d-flex align-items-center justify-content-between mb-4">
        <div className="d-flex align-items-center">
          <Bot size={28} className="me-3 text-primary" />
          <div>
            <h2 className="mb-0 fw-bold">AI Agents</h2>
            <p className="text-muted mb-0 small">Three-step pipeline: Spec → Tests → Code</p>
          </div>
        </div>
        <Button variant="outline-secondary" size="sm" onClick={handleReset} disabled={anyLoading} title="Clear all outputs and start over">
          <RotateCcw size={14} className="me-1" />
          Reset
        </Button>
      </div>

      {/* Pipeline flow indicator + Run All button */}
      <div className="d-flex align-items-center justify-content-between mb-4 flex-wrap gap-2">
        <div className="d-flex align-items-center gap-2 flex-wrap">
          <Badge bg="primary" className="d-flex align-items-center gap-1 px-3 py-2">
            <FileText size={14} />
            Step 1: Spec
          </Badge>
          <ChevronRight size={16} className="text-muted" />
          <Badge bg={hasSpec ? 'success' : 'secondary'} className="d-flex align-items-center gap-1 px-3 py-2">
            <TestTube2 size={14} />
            Step 2: Tests
          </Badge>
          <ChevronRight size={16} className="text-muted" />
          <Badge bg={hasSpec ? 'success' : 'secondary'} className="d-flex align-items-center gap-1 px-3 py-2">
            <Code2 size={14} />
            Step 3: Code
          </Badge>
        </div>
        <Button
          variant="primary"
          onClick={handleRunPipeline}
          disabled={pipelineLoading || !requirements.trim()}
          title="Run all three steps automatically"
        >
          {pipelineLoading ? (
            <>
              <Spinner animation="border" size="sm" className="me-2" />
              Running pipeline…
            </>
          ) : (
            <>
              <Play size={16} className="me-2" />
              Run Full Pipeline
            </>
          )}
        </Button>
      </div>

      {pipelineError && (
        <Alert variant="danger" dismissible onClose={() => setPipelineError(null)} className="mb-4">
          {pipelineError}
        </Alert>
      )}

      {/* Step 1 — Spec Agent */}
      <Card className="mb-4 shadow-sm">
        <Card.Header className="bg-primary bg-opacity-10 border-bottom">
          <div className="d-flex align-items-center gap-2">
            <FileText size={18} className="text-primary" />
            <span className="fw-semibold">Step 1 — Spec Agent</span>
          </div>
        </Card.Header>
        <Card.Body>
          <Form>
            <Form.Group className="mb-3">
              <Form.Label className="fw-medium">Requirements</Form.Label>
              <Form.Control
                as="textarea"
                rows={5}
                placeholder="Describe the feature or system you want to specify..."
                value={requirements}
                onChange={(e) => setRequirements(e.target.value)}
                disabled={specLoading || pipelineLoading}
              />
            </Form.Group>
            <div className="d-flex gap-3 align-items-end mb-3">
              <Form.Group style={{ minWidth: '200px' }}>
                <Form.Label className="fw-medium">Spec Type</Form.Label>
                <Form.Select
                  value={specType}
                  onChange={(e) => setSpecType(e.target.value as SpecType)}
                  disabled={specLoading || pipelineLoading}
                >
                  <option value="general">General</option>
                  <option value="user_story">User Story</option>
                  <option value="bdd">BDD</option>
                </Form.Select>
              </Form.Group>
              <Button
                variant="primary"
                onClick={handleGenerateSpec}
                disabled={specLoading || pipelineLoading || !requirements.trim()}
              >
                {specLoading ? (
                  <>
                    <Spinner animation="border" size="sm" className="me-2" />
                    Generating…
                  </>
                ) : (
                  <>
                    <FileText size={16} className="me-2" />
                    Generate Spec
                  </>
                )}
              </Button>
            </div>
          </Form>

          {specError && (
            <Alert variant="danger" dismissible onClose={() => setSpecError(null)}>
              {specError}
            </Alert>
          )}

          {specification && (
            <div className="mt-3">
              <div className="d-flex align-items-center justify-content-between mb-2">
                <span className="fw-medium text-success">✓ Specification generated</span>
                <ButtonGroup size="sm">
                  <CopyButton text={specification} />
                </ButtonGroup>
              </div>
              <pre
                className="bg-light border rounded p-3"
                style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', fontSize: '0.875rem', maxHeight: '400px', overflowY: 'auto' }}
              >
                {specification}
              </pre>
              <small className="text-muted">Auto-populated in Steps 2 and 3</small>
            </div>
          )}
        </Card.Body>
      </Card>

      {/* Step 2 — Test Agent */}
      <Card className="mb-4 shadow-sm">
        <Card.Header className={`border-bottom ${hasSpec ? 'bg-success bg-opacity-10' : 'bg-secondary bg-opacity-10'}`}>
          <div className="d-flex align-items-center gap-2">
            <TestTube2 size={18} className={hasSpec ? 'text-success' : 'text-secondary'} />
            <span className="fw-semibold">Step 2 — Test Agent</span>
            {!hasSpec && <Badge bg="secondary" className="ms-1">Provide a specification below to enable</Badge>}
          </div>
        </Card.Header>
        <Card.Body>
          <Form>
            <Form.Group className="mb-3">
              <Form.Label className="fw-medium">Specification</Form.Label>
              <Form.Control
                as="textarea"
                rows={4}
                placeholder="Paste or edit the specification to generate tests from…"
                value={testSpec}
                onChange={(e) => setTestSpec(e.target.value)}
                disabled={testLoading || pipelineLoading}
              />
            </Form.Group>
            <div className="d-flex gap-3 align-items-end mb-3">
              <Form.Group style={{ minWidth: '200px' }}>
                <Form.Label className="fw-medium">Test Type</Form.Label>
                <Form.Select
                  value={testType}
                  onChange={(e) => setTestType(e.target.value as TestType)}
                  disabled={testLoading || pipelineLoading}
                >
                  <option value="unit">Unit</option>
                  <option value="integration">Integration</option>
                  <option value="bdd">BDD</option>
                </Form.Select>
              </Form.Group>
              <Button
                variant="success"
                onClick={handleGenerateTests}
                disabled={testLoading || pipelineLoading || !testSpec.trim()}
              >
                {testLoading ? (
                  <>
                    <Spinner animation="border" size="sm" className="me-2" />
                    Generating…
                  </>
                ) : (
                  <>
                    <TestTube2 size={16} className="me-2" />
                    Generate Tests
                  </>
                )}
              </Button>
            </div>
          </Form>

          {testError && (
            <Alert variant="danger" dismissible onClose={() => setTestError(null)}>
              {testError}
            </Alert>
          )}

          {testCode && (
            <div className="mt-3">
              <div className="d-flex align-items-center justify-content-between mb-2">
                <span className="fw-medium text-success">✓ Tests generated</span>
                <CopyButton text={testCode} />
              </div>
              <pre
                className="bg-dark text-light border rounded p-3"
                style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', fontSize: '0.8125rem', maxHeight: '400px', overflowY: 'auto' }}
              >
                <code>{testCode}</code>
              </pre>
            </div>
          )}
        </Card.Body>
      </Card>

      {/* Step 3 — Dev Agent */}
      <Card className="mb-4 shadow-sm">
        <Card.Header className={`border-bottom ${hasSpec ? 'bg-info bg-opacity-10' : 'bg-secondary bg-opacity-10'}`}>
          <div className="d-flex align-items-center gap-2">
            <Code2 size={18} className={hasSpec ? 'text-info' : 'text-secondary'} />
            <span className="fw-semibold">Step 3 — Dev Agent</span>
            {!hasSpec && <Badge bg="secondary" className="ms-1">Provide a specification below to enable</Badge>}
          </div>
        </Card.Header>
        <Card.Body>
          <Form>
            <Form.Group className="mb-3">
              <Form.Label className="fw-medium">Specification</Form.Label>
              <Form.Control
                as="textarea"
                rows={4}
                placeholder="Paste or edit the specification to generate code from…"
                value={devSpec}
                onChange={(e) => setDevSpec(e.target.value)}
                disabled={devLoading || pipelineLoading}
              />
            </Form.Group>
            <div className="d-flex gap-3 align-items-end mb-3">
              <Form.Group style={{ minWidth: '200px' }}>
                <Form.Label className="fw-medium">Code Type</Form.Label>
                <Form.Select
                  value={devType}
                  onChange={(e) => setDevType(e.target.value as DevType)}
                  disabled={devLoading || pipelineLoading}
                >
                  <option value="api">API</option>
                  <option value="service">Service</option>
                  <option value="general">General</option>
                  <option value="model">Model</option>
                  <option value="util">Util</option>
                </Form.Select>
              </Form.Group>
              <Button
                variant="info"
                onClick={handleGenerateCode}
                disabled={devLoading || pipelineLoading || !devSpec.trim()}
              >
                {devLoading ? (
                  <>
                    <Spinner animation="border" size="sm" className="me-2" />
                    Generating…
                  </>
                ) : (
                  <>
                    <Code2 size={16} className="me-2" />
                    Generate Code
                  </>
                )}
              </Button>
            </div>
          </Form>

          {devError && (
            <Alert variant="danger" dismissible onClose={() => setDevError(null)}>
              {devError}
            </Alert>
          )}

          {devCode && (
            <div className="mt-3">
              <div className="d-flex align-items-center justify-content-between mb-2">
                <span className="fw-medium text-info">✓ Code generated</span>
                <CopyButton text={devCode} />
              </div>
              <pre
                className="bg-dark text-light border rounded p-3"
                style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', fontSize: '0.8125rem', maxHeight: '400px', overflowY: 'auto' }}
              >
                <code>{devCode}</code>
              </pre>
            </div>
          )}
        </Card.Body>
      </Card>
    </Container>
  )
}
