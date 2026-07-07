"""Client-side smoke test: launches server.py over stdio and exercises it."""
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    params = StdioServerParameters(command="python", args=["server.py"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("TOOLS:", [t.name for t in tools.tools])

            resources = await session.list_resources()
            print("RESOURCES:", [str(r.uri) for r in resources.resources])

            prompts = await session.list_prompts()
            print("PROMPTS:", [p.name for p in prompts.prompts])

            pace = await session.call_tool("pace_calculator", {"target_finish": "1:45:00"})
            print("PACE:", pace.content[0].text)

            alt = await session.call_tool("altitude_advice", {"coming_from_elevation_ft": 0})
            print("ALTITUDE:", alt.content[0].text)

            info = await session.read_resource("race://info")
            print("RESOURCE race://info:\n" + info.contents[0].text)

            reg = await session.call_tool("lookup_registration", {"bib": 101})
            print("REGISTRATION:", reg.content[0].text)

            reg_miss = await session.call_tool("lookup_registration", {"email": "nobody@example.com"})
            print("REGISTRATION (miss):", reg_miss.content[0].text)

            wx = await session.call_tool("race_day_weather", {})
            print("WEATHER:", wx.content[0].text)


asyncio.run(main())
