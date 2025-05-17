from fastmcp import Client

async def main():
    # Connect via stdio to a local script
    async with Client("mendserver.py") as client:
        tools = await client.list_tools()
        print(f"Available tools: {tools}")
        result = await client.call_tool("add", {"a": 5, "b": 3})
        print(f"Result: {result}")
        result = await client.call_tool("chat_with_llm", {"prompt": "Tell me a joke about programming"})
        print(f"Result: {result}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())