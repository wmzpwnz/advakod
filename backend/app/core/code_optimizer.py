"""
Сервис оптимизации кода и архитектуры
"""
import ast
import logging
import os
from typing import Dict, List, Any, Optional, Set
from pathlib import Path
import re


class CodeOptimizer:
    """Сервис оптимизации кода"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.duplicated_code = {}
        self.unused_imports = set()
        self.long_functions = []
        self.complex_functions = []
        self.todo_comments = []
    
    def analyze_codebase(self, root_path: str) -> Dict[str, Any]:
        """Анализирует кодовую базу на предмет оптимизации"""
        try:
            analysis_results = {
                "duplicated_code": self._find_duplicated_code(root_path),
                "unused_imports": self._find_unused_imports(root_path),
                "long_functions": self._find_long_functions(root_path),
                "complex_functions": self._find_complex_functions(root_path),
                "todo_comments": self._find_todo_comments(root_path),
                "missing_type_hints": self._find_missing_type_hints(root_path),
                "error_handling": self._analyze_error_handling(root_path)
            }
            
            self.logger.info("✅ Code analysis completed successfully")
            return analysis_results
            
        except Exception as e:
            self.logger.error(f"❌ Code analysis failed: {e}")
            return {"error": str(e)}
    
    def _find_duplicated_code(self, root_path: str) -> Dict[str, List[str]]:
        """Находит дублированный код"""
        duplicated = {}
        file_contents = {}
        
        try:
            # Собираем содержимое всех Python файлов
            for py_file in Path(root_path).rglob("*.py"):
                if "venv" in str(py_file) or "__pycache__" in str(py_file):
                    continue
                
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        file_contents[str(py_file)] = content
                except Exception:
                    continue
            
            # Ищем дублированные блоки кода
            for file1, content1 in file_contents.items():
                for file2, content2 in file_contents.items():
                    if file1 >= file2:  # Избегаем дублирования
                        continue
                    
                    # Ищем общие строки длиннее 5 символов
                    lines1 = content1.split('\n')
                    lines2 = content2.split('\n')
                    
                    common_lines = set(lines1) & set(lines2)
                    common_lines = {line.strip() for line in common_lines if len(line.strip()) > 5}
                    
                    if len(common_lines) > 3:  # Если больше 3 общих строк
                        key = f"{file1} <-> {file2}"
                        duplicated[key] = list(common_lines)[:10]  # Первые 10 общих строк
            
            return duplicated
            
        except Exception as e:
            self.logger.error(f"Failed to find duplicated code: {e}")
            return {}
    
    def _find_unused_imports(self, root_path: str) -> Dict[str, List[str]]:
        """Находит неиспользуемые импорты"""
        unused = {}
        
        try:
            for py_file in Path(root_path).rglob("*.py"):
                if "venv" in str(py_file) or "__pycache__" in str(py_file):
                    continue
                
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    tree = ast.parse(content)
                    imports = []
                    used_names = set()
                    
                    # Собираем импорты и используемые имена
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                imports.append(alias.name)
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                for alias in node.names:
                                    imports.append(alias.name)
                        elif isinstance(node, ast.Name):
                            used_names.add(node.id)
                        elif isinstance(node, ast.Attribute):
                            used_names.add(node.attr)
                    
                    # Находим неиспользуемые импорты
                    unused_imports = [imp for imp in imports if imp not in used_names]
                    if unused_imports:
                        unused[str(py_file)] = unused_imports
                
                except Exception:
                    continue
            
            return unused
            
        except Exception as e:
            self.logger.error(f"Failed to find unused imports: {e}")
            return {}
    
    def _find_long_functions(self, root_path: str) -> List[Dict[str, Any]]:
        """Находит длинные функции"""
        long_functions = []
        
        try:
            for py_file in Path(root_path).rglob("*.py"):
                if "venv" in str(py_file) or "__pycache__" in str(py_file):
                    continue
                
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    tree = ast.parse(content)
                    
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            # Подсчитываем строки в функции
                            func_lines = content.split('\n')[node.lineno-1:node.end_lineno]
                            func_lines = [line for line in func_lines if line.strip() and not line.strip().startswith('#')]
                            
                            if len(func_lines) > 50:  # Функции длиннее 50 строк
                                long_functions.append({
                                    "file": str(py_file),
                                    "function": node.name,
                                    "lines": len(func_lines),
                                    "line_number": node.lineno
                                })
                
                except Exception:
                    continue
            
            return long_functions
            
        except Exception as e:
            self.logger.error(f"Failed to find long functions: {e}")
            return []
    
    def _find_complex_functions(self, root_path: str) -> List[Dict[str, Any]]:
        """Находит сложные функции (высокая цикломатическая сложность)"""
        complex_functions = []
        
        try:
            for py_file in Path(root_path).rglob("*.py"):
                if "venv" in str(py_file) or "__pycache__" in str(py_file):
                    continue
                
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    tree = ast.parse(content)
                    
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            complexity = self._calculate_complexity(node)
                            
                            if complexity > 10:  # Сложность больше 10
                                complex_functions.append({
                                    "file": str(py_file),
                                    "function": node.name,
                                    "complexity": complexity,
                                    "line_number": node.lineno
                                })
                
                except Exception:
                    continue
            
            return complex_functions
            
        except Exception as e:
            self.logger.error(f"Failed to find complex functions: {e}")
            return []
    
    def _calculate_complexity(self, node: ast.AST) -> int:
        """Вычисляет цикломатическую сложность"""
        complexity = 1  # Базовая сложность
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _find_todo_comments(self, root_path: str) -> List[Dict[str, Any]]:
        """Находит TODO комментарии"""
        todos = []
        
        try:
            for py_file in Path(root_path).rglob("*.py"):
                if "venv" in str(py_file) or "__pycache__" in str(py_file):
                    continue
                
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    for i, line in enumerate(lines, 1):
                        if re.search(r'#\s*(TODO|FIXME|HACK|XXX|BUG)', line, re.IGNORECASE):
                            todos.append({
                                "file": str(py_file),
                                "line_number": i,
                                "content": line.strip(),
                                "type": re.search(r'(TODO|FIXME|HACK|XXX|BUG)', line, re.IGNORECASE).group(1).upper()
                            })
                
                except Exception:
                    continue
            
            return todos
            
        except Exception as e:
            self.logger.error(f"Failed to find TODO comments: {e}")
            return []
    
    def _find_missing_type_hints(self, root_path: str) -> List[Dict[str, Any]]:
        """Находит функции без type hints"""
        missing_hints = []
        
        try:
            for py_file in Path(root_path).rglob("*.py"):
                if "venv" in str(py_file) or "__pycache__" in str(py_file):
                    continue
                
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    tree = ast.parse(content)
                    
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            # Проверяем наличие type hints
                            has_return_annotation = node.returns is not None
                            has_args_annotations = all(arg.annotation is not None for arg in node.args.args)
                            
                            if not has_return_annotation or not has_args_annotations:
                                missing_hints.append({
                                    "file": str(py_file),
                                    "function": node.name,
                                    "line_number": node.lineno,
                                    "missing_return": not has_return_annotation,
                                    "missing_args": not has_args_annotations
                                })
                
                except Exception:
                    continue
            
            return missing_hints
            
        except Exception as e:
            self.logger.error(f"Failed to find missing type hints: {e}")
            return []
    
    def _analyze_error_handling(self, root_path: str) -> List[Dict[str, Any]]:
        """Анализирует обработку ошибок"""
        error_analysis = []
        
        try:
            for py_file in Path(root_path).rglob("*.py"):
                if "venv" in str(py_file) or "__pycache__" in str(py_file):
                    continue
                
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    tree = ast.parse(content)
                    
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            # Ищем try-except блоки
                            has_try_except = any(isinstance(child, ast.Try) for child in ast.walk(node))
                            
                            # Ищем функции без обработки ошибок
                            if not has_try_except and len(list(ast.walk(node))) > 10:  # Функции с достаточной сложностью
                                error_analysis.append({
                                    "file": str(py_file),
                                    "function": node.name,
                                    "line_number": node.lineno,
                                    "has_error_handling": has_try_except
                                })
                
                except Exception:
                    continue
            
            return error_analysis
            
        except Exception as e:
            self.logger.error(f"Failed to analyze error handling: {e}")
            return []
    
    def generate_optimization_report(self, analysis_results: Dict[str, Any]) -> str:
        """Генерирует отчет по оптимизации"""
        report = []
        report.append("# Отчет по оптимизации кода\n")
        
        # Дублированный код
        if analysis_results.get("duplicated_code"):
            report.append("## 🔄 Дублированный код")
            report.append(f"Найдено {len(analysis_results['duplicated_code'])} пар файлов с дублированным кодом:\n")
            for files, lines in analysis_results["duplicated_code"].items():
                report.append(f"- {files}")
                report.append(f"  Общие строки: {len(lines)}")
            report.append("")
        
        # Неиспользуемые импорты
        if analysis_results.get("unused_imports"):
            report.append("## 📦 Неиспользуемые импорты")
            report.append(f"Найдено {len(analysis_results['unused_imports'])} файлов с неиспользуемыми импортами:\n")
            for file, imports in analysis_results["unused_imports"].items():
                report.append(f"- {file}: {', '.join(imports)}")
            report.append("")
        
        # Длинные функции
        if analysis_results.get("long_functions"):
            report.append("## 📏 Длинные функции")
            report.append(f"Найдено {len(analysis_results['long_functions'])} функций длиннее 50 строк:\n")
            for func in analysis_results["long_functions"]:
                report.append(f"- {func['file']}:{func['line_number']} {func['function']} ({func['lines']} строк)")
            report.append("")
        
        # Сложные функции
        if analysis_results.get("complex_functions"):
            report.append("## 🧩 Сложные функции")
            report.append(f"Найдено {len(analysis_results['complex_functions'])} функций с высокой сложностью:\n")
            for func in analysis_results["complex_functions"]:
                report.append(f"- {func['file']}:{func['line_number']} {func['function']} (сложность: {func['complexity']})")
            report.append("")
        
        # TODO комментарии
        if analysis_results.get("todo_comments"):
            report.append("## 📝 TODO комментарии")
            report.append(f"Найдено {len(analysis_results['todo_comments'])} TODO комментариев:\n")
            for todo in analysis_results["todo_comments"][:20]:  # Показываем первые 20
                report.append(f"- {todo['file']}:{todo['line_number']} [{todo['type']}] {todo['content']}")
            if len(analysis_results["todo_comments"]) > 20:
                report.append(f"... и еще {len(analysis_results['todo_comments']) - 20}")
            report.append("")
        
        # Отсутствующие type hints
        if analysis_results.get("missing_type_hints"):
            report.append("## 🏷️ Отсутствующие type hints")
            report.append(f"Найдено {len(analysis_results['missing_type_hints'])} функций без type hints:\n")
            for func in analysis_results["missing_type_hints"][:10]:  # Показываем первые 10
                missing = []
                if func["missing_return"]:
                    missing.append("return type")
                if func["missing_args"]:
                    missing.append("args types")
                report.append(f"- {func['file']}:{func['line_number']} {func['function']} (отсутствует: {', '.join(missing)})")
            report.append("")
        
        # Обработка ошибок
        if analysis_results.get("error_handling"):
            no_error_handling = [f for f in analysis_results["error_handling"] if not f["has_error_handling"]]
            if no_error_handling:
                report.append("## ⚠️ Функции без обработки ошибок")
                report.append(f"Найдено {len(no_error_handling)} функций без обработки ошибок:\n")
                for func in no_error_handling[:10]:  # Показываем первые 10
                    report.append(f"- {func['file']}:{func['line_number']} {func['function']}")
                report.append("")
        
        return "\n".join(report)


# Глобальный экземпляр оптимизатора кода
code_optimizer = CodeOptimizer()
