#!/usr/bin/env python3
"""
Frontend API Call Scanner
Scans frontend JavaScript files to identify all API calls and HTTP requests
"""

import os
import re
import json
import csv
from pathlib import Path

class FrontendAPIScanner:
    def __init__(self, frontend_dir):
        self.frontend_dir = Path(frontend_dir)
        self.api_calls = []
        
    def scan_files(self):
        """Scan all JavaScript files in the frontend directory"""
        js_files = list(self.frontend_dir.rglob("*.js")) + list(self.frontend_dir.rglob("*.jsx"))
        
        for file_path in js_files:
            # Skip node_modules and build directories
            if 'node_modules' in str(file_path) or 'build' in str(file_path):
                continue
                
            self.scan_file(file_path)
    
    def scan_file(self, file_path):
        """Scan a single file for API calls"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                
            # Patterns to match API calls
            patterns = {
                'axios_call': r'axios\.(get|post|put|delete|patch)\(',
                'fetch_call': r'fetch\(',
                'http_method': r'\.(get|post|put|delete|patch)\(',
                'axios_generic': r'axios\(',
                'getApiUrl': r'getApiUrl\([\'"]([^\'"]+)[\'"]',
                'websocket': r'new WebSocket\(|getWebSocketUrl\('
            }
            
            for line_num, line in enumerate(lines, 1):
                for pattern_name, pattern in patterns.items():
                    matches = re.finditer(pattern, line, re.IGNORECASE)
                    for match in matches:
                        self.extract_api_call_info(file_path, line_num, line, match, pattern_name)
        except Exception as e:
            print(f"Error scanning {file_path}: {e}")
                        
    def extract_api_call_info(self, file_path, line_num, line, match, pattern_type):
        """Extract API call information"""
        call_info = {
            'file': str(file_path.relative_to(self.frontend_dir)),
            'line': line_num,
            'type': pattern_type,
            'full_line': line.strip(),
            'method': 'unknown',
            'endpoint': 'unknown',
            'body_schema': 'unknown',
            'auth_type': 'unknown',
            'websocket_flag': False
        }
        
        # Extract method
        if pattern_type in ['axios_call', 'http_method']:
            method_match = re.search(r'\.(get|post|put|delete|patch)\(', line, re.IGNORECASE)
            if method_match:
                call_info['method'] = method_match.group(1).upper()
        
        # Extract endpoint URL
        url_patterns = [
            r'getApiUrl\([\'"]([^\'"]+)[\'"]',
            r'[\'"]([^\'"]*/api/[^\'"]*)[\'"]',
            r'[\'"]([^\'"]*/[^\'"]*)[\'"]'
        ]
        
        for url_pattern in url_patterns:
            url_match = re.search(url_pattern, line)
            if url_match:
                call_info['endpoint'] = url_match.group(1)
                break
        
        # Check for WebSocket
        if 'websocket' in pattern_type.lower() or 'WebSocket' in line:
            call_info['websocket_flag'] = True
        
        # Check for authentication
        if 'headers' in line and ('Authorization' in line or 'Bearer' in line):
            call_info['auth_type'] = 'Bearer'
        elif 'withCredentials' in line:
            call_info['auth_type'] = 'Cookie'
        
        # Try to extract body schema
        if call_info['method'] in ['POST', 'PUT', 'PATCH']:
            # Look for object literals in the same line or nearby lines
            body_match = re.search(r'\{[^}]*\}', line)
            if body_match:
                call_info['body_schema'] = body_match.group(0)
        
        self.api_calls.append(call_info)
    
    def save_to_csv(self, output_file):
        """Save results to CSV file"""
        fieldnames = ['file', 'line', 'method', 'endpoint', 'body_schema', 'expected_response_schema', 'auth_type', 'websocket_flag', 'type', 'full_line']
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for call in self.api_calls:
                # Add missing fields
                call['expected_response_schema'] = 'unknown'
                writer.writerow(call)
    
    def save_to_json(self, output_file):
        """Save results to JSON file"""
        with open(output_file, 'w', encoding='utf-8') as jsonfile:
            json.dump(self.api_calls, jsonfile, indent=2, ensure_ascii=False)

def main():
    frontend_dir = "/Users/macbook/Desktop/advakod/frontend/src"
    
    scanner = FrontendAPIScanner(frontend_dir)
    scanner.scan_files()
    
    # Save results
    scanner.save_to_csv("/Users/macbook/Desktop/advakod/artifacts/frontend_api_calls.csv")
    scanner.save_to_json("/Users/macbook/Desktop/advakod/artifacts/frontend_api_calls.json")
    
    print(f"Scanned {len(scanner.api_calls)} API calls")
    print("Results saved to:")
    print("- artifacts/frontend_api_calls.csv")
    print("- artifacts/frontend_api_calls.json")

if __name__ == "__main__":
    main()