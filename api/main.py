"""FastAPI main application."""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from shared.database import engine, Base
from .routes import tasks, agents, payments, tools
from .middleware import logging_middleware

# Load environment variables
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    # Startup: Create database tables
    Base.metadata.create_all(bind=engine)
    print("Database initialized")
    yield
    # Shutdown
    print("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Hedera Marketplace API",
    description="Multi-agent marketplace with meta-tooling capabilities",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.middleware("http")(logging_middleware)

# Include routers
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(payments.router, prefix="/api/payments", tags=["payments"])
app.include_router(tools.router, prefix="/api/tools", tags=["tools"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Hedera Marketplace API",
        "version": "0.1.0",
        "agents": {
            "orchestrator": "Task analysis and coordination",
            "negotiator": "ERC-8004 discovery and x402 payments",
            "executor": "Dynamic tool creation and execution",
            "verifier": "Quality checks and payment release",
        },
        "features": [
            "ERC-8004 agent discovery",
            "HCS-10 coordination",
            "x402 payments",
            "Meta-tooling (dynamic tool creation)",
        ],
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))

    uvicorn.run("api.main:app", host=host, port=port, reload=True)
