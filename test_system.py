#!/usr/bin/env python3
"""
Test script for the new RTM AI Agent system
Tests the basic functionality without requiring actual Excel files
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.rtm_orchestrator import RTMOrchestrator
from app.services.dynamic_excel_processor import DynamicExcelProcessor
from app.services.groq_analyzer import GroqAnalyzer
from app.services.intelligent_chunker import IntelligentChunker
from app.config import settings

def test_imports():
    """Test that all new modules import correctly"""
    print("🧪 Testing imports...")
    
    try:
        orchestrator = RTMOrchestrator()
        print("✅ RTMOrchestrator imported and instantiated")
        
        excel_processor = DynamicExcelProcessor()
        print("✅ DynamicExcelProcessor imported and instantiated")
        
        groq_analyzer = GroqAnalyzer()
        print("✅ GroqAnalyzer imported and instantiated")
        
        chunker = IntelligentChunker()
        print("✅ IntelligentChunker imported and instantiated")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {str(e)}")
        return False

def test_configuration():
    """Test configuration settings"""
    print("\n🔧 Testing configuration...")
    
    print(f"📊 Max tokens per chunk: {settings.MAX_TOKENS_PER_CHUNK}")
    print(f"🔄 Token overlap: {settings.TOKEN_OVERLAP}")
    print(f"⚡ Groq requests per minute: {settings.GROQ_REQUESTS_PER_MINUTE}")
    print(f"🔢 Daily token limit: {settings.GROQ_DAILY_TOKEN_LIMIT:,}")
    print(f"🔑 Groq API key configured: {'Yes' if settings.GROQ_API_KEY else 'No'}")
    
    return True

def test_chunker():
    """Test the intelligent chunker with mock data"""
    print("\n✂️ Testing intelligent chunker...")
    
    try:
        chunker = IntelligentChunker()
        
        # Test token counting
        test_text = "This is a test requirement that should be counted for tokens."
        token_count = chunker.count_tokens(test_text)
        print(f"✅ Token counting works: '{test_text}' = {token_count} tokens")
        
        # Mock sheet data
        mock_requirements = [
            {
                'description': 'The system shall provide user authentication functionality',
                'original_id': 'REQ-001',
                'source': 'Sheet1!A1',
                'row_number': 1
            },
            {
                'description': 'The system shall maintain audit logs for all transactions',
                'original_id': 'REQ-002', 
                'source': 'Sheet1!A2',
                'row_number': 2
            }
        ]
        
        mock_sheet_data = {
            'sheet_name': 'Test Requirements',
            'requirements': mock_requirements
        }
        
        # Test chunking
        chunks = chunker.create_sheet_chunks(mock_sheet_data, is_focus_sheet=True)
        print(f"✅ Chunking works: Created {len(chunks)} chunks from {len(mock_requirements)} requirements")
        
        # Test validation
        validation_result = chunker.validate_chunks(chunks, mock_requirements)
        print(f"✅ Chunk validation: {'Passed' if validation_result else 'Failed'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Chunker error: {str(e)}")
        return False

def test_groq_analyzer():
    """Test Groq analyzer initialization"""
    print("\n🤖 Testing Groq analyzer...")
    
    try:
        analyzer = GroqAnalyzer()
        
        # Test usage statistics
        stats = analyzer.get_usage_statistics()
        print(f"✅ Usage statistics: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Groq analyzer error: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🚀 RTM AI Agent - System Validation Test")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 4
    
    # Run tests
    if test_imports():
        tests_passed += 1
        
    if test_configuration():
        tests_passed += 1
        
    if test_chunker():
        tests_passed += 1
        
    if test_groq_analyzer():
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 50)
    print(f"🎯 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! System is ready for operation.")
        print("\n🚀 Next steps:")
        print("   1. Run: streamlit run streamlit_app.py")
        print("   2. Upload an Excel file to test full functionality")
        print("   3. Select focus sheet and generate RTM")
    else:
        print("❌ Some tests failed. Please check the error messages above.")
        
    return tests_passed == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)