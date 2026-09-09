// engine.py e fachada por decisao registrada em .mex/AGENTS.md. Contar defs antes e
// depois evita o falso positivo de um Edit que so cita um def existente como contexto.
const fs = require('fs');
const BARRA = String.fromCharCode(92);

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

  const inp = d.tool_input || {};
  const fp = String(inp.file_path || '').split(BARRA).join('/');
  if (!fp.endsWith('src/builder/engine.py')) return passa();

  const defs = (s) => ((s || '').match(/^def /gm) || []).length;
  let antes, depois;
  if (typeof inp.new_string === 'string') {
    antes = defs(inp.old_string);
    depois = defs(inp.new_string);
  } else if (typeof inp.content === 'string') {
    antes = fs.existsSync(fp) ? defs(fs.readFileSync(fp, 'utf8')) : 0;
    depois = defs(inp.content);
  } else {
    return passa();
  }

  if (depois > antes) {
    console.error('[guarda] BLOQUEADO: ' + (depois - antes) + ' def novo(s) em engine.py.');
    console.error('.mex/AGENTS.md: engine.py e fachada. Logica nova vai no subpacote correto,');
    console.error('e o import vem do submodulo focado, nunca de engine.py.');
    process.exit(2);
  }
  passa();
});
