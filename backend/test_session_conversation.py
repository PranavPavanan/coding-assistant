#!/usr/bin/env python3
"""Test script to demonstrate session/conversation functionality."""

import requests
import json
import uuid

# Base URL for the API
BASE_URL = "http://localhost:8000"

def test_session_conversation_flow():
    """Test the complete session/conversation flow."""
    
    print("🧪 Testing Session/Conversation Flow")
    print("=" * 50)
    
    # Test 1: First query - should auto-generate session_id and conversation_id
    print("\n1️⃣ First Query (Auto-generate IDs)")
    first_query = {
        "query": "what method is used for ranking?"
    }
    
    response = requests.post(f"{BASE_URL}/chat/query", json=first_query)
    if response.status_code == 200:
        data = response.json()
        session_id = data["session_id"]
        conversation_id = data["conversation_id"]
        print(f"✅ Generated Session ID: {session_id}")
        print(f"✅ Generated Conversation ID: {conversation_id}")
        print(f"📝 Response: {data['response'][:100]}...")
    else:
        print(f"❌ First query failed: {response.status_code} - {response.text}")
        return
    
    # Test 2: Second query in same conversation - should have context awareness
    print("\n2️⃣ Second Query (Same Conversation - Context Aware)")
    second_query = {
        "query": "can you explain alternate methods?",
        "conversation_id": conversation_id,
        "session_id": session_id
    }
    
    response = requests.post(f"{BASE_URL}/chat/query", json=second_query)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Used existing Session ID: {data['session_id']}")
        print(f"✅ Used existing Conversation ID: {data['conversation_id']}")
        print(f"📝 Response: {data['response'][:100]}...")
    else:
        print(f"❌ Second query failed: {response.status_code} - {response.text}")
    
    # Test 3: New conversation in same session
    print("\n3️⃣ Third Query (New Conversation, Same Session)")
    third_query = {
        "query": "what are the configuration options?",
        "session_id": session_id
        # No conversation_id - should create new conversation
    }
    
    response = requests.post(f"{BASE_URL}/chat/query", json=third_query)
    if response.status_code == 200:
        data = response.json()
        new_conversation_id = data["conversation_id"]
        print(f"✅ Used existing Session ID: {data['session_id']}")
        print(f"✅ Generated new Conversation ID: {new_conversation_id}")
        print(f"📝 Response: {data['response'][:100]}...")
    else:
        print(f"❌ Third query failed: {response.status_code} - {response.text}")
    
    # Test 4: Check session info
    print("\n4️⃣ Check Session Information")
    response = requests.get(f"{BASE_URL}/chat/session/{session_id}")
    if response.status_code == 200:
        session_info = response.json()
        print(f"✅ Session has {session_info['conversation_count']} conversations")
        print(f"✅ Session has {session_info['total_messages']} total messages")
        print(f"✅ Session created: {session_info['created_at']}")
    else:
        print(f"❌ Session info failed: {response.status_code} - {response.text}")
    
    # Test 5: List conversations in session
    print("\n5️⃣ List Conversations in Session")
    response = requests.get(f"{BASE_URL}/chat/session/{session_id}/conversations")
    if response.status_code == 200:
        conversations = response.json()
        print(f"✅ Found {len(conversations)} conversations in session:")
        for conv in conversations:
            print(f"   - {conv['conversation_id']}: {conv['message_count']} messages")
    else:
        print(f"❌ List conversations failed: {response.status_code} - {response.text}")
    
    # Test 6: Get conversation history
    print("\n6️⃣ Get Conversation History")
    response = requests.get(f"{BASE_URL}/chat/history?conversation_id={conversation_id}")
    if response.status_code == 200:
        history = response.json()
        print(f"✅ Conversation has {len(history['messages'])} messages:")
        for msg in history['messages']:
            role = msg['role']
            content = msg['content'][:50] + "..." if len(msg['content']) > 50 else msg['content']
            print(f"   - {role}: {content}")
    else:
        print(f"❌ Get history failed: {response.status_code} - {response.text}")
    
    # Test 7: Clear session
    print("\n7️⃣ Clear Session")
    clear_request = {
        "session_id": session_id,
        "clear_all": False
    }
    response = requests.post(f"{BASE_URL}/chat/session/clear", json=clear_request)
    if response.status_code == 200:
        clear_result = response.json()
        print(f"✅ Cleared {clear_result['sessions_cleared']} session(s)")
        print(f"✅ Cleared {clear_result['conversations_cleared']} conversation(s)")
        print(f"📝 Message: {clear_result['message']}")
    else:
        print(f"❌ Clear session failed: {response.status_code} - {response.text}")
    
    print("\n🎉 Session/Conversation flow test completed!")

if __name__ == "__main__":
    test_session_conversation_flow()
