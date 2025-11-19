#!/usr/bin/env python3
"""
API Matching Tool
Matches frontend API calls with backend endpoints to identify discrepancies
"""

import csv
import json
import re
from urllib.parse import urlparse

class APIMatchingTool:
    def __init__(self, frontend_csv, backend_csv):
        self.frontend_calls = []
        self.backend_endpoints = []
        self.matches = []
        self.missing_backend = []
        self.mismatched_schema = []
        
        self.load_frontend_calls(frontend_csv)
        self.load_backend_endpoints(backend_csv)
        
    def load_frontend_calls(self, csv_file):
        """Load frontend API calls from CSV"""
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            self.frontend_calls = list(reader)
    
    def load_backend_endpoints(self, csv_file):
        """Load backend endpoints from CSV"""
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            self.backend_endpoints = list(reader)
    
    def normalize_path(self, path):
        """Normalize API paths for comparison"""
        # Remove leading/trailing slashes
        path = path.strip('/')
        
        # Handle API prefix
        if not path.startswith('api/v1/'):
            if path.startswith('/api/v1/'):
                path = path[1:]
            elif not path.startswith('api/'):
                path = f'api/v1/{path}'
        
        # Convert path parameters to consistent format
        path = re.sub(r'\{[^}]+\}', '{id}', path)
        path = re.sub(r'/\d+', '/{id}', path)
        
        return path
    
    def extract_method_from_call(self, call):
        """Extract HTTP method from frontend call"""
        method = call.get('method', 'unknown').upper()
        
        if method == 'UNKNOWN':
            # Try to infer from call type
            call_type = call.get('type', '')
            if 'get' in call_type.lower():
                method = 'GET'
            elif 'post' in call_type.lower():
                method = 'POST'
            elif 'put' in call_type.lower():
                method = 'PUT'
            elif 'delete' in call_type.lower():
                method = 'DELETE'
        
        return method
    
    def perform_matching(self):
        """Match frontend calls with backend endpoints"""
        for call in self.frontend_calls:
            if call['websocket_flag'] == 'True':
                continue  # Skip WebSocket calls for now
                
            frontend_path = self.normalize_path(call['endpoint'])
            frontend_method = self.extract_method_from_call(call)
            
            if frontend_path == 'unknown' or frontend_method == 'UNKNOWN':
                continue
            
            match_found = False
            
            for endpoint in self.backend_endpoints:
                backend_path = self.normalize_path(endpoint['path'])
                backend_method = endpoint['method']
                
                if frontend_path == backend_path and frontend_method == backend_method:
                    # Exact match found
                    match_info = {
                        'frontend_file': call['file'],
                        'frontend_line': call['line'],
                        'frontend_method': frontend_method,
                        'frontend_path': frontend_path,
                        'backend_path': backend_path,
                        'backend_method': backend_method,
                        'backend_file': endpoint['file_location'],
                        'status': 'matched',
                        'notes': 'Exact match found'
                    }
                    self.matches.append(match_info)
                    match_found = True
                    break
            
            if not match_found:
                # Check for similar paths (different method)
                similar_found = False
                for endpoint in self.backend_endpoints:
                    backend_path = self.normalize_path(endpoint['path'])
                    if frontend_path == backend_path:
                        mismatch_info = {
                            'frontend_file': call['file'],
                            'frontend_line': call['line'],
                            'frontend_method': frontend_method,
                            'frontend_path': frontend_path,
                            'backend_path': backend_path,
                            'backend_method': endpoint['method'],
                            'backend_file': endpoint['file_location'],
                            'status': 'method_mismatch',
                            'notes': f'Path exists but method mismatch: {frontend_method} vs {endpoint["method"]}'
                        }
                        self.mismatched_schema.append(mismatch_info)
                        similar_found = True
                        break
                
                if not similar_found:
                    missing_info = {
                        'frontend_file': call['file'],
                        'frontend_line': call['line'],
                        'frontend_method': frontend_method,
                        'frontend_path': frontend_path,
                        'backend_path': '',
                        'backend_method': '',
                        'backend_file': '',
                        'status': 'missing_backend',
                        'notes': 'No corresponding backend endpoint found'
                    }
                    self.missing_backend.append(missing_info)
    
    def save_mapping_report(self, output_file):
        """Save comprehensive mapping report"""
        all_mappings = self.matches + self.mismatched_schema + self.missing_backend
        
        fieldnames = ['frontend_file', 'frontend_line', 'frontend_method', 'frontend_path', 
                     'backend_path', 'backend_method', 'backend_file', 'status', 'notes']
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_mappings)
    
    def generate_summary(self):
        """Generate summary statistics"""
        total_calls = len(self.frontend_calls)
        matched = len(self.matches)
        missing = len(self.missing_backend)
        mismatched = len(self.mismatched_schema)
        
        return {
            'total_frontend_calls': total_calls,
            'matched_endpoints': matched,
            'missing_backend': missing,
            'method_mismatches': mismatched,
            'match_rate': f"{(matched / total_calls * 100):.1f}%" if total_calls > 0 else "0%"
        }

def main():
    frontend_csv = "/Users/macbook/Desktop/advakod/artifacts/frontend_api_calls.csv"
    backend_csv = "/Users/macbook/Desktop/advakod/artifacts/backend_endpoints.csv"
    
    matcher = APIMatchingTool(frontend_csv, backend_csv)
    matcher.perform_matching()
    
    # Save results
    matcher.save_mapping_report("/Users/macbook/Desktop/advakod/artifacts/mapping_report.csv")
    
    # Generate and save summary
    summary = matcher.generate_summary()
    with open("/Users/macbook/Desktop/advakod/artifacts/mapping_summary.json", 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("API Matching Complete!")
    print(f"Total frontend calls: {summary['total_frontend_calls']}")
    print(f"Matched endpoints: {summary['matched_endpoints']}")
    print(f"Missing backend: {summary['missing_backend']}")
    print(f"Method mismatches: {summary['method_mismatches']}")
    print(f"Match rate: {summary['match_rate']}")
    
    print("\nResults saved to:")
    print("- artifacts/mapping_report.csv")
    print("- artifacts/mapping_summary.json")

if __name__ == "__main__":
    main()