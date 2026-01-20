"""
DSA Solver Agent
Solves Data Structures and Algorithms problems
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from core import Request, Response, Language
import time

logger = logging.getLogger(__name__)


@dataclass
class DSASolution:
    """DSA problem solution"""
    problem_type: str
    approach: str
    time_complexity: str
    space_complexity: str
    code: str
    explanation: str
    test_cases: List[Dict[str, Any]]


class DSASolver:
    """Solves common DSA problems"""
    
    def __init__(self):
        self.problem_patterns = self._initialize_patterns()
        self.solution_templates = self._initialize_templates()
    
    def _initialize_patterns(self) -> Dict[str, str]:
        """Initialize problem detection patterns"""
        return {
            "two_sum": r"two.*sum|find.*two.*numbers.*sum",
            "reverse_string": r"reverse.*string",
            "fibonacci": r"fibonacci",
            "factorial": r"factorial",
            "palindrome": r"palindrome",
            "binary_search": r"binary.*search",
            "merge_sort": r"merge.*sort",
            "quick_sort": r"quick.*sort",
            "linked_list": r"linked.*list",
            "binary_tree": r"binary.*tree|tree.*traversal",
            "graph": r"graph",
            "dynamic_programming": r"dynamic.*programming|dp|memoization",
            "sliding_window": r"sliding.*window|subarray",
            "two_pointers": r"two.*pointer",
            "stack": r"stack|valid.*parentheses",
            "queue": r"queue",
            "hash_map": r"hash.*map|hash.*table|dictionary",
            "heap": r"heap|priority.*queue",
            "dfs": r"depth.*first|dfs",
            "bfs": r"breadth.*first|bfs"
        }
    
    def _initialize_templates(self) -> Dict[str, Dict]:
        """Initialize solution templates"""
        return {
            "two_sum": {
                "python": """def two_sum(nums, target):
    \"\"\"
    Find two numbers that add up to target
    Time: O(n), Space: O(n)
    \"\"\"
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []""",
                "java": """public int[] twoSum(int[] nums, int target) {
    Map<Integer, Integer> seen = new HashMap<>();
    for (int i = 0; i < nums.length; i++) {
        int complement = target - nums[i];
        if (seen.containsKey(complement)) {
            return new int[] {seen.get(complement), i};
        }
        seen.put(nums[i], i);
    }
    return new int[] {};
}"""
            },
            "reverse_string": {
                "python": """def reverse_string(s):
    \"\"\"
    Reverse a string
    Time: O(n), Space: O(1) with list, O(n) for string
    \"\"\"
    # Method 1: Pythonic
    return s[::-1]
    
    # Method 2: Two pointers
    chars = list(s)
    left, right = 0, len(chars) - 1
    while left < right:
        chars[left], chars[right] = chars[right], chars[left]
        left += 1
        right -= 1
    return ''.join(chars)""",
                "java": """public String reverseString(String s) {
    char[] chars = s.toCharArray();
    int left = 0, right = chars.length - 1;
    while (left < right) {
        char temp = chars[left];
        chars[left] = chars[right];
        chars[right] = temp;
        left++;
        right--;
    }
    return new String(chars);
}"""
            },
            "fibonacci": {
                "python": """def fibonacci(n):
    \"\"\"
    Calculate nth Fibonacci number
    Time: O(n), Space: O(1) - iterative
    \"\"\"
    if n <= 1:
        return n
    
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

def fibonacci_recursive(n, memo={}):
    \"\"\"
    Fibonacci with memoization
    Time: O(n), Space: O(n)
    \"\"\"
    if n in memo:
        return memo[n]
    if n <= 1:
        return n
    memo[n] = fibonacci_recursive(n-1, memo) + fibonacci_recursive(n-2, memo)
    return memo[n]""",
                "java": """public int fibonacci(int n) {
    if (n <= 1) return n;
    int a = 0, b = 1;
    for (int i = 2; i <= n; i++) {
        int temp = a + b;
        a = b;
        b = temp;
    }
    return b;
}"""
            },
            "binary_search": {
                "python": """def binary_search(arr, target):
    \"\"\"
    Binary search in sorted array
    Time: O(log n), Space: O(1)
    \"\"\"
    left, right = 0, len(arr) - 1
    
    while left <= right:
        mid = left + (right - left) // 2
        
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    return -1  # Not found""",
                "java": """public int binarySearch(int[] arr, int target) {
    int left = 0, right = arr.length - 1;
    while (left <= right) {
        int mid = left + (right - left) / 2;
        if (arr[mid] == target) {
            return mid;
        } else if (arr[mid] < target) {
            left = mid + 1;
        } else {
            right = mid - 1;
        }
    }
    return -1;
}"""
            },
            "valid_parentheses": {
                "python": """def is_valid_parentheses(s):
    \"\"\"
    Check if parentheses are balanced
    Time: O(n), Space: O(n)
    \"\"\"
    stack = []
    mapping = {')': '(', '}': '{', ']': '['}
    
    for char in s:
        if char in mapping:
            top = stack.pop() if stack else '#'
            if mapping[char] != top:
                return False
        else:
            stack.append(char)
    
    return len(stack) == 0""",
                "java": """public boolean isValid(String s) {
    Stack<Character> stack = new Stack<>();
    Map<Character, Character> mapping = new HashMap<>();
    mapping.put(')', '(');
    mapping.put('}', '{');
    mapping.put(']', '[');
    
    for (char c : s.toCharArray()) {
        if (mapping.containsKey(c)) {
            char top = stack.isEmpty() ? '#' : stack.pop();
            if (top != mapping.get(c)) {
                return false;
            }
        } else {
            stack.push(c);
        }
    }
    return stack.isEmpty();
}"""
            },
            "linked_list_cycle": {
                "python": """def has_cycle(head):
    \"\"\"
    Detect cycle in linked list using Floyd's algorithm
    Time: O(n), Space: O(1)
    \"\"\"
    if not head or not head.next:
        return False
    
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow == fast:
            return True
    return False""",
                "java": """public boolean hasCycle(ListNode head) {
    if (head == null || head.next == null) {
        return false;
    }
    ListNode slow = head, fast = head;
    while (fast != null && fast.next != null) {
        slow = slow.next;
        fast = fast.next.next;
        if (slow == fast) {
            return true;
        }
    }
    return false;
}"""
            },
            "merge_sort": {
                "python": """def merge_sort(arr):
    \"\"\"
    Merge sort implementation
    Time: O(n log n), Space: O(n)
    \"\"\"
    if len(arr) <= 1:
        return arr
    
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    
    return merge(left, right)

def merge(left, right):
    result = []
    i = j = 0
    
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    
    result.extend(left[i:])
    result.extend(right[j:])
    return result""",
                "java": """public void mergeSort(int[] arr) {
    if (arr.length <= 1) return;
    int mid = arr.length / 2;
    int[] left = Arrays.copyOfRange(arr, 0, mid);
    int[] right = Arrays.copyOfRange(arr, mid, arr.length);
    mergeSort(left);
    mergeSort(right);
    merge(arr, left, right);
}

private void merge(int[] arr, int[] left, int[] right) {
    int i = 0, j = 0, k = 0;
    while (i < left.length && j < right.length) {
        if (left[i] <= right[j]) {
            arr[k++] = left[i++];
        } else {
            arr[k++] = right[j++];
        }
    }
    while (i < left.length) arr[k++] = left[i++];
    while (j < right.length) arr[k++] = right[j++];
}"""
            }
        }
    
    def solve_problem(self, problem_statement: str, language: Language) -> DSASolution:
        """Solve DSA problem based on statement"""
        
        # Detect problem type
        problem_type = self._detect_problem_type(problem_statement)
        
        # Get solution template
        if problem_type in self.solution_templates:
            lang_key = "python" if language == Language.PYTHON else "java"
            code = self.solution_templates[problem_type].get(lang_key, "# Solution not available")
            
            # Get problem details
            details = self._get_problem_details(problem_type)
            
            return DSASolution(
                problem_type=problem_type,
                approach=details["approach"],
                time_complexity=details["time_complexity"],
                space_complexity=details["space_complexity"],
                code=code,
                explanation=details["explanation"],
                test_cases=details["test_cases"]
            )
        else:
            # Generate generic solution
            return self._generate_generic_solution(problem_statement, language)
    
    def _detect_problem_type(self, statement: str) -> str:
        """Detect problem type from statement"""
        
        statement_lower = statement.lower()
        
        for problem_type, pattern in self.problem_patterns.items():
            if re.search(pattern, statement_lower):
                # Map to template key
                if problem_type == "stack" and "parenthes" in statement_lower:
                    return "valid_parentheses"
                elif problem_type == "linked_list" and "cycle" in statement_lower:
                    return "linked_list_cycle"
                else:
                    return problem_type
        
        return "generic"
    
    def _get_problem_details(self, problem_type: str) -> Dict[str, Any]:
        """Get detailed information about problem type"""
        
        details = {
            "two_sum": {
                "approach": "Use hash map to store seen numbers and their indices. For each number, check if its complement exists.",
                "time_complexity": "O(n) - single pass through array",
                "space_complexity": "O(n) - hash map storage",
                "explanation": "We use a hash map to achieve O(1) lookups. As we iterate, we check if target - current_number exists in our map.",
                "test_cases": [
                    {"input": "nums=[2,7,11,15], target=9", "output": "[0,1]"},
                    {"input": "nums=[3,2,4], target=6", "output": "[1,2]"}
                ]
            },
            "reverse_string": {
                "approach": "Use two pointers from start and end, swap characters moving towards center.",
                "time_complexity": "O(n) - visit each character once",
                "space_complexity": "O(1) - in-place modification",
                "explanation": "Two pointer technique allows us to reverse in-place with constant extra space.",
                "test_cases": [
                    {"input": "'hello'", "output": "'olleh'"},
                    {"input": "'Python'", "output": "'nohtyP'"}
                ]
            },
            "fibonacci": {
                "approach": "Iterative approach with two variables tracking previous two numbers.",
                "time_complexity": "O(n) - linear iteration",
                "space_complexity": "O(1) - constant space",
                "explanation": "Keep track of last two Fibonacci numbers and compute next. Much more efficient than recursive approach.",
                "test_cases": [
                    {"input": "n=5", "output": "5"},
                    {"input": "n=10", "output": "55"}
                ]
            },
            "binary_search": {
                "approach": "Divide and conquer - compare middle element and eliminate half of remaining elements.",
                "time_complexity": "O(log n) - halves search space each iteration",
                "space_complexity": "O(1) - constant space",
                "explanation": "By comparing with middle element, we can eliminate half the elements, leading to logarithmic time.",
                "test_cases": [
                    {"input": "arr=[1,2,3,4,5], target=3", "output": "2"},
                    {"input": "arr=[1,2,3,4,5], target=6", "output": "-1"}
                ]
            },
            "valid_parentheses": {
                "approach": "Use stack to match opening and closing brackets.",
                "time_complexity": "O(n) - single pass",
                "space_complexity": "O(n) - stack storage",
                "explanation": "Push opening brackets onto stack. For closing brackets, check if it matches stack top.",
                "test_cases": [
                    {"input": "'()'", "output": "True"},
                    {"input": "'([)]'", "output": "False"}
                ]
            },
            "linked_list_cycle": {
                "approach": "Floyd's cycle detection (tortoise and hare) - slow and fast pointers.",
                "time_complexity": "O(n) - at most 2n steps",
                "space_complexity": "O(1) - only two pointers",
                "explanation": "Fast pointer moves twice as fast. If there's a cycle, they'll eventually meet.",
                "test_cases": [
                    {"input": "1->2->3->2 (cycle)", "output": "True"},
                    {"input": "1->2->3->null", "output": "False"}
                ]
            },
            "merge_sort": {
                "approach": "Divide array recursively, then merge sorted halves.",
                "time_complexity": "O(n log n) - guaranteed",
                "space_complexity": "O(n) - auxiliary arrays",
                "explanation": "Recursively divide until single elements, then merge sorted arrays. Stable and efficient.",
                "test_cases": [
                    {"input": "[5,2,8,1,9]", "output": "[1,2,5,8,9]"},
                    {"input": "[3,1,4,1,5]", "output": "[1,1,3,4,5]"}
                ]
            }
        }
        
        return details.get(problem_type, {
            "approach": "Analyze problem and apply appropriate data structure/algorithm",
            "time_complexity": "O(n)",
            "space_complexity": "O(1)",
            "explanation": "Solve step by step",
            "test_cases": []
        })
    
    def _generate_generic_solution(self, statement: str, language: Language) -> DSASolution:
        """Generate generic solution framework"""
        
        if language == Language.PYTHON:
            code = f'''"""
{statement}
"""

def solve(input_data):
    """
    TODO: Implement solution
    """
    # Step 1: Parse input
    
    # Step 2: Process
    
    # Step 3: Return result
    pass

# Test cases
if __name__ == "__main__":
    # Add test cases
    pass
'''
        else:
            code = f'''/**
 * {statement}
 */
public class Solution {{
    public void solve() {{
        // TODO: Implement solution
    }}
    
    public static void main(String[] args) {{
        Solution sol = new Solution();
        // Add test cases
    }}
}}
'''
        
        return DSASolution(
            problem_type="generic",
            approach="Analyze problem requirements and implement solution",
            time_complexity="To be determined",
            space_complexity="To be determined",
            code=code,
            explanation="Generic solution template. Analyze the problem and implement accordingly.",
            test_cases=[]
        )


class DSASolverAgent:
    """
    Main agent for solving DSA problems
    """
    
    def __init__(self):
        self.solver = DSASolver()
        logger.info("DSASolverAgent initialized")
    
    async def process(self, request: Request) -> Response:
        """Process DSA problem solving request"""
        start_time = time.time()
        
        try:
            if not request.problem_statement:
                raise ValueError("No problem statement provided")
            
            # Solve problem
            solution = self.solver.solve_problem(
                request.problem_statement,
                request.language
            )
            
            # Generate explanation
            report = self._generate_report(solution)
            
            result = {
                "problem_type": solution.problem_type,
                "solution": {
                    "code": solution.code,
                    "approach": solution.approach,
                    "time_complexity": solution.time_complexity,
                    "space_complexity": solution.space_complexity,
                    "explanation": solution.explanation
                },
                "test_cases": solution.test_cases,
                "report": report
            }
            
            return Response(
                request_id=request.request_id,
                success=True,
                data=result,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Error in DSA solving: {str(e)}")
            return Response(
                request_id=request.request_id,
                success=False,
                data={},
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    def _generate_report(self, solution: DSASolution) -> str:
        """Generate solution report"""
        
        report = []
        report.append(f"🎯 Problem Type: {solution.problem_type.replace('_', ' ').title()}")
        report.append("=" * 60)
        report.append(f"\n📝 Approach:\n{solution.approach}")
        report.append(f"\n⏱️  Time Complexity: {solution.time_complexity}")
        report.append(f"💾 Space Complexity: {solution.space_complexity}")
        report.append(f"\n💡 Explanation:\n{solution.explanation}")
        
        if solution.test_cases:
            report.append("\n🧪 Test Cases:")
            for i, test in enumerate(solution.test_cases, 1):
                report.append(f"  {i}. Input: {test['input']} → Output: {test['output']}")
        
        return '\n'.join(report)


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_dsa_solver():
        agent = DSASolverAgent()
        
        test_problems = [
            "Find two numbers in an array that sum to a target value",
            "Reverse a string",
            "Check if parentheses in a string are valid",
            "Detect if a linked list has a cycle"
        ]
        
        for i, problem in enumerate(test_problems, 1):
            print(f"\n{'='*60}")
            print(f"Problem {i}: {problem}")
            print('='*60)
            
            request = Request(
                request_id=f"dsa_{i}",
                request_type=None,
                language=Language.PYTHON,
                problem_statement=problem
            )
            
            response = await agent.process(request)
            
            if response.success:
                print(response.data['report'])
                print(f"\n📄 Code:\n{response.data['solution']['code']}")
            else:
                print(f"Error: {response.error}")
    
    asyncio.run(test_dsa_solver())