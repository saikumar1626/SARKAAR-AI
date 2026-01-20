# ===============================
# SARKAR CORE – Intelligent AI Orchestrator
# Author: You (with architectural guidance)
# Purpose: Central brain that understands commands, routes tasks,
#          carries knowledge, and grows by adding agents.
# ===============================

"""
CORE IDEAS
----------
1. One always-running brain
2. Intent understanding
3. Agent routing
4. Memory + knowledge support
5. Safe execution

This is NOT a chatbot.
This is an AI OPERATING CORE.
"""

# -------------------------------
# Imports
# -------------------------------
import time
import json
from typing import Dict, Any

# -------------------------------
# MEMORY (Short-term + Long-term)
# -------------------------------
class Memory:
    def __init__(self):
        self.context = []  # short-term memory
        self.knowledge_base = {}  # long-term (can be RAG later)

    def remember(self, user_input: str, response: str):
        self.context.append({"input": user_input, "response": response})
        if len(self.context) > 10:
            self.context.pop(0)

    def recall_context(self):
        return self.context

    def add_knowledge(self, key: str, value: str):
        self.knowledge_base[key] = value

    def get_knowledge(self, key: str):
        return self.knowledge_base.get(key, None)


# -------------------------------
# AGENTS (Workers)
# -------------------------------
class CodeAgent:
    def run(self, task: str) -> str:
        return f"[CodeAgent] Analysing / generating code for: {task}"


class MathAgent:
    def run(self, task: str) -> str:
        return f"[MathAgent] Calculating result for: {task}"


class WebAgent:
    def run(self, task: str) -> str:
        return f"[WebAgent] Searching the web for: {task}"


class SystemAgent:
    def run(self, task: str) -> str:
        return f"[SystemAgent] Preparing system operation for: {task}"


# -------------------------------
# INTENT CLASSIFIER (Brain Logic)
# -------------------------------
class IntentClassifier:
    def classify(self, command: str) -> str:
        command = command.lower()
        if any(k in command for k in ["code", "debug", "program", "java", "python"]):
            return "code"
        if any(k in command for k in ["calculate", "solve", "math", "bandwidth"]):
            return "math"
        if any(k in command for k in ["search", "google", "find", "web"]):
            return "web"
        if any(k in command for k in ["open", "run", "execute", "system"]):
            return "system"
        return "general"


# -------------------------------
# ROUTER (Decision Maker)
# -------------------------------
class Router:
    def __init__(self):
        self.agents = {
            "code": CodeAgent(),
            "math": MathAgent(),
            "web": WebAgent(),
            "system": SystemAgent()
        }

    def route(self, intent: str, task: str) -> str:
        agent = self.agents.get(intent)
        if not agent:
            return "[CORE] I understand you, but I don’t have that skill yet."
        return agent.run(task)


# -------------------------------
# CORE BRAIN (SARKAR)
# -------------------------------
class SarkarCore:
    def __init__(self, name="Sarkar"):
        self.name = name
        self.memory = Memory()
        self.intent_classifier = IntentClassifier()
        self.router = Router()
        self.running = True

    def think(self, command: str) -> str:
        intent = self.intent_classifier.classify(command)
        result = self.router.route(intent, command)
        self.memory.remember(command, result)
        return result

    def start(self):
        print(f"🧠 {self.name} CORE is online. Awaiting commands...")
        while self.running:
            try:
                command = input("\nYou ▶ ")
                if command.lower() in ["exit", "shutdown", "sleep"]:
                    print(f"🔻 {self.name} going offline.")
                    break
                response = self.think(command)
                print(f"{self.name} ▶ {response}")
            except KeyboardInterrupt:
                print("\n[CORE] Interrupted. Shutting down safely.")
                break


# -------------------------------
# ENTRY POINT
# -------------------------------
if __name__ == "__main__":
    core = SarkarCore()
    core.start()
