"""Minimal MCP client for testing the Loadsmart MCP server."""

from __future__ import annotations

import asyncio
import json

from mcp import Client


SERVER_URL = "http://127.0.0.1:8000/mcp"
QUESTION = "Which carrier moved the most loads into Texas?"


async def main() -> None:
    async with Client(SERVER_URL) as client:
        # Confirm that the server exposes the expected tool.
        tools = await client.list_tools()

        print("Available tools:")
        for tool in tools.tools:
            print(f"  - {tool.name}: {tool.description}")

        print("\nCalling ask_loadsmart...")
        print(f"Question: {QUESTION}\n")

        result = await client.call_tool(
            "ask_loadsmart",
            {"question": QUESTION},
        )

        print("Structured content:")
        print(result.structured_content)

        print("\nContent:")
        for item in result.content:
            print(item)

            # MCP text content normally exposes a `.text` attribute.
            text = getattr(item, "text", None)

            if text:
                print("\nDecoded result:")
                try:
                    parsed = json.loads(text)
                    print(
                        json.dumps(
                            parsed,
                            indent=2,
                            default=str,
                        )
                    )
                except json.JSONDecodeError:
                    print(text)


if __name__ == "__main__":
    asyncio.run(main())