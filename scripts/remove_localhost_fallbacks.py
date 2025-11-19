#!/usr/bin/env python3
"""
Script to remove localhost fallback values from configuration files.
This ensures strict environment variable validation in production.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple


class LocalhostFallbackRemover:
    """Remove localhost fallback values from configuration files."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.changes_made = []
        self.errors = []
    
    def find_config_files(self) -> List[Path]:
        """Find configuration files that might contain localhost fallbacks."""
        config_patterns = [
            "**/*.py",
            "**/*.js", 
            "**/*.ts",
            "**/*.jsx",
            "**/*.tsx",
            "**/.env*",
            "**/config.*",
            "**/settings.*"
        ]
        
        exclude_patterns = [
            "**/node_modules/**",
            "**/venv/**",
            "**/__pycache__/**",
            "**/test/**",
            "**/*.test.*",
            "**/*.spec.*",
            "**/dist/**",
            "**/build/**"
        ]
        
        files = []
        for pattern in config_patterns:
            for file_path in self.project_root.glob(pattern):
                if file_path.is_file():
                    # Check if file should be excluded
                    should_exclude = False
                    for exclude_pattern in exclude_patterns:
                        if file_path.match(exclude_pattern):
                            should_exclude = True
                            break
                    
                    if not should_exclude:
                        files.append(file_path)
        
        return files
    
    def detect_localhost_fallbacks(self, content: str, file_path: Path) -> List[Tuple[int, str, str]]:
        """Detect localhost fallback patterns in file content."""
        fallback_patterns = [
            # Python patterns
            r'os\.getenv\(["\']([^"\']+)["\'],\s*["\'].*localhost.*["\']',
            r'getenv\(["\']([^"\']+)["\'],\s*["\'].*localhost.*["\']',
            r'environ\.get\(["\']([^"\']+)["\'],\s*["\'].*localhost.*["\']',
            r'config\.get\(["\']([^"\']+)["\'],\s*["\'].*localhost.*["\']',
            
            # JavaScript/TypeScript patterns
            r'process\.env\.([A-Z_]+)\s*\|\|\s*["\'].*localhost.*["\']',
            r'env\.([A-Z_]+)\s*\|\|\s*["\'].*localhost.*["\']',
            
            # Environment file patterns
            r'^([A-Z_]+)=.*localhost.*$',
            
            # General fallback patterns
            r'([A-Z_]+).*=.*localhost.*default',
            r'([A-Z_]+).*=.*default.*localhost',
            r'localhost.*\|\|',
            r'\|\|.*localhost'
        ]
        
        fallbacks = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for pattern in fallback_patterns:
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    # Skip comments
                    if re.match(r'^\s*[#//]', line.strip()):
                        continue
                    
                    # Skip development-specific lines
                    if re.search(r'development|dev|test|local', line, re.IGNORECASE):
                        continue
                    
                    fallbacks.append((line_num, line.strip(), match.group(0)))
        
        return fallbacks
    
    def fix_python_fallbacks(self, content: str) -> str:
        """Fix Python localhost fallbacks."""
        # Replace os.getenv with localhost fallbacks
        content = re.sub(
            r'os\.getenv\((["\'][^"\']+["\'])\s*,\s*["\'][^"\']*localhost[^"\']*["\']',
            r'os.getenv(\1)',
            content,
            flags=re.IGNORECASE
        )
        
        # Replace environ.get with localhost fallbacks
        content = re.sub(
            r'environ\.get\((["\'][^"\']+["\'])\s*,\s*["\'][^"\']*localhost[^"\']*["\']',
            r'environ.get(\1)',
            content,
            flags=re.IGNORECASE
        )
        
        # Add validation for required environment variables
        if 'os.getenv(' in content and 'localhost' in content.lower():
            # Add validation function if not present
            validation_code = '''
def validate_required_env_vars():
    """Validate that required environment variables are set."""
    required_vars = [
        'DATABASE_URL',
        'REDIS_URL', 
        'QDRANT_HOST',
        'CORS_ORIGINS'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Validate environment variables on import
validate_required_env_vars()
'''
            
            if 'validate_required_env_vars' not in content:
                # Add validation at the end of imports
                import_section = re.search(r'((?:^(?:import|from)\s+.*$\n?)+)', content, re.MULTILINE)
                if import_section:
                    content = content.replace(
                        import_section.group(1),
                        import_section.group(1) + validation_code
                    )
        
        return content
    
    def fix_javascript_fallbacks(self, content: str) -> str:
        """Fix JavaScript/TypeScript localhost fallbacks."""
        # Replace process.env fallbacks
        content = re.sub(
            r'process\.env\.([A-Z_]+)\s*\|\|\s*["\'][^"\']*localhost[^"\']*["\']',
            r'process.env.\1',
            content,
            flags=re.IGNORECASE
        )
        
        # Add environment validation
        if 'process.env' in content and 'localhost' in content.lower():
            validation_code = '''
// Validate required environment variables
const requiredEnvVars = [
  'REACT_APP_API_URL',
  'REACT_APP_WS_URL'
];

const missingVars = requiredEnvVars.filter(varName => !process.env[varName]);
if (missingVars.length > 0) {
  throw new Error(`Missing required environment variables: ${missingVars.join(', ')}`);
}
'''
            
            if 'requiredEnvVars' not in content:
                content = validation_code + '\n' + content
        
        return content
    
    def fix_env_file_fallbacks(self, content: str) -> str:
        """Fix environment file localhost fallbacks."""
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            # Skip comments
            if line.strip().startswith('#'):
                fixed_lines.append(line)
                continue
            
            # Remove localhost fallbacks from environment variables
            if '=' in line and 'localhost' in line.lower():
                # Check if it's a development-specific variable
                if re.search(r'dev|test|local', line, re.IGNORECASE):
                    fixed_lines.append(line)
                    continue
                
                # Remove the line or comment it out
                var_name = line.split('=')[0]
                fixed_lines.append(f'# {line}  # REMOVED: localhost fallback')
                fixed_lines.append(f'# {var_name}=  # SET THIS IN PRODUCTION')
            else:
                fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def process_file(self, file_path: Path) -> bool:
        """Process a single file to remove localhost fallbacks."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Detect fallbacks
            fallbacks = self.detect_localhost_fallbacks(original_content, file_path)
            if not fallbacks:
                return False
            
            print(f"🔧 Processing {file_path}")
            for line_num, line, match in fallbacks:
                print(f"   Line {line_num}: {match}")
            
            # Fix based on file type
            fixed_content = original_content
            
            if file_path.suffix == '.py':
                fixed_content = self.fix_python_fallbacks(fixed_content)
            elif file_path.suffix in ['.js', '.jsx', '.ts', '.tsx']:
                fixed_content = self.fix_javascript_fallbacks(fixed_content)
            elif '.env' in file_path.name:
                fixed_content = self.fix_env_file_fallbacks(fixed_content)
            
            # Write back if changes were made
            if fixed_content != original_content:
                # Create backup
                backup_path = file_path.with_suffix(file_path.suffix + '.backup')
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(original_content)
                
                # Write fixed content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                
                self.changes_made.append(str(file_path))
                print(f"   ✅ Fixed {file_path} (backup: {backup_path})")
                return True
            
            return False
            
        except Exception as e:
            error_msg = f"Error processing {file_path}: {e}"
            self.errors.append(error_msg)
            print(f"   ❌ {error_msg}")
            return False
    
    def run(self) -> bool:
        """Run the localhost fallback removal process."""
        print("🔍 Scanning for localhost fallback values...")
        
        config_files = self.find_config_files()
        print(f"Found {len(config_files)} configuration files to check")
        
        files_changed = 0
        for file_path in config_files:
            if self.process_file(file_path):
                files_changed += 1
        
        print(f"\n📊 Summary:")
        print(f"   Files scanned: {len(config_files)}")
        print(f"   Files changed: {files_changed}")
        print(f"   Errors: {len(self.errors)}")
        
        if self.errors:
            print(f"\n❌ Errors encountered:")
            for error in self.errors:
                print(f"   {error}")
        
        if files_changed > 0:
            print(f"\n✅ Successfully removed localhost fallbacks from {files_changed} files")
            print(f"   Changed files:")
            for file_path in self.changes_made:
                print(f"     - {file_path}")
            
            print(f"\n⚠️  Important:")
            print(f"   - Backup files created with .backup extension")
            print(f"   - Review changes before committing")
            print(f"   - Set proper environment variables in production")
            print(f"   - Test thoroughly after changes")
            
            return True
        else:
            print(f"\n✅ No localhost fallbacks found")
            return False


def main():
    """Main function."""
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = "."
    
    remover = LocalhostFallbackRemover(project_root)
    success = remover.run()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()