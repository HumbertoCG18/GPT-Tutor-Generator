import asyncio
import json
import os
import sys
import time
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from collect import BASE, SNAP, PROJECT


async def measure(name, command, args, tool, arguments):
    start=time.perf_counter()
    env=dict(os.environ, PYTHONIOENCODING='utf-8', CBM_WORKERS='4', CBM_MEM_BUDGET_MB='2048')
    async with stdio_client(StdioServerParameters(command=command,args=args,env=env)) as (r,w):
        async with ClientSession(r,w) as session:
            init=await session.initialize()
            startup=time.perf_counter()-start
            await session.call_tool(tool,arguments)
            trials=[]
            for _ in range(3):
                start=time.perf_counter()
                result=await session.call_tool(tool,arguments)
                trials.append(dict(seconds=time.perf_counter()-start,response=result.model_dump(mode='json')))
            return dict(name=name,startup_seconds=startup,server=init.server_info.model_dump(),tool=tool,args=arguments,trials=trials)


async def main():
    results=[]
    results.append(await measure('graphify',sys.executable,['-m','graphify.serve',str(SNAP/'graphify-out/graph.json')],'get_neighbors',{'label':'unit_short_label','token_budget':2000}))
    results.append(await measure('cbm',str(Path.home()/'.local/bin/codebase-memory-mcp.exe'),[],'search_graph',{'project':PROJECT,'name_pattern':'^unit_short_label$','include_connected':True,'limit':30}))
    (BASE/'warm-mcp.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    for r in results:print(r['name'],'startup',r['startup_seconds'],'warm',[x['seconds'] for x in r['trials']])


if __name__=='__main__':asyncio.run(main())
