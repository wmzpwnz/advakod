#!/usr/bin/env python3
"""
Integration Issues Analysis and Prioritization Tool
Analyzes mismatched endpoints and categorizes by severity
"""

import csv
import json
from collections import defaultdict

class IntegrationAnalyzer:
    def __init__(self, mapping_csv, frontend_csv, backend_csv):
        self.mapping_data = []
        self.frontend_calls = []
        self.backend_endpoints = []
        
        self.load_data(mapping_csv, frontend_csv, backend_csv)
        
        # Critical flows that must work
        self.critical_endpoints = {
            '/auth/login-email': 'Authentication login',
            '/auth/register': 'User registration', 
            '/auth/me': 'Get current user',
            '/chat/sessions': 'Chat session management',
            '/chat/voice-message': 'Voice message processing',
            '/admin/dashboard': 'Admin dashboard',
            '/admin/users': 'User management',
            '/admin/documents': 'Document management'
        }
        
        # LoRA/AI features
        self.ai_endpoints = {
            '/lora/training/start': 'LoRA training',
            '/lora/data/collect': 'Training data collection',
            '/canary-lora/': 'Canary releases'
        }
        
    def load_data(self, mapping_csv, frontend_csv, backend_csv):
        """Load all CSV data"""
        with open(mapping_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            self.mapping_data = list(reader)
            
        with open(frontend_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            self.frontend_calls = list(reader)
            
        with open(backend_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            self.backend_endpoints = list(reader)
    
    def get_priority(self, endpoint_path, status):
        """Determine priority based on endpoint and status"""
        # Critical flows
        for critical_path in self.critical_endpoints:
            if critical_path in endpoint_path:
                if status == 'missing_backend':
                    return 'CRITICAL'
                else:
                    return 'HIGH'
        
        # AI/LoRA features
        for ai_path in self.ai_endpoints:
            if ai_path in endpoint_path:
                return 'HIGH'
        
        # Admin features
        if '/admin/' in endpoint_path:
            return 'MEDIUM'
            
        # Optional features
        if any(x in endpoint_path for x in ['/notifications/', '/export/', '/webhook']):
            return 'LOW'
            
        return 'MEDIUM'
    
    def analyze_issues(self):
        """Analyze and categorize all integration issues"""
        issues = []
        
        # Group mapping data by issue type
        missing_backend = [row for row in self.mapping_data if row['status'] == 'missing_backend']
        method_mismatches = [row for row in self.mapping_data if row['status'] == 'method_mismatch']
        
        # Analyze missing backend endpoints
        for row in missing_backend:
            endpoint = row['frontend_path']
            priority = self.get_priority(endpoint, 'missing_backend')
            
            # Determine action
            if endpoint in ['api/v1/unknown']:
                action = 'investigate_frontend'
                notes = 'Frontend call pattern unclear, needs investigation'
            else:
                action = 'create_backend_endpoint'
                notes = f'Create missing backend endpoint: {row["frontend_method"]} {endpoint}'
            
            issues.append({
                'type': 'missing_backend',
                'priority': priority,
                'frontend_file': row['frontend_file'],
                'frontend_line': row['frontend_line'],
                'method': row['frontend_method'],
                'endpoint': endpoint,
                'action': action,
                'notes': notes,
                'effort': self.estimate_effort(action, endpoint)
            })
        
        # Analyze method mismatches
        for row in method_mismatches:
            endpoint = row['frontend_path']
            priority = self.get_priority(endpoint, 'method_mismatch')
            
            # Prefer fixing frontend unless backend logic is clearly wrong
            action = 'fix_frontend_method'
            notes = f'Change frontend {row["frontend_method"]} to {row["backend_method"]} for {endpoint}'
            
            issues.append({
                'type': 'method_mismatch',
                'priority': priority,
                'frontend_file': row['frontend_file'],
                'frontend_line': row['frontend_line'],
                'method': row['frontend_method'],
                'endpoint': endpoint,
                'action': action,
                'notes': notes,
                'effort': 'LOW'
            })
        
        return issues
    
    def estimate_effort(self, action, endpoint):
        """Estimate development effort"""
        if action == 'investigate_frontend':
            return 'LOW'
        elif action == 'fix_frontend_method':
            return 'LOW'
        elif action == 'create_backend_endpoint':
            # Complex endpoints need more work
            if any(x in endpoint for x in ['lora', 'training', 'canary', 'admin']):
                return 'HIGH'
            elif any(x in endpoint for x in ['auth', 'chat', 'documents']):
                return 'MEDIUM'
            else:
                return 'LOW'
        return 'MEDIUM'
    
    def generate_fix_tasks(self, issues):
        """Generate actionable fix tasks"""
        # Sort by priority and effort
        priority_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        effort_order = {'HIGH': 2, 'MEDIUM': 1, 'LOW': 0}
        
        sorted_issues = sorted(issues, key=lambda x: (
            priority_order[x['priority']], 
            effort_order[x['effort']]
        ))
        
        tasks = []
        for i, issue in enumerate(sorted_issues):
            task = {
                'task_id': f'FIX_{i+1:03d}',
                'severity': issue['priority'],
                'frontend_file': issue['frontend_file'],
                'line': issue['frontend_line'],
                'frontend_call': f"{issue['method']} {issue['endpoint']}",
                'backend_file': '',  # To be filled when backend exists
                'backend_endpoint': '',  # To be filled
                'recommended_action': issue['action'],
                'notes': issue['notes'],
                'effort_estimate': issue['effort']
            }
            tasks.append(task)
        
        return tasks
    
    def save_analysis_report(self, output_file):
        """Save comprehensive analysis report"""
        issues = self.analyze_issues()
        tasks = self.generate_fix_tasks(issues)
        
        # Statistics
        stats = {
            'total_issues': len(issues),
            'by_priority': {},
            'by_type': {},
            'by_effort': {}
        }
        
        for issue in issues:
            stats['by_priority'][issue['priority']] = stats['by_priority'].get(issue['priority'], 0) + 1
            stats['by_type'][issue['type']] = stats['by_type'].get(issue['type'], 0) + 1
            stats['by_effort'][issue['effort']] = stats['by_effort'].get(issue['effort'], 0) + 1
        
        # Save tasks CSV
        fieldnames = ['task_id', 'severity', 'frontend_file', 'line', 'frontend_call', 
                     'backend_file', 'backend_endpoint', 'recommended_action', 'notes', 'effort_estimate']
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(tasks)
        
        # Save analysis JSON
        analysis_file = output_file.replace('.csv', '_analysis.json')
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump({
                'statistics': stats,
                'issues': issues,
                'critical_flows': self.critical_endpoints,
                'ai_features': self.ai_endpoints
            }, f, indent=2, ensure_ascii=False)
        
        return stats, tasks

def main():
    analyzer = IntegrationAnalyzer(
        "/Users/macbook/Desktop/advakod/artifacts/mapping_report.csv",
        "/Users/macbook/Desktop/advakod/artifacts/frontend_api_calls.csv", 
        "/Users/macbook/Desktop/advakod/artifacts/backend_endpoints.csv"
    )
    
    stats, tasks = analyzer.save_analysis_report("/Users/macbook/Desktop/advakod/artifacts/fix_tasks.csv")
    
    print("Integration Analysis Complete!")
    print(f"Total issues found: {stats['total_issues']}")
    print("By Priority:")
    for priority, count in stats['by_priority'].items():
        print(f"  {priority}: {count}")
    print("By Type:")
    for issue_type, count in stats['by_type'].items():
        print(f"  {issue_type}: {count}")
    print("By Effort:")
    for effort, count in stats['by_effort'].items():
        print(f"  {effort}: {count}")
    
    print("\nResults saved to:")
    print("- artifacts/fix_tasks.csv")
    print("- artifacts/fix_tasks_analysis.json")

if __name__ == "__main__":
    main()