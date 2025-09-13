"""
STUDENT_TODO: Currency mini-agent using LiteLLM tool calling (class-based)
- Tools to support:
  1) list_supported() -> list[str]              # PROVIDED (def + schema)
  2) resolve_currency(name_or_code: str) -> str  # PROVIDED (def + schema)
  3) convert(amount: float, base: str, quote: str) -> dict  # YOU implement (def + schema)
- Keep INTERMEDIATE prints before each execution for teaching/debugging.
"""

from typing import Dict, Any, List
from dataclasses import dataclass
import json
from litellm import completion
from config import MODEL

# ===== Mock data =====
RATE_TABLE: Dict[str, float] = {
    "USD->THB": 35.0,
    "THB->USD": 0.0286,
    "THB->EUR": 0.025,
    "EUR->THB": 40.0,
    "USD->EUR": 0.92,
    "EUR->USD": 1.087,
}
SUPPORTED = ["USD", "THB", "EUR", "JPY"]
NAME_TO_ISO = {"baht": "THB", "dollar": "USD", "euro": "EUR", "yen": "JPY"}


@dataclass
class ToolCall:
    name: str
    arguments: str


class CurrencyTools:
    """Currency utilities exposed as tools."""

    # --- Tool 1: list_supported (PROVIDED) ---
    def list_supported(self) -> List[str]:
        return SUPPORTED

    # --- Tool 2: resolve_currency (PROVIDED) ---
    def resolve_currency(self, name_or_code: str) -> str:
        code = (name_or_code or "").strip().upper()
        if code in SUPPORTED:
            return code
        return NAME_TO_ISO.get((name_or_code or "").strip().lower(), "UNKNOWN")

    # --- Tool 3: convert (YOU implement) ---
    def convert(self, amount: float, base: str, quote: str) -> Dict[str, Any]:
        """STUDENT_TODO: use RATE_TABLE to compute result.
        Return dict like: {"rate": , "converted": }.
        If missing rate -> return {"error": f"No rate for {base}->{quote}"}
        """
        # raise NotImplementedError("Implement convert() using RATE_TABLE")

        key = f"{base}->{quote}"
        if key in RATE_TABLE:
            return {"rate": RATE_TABLE[key], "converted": RATE_TABLE[key] * amount}
        else:
            return {"error": f"No rate for {base}->{quote}"}

    @classmethod
    def get_schemas(cls) -> List[dict]:
        """Return tool schemas (OpenAI-compatible). Fill the TODO for convert."""
        return [
            # 1) list_supported - schema COMPLETE
            {
                "name": "list_supported",
                "description": "Return supported currency ISO codes",
                "parameters": {"type": "object", "properties": {}},
            },
            # 2) resolve_currency - schema COMPLETE
            {
                "name": "resolve_currency",
                "description": "Map currency name or code to ISO code (e.g., 'baht'->'THB')",
                "parameters": {
                    "type": "object",
                    "properties": {"name_or_code": {"type": "string"}},
                    "required": ["name_or_code"],
                },
            },
            # 3) convert - STUDENT_TODO: COMPLETE THIS SCHEMA
            {
                "name": "convert",
                "description": "Convert amount from base to quote using fixed RATE_TABLE",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "amount": {"type": "number"},
                        "base": {"type": "string"},
                        "quote": {"type": "string"},
                    },
                    "required": ["amount", "base", "quote"],
                },
            },
        ]


class ToolExecutor:
    def __init__(self):
        self.tools = {}
        self.tool_schemas: List[dict] = []

    def register_tool(self, name: str, func, schema: dict):
        self.tools[name] = func
        self.tool_schemas.append(schema)

    def register_tools(self, tool_obj):
        for schema in tool_obj.get_schemas():
            name = schema["name"]
            if not hasattr(tool_obj, name):
                continue
            self.register_tool(name, getattr(tool_obj, name), schema)

    def run(self, user_text: str, model: str = MODEL, max_turns: int = 6):
        messages = [{"role": "user", "content": user_text}]
        for turn in range(1, max_turns + 1):
            resp = completion(
                model=model,
                messages=messages,
                functions=self.tool_schemas,
                function_call="auto",
            )
            msg = resp.choices[0].message
            fc: ToolCall | None = getattr(msg, "function_call", None)
            if not fc:
                print("FINAL:", getattr(msg, "content", None) or msg.get("content"))
                break
            # INTERMEDIATE print
            print(f"=== INTERMEDIATE (turn {turn}) ===")
            print("name:", getattr(fc, "name", None))
            print("arguments:", getattr(fc, "arguments", None))
            # Execute tool
            try:
                args = json.loads(getattr(fc, "arguments", "{}") or "{}")
                name = getattr(fc, "name", None)
                result = self.tools[name](**args) if args else self.tools[name]()
            except Exception as e:
                result = {"error": str(e)}
            # Return result
            messages.append(
                {
                    "role": "assistant",
                    "content": None,
                    "function_call": {
                        "name": getattr(fc, "name", None),
                        "arguments": getattr(fc, "arguments", "{}"),
                    },
                }
            )
            messages.append(
                {
                    "role": "function",
                    "name": getattr(fc, "name", None),
                    "content": json.dumps(result),
                }
            )


if __name__ == "__main__":
    tools = CurrencyTools()
    ex = ToolExecutor()
    ex.register_tools(tools)
    # After you implement convert() + its schema, these should work nicely:
    ex.run("Convert 100 USD to THB")
    ex.run("Convert 250 baht to euros")

