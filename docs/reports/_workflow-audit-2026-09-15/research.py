"""Download public documentation only; never run candidate installers."""
import concurrent.futures
import json
from pathlib import Path
import urllib.request

BASE = Path(__file__).resolve().parent
REPOS = ['Kc1t/alethe-agents', 'NousResearch/hermes-agent', 'Hermes-brasil/hermes-brasil',
         'joeynyc/hermes-hud', 'pivoshenko/kasetto', 'Yu-Xiao-Sheng/codex-memory-trim',
         'DobermanCore/Doberman-Core', 'eljulians/skillfile', 'diegosouzapw/OmniRoute',
         'miso-choi/TruthProbe', 'jarrodwatts/claude-hud', 'bytedance/deer-flow',
         'headroomlabs-ai/headroom', 'rtk-ai/rtk', 'rebelytics/one-skill-to-rule-them-all']


def fetch(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'workflow-audit'})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def inspect(repo):
    try:
        info = json.loads(fetch('https://api.github.com/repos/' + repo))
        branch = info['default_branch']
        latest = json.loads(fetch(f'https://api.github.com/repos/{repo}/commits/{branch}'))
        sha = latest['sha']
        readme_info = json.loads(fetch(f'https://api.github.com/repos/{repo}/readme'))
        url = f'https://raw.githubusercontent.com/{repo}/{sha}/{readme_info["path"]}'
        content = fetch(url)
        path = BASE / 'sources' / (repo.replace('/', '__') + '.md')
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(content)
        return dict(repo=repo, branch=branch, sha=sha, pushed_at=info['pushed_at'],
                    archived=info['archived'], license=(info.get('license') or {}).get('spdx_id'),
                    readme_url=url, bytes=len(content))
    except Exception as exc:
        return dict(repo=repo, error=str(exc))


if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(inspect, REPOS))
    (BASE / 'candidate-sources.json').write_text(json.dumps(rows, indent=2), encoding='utf-8')
    for row in rows:
        print(json.dumps(row))
