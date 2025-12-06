#!/usr/bin/env python3
"""
Test script for RAAG system
Verifies all components are working correctly
"""

import os
import sys
from pathlib import Path


def test_imports():
    """Test that all required packages can be imported"""
    print("Testing imports...")
    
    try:
        import fastapi
        import gradio
        import openai
        import requests
        import PIL
        import numpy
        print("✅ All packages imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Run: pip install -r requirements_enhanced.txt")
        return False


def test_openai_key():
    """Test OpenAI API key is set"""
    print("\nTesting OpenAI API key...")
    
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ OPENAI_API_KEY not set")
        print("Set it with: export OPENAI_API_KEY='sk-...'")
        return False
    
    if not api_key.startswith("sk-"):
        print("⚠️  API key doesn't start with 'sk-' - might be invalid")
        return False
    
    print(f"✅ API key found: {api_key[:10]}...")
    return True


def test_openai_connection():
    """Test actual connection to OpenAI"""
    print("\nTesting OpenAI connection...")
    
    try:
        from openai import OpenAI
        client = OpenAI()
        
        # Simple test call
        models = client.models.list()
        print("✅ Successfully connected to OpenAI")
        print(f"   Available models: {len(list(models.data))}")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI connection failed: {e}")
        return False


def test_raag_initialization():
    """Test RAAG system can be initialized"""
    print("\nTesting RAAG initialization...")
    
    try:
        from raag_enhanced import RAGMemory
        
        raag = RAGMemory(memory_file="test_memory.json")
        print("✅ RAAG initialized successfully")
        
        # Test basic operations
        stats = raag.get_statistics()
        print(f"   Statistics: {stats}")
        
        # Cleanup test file
        if os.path.exists("test_memory.json"):
            os.remove("test_memory.json")
        
        return True
        
    except Exception as e:
        print(f"❌ RAAG initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_classifier():
    """Test classifier can be initialized"""
    print("\nTesting Classifier initialization...")
    
    try:
        from raag_enhanced import RAGMemory
        from classifier_enhanced import EnhancedClassifier
        
        raag = RAGMemory(memory_file="test_memory.json")
        classifier = EnhancedClassifier(raag)
        
        print("✅ Classifier initialized successfully")
        
        # Cleanup
        if os.path.exists("test_memory.json"):
            os.remove("test_memory.json")
        
        return True
        
    except Exception as e:
        print(f"❌ Classifier initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_storage():
    """Test storage system"""
    print("\nTesting Storage system...")
    
    try:
        from storage import Storage
        
        storage = Storage()
        print("✅ Storage initialized successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Storage initialization failed: {e}")
        return False


def main():
    """Run all tests"""
    print("="*60)
    print("RAAG System Test Suite")
    print("="*60)
    
    tests = [
        ("Package Imports", test_imports),
        ("OpenAI API Key", test_openai_key),
        ("OpenAI Connection", test_openai_connection),
        ("RAAG System", test_raag_initialization),
        ("Classifier", test_classifier),
        ("Storage", test_storage),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Test '{name}' crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! System is ready to use.")
        print("\nRun: bash start_enhanced.sh")
        return 0
    else:
        print("\n⚠️  Some tests failed. Fix issues before running.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
