from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from app.api.routes import router
from app.config import settings
from app.utils.logger import setup_logger, get_logger
from app.services.file_handler import FileHandler

# Setup logging
setup_logger()
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting RTM AI Agent...")
    
    # Create necessary directories
    file_handler = FileHandler()
    
    # Log configuration
    logger.info(f"Upload directory: {settings.UPLOAD_DIR}")
    logger.info(f"Output directory: {settings.OUTPUT_DIR}")
    logger.info(f"Max file size: {settings.MAX_FILE_SIZE} bytes")
    logger.info(f"Focus sheet: {settings.FOCUS_SHEET_NAME}")
    
    # Check AI availability
    has_gemini = bool(settings.GEMINI_API_KEY)
    has_groq = bool(settings.GROQ_API_KEY)
    logger.info(f"Gemini API available: {has_gemini}")
    logger.info(f"Groq API available: {has_groq}")
    
    if not has_gemini and not has_groq:
        logger.warning("No AI API keys configured. Using fallback analysis.")
    
    yield
    
    # Shutdown
    logger.info("Shutting down RTM AI Agent...")

# Create FastAPI application
app = FastAPI(
    title="RTM AI Agent",
    description="Automated Requirements Traceability Matrix Generator with AI Analysis",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1", tags=["RTM Operations"])

# Root endpoint
@app.get("/")
async def root():
    """Welcome endpoint"""
    return {
        "message": "Welcome to RTM AI Agent",
        "version": "1.0.0",
        "docs": "/docs",
        "api_base": "/api/v1"
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
        log_level=settings.LOG_LEVEL.lower()
    )
