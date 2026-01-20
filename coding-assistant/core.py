"""
CORE System - Central Orchestrator for Reasoning and Execution
Main orchestration layer for the AI Coding Assistant
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RequestType(Enum):
    """Types of requests the CORE can handle"""
    CODE_ANALYSIS = "code_analysis"
    DEBUG = "debug"
    EXPLAIN = "explain"
    OPTIMIZE = "optimize"
    GENERATE = "generate"
    DSA_SOLVE = "dsa_solve"
    TEST_GENERATE = "test_generate"


class Language(Enum):
    """Supported programming languages"""
    PYTHON = "python"
    JAVA = "java"
    JAVASCRIPT = "javascript"
    CPP = "cpp"


@dataclass
class Request:
    """Unified request structure"""
    request_id: str
    request_type: RequestType
    language: Language
    code: Optional[str] = None
    problem_statement: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class Response:
    """Unified response structure"""
    request_id: str
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    execution_time: float = 0.0


class MemoryStore:
    """
    Stores conversation history, code context, and user preferences
    """
    def __init__(self):
        self.conversation_history: List[Dict] = []
        self.code_context: Dict[str, Any] = {}
        self.user_preferences: Dict[str, Any] = {
            "preferred_language": "python",
            "code_style": "clean",
            "explanation_depth": "detailed"
        }
    
    def add_to_history(self, request: Request, response: Response):
        """Add interaction to history"""
        self.conversation_history.append({
            "request": request.__dict__,
            "response": response.__dict__,
            "timestamp": asyncio.get_event_loop().time()
        })
        
        # Keep only last 50 interactions
        if len(self.conversation_history) > 50:
            self.conversation_history = self.conversation_history[-50:]
    
    def get_relevant_context(self, request: Request) -> Dict[str, Any]:
        """Retrieve relevant context for current request"""
        context = {
            "recent_code": [],
            "recent_errors": [],
            "preferences": self.user_preferences
        }
        
        # Get last 5 code-related interactions
        for item in reversed(self.conversation_history[-10:]):
            if item["request"].get("code"):
                context["recent_code"].append({
                    "code": item["request"]["code"],
                    "language": item["request"]["language"]
                })
        
        return context
    
    def update_code_context(self, file_path: str, code: str, metadata: Dict):
        """Update current code context"""
        self.code_context[file_path] = {
            "code": code,
            "metadata": metadata,
            "last_updated": asyncio.get_event_loop().time()
        }


class IntentRouter:
    """
    Routes requests to appropriate agents based on intent classification
    """
    def __init__(self):
        self.agent_registry = {}
    
    def register_agent(self, request_type: RequestType, agent):
        """Register an agent for a specific request type"""
        self.agent_registry[request_type] = agent
        logger.info(f"Registered agent for {request_type.value}")
    
    async def route(self, request: Request) -> str:
        """
        Determine which agent(s) should handle the request
        Returns the agent key
        """
        return request.request_type.value
    
    def get_agent(self, agent_key: str):
        """Get agent by key"""
        for req_type, agent in self.agent_registry.items():
            if req_type.value == agent_key:
                return agent
        return None


class AgentCoordinator:
    """
    Coordinates multiple agents when complex tasks require multiple steps
    """
    def __init__(self, intent_router: IntentRouter):
        self.router = intent_router
    
    async def execute_pipeline(self, request: Request, pipeline: List[RequestType]) -> Dict[str, Any]:
        """
        Execute a pipeline of agents in sequence
        """
        results = {}
        current_context = request.context or {}
        
        for step_type in pipeline:
            agent = self.router.get_agent(step_type.value)
            if agent:
                step_request = Request(
                    request_id=f"{request.request_id}_{step_type.value}",
                    request_type=step_type,
                    language=request.language,
                    code=request.code,
                    problem_statement=request.problem_statement,
                    context=current_context
                )
                
                result = await agent.process(step_request)
                results[step_type.value] = result.data
                
                # Pass results to next step
                current_context.update(result.data)
        
        return results
    
    async def execute_parallel(self, request: Request, agent_types: List[RequestType]) -> Dict[str, Any]:
        """
        Execute multiple agents in parallel
        """
        tasks = []
        for agent_type in agent_types:
            agent = self.router.get_agent(agent_type.value)
            if agent:
                step_request = Request(
                    request_id=f"{request.request_id}_{agent_type.value}",
                    request_type=agent_type,
                    language=request.language,
                    code=request.code,
                    problem_statement=request.problem_statement,
                    context=request.context
                )
                tasks.append(agent.process(step_request))
        
        results = await asyncio.gather(*tasks)
        return {agent_types[i].value: results[i].data for i in range(len(results))}


class CORE:
    """
    Central Orchestrator for Reasoning and Execution
    Main entry point for all AI assistant operations
    """
    
    def __init__(self):
        self.memory = MemoryStore()
        self.intent_router = IntentRouter()
        self.coordinator = AgentCoordinator(self.intent_router)
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_execution_time": 0.0
        }
        logger.info("CORE system initialized")
    
    def register_agent(self, request_type: RequestType, agent):
        """Register an agent with the CORE"""
        self.intent_router.register_agent(request_type, agent)
    
    async def process_request(self, request: Request) -> Response:
        """
        Main entry point for processing requests
        """
        import time
        start_time = time.time()
        
        self.metrics["total_requests"] += 1
        
        try:
            # Add context from memory
            context = self.memory.get_relevant_context(request)
            if request.context:
                request.context.update(context)
            else:
                request.context = context
            
            # Route to appropriate agent
            agent_key = await self.intent_router.route(request)
            agent = self.intent_router.get_agent(agent_key)
            
            if not agent:
                raise ValueError(f"No agent registered for {request.request_type}")
            
            # Execute agent
            response = await agent.process(request)
            
            # Store in memory
            self.memory.add_to_history(request, response)
            
            # Update metrics
            if response.success:
                self.metrics["successful_requests"] += 1
            else:
                self.metrics["failed_requests"] += 1
            
            execution_time = time.time() - start_time
            response.execution_time = execution_time
            
            # Update average execution time
            total = self.metrics["total_requests"]
            current_avg = self.metrics["avg_execution_time"]
            self.metrics["avg_execution_time"] = (current_avg * (total - 1) + execution_time) / total
            
            logger.info(f"Request {request.request_id} completed in {execution_time:.2f}s")
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing request {request.request_id}: {str(e)}")
            self.metrics["failed_requests"] += 1
            
            return Response(
                request_id=request.request_id,
                success=False,
                data={},
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    async def process_complex_request(self, request: Request, pipeline: List[RequestType]) -> Response:
        """
        Process complex requests that require multiple agents
        """
        import time
        start_time = time.time()
        
        try:
            results = await self.coordinator.execute_pipeline(request, pipeline)
            
            response = Response(
                request_id=request.request_id,
                success=True,
                data=results,
                execution_time=time.time() - start_time
            )
            
            self.memory.add_to_history(request, response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error in complex request {request.request_id}: {str(e)}")
            return Response(
                request_id=request.request_id,
                success=False,
                data={},
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get system metrics"""
        return self.metrics.copy()
    
    def get_memory_snapshot(self) -> Dict[str, Any]:
        """Get current memory state"""
        return {
            "conversation_history_size": len(self.memory.conversation_history),
            "code_context_files": list(self.memory.code_context.keys()),
            "user_preferences": self.memory.user_preferences
        }


# Example usage and testing
if __name__ == "__main__":
    async def test_core():
        core = CORE()
        
        # Create a dummy agent for testing
        class DummyAgent:
            async def process(self, request: Request) -> Response:
                return Response(
                    request_id=request.request_id,
                    success=True,
                    data={"message": "Processed successfully"}
                )
        
        # Register dummy agent
        core.register_agent(RequestType.CODE_ANALYSIS, DummyAgent())
        
        # Create test request
        request = Request(
            request_id="test_001",
            request_type=RequestType.CODE_ANALYSIS,
            language=Language.PYTHON,
            code="def hello(): print('Hello')"
        )
        
        # Process request
        response = await core.process_request(request)
        
        print(f"Response: {response}")
        print(f"Metrics: {core.get_metrics()}")
    
    # Run test
    asyncio.run(test_core())