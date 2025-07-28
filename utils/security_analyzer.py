"""
Security Analysis Module

Provides security-focused analysis for Terraform plan changes including:
- Security-related resource detection and highlighting
- Security risk scoring and recommendations
- Compliance checks for common security frameworks
"""

from typing import Dict, List, Any, Optional, Set
from collections import defaultdict
import re


class SecurityAnalyzer:
    """Analyzes Terraform plans for security-related resources and risks"""
    
    def __init__(self):
        """Initialize the security analyzer with security patterns and frameworks"""
        
        # Security-critical resource types with their risk weights
        self.security_resource_types = {
            # Identity and Access Management (Critical)
            'aws_iam_role': {'weight': 10, 'category': 'identity', 'description': 'IAM role with permissions'},
            'aws_iam_policy': {'weight': 10, 'category': 'identity', 'description': 'IAM policy defining permissions'},
            'aws_iam_user': {'weight': 9, 'category': 'identity', 'description': 'IAM user account'},
            'aws_iam_group': {'weight': 8, 'category': 'identity', 'description': 'IAM group for user management'},
            'aws_iam_role_policy_attachment': {'weight': 9, 'category': 'identity', 'description': 'Policy attachment to role'},
            'aws_iam_access_key': {'weight': 10, 'category': 'identity', 'description': 'Access key for programmatic access'},
            
            # Network Security (Critical)
            'aws_security_group': {'weight': 10, 'category': 'network', 'description': 'Network security group rules'},
            'aws_security_group_rule': {'weight': 9, 'category': 'network', 'description': 'Individual security group rule'},
            'aws_network_acl': {'weight': 9, 'category': 'network', 'description': 'Network access control list'},
            'aws_network_acl_rule': {'weight': 8, 'category': 'network', 'description': 'Network ACL rule'},
            'aws_vpc': {'weight': 8, 'category': 'network', 'description': 'Virtual private cloud'},
            'aws_vpc_endpoint': {'weight': 7, 'category': 'network', 'description': 'VPC endpoint for service access'},
            
            # Encryption and Key Management (Critical)
            'aws_kms_key': {'weight': 10, 'category': 'encryption', 'description': 'KMS encryption key'},
            'aws_kms_alias': {'weight': 8, 'category': 'encryption', 'description': 'KMS key alias'},
            'aws_kms_grant': {'weight': 9, 'category': 'encryption', 'description': 'KMS key usage grant'},
            
            # Storage Security (High)
            'aws_s3_bucket': {'weight': 8, 'category': 'storage', 'description': 'S3 storage bucket'},
            'aws_s3_bucket_policy': {'weight': 10, 'category': 'storage', 'description': 'S3 bucket access policy'},
            'aws_s3_bucket_acl': {'weight': 9, 'category': 'storage', 'description': 'S3 bucket access control list'},
            'aws_s3_bucket_public_access_block': {'weight': 9, 'category': 'storage', 'description': 'S3 public access controls'},
            'aws_s3_bucket_encryption': {'weight': 8, 'category': 'storage', 'description': 'S3 bucket encryption settings'},
            
            # Database Security (High)
            'aws_rds_instance': {'weight': 8, 'category': 'database', 'description': 'RDS database instance'},
            'aws_rds_cluster': {'weight': 8, 'category': 'database', 'description': 'RDS database cluster'},
            'aws_db_subnet_group': {'weight': 7, 'category': 'database', 'description': 'Database subnet group'},
            'aws_db_parameter_group': {'weight': 7, 'category': 'database', 'description': 'Database parameter group'},
            
            # Secrets Management (Critical)
            'aws_secretsmanager_secret': {'weight': 10, 'category': 'secrets', 'description': 'Secrets Manager secret'},
            'aws_secretsmanager_secret_version': {'weight': 9, 'category': 'secrets', 'description': 'Secret version'},
            'aws_ssm_parameter': {'weight': 8, 'category': 'secrets', 'description': 'Systems Manager parameter'},
            
            # Monitoring and Logging (Medium-High)
            'aws_cloudtrail': {'weight': 8, 'category': 'monitoring', 'description': 'CloudTrail audit logging'},
            'aws_config_configuration_recorder': {'weight': 7, 'category': 'monitoring', 'description': 'Config service recorder'},
            'aws_guardduty_detector': {'weight': 7, 'category': 'monitoring', 'description': 'GuardDuty threat detection'},
            'aws_cloudwatch_log_group': {'weight': 6, 'category': 'monitoring', 'description': 'CloudWatch log group'},
            
            # Certificate Management (High)
            'aws_acm_certificate': {'weight': 8, 'category': 'certificates', 'description': 'SSL/TLS certificate'},
            'aws_acm_certificate_validation': {'weight': 7, 'category': 'certificates', 'description': 'Certificate validation'},
        }
        
        # Security-sensitive configuration patterns
        self.security_patterns = {
            'open_to_world': {
                'pattern': r'0\.0\.0\.0/0',
                'severity': 'critical',
                'description': 'Resource allows access from anywhere on the internet'
            },
            'admin_access': {
                'pattern': r'(\*|Administrator|admin|root)',
                'severity': 'high',
                'description': 'Resource grants administrative or wildcard permissions'
            },
            'unencrypted': {
                'pattern': r'(encrypt|encryption).*false',
                'severity': 'high',
                'description': 'Resource has encryption disabled'
            },
            'public_access': {
                'pattern': r'(public|Public)',
                'severity': 'medium',
                'description': 'Resource may allow public access'
            },
            'sensitive_ports': {
                'pattern': r'(22|3389|1433|3306|5432|6379|27017)',
                'severity': 'high',
                'description': 'Resource exposes sensitive ports (SSH, RDP, databases)'
            }
        }
        
        # Compliance frameworks and their requirements
        self.compliance_frameworks = {
            'SOC2': {
                'name': 'SOC 2 Type II',
                'requirements': {
                    'encryption_at_rest': 'Data must be encrypted at rest',
                    'encryption_in_transit': 'Data must be encrypted in transit',
                    'access_logging': 'Access must be logged and monitored',
                    'least_privilege': 'Access should follow principle of least privilege',
                    'network_segmentation': 'Network should be properly segmented'
                }
            },
            'PCI_DSS': {
                'name': 'PCI DSS',
                'requirements': {
                    'network_security': 'Install and maintain firewall configuration',
                    'encryption': 'Protect stored cardholder data with encryption',
                    'access_control': 'Restrict access by business need-to-know',
                    'monitoring': 'Regularly monitor and test networks',
                    'vulnerability_management': 'Maintain vulnerability management program'
                }
            },
            'HIPAA': {
                'name': 'HIPAA',
                'requirements': {
                    'access_control': 'Implement access control for PHI',
                    'audit_controls': 'Implement audit controls',
                    'integrity': 'Implement integrity controls for PHI',
                    'transmission_security': 'Implement transmission security'
                }
            },
            'GDPR': {
                'name': 'GDPR',
                'requirements': {
                    'data_protection': 'Implement appropriate technical measures',
                    'encryption': 'Use encryption where appropriate',
                    'access_control': 'Implement access controls',
                    'data_minimization': 'Process only necessary data'
                }
            }
        }
    
    def analyze_security_resources(self, resource_changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze resource changes for security-related resources and risks
        
        Args:
            resource_changes: List of resource changes from Terraform plan
            
        Returns:
            Dictionary containing security analysis results
        """
        security_resources = []
        security_risks = []
        category_breakdown = defaultdict(int)
        total_security_score = 0
        
        for change in resource_changes:
            resource_type = change.get('type', '')
            resource_address = change.get('address', '')
            actions = change.get('change', {}).get('actions', [])
            
            # Check if this is a security-related resource
            if self._is_security_resource(resource_type):
                security_info = self.security_resource_types.get(resource_type, {})
                category = security_info.get('category', 'other')
                weight = security_info.get('weight', 5)
                description = security_info.get('description', 'Security-related resource')
                
                # Calculate risk score based on action and resource type
                risk_score = self._calculate_security_risk_score(change, weight)
                total_security_score += risk_score
                
                security_resource = {
                    'address': resource_address,
                    'type': resource_type,
                    'category': category,
                    'actions': actions,
                    'risk_score': risk_score,
                    'weight': weight,
                    'description': description,
                    'security_issues': self._identify_security_issues(change)
                }
                
                security_resources.append(security_resource)
                category_breakdown[category] += 1
                
                # Check for high-risk security issues
                if risk_score >= 8:
                    security_risks.append({
                        'resource': resource_address,
                        'type': resource_type,
                        'risk': 'High security risk resource',
                        'recommendation': self._get_security_recommendation(resource_type, actions)
                    })
        
        # Calculate overall security score
        if security_resources:
            avg_security_score = total_security_score / len(security_resources)
            security_level = self._get_security_level(avg_security_score)
        else:
            avg_security_score = 0
            security_level = 'Low'
        
        return {
            'security_resources': security_resources,
            'security_risks': security_risks,
            'category_breakdown': dict(category_breakdown),
            'total_security_resources': len(security_resources),
            'avg_security_score': round(avg_security_score, 1),
            'security_level': security_level,
            'recommendations': self._generate_security_recommendations(security_resources, security_risks)
        }
    
    def check_compliance(self, resource_changes: List[Dict[str, Any]], 
                        frameworks: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Check resource changes against compliance frameworks
        
        Args:
            resource_changes: List of resource changes from Terraform plan
            frameworks: List of framework names to check (default: all)
            
        Returns:
            Dictionary containing compliance check results
        """
        if frameworks is None:
            frameworks = list(self.compliance_frameworks.keys())
        
        compliance_results = {}
        
        for framework in frameworks:
            if framework not in self.compliance_frameworks:
                continue
                
            framework_info = self.compliance_frameworks[framework]
            compliance_results[framework] = {
                'name': framework_info['name'],
                'checks': [],
                'passed': 0,
                'failed': 0,
                'warnings': 0,
                'score': 0
            }
            
            # Perform framework-specific checks
            checks = self._perform_compliance_checks(resource_changes, framework)
            compliance_results[framework]['checks'] = checks
            
            # Calculate compliance score
            for check in checks:
                if check['status'] == 'pass':
                    compliance_results[framework]['passed'] += 1
                elif check['status'] == 'fail':
                    compliance_results[framework]['failed'] += 1
                else:
                    compliance_results[framework]['warnings'] += 1
            
            total_checks = len(checks)
            if total_checks > 0:
                score = (compliance_results[framework]['passed'] / total_checks) * 100
                compliance_results[framework]['score'] = round(score, 1)
        
        return compliance_results
    
    def get_security_dashboard_data(self, resource_changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get comprehensive security dashboard data
        
        Args:
            resource_changes: List of resource changes from Terraform plan
            
        Returns:
            Dictionary containing all security dashboard data
        """
        security_analysis = self.analyze_security_resources(resource_changes)
        compliance_results = self.check_compliance(resource_changes)
        
        # Calculate overall security posture
        security_score = security_analysis['avg_security_score']
        compliance_scores = [result['score'] for result in compliance_results.values()]
        overall_compliance_score = sum(compliance_scores) / len(compliance_scores) if compliance_scores else 0
        
        # Combine scores for overall security posture
        overall_security_score = (security_score * 10 + overall_compliance_score) / 2
        overall_security_level = self._get_security_level(overall_security_score / 10)
        
        return {
            'security_analysis': security_analysis,
            'compliance_results': compliance_results,
            'overall_security_score': round(overall_security_score, 1),
            'overall_security_level': overall_security_level,
            'total_resources_analyzed': len(resource_changes),
            'security_resource_percentage': round(
                (security_analysis['total_security_resources'] / len(resource_changes)) * 100, 1
            ) if resource_changes else 0
        }
    
    def _is_security_resource(self, resource_type: str) -> bool:
        """Check if a resource type is security-related"""
        return resource_type in self.security_resource_types
    
    def _calculate_security_risk_score(self, change: Dict[str, Any], base_weight: int) -> float:
        """Calculate security risk score for a resource change"""
        actions = change.get('change', {}).get('actions', [])
        
        # Action multipliers for security risk
        action_multipliers = {
            'create': 1.0,  # Creating new security resources
            'update': 1.5,  # Updating security configs can be risky
            'delete': 2.0   # Deleting security resources is high risk
        }
        
        # Get the highest risk action
        max_multiplier = max([action_multipliers.get(action, 1.0) for action in actions])
        
        # Base score from resource weight
        base_score = base_weight / 10.0  # Normalize to 0-1 scale
        
        # Apply action multiplier
        risk_score = min(10.0, base_score * 10 * max_multiplier)
        
        # Check for additional security issues
        security_issues = self._identify_security_issues(change)
        if security_issues:
            risk_score += len(security_issues) * 0.5  # Add 0.5 per security issue
        
        return min(10.0, risk_score)
    
    def _identify_security_issues(self, change: Dict[str, Any]) -> List[Dict[str, str]]:
        """Identify specific security issues in a resource change"""
        issues = []
        
        # Get the resource configuration
        after_config = change.get('change', {}).get('after', {})
        if not isinstance(after_config, dict):
            return issues
        
        # Convert config to string for pattern matching
        config_str = str(after_config).lower()
        
        # Check for security patterns
        for pattern_name, pattern_info in self.security_patterns.items():
            if re.search(pattern_info['pattern'], config_str, re.IGNORECASE):
                issues.append({
                    'type': pattern_name,
                    'severity': pattern_info['severity'],
                    'description': pattern_info['description']
                })
        
        return issues
    
    def _get_security_level(self, score: float) -> str:
        """Convert numeric security score to level"""
        if score >= 8:
            return 'Critical'
        elif score >= 6:
            return 'High'
        elif score >= 4:
            return 'Medium'
        else:
            return 'Low'
    
    def _get_security_recommendation(self, resource_type: str, actions: List[str]) -> str:
        """Get security recommendation for a resource type and actions"""
        recommendations = {
            'aws_iam_role': 'Review role permissions and ensure principle of least privilege',
            'aws_iam_policy': 'Validate policy permissions and avoid wildcard actions',
            'aws_security_group': 'Restrict inbound rules and avoid 0.0.0.0/0 access',
            'aws_s3_bucket_policy': 'Review bucket policy for public access restrictions',
            'aws_kms_key': 'Ensure proper key rotation and access policies',
            'aws_secretsmanager_secret': 'Verify secret access permissions and rotation settings'
        }
        
        base_recommendation = recommendations.get(resource_type, 'Review security configuration')
        
        if 'delete' in actions:
            return f"{base_recommendation}. CAUTION: Resource is being deleted - ensure no dependencies exist."
        elif 'update' in actions:
            return f"{base_recommendation}. Verify changes don't weaken security posture."
        else:
            return base_recommendation
    
    def _generate_security_recommendations(self, security_resources: List[Dict[str, Any]], 
                                         security_risks: List[Dict[str, Any]]) -> List[str]:
        """Generate overall security recommendations"""
        recommendations = []
        
        if not security_resources:
            recommendations.append("✅ No security-critical resources detected in this plan")
            return recommendations
        
        # High-level recommendations based on analysis
        high_risk_count = len([r for r in security_resources if r['risk_score'] >= 8])
        if high_risk_count > 0:
            recommendations.append(f"🔴 {high_risk_count} high-risk security resources require immediate attention")
        
        # Category-specific recommendations
        categories = set(r['category'] for r in security_resources)
        if 'identity' in categories:
            recommendations.append("🔐 IAM changes detected - verify principle of least privilege")
        if 'network' in categories:
            recommendations.append("🌐 Network security changes - review firewall rules and access controls")
        if 'encryption' in categories:
            recommendations.append("🔒 Encryption resources modified - ensure key management best practices")
        if 'storage' in categories:
            recommendations.append("💾 Storage security changes - verify access policies and encryption")
        
        # Action-based recommendations
        delete_actions = [r for r in security_resources if 'delete' in r['actions']]
        if delete_actions:
            recommendations.append(f"⚠️ {len(delete_actions)} security resources being deleted - ensure no security gaps")
        
        return recommendations
    
    def _perform_compliance_checks(self, resource_changes: List[Dict[str, Any]], 
                                 framework: str) -> List[Dict[str, Any]]:
        """Perform compliance checks for a specific framework"""
        checks = []
        
        if framework == 'SOC2':
            checks.extend(self._check_soc2_compliance(resource_changes))
        elif framework == 'PCI_DSS':
            checks.extend(self._check_pci_compliance(resource_changes))
        elif framework == 'HIPAA':
            checks.extend(self._check_hipaa_compliance(resource_changes))
        elif framework == 'GDPR':
            checks.extend(self._check_gdpr_compliance(resource_changes))
        
        return checks
    
    def _check_soc2_compliance(self, resource_changes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check SOC 2 compliance requirements"""
        checks = []
        
        # Check for encryption at rest
        encryption_resources = [r for r in resource_changes 
                              if any(enc in r.get('type', '') for enc in ['kms', 'encryption'])]
        checks.append({
            'requirement': 'Encryption at Rest',
            'status': 'pass' if encryption_resources else 'warning',
            'description': 'Encryption resources found' if encryption_resources else 'No encryption resources detected',
            'resources': [r.get('address', '') for r in encryption_resources]
        })
        
        # Check for access logging
        logging_resources = [r for r in resource_changes 
                           if any(log in r.get('type', '') for log in ['cloudtrail', 'log_group', 'config'])]
        checks.append({
            'requirement': 'Access Logging',
            'status': 'pass' if logging_resources else 'warning',
            'description': 'Logging resources found' if logging_resources else 'No logging resources detected',
            'resources': [r.get('address', '') for r in logging_resources]
        })
        
        return checks
    
    def _check_pci_compliance(self, resource_changes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check PCI DSS compliance requirements"""
        checks = []
        
        # Check for network security
        network_security = [r for r in resource_changes 
                          if 'security_group' in r.get('type', '')]
        checks.append({
            'requirement': 'Network Security',
            'status': 'pass' if network_security else 'warning',
            'description': 'Security groups found' if network_security else 'No security groups detected',
            'resources': [r.get('address', '') for r in network_security]
        })
        
        return checks
    
    def _check_hipaa_compliance(self, resource_changes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check HIPAA compliance requirements"""
        checks = []
        
        # Check for access control
        iam_resources = [r for r in resource_changes if 'iam_' in r.get('type', '')]
        checks.append({
            'requirement': 'Access Control',
            'status': 'pass' if iam_resources else 'warning',
            'description': 'IAM resources found' if iam_resources else 'No IAM resources detected',
            'resources': [r.get('address', '') for r in iam_resources]
        })
        
        return checks
    
    def _check_gdpr_compliance(self, resource_changes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check GDPR compliance requirements"""
        checks = []
        
        # Check for data protection measures
        protection_resources = [r for r in resource_changes 
                              if any(prot in r.get('type', '') for prot in ['kms', 'encryption', 'iam_'])]
        checks.append({
            'requirement': 'Data Protection',
            'status': 'pass' if protection_resources else 'warning',
            'description': 'Data protection resources found' if protection_resources else 'No data protection resources detected',
            'resources': [r.get('address', '') for r in protection_resources]
        })
        
        return checks