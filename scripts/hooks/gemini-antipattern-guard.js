// Le so as linhas adicionadas do staged: citar o anti-padrao em comentario ou
// contexto nao bloqueia. Varre por arquivo para poder isentar este proprio guarda,
// cuja lista de alvos e, ela mesma, uma ocorrencia dos padroes.
const { execSync } = require('child_process');
const NL = String.fromCharCode(10);
const ALVOS = ['google.generativeai', 'genai.GenerativeModel'];
const ISENTOS = ['scripts/hooks/gemini-antipattern-guard.js'];

let raw = '';
process.stdin.on('data', (c) => (raw += c));
process.stdin.on('end', () => {
  const passa = () => process.stdout.write(raw);
  let d;
  try {
    d = JSON.parse(raw);
  } catch (e) {
    return passa();
  }

  const cmd = String((d.tool_input || {}).command || '');
  if (cmd.indexOf('git commit') === -1) return passa();

  let staged;
  try {
    staged = execSync('git diff --cached -U0', { encoding: 'utf8', maxBuffer: 33554432 });
  } catch (e) {
    return passa();
  }

  const achados = new Set();
  let arquivo = '';
  for (const linha of staged.split(NL)) {
    if (linha.startsWith('+++ b/')) {
      arquivo = linha.slice(6).trim();
      continue;
    }
    if (!linha.startsWith('+') || linha.startsWith('+++')) continue;
    if (ISENTOS.some((iso) => arquivo === iso)) continue;
    for (const p of ALVOS) {
      if (linha.indexOf(p) !== -1) achados.add(p + '  (' + arquivo + ')');
    }
  }

  if (achados.size) {
    console.error('[guarda] BLOQUEADO: anti-padrao Gemini no staged:');
    for (const a of achados) console.error('  ' + a);
    console.error('.mex/AGENTS.md: usar google-genai, "from google import genai",');
    console.error('com o import lazy dentro do corpo do metodo.');
    process.exit(2);
  }
  passa();
});
