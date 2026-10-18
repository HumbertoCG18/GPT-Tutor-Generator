# Chama `agy -p` com o primeiro modelo da cadeia cujo balde de cota ainda tem folga.
# A cota do agy e por GRUPO (Gemini: Flash+Pro | 3p: Opus, Sonnet, GPT-OSS), nao por modelo;
# so trocar de grupo traz cota nova. A leitura de /quota nao gasta turno nem tokens (medido).
# Uso: pwsh scripts/agy-cota.ps1 [-SoEscolher] <args do agy>     (stdin e repassado)
#      pwsh scripts/agy-cota.ps1 -p "<pergunta>" --add-dir "<abs>" --output-format json
# Com --model explicito nos args, nao escolhe: repassa como esta. So print mode: sem -p e sem
# stdin redirecionado, recusa, para nunca abrir o TUI do agy dentro de uma sessao headless.
# Sem param(): com [Parameter()] o script vira advanced function e `-p` colide com -ProgressAction.

$Cadeia = @(  # ordem de custo dentro do grupo, depois o outro grupo
    @{ modelo = 'gemini-3.8-flash-low';    balde = 'gemini-5h' },
    @{ modelo = 'gemini-3.8-flash-medium'; balde = 'gemini-5h' },
    @{ modelo = 'gpt-oss-120b-medium';     balde = '3p-5h' },
    @{ modelo = 'claude-sonnet-4-6';       balde = '3p-5h' }
)
$Minimo = if ($env:AGY_COTA_MINIMO) { [double]$env:AGY_COTA_MINIMO } else { 0.10 }

$SoEscolher = $args -contains '-SoEscolher'
$rest = @($args | Where-Object { $_ -ne '-SoEscolher' })
$temPrompt = ($rest | Where-Object { $_ -in '-p', '--print', '--prompt' }).Count -gt 0
# Sem -p, o conteudo vem do stdin: pipeline do PowerShell (ExpectingInput) ou stdin do processo
# redirecionado. Contar linhas, nao so checar redirecionamento: num tool headless o stdin e o
# dispositivo nulo (redirecionado e vazio) e o agy ficaria esperando para sempre.
$entrada = @()
if (-not $temPrompt -and ($MyInvocation.ExpectingInput -or [Console]::IsInputRedirected)) { $entrada = @($input) }
if (-not $temPrompt -and -not $SoEscolher -and $entrada.Count -eq 0) {
    Write-Error 'agy-cota: so print mode. Passe -p "<pergunta>" ou conteudo pelo stdin.'; exit 4
}
if ($rest -contains '--model') { $entrada | & agy @rest; exit $LASTEXITCODE }

$q = (& agy -p '/quota' --output-format json --print-timeout 30s 2>$null | ConvertFrom-Json)
if ($q.num_turns -ne 0) { Write-Error "agy-cota: /quota virou turno de modelo (num_turns=$($q.num_turns))"; exit 2 }
$restante = @{}; $reset = @{}
foreach ($g in $q.command.data.groups) { foreach ($b in $g.buckets) { $restante[$b.id] = $b.remaining_fraction; $reset[$b.id] = $b.reset_time } }

$escolha = $Cadeia | Where-Object { $restante[$_.balde] -ge $Minimo } | Select-Object -First 1
if (-not $escolha) {
    $linhas = foreach ($k in $restante.Keys) { '  {0} {1:P0} reset {2}' -f $k, $restante[$k], $reset[$k] }
    Write-Error (('agy-cota: nenhum balde acima de {0:P0}' -f $Minimo) + "`n" + ($linhas -join "`n")); exit 3
}
Write-Host ('agy-cota: {0} {1:P0} -> {2}' -f $escolha.balde, $restante[$escolha.balde], $escolha.modelo) -ForegroundColor DarkGray
if ($SoEscolher) { "$($escolha.modelo) stdin=$($entrada.Count)"; exit 0 }
$entrada | & agy @rest --model $escolha.modelo
exit $LASTEXITCODE
