import sys
import time
import requests
from pathlib import Path

def run_test():
    agents = [
        {"name": "Travel Concierge", "url": "http://localhost:8001/a2a"},
        {"name": "Planning Committee", "url": "http://localhost:8002/a2a"},
        {"name": "Itinerary Artist", "url": "http://localhost:8003/a2a"},
    ]

    print("🔍 Testing Agent Connectivity...")
    
    for agent in agents:
        payload = {
            "jsonrpc": "2.0",
            "method": "get_card", # This might return Method Not Found if not exposed directly, but proves server is up
            "id": 1
        }
        try:
            response = requests.post(agent["url"], json=payload, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    # Method not found means JSON-RPC server IS running and parsing!
                    print(f"✅ {agent['name']} is ONLINE (JSON-RPC Active).")
                else:
                    print(f"✅ {agent['name']} is ONLINE (Card Received).")
            else:
                 print(f"⚠️ {agent['name']} returned HTTP {response.status_code}.")
                
        except Exception as e:
            print(f"❌ {agent['name']} is OFFLINE. ({e})")

    print("\n🚀 Verification Complete. Run ./setup_and_run.sh to start the UI!")

if __name__ == "__main__":
    time.sleep(2)
    run_test()
