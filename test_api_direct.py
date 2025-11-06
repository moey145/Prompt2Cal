#!/usr/bin/env python3

import requests
import json

def test_api():
    """Test the API directly"""
    
    url = "http://localhost:8000/create_event"
    data = {
        "text": "Create 5 meetings every day this week at 2pm",
        "user_id": "test_user"
    }
    
    print("Testing API with recurring events...")
    print(f"Request data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, json=data)
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response data: {json.dumps(result, indent=2)}")
            
            # Check if it's bulk or single
            if result.get('is_bulk'):
                print(f"✅ SUCCESS: Detected as bulk event with {len(result.get('parsed_events', []))} events")
            else:
                print(f"❌ ISSUE: Detected as single event instead of bulk")
                print(f"   Title: {result.get('parsed_event', {}).get('title')}")
                print(f"   Start: {result.get('parsed_event', {}).get('start_time')}")
        else:
            print(f"❌ ERROR: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")

if __name__ == "__main__":
    test_api()
