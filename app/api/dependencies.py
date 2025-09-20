from app.services.file_handler import FileHandler
from app.services.rtm_generator import RTMGenerator

def get_file_handler() -> FileHandler:
    """Dependency to get FileHandler instance"""
    return FileHandler()

def get_rtm_generator() -> RTMGenerator:
    """Dependency to get RTMGenerator instance"""
    return RTMGenerator()
