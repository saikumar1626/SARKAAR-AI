<div align="center">

# 🤖 SARKAAR-AI

**JARVIS-Inspired Modular AI System**

*Automation · Vision · Voice · Safety Agents*

[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](./LICENSE)

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![AI](https://img.shields.io/badge/AI-Modular_Agents-blueviolet?style=flat-square)
![Vision](https://img.shields.io/badge/Vision-Understanding-orange?style=flat-square)
![Voice](https://img.shields.io/badge/Voice-Interaction-blue?style=flat-square)
![DevSecOps](https://img.shields.io/badge/Safety-Guardrails-red?style=flat-square)

> A sophisticated, production-ready modular AI system with automation, vision, voice, and safety agents — orchestrated through a central CORE system. Built as the evolution of AstraOps.

</div>

---

## 📋 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage Examples](#usage-examples)
- [API Reference](#api-reference)
- [VS Code Integration](#vs-code-integration)
- [Agent Details](#agent-details)
- [Contributing](#contributing)

---

## ✨ Features

### 🔍 Code Analysis
- AST-based code parsing
- Complexity metrics (cyclomatic, cognitive)
- Code quality scoring
- Security vulnerability detection
- Performance issue identification
- Best practices checking

### 🐛 Intelligent Debugging
- Syntax error detection
- Runtime error prediction
- Logic error identification
- Automatic fix suggestions
- Context-aware explanations

### 💡 Code Generation
- Natural language to code
- Template-based generation
- Algorithm implementations
- API client scaffolding
- Data processing pipelines

### ⚡ Performance Optimization
- Loop optimization
- Data structure recommendations
- String operation improvements
- Function call optimization
- Memory usage analysis

### 📖 Code Explanation
- Line-by-line breakdown
- Concept identification
- Complexity analysis
- Purpose inference
- Step-by-step walkthrough

### 🎯 DSA Problem Solver
- Common algorithm patterns
- Data structure implementations
- Complexity analysis
- Test case generation
- Multiple solution approaches

---

## 🏗️ Architecture

```
                    CORE SYSTEM
            Request Router & Orchestrator
                         |
        ┌────────────────┼────────────────┐
        │                │                │
  Memory &         Intent Router    Agent Coordinator
  Context                │
                         │
        ┌────────────────┼────────────────┐
        │                │                │
  Code Analysis    Debug Agent    Code Generation
     Agent                              Agent
        │                │                │
  Optimization    Explanation        DSA Solver
     Agent           Agent
```

### Key Components

1. **CORE System** — Central orchestrator managing all operations
2. **Memory Store** — Maintains context and conversation history
3. **Intent Router** — Routes requests to appropriate agents
4. **Agent Coordinator** — Manages multi-agent workflows
5. **Specialized Agents** — Domain-specific processing units

---

## 🚀 Installation

### Prerequisites
- Python 3.10+
- Windows 11 (or any OS with Python support)
- pip package manager

### Step 1: Clone the Repository
```bash
git clone https://github.com/saikumar1626/SARKAAR-AI.git
cd SARKAAR-AI
```

### Step 2: Install Dependencies
```bash
# No external dependencies required!
# The system uses only Python standard library
```

All agents use only Python's standard library (ast, re, logging, etc.), making it lightweight and portable.

### Step 3: Verify Installation
```bash
python main.py
```

---

## ⚡ Quick Start

### Basic Usage
```python
import asyncio
from main import CodingAssistant

async def main():
    # Initialize assistant
    assistant = CodingAssistant()

    # Analyze code
    code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n-1)
    """

    result = await assistant.analyze_code(code, language="python")
    print(result['data']['insights'])

asyncio.run(main())
```

### Command Line Interface
```bash
python cli.py analyze my_code.py
python cli.py debug buggy_code.py
python cli.py explain algorithm.py
```

---

## 💡 Usage Examples

### Example 1: Comprehensive Code Review
```python
async def code_review_example():
    assistant = CodingAssistant()
    code = """
def process_data(items):
    result = []
    for item in items:
        if item > 0:
            result.append(item * 2)
    return result
    """
    review = await assistant.comprehensive_review(code)
    print("Analysis:", review['data']['code_analysis'])
    print("Debug Report:", review['data']['debug'])
    print("Optimizations:", review['data']['optimize'])
```

### Example 2: Generate and Test Code
```python
async def generate_and_test():
    assistant = CodingAssistant()
    result = await assistant.generate_code(
        "Create a function to calculate the nth Fibonacci number"
    )
    generated_code = result['data']['generated_code']
    analysis = await assistant.analyze_code(generated_code)
    print("\nCode Quality:", analysis['data']['analysis']['code_quality'])
```

### Example 3: Solve DSA Problem
```python
async def solve_problem():
    assistant = CodingAssistant()
    problem = "Implement a function to reverse a linked list"
    solution = await assistant.solve_dsa_problem(problem)
    print("Approach:", solution['data']['solution']['approach'])
    print("Time Complexity:", solution['data']['solution']['time_complexity'])
```

### Example 4: Debug with Error Message
```python
async def debug_with_error():
    assistant = CodingAssistant()
    code = """
def divide(a, b):
    return a / b
result = divide(10, 0)
    """
    error = "ZeroDivisionError: division by zero at line 5"
    result = await assistant.debug_code(code, error_message=error)
    print("Debug Report:")
    print(result['data']['report'])
    if result['data'].get('fixed_code'):
        print("\nFixed Code:")
        print(result['data']['fixed_code'])
```

---

## 📚 API Reference

### CodingAssistant Class

```python
async analyze_code(code: str, language: str = "python") -> Dict
```
Analyze code quality, complexity, and issues.

```python
async debug_code(code: str, language: str = "python", error_message: Optional[str] = None) -> Dict
```
Debug code and suggest fixes.

```python
async generate_code(description: str, language: str = "python") -> Dict
```
Generate code from description.

```python
async optimize_code(code: str, language: str = "python") -> Dict
```
Optimize code for performance.

```python
async explain_code(code: str, language: str = "python", detail_level: str = "medium") -> Dict
```
Explain what code does. `detail_level`: "low", "medium", or "high"

```python
async solve_dsa_problem(problem: str, language: str = "python") -> Dict
```
Solve DSA problem with complexity analysis.

```python
async comprehensive_review(code: str, language: str = "python") -> Dict
```
Complete code review (analysis + debug + optimization).

---

## 🔌 VS Code Integration

### Creating a VS Code Extension

```javascript
const vscode = require('vscode');
const { spawn } = require('child_process');

function activate(context) {
    let analyzeCmd = vscode.commands.registerCommand(
        'coding-assistant.analyze',
        async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) return;
            const code = editor.document.getText();
            const result = await runPythonScript('analyze', code);
            vscode.window.showInformationMessage(
                `Code Quality: ${result.score}`
            );
        }
    );
    context.subscriptions.push(analyzeCmd);
}
module.exports = { activate };
```

---

## 🤖 Agent Details

| Agent | Purpose | Output |
|---|---|---|
| Code Analysis Agent | Comprehensive code quality analysis | Quality score, metrics, recommendations |
| Debug Agent | Error detection and fix suggestions | Bug reports, fix suggestions, corrected code |
| Code Generation Agent | Generate code from descriptions | Generated code with documentation |
| Optimization Agent | Performance improvement suggestions | Optimization suggestions with impact analysis |
| Explanation Agent | Explain code in simple terms | Multi-level explanations |
| DSA Solver Agent | Solve algorithm and data structure problems | Complete solutions with complexity analysis |

---

## 🗺️ Roadmap

- [ ] Web API with FastAPI
- [ ] Real-time VS Code extension
- [ ] Support for more languages (C++, JavaScript, Go)
- [ ] AI model integration for enhanced analysis
- [ ] Collaborative features
- [ ] Cloud deployment options

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](./LICENSE) file for details.

---

<div align="center">

🤖 **SARKAAR-AI — Built with ❤️ for developers**

*The evolution of intelligent development assistance.*

</div>
