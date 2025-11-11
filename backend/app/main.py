from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.utils.logger import logger
from app.utils.middleware import AuditMiddleware, RateLimitMiddleware
from app.utils.database import engine, Base
from app.api import auth, tasks, monitoring, websocket
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION}")

    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created/verified")

    yield

    # Cleanup
    logger.info("Shutting down application")
    await engine.dispose()


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="AI-first MVP combining task management and operational reliability monitoring",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware
app.add_middleware(AuditMiddleware)
app.add_middleware(RateLimitMiddleware, max_requests=100, window=60)

# Include routers
app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(monitoring.router)
app.include_router(websocket.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.VERSION
    }


@app.get("/api/ai/agents")
async def list_ai_agents():
    """List available AI agents"""
    return {
        "agents": [
            {
                "name": "spec_agent",
                "description": "Generate specifications and user stories from requirements",
                "endpoint": "/api/ai/generate-specs"
            },
            {
                "name": "test_agent",
                "description": "Generate test cases and pytest code from specifications",
                "endpoint": "/api/ai/generate-tests"
            },
            {
                "name": "dev_agent",
                "description": "Generate code from specifications",
                "endpoint": "/api/ai/generate-code"
            },
            {
                "name": "monitor_agent",
                "description": "Analyze incidents and provide solutions",
                "endpoint": "/api/ai/analyze-incident"
            }
        ]
    }


@app.post("/api/ai/generate-specs")
async def generate_specs(requirements: dict):
    """Generate specifications using AI agent"""
    from app.agents import SpecAgent

    agent = SpecAgent()
    result = await agent.process(requirements)
    return result


@app.post("/api/ai/generate-tests")
async def generate_tests(specification: dict):
    """Generate test code using AI agent"""
    from app.agents import TestAgent

    agent = TestAgent()
    result = await agent.process(specification)
    return result


@app.post("/api/ai/generate-code")
async def generate_code(specification: dict):
    """Generate code using AI agent"""
    from app.agents import DevAgent

    agent = DevAgent()
    result = await agent.process(specification)
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
