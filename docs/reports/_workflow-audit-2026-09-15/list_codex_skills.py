"""Query installed Codex's catalog without creating a thread or running inference."""
import asyncio
import collections
import json
from pathlib import Path
import shutil


async def main():
    base = Path(__file__).resolve().parent
    root = base.parents[2]
    with (base / 'sources/catalog-stderr.log').open('wb') as errors:
        p = await asyncio.create_subprocess_exec(shutil.which('codex'), 'app-server', '--stdio',
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=errors, cwd=root)
        async def request(id, method, params):
            p.stdin.write((json.dumps(dict(id=id, method=method, params=params))+'\n').encode())
            await p.stdin.drain()
            while True:
                line = await asyncio.wait_for(p.stdout.readline(), timeout=45)
                if not line:
                    raise RuntimeError('app-server closed without response')
                data = json.loads(line)
                if data.get('id') == id:
                    assert 'error' not in data, data
                    return data['result']
        try:
            await request(1, 'initialize', {'clientInfo': {'name':'workflow-audit','version':'1.0'},
                                          'capabilities':{'experimentalApi':True}})
            result = await request(2, 'skills/list', {'cwds':[str(root)], 'forceReload':True})
            (base/'codex-loaded-skills.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
            for entry in result.get('data',[]):
                skills=entry.get('skills',[])
                print('catalog entries',len(skills),'errors',entry.get('errors'))
                print('fields',list(skills[0]) if skills else [])
                print('scopes',dict(collections.Counter(s.get('scope') for s in skills)))
                print('enabled',dict(collections.Counter(s.get('enabled') for s in skills)))
        finally:
            p.stdin.close()
            try:
                await asyncio.wait_for(p.wait(),timeout=10)
            except asyncio.TimeoutError:
                p.terminate()
                await p.wait()


if __name__ == '__main__':
    asyncio.run(main())
