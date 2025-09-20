import sys
from loguru import logger
from app.config import settings

def setup_logger():
    """Configure logger with appropriate settings"""
    logger.remove()  # Remove default handler
    
    # Console logging
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )
    
    # File logging
    logger.add(
        "logs/rtm_agent.log",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="7 days",
        compression="zip"
    )
    
    return logger

def get_logger(name: str = __name__):
    """Get logger instance"""
    return logger.bind(name=name)
