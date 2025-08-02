"""
Test fixtures specifically for PDF generation testing

Provides comprehensive sample Terraform plan data with various scenarios
for testing PDF generation functionality.
"""

from typing import Dict, Any, List
from datetime import datetime


class PDFTestFixtures:
    """Test fixtures for PDF generation testing"""
    
    @staticmethod
    def get_minimal_pdf_data() -> Dict[str, Any]:
        """Get minimal data for basic PDF generation testing"""
        return {
            'summary': {
                'create': 0,
                'update': 0,
                'delete': 0,
                'no-op': 0,
                'total': 0
            },
            'risk_summary': {
                'level': 'Low',
                'score': 10,
                'risk_factors': []
            },
            'resource_changes': [],
            'resource_types': {},
            'plan_data': {
                'terraform_version': '1.5.0',
                'format_version': '1.2',
                'resource_changes': []
            }
        }
    
    @staticmethod
    def get_basic_pdf_data() -> Dict[str, Any]:
        """Get basic data for standard PDF generation testing"""
        return {
            'summary': {
                'create': 3,
                'update': 2,
                'delete': 1,
                'no-op': 5,
                'total': 11
            },
            'risk_summary': {
                'level': 'Medium',
                'score': 55,
                'risk_factors': [
                    'Resource deletion detected',
                    'Security group modifications'
                ]
            },
            'resource_changes': [
                {
                    'address': 'aws_instance.web_server',
                    'type': 'aws_instance',
                    'provider_name': 'registry.terraform.io/hashicorp/aws',
                    'change': {
                        'actions': ['create']
                    }
                },
                {
                    'address': 'aws_security_group.web_sg',
                    'type': 'aws_security_group',
                    'provider_name': 'registry.terraform.io/hashicorp/aws',
                    'change': {
                        'actions': ['update']
                    }
                },
                {
                    'address': 'aws_s3_bucket.old_bucket',
                    'type': 'aws_s3_bucket',
                    'provider_name': 'registry.terraform.io/hashicorp/aws',
                    'change': {
                        'actions': ['delete']
                    }
                }
            ],
            'resource_types': {
                'aws_instance': 1,
                'aws_security_group': 1,
                'aws_s3_bucket': 1
            },
            'plan_data': {
                'terraform_version': '1.5.0',
                'format_version': '1.2',
                'resource_changes': [
                    {
                        'address': 'aws_instance.web_server',
                        'type': 'aws_instance',
                        'change': {'actions': ['create']}
                    },
                    {
                        'address': 'aws_security_group.web_sg',
                        'type': 'aws_security_group',
                        'change': {'actions': ['update']}
                    },
                    {
                        'address': 'aws_s3_bucket.old_bucket',
                        'type': 'aws_s3_bucket',
                        'change': {'actions': ['delete']}
                    }
                ]
            }
        }
    
    @staticmethod
    def get_comprehensive_pdf_data() -> Dict[str, Any]:
        """Get comprehensive data for full-featured PDF generation testing"""
        return {
            'summary': {
                'create': 15,
                'update': 8,
                'delete': 3,
                'no-op': 12,
                'total': 38
            },
            'risk_summary': {
                'overall_risk': {
                    'level': 'High',
                    'score': 78,
                    'estimated_time': '45-60 minutes',
                    'high_risk_count': 5,
                    'risk_factors': [
                        'Critical resource deletion detected',
                        'Security group with open SSH access',
                        'IAM policy with broad permissions',
                        'Database without encryption',
                        'S3 bucket public access enabled'
                    ]
                }
            },
            'resource_changes': [
                # AWS resources
                {
                    'address': 'aws_instance.web_server_1',
                    'type': 'aws_instance',
                    'provider_name': 'registry.terraform.io/hashicorp/aws',
                    'change': {
                        'actions': ['create'],
                        'before': None,
                        'after': {
                            'instance_type': 't3.medium',
                            'ami': 'ami-12345678'
                        }
                    }
                },
                {
                    'address': 'aws_instance.web_server_2',
                    'type': 'aws_instance',
                    'provider_name': 'registry.terraform.io/hashicorp/aws',
                    'change': {
                        'actions': ['create'],
                        'before': None,
                        'after': {
                            'instance_type': 't3.large',
                            'ami': 'ami-87654321'
                        }
                    }
                },
                {
                    'address': 'aws_security_group.web_sg',
                    'type': 'aws_security_group',
                    'provider_name': 'registry.terraform.io/hashicorp/aws',
                    'change': {
                        'actions': ['update'],
                        'before': {
                            'ingress': [{'from_port': 80, 'to_port': 80}]
                        },
                        'after': {
                            'ingress': [
                                {'from_port': 80, 'to_port': 80},
                                {'from_port': 443, 'to_port': 443},
                                {'from_port': 22, 'to_port': 22, 'cidr_blocks': ['0.0.0.0/0']}
                            ]
                        }
                    }
                },
                {
                    'address': 'aws_rds_instance.database',
                    'type': 'aws_rds_instance',
                    'provider_name': 'registry.terraform.io/hashicorp/aws',
                    'change': {
                        'actions': ['delete'],
                        'before': {
                            'engine': 'mysql',
                            'instance_class': 'db.t3.micro',
                            'storage_encrypted': False
                        },
                        'after': None
                    }
                },
                {
                    'address': 'aws_s3_bucket.data_bucket',
                    'type': 'aws_s3_bucket',
                    'provider_name': 'registry.terraform.io/hashicorp/aws',
                    'change': {
                        'actions': ['update'],
                        'before': {
                            'versioning': [{'enabled': False}]
                        },
                        'after': {
                            'versioning': [{'enabled': True}]
                        }
                    }
                },
                # Azure resources
                {
                    'address': 'azurerm_virtual_machine.app_vm',
                    'type': 'azurerm_virtual_machine',
                    'provider_name': 'registry.terraform.io/hashicorp/azurerm',
                    'change': {
                        'actions': ['create'],
                        'before': None,
                        'after': {
                            'vm_size': 'Standard_B2s',
                            'location': 'East US'
                        }
                    }
                },
                {
                    'address': 'azurerm_storage_account.storage',
                    'type': 'azurerm_storage_account',
                    'provider_name': 'registry.terraform.io/hashicorp/azurerm',
                    'change': {
                        'actions': ['update'],
                        'before': {
                            'account_replication_type': 'LRS'
                        },
                        'after': {
                            'account_replication_type': 'GRS'
                        }
                    }
                },
                # GCP resources
                {
                    'address': 'google_compute_instance.worker',
                    'type': 'google_compute_instance',
                    'provider_name': 'registry.terraform.io/hashicorp/google',
                    'change': {
                        'actions': ['create'],
                        'before': None,
                        'after': {
                            'machine_type': 'n1-standard-2',
                            'zone': 'us-central1-a'
                        }
                    }
                },
                {
                    'address': 'google_storage_bucket.backup',
                    'type': 'google_storage_bucket',
                    'provider_name': 'registry.terraform.io/hashicorp/google',
                    'change': {
                        'actions': ['delete'],
                        'before': {
                            'location': 'US',
                            'storage_class': 'STANDARD'
                        },
                        'after': None
                    }
                }
            ],
            'resource_types': {
                'aws_instance': 2,
                'aws_security_group': 1,
                'aws_rds_instance': 1,
                'aws_s3_bucket': 1,
                'azurerm_virtual_machine': 1,
                'azurerm_storage_account': 1,
                'google_compute_instance': 1,
                'google_storage_bucket': 1
            },
            'plan_data': {
                'terraform_version': '1.6.0',
                'format_version': '1.2',
                'resource_changes': [
                    {'address': 'aws_instance.web_server_1', 'type': 'aws_instance'},
                    {'address': 'aws_instance.web_server_2', 'type': 'aws_instance'},
                    {'address': 'aws_security_group.web_sg', 'type': 'aws_security_group'},
                    {'address': 'aws_rds_instance.database', 'type': 'aws_rds_instance'},
                    {'address': 'aws_s3_bucket.data_bucket', 'type': 'aws_s3_bucket'},
                    {'address': 'azurerm_virtual_machine.app_vm', 'type': 'azurerm_virtual_machine'},
                    {'address': 'azurerm_storage_account.storage', 'type': 'azurerm_storage_account'},
                    {'address': 'google_compute_instance.worker', 'type': 'google_compute_instance'},
                    {'address': 'google_storage_bucket.backup', 'type': 'google_storage_bucket'}
                ]
            }
        }
    
    @staticmethod
    def get_large_dataset_pdf_data() -> Dict[str, Any]:
        """Get large dataset for performance testing PDF generation"""
        # Generate large dataset
        resource_changes = []
        resource_types = {}
        plan_resources = []
        
        providers = [
            ('aws', ['aws_instance', 'aws_s3_bucket', 'aws_security_group', 'aws_rds_instance']),
            ('azure', ['azurerm_virtual_machine', 'azurerm_storage_account', 'azurerm_network_security_group']),
            ('gcp', ['google_compute_instance', 'google_storage_bucket', 'google_compute_firewall'])
        ]
        
        actions = ['create', 'update', 'delete']
        create_count = update_count = delete_count = 0
        
        for i in range(200):  # Large dataset with 200 resources
            provider_name, resource_type_list = providers[i % len(providers)]
            resource_type = resource_type_list[i % len(resource_type_list)]
            action = actions[i % len(actions)]
            
            # Count actions
            if action == 'create':
                create_count += 1
            elif action == 'update':
                update_count += 1
            elif action == 'delete':
                delete_count += 1
            
            # Count resource types
            if resource_type not in resource_types:
                resource_types[resource_type] = 0
            resource_types[resource_type] += 1
            
            # Create resource change
            resource_change = {
                'address': f'{resource_type}.resource_{i}',
                'type': resource_type,
                'provider_name': f'registry.terraform.io/hashicorp/{provider_name}',
                'change': {
                    'actions': [action],
                    'before': {'id': f'old-{i}'} if action in ['update', 'delete'] else None,
                    'after': {'id': f'new-{i}', 'name': f'resource-{i}'} if action in ['create', 'update'] else None
                }
            }
            resource_changes.append(resource_change)
            
            # Add to plan resources
            plan_resources.append({
                'address': f'{resource_type}.resource_{i}',
                'type': resource_type
            })
        
        return {
            'summary': {
                'create': create_count,
                'update': update_count,
                'delete': delete_count,
                'no-op': 50,  # Add some no-op resources
                'total': create_count + update_count + delete_count + 50
            },
            'risk_summary': {
                'overall_risk': {
                    'level': 'Critical',
                    'score': 92,
                    'estimated_time': '2-3 hours',
                    'high_risk_count': 25,
                    'risk_factors': [
                        'Large number of resource changes',
                        'Multiple provider modifications',
                        'Critical resource deletions',
                        'Security-sensitive updates',
                        'Cross-region deployments'
                    ]
                }
            },
            'resource_changes': resource_changes,
            'resource_types': resource_types,
            'plan_data': {
                'terraform_version': '1.6.0',
                'format_version': '1.2',
                'resource_changes': plan_resources
            }
        }
    
    @staticmethod
    def get_security_focused_pdf_data() -> Dict[str, Any]:
        """Get security-focused data for security analysis PDF testing"""
        return {
            'summary': {
                'create': 4,
                'update': 3,
                'delete': 1,
                'no-op': 2,
                'total': 10
            },
            'risk_summary': {
                'overall_risk': {
                    'level': 'Critical',
                    'score': 95,
                    'estimated_time': '1-2 hours',
                    'high_risk_count': 8,
                    'risk_factors': [
                        'SSH access open to world (0.0.0.0/0)',
                        'RDP access open to world (0.0.0.0/0)',
                        'IAM policy with full admin access (*:*)',
                        'S3 bucket public access enabled',
                        'Database without encryption',
                        'Database publicly accessible',
                        'Security group allows all traffic',
                        'Root access permissions granted'
                    ]
                }
            },
            'resource_changes': [
                {
                    'address': 'aws_security_group.risky_ssh',
                    'type': 'aws_security_group',
                    'provider_name': 'registry.terraform.io/hashicorp/aws',
                    'change': {
                        'actions': ['create'],
                        'before': None,
                        'after': {
                            'name': 'risky-ssh-sg',
                            'ingress': [
                                {
                                    'from_port': 22,
                                    'to_port': 22,
                                    'protocol': 'tcp',
                                    'cidr_blocks': ['0.0.0.0/0']
                                }
                            ]
                        }
                    }
                },
                {
                    'address': 'aws_security_group.risky_rdp',
                    'type': 'aws_security_group',
                    'provider_name': 'registry.terraform.io/hashicorp/aws',
                    'change': {
                        'actions': ['create'],
                        'before': None,
                        'after': {
                            'name': 'risky-rdp-sg',
                            'ingress': [
                                {
                                    'from_port': 3389,
                                    'to_port': 3389,
                                    'protocol': 'tcp',
                                    'cidr_blocks': ['0.0.0.0/0']
                                }
                            ]
                        }
                    }
                },
                {
                    'address': 'aws_iam_policy.admin_policy',
                    'type': 'aws_iam_policy',
                    'provider_name': 'registry.terraform.io/hashicorp/aws',
                    'change': {
                        'actions': ['create'],
                        'before': None,
                        'after': {
                            'name': 'admin-policy',
                            'policy': '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"*","Resource":"*"}]}'
                        }
                    }
                },
                {
                    'address': 'aws_s3_bucket_public_access_block.public_bucket',
                    'type': 'aws_s3_bucket_public_access_block',
                    'provider_name': 'registry.terraform.io/hashicorp/aws',
                    'change': {
                        'actions': ['update'],
                        'before': {
                            'block_public_acls': True,
                            'block_public_policy': True,
                            'ignore_public_acls': True,
                            'restrict_public_buckets': True
                        },
                        'after': {
                            'block_public_acls': False,
                            'block_public_policy': False,
                            'ignore_public_acls': False,
                            'restrict_public_buckets': False
                        }
                    }
                },
                {
                    'address': 'aws_rds_instance.unencrypted_db',
                    'type': 'aws_rds_instance',
                    'provider_name': 'registry.terraform.io/hashicorp/aws',
                    'change': {
                        'actions': ['create'],
                        'before': None,
                        'after': {
                            'identifier': 'unencrypted-database',
                            'engine': 'mysql',
                            'storage_encrypted': False,
                            'publicly_accessible': True,
                            'skip_final_snapshot': True
                        }
                    }
                }
            ],
            'resource_types': {
                'aws_security_group': 2,
                'aws_iam_policy': 1,
                'aws_s3_bucket_public_access_block': 1,
                'aws_rds_instance': 1
            },
            'plan_data': {
                'terraform_version': '1.6.0',
                'format_version': '1.2',
                'resource_changes': [
                    {'address': 'aws_security_group.risky_ssh', 'type': 'aws_security_group'},
                    {'address': 'aws_security_group.risky_rdp', 'type': 'aws_security_group'},
                    {'address': 'aws_iam_policy.admin_policy', 'type': 'aws_iam_policy'},
                    {'address': 'aws_s3_bucket_public_access_block.public_bucket', 'type': 'aws_s3_bucket_public_access_block'},
                    {'address': 'aws_rds_instance.unencrypted_db', 'type': 'aws_rds_instance'}
                ]
            }
        }
    
    @staticmethod
    def get_edge_case_pdf_data() -> Dict[str, Any]:
        """Get edge case data for testing PDF generation robustness"""
        return {
            'summary': {
                'create': 1,
                'update': 0,
                'delete': 0,
                'no-op': 0,
                'total': 1
            },
            'risk_summary': {
                'level': 'Unknown',
                'score': 0,
                'risk_factors': []
            },
            'resource_changes': [
                {
                    'address': 'very_long_resource_name_that_might_cause_formatting_issues.extremely_long_resource_instance_name_for_testing_edge_cases',
                    'type': 'aws_instance_with_very_long_type_name',
                    'provider_name': 'registry.terraform.io/hashicorp/aws',
                    'change': {
                        'actions': ['create'],
                        'before': None,
                        'after': {
                            'very_long_attribute_name_for_testing': 'very_long_attribute_value_that_might_cause_wrapping_issues_in_pdf_generation',
                            'special_characters': 'Testing special chars: àáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ',
                            'unicode_test': '测试中文字符 🚀 ✅ ❌ ⚠️',
                            'json_data': '{"nested": {"deeply": {"nested": {"data": "value"}}}}'
                        }
                    }
                }
            ],
            'resource_types': {
                'aws_instance_with_very_long_type_name': 1
            },
            'plan_data': {
                'terraform_version': '1.6.0-beta1',
                'format_version': '1.2',
                'resource_changes': [
                    {
                        'address': 'very_long_resource_name_that_might_cause_formatting_issues.extremely_long_resource_instance_name_for_testing_edge_cases',
                        'type': 'aws_instance_with_very_long_type_name'
                    }
                ]
            }
        }
    
    @staticmethod
    def get_nested_risk_summary_data() -> Dict[str, Any]:
        """Get data with nested risk summary structure for testing different formats"""
        basic_data = PDFTestFixtures.get_basic_pdf_data()
        basic_data['risk_summary'] = {
            'overall_risk': {
                'level': 'High',
                'score': 82,
                'estimated_time': '60-90 minutes',
                'high_risk_count': 3,
                'risk_factors': [
                    'Critical infrastructure changes',
                    'Security policy modifications',
                    'Database configuration updates'
                ]
            },
            'detailed_analysis': {
                'security_risks': ['SSH open to world', 'Unencrypted storage'],
                'compliance_risks': ['PCI DSS violation', 'GDPR concern'],
                'operational_risks': ['Single point of failure', 'No backup strategy']
            }
        }
        return basic_data
    
    @staticmethod
    def get_flat_risk_summary_data() -> Dict[str, Any]:
        """Get data with flat risk summary structure for testing different formats"""
        basic_data = PDFTestFixtures.get_basic_pdf_data()
        basic_data['risk_summary'] = {
            'level': 'Medium',
            'score': 65,
            'risk_factors': [
                'Resource modifications detected',
                'Network security changes'
            ]
        }
        return basic_data