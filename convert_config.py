#!/usr/bin/env python3
"""
TFE Configuration Converter

This utility converts TFE configuration from JSON format (used with command-line
arguments) to the YAML format required by the dashboard's TFE integration.

Usage:
    python convert_config.py config.json ws-WORKSPACE-ID run-RUN-ID [output.yaml]

This is useful for users migrating from standalone TFE scripts to the dashboard
integration.
"""

import json
import yaml
import sys

def convert_config(config_json_file, workspace_id, run_id, output_file=None):
    """Convert config.json + args to YAML format."""
    
    # Load the JSON config
    try:
        with open(config_json_file, 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load {config_json_file}: {e}")
        return False
    
    # Create YAML config with all required fields
    yaml_config = {
        'tfe_server': config.get('tfeServer', config.get('tfe_server')),
        'organization': config.get('organization'),
        'token': config.get('token'),
        'workspace_id': workspace_id,
        'run_id': run_id,
        'verify_ssl': config.get('verify_ssl', True),
        'timeout': config.get('timeout', 30),
        'retry_attempts': config.get('retry_attempts', 3)
    }
    
    # Convert to YAML
    yaml_content = yaml.dump(yaml_config, default_flow_style=False, sort_keys=False)
    
    # Add header comment
    yaml_with_header = f"""# TFE Configuration for Dashboard Integration
# Generated from {config_json_file} + command line arguments
# 
# This file contains all the information needed for the TFE integration
# including the workspace and run IDs that were passed as arguments
# to your download script.

{yaml_content}"""
    
    # Output
    if output_file:
        with open(output_file, 'w') as f:
            f.write(yaml_with_header)
        print(f"✅ YAML config written to: {output_file}")
    else:
        print("📄 YAML Configuration:")
        print("=" * 40)
        print(yaml_with_header)
    
    # Show masked version for verification
    masked_config = yaml_config.copy()
    if 'token' in masked_config and masked_config['token']:
        token = masked_config['token']
        if len(token) > 8:
            masked_config['token'] = f"{token[:4]}{'*' * (len(token) - 8)}{token[-4:]}"
        else:
            masked_config['token'] = '*' * len(token)
    
    print("\n🔍 Configuration Summary (masked):")
    print("=" * 40)
    for key, value in masked_config.items():
        print(f"{key}: {value}")
    
    return True

def main():
    if len(sys.argv) < 4:
        print("Usage: python convert_config.py <config.json> <workspace-id> <run-id> [output.yaml]")
        print("\nExample:")
        print("  python convert_config.py config.json ws-ABC123456 run-XYZ789012")
        print("  python convert_config.py config.json ws-ABC123456 run-XYZ789012 tfe-config.yaml")
        print("\nThis converts your config.json + command line arguments")
        print("into the YAML format expected by the TFE integration.")
        sys.exit(1)
    
    config_json_file = sys.argv[1]
    workspace_id = sys.argv[2]
    run_id = sys.argv[3]
    output_file = sys.argv[4] if len(sys.argv) > 4 else None
    
    print("🔄 Converting Config Format")
    print("=" * 30)
    print(f"📄 Input JSON: {config_json_file}")
    print(f"🏗️ Workspace ID: {workspace_id}")
    print(f"🏃 Run ID: {run_id}")
    if output_file:
        print(f"📝 Output YAML: {output_file}")
    print()
    
    success = convert_config(config_json_file, workspace_id, run_id, output_file)
    
    if success:
        print("\n🎉 Conversion successful!")
        print("\n💡 Next steps:")
        print("1. Use the generated YAML file with the TFE integration")
        print("2. Upload it in the dashboard's TFE tab")
        print("3. The integration should now work with the same data as your download script")
    else:
        print("\n❌ Conversion failed!")

if __name__ == "__main__":
    main()