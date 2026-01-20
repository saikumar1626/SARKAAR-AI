"""
Debug Agent
Identifies bugs, analyzes errors, and suggests fixes
"""

import re
import ast
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from core import Request, Response, Language
import time
import traceback

logger = logging.getLogger(__name__)


@dataclass
class Bug:
    """Represents a bug or error"""
    type: str
    severity: str  # critical, high, medium, low
    line: Optional[int]
    message: str
    context: str
    suggested_fix: str
    explanation: str


@dataclass
class ErrorAnalysis:
    """Complete error analysis"""
    has_errors: bool
    syntax_errors: List[Bug]
    runtime_errors: List[Bug]
    logic_errors: List[Bug]
    potential_bugs: List[Bug]
    fix_priority: List[Bug]


class PythonDebugger:
    """Advanced Python debugger"""
    
    def analyze_errors(self, code: str, error_message: Optional[str] = None) -> ErrorAnalysis:
        """Comprehensive error analysis"""
        syntax_errors = self._check_syntax_errors(code)
        runtime_errors = self._check_runtime_errors(code, error_message)
        logic_errors = self._check_logic_errors(code)
        potential_bugs = self._check_potential_bugs(code)
        
        all_bugs = syntax_errors + runtime_errors + logic_errors + potential_bugs
        
        # Sort by severity
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        fix_priority = sorted(all_bugs, key=lambda x: priority_order[x.severity])
        
        return ErrorAnalysis(
            has_errors=bool(syntax_errors or runtime_errors),
            syntax_errors=syntax_errors,
            runtime_errors=runtime_errors,
            logic_errors=logic_errors,
            potential_bugs=potential_bugs,
            fix_priority=fix_priority
        )
    
    def _check_syntax_errors(self, code: str) -> List[Bug]:
        """Check for syntax errors"""
        bugs = []
        
        try:
            ast.parse(code)
        except SyntaxError as e:
            bug = Bug(
                type="SyntaxError",
                severity="critical",
                line=e.lineno,
                message=str(e.msg),
                context=self._get_line_context(code, e.lineno),
                suggested_fix=self._suggest_syntax_fix(e, code),
                explanation=self._explain_syntax_error(e)
            )
            bugs.append(bug)
        except Exception as e:
            bug = Bug(
                type="ParsingError",
                severity="critical",
                line=None,
                message=str(e),
                context="",
                suggested_fix="Check code for structural issues",
                explanation="Unable to parse the code"
            )
            bugs.append(bug)
        
        return bugs
    
    def _check_runtime_errors(self, code: str, error_message: Optional[str]) -> List[Bug]:
        """Check for potential runtime errors"""
        bugs = []
        
        if error_message:
            # Parse provided error message
            bug = self._parse_error_message(error_message, code)
            if bug:
                bugs.append(bug)
        
        try:
            tree = ast.parse(code)
            
            # Check for common runtime error patterns
            for node in ast.walk(tree):
                # Division by zero
                if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
                    if isinstance(node.right, ast.Constant) and node.right.value == 0:
                        bugs.append(Bug(
                            type="ZeroDivisionError",
                            severity="high",
                            line=node.lineno,
                            message="Division by zero",
                            context=self._get_line_context(code, node.lineno),
                            suggested_fix="Add check: if denominator != 0: ...",
                            explanation="Dividing by zero causes a runtime error"
                        ))
                
                # Undefined variables (simplified check)
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    # This is a simplification - proper checking needs scope analysis
                    pass
                
                # Index out of range (accessing fixed indices)
                if isinstance(node, ast.Subscript):
                    if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, int):
                        if node.slice.value > 100:  # Suspicious high index
                            bugs.append(Bug(
                                type="PotentialIndexError",
                                severity="medium",
                                line=node.lineno,
                                message=f"Accessing high index: {node.slice.value}",
                                context=self._get_line_context(code, node.lineno),
                                suggested_fix="Check list length before accessing",
                                explanation="Accessing indices beyond list length causes IndexError"
                            ))
                
                # Attribute errors (calling methods on None)
                if isinstance(node, ast.Attribute):
                    # Check if accessing attribute on potential None
                    pass
        
        except:
            pass
        
        return bugs
    
    def _check_logic_errors(self, code: str) -> List[Bug]:
        """Check for logic errors"""
        bugs = []
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                # Always True/False conditions
                if isinstance(node, ast.If):
                    if isinstance(node.test, ast.Constant):
                        bugs.append(Bug(
                            type="AlwaysTrueCondition" if node.test.value else "AlwaysFalseCondition",
                            severity="high",
                            line=node.lineno,
                            message=f"Condition is always {node.test.value}",
                            context=self._get_line_context(code, node.lineno),
                            suggested_fix="Review the condition logic",
                            explanation="Constant conditions indicate logic errors"
                        ))
                
                # Unreachable code
                if isinstance(node, ast.FunctionDef):
                    for i, stmt in enumerate(node.body):
                        if isinstance(stmt, ast.Return) and i < len(node.body) - 1:
                            bugs.append(Bug(
                                type="UnreachableCode",
                                severity="medium",
                                line=node.body[i + 1].lineno,
                                message="Code after return statement is unreachable",
                                context=self._get_line_context(code, node.body[i + 1].lineno),
                                suggested_fix="Remove unreachable code or restructure logic",
                                explanation="Code after return never executes"
                            ))
                            break
                
                # Comparing with is instead of ==
                if isinstance(node, ast.Compare):
                    for op in node.ops:
                        if isinstance(op, (ast.Is, ast.IsNot)):
                            if isinstance(node.comparators[0], ast.Constant):
                                const_val = node.comparators[0].value
                                if not isinstance(const_val, (type(None), bool)):
                                    bugs.append(Bug(
                                        type="IncorrectComparison",
                                        severity="medium",
                                        line=node.lineno,
                                        message="Using 'is' for value comparison",
                                        context=self._get_line_context(code, node.lineno),
                                        suggested_fix="Use '==' for value comparison, 'is' for identity",
                                        explanation="'is' checks identity, not equality"
                                    ))
                
                # Mutable default arguments
                if isinstance(node, ast.FunctionDef):
                    for default in node.args.defaults:
                        if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                            bugs.append(Bug(
                                type="MutableDefaultArgument",
                                severity="high",
                                line=node.lineno,
                                message=f"Mutable default argument in function '{node.name}'",
                                context=self._get_line_context(code, node.lineno),
                                suggested_fix="Use None as default and create mutable in function body",
                                explanation="Mutable defaults are shared between calls"
                            ))
        
        except:
            pass
        
        return bugs
    
    def _check_potential_bugs(self, code: str) -> List[Bug]:
        """Check for potential bugs and anti-patterns"""
        bugs = []
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                # Missing return statement
                if isinstance(node, ast.FunctionDef):
                    has_return = any(isinstance(n, ast.Return) for n in ast.walk(node))
                    if not has_return and node.name != '__init__':
                        bugs.append(Bug(
                            type="MissingReturn",
                            severity="low",
                            line=node.lineno,
                            message=f"Function '{node.name}' has no return statement",
                            context=self._get_line_context(code, node.lineno),
                            suggested_fix="Add explicit return or None will be returned",
                            explanation="Functions without return implicitly return None"
                        ))
                
                # Empty exception handler
                if isinstance(node, ast.ExceptHandler):
                    if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                        bugs.append(Bug(
                            type="EmptyExceptHandler",
                            severity="medium",
                            line=node.lineno,
                            message="Empty exception handler",
                            context=self._get_line_context(code, node.lineno),
                            suggested_fix="Log the exception or handle it appropriately",
                            explanation="Silent exception handling hides errors"
                        ))
                
                # Using == with None
                if isinstance(node, ast.Compare):
                    for i, op in enumerate(node.ops):
                        if isinstance(op, (ast.Eq, ast.NotEq)):
                            if isinstance(node.comparators[i], ast.Constant) and node.comparators[i].value is None:
                                bugs.append(Bug(
                                    type="IncorrectNoneComparison",
                                    severity="low",
                                    line=node.lineno,
                                    message="Use 'is None' instead of '== None'",
                                    context=self._get_line_context(code, node.lineno),
                                    suggested_fix="Replace '== None' with 'is None'",
                                    explanation="'is' is the idiomatic way to check for None"
                                ))
        
        except:
            pass
        
        return bugs
    
    def _parse_error_message(self, error_message: str, code: str) -> Optional[Bug]:
        """Parse Python error message and create Bug object"""
        
        # Extract error type
        error_type_match = re.search(r'(\w+Error|\w+Exception)', error_message)
        error_type = error_type_match.group(1) if error_type_match else "UnknownError"
        
        # Extract line number
        line_match = re.search(r'line (\d+)', error_message)
        line = int(line_match.group(1)) if line_match else None
        
        # Generate fix based on error type
        suggested_fix = self._suggest_fix_for_error_type(error_type, error_message)
        explanation = self._explain_error_type(error_type)
        
        return Bug(
            type=error_type,
            severity="high",
            line=line,
            message=error_message,
            context=self._get_line_context(code, line) if line else "",
            suggested_fix=suggested_fix,
            explanation=explanation
        )
    
    def _suggest_syntax_fix(self, error: SyntaxError, code: str) -> str:
        """Suggest fix for syntax error"""
        msg = str(error.msg).lower()
        
        if 'invalid syntax' in msg:
            return "Check for missing colons, parentheses, or quotes"
        elif 'unexpected eof' in msg or 'eof while scanning' in msg:
            return "Check for unclosed parentheses, brackets, or quotes"
        elif 'unindent' in msg or 'indent' in msg:
            return "Fix indentation - use consistent spaces (4 spaces recommended)"
        elif 'keyword' in msg:
            return "Don't use reserved keywords as variable names"
        else:
            return "Review syntax near the error location"
    
    def _explain_syntax_error(self, error: SyntaxError) -> str:
        """Explain syntax error"""
        msg = str(error.msg).lower()
        
        if 'invalid syntax' in msg:
            return "Python couldn't understand the code structure at this location"
        elif 'eof' in msg:
            return "Python reached the end of file while expecting more code"
        elif 'indent' in msg:
            return "Python uses indentation to define code blocks - indentation is inconsistent"
        else:
            return "The code violates Python's syntax rules"
    
    def _suggest_fix_for_error_type(self, error_type: str, message: str) -> str:
        """Suggest fix based on error type"""
        fixes = {
            "NameError": "Check if variable is defined before use. Check spelling.",
            "TypeError": "Check if you're using compatible types in operations",
            "AttributeError": "Check if object has the attribute/method. Check for None values.",
            "IndexError": "Check list length before accessing. Use try-except or bounds checking.",
            "KeyError": "Check if key exists in dictionary. Use .get() method or try-except.",
            "ValueError": "Check if value is in expected format/range",
            "ZeroDivisionError": "Add check to ensure denominator is not zero",
            "ImportError": "Check if module is installed. Check import path.",
            "IndentationError": "Fix indentation - use consistent spacing (4 spaces)",
            "SyntaxError": "Check for typos, missing colons, or unclosed brackets"
        }
        
        return fixes.get(error_type, "Review the code at the error location")
    
    def _explain_error_type(self, error_type: str) -> str:
        """Explain what the error means"""
        explanations = {
            "NameError": "Attempting to use a variable that hasn't been defined",
            "TypeError": "Operation performed on incompatible types",
            "AttributeError": "Trying to access an attribute/method that doesn't exist",
            "IndexError": "Accessing a list/sequence with an invalid index",
            "KeyError": "Accessing a dictionary with a non-existent key",
            "ValueError": "Function received argument with wrong value",
            "ZeroDivisionError": "Attempting to divide by zero",
            "ImportError": "Unable to import the specified module",
            "IndentationError": "Incorrect indentation in code structure",
            "SyntaxError": "Code violates Python's syntax rules"
        }
        
        return explanations.get(error_type, "An error occurred during execution")
    
    def _get_line_context(self, code: str, line_num: Optional[int], context_lines: int = 2) -> str:
        """Get lines around the error for context"""
        if not line_num:
            return ""
        
        lines = code.split('\n')
        start = max(0, line_num - context_lines - 1)
        end = min(len(lines), line_num + context_lines)
        
        context = []
        for i in range(start, end):
            marker = ">>> " if i == line_num - 1 else "    "
            context.append(f"{marker}{i + 1}: {lines[i]}")
        
        return '\n'.join(context)
    
    def generate_fixed_code(self, code: str, bugs: List[Bug]) -> str:
        """Attempt to generate fixed code"""
        fixed_code = code
        
        # Sort bugs by line number (descending) to avoid offset issues
        sorted_bugs = sorted([b for b in bugs if b.line], key=lambda x: x.line, reverse=True)
        
        for bug in sorted_bugs:
            if bug.type == "MutableDefaultArgument":
                # Fix mutable default arguments
                fixed_code = self._fix_mutable_default(fixed_code, bug.line)
            elif bug.type == "IncorrectNoneComparison":
                # Fix None comparisons
                fixed_code = fixed_code.replace("== None", "is None").replace("!= None", "is not None")
            elif bug.type == "EmptyExceptHandler":
                # Add logging to empty except
                lines = fixed_code.split('\n')
                if bug.line and bug.line <= len(lines):
                    indent = len(lines[bug.line - 1]) - len(lines[bug.line - 1].lstrip())
                    lines.insert(bug.line, " " * (indent + 4) + "logging.warning('Exception caught')")
                    fixed_code = '\n'.join(lines)
        
        return fixed_code
    
    def _fix_mutable_default(self, code: str, line: int) -> str:
        """Fix mutable default argument"""
        lines = code.split('\n')
        if line and line <= len(lines):
            line_content = lines[line - 1]
            # Simple replacement (could be more sophisticated)
            line_content = re.sub(r'=\s*\[\]', '=None', line_content)
            line_content = re.sub(r'=\s*\{\}', '=None', line_content)
            lines[line - 1] = line_content
        return '\n'.join(lines)


class JavaDebugger:
    """Java error analyzer"""
    
    def analyze_errors(self, code: str, error_message: Optional[str] = None) -> ErrorAnalysis:
        """Analyze Java errors"""
        bugs = []
        
        # Check common Java errors
        bugs.extend(self._check_null_pointer(code))
        bugs.extend(self._check_array_bounds(code))
        bugs.extend(self._check_unclosed_resources(code))
        bugs.extend(self._check_exception_handling(code))
        
        if error_message:
            parsed_bug = self._parse_java_error(error_message, code)
            if parsed_bug:
                bugs.append(parsed_bug)
        
        # Categorize bugs
        syntax_errors = [b for b in bugs if 'Syntax' in b.type]
        runtime_errors = [b for b in bugs if b.severity in ['critical', 'high'] and 'Syntax' not in b.type]
        logic_errors = [b for b in bugs if b.severity == 'medium']
        potential_bugs = [b for b in bugs if b.severity == 'low']
        
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        fix_priority = sorted(bugs, key=lambda x: priority_order[x.severity])
        
        return ErrorAnalysis(
            has_errors=bool(syntax_errors or runtime_errors),
            syntax_errors=syntax_errors,
            runtime_errors=runtime_errors,
            logic_errors=logic_errors,
            potential_bugs=potential_bugs,
            fix_priority=fix_priority
        )
    
    def _check_null_pointer(self, code: str) -> List[Bug]:
        """Check for potential NullPointerException"""
        bugs = []
        
        # Look for method calls without null checks
        pattern = r'(\w+)\.(\w+)\('
        for i, line in enumerate(code.split('\n'), 1):
            matches = re.finditer(pattern, line)
            for match in matches:
                if 'if' not in line and 'null' not in line:
                    bugs.append(Bug(
                        type="PotentialNullPointerException",
                        severity="high",
                        line=i,
                        message=f"Method call on '{match.group(1)}' without null check",
                        context=line,
                        suggested_fix=f"Add null check: if ({match.group(1)} != null) {{...}}",
                        explanation="Calling methods on null objects causes NullPointerException"
                    ))
        
        return bugs
    
    def _check_array_bounds(self, code: str) -> List[Bug]:
        """Check for potential ArrayIndexOutOfBoundsException"""
        bugs = []
        
        pattern = r'(\w+)\[(\d+)\]'
        for i, line in enumerate(code.split('\n'), 1):
            matches = re.finditer(pattern, line)
            for match in matches:
                bugs.append(Bug(
                    type="PotentialArrayIndexOutOfBounds",
                    severity="medium",
                    line=i,
                    message=f"Fixed array index {match.group(2)}",
                    context=line,
                    suggested_fix="Check array length before accessing",
                    explanation="Accessing beyond array bounds causes exception"
                ))
        
        return bugs
    
    def _check_unclosed_resources(self, code: str) -> List[Bug]:
        """Check for unclosed resources"""
        bugs = []
        
        resources = ['FileInputStream', 'FileOutputStream', 'BufferedReader', 'Connection']
        
        for resource in resources:
            if resource in code and 'try-with-resources' not in code and '.close()' not in code:
                bugs.append(Bug(
                    type="UnclosedResource",
                    severity="high",
                    line=None,
                    message=f"{resource} may not be properly closed",
                    context="",
                    suggested_fix="Use try-with-resources statement",
                    explanation="Unclosed resources cause memory leaks"
                ))
        
        return bugs
    
    def _check_exception_handling(self, code: str) -> List[Bug]:
        """Check exception handling"""
        bugs = []
        
        # Empty catch blocks
        if re.search(r'catch\s*\([^)]+\)\s*\{\s*\}', code):
            bugs.append(Bug(
                type="EmptyCatchBlock",
                severity="medium",
                line=None,
                message="Empty catch block detected",
                context="",
                suggested_fix="Add proper exception handling or logging",
                explanation="Silent exception handling hides errors"
            ))
        
        return bugs
    
    def _parse_java_error(self, error_message: str, code: str) -> Optional[Bug]:
        """Parse Java error message"""
        
        error_types = {
            "NullPointerException": ("critical", "Add null checks before method calls"),
            "ArrayIndexOutOfBoundsException": ("high", "Check array bounds before accessing"),
            "ClassCastException": ("high", "Use instanceof before casting"),
            "NumberFormatException": ("medium", "Validate input format before parsing"),
            "IllegalArgumentException": ("medium", "Validate method arguments"),
        }
        
        for error_type, (severity, fix) in error_types.items():
            if error_type in error_message:
                line_match = re.search(r'at line (\d+)|:(\d+)', error_message)
                line = int(line_match.group(1) or line_match.group(2)) if line_match else None
                
                return Bug(
                    type=error_type,
                    severity=severity,
                    line=line,
                    message=error_message,
                    context="",
                    suggested_fix=fix,
                    explanation=f"Common Java error: {error_type}"
                )
        
        return None


class DebugAgent:
    """
    Main debugging agent
    Coordinates language-specific debuggers
    """
    
    def __init__(self):
        self.python_debugger = PythonDebugger()
        self.java_debugger = JavaDebugger()
        logger.info("DebugAgent initialized")
    
    async def process(self, request: Request) -> Response:
        """Process debug request"""
        start_time = time.time()
        
        try:
            if not request.code:
                raise ValueError("No code provided for debugging")
            
            error_message = request.context.get('error_message') if request.context else None
            
            # Select appropriate debugger
            if request.language == Language.PYTHON:
                analysis = self.python_debugger.analyze_errors(request.code, error_message)
            elif request.language == Language.JAVA:
                analysis = self.java_debugger.analyze_errors(request.code, error_message)
            else:
                raise ValueError(f"Unsupported language: {request.language}")
            
            # Generate debug report
            report = self._generate_debug_report(analysis)
            
            # Attempt to generate fixed code
            fixed_code = None
            if request.language == Language.PYTHON and analysis.fix_priority:
                fixed_code = self.python_debugger.generate_fixed_code(
                    request.code, 
                    analysis.fix_priority[:5]  # Fix top 5 issues
                )
            
            result = {
                "analysis": {
                    "has_errors": analysis.has_errors,
                    "total_issues": len(analysis.fix_priority),
                    "critical_issues": len([b for b in analysis.fix_priority if b.severity == 'critical']),
                    "syntax_errors": [self._bug_to_dict(b) for b in analysis.syntax_errors],
                    "runtime_errors": [self._bug_to_dict(b) for b in analysis.runtime_errors],
                    "logic_errors": [self._bug_to_dict(b) for b in analysis.logic_errors],
                    "potential_bugs": [self._bug_to_dict(b) for b in analysis.potential_bugs],
                },
                "fix_priority": [self._bug_to_dict(b) for b in analysis.fix_priority],
                "report": report,
                "fixed_code": fixed_code
            }
            
            return Response(
                request_id=request.request_id,
                success=True,
                data=result,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Error in debugging: {str(e)}")
            return Response(
                request_id=request.request_id,
                success=False,
                data={},
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    def _bug_to_dict(self, bug: Bug) -> Dict[str, Any]:
        """Convert Bug to dictionary"""
        return {
            "type": bug.type,
            "severity": bug.severity,
            "line": bug.line,
            "message": bug.message,
            "context": bug.context,
            "suggested_fix": bug.suggested_fix,
            "explanation": bug.explanation
        }
    
    def _generate_debug_report(self, analysis: ErrorAnalysis) -> str:
        """Generate human-readable debug report"""
        report = []
        
        if not analysis.has_errors and not analysis.logic_errors and not analysis.potential_bugs:
            return "✅ No errors or issues detected!"
        
        report.append("🐛 Debug Report")
        report.append("=" * 50)
        
        if analysis.syntax_errors:
            report.append(f"\n❌ SYNTAX ERRORS ({len(analysis.syntax_errors)}):")
            for bug in analysis.syntax_errors:
                report.append(f"\n  Line {bug.line}: {bug.type}")
                report.append(f"  Message: {bug.message}")
                report.append(f"  Fix: {bug.suggested_fix}")
        
        if analysis.runtime_errors:
            report.append(f"\n⚠️  RUNTIME ERRORS ({len(analysis.runtime_errors)}):")
            for bug in analysis.runtime_errors:
                line_str = f"Line {bug.line}" if bug.line else "Unknown line"
                report.append(f"\n  {line_str}: {bug.type}")
                report.append(f"  Message: {bug.message}")
                report.append(f"  Fix: {bug.suggested_fix}")
        
        if analysis.logic_errors:
            report.append(f"\n🔍 LOGIC ERRORS ({len(analysis.logic_errors)}):")
            for bug in analysis.logic_errors:
                line_str = f"Line {bug.line}" if bug.line else "Unknown line"
                report.append(f"\n  {line_str}: {bug.type}")
                report.append(f"  Message: {bug.message}")
                report.append(f"  Fix: {bug.suggested_fix}")
        
        if analysis.potential_bugs:
            report.append(f"\n💡 POTENTIAL ISSUES ({len(analysis.potential_bugs)}):")
            for bug in analysis.potential_bugs[:5]:  # Show top 5
                line_str = f"Line {bug.line}" if bug.line else "Unknown line"
                report.append(f"\n  {line_str}: {bug.type}")
                report.append(f"  Suggestion: {bug.suggested_fix}")
        
        return '\n'.join(report)


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_debug():
        agent = DebugAgent()
        
        # Test code with bugs
        buggy_code = """
def divide(a, b):
    return a / b  # No zero check

def process_list(items=[]):  # Mutable default
    items.append(1)
    return items

def check_value(x):
    if x = 5:  # Should be ==
        print("Five")

result = divide(10, 0)  # Will cause error
"""
        
        request = Request(
            request_id="debug_001",
            request_type=None,
            language=Language.PYTHON,
            code=buggy_code
        )
        
        response = await agent.process(request)
        
        print("=== Debug Report ===")
        print(response.data['report'])
        
        if response.data['fixed_code']:
            print("\n=== Suggested Fixed Code ===")
            print(response.data['fixed_code'])
    
    asyncio.run(test_debug())