"""
Command Line Interface for Google Chat Keycloak Integration
"""

import argparse
import sys
import json
from typing import Optional
from .auth import KeycloakWIFAuth
from .client import GoogleChatClient, GoogleChatBot
from .config import GOOGLE_CHAT_CONFIG
from .setup import setup_main


def cmd_setup(args):
    """Run setup process"""
    print("🔧 Running setup...")
    success = setup_main()
    return 0 if success else 1


def cmd_test_auth(args):
    """Test authentication"""
    print("🔐 Testing authentications...")
    

    """ Keycloak Token → STS Exchange → Federated Token → Service Account Impersonation → Google Chat Token """
    try:
        auth = KeycloakWIFAuth()
        token = auth.authenticate()
        
        if token:
            print(f"✓ Authentication successful!")
            print(f"  Access token: {token[:20]}...{token[-10:]}")
            
            # Verify authentication
            if auth.verify_authentication():
                print("✓ Token verification successful!")
                return 0
            else:
                print("❌ Token verification failed!")
                return 1
        else:
            print("❌ Failed to get access token")
            return 1
            
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return 1


def cmd_list_spaces(args):
    """List Google Chat spaces"""
    print("📋 Listing Google Chat spaces...")
    
    try:
        client = GoogleChatClient()
        spaces = client.list_spaces(page_size=args.limit)
        
        if not spaces.get('spaces'):
            print("No spaces found. Make sure the bot is added to at least one space.")
            return 1
        
        print(f"Found {len(spaces['spaces'])} spaces:")
        for i, space in enumerate(spaces['spaces'], 1):
            display_name = space.get('displayName', 'Unnamed Space')
            space_type = space.get('spaceType', 'Unknown')
            space_id = space.get('name')
            # Print only the short space id (strip the 'spaces/' prefix) so it's easy to copy for API calls
            short_id = space_id.split('/')[-1] if space_id else None
            print(f"{i:2}. {display_name} ({space_type})")
            print(f"     Resource id: {short_id}")
            if args.verbose:
                # Verbose shows the full JSON for extra debugging
                print(f"     Full object: {json.dumps(space, indent=2)}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Failed to list spaces: {e}")
        return 1


def cmd_send_message(args):
    """Send a message to a space"""
    if not args.space_id:
        print("❌ Space ID is required. Use 'list-spaces' to find space IDs.")
        return 1
    
    if not args.message:
        print("❌ Message text is required.")
        return 1
    
    print(f"💬 Sending message to space...")
    
    try:
        client = GoogleChatClient()
        message = client.create_message(args.space_id, args.message)
        
        print("✓ Message sent successfully!")
        if args.verbose:
            print(f"Message ID: {message.get('name', 'Unknown')}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Failed to send message: {e}")
        return 1


def cmd_send_card(args):
    """Send a notification card"""
    if not args.space_id:
        print("❌ Space ID is required. Use 'list-spaces' to find space IDs.")
        return 1
    
    print(f"🎴 Sending notification card...")
    
    try:
        bot = GoogleChatBot("CLI Bot")
        card = bot.send_notification_card(
            args.space_id,
            title=args.title or "Notification",
            subtitle=args.subtitle or "Google Chat Bot",
            message=args.message or "Hello from Google Chat CLI!"
        )
        
        print("✓ Notification card sent successfully!")
        if args.verbose:
            print(f"Message ID: {card.get('name', 'Unknown')}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Failed to send card: {e}")
        return 1


def cmd_demo(args):
    """Run interactive demo"""
    print("🚀 Google Chat Keycloak Integration Demo")
    print("=" * 50)
    
    try:
        # Test authentication
        print("\n1. Testing authentication...")
        auth = KeycloakWIFAuth()
        token = auth.authenticate()
        
        if not token:
            print("❌ Authentication failed")
            return 1
        
        print("✓ Authentication successful!")
        
        # List spaces
        print("\n2. Listing spaces...")
        client = GoogleChatClient()
        spaces = client.list_spaces(page_size=5)
        
        if not spaces.get('spaces'):
            print("❌ No spaces found. Add the bot to a space first.")
            return 1
        
        print(f"✓ Found {len(spaces['spaces'])} spaces")
        for i, space in enumerate(spaces['spaces'], 1):
            display_name = space.get('displayName', 'Unnamed Space')
            space_type = space.get('spaceType', 'Unknown')
            space_id = space.get('name')
            # Print only the short space id (strip the 'spaces/' prefix) so it's easy to copy for API calls
            short_id = space_id.split('/')[-1] if space_id else None
            print(f"{i:2}. {display_name} ({space_type})")
            print(f"     Resource id: {short_id}")
        
        
        # Show first space
        #demo_space = spaces['spaces'][0]
        demo_space = spaces['spaces'][1]
        space_name = demo_space['name']
        space_display_name = demo_space.get('displayName', 'Unnamed Space')
        
        print(f"\n3. Using space: {space_display_name}")
        
        # Send demo message
        print("\n4. Sending demo message...")
        demo_message = f"🤖 Hello from Google Chat CLI! Authentication via Keycloak WIF is working. User: {GOOGLE_CHAT_CONFIG['user_email']}"
        
        message = client.create_message(space_name, demo_message)
        print("✓ Demo message sent!")
        
        # Send demo card
        print("\n5. Sending demo card...")
        bot = GoogleChatBot("Demo Bot")
        card = bot.send_notification_card(
            space_name,
            title="🎉 Demo Successful!",
            subtitle="Keycloak Integration",
            message="Your Google Chat + Keycloak integration is working perfectly!"
        )
        print("✓ Demo card sent!")
        
        print("\n" + "=" * 50)
        print("🎉 Demo completed successfully!")
        print("Your Google Chat Keycloak integration is ready to use.")
        
        return 0
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return 1


def cmd_config(args):
    """Show configuration information"""
    print("⚙️  Configuration Information")
    print("=" * 40)
    
    from .config import KEYCLOAK_CONFIG, GOOGLE_CLOUD_CONFIG, GOOGLE_CHAT_CONFIG
    
    print(f"Keycloak Server: {KEYCLOAK_CONFIG['server_url']}")
    print(f"Keycloak Realm: {KEYCLOAK_CONFIG['realm']}")
    print(f"Keycloak Client: {KEYCLOAK_CONFIG['client_id']}")
    print(f"GCP Project: {GOOGLE_CLOUD_CONFIG['project_id']} ({GOOGLE_CLOUD_CONFIG['project_number']})")
    print(f"Service Account: {GOOGLE_CLOUD_CONFIG['service_account_email']}")
    print(f"Chat User: {GOOGLE_CHAT_CONFIG['user_email']}")
    
    if args.verbose:
        print("\nFull Configuration:")
        print("Keycloak:", json.dumps(KEYCLOAK_CONFIG, indent=2, default=str))
        print("Google Cloud:", json.dumps(GOOGLE_CLOUD_CONFIG, indent=2, default=str))
        print("Google Chat:", json.dumps(GOOGLE_CHAT_CONFIG, indent=2, default=str))
    
    return 0


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Google Chat API with Keycloak Workload Identity Federation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s setup                              # Run initial setup
  %(prog)s test-auth                          # Test authentication
  %(prog)s list-spaces                        # List available spaces
  %(prog)s send-message SPACE_ID "Hello!"     # Send a message
  %(prog)s demo                               # Run interactive demo
        """
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Run setup process')
    setup_parser.set_defaults(func=cmd_setup)
    
    # Test auth command
    auth_parser = subparsers.add_parser('test-auth', help='Test authentication')
    auth_parser.set_defaults(func=cmd_test_auth)
    
    # List spaces command
    spaces_parser = subparsers.add_parser('list-spaces', help='List Google Chat spaces')
    spaces_parser.add_argument('--limit', type=int, default=10, help='Maximum number of spaces to list')
    spaces_parser.set_defaults(func=cmd_list_spaces)
    
    # Send message command
    msg_parser = subparsers.add_parser('send-message', help='Send a message to a space')
    msg_parser.add_argument('space_id', help='Space ID (get from list-spaces)')
    msg_parser.add_argument('message', help='Message text to send')
    msg_parser.set_defaults(func=cmd_send_message)
    
    # Send card command
    card_parser = subparsers.add_parser('send-card', help='Send a notification card')
    card_parser.add_argument('space_id', help='Space ID (get from list-spaces)')
    card_parser.add_argument('--title', default='Notification', help='Card title')
    card_parser.add_argument('--subtitle', default='Google Chat Bot', help='Card subtitle')
    card_parser.add_argument('--message', default='Hello from CLI!', help='Card message')
    card_parser.set_defaults(func=cmd_send_card)
    
    # Demo command
    demo_parser = subparsers.add_parser('demo', help='Run interactive demo')
    demo_parser.set_defaults(func=cmd_demo)
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Show configuration')
    config_parser.set_defaults(func=cmd_config)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute command
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\n❌ Interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())