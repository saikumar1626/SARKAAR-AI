"""
Code Generation Agent
Generates code from natural language descriptions
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from core import Request, Response, Language
import time
import re

logger = logging.getLogger(__name__)


@dataclass
class CodeTemplate:
    """Template for code generation"""
    name: str
    description: str
    language: Language
    template: str
    parameters: List[str]


class PythonCodeGenerator:
    """Generates Python code from specifications"""
    
    def __init__(self):
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, CodeTemplate]:
        """Load code templates"""
        return {
            "function": CodeTemplate(
                name="function",
                description="Basic function template",
                language=Language.PYTHON,
                template="""def {function_name}({parameters}):
    \"\"\"
    {docstring}
    \"\"\"
    {body}
    return {return_value}""",
                parameters=["function_name", "parameters", "docstring", "body", "return_value"]
            ),
            "class": CodeTemplate(
                name="class",
                description="Basic class template",
                language=Language.PYTHON,
                template="""class {class_name}:
    \"\"\"
    {docstring}
    \"\"\"
    
    def __init__(self, {init_parameters}):
        {init_body}
    
    {methods}""",
                parameters=["class_name", "docstring", "init_parameters", "init_body", "methods"]
            ),
            "api_client": CodeTemplate(
                name="api_client",
                description="REST API client",
                language=Language.PYTHON,
                template="""import requests
from typing import Dict, Any, Optional

class {class_name}:
    \"\"\"REST API Client for {api_name}\"\"\"
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url
        self.api_key = api_key
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({{'Authorization': f'Bearer {{api_key}}'}})
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        response = self.session.get(f'{{self.base_url}}/{{endpoint}}', params=params)
        response.raise_for_status()
        return response.json()
    
    def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        response = self.session.post(f'{{self.base_url}}/{{endpoint}}', json=data)
        response.raise_for_status()
        return response.json()""",
                parameters=["class_name", "api_name"]
            ),
            "data_processor": CodeTemplate(
                name="data_processor",
                description="Data processing pipeline",
                language=Language.PYTHON,
                template="""import pandas as pd
from typing import List, Dict, Any

class {class_name}:
    \"\"\"Data processor for {description}\"\"\"
    
    def __init__(self, data_source: str):
        self.data_source = data_source
        self.data = None
    
    def load_data(self) -> pd.DataFrame:
        \"\"\"Load data from source\"\"\"
        self.data = pd.read_csv(self.data_source)
        return self.data
    
    def clean_data(self) -> pd.DataFrame:
        \"\"\"Clean and preprocess data\"\"\"
        # Remove duplicates
        self.data = self.data.drop_duplicates()
        # Handle missing values
        self.data = self.data.fillna(self.data.mean(numeric_only=True))
        return self.data
    
    def transform_data(self) -> pd.DataFrame:
        \"\"\"Apply transformations\"\"\"
        # Add your transformations here
        return self.data
    
    def get_summary(self) -> Dict[str, Any]:
        \"\"\"Get data summary\"\"\"
        return {{
            'shape': self.data.shape,
            'columns': list(self.data.columns),
            'dtypes': self.data.dtypes.to_dict(),
            'stats': self.data.describe().to_dict()
        }}""",
                parameters=["class_name", "description"]
            )
        }
    
    def generate_from_description(self, description: str) -> str:
        """Generate code from natural language description"""
        
        description_lower = description.lower()
        
        # Detect intent
        if any(word in description_lower for word in ['api', 'rest', 'http', 'endpoint']):
            return self._generate_api_code(description)
        elif any(word in description_lower for word in ['data', 'csv', 'dataframe', 'process']):
            return self._generate_data_processing_code(description)
        elif any(word in description_lower for word in ['class', 'object']):
            return self._generate_class_code(description)
        elif any(word in description_lower for word in ['function', 'method']):
            return self._generate_function_code(description)
        elif any(word in description_lower for word in ['algorithm', 'sort', 'search']):
            return self._generate_algorithm_code(description)
        else:
            return self._generate_generic_code(description)
    
    def _generate_api_code(self, description: str) -> str:
        """Generate API client code"""
        
        # Extract API name
        api_name_match = re.search(r'for (\w+)', description)
        api_name = api_name_match.group(1) if api_name_match else "API"
        
        class_name = f"{api_name.title()}Client"
        
        template = self.templates["api_client"]
        code = template.template.format(
            class_name=class_name,
            api_name=api_name
        )
        
        return code
    
    def _generate_data_processing_code(self, description: str) -> str:
        """Generate data processing code"""
        
        class_name = "DataProcessor"
        desc = description.split("for")[-1].strip() if "for" in description else "data processing"
        
        template = self.templates["data_processor"]
        code = template.template.format(
            class_name=class_name,
            description=desc
        )
        
        return code
    
    def _generate_class_code(self, description: str) -> str:
        """Generate class code"""
        
        # Extract class name
        class_match = re.search(r'class (\w+)', description, re.IGNORECASE)
        class_name = class_match.group(1) if class_match else "MyClass"
        
        # Extract attributes
        attr_pattern = r'with (?:attributes?|properties) ([\w, ]+)'
        attr_match = re.search(attr_pattern, description, re.IGNORECASE)
        attributes = attr_match.group(1).split(',') if attr_match else ['value']
        attributes = [attr.strip() for attr in attributes]
        
        # Generate init parameters
        init_params = ', '.join(attributes)
        init_body = '\n        '.join([f'self.{attr} = {attr}' for attr in attributes])
        
        # Generate basic methods
        methods = []
        for attr in attributes:
            methods.append(f"""    def get_{attr}(self):
        return self.{attr}
    
    def set_{attr}(self, value):
        self.{attr} = value""")
        
        template = self.templates["class"]
        code = template.template.format(
            class_name=class_name,
            docstring=f"Class representing {class_name}",
            init_parameters=init_params,
            init_body=init_body,
            methods='\n\n'.join(methods)
        )
        
        return code
    
    def _generate_function_code(self, description: str) -> str:
        """Generate function code"""
        
        # Extract function name
        func_match = re.search(r'function (?:called |named )?(\w+)', description, re.IGNORECASE)
        func_name = func_match.group(1) if func_match else "my_function"
        
        # Extract parameters
        param_pattern = r'(?:takes?|with parameters?) ([\w, ]+)'
        param_match = re.search(param_pattern, description, re.IGNORECASE)
        if param_match:
            params = param_match.group(1).split(',')
            params = ', '.join([p.strip() for p in params])
        else:
            params = "x"
        
        # Determine functionality
        body = "# TODO: Implement function logic\n    pass"
        return_value = "result"
        
        if 'sum' in description.lower() or 'add' in description.lower():
            if ',' in params:
                param_list = [p.strip() for p in params.split(',')]
                body = f"result = {' + '.join(param_list)}"
            else:
                body = f"result = sum({params})"
        elif 'calculate' in description.lower():
            body = "# Perform calculation\n    result = 0  # Placeholder"
        elif 'filter' in description.lower():
            body = f"result = [item for item in {params.split(',')[0].strip()} if condition]"
        
        template = self.templates["function"]
        code = template.template.format(
            function_name=func_name,
            parameters=params,
            docstring=description,
            body=body,
            return_value=return_value
        )
        
        return code
    
    def _generate_algorithm_code(self, description: str) -> str:
        """Generate algorithm code"""
        
        if 'bubble sort' in description.lower():
            return self._generate_bubble_sort()
        elif 'binary search' in description.lower():
            return self._generate_binary_search()
        elif 'quicksort' in description.lower() or 'quick sort' in description.lower():
            return self._generate_quicksort()
        elif 'merge sort' in description.lower():
            return self._generate_merge_sort()
        else:
            return "# Algorithm implementation\n# Please specify the algorithm"
    
    def _generate_bubble_sort(self) -> str:
        return """def bubble_sort(arr):
    \"\"\"
    Bubble sort algorithm
    Time Complexity: O(n²)
    Space Complexity: O(1)
    \"\"\"
    n = len(arr)
    for i in range(n):
        swapped = False
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                swapped = True
        if not swapped:
            break
    return arr"""
    
    def _generate_binary_search(self) -> str:
        return """def binary_search(arr, target):
    \"\"\"
    Binary search algorithm
    Time Complexity: O(log n)
    Space Complexity: O(1)
    \"\"\"
    left, right = 0, len(arr) - 1
    
    while left <= right:
        mid = (left + right) // 2
        
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    return -1  # Not found"""
    
    def _generate_quicksort(self) -> str:
        return """def quicksort(arr):
    \"\"\"
    Quicksort algorithm
    Time Complexity: O(n log n) average, O(n²) worst
    Space Complexity: O(log n)
    \"\"\"
    if len(arr) <= 1:
        return arr
    
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    
    return quicksort(left) + middle + quicksort(right)"""
    
    def _generate_merge_sort(self) -> str:
        return """def merge_sort(arr):
    \"\"\"
    Merge sort algorithm
    Time Complexity: O(n log n)
    Space Complexity: O(n)
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
    return result"""
    
    def _generate_generic_code(self, description: str) -> str:
        """Generate generic code based on description"""
        
        code = f'''"""
{description}
"""

def main():
    # TODO: Implement based on description
    pass

if __name__ == "__main__":
    main()
'''
        return code


class JavaCodeGenerator:
    """Generates Java code from specifications"""
    
    def generate_from_description(self, description: str) -> str:
        """Generate Java code from description"""
        
        description_lower = description.lower()
        
        if 'class' in description_lower:
            return self._generate_class_code(description)
        elif 'algorithm' in description_lower or 'sort' in description_lower:
            return self._generate_algorithm_code(description)
        else:
            return self._generate_generic_code(description)
    
    def _generate_class_code(self, description: str) -> str:
        """Generate Java class"""
        
        class_match = re.search(r'class (\w+)', description, re.IGNORECASE)
        class_name = class_match.group(1) if class_match else "MyClass"
        
        return f"""public class {class_name} {{
    // Instance variables
    
    /**
     * Constructor for {class_name}
     */
    public {class_name}() {{
        // Initialize
    }}
    
    /**
     * Main method
     */
    public static void main(String[] args) {{
        {class_name} obj = new {class_name}();
    }}
}}"""
    
    def _generate_algorithm_code(self, description: str) -> str:
        """Generate algorithm code"""
        
        if 'bubble sort' in description.lower():
            return """public class BubbleSort {
    public static void bubbleSort(int[] arr) {
        int n = arr.length;
        for (int i = 0; i < n - 1; i++) {
            boolean swapped = false;
            for (int j = 0; j < n - i - 1; j++) {
                if (arr[j] > arr[j + 1]) {
                    int temp = arr[j];
                    arr[j] = arr[j + 1];
                    arr[j + 1] = temp;
                    swapped = true;
                }
            }
            if (!swapped) break;
        }
    }
    
    public static void main(String[] args) {
        int[] arr = {64, 34, 25, 12, 22, 11, 90};
        bubbleSort(arr);
        System.out.println("Sorted array: " + Arrays.toString(arr));
    }
}"""
        elif 'binary search' in description.lower():
            return """public class BinarySearch {
    public static int binarySearch(int[] arr, int target) {
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
        
        return -1; // Not found
    }
    
    public static void main(String[] args) {
        int[] arr = {2, 3, 4, 10, 40};
        int target = 10;
        int result = binarySearch(arr, target);
        System.out.println("Element found at index: " + result);
    }
}"""
        else:
            return "// Algorithm implementation"
    
    def _generate_generic_code(self, description: str) -> str:
        """Generate generic Java code"""
        
        return f"""/**
 * {description}
 */
public class Main {{
    public static void main(String[] args) {{
        // TODO: Implement based on description
    }}
}}"""


class CodeGenerationAgent:
    """
    Main agent for code generation
    Generates code from natural language descriptions
    """
    
    def __init__(self):
        self.python_generator = PythonCodeGenerator()
        self.java_generator = JavaCodeGenerator()
        logger.info("CodeGenerationAgent initialized")
    
    async def process(self, request: Request) -> Response:
        """Process code generation request"""
        start_time = time.time()
        
        try:
            if not request.problem_statement:
                raise ValueError("No problem statement provided for code generation")
            
            # Select appropriate generator
            if request.language == Language.PYTHON:
                generated_code = self.python_generator.generate_from_description(
                    request.problem_statement
                )
            elif request.language == Language.JAVA:
                generated_code = self.java_generator.generate_from_description(
                    request.problem_statement
                )
            else:
                raise ValueError(f"Unsupported language: {request.language}")
            
            # Add metadata
            metadata = self._generate_metadata(request.problem_statement, generated_code)
            
            result = {
                "generated_code": generated_code,
                "language": request.language.value,
                "description": request.problem_statement,
                "metadata": metadata
            }
            
            return Response(
                request_id=request.request_id,
                success=True,
                data=result,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Error in code generation: {str(e)}")
            return Response(
                request_id=request.request_id,
                success=False,
                data={},
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    def _generate_metadata(self, description: str, code: str) -> Dict[str, Any]:
        """Generate metadata about generated code"""
        
        lines = code.split('\n')
        
        return {
            "lines_of_code": len([l for l in lines if l.strip() and not l.strip().startswith('#')]),
            "has_docstring": '"""' in code or "'''" in code,
            "estimated_complexity": self._estimate_complexity(code),
            "suggested_improvements": self._suggest_improvements(description, code)
        }
    
    def _estimate_complexity(self, code: str) -> str:
        """Estimate time complexity"""
        
        nested_loops = code.count('for') + code.count('while')
        
        if nested_loops == 0:
            return "O(1) - Constant time"
        elif nested_loops == 1:
            return "O(n) - Linear time"
        elif nested_loops == 2:
            return "O(n²) - Quadratic time"
        else:
            return f"O(n^{nested_loops}) - Polynomial time"
    
    def _suggest_improvements(self, description: str, code: str) -> List[str]:
        """Suggest code improvements"""
        
        suggestions = []
        
        if '"""' not in code and "'''" not in code:
            suggestions.append("Add docstrings to document the code")
        
        if 'def ' in code and 'return' not in code:
            suggestions.append("Consider adding return value for better usability")
        
        if code.count('for') > 1:
            suggestions.append("Multiple loops detected - consider optimization")
        
        if 'try' not in code and 'error' not in description.lower():
            suggestions.append("Consider adding error handling")
        
        return suggestions


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_generation():
        agent = CodeGenerationAgent()
        
        # Test cases
        test_cases = [
            "Create a function called calculate_average that takes a list of numbers",
            "Generate a class called Student with attributes name and age",
            "Implement bubble sort algorithm",
            "Create an API client for weather service"
        ]
        
        for i, description in enumerate(test_cases):
            print(f"\n{'='*60}")
            print(f"Test {i+1}: {description}")
            print('='*60)
            
            request = Request(
                request_id=f"gen_{i+1}",
                request_type=None,
                language=Language.PYTHON,
                problem_statement=description
            )
            
            response = await agent.process(request)
            
            if response.success:
                print(response.data['generated_code'])
                print(f"\nMetadata: {response.data['metadata']}")
            else:
                print(f"Error: {response.error}")
    
    asyncio.run(test_generation())