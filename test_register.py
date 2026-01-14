#!/usr/bin/env python
"""
Script de test pour l'inscription
"""
import requests
import json

# URL de l'API
BASE_URL = "http://localhost:8000/api"

def test_register():
    """Tester l'inscription"""
    url = f"{BASE_URL}/auth/register/"
    
    data = {
        "username": "testuser123",
        "email": "test@example.com",
        "password": "password123",
        "first_name": "Test",
        "last_name": "User",
        "phone_number": "79123456"
    }
    
    print("========== TEST REGISTER ==========")
    print(f"URL: {url}")
    print(f"Data: {json.dumps(data, indent=2)}")
    print()
    
    try:
        response = requests.post(url, json=data)
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print()
        
        if response.status_code == 201:
            print("✅ SUCCESS!")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        else:
            print("❌ ERROR!")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
    
    print("===================================")

if __name__ == "__main__":
    test_register()
