"""
Optimization Agent
Analyzes and optimizes code for better performance
"""

import ast
import re
import logging
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from core import Request, Response, Language
import time

logger = logging.getLogger(__name__)


@dataclass
class Optimization:
    """Represents a code optimization"""
    type: str
    priority: str  # high, medium, low
    line: Optional[int]
    original_code: str
    optimized_code: str
    explanation: str
    impact: str  # performance, memory, readability
    estimated_improvement: str


class PythonOptimizer:
    """Optimizes Python code"""
    
    def analyze_and_optimize(self, code: str) -> List[Optimization]:
        """Find and suggest optimizations"""
        
        optimizations = []
        
        try:
            tree = ast.parse(code)
            
            # Check various optimization opportunities
            optimizations.extend(self._optimize_loops(tree, code))
            optimizations.extend(self._optimize_data_structures(tree, code))
            optimizations.extend(self._optimize_string_operations(code))
            optimizations.extend(self._optimize_function_calls(tree, code))
            optimizations.extend(self._optimize_comprehensions(tree, code))
            
        except SyntaxError:
            pass
        
        return optimizations
    
    def _optimize_loops(self, tree: ast.AST, code: str) -> List[Optimization]:
        """Optimize loop structures"""
        optimizations = []
        
        for node in ast.walk(tree):
            # Replace loop+append with list comprehension
            if isinstance(node, ast.For):
                has_append = False
                append_target = None
                
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Attribute) and child.func.attr == 'append':
                            has_append = True
                            if isinstance(child.func.value, ast.Name):
                                append_target = child.func.value.id
                            break
                
                if has_append and append_target:
                    original = ast.unparse(node) if hasattr(ast, 'unparse') else "<loop with append>"
                    
                    # Try to create list comprehension suggestion
                    iter_var = node.target.id if isinstance(node.target, ast.Name) else "item"
                    iterable = ast.unparse(node.iter) if hasattr(ast, 'unparse') else "iterable"
                    
                    optimized = f"{append_target} = [item for {iter_var} in {iterable}]"
                    
                    optimizations.append(Optimization(
                        type="ListComprehension",
                        priority="high",
                        line=node.lineno,
                        original_code=original,
                        optimized_code=optimized,
                        explanation="Replace loop with list comprehension for better performance",
                        impact="performance",
                        estimated_improvement="2-3x faster, more Pythonic"
                    ))
        
        return optimizations
    
    def _optimize_data_structures(self, tree: ast.AST, code: str) -> List[Optimization]:
        """Optimize data structure usage"""
        optimizations = []
        
        # Check for membership testing in lists
        list_membership_pattern = r'if\s+(\w+)\s+in\s+\[([^\]]+)\]'
        for match in re.finditer(list_membership_pattern, code):
            line_num = code[:match.start()].count('\n') + 1
            variable = match.group(1)
            items = match.group(2)
            
            optimizations.append(Optimization(
                type="DataStructure",
                priority="medium",
                line=line_num,
                original_code=f"if {variable} in [{items}]",
                optimized_code=f"if {variable} in {{{items}}}",
                explanation="Use set instead of list for membership testing",
                impact="performance",
                estimated_improvement="O(1) vs O(n) lookup time"
            ))
        
        return optimizations
    
    def _optimize_string_operations(self, code: str) -> List[Optimization]:
        """Optimize string operations"""
        optimizations = []
        
        # String concatenation in loops
        concat_pattern = r'(\w+)\s*\+=\s*(?:str\()?[^#\n]+'
        for i, line in enumerate(code.split('\n'), 1):
            if '+=' in line and 'str' in line.lower():
                optimizations.append(Optimization(
                    type="StringConcatenation",
                    priority="medium",
                    line=i,
                    original_code=line.strip(),
                    optimized_code="Use list and ''.join() for string concatenation",
                    explanation="String concatenation in loops is inefficient",
                    impact="performance",
                    estimated_improvement="O(n) vs O(n²) for large strings"
                ))
        
        # Multiple string formatting
        if code.count('%') > 3 or code.count('.format') > 3:
            optimizations.append(Optimization(
                type="StringFormatting",
                priority="low",
                line=None,
                original_code="Multiple .format() or % operations",
                optimized_code="Use f-strings for better readability and performance",
                explanation="f-strings are faster and more readable",
                impact="performance",
                estimated_improvement="10-20% faster than .format()"
            ))
        
        return optimizations
    
    def _optimize_function_calls(self, tree: ast.AST, code: str) -> List[Optimization]:
        """Optimize function calls"""
        optimizations = []
        
        for node in ast.walk(tree):
            # len() in loop condition
            if isinstance(node, (ast.For, ast.While)):
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Name) and child.func.id == 'len':
                            optimizations.append(Optimization(
                                type="FunctionCall",
                                priority="low",
                                line=node.lineno,
                                original_code="len() called in loop",
                                optimized_code="Store len() result before loop",
                                explanation="Avoid repeated len() calls",
                                impact="performance",
                                estimated_improvement="Minor improvement for large iterations"
                            ))
        
        return optimizations
    
    def _optimize_comprehensions(self, tree: ast.AST, code: str) -> List[Optimization]:
        """Optimize comprehensions"""
        optimizations = []
        
        for node in ast.walk(tree):
            # Nested comprehensions
            if isinstance(node, ast.ListComp):
                nested_count = sum(1 for _ in ast.walk(node) if isinstance(_, ast.ListComp))
                if nested_count > 1:
                    optimizations.append(Optimization(
                        type="NestedComprehension",
                        priority="medium",
                        line=node.lineno,
                        original_code="Nested list comprehension",
                        optimized_code="Consider using nested loops or generator expressions",
                        explanation="Deeply nested comprehensions reduce readability",
                        impact="readability",
                        estimated_improvement="Better code maintainability"
                    ))
        
        return optimizations
    
    def apply_optimizations(self, code: str, optimizations: List[Optimization]) -> str:
        """Apply optimizations to code"""
        optimized_code = code
        
        # Sort by line number (descending) to avoid offset issues
        sorted_opts = sorted([o for o in optimizations if o.line and o.priority == "high"], 
                           key=lambda x: x.line, reverse=True)
        
        for opt in sorted_opts:
            if opt.type == "ListComprehension":
                # This is a simplified replacement
                lines = optimized_code.split('\n')
                # More sophisticated replacement would be needed for production
                pass
        
        return optimized_code


class JavaOptimizer:
    """Optimizes Java code"""
    
    def analyze_and_optimize(self, code: str) -> List[Optimization]:
        """Find and suggest Java optimizations"""
        
        optimizations = []
        
        # String concatenation in loops
        if re.search(r'for.*\{[^}]*\+=.*String', code, re.DOTALL):
            optimizations.append(Optimization(
                type="StringBuilder",
                priority="high",
                line=None,
                original_code="String concatenation in loop",
                optimized_code="Use StringBuilder instead of String concatenation",
                explanation="StringBuilder is mutable and much faster for concatenation",
                impact="performance",
                estimated_improvement="10-100x faster for large strings"
            ))
        
        # ArrayList vs LinkedList
        if 'LinkedList' in code and ('get(' in code or '[' in code):
            optimizations.append(Optimization(
                type="DataStructure",
                priority="medium",
                line=None,
                original_code="LinkedList with random access",
                optimized_code="Use ArrayList instead of LinkedList for random access",
                explanation="ArrayList has O(1) random access vs LinkedList's O(n)",
                impact="performance",
                estimated_improvement="Much faster random access"
            ))
        
        # Boxing/Unboxing
        if re.search(r'Integer|Double|Long', code) and re.search(r'for.*int|double|long', code):
            optimizations.append(Optimization(
                type="AutoBoxing",
                priority="medium",
                line=None,
                original_code="Potential autoboxing in loops",
                optimized_code="Use primitive types instead of wrapper classes",
                explanation="Avoid autoboxing overhead in performance-critical code",
                impact="performance",
                estimated_improvement="Reduced memory and CPU overhead"
            ))
        
        return optimizations


class OptimizationAgent:
    """
    Main agent for code optimization
    """
    
    def __init__(self):
        self.python_optimizer = PythonOptimizer()
        self.java_optimizer = JavaOptimizer()
        logger.info("OptimizationAgent initialized")
    
    async def process(self, request: Request) -> Response:
        """Process optimization request"""
        start_time = time.time()
        
        try:
            if not request.code:
                raise ValueError("No code provided for optimization")
            
            # Select appropriate optimizer
            if request.language == Language.PYTHON:
                optimizations = self.python_optimizer.analyze_and_optimize(request.code)
            elif request.language == Language.JAVA:
                optimizations = self.java_optimizer.analyze_and_optimize(request.code)
            else:
                raise ValueError(f"Unsupported language: {request.language}")
            
            # Generate optimization report
            report = self._generate_report(optimizations)
            
            # Apply high-priority optimizations
            optimized_code = None
            if request.language == Language.PYTHON:
                high_priority = [o for o in optimizations if o.priority == "high"]
                if high_priority:
                    optimized_code = self.python_optimizer.apply_optimizations(
                        request.code, high_priority
                    )
            
            result = {
                "original_code": request.code,
                "optimizations": [self._optimization_to_dict(o) for o in optimizations],
                "optimized_code": optimized_code,
                "report": report,
                "summary": {
                    "total_optimizations": len(optimizations),
                    "high_priority": len([o for o in optimizations if o.priority == "high"]),
                    "medium_priority": len([o for o in optimizations if o.priority == "medium"]),
                    "low_priority": len([o for o in optimizations if o.priority == "low"])
                }
            }
            
            return Response(
                request_id=request.request_id,
                success=True,
                data=result,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Error in optimization: {str(e)}")
            return Response(
                request_id=request.request_id,
                success=False,
                data={},
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    def _optimization_to_dict(self, opt: Optimization) -> Dict[str, Any]:
        """Convert Optimization to dictionary"""
        return {
            "type": opt.type,
            "priority": opt.priority,
            "line": opt.line,
            "original_code": opt.original_code,
            "optimized_code": opt.optimized_code,
            "explanation": opt.explanation,
            "impact": opt.impact,
            "estimated_improvement": opt.estimated_improvement
        }
    
    def _generate_report(self, optimizations: List[Optimization]) -> str:
        """Generate optimization report"""
        
        if not optimizations:
            return "✅ Code is already well-optimized! No significant improvements found."
        
        report = []
        report.append("⚡ Optimization Report")
        report.append("=" * 60)
        
        # Group by priority
        high = [o for o in optimizations if o.priority == "high"]
        medium = [o for o in optimizations if o.priority == "medium"]
        low = [o for o in optimizations if o.priority == "low"]
        
        if high:
            report.append(f"\n🔴 HIGH PRIORITY ({len(high)} optimizations):")
            for i, opt in enumerate(high, 1):
                report.append(f"\n{i}. {opt.type}")
                if opt.line:
                    report.append(f"   Line: {opt.line}")
                report.append(f"   Impact: {opt.impact}")
                report.append(f"   Improvement: {opt.estimated_improvement}")
                report.append(f"   Suggestion: {opt.explanation}")
        
        if medium:
            report.append(f"\n🟡 MEDIUM PRIORITY ({len(medium)} optimizations):")
            for i, opt in enumerate(medium, 1):
                report.append(f"\n{i}. {opt.type} - {opt.explanation}")
        
        if low:
            report.append(f"\n🟢 LOW PRIORITY ({len(low)} optimizations):")
            for i, opt in enumerate(low, 1):
                report.append(f"{i}. {opt.type}")
        
        return '\n'.join(report)


# Example usage
if __name__ == "__main__":
    import asyncio
    from core import RequestType
    
    async def test_optimization():
        agent = OptimizationAgent()
        
        # Test code with optimization opportunities
        test_code = """
# Inefficient code example
result = []
for i in range(1000):
    result.append(i * 2)

# String concatenation in loop
text = ""
for word in words:
    text += word + " "

# Using list for membership testing
if item in [1, 2, 3, 4, 5]:
    print("Found")
"""
        
        request = Request(
            request_id="opt_001",
            request_type=RequestType.OPTIMIZE,
            language=Language.PYTHON,
            code=test_code
        )
        
        response = await agent.process(request)
        
        print("=== Optimization Report ===")
        print(response.data['report'])
        print(f"\nTotal optimizations found: {response.data['summary']['total_optimizations']}")
    
    asyncio.run(test_optimization())