#!/usr/bin/env python3
"""
Debug script for TFE connection issues.

This script helps debug TFE connection problems by testing each step
of the connection process and providing detailed error information.
"""

import sys
import yaml
import json
from pathlib import Path
from providers.tfe_client import TFEClient
from utils.credential_manager import CredentialManager

def debug_tfe_connection(config_file: str):
    """Debug TFE connection step by step."""
    
    print("🔍 TFE Connection Debug Tool")
    print("=" * 50)
    
    # Step 1: Load and validate configuration
    print("\n📋 Step 1: Loading configuration...")
    try:
        with open(config_file, 'r') as f:
            yaml_content = f.read()
        
        config = yaml.safe_load(yaml_content)
        print(f"✅ Configuration loaded from {config_file}")
        
        # Show masked config
        masked_config = config.copy()
        if 'token' in masked_config:
            token = masked_config['token']
            if len(token) > 8:
                masked_config['token'] = f"{token[:4]}{'*' * (len(token) - 8)}{token[-4:]}"
            else:
                masked_config['token'] = '*' * len(token)
        
        print("📄 Configuration:")
        for key, value in masked_config.items():
            print(f"   {key}: {value}")
        
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        return False
    
    # Step 2: Validate configuration
    print("\n🔍 Step 2: Validating configuration...")
    try:
        cm = CredentialManager()
        is_valid, errors = cm.validate_config(config)
        
        if is_valid:
            print("✅ Configuration is valid")
        else:
            print("❌ Configuration validation failed:")
            for error in errors:
                print(f"   - {error}")
            return False
            
        cm.store_credentials(config)
        
    except Exception as e:
        print(f"❌ Configuration validation error: {e}")
        return False
    
    # Step 3: Test connection
    print("\n🌐 Step 3: Testing TFE server connection...")
    try:
        client = TFEClient(cm)
        is_connected, connection_message = client.validate_connection()
        
        if is_connected:
            print("✅ TFE server connection successful")
        else:
            print(f"❌ TFE server connection failed: {connection_message}")
            return False
            
    except Exception as e:
        print(f"❌ Connection test error: {e}")
        return False
    
    # Step 4: Test authentication
    print("\n🔐 Step 4: Testing authentication...")
    try:
        tfe_config = cm.get_config()
        is_authenticated, auth_error = client.authenticate(
            tfe_config.tfe_server,
            tfe_config.token,
            tfe_config.organization
        )
        
        if is_authenticated:
            print("✅ Authentication successful")
        else:
            print(f"❌ Authentication failed: {auth_error}")
            return False
            
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return False
    
    # Step 5: Test plan retrieval (the main issue)
    print("\n📥 Step 5: Testing plan retrieval...")
    try:
        tfe_config = cm.get_config()
        
        # First, let's test the plan info endpoint directly
        print(f"   🔍 Testing plan info endpoint for run: {tfe_config.run_id}")
        
        plan_data, error_message = client.get_plan_json(
            tfe_config.workspace_id,
            tfe_config.run_id
        )
        
        if error_message:
            print(f"❌ Plan retrieval failed: {error_message}")
            
            # Let's try to get more detailed information
            print("\n🔧 Detailed debugging:")
            
            # Test the plan info endpoint directly
            try:
                plan_info, plan_error = client._get_plan_info_from_run_with_retry(tfe_config.run_id)
                if plan_error:
                    print(f"   ❌ Plan info endpoint failed: {plan_error}")
                else:
                    print("   ✅ Plan info endpoint accessible")
                    print(f"   📊 Plan info structure: {list(plan_info.keys()) if plan_info else 'None'}")
                    
                    if plan_info and 'data' in plan_info:
                        data = plan_info['data']
                        print(f"   📊 Plan data structure: {list(data.keys()) if data else 'None'}")
                        
                        if 'links' in data:
                            links = data['links']
                            print(f"   🔗 Available links: {list(links.keys()) if links else 'None'}")
                            
                            if 'json-output-redacted' in links:
                                json_link = links['json-output-redacted']
                                print(f"   ✅ JSON output link found: {json_link}")
                            else:
                                print("   ❌ No json-output-redacted link found")
                                print(f"   🔍 Available links: {links}")
                        else:
                            print("   ❌ No links section in plan data")
                    else:
                        print("   ❌ No data section in plan info")
                        
            except Exception as debug_e:
                print(f"   ❌ Debug error: {debug_e}")
            
            return False
        else:
            print("✅ Plan retrieval successful!")
            
            # Show plan summary
            if plan_data:
                print("\n📊 Plan Summary:")
                if 'terraform_version' in plan_data:
                    print(f"   Terraform Version: {plan_data['terraform_version']}")
                if 'format_version' in plan_data:
                    print(f"   Format Version: {plan_data['format_version']}")
                if 'resource_changes' in plan_data:
                    changes = plan_data['resource_changes']
                    print(f"   Resource Changes: {len(changes)}")
                    
                    # Count actions
                    actions = {}
                    for change in changes:
                        change_actions = change.get('change', {}).get('actions', [])
                        for action in change_actions:
                            actions[action] = actions.get(action, 0) + 1
                    
                    for action, count in actions.items():
                        print(f"     {action}: {count}")
            
            return True
            
    except Exception as e:
        print(f"❌ Plan retrieval error: {e}")
        import traceback
        print("🔍 Full traceback:")
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        try:
            client.close()
        except:
            pass

def main():
    if len(sys.argv) != 2:
        print("Usage: python debug_tfe_connection.py <config.yaml>")
        print("\nExample:")
        print("  python debug_tfe_connection.py config.yaml")
        sys.exit(1)
    
    config_file = sys.argv[1]
    
    if not Path(config_file).exists():
        print(f"❌ Configuration file not found: {config_file}")
        sys.exit(1)
    
    success = debug_tfe_connection(config_file)
    
    if success:
        print("\n🎉 All tests passed! TFE integration should work.")
    else:
        print("\n❌ Some tests failed. Check the errors above.")
        print("\n💡 Common solutions:")
        print("   - Verify your token has the correct permissions")
        print("   - Check that the workspace and run IDs are correct")
        print("   - Ensure the run has completed and generated JSON output")
        print("   - Try with a different, more recent run")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()