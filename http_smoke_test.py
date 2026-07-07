"""Connects to the server over Streamable HTTP and exercises it."""
import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def main():
    url = "http://127.0.0.1:8000/mcp"
    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("TOOLS:", [t.name for t in tools.tools])
            reg = await session.call_tool("lookup_registration", {"bib": 244})
            print("REGISTRATION:", reg.content[0].text)
            pace = await session.call_tool("pace_calculator", {"target_finish": "2:00:00"})
            print("PACE:", pace.content[0].text)


asyncio.run(main())
