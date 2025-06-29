#!/usr/bin/env python3
"""
Analyze import dependencies to identify circular imports in the special education service
"""
import os
import re
import ast
from pathlib import Path
from collections import defaultdict, deque
from typing import Dict, List, Set, Tuple

class ImportAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.imports = []
        self.from_imports = []
    
    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append(alias.name)
    
    def visit_ImportFrom(self, node):
        if node.module:
            for alias in node.names:
                self.from_imports.append((node.module, alias.name))

def get_python_files(directory):
    """Get all Python files in the directory"""
    python_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files

def analyze_file_imports(filepath):
    """Analyze imports in a single Python file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the AST
        tree = ast.parse(content)
        analyzer = ImportAnalyzer()
        analyzer.visit(tree)
        
        return analyzer.imports, analyzer.from_imports
    except Exception as e:
        print(f"Error analyzing {filepath}: {e}")
        return [], []

def normalize_module_path(module_path, current_file_path, src_dir):
    """Convert relative imports to absolute module paths"""
    if module_path.startswith('.'):
        # Handle relative imports
        current_dir = os.path.dirname(current_file_path)
        level = len(module_path) - len(module_path.lstrip('.'))
        
        if level == 1:
            # Single dot - same directory
            if module_path[1:]:
                return os.path.join(current_dir, module_path[1:]).replace('/', '.')
            else:
                return current_dir.replace('/', '.')
        else:
            # Multiple dots - go up directories
            for _ in range(level - 1):
                current_dir = os.path.dirname(current_dir)
            if module_path[level:]:
                return os.path.join(current_dir, module_path[level:]).replace('/', '.')
            else:
                return current_dir.replace('/', '.')
    else:
        return module_path

def build_dependency_graph(src_directory):
    """Build a dependency graph of all Python modules"""
    src_dir = os.path.abspath(src_directory)
    python_files = get_python_files(src_dir)
    
    # Map file paths to module names
    file_to_module = {}
    module_to_file = {}
    
    for filepath in python_files:
        rel_path = os.path.relpath(filepath, src_dir)
        if rel_path.endswith('__init__.py'):
            module_name = os.path.dirname(rel_path).replace('/', '.')
        else:
            module_name = rel_path[:-3].replace('/', '.')  # Remove .py extension
        
        file_to_module[filepath] = module_name
        module_to_file[module_name] = filepath
    
    # Build dependency graph
    dependencies = defaultdict(set)
    
    for filepath in python_files:
        current_module = file_to_module[filepath]
        imports, from_imports = analyze_file_imports(filepath)
        
        # Process regular imports
        for imp in imports:
            if imp in module_to_file:
                dependencies[current_module].add(imp)
        
        # Process from imports
        for module_path, name in from_imports:
            normalized_module = normalize_module_path(module_path, 
                                                    os.path.relpath(filepath, src_dir), 
                                                    src_dir)
            
            # Remove src prefix if present
            if normalized_module.startswith('src.'):
                normalized_module = normalized_module[4:]
            
            if normalized_module in module_to_file:
                dependencies[current_module].add(normalized_module)
    
    return dependencies, module_to_file

def find_circular_dependencies(dependencies):
    """Find circular dependencies using DFS"""
    cycles = []
    visited = set()
    rec_stack = set()
    
    def dfs(node, path):
        if node in rec_stack:
            # Found a cycle
            cycle_start = path.index(node)
            cycle = path[cycle_start:] + [node]
            cycles.append(cycle)
            return
        
        if node in visited:
            return
        
        visited.add(node)
        rec_stack.add(node)
        path.append(node)
        
        for neighbor in dependencies.get(node, set()):
            dfs(neighbor, path.copy())
        
        rec_stack.remove(node)
    
    for node in dependencies:
        if node not in visited:
            dfs(node, [])
    
    return cycles

def main():
    src_directory = "src"
    print("Analyzing import dependencies in special education service...")
    print("=" * 60)
    
    # Build dependency graph
    dependencies, module_to_file = build_dependency_graph(src_directory)
    
    print(f"Found {len(module_to_file)} Python modules")
    print()
    
    # Show modules and their direct dependencies
    print("MODULE DEPENDENCIES:")
    print("-" * 40)
    for module, deps in sorted(dependencies.items()):
        if deps:
            print(f"{module}:")
            for dep in sorted(deps):
                print(f"  -> {dep}")
            print()
    
    # Find circular dependencies
    cycles = find_circular_dependencies(dependencies)
    
    print("\nCIRCULAR DEPENDENCY ANALYSIS:")
    print("=" * 40)
    
    if cycles:
        print(f"Found {len(cycles)} circular dependency chains:")
        print()
        
        for i, cycle in enumerate(cycles, 1):
            print(f"Circular Import Chain #{i}:")
            for j, module in enumerate(cycle):
                if j < len(cycle) - 1:
                    print(f"  {module}")
                    print(f"    ↓")
            print()
            
            # Show file paths for this cycle
            print("  File paths:")
            for module in cycle[:-1]:  # Exclude the duplicate at the end
                if module in module_to_file:
                    print(f"    {module} -> {module_to_file[module]}")
            print()
    else:
        print("No circular dependencies found!")
    
    # Specific analysis for database.py and models
    print("\nSPECIFIC ANALYSIS - DATABASE AND MODELS:")
    print("=" * 50)
    
    database_deps = dependencies.get('database', set())
    print(f"database.py imports from: {sorted(database_deps)}")
    
    # Find what imports from database
    imports_database = []
    for module, deps in dependencies.items():
        if 'database' in deps:
            imports_database.append(module)
    
    print(f"Files that import from database.py: {sorted(imports_database)}")
    
    # Models analysis
    models_deps = dependencies.get('models', set()) | dependencies.get('models.__init__', set())
    print(f"models/__init__.py imports from: {sorted(models_deps)}")
    
    special_ed_models_deps = dependencies.get('models.special_education_models', set())
    print(f"models/special_education_models.py imports from: {sorted(special_ed_models_deps)}")
    
    job_models_deps = dependencies.get('models.job_models', set())
    print(f"models/job_models.py imports from: {sorted(job_models_deps)}")

if __name__ == "__main__":
    main()