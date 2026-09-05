import json, subprocess
from pathlib import Path
S = Path(__file__).parent
t = (S / "razao_template.html").read_text(encoding="utf-8")

def rep(old, new):
    global t
    assert old in t, old[:70]
    t = t.replace(old, new, 1)

if "who-humano" not in t:
    rep(".chip.na{color:var(--ink-3);border-style:dashed}", """.chip.na{color:var(--ink-3);border-style:dashed}
.who{display:inline-block;font-family:var(--cond);font-weight:600;font-size:.72rem;letter-spacing:.04em;text-transform:uppercase;padding:2px 8px;border-radius:2px;white-space:nowrap}
.who-humano{background:var(--pin);color:#fff}
.who-motor{background:var(--accent);color:var(--accent-ink)}
.who-llm{background:var(--warn);color:#fff}
.who-humano-motor{background:linear-gradient(90deg,var(--pin) 50%,var(--accent) 50%);color:#fff}
.who-humano-llm{background:linear-gradient(90deg,var(--pin) 50%,var(--warn) 50%);color:#fff}
.stat .bar{display:flex;height:8px;margin-top:6px;overflow:hidden;border-radius:2px}
.stat .bar span{display:block;height:100%}
details.legend2{margin:-6px 0 16px;border:1px solid var(--line);background:var(--surface)}
details.legend2 summary{cursor:pointer;padding:8px 14px;font-family:var(--cond);font-weight:600;list-style:none}
details.legend2 summary::-webkit-details-marker{display:none}
details.legend2 summary::before{content:"\\25B8  ";font-family:var(--mono);color:var(--ink-3)}
details.legend2[open] summary::before{content:"\\25BE  "}
details.legend2 table{font-size:.82rem}
details.legend2 td.m{font-family:var(--mono);font-size:.78rem;white-space:nowrap}""")

    rep("""    <label>método <select id="fMet"><option value="">todos</option></select></label>""",
        """    <label>decisor <select id="fWho"><option value="">todos</option><option value="humano">humano</option><option value="humano-motor">humano + motor</option><option value="humano-llm">humano + LLM</option><option value="motor">motor</option><option value="llm">LLM</option></select></label>
    <label>método <select id="fMet"><option value="">todos</option></select></label>""")

    rep("""  <div class="legend">
    <span><span class="chip ok">✓ gold</span> bloco = gold</span>
    <span><span class="chip err">✗ gold</span> bloco ≠ gold</span>
    <span><span class="chip na">fora do gold</span> entry não avaliada</span>
    <span><span class="chip pin">pino</span> decisão humana (bloco ou unidade)</span>
    <span>método/provider = caminho da cascata (manual · labels · data · ordinal · topic · disamb · llm · prep-prova · irmao-card · llm-funil)</span>
  </div>""",
    """  <div class="legend">
    <span><span class="who who-humano">humano</span> pino na entry ou card manual de 1 bloco</span>
    <span><span class="who who-motor">motor</span> regra determinística, sem gente e sem LLM</span>
    <span><span class="who who-llm">LLM</span> voto do modelo decidiu o bloco</span>
    <span><span class="who who-humano-motor">humano + motor</span> janela veio de card manual, motor escolheu dentro</span>
    <span><span class="chip ok">✓ gold</span> / <span class="chip err">✗ gold</span> / <span class="chip na">fora do gold</span></span>
  </div>
  <details class="legend2"><summary>Como ler método / provider</summary><div class="tblwrap"><table><thead><tr><th>método</th><th>provider</th><th>decisor</th><th>o que aconteceu</th></tr></thead><tbody>
    <tr><td class="m">pino</td><td class="m">—</td><td><span class="who who-humano">humano</span></td><td>manual_timeline_block_id na entry: alguém fixou o bloco à mão. O motor nem roda.</td></tr>
    <tr><td class="m">janela-1</td><td class="m">manual</td><td><span class="who who-humano">humano</span></td><td>Card do Moodle mapeado à mão (.card_block_map.json, source=manual) para exatamente 1 bloco. A regra só copia.</td></tr>
    <tr><td class="m">disamb</td><td class="m">manual</td><td><span class="who who-humano-motor">humano + motor</span></td><td>Card manual com 2+ blocos; o desempate por tokens (título + rótulo + texto vs. rótulos das sessões) escolheu dentro da janela.</td></tr>
    <tr><td class="m">janela-1</td><td class="m">labels</td><td><span class="who who-motor">motor</span></td><td>Card do Moodle com datas no rótulo (parse automático) apontando 1 bloco.</td></tr>
    <tr><td class="m">janela-1</td><td class="m">data</td><td><span class="who who-motor">motor</span></td><td>Data DD.MM no nome/rótulo do arquivo (SO "12/03 Processos") → sessão do cronograma → bloco.</td></tr>
    <tr><td class="m">janela-1</td><td class="m">ordinal</td><td><span class="who who-motor">motor</span></td><td>"Aula N" no título → N-ésimo encontro de aula do cronograma → bloco.</td></tr>
    <tr><td class="m">janela-1</td><td class="m">topic</td><td><span class="who who-motor">motor</span></td><td>Tópico do card ("Threads") casou com rótulos de sessão de 1 bloco só.</td></tr>
    <tr><td class="m">disamb</td><td class="m">labels / data / topic</td><td><span class="who who-motor">motor</span></td><td>Janela automática com 2+ blocos; desempate por tokens, confiante (margem + token discriminante).</td></tr>
    <tr><td class="m">prep-prova</td><td class="m">prep-prova</td><td><span class="who who-motor">motor</span></td><td>"lista/revisão pN" → último bloco hospedável antes da N-ésima prova (convenção do curso).</td></tr>
    <tr><td class="m">irmao-card</td><td class="m">irmao-card</td><td><span class="who who-motor">motor</span></td><td>Entry sem texto herda o bloco do irmão numerado no mesmo card (roteiro7.zip ← roteiro7.pdf).</td></tr>
    <tr><td class="m">ref-generica</td><td class="m">ref-generica</td><td><span class="who who-motor">motor</span></td><td>Referência/bibliografia sem card → primeiro bloco de aula.</td></tr>
    <tr><td class="m">due-contain / due-straddle</td><td class="m">due-window</td><td><span class="who who-motor">motor</span></td><td>Prova/trabalho com prazo casado ao cronograma → bloco que contém (ou atravessa) o prazo.</td></tr>
    <tr><td class="m">llm</td><td class="m">llm</td><td><span class="who who-llm">LLM</span></td><td>Janela com 2+ blocos e desempate flagado (sem margem) → o modelo votou dentro da janela. Se a janela veio de card manual: humano + LLM.</td></tr>
    <tr><td class="m">llm-funil</td><td class="m">llm-funil</td><td><span class="who who-llm">LLM</span></td><td>Nenhum provider deu janela → o modelo votou entre TODOS os blocos hospedáveis. Degrau mais fraco; sempre flagado.</td></tr>
  </tbody></table></div></details>""")

    rep("""  var $ = function(id){ return document.getElementById(id); };""",
    """  var $ = function(id){ return document.getElementById(id); };
  ORDER.forEach(function(k){ D[k].entries.forEach(function(e){ if(e.pino){ e.bloco = e.pino; } }); });
  function who(e){
    if(e.pino) return 'humano';
    var m = e.metodo||'', p = e.provider||'';
    if(m==='llm'){ var cd = e.card && D[cur].cards[e.card]; return (cd && cd.source==='manual') ? 'humano-llm' : 'llm'; }
    if(m==='llm-funil') return 'llm';
    if(p==='manual') return m==='janela-1' ? 'humano' : 'humano-motor';
    return 'motor';
  }
  var WHO_TXT = {'humano':'humano','motor':'motor','llm':'LLM','humano-motor':'humano + motor','humano-llm':'humano + LLM'};
  function whoChip(e){ var w = who(e); return '<span class="who who-'+w+'">'+WHO_TXT[w]+'</span>'; }""")

    rep("""    var noBlock = entries.filter(function(e){return !e.bloco;}).length;""",
    """    var noBlock = entries.filter(function(e){return !e.bloco;}).length;
    var W = {humano:0,'humano-motor':0,'humano-llm':0,motor:0,llm:0}; entries.forEach(function(e){ W[who(e)]++; });
    var tot = entries.length || 1;
    var bar = '<div class="bar">'+['humano','humano-motor','humano-llm','motor','llm'].map(function(k){ return '<span class="who-'+k+'" style="width:'+(100*W[k]/tot)+'%"></span>'; }).join('')+'</div>';""")

    rep("""      stat('pinos', pinsB+'<small> bloco</small> · '+pinsU+'<small> unidade</small>', '');""",
    """      stat('pinos', pinsB+'<small> bloco</small> · '+pinsU+'<small> unidade</small>', '') +
      stat('quem decidiu o bloco', '<span style="color:var(--pin)">'+(W.humano+W['humano-motor']+W['humano-llm'])+'</span><small> humano</small> · <span style="color:var(--accent)">'+W.motor+'</span><small> motor</small> · <span style="color:var(--warn)">'+W.llm+'</span><small> LLM</small>', bar);""")

    rep("""    var onlyErr = $('onlyErr').checked, met = $('fMet').value, cat = $('fCat').value, showEmpty = $('showEmpty').checked;""",
    """    var onlyErr = $('onlyErr').checked, met = $('fMet').value, cat = $('fCat').value, showEmpty = $('showEmpty').checked, fw = $('fWho').value;""")
    rep("""      if(met && (e.metodo||'—')!==met) return false;""", """      if(met && (e.metodo||'—')!==met) return false;
      if(fw && who(e)!==fw) return false;""")
    rep("""      if(!es.length && (!showEmpty || onlyErr || q || met || cat)) return;""", """      if(!es.length && (!showEmpty || onlyErr || q || met || cat || fw)) return;""")
    rep("""<th>método / provider</th>""", """<th>decisor</th><th>método / provider</th>""")
    rep("""        '<td class="mono">'+(e.pino ? '<span class="chip pin">pino '+esc(e.pino)+'</span> ' : '')+esc(e.metodo||'—')""",
        """        '<td>'+whoChip(e)+'</td>'+
        '<td class="mono">'+(e.pino ? 'pino' : esc(e.metodo||'—'))""")
    rep("""  ['q','onlyErr','fMet','fCat','showEmpty']""", """  ['q','onlyErr','fWho','fMet','fCat','showEmpty']""")
    (S / "razao_template.html").write_text(t, encoding="utf-8")

d = json.load(open(S / "dados.json", encoding="utf-8"))
sha = subprocess.run(["git", "-C", r"C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator", "log", "-1", "--format=%h"], capture_output=True, text=True).stdout.strip()
d["__stamp"] = "2026-08-26 · gerador " + sha
js = json.dumps(d, ensure_ascii=False).replace("</", "<\\/")
html = t.replace("__DADOS__", js)
(S / "razao_dos_blocos.html").write_text(html, encoding="utf-8")
print("ok kb:", len(html.encode()) // 1024, "| fWho:", html.count("fWho"), "| who-humano:", html.count("who-humano"))
