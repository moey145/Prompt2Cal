#!/usr/bin/env python3
"""
Simple test script for Prompt2Cal API endpoints.
Run this after starting the backend server to test basic functionality.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_health():
    """Test the health endpoint."""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Health check: {response.status_code} - {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_auth_status():
    """Test the auth status endpoint."""
    print("\nTesting auth status endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/auth/status")
        print(f"Auth status: {response.status_code} - {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Auth status check failed: {e}")
        return False

def test_parse_event():
    """Test the event parsing endpoint."""
    print("\nTesting event parsing endpoint...")
    try:
        test_data = {
            "text": "Lunch with Sarah next Tuesday at 1pm"
        }
        response = requests.post(
            f"{BASE_URL}/create_event",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"Parse event: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Parsed event: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Parse event failed: {e}")
        return False

def test_google_auth_url():
    """Test getting Google auth URL."""
    print("\nTesting Google auth URL endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/auth/google")
        print(f"Auth URL: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Auth URL received: {'auth_url' in result}")
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Auth URL failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Prompt2Cal API Test Suite")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health),
        ("Auth Status", test_auth_status),
        ("Event Parsing", test_parse_event),
        ("Google Auth URL", test_google_auth_url),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"{test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("Test Results:")
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    print(f"\nSummary: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()
