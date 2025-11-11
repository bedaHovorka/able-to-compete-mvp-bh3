# AbleToCompete MVP - Task Management & Monitoring

AI-first MVP combining Trello-like task management and Betterstack-like operational reliability monitoring.

## Features

### Task Management (Trello-like)
- ✅ Create and manage boards, lists, and cards
- ✅ Drag-and-drop interface (MVP implementation)
- ✅ Activity logging and audit trail
- ✅ Real-time updates via WebSocket

### Monitoring (Betterstack-like)
- ✅ HTTP/HTTPS health checks
- ✅ Automatic incident creation on failures
- ✅ Uptime percentage calculation
- ✅ Public status page
- ✅ Dashboard with metrics

### AI Agents
- ✅ **Spec Agent**: Generate specifications and user stories
- ✅ **Test Agent**: Generate test cases from specifications
- ✅ **Dev Agent**: Code generation assistance
- ✅ **Monitor Agent**: Incident analysis and root cause suggestions

### Additional Features
- ✅ JWT authentication
- ✅ Comprehensive audit logging
- ✅ Rate limiting
- ✅ BDD/TDD test structure
- ✅ Docker deployment ready

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Relational database
- **Redis** - Caching and WebSocket support
- **SQLAlchemy** - ORM with async support
- **pytest-bdd** - Behavior-driven testing

### Frontend
- **React 18** - UI library
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **TanStack Query** - Data fetching and caching
- **Zustand** - State management
- **Vite** - Build tool

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for local development)

### Option 1: Docker Compose (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd able-to-compete-mvp-bh3

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
# Status Page: http://localhost:3000/status
```

### Option 2: Local Development

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Start PostgreSQL and Redis (using Docker)
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=pass -e POSTGRES_USER=user -e POSTGRES_DB=abletocompete postgres:15
docker run -d -p 6379:6379 redis:7-alpine

# Run migrations (tables created automatically on startup)
# Start the server
uvicorn backend.app.main:app --reload
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

## API Endpoints

### Authentication
- `POST /api/auth/login` - Login
- `POST /api/auth/register` - Register new user

### Task Management
- `GET /api/boards` - List all boards
- `POST /api/boards` - Create board
- `GET /api/boards/{id}` - Get board with lists and cards
- `POST /api/boards/{id}/lists` - Create list
- `POST /api/lists/{id}/cards` - Create card
- `PUT /api/cards/{id}/move` - Move card

### Monitoring
- `GET /api/monitors` - List all monitors
- `POST /api/monitors` - Create monitor
- `GET /api/monitors/{id}/uptime` - Get uptime stats
- `POST /api/monitors/{id}/check` - Trigger manual check
- `GET /api/metrics/dashboard` - Dashboard metrics
- `GET /api/status-page` - Public status page (no auth)

### AI Agents
- `POST /api/ai/generate-specs` - Generate specifications
- `POST /api/ai/generate-tests` - Generate test code
- `POST /api/ai/generate-code` - Generate code
- `POST /api/ai/analyze-incident` - Analyze incident

### WebSocket
- `WS /ws/monitoring` - Real-time monitoring updates
- `WS /ws/tasks` - Real-time task updates

## Testing

```bash
cd backend

# Run BDD tests
pytest tests/ --bdd

# Run all tests
pytest tests/

# Run with coverage
pytest --cov=backend.app tests/
```

## Deployment

### Deploy to Railway

1. Push code to GitHub
2. Connect to Railway
3. Configure environment variables
4. Deploy automatically

### Deploy to Render

1. Create new Web Service
2. Connect GitHub repository
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`

### Deploy to Fly.io

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Login
flyctl auth login

# Deploy
flyctl launch
flyctl deploy
```

## Environment Variables

### Backend
```env
APP_NAME=AbleToCompete MVP
DEBUG=False
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30
MONITOR_CHECK_INTERVAL=30
ALERT_COOLDOWN=300
```

### Frontend
```env
VITE_API_URL=https://your-backend-url.com
```

## Project Structure

```
able-to-compete-mvp-bh3/
├── backend/
│   ├── app/
│   │   ├── agents/          # AI agents
│   │   ├── api/             # API endpoints
│   │   ├── models/          # SQLAlchemy models
│   │   ├── services/        # Business logic
│   │   ├── utils/           # Utilities (auth, db, logging)
│   │   ├── config.py        # Configuration
│   │   └── main.py          # FastAPI application
│   ├── tests/               # BDD tests
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/           # Page components
│   │   ├── lib/             # API client
│   │   ├── store/           # State management
│   │   └── main.tsx         # Entry point
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml       # Docker orchestration
└── README.md
```

## Demo Credentials

For MVP demonstration, any email/password combination will work.

Example:
- Email: `demo@example.com`
- Password: `password`

## Performance Optimizations

- ✅ Connection pooling for database
- ✅ Redis caching for frequent queries
- ✅ Async/await throughout
- ✅ Pagination on list endpoints
- ✅ Database indexes on frequently queried fields

## Security Features

- ✅ JWT authentication
- ✅ Password hashing with bcrypt
- ✅ Input validation with Pydantic
- ✅ SQL injection prevention via ORM
- ✅ Rate limiting on API endpoints
- ✅ CORS configuration

## Monitoring

The application includes self-monitoring capabilities:

1. Create monitors for your own services
2. Configure check intervals
3. View uptime statistics
4. Receive alerts on failures
5. Analyze incidents with AI

## License

MIT License

## Support

For issues and questions, please open a GitHub issue.

---

**Built with ❤️ for the Able to Compete 100K Challenge**
