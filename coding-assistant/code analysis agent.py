"""
Code Analysis Agent
Analyzes code structure, quality, complexity, and potential issues
"""

import ast
import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from core import Request, Response, Language
import time

logger = logging.getLogger(__name__)


@dataclass
class CodeMetrics:
    """Code quality metrics"""
    lines_of_code: int
    cyclomatic_complexity: int
    cognitive_complexity: int
    maintainability_index: float
    code_smells: List[str]
    security_issues: List[str]
    performance_issues: List[str]


@dataclass
class FunctionInfo:
    """Information about a function"""
    name: str
    parameters: List[str]
    return_type: Optional[str]
    docstring: Optional[str]
    complexity: int
    line_start: int
    line_end: int


@dataclass
class ClassInfo:
    """Information about a class"""
    name: str
    methods: List[FunctionInfo]
    attributes: List[str]
    inheritance: List[str]
    docstring: Optional[str]
    line_start: int
    line_end: int


class PythonAnalyzer:
    """Advanced Python code analyzer using AST"""
    
    def analyze(self, code: str) -> Dict[str, Any]:
        """Perform comprehensive Python code analysis"""
        try:
            tree = ast.parse(code)
            
            analysis = {
                "structure": self._analyze_structure(tree),
                "metrics": self._calculate_metrics(tree, code),
                "functions": self._extract_functions(tree),
                "classes": self._extract_classes(tree),
                "imports": self._extract_imports(tree),
                "variables": self._extract_variables(tree),
                "code_quality": self._assess_code_quality(tree, code),
                "security": self._check_security(tree, code),
                "best_practices": self._check_best_practices(tree, code)
            }
            
            return analysis
            
        except SyntaxError as e:
            return {
                "error": "Syntax Error",
                "message": str(e),
                "line": e.lineno,
                "offset": e.offset
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _analyze_structure(self, tree: ast.AST) -> Dict[str, Any]:
        """Analyze code structure"""
        structure = {
            "functions": 0,
            "classes": 0,
            "async_functions": 0,
            "decorators": 0,
            "list_comprehensions": 0,
            "lambda_functions": 0,
            "nested_depth": 0
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                structure["functions"] += 1
            elif isinstance(node, ast.AsyncFunctionDef):
                structure["async_functions"] += 1
            elif isinstance(node, ast.ClassDef):
                structure["classes"] += 1
            elif isinstance(node, ast.ListComp):
                structure["list_comprehensions"] += 1
            elif isinstance(node, ast.Lambda):
                structure["lambda_functions"] += 1
        
        # Calculate max nesting depth
        structure["nested_depth"] = self._calculate_nesting_depth(tree)
        
        return structure
    
    def _calculate_nesting_depth(self, node: ast.AST, current_depth: int = 0) -> int:
        """Calculate maximum nesting depth"""
        max_depth = current_depth
        
        nesting_nodes = (ast.If, ast.For, ast.While, ast.With, ast.Try, 
                        ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        
        for child in ast.iter_child_nodes(node):
            if isinstance(child, nesting_nodes):
                depth = self._calculate_nesting_depth(child, current_depth + 1)
                max_depth = max(max_depth, depth)
            else:
                depth = self._calculate_nesting_depth(child, current_depth)
                max_depth = max(max_depth, depth)
        
        return max_depth
    
    def _calculate_metrics(self, tree: ast.AST, code: str) -> CodeMetrics:
        """Calculate code metrics"""
        lines = code.split('\n')
        loc = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
        
        # Cyclomatic complexity
        complexity = self._cyclomatic_complexity(tree)
        
        # Cognitive complexity
        cognitive = self._cognitive_complexity(tree)
        
        # Maintainability index (simplified)
        maintainability = 171 - 5.2 * complexity - 0.23 * complexity - 16.2 * (loc / 100)
        maintainability = max(0, min(100, maintainability))
        
        # Code smells
        smells = self._detect_code_smells(tree, code)
        
        # Security issues
        security = self._detect_security_issues(tree, code)
        
        # Performance issues
        performance = self._detect_performance_issues(tree, code)
        
        return CodeMetrics(
            lines_of_code=loc,
            cyclomatic_complexity=complexity,
            cognitive_complexity=cognitive,
            maintainability_index=maintainability,
            code_smells=smells,
            security_issues=security,
            performance_issues=performance
        )
    
    def _cyclomatic_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity"""
        complexity = 1  # Base complexity
        
        decision_nodes = (ast.If, ast.While, ast.For, ast.ExceptHandler,
                         ast.BoolOp, ast.IfExp, ast.comprehension)
        
        for node in ast.walk(tree):
            if isinstance(node, decision_nodes):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        
        return complexity
    
    def _cognitive_complexity(self, tree: ast.AST) -> int:
        """Calculate cognitive complexity"""
        return self._cognitive_complexity_recursive(tree, 0, 0)
    
    def _cognitive_complexity_recursive(self, node: ast.AST, nesting: int, total: int) -> int:
        """Recursively calculate cognitive complexity"""
        increment_nodes = (ast.If, ast.While, ast.For, ast.ExceptHandler)
        nesting_nodes = (ast.If, ast.While, ast.For, ast.With, ast.Try, 
                        ast.FunctionDef, ast.AsyncFunctionDef)
        
        for child in ast.iter_child_nodes(node):
            if isinstance(child, increment_nodes):
                total += 1 + nesting
            
            if isinstance(child, nesting_nodes):
                total = self._cognitive_complexity_recursive(child, nesting + 1, total)
            else:
                total = self._cognitive_complexity_recursive(child, nesting, total)
        
        return total
    
    def _detect_code_smells(self, tree: ast.AST, code: str) -> List[str]:
        """Detect common code smells"""
        smells = []
        
        for node in ast.walk(tree):
            # Long method
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
                    length = node.end_lineno - node.lineno
                    if length > 50:
                        smells.append(f"Long method '{node.name}' ({length} lines)")
            
            # Too many parameters
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                param_count = len(node.args.args)
                if param_count > 5:
                    smells.append(f"Too many parameters in '{node.name}' ({param_count})")
            
            # Deeply nested code
            if isinstance(node, (ast.If, ast.For, ast.While)):
                depth = self._get_node_depth(tree, node)
                if depth > 4:
                    smells.append(f"Deeply nested code (depth {depth})")
            
            # Large class
            if isinstance(node, ast.ClassDef):
                method_count = len([n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))])
                if method_count > 20:
                    smells.append(f"Large class '{node.name}' ({method_count} methods)")
        
        return list(set(smells))  # Remove duplicates
    
    def _detect_security_issues(self, tree: ast.AST, code: str) -> List[str]:
        """Detect potential security issues"""
        issues = []
        
        for node in ast.walk(tree):
            # Use of eval()
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == 'eval':
                    issues.append("Use of 'eval()' - potential code injection risk")
                if isinstance(node.func, ast.Name) and node.func.id == 'exec':
                    issues.append("Use of 'exec()' - potential code injection risk")
            
            # Hardcoded credentials (simple check)
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        name_lower = target.id.lower()
                        if any(keyword in name_lower for keyword in ['password', 'secret', 'key', 'token']):
                            if isinstance(node.value, ast.Constant):
                                issues.append(f"Potential hardcoded credential in variable '{target.id}'")
        
        # Check for SQL injection patterns
        if re.search(r'execute\s*\([^)]*%s[^)]*\)', code) or re.search(r'execute\s*\([^)]*\+[^)]*\)', code):
            issues.append("Potential SQL injection - use parameterized queries")
        
        return list(set(issues))
    
    def _detect_performance_issues(self, tree: ast.AST, code: str) -> List[str]:
        """Detect potential performance issues"""
        issues = []
        
        for node in ast.walk(tree):
            # Loop with append (consider list comprehension)
            if isinstance(node, (ast.For, ast.While)):
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Attribute) and child.func.attr == 'append':
                            issues.append("Consider using list comprehension instead of loop with append")
                            break
            
            # Nested loops
            if isinstance(node, (ast.For, ast.While)):
                for child in ast.iter_child_nodes(node):
                    if isinstance(child, (ast.For, ast.While)):
                        issues.append("Nested loops detected - O(n²) complexity, consider optimization")
        
        # Multiple list iterations
        list_iterations = code.count('for ') + code.count('while ')
        if list_iterations > 3:
            issues.append(f"Multiple list iterations ({list_iterations}) - consider combining operations")
        
        return list(set(issues))
    
    def _get_node_depth(self, tree: ast.AST, target_node: ast.AST, current_depth: int = 0) -> int:
        """Get the nesting depth of a specific node"""
        if tree == target_node:
            return current_depth
        
        nesting_nodes = (ast.If, ast.For, ast.While, ast.With, ast.Try,
                        ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        
        for child in ast.iter_child_nodes(tree):
            if isinstance(child, nesting_nodes):
                depth = self._get_node_depth(child, target_node, current_depth + 1)
                if depth > 0:
                    return depth
            else:
                depth = self._get_node_depth(child, target_node, current_depth)
                if depth > 0:
                    return depth
        
        return 0
    
    def _extract_functions(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract function information"""
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_info = {
                    "name": node.name,
                    "parameters": [arg.arg for arg in node.args.args],
                    "is_async": isinstance(node, ast.AsyncFunctionDef),
                    "decorators": [self._get_decorator_name(dec) for dec in node.decorator_list],
                    "docstring": ast.get_docstring(node),
                    "line_start": node.lineno,
                    "line_end": node.end_lineno if hasattr(node, 'end_lineno') else None,
                    "complexity": self._cyclomatic_complexity(node)
                }
                functions.append(func_info)
        
        return functions
    
    def _extract_classes(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract class information"""
        classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [m.name for m in node.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]
                
                class_info = {
                    "name": node.name,
                    "methods": methods,
                    "inheritance": [self._get_name(base) for base in node.bases],
                    "docstring": ast.get_docstring(node),
                    "line_start": node.lineno,
                    "line_end": node.end_lineno if hasattr(node, 'end_lineno') else None
                }
                classes.append(class_info)
        
        return classes
    
    def _extract_imports(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract import information"""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({
                        "module": alias.name,
                        "alias": alias.asname,
                        "type": "import"
                    })
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    imports.append({
                        "module": node.module,
                        "name": alias.name,
                        "alias": alias.asname,
                        "type": "from_import"
                    })
        
        return imports
    
    def _extract_variables(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract variable information"""
        variables = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        var_type = self._infer_type(node.value)
                        variables.append({
                            "name": target.id,
                            "inferred_type": var_type,
                            "line": node.lineno
                        })
        
        return variables
    
    def _infer_type(self, node: ast.AST) -> str:
        """Infer variable type from assignment"""
        if isinstance(node, ast.Constant):
            return type(node.value).__name__
        elif isinstance(node, ast.List):
            return "list"
        elif isinstance(node, ast.Dict):
            return "dict"
        elif isinstance(node, ast.Set):
            return "set"
        elif isinstance(node, ast.Tuple):
            return "tuple"
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                return node.func.id
        return "unknown"
    
    def _get_decorator_name(self, decorator: ast.AST) -> str:
        """Get decorator name"""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name):
            return decorator.func.id
        return "unknown"
    
    def _get_name(self, node: ast.AST) -> str:
        """Get name from node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        return "unknown"
    
    def _assess_code_quality(self, tree: ast.AST, code: str) -> Dict[str, Any]:
        """Assess overall code quality"""
        metrics = self._calculate_metrics(tree, code)
        
        # Calculate quality score (0-100)
        quality_score = 100
        
        # Deduct for high complexity
        if metrics.cyclomatic_complexity > 10:
            quality_score -= (metrics.cyclomatic_complexity - 10) * 2
        
        # Deduct for code smells
        quality_score -= len(metrics.code_smells) * 5
        
        # Deduct for security issues
        quality_score -= len(metrics.security_issues) * 10
        
        # Deduct for performance issues
        quality_score -= len(metrics.performance_issues) * 3
        
        quality_score = max(0, min(100, quality_score))
        
        # Determine rating
        if quality_score >= 90:
            rating = "Excellent"
        elif quality_score >= 75:
            rating = "Good"
        elif quality_score >= 60:
            rating = "Fair"
        elif quality_score >= 40:
            rating = "Poor"
        else:
            rating = "Critical"
        
        return {
            "score": quality_score,
            "rating": rating,
            "maintainability_index": metrics.maintainability_index,
            "summary": self._generate_quality_summary(metrics, quality_score, rating)
        }
    
    def _generate_quality_summary(self, metrics: CodeMetrics, score: float, rating: str) -> str:
        """Generate quality summary"""
        issues = []
        
        if metrics.cyclomatic_complexity > 10:
            issues.append(f"high complexity ({metrics.cyclomatic_complexity})")
        if metrics.code_smells:
            issues.append(f"{len(metrics.code_smells)} code smells")
        if metrics.security_issues:
            issues.append(f"{len(metrics.security_issues)} security issues")
        if metrics.performance_issues:
            issues.append(f"{len(metrics.performance_issues)} performance issues")
        
        if issues:
            return f"Code quality is {rating.lower()} with {', '.join(issues)}"
        else:
            return f"Code quality is {rating.lower()} with no major issues"
    
    def _check_best_practices(self, tree: ast.AST, code: str) -> List[Dict[str, str]]:
        """Check adherence to best practices"""
        recommendations = []
        
        # Check for docstrings
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if not ast.get_docstring(node):
                    recommendations.append({
                        "type": "documentation",
                        "severity": "medium",
                        "message": f"Missing docstring for {node.__class__.__name__.lower()} '{node.name}'",
                        "line": node.lineno
                    })
        
        # Check naming conventions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not node.name.islower() and not node.name.startswith('_'):
                    recommendations.append({
                        "type": "naming",
                        "severity": "low",
                        "message": f"Function '{node.name}' should use snake_case",
                        "line": node.lineno
                    })
            elif isinstance(node, ast.ClassDef):
                if not node.name[0].isupper():
                    recommendations.append({
                        "type": "naming",
                        "severity": "low",
                        "message": f"Class '{node.name}' should use PascalCase",
                        "line": node.lineno
                    })
        
        # Check for bare except
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    recommendations.append({
                        "type": "error_handling",
                        "severity": "high",
                        "message": "Avoid bare 'except:' clause - catch specific exceptions",
                        "line": node.lineno
                    })
        
        return recommendations


class JavaAnalyzer:
    """Java code analyzer using regex patterns"""
    
    def analyze(self, code: str) -> Dict[str, Any]:
        """Perform Java code analysis"""
        analysis = {
            "structure": self._analyze_structure(code),
            "metrics": self._calculate_metrics(code),
            "classes": self._extract_classes(code),
            "methods": self._extract_methods(code),
            "imports": self._extract_imports(code),
            "code_quality": self._assess_code_quality(code),
            "security": self._check_security(code),
            "best_practices": self._check_best_practices(code)
        }
        
        return analysis
    
    def _analyze_structure(self, code: str) -> Dict[str, Any]:
        """Analyze Java code structure"""
        return {
            "classes": len(re.findall(r'\bclass\s+\w+', code)),
            "interfaces": len(re.findall(r'\binterface\s+\w+', code)),
            "methods": len(re.findall(r'(?:public|private|protected)\s+(?:static\s+)?[\w<>\[\]]+\s+\w+\s*\(', code)),
            "enums": len(re.findall(r'\benum\s+\w+', code)),
            "annotations": len(re.findall(r'@\w+', code))
        }
    
    def _calculate_metrics(self, code: str) -> Dict[str, Any]:
        """Calculate Java code metrics"""
        lines = code.split('\n')
        loc = len([line for line in lines if line.strip() and not line.strip().startswith('//')])
        
        # Simplified complexity calculation
        complexity = 1
        complexity += code.count('if ')
        complexity += code.count('for ')
        complexity += code.count('while ')
        complexity += code.count('case ')
        complexity += code.count('catch ')
        complexity += code.count('&&')
        complexity += code.count('||')
        
        return {
            "lines_of_code": loc,
            "cyclomatic_complexity": complexity,
            "comment_lines": len([line for line in lines if line.strip().startswith('//')]),
            "blank_lines": len([line for line in lines if not line.strip()])
        }
    
    def _extract_classes(self, code: str) -> List[Dict[str, Any]]:
        """Extract Java class information"""
        classes = []
        pattern = r'(public\s+|private\s+|protected\s+)?(abstract\s+|final\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([\w,\s]+))?'
        
        for match in re.finditer(pattern, code):
            classes.append({
                "name": match.group(3),
                "visibility": match.group(1).strip() if match.group(1) else "package-private",
                "modifiers": match.group(2).strip() if match.group(2) else None,
                "extends": match.group(4),
                "implements": match.group(5).split(',') if match.group(5) else []
            })
        
        return classes
    
    def _extract_methods(self, code: str) -> List[Dict[str, Any]]:
        """Extract Java method information"""
        methods = []
        pattern = r'(public|private|protected)\s+(static\s+)?([\w<>\[\]]+)\s+(\w+)\s*\((.*?)\)'
        
        for match in re.finditer(pattern, code):
            methods.append({
                "visibility": match.group(1),
                "is_static": bool(match.group(2)),
                "return_type": match.group(3),
                "name": match.group(4),
                "parameters": match.group(5).strip()
            })
        
        return methods
    
    def _extract_imports(self, code: str) -> List[str]:
        """Extract Java imports"""
        return re.findall(r'import\s+([\w.]+);', code)
    
    def _assess_code_quality(self, code: str) -> Dict[str, Any]:
        """Assess Java code quality"""
        issues = []
        
        # Check for empty catch blocks
        if re.search(r'catch\s*\([^)]+\)\s*\{\s*\}', code):
            issues.append("Empty catch blocks detected")
        
        # Check for System.out.println (should use logging)
        if 'System.out.println' in code:
            issues.append("Using System.out.println - consider using logging framework")
        
        # Check for deprecated @SuppressWarnings("all")
        if '@SuppressWarnings("all")' in code:
            issues.append("Overly broad @SuppressWarnings - be more specific")
        
        score = 100 - (len(issues) * 10)
        
        return {
            "score": max(0, score),
            "issues": issues
        }
    
    def _check_security(self, code: str) -> List[str]:
        """Check for Java security issues"""
        issues = []
        
        if re.search(r'(Runtime\.getRuntime\(\)\.exec|ProcessBuilder)', code):
            issues.append("Command execution detected - validate inputs carefully")
        
        if 'PreparedStatement' not in code and re.search(r'Statement.*execute', code):
            issues.append("Potential SQL injection - use PreparedStatement")
        
        if 'SecureRandom' not in code and 'Random' in code:
            issues.append("Using Random instead of SecureRandom for security operations")
        
        return issues
    
    def _check_best_practices(self, code: str) -> List[Dict[str, str]]:
        """Check Java best practices"""
        recommendations = []
        
        # Check for proper exception handling
        if code.count('catch (Exception e)') > code.count('catch ('):
            recommendations.append({
                "type": "error_handling",
                "message": "Catch specific exceptions instead of generic Exception"
            })
        
        # Check for proper resource management
        if 'new FileInputStream' in code and 'try-with-resources' not in code:
            recommendations.append({
                "type": "resource_management",
                "message": "Use try-with-resources for automatic resource management"
            })
        
        return recommendations


class CodeAnalysisAgent:
    """
    Main agent for code analysis
    Coordinates language-specific analyzers
    """
    
    def __init__(self):
        self.python_analyzer = PythonAnalyzer()
        self.java_analyzer = JavaAnalyzer()
        logger.info("CodeAnalysisAgent initialized")
    
    async def process(self, request: Request) -> Response:
        """Process code analysis request"""
        start_time = time.time()
        
        try:
            if not request.code:
                raise ValueError("No code provided for analysis")
            
            # Select appropriate analyzer
            if request.language == Language.PYTHON:
                analysis = self.python_analyzer.analyze(request.code)
            elif request.language == Language.JAVA:
                analysis = self.java_analyzer.analyze(request.code)
            else:
                raise ValueError(f"Unsupported language: {request.language}")
            
            # Add general insights
            insights = self._generate_insights(analysis)
            
            result = {
                "analysis": analysis,
                "insights": insights,
                "language": request.language.value
            }
            
            return Response(
                request_id=request.request_id,
                success=True,
                data=result,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Error in code analysis: {str(e)}")
            return Response(
                request_id=request.request_id,
                success=False,
                data={},
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    def _generate_insights(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate actionable insights from analysis"""
        insights = []
        
        if 'error' in analysis:
            return [f"Code has syntax errors: {analysis.get('message', 'Unknown error')}"]
        
        # Complexity insights
        if 'metrics' in analysis:
            metrics = analysis['metrics']
            if isinstance(metrics, CodeMetrics):
                if metrics.cyclomatic_complexity > 10:
                    insights.append(f"⚠️ High cyclomatic complexity ({metrics.cyclomatic_complexity}). Consider refactoring into smaller functions.")
                
                if metrics.cognitive_complexity > 15:
                    insights.append(f"⚠️ High cognitive complexity ({metrics.cognitive_complexity}). Code may be difficult to understand.")
                
                if metrics.maintainability_index < 60:
                    insights.append(f"⚠️ Low maintainability index ({metrics.maintainability_index:.1f}). Code may be hard to maintain.")
        
        # Security insights
        if 'security' in analysis and analysis['security']:
            insights.append(f"🔒 {len(analysis['security'])} security issues found. Review and address immediately.")
        
        # Performance insights
        if 'metrics' in analysis and isinstance(analysis['metrics'], CodeMetrics):
            if analysis['metrics'].performance_issues:
                insights.append(f"⚡ {len(analysis['metrics'].performance_issues)} performance issues detected.")
        
        # Best practices insights
        if 'best_practices' in analysis and analysis['best_practices']:
            high_severity = [r for r in analysis['best_practices'] if r.get('severity') == 'high']
            if high_severity:
                insights.append(f"📋 {len(high_severity)} high-priority best practice violations.")
        
        if not insights:
            insights.append("✅ Code looks good! No major issues detected.")
        
        return insights


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_analysis():
        agent = CodeAnalysisAgent()
        
        # Test Python code
        python_code = """
def calculate_fibonacci(n):
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

def process_data(data):
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
    return result

password = "hardcoded_secret_123"
"""
        
        request = Request(
            request_id="test_001",
            request_type=None,
            language=Language.PYTHON,
            code=python_code
        )
        
        response = await agent.process(request)
        
        print("=== Code Analysis Results ===")
        print(f"Success: {response.success}")
        print(f"\nInsights:")
        for insight in response.data.get('insights', []):
            print(f"  {insight}")
        
        print(f"\nCode Quality Score: {response.data['analysis']['code_quality']['score']}")
        print(f"Rating: {response.data['analysis']['code_quality']['rating']}")
    
    asyncio.run(test_analysis())