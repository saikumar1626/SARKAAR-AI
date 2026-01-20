"""
Explanation Agent
Explains code logic in simple, understandable terms
"""

import ast
import re
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from core import Request, Response, Language
import time

logger = logging.getLogger(__name__)


@dataclass
class Explanation:
    """Code explanation"""
    section: str
    line_range: Optional[tuple]
    explanation: str
    complexity: str
    key_concepts: List[str]


class PythonExplainer:
    """Explains Python code"""
    
    def explain_code(self, code: str, detail_level: str = "medium") -> Dict[str, Any]:
        """Generate comprehensive code explanation"""
        
        try:
            tree = ast.parse(code)
            
            explanation = {
                "overview": self._generate_overview(tree, code),
                "structure": self._explain_structure(tree),
                "functions": self._explain_functions(tree),
                "classes": self._explain_classes(tree),
                "logic_flow": self._explain_logic_flow(tree, code),
                "key_concepts": self._identify_key_concepts(tree, code),
                "step_by_step": self._generate_step_by_step(code, detail_level)
            }
            
            return explanation
            
        except SyntaxError as e:
            return {
                "error": "Cannot explain code with syntax errors",
                "suggestion": f"Fix syntax error at line {e.lineno}"
            }
    
    def _generate_overview(self, tree: ast.AST, code: str) -> str:
        """Generate high-level overview"""
        
        lines = code.split('\n')
        loc = len([l for l in lines if l.strip() and not l.strip().startswith('#')])
        
        functions = len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)])
        classes = len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)])
        
        overview = []
        overview.append(f"This is a Python program with {loc} lines of code")
        
        if classes > 0:
            overview.append(f"It defines {classes} class{'es' if classes > 1 else ''}")
        if functions > 0:
            overview.append(f"It contains {functions} function{'s' if functions > 1 else ''}")
        
        # Determine purpose
        purpose = self._infer_purpose(tree, code)
        if purpose:
            overview.append(f"Purpose: {purpose}")
        
        return '. '.join(overview) + '.'
    
    def _infer_purpose(self, tree: ast.AST, code: str) -> str:
        """Infer code purpose"""
        
        code_lower = code.lower()
        
        if any(word in code_lower for word in ['request', 'api', 'http', 'url']):
            return "Makes HTTP requests or works with web APIs"
        elif any(word in code_lower for word in ['dataframe', 'pd.', 'csv', 'read_']):
            return "Processes and analyzes data"
        elif any(word in code_lower for word in ['sort', 'search', 'tree', 'graph']):
            return "Implements algorithms or data structures"
        elif any(word in code_lower for word in ['def test_', 'assert', 'unittest']):
            return "Contains test cases"
        elif any(word in code_lower for word in ['class', 'object', '__init__']):
            return "Implements classes and objects"
        else:
            return ""
    
    def _explain_structure(self, tree: ast.AST) -> Dict[str, Any]:
        """Explain code structure"""
        
        structure = {
            "imports": [],
            "global_variables": [],
            "functions": [],
            "classes": []
        }
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        structure["imports"].append(f"import {alias.name}")
                else:
                    for alias in node.names:
                        structure["imports"].append(f"from {node.module} import {alias.name}")
            
            elif isinstance(node, ast.FunctionDef):
                structure["functions"].append(node.name)
            
            elif isinstance(node, ast.ClassDef):
                structure["classes"].append(node.name)
        
        return structure
    
    def _explain_functions(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Explain each function"""
        
        explanations = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                params = [arg.arg for arg in node.args.args]
                docstring = ast.get_docstring(node)
                
                # Generate explanation
                explanation = self._explain_function_purpose(node, docstring)
                
                explanations.append({
                    "name": node.name,
                    "parameters": params,
                    "explanation": explanation,
                    "docstring": docstring,
                    "returns": self._check_return_type(node)
                })
        
        return explanations
    
    def _explain_function_purpose(self, func_node: ast.FunctionDef, docstring: Optional[str]) -> str:
        """Explain function purpose"""
        
        if docstring:
            return docstring.split('\n')[0]
        
        # Infer from name
        name = func_node.name
        
        if name.startswith('get_'):
            return f"Retrieves or returns {name[4:].replace('_', ' ')}"
        elif name.startswith('set_'):
            return f"Sets or updates {name[4:].replace('_', ' ')}"
        elif name.startswith('is_') or name.startswith('has_'):
            return f"Checks if {name[3:].replace('_', ' ')}"
        elif name.startswith('calculate_'):
            return f"Calculates {name[10:].replace('_', ' ')}"
        elif name.startswith('process_'):
            return f"Processes {name[8:].replace('_', ' ')}"
        elif name == '__init__':
            return "Initializes a new instance of the class"
        else:
            return f"Function: {name.replace('_', ' ')}"
    
    def _check_return_type(self, func_node: ast.FunctionDef) -> str:
        """Check what function returns"""
        
        for node in ast.walk(func_node):
            if isinstance(node, ast.Return):
                if node.value is None:
                    return "None"
                elif isinstance(node.value, ast.Constant):
                    return type(node.value.value).__name__
                elif isinstance(node.value, ast.Name):
                    return "variable"
                elif isinstance(node.value, ast.List):
                    return "list"
                elif isinstance(node.value, ast.Dict):
                    return "dict"
        
        return "None (implicit)"
    
    def _explain_classes(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Explain each class"""
        
        explanations = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
                docstring = ast.get_docstring(node)
                
                explanations.append({
                    "name": node.name,
                    "purpose": docstring or f"Represents a {node.name}",
                    "methods": methods,
                    "inheritance": [self._get_name(base) for base in node.bases]
                })
        
        return explanations
    
    def _get_name(self, node: ast.AST) -> str:
        """Get name from node"""
        if isinstance(node, ast.Name):
            return node.id
        return "unknown"
    
    def _explain_logic_flow(self, tree: ast.AST, code: str) -> List[str]:
        """Explain program logic flow"""
        
        flow = []
        
        # Find main execution
        has_main = any(isinstance(n, ast.If) and 
                      isinstance(n.test, ast.Compare) and
                      '__name__' in ast.unparse(n.test) if hasattr(ast, 'unparse') else False
                      for n in ast.walk(tree))
        
        if has_main:
            flow.append("Program has a main execution block (if __name__ == '__main__')")
        
        # Check for loops
        loops = len([n for n in ast.walk(tree) if isinstance(n, (ast.For, ast.While))])
        if loops > 0:
            flow.append(f"Contains {loops} loop(s) for iteration")
        
        # Check for conditionals
        ifs = len([n for n in ast.walk(tree) if isinstance(n, ast.If)])
        if ifs > 0:
            flow.append(f"Uses {ifs} conditional statement(s) for decision making")
        
        # Check for exception handling
        try_blocks = len([n for n in ast.walk(tree) if isinstance(n, ast.Try)])
        if try_blocks > 0:
            flow.append(f"Includes {try_blocks} try-except block(s) for error handling")
        
        return flow
    
    def _identify_key_concepts(self, tree: ast.AST, code: str) -> List[str]:
        """Identify key programming concepts used"""
        
        concepts = []
        
        # Check for OOP
        if any(isinstance(n, ast.ClassDef) for n in ast.walk(tree)):
            concepts.append("Object-Oriented Programming (Classes)")
        
        # Check for list comprehensions
        if any(isinstance(n, ast.ListComp) for n in ast.walk(tree)):
            concepts.append("List Comprehensions")
        
        # Check for lambda functions
        if any(isinstance(n, ast.Lambda) for n in ast.walk(tree)):
            concepts.append("Lambda Functions")
        
        # Check for generators
        if any(isinstance(n, ast.GeneratorExp) for n in ast.walk(tree)):
            concepts.append("Generator Expressions")
        
        # Check for decorators
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.decorator_list:
                concepts.append("Decorators")
                break
        
        # Check for async
        if any(isinstance(n, (ast.AsyncFunctionDef, ast.Await)) for n in ast.walk(tree)):
            concepts.append("Asynchronous Programming")
        
        # Check for context managers
        if 'with ' in code:
            concepts.append("Context Managers (with statement)")
        
        return list(set(concepts))
    
    def _generate_step_by_step(self, code: str, detail_level: str) -> List[str]:
        """Generate step-by-step explanation"""
        
        steps = []
        lines = code.split('\n')
        
        # Only do step-by-step for short code
        if len(lines) > 20 and detail_level != "high":
            return ["Code is too long for step-by-step explanation. Use 'detail_level=high' for longer code."]
        
        try:
            tree = ast.parse(code)
            
            step_num = 1
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        steps.append(f"Step {step_num}: Import {alias.name} module")
                        step_num += 1
                
                elif isinstance(node, ast.FunctionDef):
                    steps.append(f"Step {step_num}: Define function '{node.name}'")
                    step_num += 1
                
                elif isinstance(node, ast.ClassDef):
                    steps.append(f"Step {step_num}: Define class '{node.name}'")
                    step_num += 1
        
        except:
            return ["Unable to generate step-by-step explanation"]
        
        return steps[:10]  # Limit to first 10 steps


class JavaExplainer:
    """Explains Java code"""
    
    def explain_code(self, code: str, detail_level: str = "medium") -> Dict[str, Any]:
        """Generate Java code explanation"""
        
        explanation = {
            "overview": self._generate_overview(code),
            "structure": self._explain_structure(code),
            "classes": self._explain_classes(code),
            "methods": self._explain_methods(code),
            "key_concepts": self._identify_key_concepts(code)
        }
        
        return explanation
    
    def _generate_overview(self, code: str) -> str:
        """Generate overview of Java code"""
        
        classes = len(re.findall(r'\bclass\s+\w+', code))
        methods = len(re.findall(r'(?:public|private|protected)\s+(?:static\s+)?[\w<>\[\]]+\s+\w+\s*\(', code))
        
        overview = f"This is a Java program with {classes} class{'es' if classes != 1 else ''} "
        overview += f"and {methods} method{'s' if methods != 1 else ''}."
        
        return overview
    
    def _explain_structure(self, code: str) -> Dict[str, List[str]]:
        """Explain Java code structure"""
        
        return {
            "imports": re.findall(r'import\s+([\w.]+);', code),
            "classes": re.findall(r'class\s+(\w+)', code),
            "interfaces": re.findall(r'interface\s+(\w+)', code)
        }
    
    def _explain_classes(self, code: str) -> List[Dict[str, Any]]:
        """Explain Java classes"""
        
        explanations = []
        pattern = r'class\s+(\w+)'
        
        for match in re.finditer(pattern, code):
            explanations.append({
                "name": match.group(1),
                "purpose": f"Java class {match.group(1)}"
            })
        
        return explanations
    
    def _explain_methods(self, code: str) -> List[Dict[str, str]]:
        """Explain Java methods"""
        
        explanations = []
        pattern = r'(public|private|protected)\s+(static\s+)?([\w<>\[\]]+)\s+(\w+)\s*\('
        
        for match in re.finditer(pattern, code):
            explanations.append({
                "name": match.group(4),
                "visibility": match.group(1),
                "return_type": match.group(3),
                "explanation": f"Method {match.group(4)} returns {match.group(3)}"
            })
        
        return explanations
    
    def _identify_key_concepts(self, code: str) -> List[str]:
        """Identify Java concepts"""
        
        concepts = []
        
        if 'extends' in code:
            concepts.append("Inheritance")
        if 'implements' in code:
            concepts.append("Interfaces")
        if '@Override' in code:
            concepts.append("Method Overriding")
        if 'abstract' in code:
            concepts.append("Abstract Classes")
        if re.search(r'<\w+>', code):
            concepts.append("Generics")
        
        return concepts


class ExplanationAgent:
    """
    Main agent for code explanation
    """
    
    def __init__(self):
        self.python_explainer = PythonExplainer()
        self.java_explainer = JavaExplainer()
        logger.info("ExplanationAgent initialized")
    
    async def process(self, request: Request) -> Response:
        """Process explanation request"""
        start_time = time.time()
        
        try:
            if not request.code:
                raise ValueError("No code provided for explanation")
            
            detail_level = request.context.get('detail_level', 'medium') if request.context else 'medium'
            
            # Select appropriate explainer
            if request.language == Language.PYTHON:
                explanation = self.python_explainer.explain_code(request.code, detail_level)
            elif request.language == Language.JAVA:
                explanation = self.java_explainer.explain_code(request.code, detail_level)
            else:
                raise ValueError(f"Unsupported language: {request.language}")
            
            # Generate summary
            summary = self._generate_summary(explanation)
            
            result = {
                "explanation": explanation,
                "summary": summary,
                "language": request.language.value
            }
            
            return Response(
                request_id=request.request_id,
                success=True,
                data=result,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Error in explanation: {str(e)}")
            return Response(
                request_id=request.request_id,
                success=False,
                data={},
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    def _generate_summary(self, explanation: Dict[str, Any]) -> str:
        """Generate explanation summary"""
        
        if 'error' in explanation:
            return explanation['error']
        
        summary_parts = []
        
        if 'overview' in explanation:
            summary_parts.append(explanation['overview'])
        
        if 'key_concepts' in explanation and explanation['key_concepts']:
            concepts = ', '.join(explanation['key_concepts'])
            summary_parts.append(f"Key concepts: {concepts}")
        
        return ' '.join(summary_parts)


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_explanation():
        agent = ExplanationAgent()
        
        test_code = """
def calculate_fibonacci(n):
    \"\"\"Calculate the nth Fibonacci number\"\"\"
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

class Calculator:
    def __init__(self):
        self.result = 0
    
    def add(self, x, y):
        self.result = x + y
        return self.result

if __name__ == "__main__":
    calc = Calculator()
    print(calc.add(5, 3))
"""
        
        request = Request(
            request_id="explain_001",
            request_type=None,
            language=Language.PYTHON,
            code=test_code
        )
        
        response = await agent.process(request)
        
        print("=== Code Explanation ===")
        print(f"\nOverview: {response.data['explanation']['overview']}")
        print(f"\nKey Concepts: {', '.join(response.data['explanation']['key_concepts'])}")
        print(f"\nFunctions:")
        for func in response.data['explanation']['functions']:
            print(f"  - {func['name']}: {func['explanation']}")
    
    asyncio.run(test_explanation())