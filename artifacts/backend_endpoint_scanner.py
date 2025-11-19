#!/usr/bin/env python3
"""
Backend Endpoint Scanner
Scans FastAPI backend files to identify all endpoints and routes
"""

import os
import re
import json
import csv
from pathlib import Path

class BackendEndpointScanner:
    def __init__(self, backend_dir):
        self.backend_dir = Path(backend_dir)
        self.endpoints = []
        
    def scan_files(self):
        """Scan all Python files in the backend directory"""
        py_files = list(self.backend_dir.rglob("*.py"))
        
        for file_path in py_files:
            # Skip __pycache__ and other irrelevant directories
            if '__pycache__' in str(file_path) or 'migrations' in str(file_path):
                continue
                
            self.scan_file(file_path)
    
    def scan_file(self, file_path):
        """Scan a single file for FastAPI endpoints"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                
            # Patterns to match FastAPI endpoints
            patterns = {
                'router_method': r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
                'app_method': r'@app\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
                'websocket': r'@router\.websocket\(["\']([^"\']+)["\']',
                'include_router': r'include_router\([^,]+,\s*prefix=["\']([^"\']+)["\']'
            }
            
            current_function = None
            current_endpoint_info = None
            
            for line_num, line in enumerate(lines, 1):
                stripped_line = line.strip()
                
                # Check for endpoint decorators
                for pattern_name, pattern in patterns.items():
                    match = re.search(pattern, stripped_line)
                    if match:
                        if pattern_name == 'include_router':
                            # Handle router inclusion
                            prefix = match.group(1)
                            continue
                        else:
                            # Extract endpoint info
                            method = match.group(1).upper() if pattern_name != 'websocket' else 'WEBSOCKET'
                            path = match.group(2)
                            
                            current_endpoint_info = {
                                'file': str(file_path.relative_to(self.backend_dir)),
                                'line': line_num,
                                'method': method,
                                'path': path,
                                'function_name': 'unknown',
                                'request_schema': 'unknown',
                                'response_schema': 'unknown',
                                'auth_required': 'unknown',
                                'full_line': stripped_line
                            }
                            
                # Check for function definition after decorator
                if current_endpoint_info and (stripped_line.startswith('async def ') or stripped_line.startswith('def ')):
                    func_match = re.search(r'(async )?def ([^(]+)\(', stripped_line)
                    if func_match:
                        current_endpoint_info['function_name'] = func_match.group(2)
                        
                        # Check for authentication in function parameters
                        if 'current_user' in stripped_line or 'Depends(' in stripped_line:
                            current_endpoint_info['auth_required'] = 'Yes'
                        else:
                            current_endpoint_info['auth_required'] = 'No'
                        
                        # Look for Pydantic models in parameters
                        model_match = re.search(r'([A-Z][a-zA-Z]+):', stripped_line)
                        if model_match:
                            current_endpoint_info['request_schema'] = model_match.group(1)
                        
                        # Look for response model in decorator
                        response_match = re.search(r'response_model=([A-Z][a-zA-Z]+)', current_endpoint_info['full_line'])
                        if response_match:
                            current_endpoint_info['response_schema'] = response_match.group(1)
                        
                        self.endpoints.append(current_endpoint_info)
                        current_endpoint_info = None
                        
        except Exception as e:
            print(f"Error scanning {file_path}: {e}")
    
    def save_to_csv(self, output_file):
        """Save results to CSV file"""
        fieldnames = ['path', 'method', 'request_schema', 'response_schema', 'auth_required', 'file_location', 'function_name', 'line', 'full_line']
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for endpoint in self.endpoints:
                # Reorder fields to match CSV header
                csv_row = {
                    'path': endpoint['path'],
                    'method': endpoint['method'],
                    'request_schema': endpoint['request_schema'],
                    'response_schema': endpoint['response_schema'],
                    'auth_required': endpoint['auth_required'],
                    'file_location': endpoint['file'],
                    'function_name': endpoint['function_name'],
                    'line': endpoint['line'],
                    'full_line': endpoint['full_line']
                }
                writer.writerow(csv_row)
    
    def save_to_json(self, output_file):
        """Save results to JSON file"""
        with open(output_file, 'w', encoding='utf-8') as jsonfile:
            json.dump(self.endpoints, jsonfile, indent=2, ensure_ascii=False)

def main():
    backend_dir = "/Users/macbook/Desktop/advakod/backend"
    
    scanner = BackendEndpointScanner(backend_dir)
    scanner.scan_files()
    
    # Save results
    scanner.save_to_csv("/Users/macbook/Desktop/advakod/artifacts/backend_endpoints.csv")
    scanner.save_to_json("/Users/macbook/Desktop/advakod/artifacts/backend_endpoints.json")
    
    print(f"Scanned {len(scanner.endpoints)} endpoints")
    print("Results saved to:")
    print("- artifacts/backend_endpoints.csv")
    print("- artifacts/backend_endpoints.json")

if __name__ == "__main__":
    main()