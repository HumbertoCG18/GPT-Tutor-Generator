# Painel ao vivo: quem esta rodando (codex, agy) e o que cada um gravou por ultimo.
# Uso: pwsh scripts/monitor-agentes.ps1        (atualiza a cada 2 s; Ctrl+C sai)
#      pwsh scripts/monitor-agentes.ps1 -Once  (uma passada)
param([switch]$Once, [int]$Intervalo = 2)

function Mostra {
    $agora = Get-Date -Format 'HH:mm:ss'
    $procs = Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^(codex|agy)\.exe$' }
    Write-Host "== $agora  processos vivos ==" -ForegroundColor Cyan
    if ($procs) {
        foreach ($p in $procs) {
            $ini = $p.CreationDate.ToString('HH:mm:ss'); $dur = [int]((Get-Date) - $p.CreationDate).TotalSeconds
            $cmd = ($p.CommandLine -replace '^"[^"]*"\s*', '')
            if ($cmd.Length -gt 90) { $cmd = $cmd.Substring(0, 90) + '...' }
            Write-Host ("  {0,-9} pid {1,-6} desde {2} ({3}s)  {4}" -f $p.Name, $p.ProcessId, $ini, $dur, $cmd) -ForegroundColor Green
        }
    } else { Write-Host "  nenhum" -ForegroundColor DarkGray }

    Write-Host "== codex: ultimas sessoes ==" -ForegroundColor Cyan
    Get-ChildItem "$HOME\.codex\sessions" -Recurse -Filter 'rollout-*.jsonl' -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending | Select-Object -First 3 | ForEach-Object {
            $txt = (Get-Content $_.FullName -TotalCount 12) -join "`n"
            $orig = [regex]::Match($txt, '"originator":"([^"]+)"').Groups[1].Value
            $model = [regex]::Match($txt, '"model":"([^"]+)"').Groups[1].Value
            Write-Host ("  {0}  {1,-11} {2,-14} {3}" -f $_.LastWriteTime.ToString('HH:mm:ss'), $orig, $model, $_.Name.Substring(8, 19))
        }

    Write-Host "== agy: ultimas conversas ==" -ForegroundColor Cyan
    Get-ChildItem "$HOME\.gemini\antigravity-cli\conversations\*.db" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending | Select-Object -First 3 | ForEach-Object {
            Write-Host ("  {0}  {1}  (agy --conversation {1})" -f $_.LastWriteTime.ToString('HH:mm:ss'), $_.BaseName)
        }
}

if ($Once) { Mostra; exit 0 }
while ($true) { try { Clear-Host } catch {}; Mostra; Start-Sleep -Seconds $Intervalo }  # Clear-Host falha fora de console
