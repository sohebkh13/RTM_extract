#!/usr/bin/env python3
"""
RTM AI Agent - Main Entry Point
Requirements Traceability Matrix Generator with AI Analysis
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import after path setup
from app.main import app
from app.config import settings
import uvicorn

def main():
    """Main entry point for the application"""
    print("=" * 60)
    print("🚀 RTM AI Agent - Dynamic Excel Analysis System")
    print("=" * 60)
    print(f"📊 Processing: Dynamic sheet detection")
    print(f"📁 Upload Directory: {settings.UPLOAD_DIR}")
    print(f"📁 Output Directory: {settings.OUTPUT_DIR}")
    print(f"🤖 Groq AI: {'✅ Configured' if settings.GROQ_API_KEY else '❌ Not configured'}")
    print(f"� Token Limit per Chunk: {settings.MAX_TOKENS_PER_CHUNK}")
    print(f"⚡ Rate Limit: {settings.GROQ_REQUESTS_PER_MINUTE} requests/minute")
    print(f"🌐 Server: http://{settings.API_HOST}:{settings.API_PORT}")
    print(f"📚 API Docs: http://{settings.API_HOST}:{settings.API_PORT}/docs")
    print("=" * 60)
    
    # Check if Groq API is configured
    if not settings.GROQ_API_KEY:
        print("⚠️  WARNING: GROQ_API_KEY not configured!")
        print("   The system will use rule-based analysis as fallback.")
        print("   For AI-powered analysis, configure GROQ_API_KEY in .env file.")
        print()
    else:
        print("✅ Groq AI configured - Full AI analysis available")
        print(f"   Model: {settings.GROQ_MODEL}")
        print(f"   Daily limits: {settings.GROQ_DAILY_REQUEST_LIMIT:,} requests, {settings.GROQ_DAILY_TOKEN_LIMIT:,} tokens")
        print()
    
    print("🎯 New Features:")
    print("   • Dynamic Excel structure detection")
    print("   • User-selectable focus sheets")
    print("   • 3-sheet RTM output (Detailed, Complete, Summary)")
    print("   • Smart chunking with rate limiting")
    print("   • Original data preservation")
    print()
    
    # Run the application
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
        log_level=settings.LOG_LEVEL.lower()
    )

if __name__ == "__main__":
    main()
