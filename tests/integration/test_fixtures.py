"""
Test fixtures for integration tests

Provides sample Terraform plan data of various sizes and complexity levels.
"""

import json
from typing import Dict, Any, List


class TestFixtures:
    """Test fixtures for various Terraform plan scenarios"""
    
    @staticmethod
    def get_minimal_plan() -> Dict[str, Any]:
        """Get minimal valid Terraform plan for basic testing"""
        return {
            "terraform_version": "1.0.0",
            "format_version": "1.0",
            "resource_changes": []
        }
    
    @staticmethod
    def get_simple_plan() -> Dict[str, Any]:
        """Get simple Terraform plan with basic resource changes"""
        return {
            "terraform_version": "1.5.0",
            "format_version": "1.2",
            "resource_changes": [
                {
                    "address": "aws_instance.web",
                    "mode": "managed",
                    "type": "aws_instance",
                    "name": "web",
                    "provider_name": "registry.terraform.io/hashicorp/aws",
                    "change": {
                        "actions": ["create"],
                        "before": None,
                        "after": {
                            "ami": "ami-12345678",
                            "instance_type": "t3.micro",
                            "tags": {
                                "Name": "web-server",
                                "Environment": "production"
                            }
                        }
                    }
                },
                {
                    "address": "aws_s3_bucket.data",
                    "mode": "managed",
                    "type": "aws_s3_bucket",
                    "name": "data",
                    "provider_name": "registry.terraform.io/hashicorp/aws",
                    "change": {
                        "actions": ["update"],
                        "before": {
                            "bucket": "my-data-bucket",
                            "versioning": [{"enabled": False}]
                        },
                        "after": {
                            "bucket": "my-data-bucket",
                            "versioning": [{"enabled": True}]
                        }
                    }
                }
            ]
        }
    
    @staticmethod
    def get_multi_cloud_plan() -> Dict[str, Any]:
        """Get multi-cloud Terraform plan with AWS, Azure, and GCP resources"""
        return {
            "terraform_version": "1.6.0",
            "format_version": "1.2",
            "resource_changes": [
                # AWS resources
                {
                    "address": "aws_instance.web",
                    "mode": "managed",
                    "type": "aws_instance",
                    "name": "web",
                    "provider_name": "registry.terraform.io/hashicorp/aws",
                    "change": {
                        "actions": ["create"],
                        "before": None,
                        "after": {
                            "ami": "ami-12345678",
                            "instance_type": "t3.medium",
                            "security_groups": ["sg-12345678"],
                            "tags": {
                                "Name": "web-server",
                                "Environment": "production",
                                "Provider": "aws"
                            }
                        }
                    }
                },
                {
                    "address": "aws_security_group.web",
                    "mode": "managed",
                    "type": "aws_security_group",
                    "name": "web",
                    "provider_name": "registry.terraform.io/hashicorp/aws",
                    "change": {
                        "actions": ["create"],
                        "before": None,
                        "after": {
                            "name": "web-sg",
                            "ingress": [
                                {
                                    "from_port": 80,
                                    "to_port": 80,
                                    "protocol": "tcp",
                                    "cidr_blocks": ["0.0.0.0/0"]
                                }
                            ]
                        }
                    }
                },
                # Azure resources
                {
                    "address": "azurerm_virtual_machine.app",
                    "mode": "managed",
                    "type": "azurerm_virtual_machine",
                    "name": "app",
                    "provider_name": "registry.terraform.io/hashicorp/azurerm",
                    "change": {
                        "actions": ["create"],
                        "before": None,
                        "after": {
                            "name": "app-vm",
                            "location": "East US",
                            "resource_group_name": "my-rg",
                            "vm_size": "Standard_B2s",
                            "tags": {
                                "Environment": "production",
                                "Provider": "azure"
                            }
                        }
                    }
                },
                {
                    "address": "azurerm_storage_account.data",
                    "mode": "managed",
                    "type": "azurerm_storage_account",
                    "name": "data",
                    "provider_name": "registry.terraform.io/hashicorp/azurerm",
                    "change": {
                        "actions": ["update"],
                        "before": {
                            "account_tier": "Standard",
                            "account_replication_type": "LRS"
                        },
                        "after": {
                            "account_tier": "Standard",
                            "account_replication_type": "GRS"
                        }
                    }
                },
                # GCP resources
                {
                    "address": "google_compute_instance.database",
                    "mode": "managed",
                    "type": "google_compute_instance",
                    "name": "database",
                    "provider_name": "registry.terraform.io/hashicorp/google",
                    "change": {
                        "actions": ["delete"],
                        "before": {
                            "name": "db-instance",
                            "machine_type": "n1-standard-1",
                            "zone": "us-central1-a",
                            "labels": {
                                "environment": "staging",
                                "provider": "gcp"
                            }
                        },
                        "after": None
                    }
                },
                # Replacement (create + delete)
                {
                    "address": "aws_rds_instance.main",
                    "mode": "managed",
                    "type": "aws_rds_instance",
                    "name": "main",
                    "provider_name": "registry.terraform.io/hashicorp/aws",
                    "change": {
                        "actions": ["create", "delete"],
                        "before": {
                            "engine": "mysql",
                            "engine_version": "5.7",
                            "instance_class": "db.t3.micro"
                        },
                        "after": {
                            "engine": "mysql",
                            "engine_version": "8.0",
                            "instance_class": "db.t3.small"
                        }
                    }
                }
            ]
        }
    
    @staticmethod
    def get_large_plan() -> Dict[str, Any]:
        """Get large Terraform plan with many resources for performance testing"""
        base_plan = {
            "terraform_version": "1.6.0",
            "format_version": "1.2",
            "resource_changes": []
        }
        
        # Generate 100 resources across different providers
        providers = [
            ("aws", ["aws_instance", "aws_s3_bucket", "aws_security_group", "aws_rds_instance"]),
            ("azure", ["azurerm_virtual_machine", "azurerm_storage_account", "azurerm_network_security_group"]),
            ("gcp", ["google_compute_instance", "google_storage_bucket", "google_compute_firewall"])
        ]
        
        actions = ["create", "update", "delete"]
        
        for i in range(100):
            provider_name, resource_types = providers[i % len(providers)]
            resource_type = resource_types[i % len(resource_types)]
            action = actions[i % len(actions)]
            
            resource_change = {
                "address": f"{resource_type}.resource_{i}",
                "mode": "managed",
                "type": resource_type,
                "name": f"resource_{i}",
                "provider_name": f"registry.terraform.io/hashicorp/{provider_name}",
                "change": {
                    "actions": [action],
                    "before": {"id": f"old-{i}"} if action in ["update", "delete"] else None,
                    "after": {"id": f"new-{i}", "name": f"resource-{i}"} if action in ["create", "update"] else None
                }
            }
            
            base_plan["resource_changes"].append(resource_change)
        
        return base_plan
    
    @staticmethod
    def get_security_focused_plan() -> Dict[str, Any]:
        """Get plan with security-related resources for security analysis testing"""
        return {
            "terraform_version": "1.6.0",
            "format_version": "1.2",
            "resource_changes": [
                # Security groups with risky configurations
                {
                    "address": "aws_security_group.risky",
                    "mode": "managed",
                    "type": "aws_security_group",
                    "name": "risky",
                    "provider_name": "registry.terraform.io/hashicorp/aws",
                    "change": {
                        "actions": ["create"],
                        "before": None,
                        "after": {
                            "name": "risky-sg",
                            "ingress": [
                                {
                                    "from_port": 22,
                                    "to_port": 22,
                                    "protocol": "tcp",
                                    "cidr_blocks": ["0.0.0.0/0"]  # Risky: SSH open to world
                                },
                                {
                                    "from_port": 3389,
                                    "to_port": 3389,
                                    "protocol": "tcp",
                                    "cidr_blocks": ["0.0.0.0/0"]  # Risky: RDP open to world
                                }
                            ]
                        }
                    }
                },
                # IAM policy with broad permissions
                {
                    "address": "aws_iam_policy.admin",
                    "mode": "managed",
                    "type": "aws_iam_policy",
                    "name": "admin",
                    "provider_name": "registry.terraform.io/hashicorp/aws",
                    "change": {
                        "actions": ["create"],
                        "before": None,
                        "after": {
                            "name": "admin-policy",
                            "policy": json.dumps({
                                "Version": "2012-10-17",
                                "Statement": [
                                    {
                                        "Effect": "Allow",
                                        "Action": "*",  # Risky: Full admin access
                                        "Resource": "*"
                                    }
                                ]
                            })
                        }
                    }
                },
                # S3 bucket with public access
                {
                    "address": "aws_s3_bucket_public_access_block.public",
                    "mode": "managed",
                    "type": "aws_s3_bucket_public_access_block",
                    "name": "public",
                    "provider_name": "registry.terraform.io/hashicorp/aws",
                    "change": {
                        "actions": ["update"],
                        "before": {
                            "block_public_acls": True,
                            "block_public_policy": True
                        },
                        "after": {
                            "block_public_acls": False,  # Risky: Allowing public ACLs
                            "block_public_policy": False  # Risky: Allowing public policies
                        }
                    }
                },
                # Database without encryption
                {
                    "address": "aws_rds_instance.unencrypted",
                    "mode": "managed",
                    "type": "aws_rds_instance",
                    "name": "unencrypted",
                    "provider_name": "registry.terraform.io/hashicorp/aws",
                    "change": {
                        "actions": ["create"],
                        "before": None,
                        "after": {
                            "identifier": "unencrypted-db",
                            "engine": "mysql",
                            "storage_encrypted": False,  # Risky: No encryption
                            "publicly_accessible": True  # Risky: Publicly accessible
                        }
                    }
                }
            ]
        }
    
    @staticmethod
    def get_invalid_plan() -> Dict[str, Any]:
        """Get invalid plan for error handling testing"""
        return {
            "terraform_version": "1.0.0",
            # Missing format_version
            "resource_changes": "not_a_list"  # Invalid type
        }
    
    @staticmethod
    def get_empty_plan() -> Dict[str, Any]:
        """Get empty plan with no changes"""
        return {
            "terraform_version": "1.6.0",
            "format_version": "1.2",
            "resource_changes": []
        }
    
    @staticmethod
    def get_plan_with_dependencies() -> Dict[str, Any]:
        """Get plan with resource dependencies for dependency analysis testing"""
        return {
            "terraform_version": "1.6.0",
            "format_version": "1.2",
            "resource_changes": [
                # VPC (base dependency)
                {
                    "address": "aws_vpc.main",
                    "mode": "managed",
                    "type": "aws_vpc",
                    "name": "main",
                    "provider_name": "registry.terraform.io/hashicorp/aws",
                    "change": {
                        "actions": ["create"],
                        "before": None,
                        "after": {
                            "cidr_block": "10.0.0.0/16",
                            "tags": {"Name": "main-vpc"}
                        }
                    }
                },
                # Subnet (depends on VPC)
                {
                    "address": "aws_subnet.public",
                    "mode": "managed",
                    "type": "aws_subnet",
                    "name": "public",
                    "provider_name": "registry.terraform.io/hashicorp/aws",
                    "change": {
                        "actions": ["create"],
                        "before": None,
                        "after": {
                            "vpc_id": "${aws_vpc.main.id}",
                            "cidr_block": "10.0.1.0/24",
                            "availability_zone": "us-west-2a"
                        }
                    }
                },
                # Security Group (depends on VPC)
                {
                    "address": "aws_security_group.web",
                    "mode": "managed",
                    "type": "aws_security_group",
                    "name": "web",
                    "provider_name": "registry.terraform.io/hashicorp/aws",
                    "change": {
                        "actions": ["create"],
                        "before": None,
                        "after": {
                            "vpc_id": "${aws_vpc.main.id}",
                            "name": "web-sg"
                        }
                    }
                },
                # Instance (depends on subnet and security group)
                {
                    "address": "aws_instance.web",
                    "mode": "managed",
                    "type": "aws_instance",
                    "name": "web",
                    "provider_name": "registry.terraform.io/hashicorp/aws",
                    "change": {
                        "actions": ["create"],
                        "before": None,
                        "after": {
                            "ami": "ami-12345678",
                            "instance_type": "t3.micro",
                            "subnet_id": "${aws_subnet.public.id}",
                            "vpc_security_group_ids": ["${aws_security_group.web.id}"]
                        }
                    }
                }
            ]
        }