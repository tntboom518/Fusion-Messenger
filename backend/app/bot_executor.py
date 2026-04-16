import json
import re
import traceback
from typing import Any


class BotExecutor:
    """Execute bot code safely and return response"""

    def __init__(self, code: str, language: str, message: str, user_context: dict):
        self.code = code
        self.language = language
        self.message = message
        self.user_context = user_context
        self.response = ""
        self.media_type = None
        self.media_url = None

    def execute(self) -> dict:
        """Execute the bot code and return result"""
        try:
            if self.language == "python":
                return self._execute_python()
            elif self.language == "javascript":
                return self._execute_javascript()
            else:
                return {
                    "response": f"Unknown language: {self.language}",
                    "media_type": None,
                    "media_url": None,
                }
        except Exception as e:
            return {
                "response": f"Error: {str(e)}",
                "media_type": None,
                "media_url": None,
            }

    def _execute_python(self) -> dict:
        """Execute Python code"""
        # Create a safe execution environment
        safe_globals = {
            "__builtins__": {},
            "message": self.message,
            "user_name": self.user_context.get("full_name", "User"),
            "user_id": self.user_context.get("id", 0),
            "response": "",
            "media_type": None,
            "media_url": None,
        }

        # Wrap user code to capture response
        wrapped_code = f"""
message = {json.dumps(self.message)}
user_name = {json.dumps(self.user_context.get("full_name", "User"))}
user_id = {self.user_context.get("id", 0)}
response = ""
media_type = None
media_url = None

{self.code}

result = response
"""

        try:
            exec(wrapped_code, safe_globals)
            return {
                "response": safe_globals.get("result", ""),
                "media_type": safe_globals.get("media_type"),
                "media_url": safe_globals.get("media_url"),
            }
        except Exception as e:
            return {
                "response": f"Code error: {str(e)}",
                "media_type": None,
                "media_url": None,
            }

    def _execute_javascript(self) -> dict:
        """Execute JavaScript code using simple eval"""
        # Create a simulated environment
        js_code = f"""
const message = {json.dumps(self.message)};
const userName = {json.dumps(self.user_context.get("full_name", "User"))};
const userId = {self.user_context.get("id", 0)};
let response = "";
let mediaType = null;
let mediaUrl = null;

{self.code};

JSON.stringify({{ response, mediaType, mediaUrl }});
"""

        try:
            import subprocess

            result = subprocess.run(
                ["node", "-e", js_code], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                parsed = json.loads(result.stdout.strip())
                return parsed
            else:
                return {
                    "response": f"JS Error: {result.stderr}",
                    "media_type": None,
                    "media_url": None,
                }
        except FileNotFoundError:
            return {
                "response": "Node.js not available",
                "media_type": None,
                "media_url": None,
            }
        except Exception as e:
            return {
                "response": f"Execution error: {str(e)}",
                "media_type": None,
                "media_url": None,
            }


def execute_bot(code: str, language: str, message: str, user_context: dict) -> dict:
    """Main function to execute bot code"""
    executor = BotExecutor(code, language, message, user_context)
    return executor.execute()
