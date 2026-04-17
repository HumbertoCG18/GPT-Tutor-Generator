import json
import re
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from typing import Optional, List, Tuple, Dict
import os
from datetime import datetime
from pathlib import Path
from src.models.core import FileEntry, SubjectProfile, StudentProfile, SubjectStore, StudentStore
from src.utils.helpers import (
    CATEGORY_LABELS, DEFAULT_CATEGORIES, DEFAULT_OCR_LANGUAGE, PROCESSING_MODES,
    DOCUMENT_PROFILES, PREFERRED_BACKENDS, OCR_LANGS, CODE_EXTENSIONS,
    slugify, parse_html_schedule, auto_detect_category, auto_detect_title,
    fetch_url_title, APP_NAME, HAS_PYMUPDF4LLM, normalize_document_profile
)
from src.builder.datalab_client import get_datalab_base_url, has_datalab_api_key
from src.builder.entry_signals import (
    collect_entry_unit_signals as _collect_entry_unit_signals,
    entry_image_source_dirs as _entry_image_source_dirs,
    normalize_match_text as _normalize_match_text,
    score_text_against_row as _score_text_against_row,
)
from src.builder.engine import BackendSelector, has_docling_python_api
from src.builder.navigation_artifacts import _entry_markdown_text_for_file_map
from src.ui.theme import ThemeManager, AppConfig, THEMES, apply_theme_to_toplevel
class Tooltip:
    """Shows a descriptive tooltip balloon after the mouse hovers for `delay` ms."""

    def __init__(self, widget: tk.Widget, text: str, delay: int = 600):
        self.widget = widget
        self.text = text
        self.delay = delay
        self._job = None
        self._tip: Optional[tk.Toplevel] = None
        widget.bind("<Enter>", self._on_enter, add="+")
        widget.bind("<Leave>", self._on_leave, add="+")
        widget.bind("<ButtonPress>", self._on_leave, add="+")

    def _on_enter(self, _event=None):
        self._cancel()
        self._job = self.widget.after(self.delay, self._show)

    def _on_leave(self, _event=None):
        self._cancel()
        self._hide()

    def _cancel(self):
        if self._job:
            self.widget.after_cancel(self._job)
            self._job = None

    def _show(self):
        if self._tip:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6

        try:
            root = self.widget.winfo_toplevel()
            theme_name = getattr(root, "_theme_name", "dark")
            p = THEMES.get(theme_name, THEMES["dark"])
            bg, fg = p["tooltip_bg"], p["tooltip_fg"]
            border = p["border"]
        except Exception:
            bg, fg, border = "#313244", "#cdd6f4", "#45475a"

        self._tip = tk.Toplevel(self.widget)
        self._tip.wm_overrideredirect(True)
        self._tip.wm_geometry(f"+{x}+{y}")
        self._tip.attributes("-topmost", True)

        frame = tk.Frame(self._tip, background=border, bd=0)
        frame.pack()
        inner = tk.Frame(frame, background=bg, bd=0, padx=10, pady=6)
        inner.pack(padx=1, pady=1)
        tk.Label(
            inner,
            text=self.text,
            background=bg,
            foreground=fg,
            font=("Segoe UI", 9),
            wraplength=320,
            justify="left",
        ).pack()

    def _hide(self):
        if self._tip:
            self._tip.destroy()
            self._tip = None


PROFILE_TOOLTIP_TEXT = (
    "Descreve o tipo de conteudo do PDF. Cada perfil ajusta modo e backend automaticamente.\n\n"
    "auto -> detecta automaticamente\n"
    "math_heavy -> muitas formulas/LaTeX e figuras matematicas (marker/docling)\n"
    "diagram_heavy -> muitas imagens, diagramas, tabelas ou muitas paginas (docling/marker)\n"
    "scanned -> PDF de scan/foto (ativa OCR)"
)


def add_tooltip(widget: tk.Widget, text: str, delay: int = 600) -> Tooltip:
    """Convenience function to attach a Tooltip to any widget."""
    return Tooltip(widget, text, delay)


# ---------------------------------------------------------------------------
# GUI — Settings Dialog
# ---------------------------------------------------------------------------

class SettingsDialog(tk.Toplevel):
    """Modal settings window with Appearance and Processing tabs."""

    def __init__(self, parent: tk.Tk, config: AppConfig, theme_mgr: ThemeManager):
        super().__init__(parent)
        self.parent = parent
        self.config = config
        self.theme_mgr = theme_mgr
        self.title("Configurações")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self._saved = False
        self._build()
        self.update_idletasks()
        # Centre over parent
        px, py = parent.winfo_x(), parent.winfo_y()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        w, h = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{px + (pw - w)//2}+{py + (ph - h)//2}")

    def _build(self):
        p = self.theme_mgr.palette(self.theme_mgr.current)
        self.configure(bg=p["bg"])

        # Header
        hdr = tk.Frame(self, bg=p["header_bg"], pady=12, padx=16)
        hdr.pack(fill="x")
        tk.Label(hdr, text="⚙  Configurações", bg=p["header_bg"], fg=p["header_fg"],
                 font=("Segoe UI", 13, "bold")).pack(anchor="w")
        tk.Label(hdr, text="Personalize o comportamento e aparência do app.",
                 bg=p["header_bg"], fg=p["muted"], font=("Segoe UI", 9)).pack(anchor="w")

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=16, pady=12)

        # ── Appearance tab ──────────────────────────────────────────────
        tab_app = ttk.Frame(nb, padding=16)
        nb.add(tab_app, text="  🎨  Aparência  ")

        ttk.Label(tab_app, text="Tema da interface", style="Accent.TLabel").grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))

        self._var_theme = tk.StringVar(value=self.config.get("theme"))
        theme_desc = {
            "dark": "Escuro (Catppuccin Mocha)",
            "light": "Claro (Catppuccin Latte)",
            "solarized": "Solarized Dark",
        }
        for i, (key, label) in enumerate(theme_desc.items()):
            row_f = ttk.Frame(tab_app)
            row_f.grid(row=i + 1, column=0, columnspan=3, sticky="ew", pady=2)
            rb = ttk.Radiobutton(row_f, text=label, variable=self._var_theme,
                                  value=key, command=self._preview_theme)
            rb.pack(side="left")
            # Colour swatch
            sw_p = THEMES[key]
            swatch = tk.Canvas(row_f, width=80, height=18, bg=sw_p["bg"],
                                highlightthickness=1, highlightbackground=sw_p["border"])
            swatch.pack(side="left", padx=(8, 0))
            swatch.create_rectangle(1, 1, 26, 17, fill=sw_p["accent"], outline="")
            swatch.create_rectangle(27, 1, 52, 17, fill=sw_p["accent2"], outline="")
            swatch.create_rectangle(53, 1, 79, 17, fill=sw_p["input_bg"], outline="")

        # ── Processing tab ──────────────────────────────────────────────
        tab_proc = ttk.Frame(nb, padding=16)
        nb.add(tab_proc, text="  ⚙  Processamento  ")

        self._var_mode = tk.StringVar(value=self.config.get("default_mode"))
        self._var_ocr = tk.StringVar(value=self.config.get("default_ocr_language"))
        self._var_profile = tk.StringVar(value=normalize_document_profile(self.config.get("default_profile")))
        self._var_backend = tk.StringVar(value=self.config.get("default_backend"))
        self._var_image_format = tk.StringVar(value=self.config.get("image_format"))

        IMAGE_FORMATS = ["png", "jpeg"]
        fields = [
            ("Modo de processamento padrão", self._var_mode, PROCESSING_MODES),
            ("Idioma OCR padrão", self._var_ocr, OCR_LANGS),
            ("Perfil de documento padrão", self._var_profile, DOCUMENT_PROFILES),
            ("Backend preferido padrão", self._var_backend, PREFERRED_BACKENDS),
            ("Formato de imagem no Markdown", self._var_image_format, IMAGE_FORMATS),
        ]
        for r, (label, var, vals) in enumerate(fields):
            ttk.Label(tab_proc, text=label).grid(row=r, column=0, sticky="w", pady=6, padx=(0, 16))
            cb = ttk.Combobox(tab_proc, textvariable=var, values=vals, state="readonly", width=22)
            cb.grid(row=r, column=1, sticky="ew")
        add_tooltip(cb, "PNG: qualidade máxima, sem perda (arquivos maiores).\n"
                        "JPEG: arquivos menores, boa qualidade (leve perda).\n"
                        "Afeta extração e consolidação de imagens no repositório.")

        # Stall timeout (spinbox)
        next_row = len(fields)
        self._var_stall_timeout = tk.IntVar(value=int(self.config.get("stall_timeout", 300)))
        self._var_marker_chunking_mode = tk.StringVar(
            value=str(self.config.get("marker_chunking_mode", "fallback"))
        )
        self._var_marker_use_llm = tk.BooleanVar(
            value=bool(self.config.get("marker_use_llm", False))
        )
        self._var_marker_llm_model = tk.StringVar(
            value=str(self.config.get("marker_llm_model", ""))
        )
        self._var_marker_torch_device = tk.StringVar(
            value=str(self.config.get("marker_torch_device", "auto"))
        )
        ttk.Label(tab_proc, text="Timeout de inatividade (seg)").grid(
            row=next_row, column=0, sticky="w", pady=6, padx=(0, 16))
        stall_spin = ttk.Spinbox(tab_proc, from_=60, to=1800, increment=30,
                                  textvariable=self._var_stall_timeout, width=8)
        stall_spin.grid(row=next_row, column=1, sticky="w")
        add_tooltip(stall_spin,
                    "Se o Marker/Docling parar de produzir output por este tempo,\n"
                    "o processo é encerrado automaticamente para evitar travamento.\n"
                    "Padrão: 300s (5 min). Para PDFs grandes, aumente para 600-900s.")

        # ── Vision / Image Description ────────────────────────────────
        ttk.Label(tab_proc, text="Chunking do Marker").grid(
            row=next_row + 1, column=0, sticky="w", pady=6, padx=(0, 16))
        marker_chunk_combo = ttk.Combobox(
            tab_proc,
            textvariable=self._var_marker_chunking_mode,
            values=["off", "fallback", "always"],
            state="readonly",
            width=22,
        )
        marker_chunk_combo.grid(row=next_row + 1, column=1, sticky="w")
        add_tooltip(
            marker_chunk_combo,
            "off -> nunca divide o Marker em chunks.\n"
            "fallback -> tenta inteiro primeiro e sÃ³ divide se travar por timeout.\n"
            "always -> divide preventivamente PDFs grandes em chunks.",
        )

        marker_llm = ttk.Checkbutton(
            tab_proc,
            text="Marker usa LLM via Ollama",
            variable=self._var_marker_use_llm,
        )
        marker_llm.grid(row=next_row + 2, column=0, columnspan=2, sticky="w", pady=(2, 4))
        add_tooltip(
            marker_llm,
            "Ativa --use_llm no Marker e usa marker.services.ollama.OllamaService.\n"
            "Requer uma versão do Marker com suporte a LLM, um Ollama acessível\n"
            "e um modelo explícito em 'Modelo Ollama do Marker'.",
        )

        ttk.Label(tab_proc, text="Modelo Ollama do Marker").grid(
            row=next_row + 3, column=0, sticky="w", pady=6, padx=(0, 16))
        marker_llm_model = ttk.Entry(tab_proc, textvariable=self._var_marker_llm_model, width=28)
        marker_llm_model.grid(row=next_row + 3, column=1, sticky="ew")
        add_tooltip(
            marker_llm_model,
            "Obrigatório quando o LLM do Marker estiver ativado.\n"
            "Este campo é independente do modelo Vision usado na descrição de imagens.\n"
            "Recomendação atual para estabilidade: qwen3-vl:8b.",
        )

        ttk.Label(tab_proc, text="TORCH_DEVICE do Marker").grid(
            row=next_row + 4, column=0, sticky="w", pady=6, padx=(0, 16)
        )
        marker_torch_device = ttk.Combobox(
            tab_proc,
            textvariable=self._var_marker_torch_device,
            values=["auto", "cuda", "mps", "cpu"],
            state="readonly",
            width=22,
        )
        marker_torch_device.grid(row=next_row + 4, column=1, sticky="w")
        add_tooltip(
            marker_torch_device,
            "Define a variável TORCH_DEVICE só para o processo do Marker.\n"
            "auto -> usa cuda fora do macOS e mps no macOS.\n"
            "Use cpu se quiser forçar execução sem GPU no Marker.",
        )

        self._var_prevent_sleep = tk.BooleanVar(
            value=bool(self.config.get("prevent_sleep_during_build", True))
        )
        prevent_sleep = ttk.Checkbutton(
            tab_proc,
            text="Evitar suspensão do Windows durante builds longos",
            variable=self._var_prevent_sleep,
        )
        prevent_sleep.grid(row=next_row + 5, column=0, columnspan=2, sticky="w", pady=(2, 6))
        add_tooltip(
            prevent_sleep,
            "Mantém o sistema acordado durante builds, OCR e reprocessamentos longos.\n"
            "Não altera a curadoria nem a aprovação; só reduz risco de pausa por suspensão.",
        )

        sep_row = next_row + 7
        ttk.Separator(tab_proc, orient="horizontal").grid(
            row=sep_row, column=0, columnspan=2, sticky="ew", pady=(12, 8))
        ttk.Label(tab_proc, text="Vision — Descrição de Imagens",
                  style="Accent.TLabel").grid(
            row=sep_row + 1, column=0, columnspan=2, sticky="w", pady=(0, 8))

        VISION_BACKENDS = ["ollama"]
        VISION_MODELS = [
            "qwen3-vl:235b-cloud",
            "qwen3-vl:8b",
        ]
        QUANTIZATIONS = ["default", "q4_K_M", "q5_K_M", "q8_0", "fp16"]

        self._var_vision_backend = tk.StringVar(value=self.config.get("vision_backend", "ollama"))
        self._var_vision_model = tk.StringVar(value=self.config.get("vision_model"))
        self._var_vision_quant = tk.StringVar(value=self.config.get("vision_model_quantization"))
        self._var_ollama_url = tk.StringVar(value=self.config.get("ollama_base_url"))

        vision_fields = [
            ("Backend Vision", self._var_vision_backend, VISION_BACKENDS),
            ("Modelo Vision", self._var_vision_model, VISION_MODELS),
            ("Quantização", self._var_vision_quant, QUANTIZATIONS),
        ]
        for i, (label, var, vals) in enumerate(vision_fields):
            r = sep_row + 2 + i
            ttk.Label(tab_proc, text=label).grid(row=r, column=0, sticky="w", pady=6, padx=(0, 16))
            state = "readonly" if label != "Modelo Vision" else "normal"
            vcb = ttk.Combobox(tab_proc, textvariable=var, values=vals, state=state, width=28)
            vcb.grid(row=r, column=1, sticky="ew")

        url_row = sep_row + 2 + len(vision_fields)
        ttk.Label(tab_proc, text="URL do Ollama").grid(
            row=url_row, column=0, sticky="w", pady=6, padx=(0, 16))
        ttk.Entry(tab_proc, textvariable=self._var_ollama_url, width=28).grid(
            row=url_row, column=1, sticky="ew")
        add_tooltip(vcb, "Para Ollama, use nomes como qwen3-vl:235b-cloud ou qwen3-vl:8b.\n"
                         "qwen3-vl:235b-cloud é o padrão para máxima qualidade visual.\n"
                         "qwen3-vl:8b é o fallback local recomendado.")

        tab_proc.columnconfigure(1, weight=1)

        # ── Buttons ─────────────────────────────────────────────────────
        btn_frame = ttk.Frame(self, padding=(16, 0, 16, 16))
        btn_frame.pack(fill="x")
        ttk.Button(btn_frame, text="Cancelar", command=self._cancel).pack(side="right", padx=(8, 0))
        ttk.Button(btn_frame, text="Salvar", style="Accent.TButton",
                   command=self._save).pack(side="right")

    def _preview_theme(self):
        self.theme_mgr.apply(self.parent, self._var_theme.get())
        self.parent._theme_name = self._var_theme.get()  # type: ignore[attr-defined]
        # Rebuild self visuals too
        self.destroy()
        SettingsDialog(self.parent, self.config, self.theme_mgr)

    def _save(self):
        self.config.set("theme", self._var_theme.get())
        self.config.set("default_mode", self._var_mode.get())
        self.config.set("default_ocr_language", self._var_ocr.get())
        self.config.set("default_profile", self._var_profile.get())
        self.config.set("default_backend", self._var_backend.get())
        self.config.set("image_format", self._var_image_format.get())
        self.config.set("stall_timeout", self._var_stall_timeout.get())
        self.config.set("marker_chunking_mode", self._var_marker_chunking_mode.get())
        self.config.set("marker_use_llm", bool(self._var_marker_use_llm.get()))
        self.config.set("marker_llm_model", self._var_marker_llm_model.get().strip())
        self.config.set("marker_torch_device", self._var_marker_torch_device.get().strip() or "auto")
        self.config.set("prevent_sleep_during_build", bool(self._var_prevent_sleep.get()))
        vision_backend = self._var_vision_backend.get()
        vision_model = self._var_vision_model.get().strip()
        self.config.set("vision_backend", vision_backend)
        self.config.set("vision_model", vision_model)
        self.config.set("vision_model_quantization", self._var_vision_quant.get())
        self.config.set("ollama_base_url", self._var_ollama_url.get())
        self.config.save()
        self.theme_mgr.apply(self.parent, self._var_theme.get())
        self.parent._theme_name = self._var_theme.get()  # type: ignore[attr-defined]
        self._saved = True
        self.destroy()

    def _cancel(self):
        # Revert preview if user just browsed themes
        self.theme_mgr.apply(self.parent, self.config.get("theme"))
        self.parent._theme_name = self.config.get("theme")  # type: ignore[attr-defined]
        self.destroy()


# ---------------------------------------------------------------------------
# GUI — Help Window
# ---------------------------------------------------------------------------

HELP_SECTIONS: List[Tuple[str, str]] = [
    ("Visão Geral", """O Academic Tutor Repo Builder V3 transforma materiais acadêmicos em um repositório estruturado para estudo assistido por IA.

PLATAFORMAS
  O app gera instruções para Claude, GPT e Gemini.
  A matéria pode ter uma plataforma principal, mas os 3 arquivos de instruções são gerados.

FLUXO RECOMENDADO
  1. Crie ou selecione uma matéria em "📝 Gerenciar".
  2. Confira os dados da disciplina e a pasta do repositório.
  3. Adicione PDFs, imagens, links, código ou ZIP.
  4. Ajuste categoria, modo, perfil e backend quando necessário.
  5. Processe itens individualmente ou clique em "🚀 Criar Repositório".
  6. Revise o que cair em manual-review/ no "🖌 Curator Studio".
  7. Gere ou regenere as instruções LLM pela aba Backlog.

ESTRUTURA MENTAL DO APP
  • Fila a Processar: itens ainda não processados.
  • Tasks de Repositório: fila persistente de builds, reprocessamentos e processamentos individuais.
  • Backlog: itens já processados, lidos do manifest do repositório.
  • Dashboard: visão operacional dos repositórios, manifest e manual-review.
  • Log: saída detalhada das operações.
"""),
    ("Tela Principal", """BARRA SUPERIOR
  📚 Matéria ativa
    Carrega um SubjectProfile salvo e preenche os dados da disciplina.

  📝 Gerenciar
    Abre o cadastro de matérias.

  👤 Aluno
    Edita o perfil do aluno, usado nos arquivos pedagógicos e instruções.

  📊 Status
    Mostra se backends, OCR e perfil do aluno estão configurados.

TOOLBAR
  ➕ PDFs / 🖼 Imagens/Fotos / 🔗 Adicionar Link / 💻 Código / ZIP
    Importa diferentes tipos de material.

  ⚡ Processar
    Processa apenas o item selecionado na fila.

  📂 Abrir Repo
    Carrega um repositório existente pelo manifest.json.

  🖌 Curator Studio
    Abre a revisão manual dos arquivos em manual-review/.

  🚀 Criar Repositório
    Faz build novo ou incremental, dependendo do estado do repo selecionado.

ABAS
  🧱 Tasks de Repositório
    Mostra a fila persistente de operações por repositório.
    Permite enfileirar build, reprocessamento e item selecionado.

  🖥 Dashboard
    Resume status do repositório, manifest, manual-review e tasks pendentes por matéria.
"""),
    ("Dados da Disciplina", """Os dados exibidos na tela principal vêm da matéria ativa ou do repositório aberto.

NOME DA DISCIPLINA / SLUG
  Identificam a disciplina no manifest e nos arquivos pedagógicos.
  O slug é usado em nomes de pasta e arquivos.

SEMESTRE / PROFESSOR / INSTITUIÇÃO
  Entram nos metadados do repositório e nas instruções para a IA.

PASTA DO REPOSITÓRIO
  Caminho da raiz do repositório gerado.
  Se já existir manifest.json, o app consegue abrir e reutilizar esse repo.

MODO PADRÃO / OCR PADRÃO
  Vêm do SubjectProfile e são usados como base para novos itens.
"""),
    ("Gerenciador de Matérias", """O Gerenciador de Matérias salva perfis reutilizáveis.

CAMPOS IMPORTANTES
  Nome, slug, professor, instituição, semestre e horário.
  Modo padrão e OCR padrão.
  Pasta do repositório.
  URL GitHub do repositório.
  LLM principal: claude, gpt ou gemini.

CAMPOS LONGOS
  Cronograma
    Pode ser digitado manualmente ou importado de HTML.

  Plano de Ensino
    Pode ser colado manualmente ou extraído de PDF.
    Esse campo é importante para COURSE_MAP, glossário e bibliografia.

OBSERVAÇÃO
  A fila de arquivos da matéria é persistida junto do perfil.
  Ao trocar de matéria, a fila da matéria ativa é restaurada.
"""),
    ("Categorias e Tipos", """TIPOS SUPORTADOS
  pdf
  image
  url
  github-repo
  code
  zip

CATEGORIAS ATUAIS
  material-de-aula   → slides, notas, apostilas
  provas             → provas em PDF
  listas             → listas de exercícios
  gabaritos          → resoluções e respostas
  fotos-de-prova     → prova, caderno ou folha fotografada
  referencias        → documentos e materiais de apoio
  bibliografia       → livros, artigos e links
  cronograma         → calendário da disciplina
  trabalhos          → enunciados e requisitos de projetos
  codigo-professor   → código base, exemplos e skeletons
  codigo-aluno       → seu código para revisão
  quadro-branco      → foto de quadro ou explicação manuscrita
  outros             → materiais fora dos grupos acima

OBSERVAÇÃO
  Algumas categorias afetam arquivos derivados:
  • provas e fotos-de-prova alimentam índices de exames
  • listas e gabaritos alimentam índices de exercícios
  • trabalhos, código e quadro-branco também entram nas instruções LLM
"""),
    ("Modos e Perfis", """MODOS DE PROCESSAMENTO
  auto
    O sistema decide com base no documento.

  quick
    Só camada base. Mais rápido, menos profundo.

  high_fidelity
    Usa camada base + camada avançada quando fizer sentido.

  manual_assisted
    Igual ao high_fidelity, mas já prepara revisão guiada em manual-review/.

PERFIS DE DOCUMENTO
  auto
    Heurística automática.

  math_heavy
    Muito LaTeX, formulas e imagens matematicas.

  diagram_heavy
    Muitas imagens, diagramas, tabelas ou muitas paginas sem foco em LaTeX.

  scanned
    Escaneado ou fotografado; forca OCR.
"""),
    ("Backends de Extração", """CAMADA BASE
  pymupdf4llm
    Melhor escolha para PDF digital quando disponível.

  pymupdf
    Fallback bruto e rápido.

CAMADA AVANÇADA
  docling
    Melhor para OCR, fórmulas, tabelas e documentos difíceis.

  marker
    Forte em layout, tabelas e equações inline.

BACKEND PREFERIDO
  O campo "backend preferido" orienta a decisão final.
  Mesmo assim, docling e marker continuam sendo complementares à camada base.

STATUS
  Use "📊 Status" para verificar se PyMuPDF, PyMuPDF4LLM, pdfplumber, docling,
  marker e tessdata estão disponíveis no ambiente.
"""),
    ("Opções por Arquivo", """TÍTULO
  Nome legível do item no manifest e nos índices.

UNIDADE / TAGS
  Campo livre para palavras-chave, unidade da disciplina ou branch no caso de GitHub.

NOTAS
  Observações operacionais do item.

PISTA DO PROFESSOR
  Padrões de cobrança, estilo da disciplina, recorrências de prova.

RELEVANTE PARA PROVA
  Sinaliza prioridade pedagógica para estudo e bundle.

INCLUIR NO BUNDLE INICIAL
  Inclui o item em build/claude-knowledge/bundle.seed.json.
  Esse bundle serve como seleção inicial de materiais prioritários.

TIPOS ESPECIAIS
  Link
    Pode virar bibliografia ou material externo.

  GitHub repo
    Detectado automaticamente por URL do GitHub; o campo Tags vira branch.

  Código
    Usa o campo de linguagem como tag principal.
"""),
    ("Opções de PDF", """PRESERVAR IMAGENS NO MARKDOWN BASE
  Salva imagens externas referenciadas pelo markdown base.

FORÇAR OCR
  Ignora o texto embutido e passa tudo por OCR.

EXTRAIR IMAGENS
  Salva figuras em staging/assets/images/.

EXTRAIR TABELAS
  Exporta tabelas detectadas em CSV/Markdown.

PAGE RANGE
  Limita o processamento a páginas específicas.
  Exemplos: 1-5 | 1,3,7 | 0,2,5-7
  Sem zero explícito, o sistema interpreta como base-1.

OCR LANGUAGE
  Idiomas separados por vírgula.
  Padrão recomendado: por,eng
"""),
    ("Curator Studio", """O Curator Studio revisa manualmente saídas de manual-review/.

COMO FUNCIONA
  1. Abra um repositório existente.
  2. Clique em "🖌 Curator Studio".
  3. Selecione um item da lista.
  4. Compare preview, metadados e markdown.
  5. Escolha a melhor fonte disponível: base, avançada ou template.
  6. Edite e salve com Ctrl+S.

APROVAR
  Ao aprovar, o app copia o markdown final para a pasta adequada:
  • content/curated/
  • exercises/lists/
  • exams/past-exams/

  O manifest também é atualizado com approved_markdown / curated_markdown.

REPROVAR
  Remove artefatos gerados, tira a entry do manifest e devolve o item para a fila principal.

UTILITÁRIOS
  Aprovar todos os pendentes.
  Restaurar templates de revisão ausentes.
"""),
    ("Backlog e Instruções", """BACKLOG
  A aba Backlog mostra o que já está no manifest do repositório atual.

AÇÕES PRINCIPAIS
  Atualizar Backlog
    Recarrega o manifest.

  Editar
    Ajusta metadados e visualiza markdowns relacionados.

  Limpar Processamento
    Remove os arquivos gerados de uma entry específica.

  Reprocessar Repositório
    Regenera os arquivos pedagógicos com o código atual.
    É o caminho certo para aplicar a arquitetura mais nova a um repositório antigo.
    Hoje isso também reaplica:
    • COURSE_MAP.md e FILE_MAP.md em modo mais enxuto
    • GLOSSARY.md com definições curtas e evidência compacta
    • bundle.seed.json seletivo para Claude Web
    • reinjeção de descrições de imagem em formato compacto

  Gerar Instruções LLM
    Gera:
    • setup/INSTRUCOES_CLAUDE_PROJETO.md
    • setup/INSTRUCOES_GPT_PROJETO.md
    • setup/INSTRUCOES_GEMINI_PROJETO.md
    (pasta `setup/` fica fora do knowledge base indexado pelo tutor)

  Consolidar Unidade
    Consolida baterias de uma unidade inteira num summary compacto.
    Gera student/batteries/<unit>.summary.md e remove as baterias individuais.
    Backup automático em build/consolidation-backup/.

OBSERVAÇÃO
  Quando COURSE_MAP.md e FILE_MAP.md já estão maduros, o app pode omitir
  o protocolo de primeira sessão ao gerar essas instruções.
"""),
    ("Claude e Tokens", """ARQUITETURA MAP-FIRST / LOW-TOKEN
  O app gera artefatos pensando em baixo custo de contexto no Claude Web.

ORDEM IDEAL DE LEITURA
  1. course/COURSE_MAP.md
  2. student/STUDENT_STATE.md
  3. course/FILE_MAP.md
  4. Só então abrir markdowns longos em content/, exercises/ ou exams/

ARTEFATOS-CHAVE
  COURSE_MAP.md
    Mapa pedagógico curto da disciplina.

  FILE_MAP.md
    Índice de roteamento com colunas como "Quando abrir" e "Prioridade".

  EXERCISE_INDEX.md
    Índice operacional de prática para localizar listas, provas antigas e exercícios por unidade.

  build/claude-knowledge/bundle.seed.json
    Lista seletiva de metadados e materiais de alto sinal para bundle manual. Não substitui os mapas.

IMAGENS
  As descrições de imagem do markdown final agora entram em formato compacto.
  Em duplicatas exatas entre páginas vizinhas, o sistema pode trocar repetição
  por uma referência curta à primeira ocorrência.

ROLLOUT
  Para aplicar isso em repositórios antigos, use:
  • Reprocessar Repositório

OBSERVAÇÃO
  COURSE_MAP.md omite seções vazias até existir sinal real, como incidência em prova
  ou notas do professor. Isso evita desperdiçar contexto logo no primeiro chat.
"""),
    ("Continuidade", """ARQUIVOS DE ESTADO
  student/STUDENT_STATE.md
    Registra progresso e próximos passos do aluno. Consulte antes de repetir ou aprofundar demais.

  student/PROGRESS_SCHEMA.md
    Define a estrutura esperada para atualizações de progresso.

  USO PRÁTICO
  Ao final de uma sessão de estudo, atualize o estado do aluno no repositório.
  Em um novo chat, entregue esse estado para a IA junto do repositório conectado.

GITHUB
  Se a matéria tiver URL GitHub configurada, esse dado entra nas instruções geradas.
  Isso ajuda principalmente fluxos conectados a projetos com sync de repositório.

  ATUALIZAÇÃO INCREMENTAL
  Se o repositório já existir, o build pode adicionar apenas arquivos novos
  e ainda regenerar os arquivos pedagógicos.
"""),
    ("Atalhos e Dicas", """ATALHOS
  F1            → abre esta janela
  Double-click  → edita item selecionado na fila ou backlog
  Delete        → remove item selecionado
  Espaço        → ativa/desativa item na fila
  Ctrl+S        → salva no Curator Studio

DICAS
  • Use "📂 Abrir Repo" antes de mexer em backlog ou Curator Studio.
  • O manifest.json é a fonte de verdade do repositório processado.
  • O status da barra inferior é um bom diagnóstico rápido do ambiente.
  • Reprocessar Repositório é a forma mais segura de aplicar mudanças de arquitetura
    aos repositórios já existentes.

DEPENDÊNCIAS
  Se faltarem PyMuPDF, PyMuPDF4LLM ou pdfplumber:
  pip install pymupdf pymupdf4llm pdfplumber
"""),
]


class HelpWindow(tk.Toplevel):
    """F1-style help window with navigation panel and searchable content."""

    def __init__(self, parent: tk.Tk, theme_mgr: ThemeManager):
        super().__init__(parent)
        self.theme_mgr = theme_mgr
        self.title("Ajuda — Academic Tutor Repo Builder")
        self.geometry("900x620")
        self.minsize(700, 480)
        self.transient(parent)
        p = self.theme_mgr.palette(self.theme_mgr.current)
        self.configure(bg=p["bg"])
        self._build(p)

    def _build(self, p: Dict[str, str]):
        font_body = ("Segoe UI", 10)
        font_bold = ("Segoe UI", 10, "bold")

        # Header
        hdr = tk.Frame(self, bg=p["header_bg"], pady=10, padx=16)
        hdr.pack(fill="x")
        tk.Label(hdr, text="?  Central de Ajuda", bg=p["header_bg"], fg=p["header_fg"],
                 font=("Segoe UI", 13, "bold")).pack(side="left")

        # Search bar
        search_frame = tk.Frame(hdr, bg=p["header_bg"])
        search_frame.pack(side="right")
        tk.Label(search_frame, text="🔍", bg=p["header_bg"], fg=p["muted"],
                 font=("Segoe UI", 10)).pack(side="left")
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", self._on_search)
        search_entry = tk.Entry(search_frame, textvariable=self._search_var,
                                 bg=p["input_bg"], fg=p["fg"], insertbackground=p["fg"],
                                 relief="flat", font=font_body, width=22)
        search_entry.pack(side="left", padx=(4, 0), ipady=3)

        body = tk.Frame(self, bg=p["bg"])
        body.pack(fill="both", expand=True)

        # Left navigation pane
        nav_frame = tk.Frame(body, bg=p["frame_bg"], width=200)
        nav_frame.pack(side="left", fill="y")
        nav_frame.pack_propagate(False)

        tk.Label(nav_frame, text="Seções", bg=p["frame_bg"], fg=p["accent"],
                 font=font_bold, padx=12, pady=8).pack(anchor="w")

        self._nav_buttons: List[tk.Button] = []
        for i, (title, _) in enumerate(HELP_SECTIONS):
            btn = tk.Button(
                nav_frame, text=title, anchor="w", padx=12, pady=6,
                bg=p["frame_bg"] if i != 0 else p["select_bg"],
                fg=p["fg"] if i != 0 else p["accent"],
                activebackground=p["select_bg"], activeforeground=p["accent"],
                relief="flat", bd=0, font=font_body, cursor="hand2",
                command=lambda idx=i: self._show_section(idx),
            )
            btn.pack(fill="x")
            self._nav_buttons.append(btn)

        # Divider
        tk.Frame(body, bg=p["border"], width=1).pack(side="left", fill="y")

        # Content area
        content_frame = tk.Frame(body, bg=p["bg"])
        content_frame.pack(side="left", fill="both", expand=True)

        self._text = tk.Text(
            content_frame, wrap="word", state="disabled",
            bg=p["bg"], fg=p["fg"], font=font_body,
            relief="flat", padx=24, pady=16,
            spacing1=2, spacing3=4,
            selectbackground=p["select_bg"], selectforeground=p["select_fg"],
            cursor="arrow",
        )
        self._text.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(content_frame, orient="vertical", command=self._text.yview)
        sb.pack(side="right", fill="y")
        self._text.configure(yscrollcommand=sb.set)

        # Configure text tags
        self._text.tag_configure("h1", font=("Segoe UI", 14, "bold"),
                                  foreground=p["accent"], spacing1=4, spacing3=8)
        self._text.tag_configure("h2", font=("Segoe UI", 11, "bold"),
                                  foreground=p["accent2"], spacing1=10, spacing3=4)
        self._text.tag_configure("body", font=font_body, foreground=p["fg"])
        self._text.tag_configure("code", font=("Consolas", 9),
                                  foreground=p["success"], background=p["frame_bg"])
        self._text.tag_configure("keyword", font=font_bold, foreground=p["warning"])
        self._text.tag_configure("highlight", background=p["warning"],
                                  foreground=p["bg"])

        self._current_section = 0
        self._show_section(0)

    def _show_section(self, idx: int):
        p = self.theme_mgr.palette(self.theme_mgr.current)
        self._current_section = idx

        # Update nav button highlights
        for i, btn in enumerate(self._nav_buttons):
            if i == idx:
                btn.configure(bg=p["select_bg"], fg=p["accent"])
            else:
                btn.configure(bg=p["frame_bg"], fg=p["fg"])

        title, content = HELP_SECTIONS[idx]
        self._render(title, content)

    def _render(self, title: str, content: str, highlight: str = ""):
        self._text.configure(state="normal")
        self._text.delete("1.0", "end")
        self._text.insert("end", title + "\n", "h1")
        self._text.insert("end", "─" * 60 + "\n", "body")

        for line in content.split("\n"):
            stripped = line.strip()
            if stripped and stripped == stripped.upper() and len(stripped) > 3 and not stripped.startswith("•"):
                # ALL CAPS lines → subheading
                self._text.insert("end", "\n" + line + "\n", "h2")
            elif stripped.startswith("•"):
                self._text.insert("end", "  " + line.lstrip() + "\n", "body")
            else:
                self._text.insert("end", line + "\n", "body")

        # Highlight search term if provided
        if highlight:
            self._highlight_in_text(highlight)

        self._text.configure(state="disabled")
        self._text.see("1.0")

    def _highlight_in_text(self, term: str):
        content = self._text.get("1.0", "end").lower()
        term_lower = term.lower()
        start = 0
        while True:
            pos = content.find(term_lower, start)
            if pos == -1:
                break
            line = content[:pos].count("\n") + 1
            col = pos - content[:pos].rfind("\n") - 1
            end_col = col + len(term)
            self._text.tag_add("highlight", f"{line}.{col}", f"{line}.{end_col}")
            start = pos + 1

    def _on_search(self, *_args):
        query = self._search_var.get().strip().lower()
        if not query:
            self._show_section(self._current_section)
            return

        # Search across all sections
        results = []
        for title, content in HELP_SECTIONS:
            if query in title.lower() or query in content.lower():
                results.append((title, content))

        self._text.configure(state="normal")
        self._text.delete("1.0", "end")
        p = self.theme_mgr.palette(self.theme_mgr.current)

        if not results:
            self._text.insert("end", "Nenhum resultado encontrado para: ", "body")
            self._text.insert("end", f'"{query}"', "keyword")
        else:
            self._text.insert("end", f"Resultados para: ", "body")
            self._text.insert("end", f'"{query}"\n\n', "keyword")
            for title, content in results:
                self._text.insert("end", title + "\n", "h1")
                self._text.insert("end", "─" * 60 + "\n", "body")
                for line in content.split("\n"):
                    self._text.insert("end", line + "\n", "body")
                self._text.insert("end", "\n", "body")
            self._highlight_in_text(query)

        self._text.configure(state="disabled")
        self._text.see("1.0")


class HTMLImportDialog(tk.Toplevel):
    """Diálogo para colar código HTML do cronograma e converter."""
    def __init__(self, parent: "SubjectManagerDialog"):
        super().__init__(parent)
        self.title("📥  Importar Cronograma (HTML)")
        self.geometry("640x480")
        self.transient(parent)
        self.grab_set()
        p = apply_theme_to_toplevel(self, parent)
        self.parent = parent

        ttk.Label(self, text="Cole o elemento HTML interiro da tabela de cronograma (ex: Portal/Moodle):").pack(padx=10, pady=(10, 5), anchor="w")
        self.text = tk.Text(
            self,
            font=("Consolas", 10),
            wrap="word",
            bg=p["input_bg"],
            fg=p["fg"],
            insertbackground=p["fg"],
            selectbackground=p["select_bg"],
            selectforeground=p["select_fg"],
            relief="flat",
            borderwidth=1,
        )
        self.text.pack(fill="both", expand=True, padx=10, pady=5)
        
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=10)
        ttk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(side="right", padx=(5, 0))
        btn_import = ttk.Button(btn_frame, text="Importar para Markdown", style="Accent.TButton", command=self._process)
        btn_import.pack(side="right")
        
    def _process(self):
        html_str = self.text.get("1.0", "end").strip()
        if not html_str:
            self.destroy()
            return
        
        res = parse_html_schedule(html_str)
        if res.startswith("Erro:"):
            messagebox.showerror(APP_NAME, res, parent=self)
            return
            
        current = self.parent._syllabus_text.get("1.0", "end").strip()
        if current:
            current += "\n\n"
        self.parent._syllabus_text.delete("1.0", "end")
        self.parent._syllabus_text.insert("end", current + res)
        self.destroy()


# ---------------------------------------------------------------------------
# GUI — Subject Manager Dialog
# ---------------------------------------------------------------------------

class SubjectManagerDialog(tk.Toplevel):
    """Gerenciador de matérias — criar, editar, excluir perfis."""

    def __init__(self, parent, subject_store: SubjectStore, theme_mgr: ThemeManager):
        super().__init__(parent)
        self.title("📚  Gerenciador de Matérias")
        self.geometry("780x700")
        self.transient(parent)
        self.grab_set()
        self._store = subject_store
        self._theme_mgr = theme_mgr
        self._p = apply_theme_to_toplevel(self, parent)
        self._current_name: Optional[str] = None
        self._build_ui()
        self._refresh_list()

    def _build_ui(self):
        p = self._p
        pw = ttk.PanedWindow(self, orient="horizontal")
        pw.pack(fill="both", expand=True, padx=10, pady=10)

        # ── Left panel: subject list ─────────────────────────────────
        left = ttk.Frame(pw, width=220)
        pw.add(left, weight=0)

        ttk.Label(left, text="Matérias salvas", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 6))
        self._listbox = tk.Listbox(
            left,
            width=28,
            font=("Segoe UI", 10),
            bg=p["input_bg"],
            fg=p["fg"],
            selectbackground=p["select_bg"],
            selectforeground=p["select_fg"],
            highlightthickness=0,
            relief="flat",
        )
        self._listbox.pack(fill="both", expand=True)
        self._listbox.bind("<<ListboxSelect>>", self._on_select)

        btn_frame = ttk.Frame(left)
        btn_frame.pack(fill="x", pady=(8, 0))
        ttk.Button(btn_frame, text="➕ Nova", command=self._new).pack(side="left")
        ttk.Button(btn_frame, text="✖ Excluir", command=self._delete).pack(side="right")

        # ── Right panel: edit form ───────────────────────────────────
        right = ttk.Frame(pw)
        pw.add(right, weight=1)

        form = ttk.LabelFrame(right, text="  Dados da Matéria", padding=12)
        form.pack(fill="both", expand=True)

        self._vars: Dict[str, tk.StringVar] = {}
        labels = [
            ("name", "Nome da matéria", "Ex: Cálculo I, Estruturas de Dados"),
            ("slug", "Slug", "Auto-gerado se vazio. Ex: calculo-i"),
            ("professor", "Professor", "Nome do professor"),
            ("institution", "Instituição", "Ex: PUCRS"),
            ("semester", "Semestre", "Ex: 2025/1"),
            ("schedule", "Horário", "Ex: Seg/Qua 10:15-11:55"),
            ("default_mode", "Modo padrão", "auto, quick, high_fidelity, manual_assisted"),
            ("default_ocr_lang", "OCR padrão", DEFAULT_OCR_LANGUAGE),
            ("repo_root", "Pasta do repositório", "Caminho completo do repo (ex: C:\\Users\\...\\Metodos-Formais-Tutor)"),
            ("github_url", "URL GitHub", "Ex: https://github.com/seu-user/metodos-formais-tutor"),
            ("preferred_llm", "LLM Principal", "Plataforma que você usa principalmente"),
        ]

        for i, (key, label, tip) in enumerate(labels):
            lbl = ttk.Label(form, text=label)
            lbl.grid(row=i, column=0, sticky="w", pady=3)
            add_tooltip(lbl, tip)
            var = tk.StringVar()
            self._vars[key] = var
            if key == "default_mode":
                ttk.Combobox(form, textvariable=var, values=PROCESSING_MODES,
                             state="readonly", width=22).grid(row=i, column=1, sticky="ew", padx=(8, 0))
            elif key == "repo_root":
                fr = ttk.Frame(form)
                fr.grid(row=i, column=1, sticky="ew", padx=(8, 0))
                ttk.Entry(fr, textvariable=var).pack(side="left", fill="x", expand=True)
                ttk.Button(fr, text="📁", width=3,
                           command=lambda v=var: v.set(filedialog.askdirectory() or v.get())).pack(side="right", padx=(4, 0))
            elif key == "preferred_llm":
                ttk.Combobox(form, textvariable=var,
                             values=["claude", "gpt", "gemini"],
                             state="readonly", width=22).grid(row=i, column=1, sticky="ew", padx=(8, 0))
            else:
                ttk.Entry(form, textvariable=var, width=36).grid(row=i, column=1, sticky="ew", padx=(8, 0))

        form.columnconfigure(1, weight=1)

        # Syllabus (cronograma) — multiline
        row_syl = len(labels)
        
        lbl_syl_frame = ttk.Frame(form)
        lbl_syl_frame.grid(row=row_syl, column=0, sticky="nw", pady=3)
        lbl_syl = ttk.Label(lbl_syl_frame, text="Cronograma")
        lbl_syl.pack(anchor="w")
        btn_html = ttk.Button(lbl_syl_frame, text="📥 De HTML", width=12, command=self._import_html)
        btn_html.pack(anchor="w", pady=(8, 0))
        add_tooltip(btn_html, "Cole o HTML do cronograma (do Portal/Moodle) para converter automaticamente numa tabela Markdown limpa.")

        self._syllabus_text = tk.Text(
            form,
            height=6,
            width=36,
            font=("Segoe UI", 9),
            wrap="word",
            bg=p["input_bg"],
            fg=p["fg"],
            insertbackground=p["fg"],
            selectbackground=p["select_bg"],
            selectforeground=p["select_fg"],
            highlightthickness=0,
            relief="flat",
        )
        self._syllabus_text.grid(row=row_syl, column=1, sticky="nsew", padx=(8, 0), pady=3)
        form.rowconfigure(row_syl, weight=1)

        # Teaching Plan (Plano de ensino) — multiline
        row_tp = row_syl + 1
        lbl_tp_frame = ttk.Frame(form)
        lbl_tp_frame.grid(row=row_tp, column=0, sticky="nw", pady=3)
        lbl_tp = ttk.Label(lbl_tp_frame, text="Plano de Ensino\n(Ementa, Objetivos)")
        lbl_tp.pack(anchor="w")
        
        btn_pdf = ttk.Button(lbl_tp_frame, text="📥 Extrair PDF", width=12, command=self._import_pdf_teaching_plan)
        btn_pdf.pack(anchor="w", pady=(8, 0))
        add_tooltip(btn_pdf, "Selecione o arquivo PDF do Plano de Ensino da faculdade. A aplicação extrairá todo o texto estruturado e o converterá para Markdown perfeitamente usando pymupdf4llm.")

        self._teaching_plan_text = tk.Text(
            form,
            height=6,
            width=36,
            font=("Segoe UI", 9),
            wrap="word",
            bg=p["input_bg"],
            fg=p["fg"],
            insertbackground=p["fg"],
            selectbackground=p["select_bg"],
            selectforeground=p["select_fg"],
            highlightthickness=0,
            relief="flat",
        )
        self._teaching_plan_text.grid(row=row_tp, column=1, sticky="nsew", padx=(8, 0), pady=3)
        form.rowconfigure(row_tp, weight=1)

        # Save button
        ttk.Button(right, text="💾  Salvar matéria", style="Accent.TButton",
                   command=self._save).pack(fill="x", pady=(10, 0))

    def _refresh_list(self):
        self._listbox.delete(0, "end")
        for name in self._store.names():
            self._listbox.insert("end", name)

    def _on_select(self, _event=None):
        sel = self._listbox.curselection()
        if not sel:
            return
        name = self._listbox.get(sel[0])
        sp = self._store.get(name)
        if not sp:
            return
        self._current_name = name
        for key, var in self._vars.items():
            var.set(getattr(sp, key, ""))
        self._syllabus_text.delete("1.0", "end")
        self._syllabus_text.insert("1.0", sp.syllabus)
        self._teaching_plan_text.delete("1.0", "end")
        self._teaching_plan_text.insert("1.0", getattr(sp, "teaching_plan", ""))

    def _new(self):
        self._current_name = None
        for var in self._vars.values():
            var.set("")
        self._vars["institution"].set("PUCRS")
        self._vars["default_mode"].set("auto")
        self._vars["default_ocr_lang"].set(DEFAULT_OCR_LANGUAGE)
        self._vars["preferred_llm"].set("claude")
        self._syllabus_text.delete("1.0", "end")
        self._teaching_plan_text.delete("1.0", "end")

    def _save(self):
        name = self._vars["name"].get().strip()
        if not name:
            messagebox.showwarning("Matéria", "Preencha o nome da matéria.")
            return
        slug = self._vars["slug"].get().strip() or slugify(name)
        # Preserve existing queue from the store (avoid wiping queued files)
        existing = self._store.get(name)
        existing_queue = existing.queue if existing else []
        sp = SubjectProfile(
            name=name,
            slug=slug,
            professor=self._vars["professor"].get().strip(),
            institution=self._vars["institution"].get().strip() or "PUCRS",
            semester=self._vars["semester"].get().strip(),
            schedule=self._vars["schedule"].get().strip(),
            syllabus=self._syllabus_text.get("1.0", "end-1c").strip(),
            teaching_plan=self._teaching_plan_text.get("1.0", "end-1c").strip(),
            default_mode=self._vars["default_mode"].get(),
            default_ocr_lang=self._vars["default_ocr_lang"].get().strip() or DEFAULT_OCR_LANGUAGE,
            repo_root=self._vars["repo_root"].get().strip(),
            github_url=self._vars["github_url"].get().strip(),
            preferred_llm=self._vars["preferred_llm"].get().strip() or "claude",
            queue=existing_queue,
        )
        self._store.add(sp)
        self._current_name = name
        self._refresh_list()
        messagebox.showinfo(APP_NAME, f"Matéria '{sp.name}' salva com sucesso!", parent=self)
        
    def _import_html(self):
        HTMLImportDialog(self)

    def _import_pdf_teaching_plan(self):
        if not HAS_PYMUPDF4LLM:
            messagebox.showerror(APP_NAME, "pymupdf4llm não está instalado. Feche a aplicação e execute 'pip install pymupdf4llm'.")
            return
            
        pdf_path = filedialog.askopenfilename(
            parent=self, 
            title="Selecione o Plano de Ensino em PDF", 
            filetypes=[("Arquivos PDF", "*.pdf")]
        )
        if not pdf_path:
            return
            
        import threading
        
        def worker():
            try:
                import pymupdf4llm
                md_text = pymupdf4llm.to_markdown(pdf_path)

                def _apply():
                    try:
                        self._teaching_plan_text.delete("1.0", "end")
                        self._teaching_plan_text.insert("1.0", md_text)
                        messagebox.showinfo(APP_NAME, "Plano de Ensino extraído com sucesso!", parent=self)
                    except Exception:
                        pass  # widget destroyed while extracting
                self.after(0, _apply)
            except Exception as e:
                self.after(0, lambda: messagebox.showerror(APP_NAME, f"Erro ao extrair PDF:\n{e}", parent=self))

        threading.Thread(target=worker, daemon=True).start()

    def _delete(self):
        sel = self._listbox.curselection()
        if not sel:
            messagebox.showinfo("Matéria", "Selecione uma matéria para excluir.")
            return
        name = self._listbox.get(sel[0])
        if messagebox.askyesno("Matéria", f"Excluir '{name}'?"):
            self._store.delete(name)
            self._current_name = None
            self._new()
            self._refresh_list()


# ---------------------------------------------------------------------------
# GUI — Student Profile Dialog
# ---------------------------------------------------------------------------

class StudentProfileDialog(tk.Toplevel):
    """Editor do perfil do aluno."""

    def __init__(self, parent, student_store: StudentStore, theme_mgr: ThemeManager):
        super().__init__(parent)
        self.title("👤  Perfil do Aluno")
        self.geometry("560x520")
        self.transient(parent)
        self.grab_set()
        self._store = student_store
        self._p = apply_theme_to_toplevel(self, parent)
        self._build_ui()

    def _build_ui(self):
        palette = self._p
        profile = self._store.profile
        frm = ttk.LabelFrame(self, text="  Seus dados", padding=14)
        frm.pack(fill="x", padx=14, pady=(14, 8))

        self._vars: Dict[str, tk.StringVar] = {}
        entries = [
            ("full_name", "Nome completo", "Seu nome completo, como aparece no sistema acadêmico."),
            ("nickname", "Como prefere ser chamado", "Nome/apelido que o tutor deve usar ao se referir a você.\nEx: Humberto, Beto, Hu"),
        ]
        for i, (key, label, tip) in enumerate(entries):
            lbl = ttk.Label(frm, text=label)
            lbl.grid(row=i, column=0, sticky="w", pady=4)
            add_tooltip(lbl, tip)
            var = tk.StringVar(value=getattr(profile, key, ""))
            self._vars[key] = var
            ttk.Entry(frm, textvariable=var, width=40).grid(row=i, column=1, sticky="ew", padx=(8, 0))
        frm.columnconfigure(1, weight=1)

        # Personality — multiline
        pers_frame = ttk.LabelFrame(self, text="  🧠  Personalidade do Tutor", padding=14)
        pers_frame.pack(fill="both", expand=True, padx=14, pady=(0, 8))

        hint = ttk.Label(pers_frame, text="Como o tutor deve te ajudar? Descreva o estilo que funciona para você:",
                         style="Muted.TLabel")
        hint.pack(anchor="w", pady=(0, 6))
        add_tooltip(hint, "Este texto será exportado nos repositórios e define como a IA principal interage com você.\nDica: seja específico sobre estilo de explicação, nível de detalhe e preferências.")

        self._personality_text = tk.Text(
            pers_frame,
            height=10,
            font=("Segoe UI", 10),
            wrap="word",
            bg=palette["input_bg"],
            fg=palette["fg"],
            insertbackground=palette["fg"],
            selectbackground=palette["select_bg"],
            selectforeground=palette["select_fg"],
            highlightthickness=0,
            relief="flat",
        )
        self._personality_text.pack(fill="both", expand=True)
        self._text_normal_fg = self._personality_text.cget("fg")
        if profile.personality:
            self._personality_text.insert("1.0", profile.personality)
        else:
            # Placeholder text
            placeholder = (
                "Exemplo:\n"
                "• Explique com exemplos práticos e analogias.\n"
                "• Quando eu errar, me mostre o raciocínio passo a passo.\n"
                "• Foque em preparação para provas.\n"
                "• Use português informal.\n"
                "• Quando possível, mostre como resolver de mais de uma forma."
            )
            self._personality_text.insert("1.0", placeholder)
            self._personality_text.config(fg="#888888")
            self._personality_text.bind("<FocusIn>", self._clear_placeholder)

        ttk.Button(self, text="💾  Salvar Perfil", style="Accent.TButton",
                   command=self._save).pack(fill="x", padx=14, pady=(0, 14))

    def _clear_placeholder(self, _event=None):
        if self._personality_text.get("1.0", "2.0").startswith("Exemplo:"):
            self._personality_text.delete("1.0", "end")
            self._personality_text.config(fg=self._text_normal_fg)

    def _save(self):
        sp = StudentProfile(
            full_name=self._vars["full_name"].get().strip(),
            nickname=self._vars["nickname"].get().strip(),
            personality=self._personality_text.get("1.0", "end-1c").strip(),
        )
        self._store.profile = sp
        self._store.save()
        messagebox.showinfo("Perfil", "Perfil salvo com sucesso!")
        self.destroy()


# ---------------------------------------------------------------------------
# GUI — Backlog Entry Edit Dialog
# ---------------------------------------------------------------------------

class BacklogEntryEditDialog(tk.Toplevel):
    """Edita metadados de uma entrada já processada, com visualização MD e PDF."""

    def __init__(self, parent, entry_data: dict, repo_dir=None, theme_mgr: ThemeManager = None):
        super().__init__(parent)
        self._data = dict(entry_data)
        self._repo_dir = Path(repo_dir) if repo_dir else None
        self._theme_mgr = theme_mgr
        self.result_data: Optional[dict] = None
        self.result_data: Optional[dict] = None
        self._current_md_source_path: Optional[Path] = None
        self._current_md_source_pdf: Optional[str] = None

        self.title("✏  Editar entrada do Backlog")
        self.geometry("900x600")
        self.minsize(700, 450)
        self.transient(parent)
        self.grab_set()

        # Apply theme
        if theme_mgr:
            self._p = theme_mgr.palette(theme_mgr.current)
        else:
            self._p = {"bg": "#1e1e2e", "fg": "#cdd6f4", "header_bg": "#181825",
                       "header_fg": "#cdd6f4", "input_bg": "#313244", "border": "#45475a",
                       "select_bg": "#585b70", "select_fg": "#cdd6f4", "frame_bg": "#1e1e2e",
                       "muted": "#6c7086", "accent": "#89b4fa"}
        p = self._p
        self.configure(bg=p["bg"])

        self._build_ui(p)

    def _build_ui(self, p):
        # ── Header ─────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=p["header_bg"], pady=8, padx=16)
        hdr.pack(fill="x")
        title_text = self._data.get("title", "Sem título")
        tk.Label(hdr, text=f"✏  {title_text}", bg=p["header_bg"], fg=p["header_fg"],
                 font=("Segoe UI", 12, "bold")).pack(side="left")

        # Buttons on header
        btn_frame = tk.Frame(hdr, bg=p["header_bg"])
        btn_frame.pack(side="right")
        ttk.Button(btn_frame, text="Salvar", command=self._on_save).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(side="left", padx=4)

        # ── Notebook ───────────────────────────────────────────────────
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        # ── Tab 1: Editar ──────────────────────────────────────────────
        tab_edit_outer = tk.Frame(nb, bg=p["bg"])
        nb.add(tab_edit_outer, text="  Editar  ")
        edit_canvas = tk.Canvas(tab_edit_outer, bg=p["bg"], highlightthickness=0, bd=0)
        edit_scroll = ttk.Scrollbar(tab_edit_outer, orient="vertical", command=edit_canvas.yview)
        edit_canvas.configure(yscrollcommand=edit_scroll.set)
        edit_scroll.pack(side="right", fill="y")
        edit_canvas.pack(side="left", fill="both", expand=True)

        tab_edit = tk.Frame(edit_canvas, bg=p["bg"], padx=16, pady=12)
        edit_window = edit_canvas.create_window((0, 0), window=tab_edit, anchor="nw")

        def _sync_edit_scrollregion(_event=None):
            edit_canvas.configure(scrollregion=edit_canvas.bbox("all"))

        def _resize_edit_width(event):
            edit_canvas.itemconfigure(edit_window, width=event.width)

        def _on_edit_mousewheel(event):
            delta = getattr(event, "delta", 0)
            if delta:
                edit_canvas.yview_scroll(int(-1 * (delta / 120)), "units")
                return
            num = getattr(event, "num", None)
            if num == 4:
                edit_canvas.yview_scroll(-1, "units")
            elif num == 5:
                edit_canvas.yview_scroll(1, "units")

        tab_edit.bind("<Configure>", _sync_edit_scrollregion)
        edit_canvas.bind("<Configure>", _resize_edit_width)
        edit_canvas.bind("<Enter>", lambda _e: edit_canvas.bind_all("<MouseWheel>", _on_edit_mousewheel))
        edit_canvas.bind("<Leave>", lambda _e: edit_canvas.unbind_all("<MouseWheel>"))
        edit_canvas.bind("<Enter>", lambda _e: edit_canvas.bind_all("<Button-4>", _on_edit_mousewheel), add="+")
        edit_canvas.bind("<Enter>", lambda _e: edit_canvas.bind_all("<Button-5>", _on_edit_mousewheel), add="+")
        edit_canvas.bind("<Leave>", lambda _e: edit_canvas.unbind_all("<Button-4>"), add="+")
        edit_canvas.bind("<Leave>", lambda _e: edit_canvas.unbind_all("<Button-5>"), add="+")
        tab_edit.columnconfigure(1, weight=1)

        fields = [
            ("Título",    "title"),
            ("Categoria", "category"),
            ("Perfil",    "document_profile"),
        ]

        self._vars: Dict[str, tk.StringVar] = {}
        for row, (label, key) in enumerate(fields):
            tk.Label(tab_edit, text=label, bg=p["bg"], fg=p["fg"],
                     font=("Segoe UI", 10)).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=6)
            if key == "document_profile":
                initial_value = normalize_document_profile(
                    self._data.get("document_profile") or self._data.get("effective_profile") or "auto"
                )
            else:
                initial_value = self._data.get(key, "")
            var = tk.StringVar(value=initial_value)
            self._vars[key] = var
            if key == "category":
                ttk.Combobox(tab_edit, textvariable=var, values=DEFAULT_CATEGORIES,
                             state="readonly", width=32).grid(row=row, column=1, sticky="ew", pady=6)
            elif key == "document_profile":
                from src.utils.helpers import DOCUMENT_PROFILES
                ttk.Combobox(tab_edit, textvariable=var, values=DOCUMENT_PROFILES,
                             state="readonly", width=32).grid(row=row, column=1, sticky="ew", pady=6)
            else:
                tk.Entry(tab_edit, textvariable=var, width=40,
                         bg=p["input_bg"], fg=p["fg"], insertbackground=p["fg"],
                         relief="flat", highlightthickness=1,
                         highlightcolor=p["border"], highlightbackground=p["border"],
                         font=("Segoe UI", 10)).grid(row=row, column=1, sticky="ew", pady=6)

        row_tags = len(fields)
        latex_warning = self._data.get("latex_corruption") or {}
        if isinstance(latex_warning, dict) and latex_warning.get("detected"):
            score = int(latex_warning.get("score", 0) or 0)
            signals = [str(signal).strip() for signal in (latex_warning.get("signals") or []) if str(signal).strip()]
            warning_frame = tk.Frame(
                tab_edit,
                bg=p["input_bg"],
                highlightthickness=1,
                highlightbackground=p["border"],
                padx=10,
                pady=8,
            )
            warning_frame.grid(row=row_tags, column=0, columnspan=2, sticky="ew", pady=(8, 6))
            tk.Label(
                warning_frame,
                text=f"⚠ LaTeX possivelmente corrompido (score: {score}/100)",
                bg=p["input_bg"],
                fg=p.get("warning", "#f9e2af"),
                font=("Segoe UI", 9, "bold"),
                justify="left",
            ).pack(anchor="w")
            signals_text = "\n".join(f"• {signal}" for signal in signals) if signals else "• Sinais heurísticos não detalhados."
            tk.Label(
                warning_frame,
                text=(
                    f"Sinais detectados:\n{signals_text}\n\n"
                    f"Recomendação: reprocessar com Marker ou Datalab se a notação formal estiver ilegível."
                ),
                bg=p["input_bg"],
                fg=p["muted"],
                font=("Segoe UI", 9),
                justify="left",
                wraplength=620,
            ).pack(anchor="w", pady=(6, 0))
            row_tags += 1

        tag_catalog = _load_tag_catalog(self._repo_dir)
        self._manual_tags_initial = list(self._data.get("manual_tags") or [])
        self._manual_tags_committed = [str(tag).strip() for tag in self._manual_tags_initial if str(tag).strip()]
        self._auto_tags_initial = list(self._data.get("auto_tags") or [])
        legacy_tags = str(self._data.get("tags") or "").strip()
        tag_summary = _format_backlog_tag_summary(
            self._manual_tags_committed,
            self._auto_tags_initial,
            legacy_tags,
        )

        tags_frame = tk.Frame(
            tab_edit,
            bg=p["input_bg"],
            highlightthickness=1,
            highlightbackground=p["border"],
            padx=10,
            pady=8,
        )
        tags_frame.grid(row=row_tags, column=0, columnspan=2, sticky="ew", pady=(10, 6))
        tags_frame.grid_columnconfigure(1, weight=1)

        self._tag_summary_manual_var = tk.StringVar(value=tag_summary["manual"])
        self._tag_summary_effective_var = tk.StringVar(value=tag_summary["effective"])
        self._tag_pending_var = tk.StringVar(value="Nenhuma alteração pendente nas tags manuais.")

        tk.Label(tags_frame, text="Tags manuais", bg=p["input_bg"], fg=p["muted"],
                 font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="nw", padx=(0, 12))
        tk.Label(tags_frame, textvariable=self._tag_summary_manual_var, bg=p["input_bg"], fg=p["fg"],
                 font=("Segoe UI", 9), wraplength=520, justify="left").grid(row=0, column=1, sticky="w")

        tk.Label(tags_frame, text="Tags automáticas", bg=p["input_bg"], fg=p["muted"],
                 font=("Segoe UI", 9, "bold")).grid(row=1, column=0, sticky="nw", padx=(0, 12), pady=(6, 0))
        tk.Label(tags_frame, text=tag_summary["auto"], bg=p["input_bg"], fg=p["fg"],
                 font=("Segoe UI", 9), wraplength=520, justify="left").grid(row=1, column=1, sticky="w", pady=(6, 0))

        tk.Label(tags_frame, text="Tags atribuídas", bg=p["input_bg"], fg=p["muted"],
                 font=("Segoe UI", 9, "bold")).grid(row=2, column=0, sticky="nw", padx=(0, 12), pady=(6, 0))
        tk.Label(tags_frame, textvariable=self._tag_summary_effective_var, bg=p["input_bg"], fg=p["fg"],
                 font=("Segoe UI", 9), wraplength=520, justify="left").grid(
            row=2, column=1, sticky="w", pady=(6, 0)
        )

        if legacy_tags:
            tk.Label(tags_frame, text="Campo legado", bg=p["input_bg"], fg=p["muted"],
                     font=("Segoe UI", 9)).grid(row=3, column=0, sticky="nw", padx=(0, 12), pady=(6, 0))
            tk.Label(tags_frame, text=legacy_tags, bg=p["input_bg"], fg=p["fg"],
                     font=("Consolas", 9), wraplength=520, justify="left").grid(
                row=3, column=1, sticky="w", pady=(6, 0)
            )

        tk.Label(tags_frame, text="Seleção manual", bg=p["input_bg"], fg=p["muted"],
                 font=("Segoe UI", 9)).grid(row=4, column=0, sticky="nw", padx=(0, 12), pady=(8, 0))
        if tag_catalog:
            list_frame = tk.Frame(tags_frame, bg=p["input_bg"])
            list_frame.grid(row=4, column=1, sticky="ew", pady=(8, 0))
            self._manual_tag_listbox = tk.Listbox(
                list_frame,
                selectmode=tk.MULTIPLE,
                exportselection=False,
                height=min(8, max(4, len(tag_catalog))),
                bg=p["bg"],
                fg=p["fg"],
                selectbackground=p["select_bg"],
                selectforeground=p["select_fg"],
                relief="flat",
                highlightthickness=1,
                highlightbackground=p["border"],
            )
            tag_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self._manual_tag_listbox.yview)
            self._manual_tag_listbox.configure(yscrollcommand=tag_scroll.set)
            self._manual_tag_listbox.pack(side="left", fill="both", expand=True)
            tag_scroll.pack(side="right", fill="y")
            self._tag_catalog = tag_catalog
            selected = set(_normalize_selected_manual_tags(self._manual_tags_initial, tag_catalog))
            for idx, tag in enumerate(tag_catalog):
                self._manual_tag_listbox.insert("end", tag)
                if tag in selected:
                    self._manual_tag_listbox.selection_set(idx)
            self._manual_tag_listbox.bind("<<ListboxSelect>>", self._on_manual_tag_selection_changed)
        else:
            self._manual_tag_listbox = None
            self._tag_catalog = []
            tk.Label(
                tags_frame,
                text="Nenhuma tag disponível no catálogo da disciplina ainda.",
                bg=p["input_bg"],
                fg=p["muted"],
                font=("Segoe UI", 9, "italic"),
                wraplength=520,
                justify="left",
            ).grid(row=4, column=1, sticky="w", pady=(8, 0))

        tag_actions = tk.Frame(tags_frame, bg=p["input_bg"])
        tag_actions.grid(row=5, column=1, sticky="w", pady=(8, 0))
        ttk.Button(tag_actions, text="Aplicar seleção", command=self._apply_manual_tag_selection).pack(side="left")
        ttk.Button(tag_actions, text="Limpar tags manuais", command=self._clear_manual_tags).pack(side="left", padx=(8, 0))

        tk.Label(
            tags_frame,
            textvariable=self._tag_pending_var,
            bg=p["input_bg"],
            fg=p["muted"],
            font=("Segoe UI", 9, "italic"),
            wraplength=520,
            justify="left",
        ).grid(row=6, column=1, sticky="w", pady=(6, 0))

        tk.Label(
            tags_frame,
            text="Selecione no catálogo e clique em “Aplicar seleção”. Para remover tags, desmarque-as e aplique novamente, ou use “Limpar tags manuais”.",
            bg=p["input_bg"],
            fg=p["muted"],
            font=("Segoe UI", 9),
            wraplength=520,
            justify="left",
        ).grid(row=7, column=1, sticky="w", pady=(4, 0))

        row_unit = row_tags + 1
        tk.Label(tab_edit, text="Unidade manual", bg=p["bg"], fg=p["fg"],
                 font=("Segoe UI", 10)).grid(row=row_unit, column=0, sticky="w", padx=(0, 12), pady=6)
        self._manual_unit_options = _load_file_map_unit_options(self._repo_dir)
        self._manual_unit_label_by_slug = {slug: label for label, slug in self._manual_unit_options}
        current_manual_unit = str(self._data.get("manual_unit_slug") or "").strip()
        self._manual_unit_committed = current_manual_unit
        unit_labels = ["Automático (usar matcher)"] + [label for label, _slug in self._manual_unit_options]
        self._manual_unit_var = tk.StringVar(value="Automático (usar matcher)")
        if current_manual_unit:
            for label, slug in self._manual_unit_options:
                if slug == current_manual_unit:
                    self._manual_unit_var.set(label)
                    break
        if len(unit_labels) > 1:
            unit_combo = ttk.Combobox(
                tab_edit,
                textvariable=self._manual_unit_var,
                values=unit_labels,
                state="readonly",
                width=42,
            )
            unit_combo.grid(row=row_unit, column=1, sticky="ew", pady=6)
            unit_combo.bind("<<ComboboxSelected>>", self._on_manual_unit_selection_changed)
        else:
            tk.Label(
                tab_edit,
                text="Nenhuma unidade disponível ainda. Gere ou reprocesse o COURSE_MAP para habilitar o override manual.",
                bg=p["bg"],
                fg=p["muted"],
                font=("Segoe UI", 9, "italic"),
                wraplength=520,
                justify="left",
            ).grid(row=row_unit, column=1, sticky="w", pady=6)

        unit_status = _resolve_backlog_unit_status(
            self._data,
            self._repo_dir,
            self._manual_unit_label_by_slug,
        )
        row_unit_status = row_unit + 1
        unit_frame = tk.Frame(
            tab_edit,
            bg=p["input_bg"],
            highlightthickness=1,
            highlightbackground=p["border"],
            padx=10,
            pady=8,
        )
        unit_frame.grid(row=row_unit_status, column=0, columnspan=2, sticky="ew", pady=(6, 4))
        unit_frame.grid_columnconfigure(1, weight=1)

        self._unit_assigned_var = tk.StringVar(value=unit_status["assigned"])
        self._unit_source_var = tk.StringVar(value=unit_status["source"])
        self._unit_note_var = tk.StringVar(value=unit_status["note"])
        self._unit_pending_var = tk.StringVar(value="Nenhuma alteração pendente na unidade manual.")

        tk.Label(unit_frame, text="Unidade atribuída", bg=p["input_bg"], fg=p["muted"],
                 font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", padx=(0, 12))
        tk.Label(unit_frame, textvariable=self._unit_assigned_var, bg=p["input_bg"], fg=p["fg"],
                 font=("Segoe UI", 9), wraplength=520, justify="left").grid(row=0, column=1, sticky="w")

        tk.Label(unit_frame, text="Origem", bg=p["input_bg"], fg=p["muted"],
                 font=("Segoe UI", 9)).grid(row=1, column=0, sticky="nw", padx=(0, 12), pady=(6, 0))
        tk.Label(unit_frame, textvariable=self._unit_source_var, bg=p["input_bg"], fg=p["fg"],
                 font=("Segoe UI", 9), wraplength=520, justify="left").grid(row=1, column=1, sticky="w", pady=(6, 0))

        tk.Label(unit_frame, text="Observação", bg=p["input_bg"], fg=p["muted"],
                 font=("Segoe UI", 9)).grid(row=2, column=0, sticky="nw", padx=(0, 12), pady=(6, 0))
        tk.Label(unit_frame, textvariable=self._unit_note_var, bg=p["input_bg"], fg=p["fg"],
                 font=("Segoe UI", 9), wraplength=520, justify="left").grid(row=2, column=1, sticky="w", pady=(6, 0))

        unit_actions = tk.Frame(unit_frame, bg=p["input_bg"])
        unit_actions.grid(row=3, column=1, sticky="w", pady=(8, 0))
        ttk.Button(unit_actions, text="Aplicar unidade", command=self._apply_manual_unit_selection).pack(side="left")
        ttk.Button(unit_actions, text="Voltar para automático", command=self._clear_manual_unit).pack(side="left", padx=(8, 0))

        tk.Label(
            unit_frame,
            textvariable=self._unit_pending_var,
            bg=p["input_bg"],
            fg=p["muted"],
            font=("Segoe UI", 9, "italic"),
            wraplength=520,
            justify="left",
        ).grid(row=4, column=1, sticky="w", pady=(6, 0))

        timeline_status = _resolve_backlog_timeline_status(self._data, self._repo_dir)
        row_timeline = row_unit_status + 1
        timeline_frame = tk.Frame(
            tab_edit,
            bg=p["input_bg"],
            highlightthickness=1,
            highlightbackground=p["border"],
            padx=10,
            pady=8,
        )
        timeline_frame.grid(row=row_timeline, column=0, columnspan=2, sticky="ew", pady=(6, 4))
        timeline_frame.grid_columnconfigure(1, weight=1)

        self._manual_timeline_options = _load_timeline_block_options(self._repo_dir)
        self._manual_timeline_label_by_id = {block_id: label for label, block_id in self._manual_timeline_options}
        current_manual_timeline = str(self._data.get("manual_timeline_block_id") or "").strip()
        self._manual_timeline_committed = current_manual_timeline
        timeline_labels = ["Automático (usar timeline index)"] + [label for label, _block_id in self._manual_timeline_options]
        self._manual_timeline_var = tk.StringVar(value="Automático (usar timeline index)")
        if current_manual_timeline:
            for label, block_id in self._manual_timeline_options:
                if block_id == current_manual_timeline:
                    self._manual_timeline_var.set(label)
                    break

        tk.Label(timeline_frame, text="Bloco manual", bg=p["input_bg"], fg=p["muted"],
                 font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", padx=(0, 12))
        if len(timeline_labels) > 1:
            timeline_combo = ttk.Combobox(
                timeline_frame,
                textvariable=self._manual_timeline_var,
                values=timeline_labels,
                state="readonly",
                width=52,
            )
            timeline_combo.grid(row=0, column=1, sticky="ew")
            timeline_combo.bind("<<ComboboxSelected>>", self._on_manual_timeline_selection_changed)
        else:
            tk.Label(
                timeline_frame,
                text="Nenhum bloco temporal disponível ainda. Reprocesse o repositório para gerar o timeline index.",
                bg=p["input_bg"],
                fg=p["muted"],
                font=("Segoe UI", 9, "italic"),
                wraplength=520,
                justify="left",
            ).grid(row=0, column=1, sticky="w")

        timeline_actions = tk.Frame(timeline_frame, bg=p["input_bg"])
        timeline_actions.grid(row=1, column=1, sticky="w", pady=(8, 0))
        ttk.Button(timeline_actions, text="Aplicar bloco", command=self._apply_manual_timeline_selection).pack(side="left")
        ttk.Button(timeline_actions, text="Voltar para automático", command=self._clear_manual_timeline).pack(side="left", padx=(8, 0))

        self._timeline_pending_var = tk.StringVar(value="Nenhuma alteração pendente no bloco temporal.")
        tk.Label(
            timeline_frame,
            textvariable=self._timeline_pending_var,
            bg=p["input_bg"],
            fg=p["muted"],
            font=("Segoe UI", 9, "italic"),
            wraplength=520,
            justify="left",
        ).grid(row=2, column=1, sticky="w", pady=(6, 0))

        self._timeline_period_var = tk.StringVar(value=timeline_status["period"])
        self._timeline_block_var = tk.StringVar(value=timeline_status["block"])
        self._timeline_topics_var = tk.StringVar(value=timeline_status["topics"])
        self._timeline_aliases_var = tk.StringVar(value=timeline_status["aliases"])
        self._timeline_note_var = tk.StringVar(value=timeline_status["note"])

        tk.Label(timeline_frame, text="Período do bloco", bg=p["input_bg"], fg=p["muted"],
                 font=("Segoe UI", 9, "bold")).grid(row=3, column=0, sticky="w", padx=(0, 12), pady=(6, 0))
        tk.Label(timeline_frame, textvariable=self._timeline_period_var, bg=p["input_bg"], fg=p["fg"],
                 font=("Segoe UI", 9), wraplength=520, justify="left").grid(row=3, column=1, sticky="w", pady=(6, 0))

        tk.Label(timeline_frame, text="ID do bloco", bg=p["input_bg"], fg=p["muted"],
                 font=("Segoe UI", 9)).grid(row=4, column=0, sticky="nw", padx=(0, 12), pady=(6, 0))
        tk.Label(timeline_frame, textvariable=self._timeline_block_var, bg=p["input_bg"], fg=p["fg"],
                 font=("Segoe UI", 9), wraplength=520, justify="left").grid(row=4, column=1, sticky="w", pady=(6, 0))

        tk.Label(timeline_frame, text="Tópicos do bloco", bg=p["input_bg"], fg=p["muted"],
                 font=("Segoe UI", 9)).grid(row=5, column=0, sticky="nw", padx=(0, 12), pady=(6, 0))
        tk.Label(timeline_frame, textvariable=self._timeline_topics_var, bg=p["input_bg"], fg=p["fg"],
                 font=("Segoe UI", 9), wraplength=520, justify="left").grid(row=5, column=1, sticky="w", pady=(6, 0))

        tk.Label(timeline_frame, text="Aliases", bg=p["input_bg"], fg=p["muted"],
                 font=("Segoe UI", 9)).grid(row=6, column=0, sticky="nw", padx=(0, 12), pady=(6, 0))
        tk.Label(timeline_frame, textvariable=self._timeline_aliases_var, bg=p["input_bg"], fg=p["fg"],
                 font=("Segoe UI", 9), wraplength=520, justify="left").grid(row=6, column=1, sticky="w", pady=(6, 0))

        tk.Label(timeline_frame, text="Observação", bg=p["input_bg"], fg=p["muted"],
                 font=("Segoe UI", 9)).grid(row=7, column=0, sticky="nw", padx=(0, 12), pady=(6, 0))
        tk.Label(timeline_frame, textvariable=self._timeline_note_var, bg=p["input_bg"], fg=p["fg"],
                 font=("Segoe UI", 9), wraplength=520, justify="left").grid(row=7, column=1, sticky="w", pady=(6, 0))

        row_notes = row_timeline + 1
        tk.Label(tab_edit, text="Notas", bg=p["bg"], fg=p["fg"],
                 font=("Segoe UI", 10)).grid(row=row_notes, column=0, sticky="nw", padx=(0, 12), pady=6)
        self._notes_text = tk.Text(tab_edit, height=4, width=40, font=("Segoe UI", 10), wrap="word",
                                   bg=p["input_bg"], fg=p["fg"], insertbackground=p["fg"],
                                   relief="flat", highlightthickness=1,
                                   highlightcolor=p["border"], highlightbackground=p["border"])
        self._notes_text.grid(row=row_notes, column=1, sticky="ew", pady=6)
        self._notes_text.insert("1.0", self._data.get("notes", ""))

        row_cb = row_notes + 1
        self._var_bundle = tk.BooleanVar(value=bool(self._data.get("include_in_bundle", True)))
        self._var_exam   = tk.BooleanVar(value=bool(self._data.get("relevant_for_exam", True)))
        ttk.Checkbutton(tab_edit, text="Incluir no bundle",   variable=self._var_bundle).grid(
            row=row_cb, column=0, columnspan=2, sticky="w", pady=(8, 2))
        ttk.Checkbutton(tab_edit, text="Relevante para prova", variable=self._var_exam).grid(
            row=row_cb + 1, column=0, columnspan=2, sticky="w", pady=2)

        row_status = row_cb + 2
        status = _resolve_backlog_markdown_status(self._data, self._repo_dir)
        status_frame = tk.Frame(
            tab_edit,
            bg=p["input_bg"],
            highlightthickness=1,
            highlightbackground=p["border"],
            padx=10,
            pady=8,
        )
        status_frame.grid(row=row_status, column=0, columnspan=2, sticky="ew", pady=(12, 4))
        status_frame.grid_columnconfigure(1, weight=1)

        status["status"] = status["status"].replace(
            "Processado (sÃƒÂ³ staging)",
            "Processado (s\u00f3 staging)",
        )
        status_color = {
            "Aprovado/final": "#a6e3a1",
            "Curado/final": "#a6e3a1",
            "Processado (s\u00f3 staging)": "#f9e2af",
            "Caminho quebrado": "#f38ba8",
            "Processado (sem markdown)": "#f38ba8",
            "Sem markdown": "#f38ba8",
        }.get(status["status"], p["accent"])

        tk.Label(status_frame, text="Estado do markdown", bg=p["input_bg"], fg=p["muted"],
                 font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", padx=(0, 12))
        tk.Label(status_frame, text=status["status"], bg=p["input_bg"], fg=status_color,
                 font=("Segoe UI", 10, "bold")).grid(row=0, column=1, sticky="w")

        tk.Label(status_frame, text="Caminho ativo", bg=p["input_bg"], fg=p["muted"],
                 font=("Segoe UI", 9)).grid(row=1, column=0, sticky="nw", padx=(0, 12), pady=(6, 0))
        tk.Label(status_frame, text=status["path"] or "—", bg=p["input_bg"], fg=p["fg"],
                 font=("Consolas", 9), wraplength=520, justify="left").grid(
            row=1, column=1, sticky="w", pady=(6, 0)
        )

        tk.Label(status_frame, text="Observação", bg=p["input_bg"], fg=p["muted"],
                 font=("Segoe UI", 9)).grid(row=2, column=0, sticky="nw", padx=(0, 12), pady=(6, 0))
        tk.Label(status_frame, text=status["note"], bg=p["input_bg"], fg=p["fg"],
                 font=("Segoe UI", 9), wraplength=520, justify="left").grid(
            row=2, column=1, sticky="w", pady=(6, 0)
        )

        if status["needs_reprocess"] == "true":
            tk.Label(
                status_frame,
                text="Ação sugerida: reprocessar o repositório para promover esse material a um markdown final.",
                bg=p["input_bg"],
                fg="#f9e2af",
                font=("Segoe UI", 9, "italic"),
                wraplength=640,
                justify="left",
            ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 0))

        # ── Tab 2: Visualização MD ─────────────────────────────────────
        tab_md = tk.Frame(nb, bg=p["bg"], padx=8, pady=5)
        nb.add(tab_md, text="  Visualização MD  ")
        self._build_md_tab(tab_md, p)

        # ── Tab 3: Imagens Extraídas ──────────────────────────────────
        tab_imgs = tk.Frame(nb, bg=p["bg"], padx=8, pady=5)
        nb.add(tab_imgs, text="  Imagens  ")
        self._build_images_tab(tab_imgs, p)

    _IMG_EXTS = ("*.png", "*.jpg", "*.jpeg", "*.webp", "*.bmp")

    def _build_images_tab(self, parent, p):
        """Build the extracted images gallery tab."""
        self._img_refs = []  # keep references to prevent GC

        # Collect images from entry-specific sources (dedup by resolved path)
        seen_paths: set = set()
        images_found: List[Path] = []

        def _collect_from(directory: Path):
            if not directory.exists():
                return
            for ext in self._IMG_EXTS:
                for img in directory.glob(ext):
                    resolved = img.resolve()
                    if resolved not in seen_paths:
                        seen_paths.add(resolved)
                        images_found.append(img)

        if self._repo_dir:
            for directory in _entry_image_source_dirs(self._repo_dir, self._data):
                _collect_from(directory)
        images_found.sort(key=lambda x: x.name)

        # Filter noise images (too small, solid color, extreme aspect ratio)
        def _is_useful(img_path: Path) -> bool:
            if img_path.stat().st_size < 2000:
                return False
            try:
                from PIL import Image as PILImage
                img = PILImage.open(img_path)
                w, h = img.size
                if w < 20 or h < 20:
                    return False
                if max(w / h, h / w) > 8.0:
                    return False
                colors = img.getcolors(maxcolors=5)
                if colors is not None and len(colors) <= 4:
                    return False
            except Exception:
                return False
            return True
        images_found = [f for f in images_found if _is_useful(f)]

        # Header with count
        hdr = tk.Frame(parent, bg=p["bg"])
        hdr.pack(fill="x", pady=(0, 5))
        tk.Label(hdr, text=f"{len(images_found)} imagem(ns) extraída(s)",
                 bg=p["bg"], fg=p["muted"], font=("Segoe UI", 9)).pack(side="left")

        if not images_found:
            tk.Label(parent, text="Nenhuma imagem extraída para este arquivo.",
                     bg=p["bg"], fg=p["muted"], font=("Segoe UI", 10)).pack(pady=30)
            return

        # Scrollable canvas
        canvas = tk.Canvas(parent, bg=p["bg"], highlightthickness=0)
        scroll = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=p["bg"])
        canvas_win = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_win, width=e.width))

        def _on_mousewheel(event):
            try:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except tk.TclError:
                pass
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        # Render images in a grid (2 columns)
        target_width = 380
        col_count = 2
        for idx, img_path in enumerate(images_found):
            try:
                from PIL import Image as PILImage, ImageTk as PILImageTk
                pil_img = PILImage.open(img_path)
                w, h = pil_img.size
                new_w = min(target_width, w)
                new_h = int(new_w * (h / w))
                pil_img = pil_img.resize((new_w, new_h), PILImage.Resampling.LANCZOS)
                tk_img = PILImageTk.PhotoImage(pil_img)
                self._img_refs.append(tk_img)

                row = idx // col_count
                col = idx % col_count

                frame = tk.Frame(inner, bg=p["input_bg"], padx=4, pady=4)
                frame.grid(row=row * 2, column=col, padx=6, pady=6, sticky="n")

                lbl_img = tk.Label(frame, image=tk_img, bg=p["input_bg"])
                lbl_img.pack()

                lbl_name = tk.Label(frame, text=img_path.name, bg=p["input_bg"], fg=p["muted"],
                                    font=("Consolas", 8), wraplength=target_width)
                lbl_name.pack(pady=(2, 0))
            except Exception:
                pass

    def _parse_md_frontmatter(self, fpath: Path) -> Dict[str, str]:
        """Parse simples do frontmatter YAML do markdown selecionado."""
        try:
            content = fpath.read_text("utf-8", errors="replace")
        except Exception:
            return {}

        lines = content.splitlines()
        if not lines or lines[0].strip() != "---":
            return {}

        fm: Dict[str, str] = {}
        for line in lines[1:]:
            if line.strip() == "---":
                break
            if ":" not in line:
                continue
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if value.lower() in ("null", "none"):
                value = ""
            fm[key] = value
        return fm

    def _add_md_source(self, display: str, path: Path) -> None:
        """Adiciona uma fonte MD ao combobox, evitando duplicatas."""
        if not path.exists():
            return

        try:
            candidate = path.resolve()
        except Exception:
            candidate = path

        for existing in self._md_sources.values():
            try:
                if existing.resolve() == candidate:
                    return
            except Exception:
                if existing == path:
                    return

        self._md_sources[display] = path

    def _approved_md_candidates(self) -> List[Tuple[str, Path]]:
        """
        Retorna possíveis markdowns aprovados pelo Curator Studio.
        O Curator copia o arquivo aprovado para uma pasta final, mas hoje
        o manifest não é atualizado com esse novo caminho.
        """
        if not self._repo_dir:
            return []

        entry_id = self._data.get("id")
        if not entry_id:
            return []

        candidates = [
            ("Aprovado — content/curated", self._repo_dir / "content" / "curated" / f"{entry_id}.md"),
            ("Aprovado — exercises/lists", self._repo_dir / "exercises" / "lists" / f"{entry_id}.md"),
            ("Aprovado — exams/past-exams", self._repo_dir / "exams" / "past-exams" / f"{entry_id}.md"),
        ]

        return [(label, path) for label, path in candidates if path.exists()]
    def _build_md_tab(self, parent, p):
        """Build the markdown visualization tab with PDF button."""
        toolbar = tk.Frame(parent, bg=p["bg"])
        toolbar.pack(fill="x", pady=(0, 5))

        tk.Label(toolbar, text="Fonte:", bg=p["bg"], fg=p["fg"],
                 font=("Segoe UI", 9, "bold")).pack(side="left")

        self._md_source_var = tk.StringVar()
        self._md_source_combo = ttk.Combobox(
            toolbar,
            textvariable=self._md_source_var,
            state="readonly",
            width=50,
        )
        self._md_source_combo.pack(side="left", padx=5)
        self._md_source_combo.bind("<<ComboboxSelected>>", self._on_md_source_changed)

        ttk.Button(toolbar, text="📄 Ver PDF Original", command=self._open_pdf_viewer).pack(side="right", padx=5)

        self._md_stats_var = tk.StringVar(value="")
        tk.Label(parent, textvariable=self._md_stats_var, bg=p["bg"], fg=p["muted"],
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 3))

        viewer_frame = tk.Frame(parent, bg=p["bg"])
        viewer_frame.pack(fill="both", expand=True)

        self._md_text = tk.Text(
            viewer_frame,
            wrap="word",
            font=("Consolas", 10),
            state="disabled",
            bg=p["input_bg"],
            fg=p["fg"],
            insertbackground=p["fg"],
            relief="flat",
            highlightthickness=1,
            highlightcolor=p["border"],
            highlightbackground=p["border"],
            selectbackground=p["select_bg"],
            selectforeground=p["select_fg"],
        )
        scroll = ttk.Scrollbar(viewer_frame, orient="vertical", command=self._md_text.yview)
        self._md_text.configure(yscrollcommand=scroll.set)
        self._md_text.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self._md_text.tag_configure("heading", font=("Segoe UI", 12, "bold"), foreground="#89b4fa")
        self._md_text.tag_configure("latex", foreground="#f9e2af", font=("Consolas", 10, "italic"))
        self._md_text.tag_configure("code", background="#45475a", font=("Consolas", 10))
        self._md_text.tag_configure("table_row", foreground="#a6e3a1")

        # Populate sources
        self._md_sources: Dict[str, Path] = {}

        if self._repo_dir:
            # 1) Primeiro tenta arquivos já aprovados pelo Curator Studio
            for label, path in self._approved_md_candidates():
                self._add_md_source(f"{label} ({path.name})", path)

            # 2) Depois tenta as fontes clássicas do manifest
            for key, label in [
                ("base_markdown", "Base"),
                ("advanced_markdown", "Avançado"),
                ("manual_review", "Revisão"),
            ]:
                val = self._data.get(key)
                if not val:
                    continue

                path = self._repo_dir / val
                if not path.exists():
                    continue

                if key == "base_markdown":
                    backend = self._data.get("base_backend", "")
                elif key == "advanced_markdown":
                    backend = self._data.get("advanced_backend", "")
                else:
                    backend = ""

                display = f"{label} — {backend} ({path.name})" if backend else f"{label} ({path.name})"
                self._add_md_source(display, path)

        self._md_source_combo["values"] = list(self._md_sources.keys())

        if self._md_sources:
            first = list(self._md_sources.keys())[0]
            self._md_source_var.set(first)
            self._load_md_content(self._md_sources[first])
        else:
            self._current_md_source_path = None
            self._current_md_source_pdf = None
            self._md_stats_var.set("Nenhum markdown disponível para esta entrada.")

    def _on_md_source_changed(self, _event=None):
        name = self._md_source_var.get()
        if name in self._md_sources:
            self._load_md_content(self._md_sources[name])

    def _load_md_content(self, fpath: Path):
        self._current_md_source_path = fpath
        fm = self._parse_md_frontmatter(fpath)
        self._current_md_source_pdf = fm.get("source_pdf") or self._data.get("raw_target")

        try:
            content = fpath.read_text("utf-8", errors="replace")
        except Exception as e:
            content = f"Erro ao ler arquivo: {e}"

        lines = content.split("\n")
        latex_count = content.count("$")
        latex_blocks = content.count("$$")
        img_refs = content.count("![")

        self._md_stats_var.set(
            f"{len(lines)} linhas  |  "
            f"LaTeX inline: ~{latex_count - latex_blocks * 2}  |  "
            f"LaTeX blocos: {latex_blocks}  |  "
            f"Imagens: {img_refs}"
        )

        self._md_text.configure(state="normal")
        self._md_text.delete("1.0", "end")
        self._md_text.insert("1.0", content)

        for i, line in enumerate(lines, 1):
            tag = f"{i}.0"
            tag_end = f"{i}.end"
            if line.startswith("#"):
                self._md_text.tag_add("heading", tag, tag_end)
            elif "$$" in line or line.strip().startswith("\\"):
                self._md_text.tag_add("latex", tag, tag_end)
            elif "$" in line:
                self._md_text.tag_add("latex", tag, tag_end)
            elif line.startswith("|") and "|" in line[1:]:
                self._md_text.tag_add("table_row", tag, tag_end)
            elif line.startswith("```"):
                self._md_text.tag_add("code", tag, tag_end)

        self._md_text.configure(state="disabled")

    def _open_pdf_viewer(self):
        """Open the original PDF associated with the currently selected markdown source."""
        if not self._repo_dir:
            return

        raw_target = self._current_md_source_pdf or self._data.get("raw_target")
        if not raw_target:
            messagebox.showinfo("PDF", "Nenhum PDF original associado a esta entrada.")
            return

        pdf_path = Path(raw_target)
        if not pdf_path.is_absolute():
            pdf_path = self._repo_dir / raw_target

        if not pdf_path.exists():
            messagebox.showinfo("PDF", f"Arquivo não encontrado:\n{pdf_path}")
            return

        os.startfile(str(pdf_path))

    def _on_save(self):
        pending_manual_tags = self._current_manual_tag_selection()
        committed_manual_tags = list(getattr(self, "_manual_tags_committed", []))
        if pending_manual_tags != committed_manual_tags:
            decision = messagebox.askyesnocancel(
                "Tags manuais",
                "Há uma seleção de tags manuais ainda não aplicada.\n\n"
                "Deseja aplicar a seleção atual à entry antes de salvar?",
                parent=self,
            )
            if decision is None:
                return
            if decision:
                self._apply_manual_tag_selection(confirm=False)
        pending_manual_unit = self._current_manual_unit_selection_slug()
        committed_manual_unit = str(getattr(self, "_manual_unit_committed", "") or "").strip()
        if pending_manual_unit != committed_manual_unit:
            decision = messagebox.askyesnocancel(
                "Unidade manual",
                "Há uma seleção de unidade manual ainda não aplicada.\n\n"
                "Deseja aplicar a seleção atual à entry antes de salvar?",
                parent=self,
            )
            if decision is None:
                return
            if decision:
                self._apply_manual_unit_selection(confirm=False)
        pending_manual_timeline = self._current_manual_timeline_selection_id()
        committed_manual_timeline = str(getattr(self, "_manual_timeline_committed", "") or "").strip()
        if pending_manual_timeline != committed_manual_timeline:
            decision = messagebox.askyesnocancel(
                "Bloco temporal manual",
                "Há uma seleção de bloco temporal ainda não aplicada.\n\n"
                "Deseja aplicar a seleção atual à entry antes de salvar?",
                parent=self,
            )
            if decision is None:
                return
            if decision:
                self._apply_manual_timeline_selection(confirm=False)
        profile_var = self._vars.get("document_profile") or self._vars.get("effective_profile")
        profile = normalize_document_profile(profile_var.get().strip() if profile_var else "auto")
        self.result_data = {
            "title":            self._vars["title"].get().strip(),
            "category":         self._vars["category"].get().strip(),
            "tags":             str(self._data.get("tags") or "").strip(),
            "manual_tags":      self._selected_manual_tags(),
            "auto_tags":        list(self._data.get("auto_tags") or []),
            "manual_unit_slug": self._selected_manual_unit_slug(),
            "manual_timeline_block_id": self._selected_manual_timeline_block_id(),
            "document_profile": profile,
            "effective_profile": profile,
            "notes":            self._notes_text.get("1.0", "end-1c").strip(),
            "include_in_bundle": self._var_bundle.get(),
            "relevant_for_exam": self._var_exam.get(),
        }
        self.destroy()

    def _selected_manual_tags(self) -> List[str]:
        if hasattr(self, "_manual_tags_committed"):
            return list(getattr(self, "_manual_tags_committed", []))
        if not getattr(self, "_manual_tag_listbox", None):
            return _normalize_selected_manual_tags(self._manual_tags_initial, getattr(self, "_tag_catalog", []))
        return self._current_manual_tag_selection()

    def _selected_manual_unit_slug(self) -> str:
        if hasattr(self, "_manual_unit_committed"):
            return str(getattr(self, "_manual_unit_committed", "") or "").strip()
        return self._current_manual_unit_selection_slug()

    def _selected_manual_timeline_block_id(self) -> str:
        if hasattr(self, "_manual_timeline_committed"):
            return str(getattr(self, "_manual_timeline_committed", "") or "").strip()
        return self._current_manual_timeline_selection_id()

    def _current_manual_tag_selection(self) -> List[str]:
        if not getattr(self, "_manual_tag_listbox", None):
            return list(getattr(self, "_manual_tags_committed", []))
        selected_indices = self._manual_tag_listbox.curselection()
        selected_tags = [self._manual_tag_listbox.get(i) for i in selected_indices]
        return _normalize_selected_manual_tags(selected_tags, getattr(self, "_tag_catalog", []))

    def _refresh_tag_summary_display(self) -> None:
        summary = _format_backlog_tag_summary(
            list(getattr(self, "_manual_tags_committed", [])),
            self._auto_tags_initial,
            str(self._data.get("tags") or "").strip(),
        )
        if hasattr(self, "_tag_summary_manual_var"):
            self._tag_summary_manual_var.set(summary["manual"])
        if hasattr(self, "_tag_summary_effective_var"):
            self._tag_summary_effective_var.set(summary["effective"])
        self._update_manual_tag_pending_state()

    def _update_manual_tag_pending_state(self) -> None:
        pending = self._current_manual_tag_selection()
        committed = list(getattr(self, "_manual_tags_committed", []))
        if pending == committed:
            self._tag_pending_var.set("Nenhuma alteração pendente nas tags manuais.")
            return
        if pending:
            self._tag_pending_var.set(
                "Seleção pendente: clique em “Aplicar seleção” para atribuir estas tags à entry."
            )
        else:
            self._tag_pending_var.set(
                "Remoção pendente: clique em “Aplicar seleção” ou “Limpar tags manuais” para remover as tags manuais."
            )

    def _on_manual_tag_selection_changed(self, _event=None) -> None:
        self._update_manual_tag_pending_state()

    def _apply_manual_tag_selection(self, confirm: bool = True) -> None:
        selected = self._current_manual_tag_selection()
        committed = list(getattr(self, "_manual_tags_committed", []))
        if selected == committed:
            self._update_manual_tag_pending_state()
            return
        if confirm:
            target_text = ", ".join(selected) if selected else "nenhuma tag manual"
            should_apply = messagebox.askyesno(
                "Aplicar tags manuais",
                f"Deseja aplicar esta seleção à entry?\n\n{target_text}",
                parent=self,
            )
            if not should_apply:
                return
        self._manual_tags_committed = selected
        self._data["manual_tags"] = list(selected)
        self._refresh_tag_summary_display()

    def _clear_manual_tags(self) -> None:
        committed = list(getattr(self, "_manual_tags_committed", []))
        if not committed and not self._current_manual_tag_selection():
            self._update_manual_tag_pending_state()
            return
        should_clear = messagebox.askyesno(
            "Limpar tags manuais",
            "Deseja remover todas as tags manuais atribuídas a esta entry?",
            parent=self,
        )
        if not should_clear:
            return
        if getattr(self, "_manual_tag_listbox", None):
            self._manual_tag_listbox.selection_clear(0, "end")
        self._manual_tags_committed = []
        self._data["manual_tags"] = []
        self._refresh_tag_summary_display()

    def _current_manual_unit_selection_slug(self) -> str:
        selected = str(getattr(self, "_manual_unit_var", tk.StringVar(value="")).get() or "").strip()
        if not selected or selected.startswith("Automático"):
            return ""
        for label, slug in getattr(self, "_manual_unit_options", []):
            if label == selected:
                return slug
        return ""

    def _refresh_unit_status_display(self) -> None:
        entry_view = dict(self._data)
        entry_view["manual_unit_slug"] = str(getattr(self, "_manual_unit_committed", "") or "").strip()
        unit_status = _resolve_backlog_unit_status(
            entry_view,
            self._repo_dir,
            getattr(self, "_manual_unit_label_by_slug", {}),
        )
        if hasattr(self, "_unit_assigned_var"):
            self._unit_assigned_var.set(unit_status["assigned"])
        if hasattr(self, "_unit_source_var"):
            self._unit_source_var.set(unit_status["source"])
        if hasattr(self, "_unit_note_var"):
            self._unit_note_var.set(unit_status["note"])
        self._update_manual_unit_pending_state()

    def _update_manual_unit_pending_state(self) -> None:
        pending = self._current_manual_unit_selection_slug()
        committed = str(getattr(self, "_manual_unit_committed", "") or "").strip()
        if pending == committed:
            self._unit_pending_var.set("Nenhuma alteração pendente na unidade manual.")
            return
        if pending:
            label = getattr(self, "_manual_unit_label_by_slug", {}).get(pending, pending)
            self._unit_pending_var.set(
                f"Seleção pendente: clique em “Aplicar unidade” para salvar `{label}` como override manual."
            )
            return
        self._unit_pending_var.set(
            "Remoção pendente: clique em “Aplicar unidade” ou “Voltar para automático” para remover o override manual."
        )

    def _on_manual_unit_selection_changed(self, _event=None) -> None:
        self._update_manual_unit_pending_state()

    def _apply_manual_unit_selection(self, confirm: bool = True) -> None:
        selected = self._current_manual_unit_selection_slug()
        committed = str(getattr(self, "_manual_unit_committed", "") or "").strip()
        if selected == committed:
            self._update_manual_unit_pending_state()
            return
        if confirm:
            selected_label = getattr(self, "_manual_unit_label_by_slug", {}).get(selected, "Automático (usar matcher)")
            should_apply = messagebox.askyesno(
                "Aplicar unidade manual",
                f"Deseja aplicar esta configuração de unidade à entry?\n\n{selected_label}",
                parent=self,
            )
            if not should_apply:
                return
        self._manual_unit_committed = selected
        self._data["manual_unit_slug"] = selected
        self._refresh_unit_status_display()

    def _clear_manual_unit(self) -> None:
        committed = str(getattr(self, "_manual_unit_committed", "") or "").strip()
        if not committed and not self._current_manual_unit_selection_slug():
            self._update_manual_unit_pending_state()
            return
        should_clear = messagebox.askyesno(
            "Voltar para automático",
            "Deseja remover o override manual e voltar a usar o matcher automático para a unidade desta entry?",
            parent=self,
        )
        if not should_clear:
            return
        if hasattr(self, "_manual_unit_var"):
            self._manual_unit_var.set("Automático (usar matcher)")
        self._manual_unit_committed = ""
        self._data["manual_unit_slug"] = ""
        self._refresh_unit_status_display()

    def _current_manual_timeline_selection_id(self) -> str:
        selected = str(getattr(self, "_manual_timeline_var", tk.StringVar(value="")).get() or "").strip()
        if not selected or selected.startswith("Automático"):
            return ""
        for label, block_id in getattr(self, "_manual_timeline_options", []):
            if label == selected:
                return block_id
        return ""

    def _refresh_timeline_status_display(self) -> None:
        entry_view = dict(self._data)
        entry_view["manual_timeline_block_id"] = str(getattr(self, "_manual_timeline_committed", "") or "").strip()
        timeline_status = _resolve_backlog_timeline_status(entry_view, self._repo_dir)
        if hasattr(self, "_timeline_period_var"):
            self._timeline_period_var.set(timeline_status["period"])
        if hasattr(self, "_timeline_block_var"):
            self._timeline_block_var.set(timeline_status["block"])
        if hasattr(self, "_timeline_topics_var"):
            self._timeline_topics_var.set(timeline_status["topics"])
        if hasattr(self, "_timeline_aliases_var"):
            self._timeline_aliases_var.set(timeline_status["aliases"])
        if hasattr(self, "_timeline_note_var"):
            self._timeline_note_var.set(timeline_status["note"])
        self._update_manual_timeline_pending_state()

    def _update_manual_timeline_pending_state(self) -> None:
        pending = self._current_manual_timeline_selection_id()
        committed = str(getattr(self, "_manual_timeline_committed", "") or "").strip()
        if pending == committed:
            self._timeline_pending_var.set("Nenhuma alteração pendente no bloco temporal.")
            return
        if pending:
            label = getattr(self, "_manual_timeline_label_by_id", {}).get(pending, pending)
            self._timeline_pending_var.set(
                f"Seleção pendente: clique em “Aplicar bloco” para salvar `{label}` como override temporal."
            )
            return
        self._timeline_pending_var.set(
            "Remoção pendente: clique em “Aplicar bloco” ou “Voltar para automático” para remover o override temporal."
        )

    def _on_manual_timeline_selection_changed(self, _event=None) -> None:
        self._update_manual_timeline_pending_state()

    def _apply_manual_timeline_selection(self, confirm: bool = True) -> None:
        selected = self._current_manual_timeline_selection_id()
        committed = str(getattr(self, "_manual_timeline_committed", "") or "").strip()
        if selected == committed:
            self._update_manual_timeline_pending_state()
            return
        if confirm:
            selected_label = getattr(self, "_manual_timeline_label_by_id", {}).get(selected, "Automático (usar timeline index)")
            should_apply = messagebox.askyesno(
                "Aplicar bloco temporal manual",
                f"Deseja aplicar esta configuração temporal à entry?\n\n{selected_label}",
                parent=self,
            )
            if not should_apply:
                return
        self._manual_timeline_committed = selected
        self._data["manual_timeline_block_id"] = selected
        self._refresh_timeline_status_display()

    def _clear_manual_timeline(self) -> None:
        committed = str(getattr(self, "_manual_timeline_committed", "") or "").strip()
        if not committed and not self._current_manual_timeline_selection_id():
            self._update_manual_timeline_pending_state()
            return
        should_clear = messagebox.askyesno(
            "Voltar para automático",
            "Deseja remover o override temporal e voltar a usar o timeline index automático para esta entry?",
            parent=self,
        )
        if not should_clear:
            return
        if hasattr(self, "_manual_timeline_var"):
            self._manual_timeline_var.set("Automático (usar timeline index)")
        self._manual_timeline_committed = ""
        self._data["manual_timeline_block_id"] = ""
        self._refresh_timeline_status_display()

# ---------------------------------------------------------------------------
# GUI — FileEntryDialog & App
# ---------------------------------------------------------------------------

class FileEntryDialog(simpledialog.Dialog):
    def __init__(self, parent, path: str, initial: Optional[FileEntry] = None,
                 default_mode: str = "auto", default_ocr_language: str = DEFAULT_OCR_LANGUAGE,
                 file_type_hint: str = ""):
        self._parent = parent
        self.path = path
        self.initial = initial
        self.default_mode = default_mode
        self.default_ocr_language = default_ocr_language
        self.file_type_hint = file_type_hint
        self.result_entry: Optional[FileEntry] = None
        super().__init__(parent, title="Editar item")

    _FILE_TYPES = ["pdf", "image", "url", "code", "zip", "github-repo"]
    
    def _get_palette(self) -> Dict[str, str]:
        theme_name = getattr(self._parent, "_theme_name", "dark")
        return THEMES.get(theme_name, THEMES["dark"])

    def buttonbox(self):
        """Rodapé customizado no tema do app, substituindo o buttonbox branco do simpledialog."""
        p = self._get_palette()

        box = tk.Frame(self, bg=p["bg"], padx=12, pady=12)
        box.pack(fill="x")

        btn_cancel = ttk.Button(box, text="Cancel", command=self.cancel)
        btn_cancel.pack(side="right", padx=(8, 0))

        btn_ok = ttk.Button(box, text="OK", style="Accent.TButton", command=self.ok)
        btn_ok.pack(side="right")

        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

        try:
            btn_ok.focus_set()
        except Exception:
            pass
    
    

    def body(self, master):
        p = self._get_palette()
        self.configure(bg=p["bg"])
        master.configure(bg=p["bg"])
        self._theme_name = getattr(self._parent, "_theme_name", "dark")

        src = Path(self.path)

        if self.initial:
            self.file_type = self.initial.file_type
        elif self.file_type_hint:
            self.file_type = self.file_type_hint
        elif src.suffix.lower() == ".pdf":
            self.file_type = "pdf"
        elif src.suffix.lower() == ".zip":
            self.file_type = "zip"
        elif src.suffix.lower() in CODE_EXTENSIONS:
            self.file_type = "code"
        else:
            self.file_type = "image"

        # Notebook com duas abas
        nb = ttk.Notebook(master)
        nb.pack(fill="both", expand=True)

        tab_config = ttk.Frame(nb, padding=8)
        nb.add(tab_config, text="  \u2699 Configurar  ")

        tab_preview = tk.Frame(nb, bg=p["bg"])
        nb.add(tab_preview, text="  \U0001f441 Visualizar  ")

        self._build_preview_tab(tab_preview, p)

        # --- All config fields go into tab_config ---
        outer = tab_config

        ttk.Label(outer, text=f"Arquivo: {src.name}", style="Accent.TLabel").grid(
            row=0, column=0, columnspan=4, sticky="w", pady=(0, 10))

        self.var_title = tk.StringVar(value=self.initial.title if self.initial else auto_detect_title(self.path))
        self.var_category = tk.StringVar(value=self.initial.category if self.initial else auto_detect_category(src.name, self.file_type == "image"))
        self.var_tags = tk.StringVar(value=self.initial.tags if self.initial else "")
        self.var_notes = tk.StringVar(value=self.initial.notes if self.initial else "")
        self.var_prof = tk.StringVar(value=self.initial.professor_signal if self.initial else "")
        self.var_bundle = tk.BooleanVar(value=self.initial.include_in_bundle if self.initial else True)
        self.var_exam = tk.BooleanVar(value=self.initial.relevant_for_exam if self.initial else True)

        self.var_mode = tk.StringVar(value=self.initial.processing_mode if self.initial else self.default_mode)
        self.var_profile = tk.StringVar(
            value=normalize_document_profile(self.initial.document_profile if self.initial else "auto")
        )
        self.var_backend = tk.StringVar(value=self.initial.preferred_backend if self.initial else "auto")
        self.var_datalab_mode = tk.StringVar(value=getattr(self.initial, "datalab_mode", "accurate") if self.initial else "accurate")
        self.var_formula = tk.BooleanVar(value=self.initial.formula_priority if self.initial else False)
        self.var_keep_images = tk.BooleanVar(value=self.initial.preserve_pdf_images_in_markdown if self.initial else True)
        self.var_force_ocr = tk.BooleanVar(value=self.initial.force_ocr if self.initial else False)
        self.var_imgs = tk.BooleanVar(value=self.initial.extract_images if self.initial else True)
        self.var_tables = tk.BooleanVar(value=self.initial.extract_tables if self.initial else True)
        self.var_page_range = tk.StringVar(value=self.initial.page_range if self.initial else "")
        self.var_ocr_lang = tk.StringVar(value=self.initial.ocr_language if self.initial else self.default_ocr_language)

        self.var_file_type = tk.StringVar(value=self.file_type)

        row = 1

        lbl_title = ttk.Label(outer, text="Título")
        lbl_title.grid(row=row, column=0, sticky="w", pady=4)
        add_tooltip(lbl_title, "Nome legível do documento. Aparece nos metadados e no índice do repositório.")
        ttk.Entry(outer, textvariable=self.var_title, width=54).grid(row=row, column=1, columnspan=3, sticky="ew")
        row += 1

        # Language field for code files
        self.var_language = tk.StringVar(
            value=self.initial.tags if self.initial and self.file_type == "code"
            else src.suffix.lower().lstrip(".") if self.file_type == "code" else "")
        self._lang_label = ttk.Label(outer, text="Linguagem")
        self._lang_entry = ttk.Entry(outer, textvariable=self.var_language, width=20)
        if self.file_type == "code":
            self._lang_label.grid(row=row, column=0, sticky="w", pady=4)
            self._lang_entry.grid(row=row, column=1, sticky="w")
            row += 1
        self._lang_row = row - 1 if self.file_type == "code" else None

        lbl_type = ttk.Label(outer, text="Tipo")
        lbl_type.grid(row=row, column=0, sticky="w", pady=4)
        add_tooltip(lbl_type, "Tipo do item.\npdf → documento PDF\nimage → imagem (foto de prova, slide, etc.)\nurl → link web (YouTube, artigo, etc.)")
        cb_type = ttk.Combobox(outer, textvariable=self.var_file_type, values=self._FILE_TYPES, state="readonly", width=22)
        cb_type.grid(row=row, column=1, sticky="ew")
        cb_type.bind("<<ComboboxSelected>>", self._on_type_changed)
        row += 1

        lbl_cat = ttk.Label(outer, text="Categoria")
        lbl_cat.grid(row=row, column=0, sticky="w", pady=4)
        add_tooltip(lbl_cat, "Classifica o arquivo na estrutura do repositório.\nExemplos: material-de-aula, provas, listas, gabaritos, referencias, bibliografia, trabalhos, codigo-professor, codigo-aluno, quadro-branco.")
        ttk.Combobox(outer, textvariable=self.var_category, values=DEFAULT_CATEGORIES, state="readonly", width=22).grid(row=row, column=1, sticky="ew")

        lbl_mode = ttk.Label(outer, text="Modo")
        lbl_mode.grid(row=row, column=2, sticky="w", padx=(12, 0))
        add_tooltip(lbl_mode, "Controla o pipeline de processamento.\nauto → decide pelo perfil do documento\nquick → só backend base (rápido)\nhigh_fidelity → base + avançado\nmanual_assisted → base + avançado + revisão humana guiada")
        ttk.Combobox(outer, textvariable=self.var_mode, values=PROCESSING_MODES, state="readonly", width=20).grid(row=row, column=3, sticky="ew")
        row += 1

        lbl_profile = ttk.Label(outer, text="Perfil")
        lbl_profile.grid(row=row, column=0, sticky="w", pady=4)
        combo_profile = ttk.Combobox(outer, textvariable=self.var_profile, values=DOCUMENT_PROFILES, state="readonly", width=22)
        combo_profile.grid(row=row, column=1, sticky="ew")
        combo_profile.bind("<<ComboboxSelected>>", self._on_profile_changed)

        lbl_backend = ttk.Label(outer, text="Backend preferido")
        lbl_backend.grid(row=row, column=2, sticky="w", padx=(12, 0))
        add_tooltip(lbl_backend, "Backend de extração preferido.\nauto → seleção automática\npymupdf4llm → rápido e bom para PDFs digitais\npymupdf → fallback básico\ndatalab → API cloud para markdown de alta qualidade em PDFs complexos\ndocling → avançado: OCR, fórmulas, tabelas (CLI externo)\ndocling_python → teste via API Python do Docling com formula enrichment\nmarker → avançado: equações e imagens (CLI externo)")
        combo_backend = ttk.Combobox(outer, textvariable=self.var_backend, values=PREFERRED_BACKENDS, state="readonly", width=20)
        combo_backend.grid(row=row, column=3, sticky="ew")
        combo_backend.bind("<<ComboboxSelected>>", self._on_backend_changed)
        add_tooltip(lbl_profile, PROFILE_TOOLTIP_TEXT)
        row += 1

        self._datalab_model_row = row
        self._datalab_model_label = ttk.Label(outer, text="Modelo")
        add_tooltip(
            self._datalab_model_label,
            "Modo da API do Datalab.\nfast → menor custo/latência\nbalanced → equilíbrio geral\naccurate → maior qualidade para PDFs complexos e math_heavy.",
        )
        self._datalab_model_combo = ttk.Combobox(
            outer,
            textvariable=self.var_datalab_mode,
            values=["fast", "balanced", "accurate"],
            state="readonly",
            width=20,
        )
        row += 1

        lbl_tags = ttk.Label(outer, text="Tags")
        lbl_tags.grid(row=row, column=0, sticky="w", pady=4)
        add_tooltip(lbl_tags, "Palavras-chave separadas por vírgula para facilitar busca futura.\nExemplo: gabarito, integração, 2024-1")
        ttk.Entry(outer, textvariable=self.var_tags, width=26).grid(row=row, column=1, sticky="ew")

        lbl_ocr = ttk.Label(outer, text="OCR lang")
        lbl_ocr.grid(row=row, column=2, sticky="w", padx=(12, 0))
        add_tooltip(lbl_ocr, "Idioma(s) para o OCR.\npor,eng → Português + Inglês (padrão recomendado)\npor → só Português | eng → só Inglês")
        ttk.Combobox(outer, textvariable=self.var_ocr_lang, values=OCR_LANGS, width=20).grid(row=row, column=3, sticky="ew")
        row += 1

        lbl_notes = ttk.Label(outer, text="Notas")
        lbl_notes.grid(row=row, column=0, sticky="w", pady=4)
        add_tooltip(lbl_notes, "Observação livre sobre o arquivo. Não afeta o processamento, apenas fica registrado nos metadados.")
        ttk.Entry(outer, textvariable=self.var_notes, width=54).grid(row=row, column=1, columnspan=3, sticky="ew")
        row += 1

        lbl_prof = ttk.Label(outer, text="Pista do professor")
        lbl_prof.grid(row=row, column=0, sticky="w", pady=4)
        add_tooltip(lbl_prof, "Padrões observados no estilo do professor: tipo de cobrança, notação preferida, nível de detalhe.\nExemplo: cobra demonstração formal; mistura indução e recursão")
        ttk.Entry(outer, textvariable=self.var_prof, width=54).grid(row=row, column=1, columnspan=3, sticky="ew")
        row += 1

        cb_exam = ttk.Checkbutton(outer, text="Relevante para prova", variable=self.var_exam)
        cb_exam.grid(row=row, column=0, sticky="w", pady=4)
        add_tooltip(cb_exam, "Marca este material como importante para preparação de provas. Afeta priorização pedagógica e o bundle inicial.")

        cb_bundle = ttk.Checkbutton(outer, text="Incluir no bundle inicial", variable=self.var_bundle)
        cb_bundle.grid(row=row, column=1, sticky="w")
        add_tooltip(cb_bundle, "Se marcado, o arquivo entra no bundle.seed.json como conhecimento base prioritário do repositório.")

        cb_formula = ttk.Checkbutton(outer, text="Prioridade em fórmulas", variable=self.var_formula)
        cb_formula.grid(row=row, column=2, sticky="w")
        add_tooltip(cb_formula, "Força ativação do backend avançado (docling/marker) mesmo em modo auto ou quick.\nUse quando o documento tem muitas equações matemáticas críticas.")
        row += 1

        # --- PDF-only options frame ---
        self._pdf_frame = ttk.LabelFrame(outer, text="Opções de PDF", padding=4)
        self._pdf_row = row  # remember grid row for show/hide

        pr = 0
        cb_keep = ttk.Checkbutton(self._pdf_frame, text="Preservar imagens do PDF no Markdown base", variable=self.var_keep_images)
        cb_keep.grid(row=pr, column=0, columnspan=2, sticky="w", pady=4)
        add_tooltip(cb_keep, "Se marcado, o pymupdf4llm extrai as imagens embutidas no PDF e as referencia no Markdown. Útil para manter figuras após a extração.")

        cb_ocr = ttk.Checkbutton(self._pdf_frame, text="Forçar OCR", variable=self.var_force_ocr)
        cb_ocr.grid(row=pr, column=2, sticky="w")
        add_tooltip(cb_ocr, "Ignora o texto digital do PDF e passa tudo pelo OCR.\nUse para PDFs com texto não selecionável, imagens de texto, ou codificação incorreta.")
        pr += 1

        cb_imgs = ttk.Checkbutton(self._pdf_frame, text="Extrair imagens do PDF", variable=self.var_imgs)
        cb_imgs.grid(row=pr, column=0, sticky="w")
        add_tooltip(cb_imgs, "Extrai todas as imagens embutidas no PDF para staging/assets/images/.\nRequer PyMuPDF instalado.")

        cb_tbl = ttk.Checkbutton(self._pdf_frame, text="Extrair tabelas", variable=self.var_tables)
        cb_tbl.grid(row=pr, column=2, sticky="w")
        add_tooltip(cb_tbl, "Detecta e exporta tabelas como CSV e Markdown em staging/assets/tables/.\nRequer pdfplumber e/ou PyMuPDF instalados.")
        pr += 1

        lbl_pr = ttk.Label(self._pdf_frame, text="Page range")
        lbl_pr.grid(row=pr, column=0, sticky="w", pady=4)
        add_tooltip(lbl_pr, 'Limita o processamento a páginas específicas. Deixe vazio para processar todas.\nFormatos aceitos: "1-5" (págs 1 a 5) | "1,3,7" (págs específicas) | "2, 5-8" (misto)\nNota: sem o zero, é interpretado como base-1 (página 1 = primeira página).')
        ttk.Entry(self._pdf_frame, textvariable=self.var_page_range, width=18).grid(row=pr, column=1, sticky="w")
        ttk.Label(self._pdf_frame, text='Ex.: "1-4" ou "0,2,5-7"', style="Muted.TLabel").grid(row=pr, column=2, columnspan=2, sticky="w")

        self._pdf_frame.columnconfigure(1, weight=1)

        # Show/hide based on current type
        self._update_pdf_frame_visibility()
        self._update_datalab_mode_visibility()

        outer.columnconfigure(1, weight=1)
        outer.columnconfigure(3, weight=1)
        return master

    def _on_type_changed(self, _event=None):
        self.file_type = self.var_file_type.get()
        self._update_pdf_frame_visibility()
        self._update_datalab_mode_visibility()

    def _update_datalab_mode_visibility(self):
        if self.file_type == "pdf" and self.var_backend.get() == "datalab":
            self._datalab_model_label.grid(row=self._datalab_model_row, column=2, sticky="w", padx=(12, 0), pady=4)
            self._datalab_model_combo.grid(row=self._datalab_model_row, column=3, sticky="ew")
        else:
            self._datalab_model_label.grid_remove()
            self._datalab_model_combo.grid_remove()

    def _on_backend_changed(self, _event=None):
        if self.var_backend.get() == "datalab" and not self.var_datalab_mode.get():
            self.var_datalab_mode.set("accurate")
        self._update_datalab_mode_visibility()

    def _on_profile_changed(self, _event=None):
        """Quando o perfil muda, ajusta backend e modo automaticamente.
        Presets baseados no nível de complexidade do documento."""
        profile = normalize_document_profile(self.var_profile.get())
        self.var_profile.set(profile)
        # Reset para defaults antes de aplicar preset
        self.var_formula.set(False)
        self.var_force_ocr.set(False)

        if profile == "auto":
            # Texto simples, sem fórmulas → rápido
            self.var_mode.set("auto")
            self.var_backend.set("auto")
        elif profile == "diagram_heavy":
            # Algumas fórmulas → docling sem enrich-formula
            self.var_mode.set("high_fidelity")
            self.var_backend.set("docling")
        elif profile == "math_heavy":
            # Muitas fórmulas → docling com enrich-formula
            self.var_mode.set("high_fidelity")
            self.var_backend.set("marker")
            self.var_formula.set(True)
        elif profile == "scanned":
            # PDF digitalizado/foto → força OCR
            self.var_mode.set("auto")
            self.var_backend.set("auto")
            self.var_force_ocr.set(True)
        self._update_datalab_mode_visibility()

    def _update_pdf_frame_visibility(self):
        if self.file_type == "pdf":
            self._pdf_frame.grid(row=self._pdf_row, column=0, columnspan=4, sticky="ew", pady=(4, 0))
        else:
            self._pdf_frame.grid_remove()

    def _build_preview_tab(self, parent, p):
        """Preview do arquivo: imagem direta ou primeiras páginas do PDF."""
        file_type = getattr(self, "file_type",
                            self.file_type_hint or
                            (self.initial.file_type if self.initial else ""))
        path = Path(self.path) if self.path else None

        if file_type == "image" and path and path.exists():
            try:
                from PIL import Image as PILImage, ImageTk
                img = PILImage.open(path)
                img.thumbnail((560, 460))
                photo = ImageTk.PhotoImage(img)
                lbl = tk.Label(parent, image=photo, bg=p["bg"])
                lbl.image = photo  # prevent GC
                lbl.pack(expand=True, pady=8)
            except Exception as e:
                ttk.Label(parent,
                          text="Erro ao carregar imagem:\n{}".format(e),
                          style="Muted.TLabel",
                          justify="center").pack(expand=True)

        elif file_type == "pdf" and path and path.exists():
            frame = tk.Frame(parent, bg=p["bg"])
            frame.pack(fill="both", expand=True)

            v_scroll = ttk.Scrollbar(frame, orient="vertical")
            v_scroll.pack(side="right", fill="y")

            canvas = tk.Canvas(frame,
                               bg=p["frame_bg"],
                               yscrollcommand=v_scroll.set,
                               highlightthickness=0)
            canvas.pack(fill="both", expand=True)
            v_scroll.configure(command=canvas.yview)

            canvas.bind("<MouseWheel>",
                        lambda e: canvas.yview_scroll(
                            int(-1 * (e.delta / 120)), "units"))

            self._preview_photos = []
            loading_lbl = ttk.Label(parent, text="\u23f3 Carregando\u2026",
                                    style="Muted.TLabel")
            loading_lbl.pack(pady=4)

            def _render():
                try:
                    import fitz
                    from PIL import Image as PILImage, ImageTk
                    doc = fitz.open(str(path))
                    photos = []
                    for i in range(min(3, len(doc))):
                        pix = doc[i].get_pixmap(matrix=fitz.Matrix(1.2, 1.2))
                        img = PILImage.frombytes(
                            "RGB", [pix.width, pix.height], pix.samples)
                        photos.append(ImageTk.PhotoImage(img))
                    doc.close()
                    canvas.after(0, lambda ph=photos: _display(ph))
                except Exception as ex:
                    canvas.after(0, lambda: ttk.Label(
                        parent,
                        text="Erro ao renderizar PDF:\n{}".format(ex),
                        style="Muted.TLabel",
                        justify="center").pack(expand=True))

            def _display(photos):
                try:
                    loading_lbl.destroy()
                except Exception:
                    pass
                self._preview_photos = photos
                y = 8
                for photo in photos:
                    canvas.create_image(4, y, anchor="nw", image=photo)
                    y += photo.height() + 8
                if photos:
                    canvas.configure(
                        scrollregion=(0, 0, photos[0].width() + 8, y))

            import threading
            threading.Thread(target=_render, daemon=True).start()

        else:
            icons = {
                "url": "\U0001f517", "code": "\U0001f4bb", "zip": "\U0001f4e6",
                "github-repo": "\U0001f419", "": "\U0001f4c4",
            }
            icon = icons.get(file_type, "\U0001f4c4")
            msg = ("{} Pre-visualização não disponível\n"
                   "para o tipo '{}'.".format(icon, file_type or 'desconhecido'))
            ttk.Label(parent, text=msg,
                      style="Muted.TLabel",
                      justify="center").pack(expand=True)

    def apply(self):
        # For code files, tags come from the language field
        tags = (self.var_language.get().strip()
                if self.file_type == "code"
                else self.var_tags.get().strip())
        self.result_entry = FileEntry(
            source_path=self.path,
            file_type=self.file_type,
            category=self.var_category.get(),
            title=self.var_title.get().strip() or Path(self.path).stem,
            tags=tags,
            notes=self.var_notes.get().strip(),
            professor_signal=self.var_prof.get().strip(),
            relevant_for_exam=self.var_exam.get(),
            include_in_bundle=self.var_bundle.get(),
            processing_mode=self.var_mode.get(),
            document_profile=self.var_profile.get(),
            preferred_backend=self.var_backend.get(),
            datalab_mode=self.var_datalab_mode.get().strip() or "accurate",
            formula_priority=self.var_formula.get() if self.file_type == "pdf" else False,
            preserve_pdf_images_in_markdown=self.var_keep_images.get() if self.file_type == "pdf" else False,
            force_ocr=self.var_force_ocr.get() if self.file_type == "pdf" else False,
            extract_images=self.var_imgs.get() if self.file_type == "pdf" else False,
            extract_tables=self.var_tables.get() if self.file_type == "pdf" else False,
            page_range=self.var_page_range.get().strip() if self.file_type == "pdf" else "",
            ocr_language=self.var_ocr_lang.get().strip() or self.default_ocr_language,
        )


def _is_github_repo(url: str) -> bool:
    """Detecta se a URL é um repositório GitHub (não um arquivo dentro dele)."""
    import re
    url = url.strip().rstrip("/")
    return bool(re.match(
        r'^https?://github\.com/[\w.-]+/[\w.-]+(\.git)?$', url))


def _resolve_backlog_markdown_status(entry_data: dict, repo_dir: Optional[Path]) -> Dict[str, str]:
    """Resolve o estado do markdown de uma entry processada para a UI do backlog."""
    final_prefixes = (
        "content/",
        "exercises/",
        "exams/",
        "code/",
        "references/",
        "bibliography/",
        "assignments/",
        "whiteboards/",
    )
    entry_id = str(entry_data.get("id") or "").strip()
    if repo_dir and entry_id:
        final_candidates = [
            repo_dir / "content" / "curated" / f"{entry_id}.md",
            repo_dir / "exercises" / "lists" / f"{entry_id}.md",
            repo_dir / "exams" / "past-exams" / f"{entry_id}.md",
        ]
        for path in final_candidates:
            if path.exists():
                return {
                    "status": "Curado/final",
                    "path": str(path.relative_to(repo_dir)).replace("\\", "/"),
                    "source_key": "derived_final_markdown",
                    "needs_reprocess": "false",
                    "note": "Markdown final detectado no repositório, mesmo que o manifest ainda esteja desatualizado.",
                }

    candidates = [
        ("approved_markdown", entry_data.get("approved_markdown") or ""),
        ("curated_markdown", entry_data.get("curated_markdown") or ""),
        ("advanced_markdown", entry_data.get("advanced_markdown") or ""),
        ("base_markdown", entry_data.get("base_markdown") or ""),
    ]

    for key, rel in candidates:
        rel = str(rel or "").strip()
        if not rel or not rel.lower().endswith(".md"):
            continue
        rel_posix = rel.replace("\\", "/")
        if rel_posix.startswith("staging/"):
            return {
                "status": "Processado (s\u00f3 staging)",
                "path": rel,
                "source_key": key,
                "needs_reprocess": "true",
                "note": "Ainda não foi promovido para um destino final; reprocessar ou revisar.",
            }
        exists = bool(repo_dir and (repo_dir / rel).exists())
        if rel_posix.startswith(final_prefixes):
            return {
                "status": "Aprovado/final" if key == "approved_markdown" else "Curado/final",
                "path": rel,
                "source_key": key,
                "needs_reprocess": "false",
                "note": "Markdown final pronto para o tutor.",
            }
        if exists:
            return {
                "status": "Markdown externo",
                "path": rel,
                "source_key": key,
                "needs_reprocess": "false",
                "note": "Markdown existe fora dos destinos padrão finais.",
            }
        return {
            "status": "Caminho quebrado",
            "path": rel,
            "source_key": key,
            "needs_reprocess": "true",
            "note": "O manifest aponta para um markdown que não existe mais.",
        }

    return {
        "status": "Processado (sem markdown)",
        "path": "",
        "source_key": "",
        "needs_reprocess": "true",
        "note": "Nenhum markdown associado à entry.",
    }


def _find_backlog_file_map_row(entry_data: dict, repo_dir: Optional[Path]) -> Dict[str, str]:
    if not repo_dir:
        return {}
    file_map_path = repo_dir / "course" / "FILE_MAP.md"
    if not file_map_path.exists():
        return {}

    title = str(entry_data.get("title") or "").strip()
    category = str(entry_data.get("category") or "").strip()
    if not title:
        return {}

    try:
        current_headers: List[str] = []
        for line in file_map_path.read_text(encoding="utf-8").splitlines():
            if not line.startswith("|"):
                continue
            parts = [part.strip() for part in line.split("|")[1:-1]]
            if not parts:
                continue
            if "Título" in parts and "Categoria" in parts:
                current_headers = parts
                continue
            if current_headers and len(parts) != len(current_headers):
                continue
            if parts[0] in {"#", ""} or parts[0].startswith("---") or "rastreabilidade" in parts:
                continue
            if current_headers:
                row = {current_headers[idx]: parts[idx] for idx in range(len(parts))}
                row_title = str(row.get("Título") or "").strip()
                row_category = str(row.get("Categoria") or "").strip()
                if row_title != title:
                    continue
                if category and row_category and row_category != category:
                    continue
                return {
                    "title": row_title,
                    "category": row_category,
                    "markdown": str(row.get("Markdown") or "").strip(),
                    "sections": str(row.get("Seções") or "").strip(),
                    "unit": str(row.get("Unidade") or "").strip(),
                    "confidence": str(row.get("Confiança") or "").strip(),
                    "period": str(row.get("Período") or "").strip(),
                }

            if len(parts) < 8:
                continue
            if parts[1] != title:
                continue
            if category and parts[2] and parts[2] != category:
                continue
            return {
                "title": parts[1],
                "category": parts[2],
                "markdown": parts[5],
                "unit": parts[6],
                "period": parts[7],
            }
    except Exception:
        return {}
    return {}


def _resolve_backlog_unit_status(
    entry_data: dict,
    repo_dir: Optional[Path],
    unit_label_by_slug: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    unit_label_by_slug = unit_label_by_slug or {}
    manual_slug = str(entry_data.get("manual_unit_slug") or "").strip()
    title = str(entry_data.get("title") or "").strip()
    category = str(entry_data.get("category") or "").strip()
    file_map_row = _find_backlog_file_map_row(
        {"title": title, "category": category},
        repo_dir,
    )
    current_unit_cell = str(file_map_row.get("unit") or "").strip()

    def _display_unit(slug: str) -> str:
        return unit_label_by_slug.get(slug, slug) if slug else "—"

    current_slug_match = re.search(r"(unidade-[a-z0-9-]+)", current_unit_cell or "")
    current_slug = current_slug_match.group(1) if current_slug_match else ""

    if manual_slug:
        assigned = _display_unit(manual_slug)
        if current_slug == manual_slug:
            return {
                "assigned": assigned,
                "source": "Override manual aplicado",
                "note": "O FILE_MAP atual já reflete a unidade manual selecionada.",
            }
        if current_unit_cell:
            return {
                "assigned": assigned,
                "source": "Override manual salvo",
                "note": f"O FILE_MAP atual ainda mostra `{current_unit_cell}`; reprocesse o repositório para aplicar a unidade manual.",
            }
        return {
            "assigned": assigned,
            "source": "Override manual salvo",
            "note": "A unidade manual já está salva nesta entry; reprocesse o repositório para refletir isso no FILE_MAP.",
        }

    if current_unit_cell:
        return {
            "assigned": current_unit_cell,
            "source": "FILE_MAP atual",
            "note": "Unidade atribuída automaticamente com base no FILE_MAP gerado no último processamento.",
        }

    return {
        "assigned": "—",
        "source": "Sem atribuição",
        "note": "Nenhuma unidade atribuída ainda para esta entry.",
    }


def _resolve_backlog_timeline_status(entry_data: dict, repo_dir: Optional[Path]) -> Dict[str, str]:
    file_map_row = _find_backlog_file_map_row(entry_data, repo_dir)
    period = str(file_map_row.get("period") or "").strip()
    unit_cell = str(file_map_row.get("unit") or "").strip()
    manual_slug = str(entry_data.get("manual_unit_slug") or "").strip()
    manual_block_id = str(entry_data.get("manual_timeline_block_id") or "").strip()

    if not period:
        note = "A entry ainda não tem período preenchido no FILE_MAP."
        if manual_slug:
            note += " Há override manual de unidade salvo; reprocesse o repositório para recalcular a conexão temporal."
        return {
            "period": "—",
            "block": "—",
            "topics": "—",
            "aliases": "—",
            "note": note,
        }

    timeline_path = repo_dir / "course" / ".timeline_index.json" if repo_dir else None
    if not timeline_path or not timeline_path.exists():
        return {
            "period": _format_timeline_period_text(period),
            "block": "—",
            "topics": "—",
            "aliases": "—",
            "note": "Há período no FILE_MAP, mas o índice temporal interno ainda não foi encontrado.",
        }

    unit_slug_match = re.search(r"(unidade-[a-z0-9-]+)", unit_cell)
    unit_slug = unit_slug_match.group(1) if unit_slug_match else ""

    try:
        payload = json.loads(timeline_path.read_text(encoding="utf-8"))
    except Exception:
        return {
            "period": _format_timeline_period_text(period),
            "block": "—",
            "topics": "—",
            "aliases": "—",
            "note": "O índice temporal interno existe, mas não pôde ser lido.",
        }

    blocks = list(payload.get("blocks") or [])
    if manual_block_id:
        manual_matches = [block for block in blocks if str(block.get("id") or "").strip() == manual_block_id]
        if manual_matches:
            block = manual_matches[0]
            topics = ", ".join(str(item).strip() for item in list(block.get("topics") or [])[:4] if str(item).strip()) or "—"
            aliases = ", ".join(str(item).strip() for item in list(block.get("aliases") or [])[:4] if str(item).strip()) or "—"
            block_period = _timeline_block_display_period(block)
            if _format_timeline_label_dates(period) == block_period:
                note = "Bloco manual já refletido no FILE_MAP atual."
            else:
                note = "Bloco manual salvo; reprocesse o repositório para refletir esse período no FILE_MAP."
            return {
                "period": block_period,
                "block": str(block.get("id") or "—"),
                "topics": topics,
                "aliases": aliases,
                "note": note,
            }
        return {
            "period": _format_timeline_period_text(period) or "—",
            "block": manual_block_id,
            "topics": "—",
            "aliases": "—",
            "note": "Há um bloco manual salvo, mas ele não foi encontrado no timeline index atual.",
        }

    exact_matches = [block for block in blocks if str(block.get("period_label") or "").strip() == period]
    overlap_matches = [block for block in blocks if _periods_overlap(period, str(block.get("period_label") or "").strip())]

    candidate_blocks = exact_matches or overlap_matches or list(blocks)
    if unit_slug:
        unit_filtered = [block for block in candidate_blocks if str(block.get("unit_slug") or "").strip() == unit_slug]
        if unit_filtered:
            candidate_blocks = unit_filtered

    if not candidate_blocks:
        return {
            "period": _format_timeline_period_text(period),
            "block": "—",
            "topics": "—",
            "aliases": "—",
            "note": "Há período no FILE_MAP, mas nenhum bloco correspondente foi localizado no timeline index atual.",
        }

    markdown_text = _entry_markdown_text_for_file_map(repo_dir, entry_data) if repo_dir else ""
    scored_blocks = [
        (
            block,
            _score_serialized_timeline_block(
                entry_data,
                markdown_text,
                block,
                preferred_unit_slug=unit_slug,
                preferred_period=period,
            ),
        )
        for block in candidate_blocks
    ]
    scored_blocks.sort(key=lambda item: item[1], reverse=True)
    block, best_score = scored_blocks[0]
    runner_up_score = scored_blocks[1][1] if len(scored_blocks) > 1 else 0.0

    sessions = list(block.get("sessions") or [])
    session_preview = _timeline_block_session_preview(block)
    card_preview = _timeline_block_card_evidence_preview(block)
    session_signals = []
    for session in sessions:
        if not isinstance(session, dict):
            continue
        for signal in list(session.get("signals") or []):
            value = str(signal).strip()
            if value:
                session_signals.append(value)

    topics_list = [str(item).strip() for item in list(block.get("topics") or [])[:4] if str(item).strip()]
    aliases_list = [str(item).strip() for item in list(block.get("aliases") or [])[:4] if str(item).strip()]
    if not topics_list and session_preview:
        topics_list = session_preview[:4]
    if not topics_list and card_preview:
        topics_list = card_preview[:4]
    if not aliases_list and session_signals:
        aliases_list = session_signals[:4]
    if not aliases_list and not session_signals and card_preview:
        aliases_list = card_preview[:4]

    topics = ", ".join(topics_list) or "—"
    aliases = ", ".join(aliases_list) or "—"
    note = "Período do FILE_MAP conectado a este bloco do cronograma via `course/.timeline_index.json`."
    if session_preview:
        note += f" Sessões normalizadas: {len(sessions)}."
    if card_preview and not session_preview and not block.get("topics"):
        note += f" Evidências de card: {len(card_preview)}."
    if overlap_matches and not exact_matches:
        note = (
            "Período do FILE_MAP foi reconciliado por sobreposição de datas e sinais do conteúdo da entry "
            f"(score: {best_score:.2f})."
        )
        if session_preview:
            note += f" Sessões normalizadas: {len(sessions)}."
    elif len(scored_blocks) > 1 and abs(best_score - runner_up_score) < 0.20:
        note = (
            "Bloco selecionado heurísticamente entre múltiplos candidatos próximos; "
            f"revise manualmente se o cronograma parecer incorreto (score: {best_score:.2f})."
        )
        if session_preview:
            note += f" Sessões normalizadas: {len(sessions)}."

    return {
        "period": _timeline_block_display_period(block),
        "block": str(block.get("id") or "—"),
        "topics": topics,
        "aliases": aliases,
        "note": note,
    }


def _load_tag_catalog(repo_dir: Optional[Path]) -> List[str]:
    if not repo_dir:
        return []
    catalog_path = repo_dir / "course" / ".tag_catalog.json"
    if not catalog_path.exists():
        return []
    try:
        payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    except Exception:
        return []
    tags = payload.get("tags") or []
    cleaned: List[str] = []
    seen = set()
    for tag in tags:
        value = str(tag).strip()
        if not value or value in seen:
            continue
        cleaned.append(value)
        seen.add(value)
    return cleaned


def _load_file_map_unit_options(repo_dir: Optional[Path]) -> List[Tuple[str, str]]:
    if not repo_dir:
        return []

    options: List[Tuple[str, str]] = []
    seen = set()

    course_map_path = repo_dir / "course" / "COURSE_MAP.md"
    if course_map_path.exists():
        try:
            content = course_map_path.read_text(encoding="utf-8")
            for line in content.splitlines():
                if not line.startswith("| Unidade "):
                    continue
                parts = [part.strip() for part in line.split("|")[1:-1]]
                if len(parts) < 3:
                    continue
                label = parts[0]
                match = re.search(r"`([^`]+)`", parts[2])
                slug = match.group(1).strip() if match else ""
                if not slug or slug in seen:
                    continue
                options.append((f"{label} ({slug})", slug))
                seen.add(slug)
        except Exception:
            pass

    if options:
        return options

    try:
        subject_store = SubjectStore()
        repo_resolved = repo_dir.resolve()
        subject = None
        for name in subject_store.names():
            candidate = subject_store.get(name)
            if not candidate or not getattr(candidate, "repo_root", ""):
                continue
            try:
                if Path(candidate.repo_root).resolve() == repo_resolved:
                    subject = candidate
                    break
            except Exception:
                continue
        if subject and getattr(subject, "teaching_plan", ""):
            from src.builder.engine import _normalize_unit_slug, _parse_units_from_teaching_plan

            for title, _topics in _parse_units_from_teaching_plan(subject.teaching_plan):
                slug = _normalize_unit_slug(title)
                if slug and slug not in seen:
                    options.append((f"{title} ({slug})", slug))
                    seen.add(slug)
    except Exception:
        pass

    return options


def _format_timeline_label_dates(text: str) -> str:
    value = str(text or "").strip()
    if not value:
        return ""

    def _replace_date(match: re.Match) -> str:
        raw = match.group(0)
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(raw, fmt).strftime("%d/%m/%Y")
            except ValueError:
                continue
        return raw

    normalized = re.sub(
        r"\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4}",
        _replace_date,
        value,
    )
    normalized = re.sub(
        r"(\d{2}/\d{2}/\d{4})\s*[–—-]\s*(\d{2}/\d{2}/\d{4})",
        r"\1 a \2",
        normalized,
    )
    return normalized


def _format_timeline_period_text(text: str) -> str:
    start, end = _parse_period_bounds(text)
    if start and end:
        return f"{start.strftime('%d/%m/%Y')} a {end.strftime('%d/%m/%Y')}"
    return _format_timeline_label_dates(text)


def _parse_period_bounds(text: str) -> Tuple[Optional[datetime], Optional[datetime]]:
    value = str(text or "").strip()
    if not value:
        return None, None
    found = re.findall(r"\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4}", value)
    if not found:
        return None, None

    def _parse_one(raw: str) -> Optional[datetime]:
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(raw, fmt)
            except ValueError:
                continue
        return None

    start = _parse_one(found[0])
    end = _parse_one(found[1]) if len(found) > 1 else start
    if start and end and start > end:
        start, end = end, start
    return start, end


def _periods_overlap(left: str, right: str) -> bool:
    left_start, left_end = _parse_period_bounds(left)
    right_start, right_end = _parse_period_bounds(right)
    if not left_start or not left_end or not right_start or not right_end:
        return False
    return left_start <= right_end and right_start <= left_end


def _timeline_block_display_period(block: Dict[str, object]) -> str:
    start_text = str(block.get("period_start") or "").strip()
    end_text = str(block.get("period_end") or "").strip()
    if start_text or end_text:
        return _format_timeline_period_text(f"{start_text} a {end_text}")
    return _format_timeline_period_text(str(block.get("period_label") or "").strip())


def _timeline_block_session_preview(block: Dict[str, object], limit: int = 2) -> List[str]:
    sessions = list(block.get("sessions") or [])
    preview: List[str] = []
    seen: set[str] = set()

    for session in sessions:
        if not isinstance(session, dict):
            continue
        label = str(session.get("label") or "").strip()
        if not label:
            continue

        date = str(session.get("date") or "").strip()
        kind = str(session.get("kind") or "").strip()
        parts: List[str] = []
        if date:
            parts.append(_format_timeline_period_text(date))
        if kind and kind not in {"class", "lecture"}:
            parts.append(kind)

        if parts:
            label = f"{label} ({', '.join(parts)})"

        normalized = _normalize_match_text(label)
        if normalized in seen:
            continue
        seen.add(normalized)
        preview.append(label)
        if len(preview) >= max(1, limit):
            break

    return preview


def _timeline_block_card_evidence_preview(block: Dict[str, object], limit: int = 2) -> List[str]:
    card_items = list(block.get("card_evidence") or [])
    preview: List[str] = []
    seen: set[str] = set()

    for item in card_items:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or item.get("normalized_title") or "").strip()
        if not title:
            continue

        normalized = _normalize_match_text(title)
        if normalized in seen:
            continue
        seen.add(normalized)
        preview.append(title)
        if len(preview) >= max(1, limit):
            break

    return preview


def _score_serialized_timeline_block(
    entry_data: dict,
    markdown_text: str,
    block: Dict[str, object],
    *,
    preferred_unit_slug: str = "",
    preferred_period: str = "",
) -> float:
    signals = _collect_entry_unit_signals(entry_data, markdown_text)
    score = 0.0

    block_unit_slug = str(block.get("unit_slug") or "").strip()
    if preferred_unit_slug:
        if block_unit_slug == preferred_unit_slug:
            score += 1.25
        elif block_unit_slug:
            score -= 0.35

    block_period = _timeline_block_display_period(block)
    if preferred_period:
        preferred_norm = _format_timeline_label_dates(preferred_period)
        if preferred_norm and block_period == preferred_norm:
            score += 0.85
        elif preferred_norm and _periods_overlap(preferred_norm, block_period):
            score += 0.45

    block_text_parts = [
        str(block.get("primary_topic_label") or ""),
        str(block.get("topic_text") or ""),
        " ".join(str(item) for item in (block.get("topics") or []) if str(item).strip()),
        " ".join(str(item) for item in (block.get("aliases") or []) if str(item).strip()),
    ]
    block_norm = _normalize_match_text(" ".join(part for part in block_text_parts if part))
    block_tokens = [tok for tok in block_norm.split() if len(tok) >= 4]

    score += _score_text_against_row(signals.get("title_text", ""), block_tokens, weight=1.25)
    score += _score_text_against_row(signals.get("tags_text", ""), block_tokens, weight=1.05)
    score += _score_text_against_row(signals.get("markdown_headings_text", ""), block_tokens, weight=0.95)
    score += _score_text_against_row(signals.get("markdown_lead_text", ""), block_tokens, weight=0.75)
    score += _score_text_against_row(signals.get("markdown_text", ""), block_tokens, weight=0.18)

    score += float(block.get("primary_topic_confidence", 0.0) or 0.0) * 0.25
    score += float(block.get("unit_confidence", 0.0) or 0.0) * 0.10
    return score


def _load_timeline_block_options(repo_dir: Optional[Path]) -> List[Tuple[str, str]]:
    if not repo_dir:
        return []
    timeline_path = repo_dir / "course" / ".timeline_index.json"
    if not timeline_path.exists():
        return []
    try:
        payload = json.loads(timeline_path.read_text(encoding="utf-8"))
    except Exception:
        return []

    options: List[Tuple[str, str]] = []
    seen = set()
    for block in list(payload.get("blocks") or []):
        block_id = str(block.get("id") or "").strip()
        period_label = str(block.get("period_label") or "").strip()
        if not block_id or not period_label or block_id in seen:
            continue
        topics = [str(item).strip() for item in list(block.get("topics") or []) if str(item).strip()]
        session_preview = _timeline_block_session_preview(block, limit=1)
        card_preview = _timeline_block_card_evidence_preview(block, limit=1)
        unit_slug = str(block.get("unit_slug") or "").strip()
        topic_preview = (
            ", ".join(topics[:2])
            or (session_preview[0] if session_preview else "")
            or (card_preview[0] if card_preview else "sem tópicos fortes")
        )
        suffix = f" | {unit_slug}" if unit_slug else ""
        label = f"{_timeline_block_display_period(block)} | {topic_preview}{suffix}"
        options.append((label, block_id))
        seen.add(block_id)
    return options


def _normalize_selected_manual_tags(selected_tags: List[str], catalog_tags: List[str]) -> List[str]:
    selected = {str(tag).strip() for tag in (selected_tags or []) if str(tag).strip()}
    ordered_catalog = [str(tag).strip() for tag in (catalog_tags or []) if str(tag).strip()]
    return [tag for tag in ordered_catalog if tag in selected]


def _format_backlog_tag_summary(
    manual_tags: List[str],
    auto_tags: List[str],
    legacy_tags: str = "",
) -> Dict[str, str]:
    manual_list = [str(tag).strip() for tag in (manual_tags or []) if str(tag).strip()]
    auto_list = [str(tag).strip() for tag in (auto_tags or []) if str(tag).strip()]
    legacy_list = [part.strip() for part in re.split(r"[;,]", legacy_tags or "") if part.strip()]
    effective_list: List[str] = []
    seen: set[str] = set()
    for tag in manual_list + auto_list + legacy_list:
        if tag not in seen:
            effective_list.append(tag)
            seen.add(tag)
    manual = ", ".join(manual_list) or "—"
    auto = ", ".join(auto_list) or "—"
    effective = ", ".join(effective_list) or "—"
    return {
        "manual": manual,
        "auto": auto,
        "effective": effective,
    }


class URLEntryDialog(tk.Toplevel):
    """Dialog specifically for entering a URL representing a web bibliography/document."""
    _is_github_repo = staticmethod(_is_github_repo)

    def __init__(self, parent, default_category: str = "references"):
        super().__init__(parent)
        self.title("🔗 Importar Link / Bibliografia")
        self.geometry("560x460")
        self.transient(parent)
        self.grab_set()
        self._p = apply_theme_to_toplevel(self, parent)

        self.result_entry: Optional[FileEntry] = None
        self.var_url = tk.StringVar()
        self.var_title = tk.StringVar()
        self.var_category = tk.StringVar(value=default_category)
        self.var_tags = tk.StringVar()
        self.var_notes = tk.StringVar()
        self.var_bundle = tk.BooleanVar(value=True)
        self.var_branch = tk.StringVar(value="main")

        self._build_ui()

    def _build_ui(self):
        form = ttk.Frame(self, padding=14)
        form.pack(fill="both", expand=True)

        r = 0
        ttk.Label(form, text="URL do material:").grid(row=r, column=0, sticky="w", pady=4)
        url_entry = ttk.Entry(form, textvariable=self.var_url, width=40)
        url_entry.grid(row=r, column=1, sticky="w", padx=8)
        url_entry.bind("<FocusOut>", self._on_url_focus_out)

        r += 1
        ttk.Label(form, text="Título:").grid(row=r, column=0, sticky="w", pady=4)
        self._title_entry = ttk.Entry(form, textvariable=self.var_title, width=40)
        self._title_entry.grid(row=r, column=1, sticky="w", padx=8)
        self._title_hint = ttk.Label(form, text="", style="Muted.TLabel")
        self._title_hint.grid(row=r+1, column=1, sticky="w", padx=8)

        r += 2
        # GitHub repo branch field (hidden by default)
        self._github_lbl = ttk.Label(form, text="Branch:")
        self._github_entry = ttk.Entry(form, textvariable=self.var_branch, width=20)
        self._github_hint = ttk.Label(form, text="(GitHub repo detectado)", style="Muted.TLabel")
        self._github_row = r
        # Don't grid yet — shown by _check_github

        r += 1
        ttk.Label(form, text="Categoria:").grid(row=r, column=0, sticky="w", pady=4)
        ttk.Combobox(form, textvariable=self.var_category, values=list(CATEGORY_LABELS.keys()), state="readonly", width=38).grid(row=r, column=1, sticky="w", padx=8)

        r += 1
        ttk.Label(form, text="Tags (vírgulas):").grid(row=r, column=0, sticky="w", pady=4)
        ttk.Entry(form, textvariable=self.var_tags, width=40).grid(row=r, column=1, sticky="w", padx=8)

        r += 1
        ttk.Label(form, text="Notas:").grid(row=r, column=0, sticky="w", pady=4)
        ttk.Entry(form, textvariable=self.var_notes, width=40).grid(row=r, column=1, sticky="w", padx=8)

        r += 1
        ttk.Checkbutton(form, text="Incluir no bundle base", variable=self.var_bundle).grid(row=r, column=0, columnspan=2, sticky="w", pady=8)

        btn_frame = ttk.Frame(self, padding=(14, 0, 14, 14))
        btn_frame.pack(fill="x")
        ttk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(side="right", padx=(6, 0))
        ttk.Button(btn_frame, text="Salvar Link", style="Accent.TButton", command=self._save).pack(side="right")

    def _check_github(self):
        """Show/hide GitHub branch field based on URL."""
        url = self.var_url.get().strip()
        if self._is_github_repo(url):
            self._github_lbl.grid(row=self._github_row, column=0, sticky="w", pady=4)
            self._github_entry.grid(row=self._github_row, column=1, sticky="w", padx=8)
            self._github_hint.grid(row=self._github_row, column=1, sticky="e", padx=8)
            if not self.var_category.get() or self.var_category.get() == "references":
                self.var_category.set("codigo-professor")
        else:
            self._github_lbl.grid_forget()
            self._github_entry.grid_forget()
            self._github_hint.grid_forget()
        
    def _on_url_focus_out(self, _event=None):
        """Auto-busca o título da página quando o campo URL perde o foco."""
        url = self.var_url.get().strip()
        self._check_github()
        if not url or self.var_title.get().strip():
            return  # Nada para buscar ou título já preenchido
        if not url.startswith(("http://", "https://")):
            return
        self._title_hint.config(text="Buscando título...")
        import threading
        def _fetch():
            title = fetch_url_title(url)
            self.after(0, lambda: self._apply_fetched_title(title))
        threading.Thread(target=_fetch, daemon=True).start()

    def _apply_fetched_title(self, title: str):
        self._title_hint.config(text="")
        if title and not self.var_title.get().strip():
            self.var_title.set(title)

    def _save(self):
        url = self.var_url.get().strip()
        title = self.var_title.get().strip()
        if not url:
            messagebox.showwarning(APP_NAME, "O URL é obrigatório.", parent=self)
            return
        if not title:
            title = url.split("://")[-1].split("/")[0] # fallback pro domínio

        is_gh = self._is_github_repo(url)
        file_type = "github-repo" if is_gh else "url"
        tags = self.var_branch.get().strip() if is_gh else self.var_tags.get().strip()

        self.result_entry = FileEntry(
            source_path=url,
            file_type=file_type,
            category=self.var_category.get(),
            title=title,
            tags=tags,
            notes=self.var_notes.get().strip(),
            include_in_bundle=self.var_bundle.get(),
            document_profile="auto",
            processing_mode="auto",
            preferred_backend="url_fetcher" if not is_gh else "auto",
        )
        self.destroy()


class StatusDialog(tk.Toplevel):
    """Janela de diagnóstico: mostra se todos os serviços estão configurados."""

    def __init__(self, parent, config_obj: "AppConfig", student_store, theme_mgr: "ThemeManager"):
        super().__init__(parent)
        self.title("📊 Status dos Serviços")
        self.resizable(False, False)
        self.grab_set()

        theme_name = config_obj.get("theme", "dark")
        p = theme_mgr.palette(theme_name)

        self.configure(bg=p["bg"])

        # importações locais para evitar ciclo
        import shutil
        from src.utils.helpers import (
            HAS_PYMUPDF, HAS_PYMUPDF4LLM, HAS_PDFPLUMBER,
            DOCLING_CLI, MARKER_CLI, TESSDATA_PATH,
        )

        outer = ttk.Frame(self, padding=20)
        outer.pack(fill="both", expand=True)

        def section(title: str) -> ttk.LabelFrame:
            f = ttk.LabelFrame(outer, text=f"  {title}", padding=(12, 8))
            f.pack(fill="x", pady=(0, 10))
            return f

        def row(frame, label: str, ok: bool, detail: str = ""):
            icon = "✅" if ok else "❌"
            color = p["accent"] if ok else "#f38ba8"
            r = ttk.Frame(frame)
            r.pack(fill="x", pady=2)
            tk.Label(r, text=icon, bg=p["bg"], font=("Segoe UI", 10)).pack(side="left")
            tk.Label(r, text=f"  {label}", bg=p["bg"], fg=p["fg"],
                     font=("Segoe UI", 10)).pack(side="left")
            if detail:
                tk.Label(r, text=f"  —  {detail}", bg=p["bg"], fg=p["muted"],
                         font=("Consolas", 9)).pack(side="left")

        def warn_row(frame, label: str, detail: str = ""):
            r = ttk.Frame(frame)
            r.pack(fill="x", pady=2)
            tk.Label(r, text="⚠️", bg=p["bg"], font=("Segoe UI", 10)).pack(side="left")
            tk.Label(r, text=f"  {label}", bg=p["bg"], fg="#f9e2af",
                     font=("Segoe UI", 10)).pack(side="left")
            if detail:
                tk.Label(r, text=f"  —  {detail}", bg=p["bg"], fg=p["muted"],
                         font=("Consolas", 9)).pack(side="left")

        def mask_key(key: str) -> str:
            if not key:
                return "(não definida)"
            if len(key) <= 8:
                return "***"
            return key[:4] + "..." + key[-4:]

        # ── Backends de Extração ─────────────────────────────────────────
        f_ext = section("Backends de Extração de PDF")
        row(f_ext, "PyMuPDF",      HAS_PYMUPDF,      "pymupdf" if HAS_PYMUPDF else "pip install pymupdf")
        row(f_ext, "PyMuPDF4LLM", HAS_PYMUPDF4LLM,  "pymupdf4llm" if HAS_PYMUPDF4LLM else "pip install pymupdf4llm")
        row(f_ext, "pdfplumber",   HAS_PDFPLUMBER,   "pdfplumber" if HAS_PDFPLUMBER else "pip install pdfplumber")
        row(f_ext, "Datalab API", has_datalab_api_key(), get_datalab_base_url() if has_datalab_api_key() else "defina DATALAB_API_KEY no .env")
        row(f_ext, "docling CLI",  bool(DOCLING_CLI), DOCLING_CLI or "não encontrado no PATH")
        row(f_ext, "docling Python", has_docling_python_api(), "API importável" if has_docling_python_api() else "pip install docling")
        row(f_ext, "marker CLI",   bool(MARKER_CLI),  MARKER_CLI  or "não encontrado no PATH")
        marker_torch_device = str(config_obj.get("marker_torch_device", "auto") or "auto").strip().lower() or "auto"
        marker_torch_effective = "mps" if (marker_torch_device == "auto" and sys.platform == "darwin") else ("cuda" if marker_torch_device == "auto" else marker_torch_device)
        row(
            f_ext,
            "TORCH_DEVICE do Marker",
            bool(MARKER_CLI),
            f"configurado={marker_torch_device} | efetivo={marker_torch_effective}",
        )

        # ── OCR / Tesseract ──────────────────────────────────────────────
        f_ocr = section("OCR (Tesseract)")
        tess_bin = shutil.which("tesseract")
        row(f_ocr, "Executável tesseract", bool(tess_bin), tess_bin or "não encontrado no PATH")
        row(f_ocr, "Dados de idioma (tessdata)", bool(TESSDATA_PATH),
            TESSDATA_PATH or "defina TESSDATA_PREFIX nas variáveis de ambiente")

        # ── Perfil do Aluno ──────────────────────────────────────────────
        f_stu = section("Perfil do Aluno")
        profile = student_store.profile
        has_name = bool(getattr(profile, "full_name", ""))
        has_pers = bool(getattr(profile, "personality", ""))
        row(f_stu, "Nome configurado",         has_name, getattr(profile, "full_name", "") or "não definido")
        row(f_stu, "Personalidade/preferências", has_pers,
            (getattr(profile, "personality", "")[:60] + "...") if has_pers else "não definida")

        # ── Ollama / Vision ───────────────────────────────────────────
        backend = config_obj.get("vision_backend", "ollama")
        f_vis = section(f"Vision — Descrição de Imagens ({backend})")
        row(f_vis, "Backend selecionado", True, backend)

        configured_model = config_obj.get("vision_model", "qwen3-vl:235b-cloud")
        ollama_url = config_obj.get("ollama_base_url", "http://localhost:11434")
        from src.builder.ollama_client import FALLBACK_MODEL, get_vision_setup_status
        vision_status = get_vision_setup_status(ollama_url, configured_model)
        available_models = vision_status["available_models"]
        model_found = bool(vision_status["model_found"])
        fallback_found = bool(vision_status["fallback_found"])

        row(f_vis, "Ollama rodando", bool(vision_status["ollama_running"]),
            ollama_url if vision_status["ollama_running"] else f"não acessível em {ollama_url}")

        row(f_vis, f"Modelo: {configured_model}", model_found,
            "disponível" if model_found else f"ollama pull {configured_model}")
        if configured_model.endswith("-cloud"):
            if vision_status["cloud_ready"]:
                row(f_vis, "Cloud pronto", True, "modelo cloud exato disponível")
            elif vision_status["local_family_ready"]:
                warn_row(
                    f_vis,
                    "Modo local detectado",
                    f"família {configured_model.split(':')[0]} disponível localmente; cloud exato não encontrado",
                )
            else:
                warn_row(
                    f_vis,
                    "Modelo cloud",
                    "requer ollama signin e uso pode ser limitado pelo plano",
                )

        row(f_vis, f"Fallback: {FALLBACK_MODEL}", fallback_found,
            "disponível" if fallback_found else f"ollama pull {FALLBACK_MODEL}")

        vision_keywords = ["qwen", "llava", "vl", "vision"]
        vision_models = [m for m in available_models
                         if any(kw in m.lower() for kw in vision_keywords)]
        if vision_models and not model_found:
            warn_row(f_vis, "Modelos Vision disponíveis",
                     ", ".join(vision_models[:5]))

        def validate_vision_setup():
            status = get_vision_setup_status(ollama_url, configured_model)
            checks = [
                ("Ollama acessível", bool(status["ollama_running"])),
                ("Modelo configurado disponível", bool(status["model_found"])),
                ("Fallback disponível", bool(status["fallback_found"])),
            ]
            if configured_model.endswith("-cloud"):
                checks.append(("Cloud pronto (signin + pull)", bool(status["cloud_ready"])))
                checks.append(("Família local disponível", bool(status["local_family_ready"])))

            lines = []
            for label, ok in checks:
                lines.append(f"{'OK' if ok else 'FALHA'} - {label}")

            if not status["ollama_running"]:
                lines.append("")
                lines.append(f"Ação sugerida: verificar {ollama_url} e iniciar 'ollama serve'.")
            elif configured_model.endswith("-cloud") and not status["cloud_ready"]:
                lines.append("")
                if status["local_family_ready"]:
                    lines.append("Operação possível em modo local com a mesma família de modelo.")
                    lines.append(f"Modelo local detectado: {FALLBACK_MODEL}")
                    lines.append("Para habilitar o cloud exato:")
                    lines.append("1. ollama signin")
                    lines.append(f"2. ollama pull {configured_model}")
                else:
                    lines.append("Ações sugeridas:")
                    lines.append("1. ollama signin")
                    lines.append(f"2. ollama pull {configured_model}")
            elif not status["model_found"]:
                lines.append("")
                lines.append(f"Ação sugerida: ollama pull {configured_model}")
            elif not status["fallback_found"]:
                lines.append("")
                lines.append(f"Ação sugerida: ollama pull {FALLBACK_MODEL}")

            messagebox.showinfo("Validação Vision", "\n".join(lines), parent=self)

        ttk.Button(f_vis, text="Validar Vision", command=validate_vision_setup).pack(anchor="w", pady=(8, 0))

        # ── Botão fechar ─────────────────────────────────────────────────
        ttk.Button(outer, text="Fechar", command=self.destroy).pack(pady=(4, 0))

        self.update_idletasks()
        self.geometry(f"{self.winfo_reqwidth() + 20}x{self.winfo_reqheight() + 10}")


