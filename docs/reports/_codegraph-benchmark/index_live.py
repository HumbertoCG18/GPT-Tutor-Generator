"""Index the live root once, using CBM's canonical name and native exclusions."""
import asyncio
import json
import os
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import ListRootsResult, Root


async def main():
    base = Path(__file__).resolve().parent
    root = base.parents[2]
    async def roots(*args):
        return ListRootsResult(roots=[Root(uri=root.as_uri(), name=root.name)])
    params = StdioServerParameters(
        command=str(Path.home() / '.local/bin/codebase-memory-mcp.exe'), cwd=str(root),
        env=dict(os.environ, CBM_WORKERS='4', CBM_MEM_BUDGET_MB='2048'))
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w, list_roots_callback=roots) as session:
            await session.initialize()
            result = await session.call_tool('index_repository', {
                'repo_path': str(root), 'mode': 'full', 'persistence': False})
            assert not result.is_error, result
            (base / 'live-cbm-index.json').write_text(result.model_dump_json(indent=2), encoding='utf-8')
            data = json.loads(next(c.text for c in result.content if hasattr(c, 'text')))
            print(json.dumps(data), flush=True)
            project = data['project']
            check = await session.call_tool('search_graph', {
                'project': project, 'file_pattern': '.*_codegraph-benchmark.*', 'limit': 5})
            assert not check.is_error, check
            (base / 'live-cbm-exclusions.json').write_text(check.model_dump_json(indent=2), encoding='utf-8')
            print(check.model_dump_json())


if __name__ == '__main__':
    asyncio.run(main())
