import asyncio
import json
import os
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    base = Path(__file__).resolve().parent
    env = dict(os.environ, CBM_WORKERS='4', CBM_MEM_BUDGET_MB='2048')
    command = str(Path.home() / '.local/bin/codebase-memory-mcp.exe')
    async with stdio_client(StdioServerParameters(command=command, env=env)) as (r, w):
        async with ClientSession(r, w) as session:
            init = await session.initialize()
            result = await session.list_tools()
            (base / 'mcp-tools.json').write_text(result.model_dump_json(indent=2), encoding='utf-8')
            (base / 'mcp-initialize.json').write_text(init.model_dump_json(indent=2), encoding='utf-8')
            print(init.server_info)
            print('tools', len(result.tools))
            for tool in result.tools:
                if tool.name in ['index_repository', 'search_graph', 'trace_path', 'get_code_snippet', 'query_graph']:
                    print(tool.name, json.dumps(tool.input_schema))


if __name__ == '__main__':
    asyncio.run(main())
