import json
import os
import anthropic
from dotenv import load_dotenv
from tools import TOOL_DEFINITIONS, TOOL_HANDLERS

load_dotenv()

SYSTEM_PROMPT = """You are a Robinhood trading assistant with direct access to the user's brokerage account.

You can:
- Check portfolio value and positions
- Look up stock prices
- Place market buy and sell orders
- View and cancel open orders

Safety rules you must always follow:
1. Before placing any order, confirm the action and amount with the user unless they gave explicit instruction.
2. Never invest more than the user explicitly specifies.
3. If the user's intent is ambiguous, ask for clarification before trading.
4. Always report the outcome of orders (order ID, state) after execution.

Be concise, factual, and surface the numbers the user needs to make decisions."""

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

def run_agent(user_message: str, conversation_history: list[dict]) -> tuple[str, list[dict]]:
    """Run one turn of the agent loop. Returns (assistant_text, updated_history)."""
    conversation_history = conversation_history + [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model="claude-opus-4-8",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOL_DEFINITIONS,
            messages=conversation_history,
        )

        assistant_content = response.content
        conversation_history = conversation_history + [{"role": "assistant", "content": assistant_content}]

        if response.stop_reason == "end_turn":
            text = next((b.text for b in assistant_content if hasattr(b, "text")), "")
            return text, conversation_history

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in assistant_content:
                if block.type != "tool_use":
                    continue
                handler = TOOL_HANDLERS.get(block.name)
                if handler is None:
                    result = {"error": f"Unknown tool: {block.name}"}
                else:
                    try:
                        result = handler(block.input)
                    except Exception as e:
                        result = {"error": str(e)}

                print(f"  [tool] {block.name}({json.dumps(block.input)}) → {json.dumps(result)}")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                })

            conversation_history = conversation_history + [{"role": "user", "content": tool_results}]
