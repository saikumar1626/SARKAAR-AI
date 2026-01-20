# 🚀 Complete Setup Guide - Windows 11

## Step-by-Step Installation for Beginners

### Phase 1: Prerequisites (10 minutes)

#### Step 1.1: Install Python

1. Go to [python.org/downloads](https://www.python.org/downloads/)
2. Download Python 3.10 or later for Windows
3. **Important**: Check "Add Python to PATH" during installation
4. Verify installation:
   ```bash
   python --version
   ```
   Should show: Python 3.10.x or higher

#### Step 1.2: Install VS Code

1. Go to [code.visualstudio.com](https://code.visualstudio.com/)
2. Download and install VS Code for Windows
3. Install Python extension:
   - Open VS Code
   - Click Extensions (Ctrl+Shift+X)
   - Search "Python"
   - Install official Python extension by Microsoft

#### Step 1.3: Install Git (Optional but recommended)

1. Download from [git-scm.com](https://git-scm.com/download/win)
2. Install with default settings

---

### Phase 2: Project Setup (5 minutes)

#### Step 2.1: Create Project Directory

```bash
# Open Windows Terminal or Command Prompt
cd Desktop
mkdir coding-assistant
cd coding-assistant
```

#### Step 2.2: Download Project Files

Save these files in the `coding-assistant` folder:

1. `core.py` - CORE orchestration system
2. `code_analysis_agent.py` - Code analysis
3. `debug_agent.py` - Debugging
4. `code_generation_agent.py` - Code generation
5. `optimization_agent.py` - Optimization
6. `explanation_agent.py` - Code explanation
7. `dsa_solver_agent.py` - DSA problems
8. `main.py` - Main integration
9. `README.md` - Documentation

#### Step 2.3: Create Virtual Environment (Recommended)

```bash
# In coding-assistant directory
python -m venv venv

# Activate virtual environment
venv\Scripts\activate  # Windows

# You should see (venv) in your prompt
```

---

### Phase 3: Testing (5 minutes)

#### Step 3.1: Run the Demo

```bash
python main.py
```

You should see:
```
================================================================================
🤖 ADVANCED AI CODING ASSISTANT - DEMONSTRATION
================================================================================

✅ Coding Assistant initialized successfully!
...
```

If you see errors:
- Make sure Python 3.10+ is installed
- Verify all files are in the same directory
- Check that file names match exactly

#### Step 3.2: Test Individual Agents

Create a test file `test_simple.py`:

```python
import asyncio
from main import CodingAssistant

async def test():
    assistant = CodingAssistant()
    
    # Test code analysis
    code = "def hello(): print('Hello World')"
    result = await assistant.analyze_code(code)
    
    print("Success!" if result['success'] else "Failed!")
    print(f"Quality Score: {result['data']['analysis']['code_quality']['score']}")

asyncio.run(test())
```

Run it:
```bash
python test_simple.py
```

---

### Phase 4: VS Code Integration (15 minutes)

#### Step 4.1: Create CLI Interface

Create `cli.py`:

```python
import asyncio
import sys
import json
from main import CodingAssistant

async def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No command provided"}))
        return
    
    command = sys.argv[1]
    
    # Read code from stdin
    code = sys.stdin.read()
    
    assistant = CodingAssistant()
    
    # Map commands to methods
    commands = {
        "analyze": assistant.analyze_code,
        "debug": assistant.debug_code,
        "explain": assistant.explain_code,
        "optimize": assistant.optimize_code,
    }
    
    if command in commands:
        result = await commands[command](code)
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps({"error": f"Unknown command: {command}"}))

if __name__ == "__main__":
    asyncio.run(main())
```

#### Step 4.2: Test CLI

```bash
# Analyze a file
type my_code.py | python cli.py analyze

# On Unix/Mac use 'cat' instead of 'type'
```

#### Step 4.3: Add VS Code Tasks

Create `.vscode/tasks.json` in your project:

```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Analyze Code",
            "type": "shell",
            "command": "type ${file} | python cli.py analyze",
            "group": "test",
            "presentation": {
                "reveal": "always",
                "panel": "new"
            }
        },
        {
            "label": "Debug Code",
            "type": "shell",
            "command": "type ${file} | python cli.py debug",
            "group": "test"
        },
        {
            "label": "Explain Code",
            "type": "shell",
            "command": "type ${file} | python cli.py explain",
            "group": "test"
        },
        {
            "label": "Optimize Code",
            "type": "shell",
            "command": "type ${file} | python cli.py optimize",
            "group": "test"
        }
    ]
}
```

#### Step 4.4: Use in VS Code

1. Open any Python file in VS Code
2. Press `Ctrl+Shift+P`
3. Type "Tasks: Run Task"
4. Select "Analyze Code" (or any other task)
5. Results appear in the terminal

#### Step 4.5: Create Keyboard Shortcuts

Add to `.vscode/keybindings.json`:

```json
[
    {
        "key": "ctrl+alt+a",
        "command": "workbench.action.tasks.runTask",
        "args": "Analyze Code"
    },
    {
        "key": "ctrl+alt+d",
        "command": "workbench.action.tasks.runTask",
        "args": "Debug Code"
    },
    {
        "key": "ctrl+alt+e",
        "command": "workbench.action.tasks.runTask",
        "args": "Explain Code"
    },
    {
        "key": "ctrl+alt+o",
        "command": "workbench.action.tasks.runTask",
        "args": "Optimize Code"
    }
]
```

Now you can use:
- `Ctrl+Alt+A` - Analyze current file
- `Ctrl+Alt+D` - Debug current file
- `Ctrl+Alt+E` - Explain current file
- `Ctrl+Alt+O` - Optimize current file

---

### Phase 5: Advanced Usage (Optional)

#### Create a Web API

Create `api.py`:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from main import CodingAssistant
import asyncio

app = FastAPI(title="Coding Assistant API")
assistant = CodingAssistant()

class CodeRequest(BaseModel):
    code: str
    language: str = "python"

class GenerateRequest(BaseModel):
    description: str
    language: str = "python"

@app.post("/analyze")
async def analyze_code(request: CodeRequest):
    result = await assistant.analyze_code(request.code, request.language)
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    return result

@app.post("/debug")
async def debug_code(request: CodeRequest):
    result = await assistant.debug_code(request.code, request.language)
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    return result

@app.post("/generate")
async def generate_code(request: GenerateRequest):
    result = await assistant.generate_code(request.description, request.language)
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    return result

@app.get("/")
async def root():
    return {"message": "Coding Assistant API", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

Install FastAPI:
```bash
pip install fastapi uvicorn
```

Run API:
```bash
python api.py
```

Access at: http://localhost:8000/docs

---

### Phase 6: Troubleshooting

#### Common Issues

**1. "Python not recognized"**
- Solution: Reinstall Python and check "Add to PATH"
- Or manually add Python to PATH in System Environment Variables

**2. "Module not found"**
- Solution: Make sure all files are in the same directory
- Check file names match exactly (case-sensitive)

**3. "SyntaxError in agent files"**
- Solution: Make sure you're using Python 3.10+
- The code uses modern Python features

**4. "Permission denied"**
- Solution: Run terminal as Administrator
- Or check file permissions

**5. Slow performance**
- Solution: The first run loads all agents (takes a few seconds)
- Subsequent runs are faster due to caching

#### Getting Help

1. Check README.md for detailed documentation
2. Review error messages carefully
3. Test individual components with test_simple.py
4. Verify Python version: `python --version`

---

### Phase 7: Next Steps

#### Extend the System

1. **Add More Languages**
   - Create new analyzers in agents
   - Add to Language enum in core.py

2. **Integrate AI Models**
   - Add OpenAI/Anthropic API integration
   - Use for more sophisticated analysis

3. **Create GUI**
   - Use Tkinter for simple GUI
   - Or create web interface with React

4. **Deploy to Cloud**
   - Package as Docker container
   - Deploy to AWS/Azure/GCP

#### Learning Resources

- Python AsyncIO: docs.python.org/3/library/asyncio.html
- VS Code Extensions: code.visualstudio.com/api
- FastAPI: fastapi.tiangolo.com

---

## Summary

✅ Install Python 3.10+
✅ Install VS Code with Python extension  
✅ Create project directory
✅ Add all Python files
✅ Run demo: `python main.py`
✅ Create CLI: `cli.py`
✅ Add VS Code tasks
✅ Set up keyboard shortcuts
✅ (Optional) Create web API

**You now have a fully functional AI coding assistant!**

---

## Quick Commands Reference

```bash
# Activate virtual environment
venv\Scripts\activate

# Run demo
python main.py

# Test single file
python test_simple.py

# Use CLI
type mycode.py | python cli.py analyze

# Run API server (if installed)
python api.py

# Deactivate virtual environment
deactivate
```

---

**Happy Coding! 🎉**