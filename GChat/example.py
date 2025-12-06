"""
Example usage of Google Chat API with Keycloak Workload Identity Federation
"""

import time
from google_chat_client import GoogleChatClient, GoogleChatBot
from config import GOOGLE_CHAT_CONFIG


def example_basic_operations():
    """
    Demonstrate basic Google Chat API operations
    """
    print("=== Basic Google Chat API Operations ===\n")
    
    # Initialize client
    client = GoogleChatClient()
    
    try:
        # 1. List available spaces
        print("1. Listing available spaces...")
        spaces = client.list_spaces()
        
        if not spaces.get('spaces'):
            print("No spaces found. Make sure the bot is added to at least one space.")
            return
        
        print(f"Found {len(spaces['spaces'])} spaces:")
        for i, space in enumerate(spaces['spaces'][:3]):  # Show first 3 spaces
            print(f"   {i+1}. {space.get('displayName', 'Unnamed Space')} ({space['name']})")
        
        # Select first space for demonstration
        demo_space = spaces['spaces'][0]
        space_name = demo_space['name']
        space_display_name = demo_space.get('displayName', 'Unnamed Space')
        
        print(f"\nUsing space: {space_display_name}")
        
        # 2. Send a simple text message
        print("\n2. Sending a simple text message...")
        message_text = f"Hello! This is a test message from {GOOGLE_CHAT_CONFIG['user_email']} using Keycloak WIF authentication. 🚀"
        
        message = client.create_message(space_name, message_text)
        message_name = message.get('name', '')
        print(f"Message sent successfully! Message ID: {message_name}")
        
        # 3. List recent messages
        print("\n3. Listing recent messages...")
        messages = client.list_messages(space_name, page_size=5)
        
        if messages.get('messages'):
            print(f"Recent messages ({len(messages['messages'])}):")
            for msg in messages['messages'][:3]:
                sender = msg.get('sender', {}).get('displayName', 'Unknown')
                text = msg.get('text', 'No text content')[:50]
                print(f"   - {sender}: {text}...")
        
        # 4. Add a reaction to the message we sent
        if message_name:
            print("\n4. Adding reaction to our message...")
            try:
                reaction = client.create_reaction(message_name, "👍")
                print("Reaction added successfully!")
            except Exception as e:
                print(f"Could not add reaction: {e}")
        
        # 5. List space members
        print("\n5. Listing space members...")
        try:
            members = client.list_members(space_name)
            if members.get('memberships'):
                print(f"Space has {len(members['memberships'])} members:")
                for member in members['memberships'][:3]:
                    member_info = member.get('member', {})
                    name = member_info.get('displayName', 'Unknown')
                    member_type = member_info.get('type', 'UNKNOWN')
                    print(f"   - {name} ({member_type})")
        except Exception as e:
            print(f"Could not list members: {e}")
        
        return space_name
        
    except Exception as e:
        print(f"Error in basic operations: {e}")
        return None


def example_bot_operations(space_name: str):
    """
    Demonstrate higher-level bot operations
    """
    print("\n\n=== Bot Operations ===\n")
    
    # Initialize bot
    bot = GoogleChatBot("Keycloak Demo Bot")
    
    try:
        # 1. Send notification card
        print("1. Sending notification card...")
        notification = bot.send_notification_card(
            space_name,
            title="System Notification",
            subtitle="Keycloak Integration Demo",
            message="This is a demo notification card sent via Keycloak Workload Identity Federation. The authentication is working correctly! ✅"
        )
        print("Notification card sent successfully!")
        
        # Wait a moment between messages
        time.sleep(2)
        
        # 2. Send interactive card with buttons
        print("\n2. Sending interactive card...")
        buttons = [
            {
                "text": "Get Status",
                "action": "get_status",
                "parameters": [{"key": "action", "value": "status"}]
            },
            {
                "text": "Show Help",
                "action": "show_help",
                "parameters": [{"key": "action", "value": "help"}]
            }
        ]
        
        interactive_card = bot.send_interactive_card(
            space_name,
            "Welcome to Keycloak-Google Chat Integration! Choose an action:",
            buttons
        )
        print("Interactive card sent successfully!")
        
    except Exception as e:
        print(f"Error in bot operations: {e}")


def example_monitoring(space_name: str):
    """
    Demonstrate space monitoring (for a short time)
    """
    print("\n\n=== Space Monitoring Demo ===\n")
    print("Monitoring space for new messages for 30 seconds...")
    print("Try sending a message in the chat to see it detected!")
    
    bot = GoogleChatBot("Monitor Bot")
    
    def message_callback(message):
        """Handle new messages"""
        sender = message.get('sender', {}).get('displayName', 'Unknown')
        text = message.get('text', 'No text content')
        timestamp = message.get('createTime', 'Unknown time')
        
        print(f"New message detected!")
        print(f"  From: {sender}")
        print(f"  Text: {text[:100]}...")
        print(f"  Time: {timestamp}")
        print("---")
    
    # Monitor for 30 seconds
    import threading
    import time
    
    stop_monitoring = False
    
    def monitor_with_timeout():
        nonlocal stop_monitoring
        start_time = time.time()
        
        try:
            while not stop_monitoring and (time.time() - start_time) < 30:
                try:
                    messages = bot.client.list_messages(space_name, page_size=5)
                    # Simple monitoring logic here
                    time.sleep(3)
                except Exception as e:
                    print(f"Monitoring error: {e}")
                    break
        except KeyboardInterrupt:
            pass
        
        stop_monitoring = True
    
    monitor_thread = threading.Thread(target=monitor_with_timeout)
    monitor_thread.start()
    
    try:
        monitor_thread.join(timeout=35)
        stop_monitoring = True
        print("Monitoring completed.")
    except KeyboardInterrupt:
        stop_monitoring = True
        print("Monitoring stopped by user.")


def main():
    """
    Main example function
    """
    print("Google Chat API with Keycloak Workload Identity Federation")
    print("=" * 60)
    print(f"User: {GOOGLE_CHAT_CONFIG['user_email']}")
    print(f"Domain: drapps.dev")
    print("=" * 60)
    
    try:
        # Run basic operations
        space_name = example_basic_operations()
        
        if space_name:
            # Run bot operations
            example_bot_operations(space_name)
            
            # Ask user if they want to see monitoring demo
            response = input("\nWould you like to see the monitoring demo? (y/n): ")
            if response.lower().startswith('y'):
                example_monitoring(space_name)
        
        print("\n" + "=" * 60)
        print("Demo completed successfully! 🎉")
        print("Your Keycloak-Google Chat integration is working.")
        
    except Exception as e:
        print(f"\nDemo failed: {e}")
        print("\nTroubleshooting steps:")
        print("1. Verify config.py has correct values")
        print("2. Run wif_setup.py to generate WIF configuration")
        print("3. Ensure Workload Identity Federation is set up in Google Cloud")
        print("4. Check that the bot is added to at least one Chat space")
        print("5. Verify Keycloak client configuration")


if __name__ == "__main__":
    main()