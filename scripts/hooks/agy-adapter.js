// Adapta os guardas (protocolo do Claude Code) ao contrato PreToolUse do agy.
//
// agy manda no stdin, em camelCase:
//   { toolCall: { name: 'run_command', args: { CommandLine } }, workspacePaths: [...] }
//   { toolCall: { name: 'file_change', args: { TargetFile, CodeEdit|ReplacementContent|CodeContent, TargetContent } } }
// e espera no stdout { decision: 'allow' | 'deny', reason }. Exit code nao significa nada.
//
// Os guardas leem { tool_input: { command | file_path, old_string, new_string } } e
// bloqueiam com exit 2 + stderr. Este arquivo traduz nos dois sentidos, e muda o cwd
// para o workspace porque o agy executa o hook dentro de .agents/.
//
// Uso: node agy-adapter.js <nome-do-guarda.js>   (resolvido ao lado deste arquivo)
const { spawnSync } = require('child_process');
const path = require('path');

const guarda = path.join(__dirname, process.argv[2] || '');
let raw = '';
process.stdin.on('data', (c) => (raw += c));
process.stdin.on('end', () => {
  const allow = () => process.stdout.write('{"decision":"allow"}');
  let d;
  try {
    d = JSON.parse(raw);
  } catch (e) {
    return allow();
  }
  const ws = (d.workspacePaths || [])[0];
  if (ws) {
    try { process.chdir(ws); } catch (e) {}
  }
  const tc = d.toolCall || {};
  const a = tc.args || {};
  const tool_input = {};
  if (a.CommandLine) tool_input.command = String(a.CommandLine);
  if (a.TargetFile) tool_input.file_path = String(a.TargetFile);
  const novo = a.CodeEdit || a.ReplacementContent || a.CodeContent;
  if (novo !== undefined) tool_input.new_string = String(novo);
  if (a.TargetContent !== undefined) tool_input.old_string = String(a.TargetContent);

  const r = spawnSync('node', [guarda], {
    input: JSON.stringify({ tool_name: tc.name || '', tool_input }),
    encoding: 'utf8',
    timeout: 12000,
  });
  if (r.status === 2) {
    const reason = String(r.stderr || '').trim() || 'bloqueado pelo guarda';
    return process.stdout.write(JSON.stringify({ decision: 'deny', reason }));
  }
  allow();
});
