import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, MoreVertical, Layout, Trello } from 'lucide-react'
import { boards, lists, cards } from '../lib/api'
import { Row, Col, Card, Button, Form, InputGroup, Badge, Modal } from 'react-bootstrap'

export default function TaskBoard() {
  const queryClient = useQueryClient()
  const [selectedBoard, setSelectedBoard] = useState<string | null>(null)
  const [newBoardName, setNewBoardName] = useState('')
  const [showNewBoardModal, setShowNewBoardModal] = useState(false)
  const [showNewListModal, setShowNewListModal] = useState(false)
  const [showNewCardModal, setShowNewCardModal] = useState(false)
  const [newListName, setNewListName] = useState('')
  const [newCardTitle, setNewCardTitle] = useState('')
  const [selectedListId, setSelectedListId] = useState<string | null>(null)

  const { data: boardsList } = useQuery({
    queryKey: ['boards'],
    queryFn: () => boards.list().then((res) => res.data),
  })

  const { data: boardDetail } = useQuery({
    queryKey: ['board', selectedBoard],
    queryFn: () => boards.get(selectedBoard!).then((res) => res.data),
    enabled: !!selectedBoard,
  })

  const createBoardMutation = useMutation({
    mutationFn: (name: string) => boards.create({ name }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['boards'] })
      setNewBoardName('')
      setShowNewBoardModal(false)
    },
  })

  const createListMutation = useMutation({
    mutationFn: (data: { boardId: string; name: string }) =>
      lists.create(data.boardId, { name: data.name, position: 0 }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['board', selectedBoard] })
      setNewListName('')
      setShowNewListModal(false)
    },
  })

  const createCardMutation = useMutation({
    mutationFn: (data: { listId: string; title: string }) =>
      cards.create(data.listId, { title: data.title }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['board', selectedBoard] })
      setNewCardTitle('')
      setShowNewCardModal(false)
      setSelectedListId(null)
    },
  })

  const handleCreateBoard = () => {
    if (newBoardName.trim()) {
      createBoardMutation.mutate(newBoardName)
    }
  }

  const handleCreateList = () => {
    if (newListName.trim() && selectedBoard) {
      createListMutation.mutate({ boardId: selectedBoard, name: newListName })
    }
  }

  const handleCreateCard = () => {
    if (newCardTitle.trim() && selectedListId) {
      createCardMutation.mutate({ listId: selectedListId, title: newCardTitle })
    }
  }

  return (
    <div className="animate-fade-in">
      {/* Page Header */}
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h1 className="h2 mb-1 fw-bold">
            <Trello size={32} className="me-2 text-primary" style={{ verticalAlign: 'sub' }} />
            Task Boards
          </h1>
          <p className="text-muted mb-0">Create and manage your project boards</p>
        </div>
        <Button
          variant="primary"
          onClick={() => setShowNewBoardModal(true)}
          className="d-flex align-items-center"
        >
          <Plus size={18} className="me-2" />
          New Board
        </Button>
      </div>

      {/* Boards Grid */}
      {!selectedBoard ? (
        <>
          <Row className="g-4 mb-4">
            {boardsList?.length === 0 && (
              <Col xs={12}>
                <Card className="text-center py-5">
                  <Card.Body>
                    <Layout size={48} className="text-muted mb-3" />
                    <h4 className="text-muted">No boards yet</h4>
                    <p className="text-muted mb-3">Create your first board to get started</p>
                    <Button variant="primary" onClick={() => setShowNewBoardModal(true)}>
                      <Plus size={18} className="me-2" />
                      Create Board
                    </Button>
                  </Card.Body>
                </Card>
              </Col>
            )}

            {boardsList?.map((board: any) => (
              <Col key={board.id} xs={12} sm={6} lg={4}>
                <Card
                  className="h-100 shadow-sm-hover"
                  style={{ cursor: 'pointer' }}
                  onClick={() => setSelectedBoard(board.id)}
                >
                  <Card.Body>
                    <div className="d-flex justify-content-between align-items-start mb-2">
                      <h5 className="card-title mb-0 fw-bold">{board.name}</h5>
                      <Badge bg="primary" className="ms-2">
                        {board.lists?.length || 0} lists
                      </Badge>
                    </div>
                    {board.description && (
                      <p className="text-muted small mb-0">{board.description}</p>
                    )}
                    <div className="mt-3">
                      <small className="text-muted">
                        Created {new Date(board.created_at).toLocaleDateString()}
                      </small>
                    </div>
                  </Card.Body>
                </Card>
              </Col>
            ))}
          </Row>
        </>
      ) : (
        <>
          {/* Board Detail View */}
          <Card className="mb-4">
            <Card.Header className="bg-white d-flex justify-content-between align-items-center">
              <div>
                <Button
                  variant="outline-secondary"
                  size="sm"
                  onClick={() => setSelectedBoard(null)}
                  className="me-3"
                >
                  ← Back
                </Button>
                <span className="h4 mb-0 fw-bold">{boardDetail?.name}</span>
              </div>
              <Button
                variant="success"
                size="sm"
                onClick={() => setShowNewListModal(true)}
              >
                <Plus size={16} className="me-1" />
                Add List
              </Button>
            </Card.Header>
          </Card>

          {/* Lists (Kanban Columns) */}
          <div className="d-flex gap-3 overflow-auto pb-4" style={{ minHeight: '500px' }}>
            {boardDetail?.lists?.map((list: any) => (
              <Card
                key={list.id}
                className="flex-shrink-0 bg-light border-0"
                style={{ width: '300px', maxHeight: '600px' }}
              >
                <Card.Header className="bg-light border-0 d-flex justify-content-between align-items-center">
                  <h6 className="mb-0 fw-bold">{list.name}</h6>
                  <Badge bg="secondary">{list.cards?.length || 0}</Badge>
                </Card.Header>
                <Card.Body className="overflow-auto">
                  <div className="d-flex flex-column gap-2">
                    {list.cards?.map((card: any) => (
                      <Card
                        key={card.id}
                        className="shadow-sm"
                        style={{ cursor: 'pointer' }}
                      >
                        <Card.Body className="p-3">
                          <p className="mb-1 fw-medium">{card.title}</p>
                          {card.description && (
                            <p className="mb-0 text-muted small">{card.description}</p>
                          )}
                        </Card.Body>
                      </Card>
                    ))}

                    <Button
                      variant="light"
                      size="sm"
                      className="w-100 text-start border-0"
                      onClick={() => {
                        setSelectedListId(list.id)
                        setShowNewCardModal(true)
                      }}
                    >
                      <Plus size={16} className="me-1" />
                      Add a card
                    </Button>
                  </div>
                </Card.Body>
              </Card>
            ))}

            {/* Add List Button */}
            <Card
              className="flex-shrink-0 bg-light border-2 border-dashed text-center"
              style={{ width: '300px', cursor: 'pointer' }}
              onClick={() => setShowNewListModal(true)}
            >
              <Card.Body className="d-flex flex-column justify-content-center align-items-center" style={{ minHeight: '150px' }}>
                <Plus size={32} className="text-muted mb-2" />
                <p className="text-muted mb-0 fw-medium">Add another list</p>
              </Card.Body>
            </Card>
          </div>
        </>
      )}

      {/* New Board Modal */}
      <Modal show={showNewBoardModal} onHide={() => setShowNewBoardModal(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>Create New Board</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form>
            <Form.Group>
              <Form.Label>Board Name</Form.Label>
              <Form.Control
                type="text"
                placeholder="Enter board name"
                value={newBoardName}
                onChange={(e) => setNewBoardName(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleCreateBoard()}
                autoFocus
              />
            </Form.Group>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowNewBoardModal(false)}>
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={handleCreateBoard}
            disabled={!newBoardName.trim() || createBoardMutation.isPending}
          >
            {createBoardMutation.isPending ? 'Creating...' : 'Create Board'}
          </Button>
        </Modal.Footer>
      </Modal>

      {/* New List Modal */}
      <Modal show={showNewListModal} onHide={() => setShowNewListModal(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>Create New List</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form>
            <Form.Group>
              <Form.Label>List Name</Form.Label>
              <Form.Control
                type="text"
                placeholder="Enter list name (e.g., To Do, In Progress)"
                value={newListName}
                onChange={(e) => setNewListName(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleCreateList()}
                autoFocus
              />
            </Form.Group>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowNewListModal(false)}>
            Cancel
          </Button>
          <Button
            variant="success"
            onClick={handleCreateList}
            disabled={!newListName.trim() || createListMutation.isPending}
          >
            {createListMutation.isPending ? 'Creating...' : 'Create List'}
          </Button>
        </Modal.Footer>
      </Modal>

      {/* New Card Modal */}
      <Modal show={showNewCardModal} onHide={() => setShowNewCardModal(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>Create New Card</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form>
            <Form.Group>
              <Form.Label>Card Title</Form.Label>
              <Form.Control
                type="text"
                placeholder="Enter card title"
                value={newCardTitle}
                onChange={(e) => setNewCardTitle(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleCreateCard()}
                autoFocus
              />
            </Form.Group>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowNewCardModal(false)}>
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={handleCreateCard}
            disabled={!newCardTitle.trim() || createCardMutation.isPending}
          >
            {createCardMutation.isPending ? 'Creating...' : 'Create Card'}
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  )
}
