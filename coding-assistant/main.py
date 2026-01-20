"""
Main Integration - Advanced Coding Assistant
Integrates all agents with CORE system
"""

import asyncio
import logging
from typing import Dict, Any, Optional
import uuid

# Import CORE
from core import CORE, Request, Response, RequestType, Language

# Import all agents
from code_analysis_agent import CodeAnalysisAgent
from debug_agent import DebugAgent
from code_generation_agent import CodeGenerationAgent
from optimization_agent import OptimizationAgent
from explanation_agent import ExplanationAgent
from dsa_solver_agent import DSASolverAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CodingAssistant:
    """
    Advanced AI Coding Assistant
    Integrates all agents through CORE orchestration system
    """
    
    def __init__(self):
        """Initialize the coding assistant"""
        logger.info("Initializing Advanced Coding Assistant...")
        
        # Initialize CORE
        self.core = CORE()
        
        # Initialize all agents
        self._initialize_agents()
        
        logger.info("✅ Coding Assistant initialized successfully!")
        logger.info(f"Registered agents: {len(self.core.intent_router.agent_registry)}")
    
    def _initialize_agents(self):
        """Initialize and register all agents with CORE"""
        
        # Code Analysis Agent
        code_analysis_agent = CodeAnalysisAgent()
        self.core.register_agent(RequestType.CODE_ANALYSIS, code_analysis_agent)
        
        # Debug Agent
        debug_agent = DebugAgent()
        self.core.register_agent(RequestType.DEBUG, debug_agent)
        
        # Code Generation Agent
        code_gen_agent = CodeGenerationAgent()
        self.core.register_agent(RequestType.GENERATE, code_gen_agent)
        
        # Optimization Agent
        optimization_agent = OptimizationAgent()
        self.core.register_agent(RequestType.OPTIMIZE, optimization_agent)
        
        # Explanation Agent
        explanation_agent = ExplanationAgent()
        self.core.register_agent(RequestType.EXPLAIN, explanation_agent)
        
        # DSA Solver Agent
        dsa_agent = DSASolverAgent()
        self.core.register_agent(RequestType.DSA_SOLVE, dsa_agent)
        
        logger.info("All agents registered with CORE")
    
    # === HIGH-LEVEL API METHODS ===
    
    async def analyze_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """
        Analyze code for quality, complexity, and issues
        
        Args:
            code: Source code to analyze
            language: Programming language (python, java)
        
        Returns:
            Analysis results with metrics, insights, and quality scores
        """
        request = Request(
            request_id=self._generate_request_id(),
            request_type=RequestType.CODE_ANALYSIS,
            language=Language[language.upper()],
            code=code
        )
        
        response = await self.core.process_request(request)
        return self._format_response(response)
    
    async def debug_code(self, code: str, language: str = "python", 
                        error_message: Optional[str] = None) -> Dict[str, Any]:
        """
        Debug code and suggest fixes
        
        Args:
            code: Source code with potential bugs
            language: Programming language
            error_message: Optional error message if code threw an error
        
        Returns:
            Debug analysis with bug reports and suggested fixes
        """
        context = {"error_message": error_message} if error_message else None
        
        request = Request(
            request_id=self._generate_request_id(),
            request_type=RequestType.DEBUG,
            language=Language[language.upper()],
            code=code,
            context=context
        )
        
        response = await self.core.process_request(request)
        return self._format_response(response)
    
    async def generate_code(self, description: str, language: str = "python") -> Dict[str, Any]:
        """
        Generate code from natural language description
        
        Args:
            description: Natural language description of desired code
            language: Target programming language
        
        Returns:
            Generated code with metadata
        """
        request = Request(
            request_id=self._generate_request_id(),
            request_type=RequestType.GENERATE,
            language=Language[language.upper()],
            problem_statement=description
        )
        
        response = await self.core.process_request(request)
        return self._format_response(response)
    
    async def optimize_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """
        Optimize code for better performance
        
        Args:
            code: Source code to optimize
            language: Programming language
        
        Returns:
            Optimization suggestions and optimized code
        """
        request = Request(
            request_id=self._generate_request_id(),
            request_type=RequestType.OPTIMIZE,
            language=Language[language.upper()],
            code=code
        )
        
        response = await self.core.process_request(request)
        return self._format_response(response)
    
    async def explain_code(self, code: str, language: str = "python", 
                          detail_level: str = "medium") -> Dict[str, Any]:
        """
        Explain what code does in simple terms
        
        Args:
            code: Source code to explain
            language: Programming language
            detail_level: Level of detail (low, medium, high)
        
        Returns:
            Comprehensive code explanation
        """
        request = Request(
            request_id=self._generate_request_id(),
            request_type=RequestType.EXPLAIN,
            language=Language[language.upper()],
            code=code,
            context={"detail_level": detail_level}
        )
        
        response = await self.core.process_request(request)
        return self._format_response(response)
    
    async def solve_dsa_problem(self, problem: str, language: str = "python") -> Dict[str, Any]:
        """
        Solve a Data Structures & Algorithms problem
        
        Args:
            problem: Problem statement
            language: Target programming language
        
        Returns:
            Solution with code, explanation, and complexity analysis
        """
        request = Request(
            request_id=self._generate_request_id(),
            request_type=RequestType.DSA_SOLVE,
            language=Language[language.upper()],
            problem_statement=problem
        )
        
        response = await self.core.process_request(request)
        return self._format_response(response)
    
    async def comprehensive_review(self, code: str, language: str = "python") -> Dict[str, Any]:
        """
        Perform comprehensive code review (analysis + debug + optimization)
        
        Args:
            code: Source code to review
            language: Programming language
        
        Returns:
            Complete review with all analyses
        """
        pipeline = [
            RequestType.CODE_ANALYSIS,
            RequestType.DEBUG,
            RequestType.OPTIMIZE
        ]
        
        request = Request(
            request_id=self._generate_request_id(),
            request_type=RequestType.CODE_ANALYSIS,  # Primary type
            language=Language[language.upper()],
            code=code
        )
        
        response = await self.core.process_complex_request(request, pipeline)
        return self._format_response(response)
    
    # === UTILITY METHODS ===
    
    def _generate_request_id(self) -> str:
        """Generate unique request ID"""
        return f"req_{uuid.uuid4().hex[:8]}"
    
    def _format_response(self, response: Response) -> Dict[str, Any]:
        """Format response for user consumption"""
        return {
            "success": response.success,
            "data": response.data,
            "error": response.error,
            "execution_time": response.execution_time,
            "request_id": response.request_id
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get system metrics"""
        return self.core.get_metrics()
    
    def get_memory_info(self) -> Dict[str, Any]:
        """Get memory system information"""
        return self.core.get_memory_snapshot()


# === DEMONSTRATION AND TESTING ===

async def demo():
    """Demonstration of the coding assistant capabilities"""
    
    print("=" * 80)
    print("🤖 ADVANCED AI CODING ASSISTANT - DEMONSTRATION")
    print("=" * 80)
    
    # Initialize assistant
    assistant = CodingAssistant()
    
    # Test code
    test_code = """
def calculate_sum(numbers):
    result = 0
    for num in numbers:
        result = result + num
    return result

def find_max(arr):
    if len(arr) == 0:
        return None
    max_val = arr[0]
    for i in range(1, len(arr)):
        if arr[i] > max_val:
            max_val = arr[i]
    return max_val
"""
    
    print("\n" + "=" * 80)
    print("TEST 1: CODE ANALYSIS")
    print("=" * 80)
    result = await assistant.analyze_code(test_code)
    if result['success']:
        print(f"✅ Analysis completed in {result['execution_time']:.2f}s")
        print(f"Code Quality Score: {result['data']['analysis']['code_quality']['score']}")
        print("Insights:")
        for insight in result['data']['insights']:
            print(f"  • {insight}")
    
    print("\n" + "=" * 80)
    print("TEST 2: CODE EXPLANATION")
    print("=" * 80)
    result = await assistant.explain_code(test_code)
    if result['success']:
        print(f"✅ Explanation generated in {result['execution_time']:.2f}s")
        print(f"\nOverview: {result['data']['explanation']['overview']}")
        print(f"\nKey Concepts: {', '.join(result['data']['explanation']['key_concepts'])}")
    
    print("\n" + "=" * 80)
    print("TEST 3: CODE OPTIMIZATION")
    print("=" * 80)
    result = await assistant.optimize_code(test_code)
    if result['success']:
        print(f"✅ Optimization analysis completed in {result['execution_time']:.2f}s")
        print(result['data']['report'])
    
    print("\n" + "=" * 80)
    print("TEST 4: CODE GENERATION")
    print("=" * 80)
    result = await assistant.generate_code(
        "Create a function to check if a number is prime"
    )
    if result['success']:
        print(f"✅ Code generated in {result['execution_time']:.2f}s")
        print("\nGenerated Code:")
        print(result['data']['generated_code'])
    
    print("\n" + "=" * 80)
    print("TEST 5: DSA PROBLEM SOLVING")
    print("=" * 80)
    result = await assistant.solve_dsa_problem(
        "Find two numbers in an array that sum to a target value"
    )
    if result['success']:
        print(f"✅ Solution found in {result['execution_time']:.2f}s")
        print(result['data']['report'])
    
    print("\n" + "=" * 80)
    print("TEST 6: DEBUG CODE")
    print("=" * 80)
    buggy_code = """
def divide(a, b):
    return a / b

result = divide(10, 0)
"""
    result = await assistant.debug_code(buggy_code)
    if result['success']:
        print(f"✅ Debug analysis completed in {result['execution_time']:.2f}s")
        print(result['data']['report'])
    
    # System metrics
    print("\n" + "=" * 80)
    print("📊 SYSTEM METRICS")
    print("=" * 80)
    metrics = assistant.get_metrics()
    print(f"Total Requests: {metrics['total_requests']}")
    print(f"Successful: {metrics['successful_requests']}")
    print(f"Failed: {metrics['failed_requests']}")
    print(f"Average Execution Time: {metrics['avg_execution_time']:.3f}s")
    
    print("\n" + "=" * 80)
    print("✨ DEMONSTRATION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    # Run demonstration
    asyncio.run(demo())