import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from typing import Optional, List, Tuple, Dict
import os
from pathlib import Path
from src.models.core import FileEntry, SubjectProfile, StudentProfile, SubjectStore, StudentStore
from src.utils.helpers import (
    CATEGORY_LABELS, DEFAULT_CATEGORIES, DEFAULT_OCR_LANGUAGE, PROCESSING_MODES,
    DOCUMENT_PROFILES, PREFERRED_BACKENDS, OCR_LANGS,
    slugify, parse_html_schedule, auto_detect_category, auto_detect_title,
    fetch_url_title, APP_NAME, HAS_PYMUPDF4LLM
)
from src.builder.engine import BackendSelector
from src.ui.theme import ThemeManager, AppConfig, THEMES

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

        # Try to get theme colours from the root
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
        self._var_profile = tk.StringVar(value=self.config.get("default_profile"))
        self._var_backend = tk.StringVar(value=self.config.get("default_backend"))

        fields = [
            ("Modo de processamento padrão", self._var_mode, PROCESSING_MODES),
            ("Idioma OCR padrão", self._var_ocr, OCR_LANGS),
            ("Perfil de documento padrão", self._var_profile, DOCUMENT_PROFILES),
            ("Backend preferido padrão", self._var_backend, PREFERRED_BACKENDS),
        ]
        for r, (label, var, vals) in enumerate(fields):
            ttk.Label(tab_proc, text=label).grid(row=r, column=0, sticky="w", pady=6, padx=(0, 16))
            ttk.Combobox(tab_proc, textvariable=var, values=vals, state="readonly",
                          width=22).grid(row=r, column=1, sticky="ew")
        tab_proc.columnconfigure(1, weight=1)

        # ── LLM AI tab ──────────────────────────────────────────────
        tab_ia = ttk.Frame(nb, padding=16)
        nb.add(tab_ia, text="  🤖  Inteligência Artificial  ")

        self._var_ai_provider = tk.StringVar(value=self.config.get("default_ai_provider", "openai"))
        self._var_openai_key = tk.StringVar(value=self.config.get("openai_api_key", ""))
        self._var_gemini_key = tk.StringVar(value=self.config.get("gemini_api_key", ""))

        ttk.Label(tab_ia, text="Provedor Padrão para Categorização", style="Accent.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
            
        ttk.Combobox(tab_ia, textvariable=self._var_ai_provider, values=["openai", "gemini"], 
                     state="readonly", width=15).grid(row=0, column=2, sticky="ew", pady=(0, 8))

        ttk.Label(tab_ia, text="OpenAI API Key (GPT-4o-mini)").grid(row=1, column=0, sticky="w", pady=6)
        ttk.Entry(tab_ia, textvariable=self._var_openai_key, show="*", width=35).grid(row=1, column=1, columnspan=2, sticky="ew", padx=(8,0))

        ttk.Label(tab_ia, text="Google Gemini API Key (1.5 Flash)").grid(row=2, column=0, sticky="w", pady=6)
        ttk.Entry(tab_ia, textvariable=self._var_gemini_key, show="*", width=35).grid(row=2, column=1, columnspan=2, sticky="ew", padx=(8,0))
        
        ttk.Label(tab_ia, text="A chave é salva localmente e só sai de sua máquina direto para o provedor oficial.",
                  foreground=p["muted"], font=("Segoe UI", 8)).grid(row=3, column=0, columnspan=3, sticky="w", pady=(12, 0))
                  
        tab_ia.columnconfigure(2, weight=1)


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
        self.config.set("default_ai_provider", self._var_ai_provider.get())
        self.config.set("openai_api_key", self._var_openai_key.get().strip())
        self.config.set("gemini_api_key", self._var_gemini_key.get().strip())
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
    ("Visão Geral", """O Academic Tutor Repo Builder converte PDFs e imagens acadêmicas em repositórios estruturados de conhecimento, prontos para uso com tutores no Claude Projects.

Fluxo recomendado:
  1. Gerencie suas matérias no botão "📚 Gerenciar".
  2. Selecione a matéria para auto-preencher os dados.
  3. Adicione PDFs e imagens (ou links).
  4. Configure cada arquivo (categoria, modo, perfil).
  5. Clique em "🚀 Criar repositório".
  6. Use o "🖌 Curator Studio" para revisar arquivos em manual-review/.
  7. Mova o conteúdo aprovado para a estrutura final do repositório.
"""),
    ("Dados da Disciplina", """NOME DA DISCIPLINA
  Nome completo como aparece no sistema acadêmico. Obrigatório.
  Exemplo: "Cálculo I", "Estruturas de Dados"

SLUG
  Identificador curto usado para nomear pastas e arquivos. Gerado automaticamente a partir do nome se vazio.
  Use letras minúsculas, números e hífens.
  Exemplo: "calculo-i", "estruturas-de-dados"

SEMESTRE
  Período letivo. Não há validação de formato; use o que fizer sentido.
  Exemplos: "2024/1", "2025-2", "1º sem 2025"

PROFESSOR
  Nome do professor principal da disciplina. Usado para contextualizar o tutor.

INSTITUIÇÃO
  Nome da instituição (padrão: PUCRS). Armazenado nos metadados.

PASTA DO REPOSITÓRIO
  Pasta onde o repositório será criado. Dentro dela, uma subpasta com o slug será gerada.
  Clicar em "Escolher pasta" abre o seletor de diretórios.
"""),
    ("Modos de Processamento", """Os modos controlam QUANTO processamento cada arquivo recebe.

auto
  Detecta automaticamente o tipo de documento e escolhe o melhor pipeline.
  Use quando não tiver certeza. É o padrão.

quick
  Só a camada base (pymupdf4llm ou pymupdf). Rápido e leve.
  Use para materiais simples: cronogramas, ementas, textos corridos.

high_fidelity
  Camada base + camada avançada (docling ou marker) quando disponível.
  Use para PDFs com fórmulas, tabelas complexas ou layout diferenciado.

manual_assisted
  Igual ao high_fidelity + geração de arquivo de revisão manual guiada.
  Use para provas, gabaritos, materiais críticos onde a precisão é essencial.
  Exige que você revise o conteúdo gerado antes de publicar.
"""),
    ("Perfis de Documento", """Os perfis descrevem o TIPO de conteúdo do documento e ajustam modo + backend automaticamente.

auto
  O sistema analisa o PDF (texto, imagens, tabelas, densidade) e decide.
  Recomendado por padrão.

general  (modo: auto | backend: pymupdf4llm)
  Documento de texto comum. Slides simples, ementas, cronogramas.
  Sem fórmulas — processamento rápido.

math_light  (modo: high_fidelity | backend: docling)
  Algumas fórmulas LaTeX ou notação matemática.
  Usa docling para melhor extração, sem enrich-formula.

math_heavy  (modo: high_fidelity | backend: docling + enrich-formula)
  Muitas fórmulas, LaTeX, teoremas, provas formais.
  Ativa docling com reconhecimento IA de fórmulas em imagens.

layout_heavy  (modo: high_fidelity | backend: docling)
  Layout complexo: múltiplas colunas, figuras, tabelas elaboradas.

scanned  (modo: auto | force_ocr)
  PDF gerado a partir de scanner ou foto, sem texto digital.
  Ativa OCR obrigatório.

exam_pdf  (modo: auto | backend: auto)
  Prova ou lista de exercícios. Combina necessidades de layout e fórmulas.
"""),
    ("Backends de Extração", """Os backends são os motores que extraem texto e conteúdo dos PDFs.

CAMADA BASE (rápida)
  pymupdf4llm — Markdown de alta qualidade para PDFs digitais. Recomendado.
  pymupdf    — Fallback bruto quando pymupdf4llm não está disponível.

CAMADA AVANÇADA (para documentos difíceis)
  docling    — OCR, fórmulas, tabelas e imagens referenciadas (CLI externo).
  marker     — Excelente para equações inline, tabelas e imagens (CLI externo).

BACKEND PREFERIDO
  Define qual backend usar por padrão para este arquivo, sobrepondo a seleção automática.
  Deixe "auto" para que o sistema escolha com base no perfil e modo.

  Se escolher docling ou marker como preferido, o sistema ainda executa a
  camada base (pymupdf4llm) como complemento.
"""),
    ("Opções por Arquivo", """TÍTULO
  Nome legível do documento. Usado nos metadados e no índice do repositório.

CATEGORIA
  Classifica o arquivo dentro da estrutura do repositório.
  course-material  → Slides, notas de aula, apostilas
  exams            → Provas anteriores em PDF
  exercise-lists   → Listas de exercícios
  rubrics          → Gabaritos e critérios de correção
  schedule         → Cronograma da disciplina
  references       → Livros, artigos, documentos de referência
  photos-of-exams  → Fotos de provas manuscritas
  answer-keys      → Gabaritos separados
  other            → Qualquer outro material

TAGS
  Palavras-chave separadas por vírgula para facilitar busca futura.
  Exemplo: "gabarito, integração, 2024-1"

NOTAS
  Observação livre sobre o arquivo. Não afeta o processamento.

PISTA DO PROFESSOR
  Registre padrões observados: tipo de cobrança, notação preferida, dificuldade recorrente.
  Exemplo: "cobra demonstração formal; mistura indução e recursão"

RELEVANTE PARA PROVA
  Marca o material como importante para preparação de provas. Afeta priorização no bundle.

INCLUIR NO BUNDLE INICIAL
  Se marcado, o arquivo entra no bundle.seed.json para alimentar o tutor Claude.

PRIORIDADE EM FÓRMULAS
  Força ativação do backend avançado mesmo em modo auto ou quick.
  Use quando o documento tem muitas equações críticas.
"""),
    ("Opções de PDF", """PRESERVAR IMAGENS NO MARKDOWN BASE
  Se marcado, o pymupdf4llm salva as imagens do PDF como arquivos externos
  referenciados no Markdown. Útil para manter figuras após a extração.

FORÇAR OCR
  Ignora o texto digital do PDF e passa tudo pelo OCR.
  Use para PDFs com texto não selecionável ou codificação incorreta.

EXPORTAR PREVIEWS DAS PÁGINAS
  Gera imagens PNG de cada página (resolução 1.5x) em staging/assets/page-previews/.
  Consome mais espaço mas facilita a revisão visual do conteúdo.

EXTRAIR IMAGENS DO PDF
  Extrai todas as imagens embutidas no PDF para staging/assets/images/.
  Requer PyMuPDF instalado.

EXTRAIR TABELAS
  Detecta e exporta tabelas como CSV e Markdown em staging/assets/tables/.
  Requer pdfplumber e/ou PyMuPDF instalados.

PAGE RANGE (Intervalo de páginas)
  Limita o processamento a páginas específicas.
  Formato: "1-5" (páginas 1 a 5), "1,3,7" (páginas 1, 3 e 7), "2, 5-8" (misto).
  Deixe em branco para processar todas as páginas.
  Tratamento: se o intervalo não contiver zero, é interpretado como base-1.

OCR LANGUAGE
  Idiomas para o mecanismo OCR. Separados por vírgula.
  por,eng → Português + Inglês (padrão recomendado)
  por     → Somente Português
  eng     → Somente Inglês
"""),
    ("Curator Studio", """O Curator Studio é o ambiente de revisão manual para garantir a integridade total da informação extraída.

COMO USAR
  1. Gere um repositório com arquivos no modo "manual_assisted".
  2. Abra o Curator Studio pelo botão "🖌" na barra de ferramentas.
  3. Selecione um arquivo da lista (pasta manual-review/).
  4. Compare o Markdown (à direita) com a imagem original (ao centro).
  5. Edite o texto para corrigir fórmulas, tabelas ou OCR.
  6. Salve as alterações (Ctrl+S).

IMPORTANTE
  Arquivos revisados aqui devem ser movidos manualmente para as pastas finais
  (content/, exams/, etc.) conforme sua organização.
"""),
    ("Gerenciador de Matérias", """Permite salvar perfis recorrentes para não precisar preencher tudo toda vez.

RECURSOS
  • Salva Professor, Instituição, Semestre e Horário.
  • Permite definir Modos e OCR padrão por matéria.
  • Define a pasta raiz do repositório para aquela disciplina.
  • IMPORTAR CRONOGRAMA: No formulário da matéria, você pode colar o HTML
    de uma tabela (ex: Moodle) para converter em Markdown automaticamente.

USO
  Selecione a matéria no menu suspenso (Combobox) na tela principal para aplicar.
"""),
    ("Handoff e Continuidade", """Garantindo a continuidade do trabalho em chats longos.

STUDENT_STATE.md (O Estado do Aluno)
  • Registra progresso, tópicos estudados e próximas metas.
  • Salvo em student/STUDENT_STATE.md no repositório.
  • QUANDO USAR: Ao final de cada sessão de estudo, peça ao Claude para
    sugerir uma atualização — então faça commit e push no GitHub.

HANDOFF (O Pacote de Transferência)
  • É um resumo rápido e situacional para transição entre chats.
  • QUANDO USAR: Quando o chat ficar muito grande/lento, peça ao Claude
    para gerar um "Handoff".
  • FLUXO:
    1. O Claude gera o Handoff (contexto, decisões, próximos passos).
    2. Você copia o Handoff + o STUDENT_STATE.md atualizado.
    3. Cola tudo em um NOVO chat do Projeto Claude.
    4. O Claude lê o estado e continua de onde parou, sem repetir trabalho.

ATUALIZAÇÃO INCREMENTAL
  Ao clicar em "🚀 Criar Repositório" com um repositório existente:
  • O sistema pergunta: "Adicionar novos arquivos ou recriar do zero?"
  • No modo incremental, apenas os NOVOS arquivos são processados.
  • O manifest.json é mesclado (não substituído).

BOTÃO "📂 Abrir Repo"
  Permite selecionar um repositório existente e carregar seus dados
  (nome da disciplina, professor, semestre, etc.) automaticamente no app.
"""),
    ("Atalhos e Dicas", """ATALHOS
  F1          → Abre esta janela de ajuda
  Double-click → Edita o item selecionado na tabela
  Delete      → Remove o item selecionado (via botão na toolbar)
  Ctrl+S      → Salva edição no Curator Studio

DICAS GERAIS
  • Duplique um item bem configurado para processar arquivos similares rapidamente.
  • O slug da disciplina define o nome da pasta raiz do repositório.
  • O arquivo manifest.json gerado contém o histórico completo de todas as decisões de pipeline.
  • Use o modo 'high_fidelity' para PDFs digitais com fórmulas.
  • Use 'scanned' para fotos de provas (ativa OCR avançado).


AMBIENTE DETECTADO
  Se PyMuPDF, PyMuPDF4LLM ou pdfplumber aparecem como False na barra inferior,
  instale-os com: pip install pymupdf pymupdf4llm pdfplumber
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
        self.parent = parent
        
        ttk.Label(self, text="Cole o elemento HTML interiro da tabela de cronograma (ex: Portal/Moodle):").pack(padx=10, pady=(10, 5), anchor="w")
        self.text = tk.Text(self, font=("Consolas", 10), wrap="word")
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
        self.geometry("780x560")
        self.transient(parent)
        self.grab_set()
        self._store = subject_store
        self._theme_mgr = theme_mgr
        self._current_name: Optional[str] = None
        self._build_ui()
        self._refresh_list()

    def _build_ui(self):
        pw = ttk.PanedWindow(self, orient="horizontal")
        pw.pack(fill="both", expand=True, padx=10, pady=10)

        # ── Left panel: subject list ─────────────────────────────────
        left = ttk.Frame(pw, width=220)
        pw.add(left, weight=0)

        ttk.Label(left, text="Matérias salvas", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 6))
        self._listbox = tk.Listbox(left, width=28, font=("Segoe UI", 10))
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
            ("repo_root", "Pasta do repositório", "Pasta base para criar repos"),
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

        self._syllabus_text = tk.Text(form, height=6, width=36, font=("Segoe UI", 9), wrap="word")
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

        self._teaching_plan_text = tk.Text(form, height=6, width=36, font=("Segoe UI", 9), wrap="word")
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
        self._build_ui()

    def _build_ui(self):
        p = self._store.profile
        frm = ttk.LabelFrame(self, text="  Seus dados", padding=14)
        frm.pack(fill="x", padx=14, pady=(14, 8))

        self._vars: Dict[str, tk.StringVar] = {}
        entries = [
            ("full_name", "Nome completo", "Seu nome completo, como aparece no sistema acadêmico."),
            ("nickname", "Como prefere ser chamado", "Nome/apelido que o tutor Claude deve usar ao se referir a você.\nEx: Humberto, Beto, Hu"),
        ]
        for i, (key, label, tip) in enumerate(entries):
            lbl = ttk.Label(frm, text=label)
            lbl.grid(row=i, column=0, sticky="w", pady=4)
            add_tooltip(lbl, tip)
            var = tk.StringVar(value=getattr(p, key, ""))
            self._vars[key] = var
            ttk.Entry(frm, textvariable=var, width=40).grid(row=i, column=1, sticky="ew", padx=(8, 0))
        frm.columnconfigure(1, weight=1)

        # Personality — multiline
        pers_frame = ttk.LabelFrame(self, text="  🧠  Personalidade do Tutor", padding=14)
        pers_frame.pack(fill="both", expand=True, padx=14, pady=(0, 8))

        hint = ttk.Label(pers_frame, text="Como o tutor Claude deve te ajudar? Descreva o estilo que funciona para você:",
                         style="Muted.TLabel")
        hint.pack(anchor="w", pady=(0, 6))
        add_tooltip(hint, "Este texto será exportado nos repositórios e define como o tutor Claude interage com você.\nDica: seja específico sobre estilo de explicação, nível de detalhe, e preferências.")

        self._personality_text = tk.Text(pers_frame, height=10, font=("Segoe UI", 10), wrap="word")
        self._personality_text.pack(fill="both", expand=True)
        self._text_normal_fg = self._personality_text.cget("fg")
        if p.personality:
            self._personality_text.insert("1.0", p.personality)
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
# GUI — Categorization Review Dialog
# ---------------------------------------------------------------------------

class CategorizationReviewDialog(tk.Toplevel):
    """Mostra os resultados da auto-categorização para revisão antes de aplicar."""

    def __init__(self, parent, results: list):
        """results: List of (FileEntry, category, unit, exam_ref) ou (FileEntry, category, unit)"""
        super().__init__(parent)
        self.title("🔮  Revisão — Auto-Categorização")
        self.geometry("920x460")
        self.minsize(700, 360)
        self.transient(parent)
        self.grab_set()
        self.resizable(True, True)

        # Normaliza para 4-tuplas
        self._results = [
            r if len(r) == 4 else (*r, "") for r in results
        ]
        self._selected = [True] * len(self._results)
        self.confirmed: list = []  # populated on OK

        self._build_ui()
        self.wait_window(self)

    def _build_ui(self):
        ttk.Label(self, text="Revise as classificações sugeridas pela IA. Desmarque o que não quiser aplicar.",
                  font=("Segoe UI", 10)).pack(padx=14, pady=(12, 6), anchor="w")

        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True, padx=14, pady=(0, 4))

        cols = ("apply", "file", "category", "unit", "exam_ref")
        self._tree = ttk.Treeview(frame, columns=cols, show="headings", height=12)
        self._tree.heading("apply",    text="Aplicar")
        self._tree.heading("file",     text="Arquivo")
        self._tree.heading("category", text="Categoria")
        self._tree.heading("unit",     text="Unidade")
        self._tree.heading("exam_ref", text="Referência (gabarito/lista)")
        self._tree.column("apply",    width=65,  anchor="center", stretch=False)
        self._tree.column("file",     width=220)
        self._tree.column("category", width=140, anchor="center")
        self._tree.column("unit",     width=110, anchor="center")
        self._tree.column("exam_ref", width=220)

        sb = ttk.Scrollbar(frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscroll=sb.set)
        self._tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        for i, (entry, category, unit, exam_ref) in enumerate(self._results):
            self._tree.insert("", "end", iid=str(i), values=(
                "✓",
                Path(entry.source_path).name,
                category or "—",
                unit or "—",
                exam_ref or "—",
            ))

        self._tree.bind("<ButtonRelease-1>", self._on_click)

        # Select / Deselect all
        sel_frame = ttk.Frame(self)
        sel_frame.pack(fill="x", padx=14, pady=(0, 4))
        ttk.Button(sel_frame, text="Selecionar todos",
                   command=lambda: self._toggle_all(True)).pack(side="left")
        ttk.Button(sel_frame, text="Desmarcar todos",
                   command=lambda: self._toggle_all(False)).pack(side="left", padx=(6, 0))
        ttk.Label(sel_frame, text=f"{len(self._results)} arquivo(s) classificado(s)",
                  style="Muted.TLabel").pack(side="right")

        # OK / Cancel
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=14, pady=(0, 12))
        ttk.Button(btn_frame, text="Cancelar",
                   command=self._cancel).pack(side="right")
        ttk.Button(btn_frame, text="✓ Aplicar selecionados", style="Accent.TButton",
                   command=self._ok).pack(side="right", padx=(0, 8))

    def _on_click(self, event):
        if self._tree.identify_region(event.x, event.y) != "cell":
            return
        if self._tree.identify_column(event.x) != "#1":
            return
        row_id = self._tree.identify_row(event.y)
        if not row_id:
            return
        idx = int(row_id)
        self._selected[idx] = not self._selected[idx]
        vals = list(self._tree.item(row_id, "values"))
        vals[0] = "✓" if self._selected[idx] else "✗"
        self._tree.item(row_id, values=vals)

    def _toggle_all(self, state: bool):
        for i in range(len(self._results)):
            self._selected[i] = state
            vals = list(self._tree.item(str(i), "values"))
            vals[0] = "✓" if state else "✗"
            self._tree.item(str(i), values=vals)

    def _ok(self):
        self.confirmed = [
            (entry, category, unit, exam_ref)
            for i, (entry, category, unit, exam_ref) in enumerate(self._results)
            if self._selected[i]
        ]
        self.destroy()

    def _cancel(self):
        self.confirmed = []
        self.destroy()


# ---------------------------------------------------------------------------
# GUI — Backlog Entry Edit Dialog
# ---------------------------------------------------------------------------

class BacklogEntryEditDialog(simpledialog.Dialog):
    """Edita metadados de uma entrada já processada no manifest.json."""

    def __init__(self, parent, entry_data: dict):
        self._data = dict(entry_data)
        self.result_data: Optional[dict] = None
        super().__init__(parent, title="✏  Editar entrada do Backlog")

    def body(self, master):
        master.columnconfigure(1, weight=1)

        fields = [
            ("Título",    "title",            False),
            ("Categoria", "category",          False),
            ("Tags",      "tags",              False),
            ("Camada",    "effective_profile", False),
        ]

        self._vars: Dict[str, tk.StringVar] = {}
        first_entry = None
        for row, (label, key, _) in enumerate(fields):
            ttk.Label(master, text=label).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=4)
            var = tk.StringVar(value=self._data.get(key, ""))
            self._vars[key] = var
            if key == "category":
                ttk.Combobox(master, textvariable=var, values=DEFAULT_CATEGORIES,
                             state="readonly", width=28).grid(row=row, column=1, sticky="ew", pady=4)
            elif key == "effective_profile":
                from src.utils.helpers import DOCUMENT_PROFILES
                ttk.Combobox(master, textvariable=var, values=DOCUMENT_PROFILES,
                             state="readonly", width=28).grid(row=row, column=1, sticky="ew", pady=4)
            else:
                widget = ttk.Entry(master, textvariable=var, width=38)
                widget.grid(row=row, column=1, sticky="ew", pady=4)
                if first_entry is None:
                    first_entry = widget

        # Notes — multiline
        row_notes = len(fields)
        ttk.Label(master, text="Notas").grid(row=row_notes, column=0, sticky="nw", padx=(0, 12), pady=4)
        self._notes_text = tk.Text(master, height=4, width=38, font=("Segoe UI", 9), wrap="word")
        self._notes_text.grid(row=row_notes, column=1, sticky="ew", pady=4)
        self._notes_text.insert("1.0", self._data.get("notes", ""))

        # Checkboxes
        row_cb = row_notes + 1
        self._var_bundle = tk.BooleanVar(value=bool(self._data.get("include_in_bundle", True)))
        self._var_exam   = tk.BooleanVar(value=bool(self._data.get("relevant_for_exam", True)))
        ttk.Checkbutton(master, text="Incluir no bundle",   variable=self._var_bundle).grid(
            row=row_cb, column=0, columnspan=2, sticky="w", pady=(6, 2))
        ttk.Checkbutton(master, text="Relevante para prova", variable=self._var_exam).grid(
            row=row_cb + 1, column=0, columnspan=2, sticky="w", pady=2)

        return first_entry  # widget que recebe o foco inicial

    def apply(self):
        self.result_data = {
            "title":            self._vars["title"].get().strip(),
            "category":         self._vars["category"].get().strip(),
            "tags":             self._vars["tags"].get().strip(),
            "effective_profile": self._vars["effective_profile"].get().strip(),
            "notes":            self._notes_text.get("1.0", "end-1c").strip(),
            "include_in_bundle": self._var_bundle.get(),
            "relevant_for_exam": self._var_exam.get(),
        }


# ---------------------------------------------------------------------------
# GUI — Markdown Preview Window
# ---------------------------------------------------------------------------

class MarkdownPreviewWindow(tk.Toplevel):
    """Visualizador de Markdown processado — mostra conteúdo e verifica LaTeX."""

    def __init__(self, parent, repo_dir: str, theme_mgr: ThemeManager):
        super().__init__(parent)
        self.title("📄  Visualizador de Markdown")
        self.geometry("900x650")
        self.transient(parent)
        self._repo_dir = Path(repo_dir)
        self._theme_mgr = theme_mgr
        self._build_ui()

    def _build_ui(self):
        pw = ttk.PanedWindow(self, orient="horizontal")
        pw.pack(fill="both", expand=True, padx=8, pady=8)

        # ── Left: file tree ──────────────────────────────────────────
        left = ttk.Frame(pw, width=250)
        pw.add(left, weight=0)
        ttk.Label(left, text="Arquivos Markdown", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 6))

        self._file_list = tk.Listbox(left, width=35, font=("Consolas", 9))
        self._file_list.pack(fill="both", expand=True)
        self._file_list.bind("<<ListboxSelect>>", self._load_file)

        # Populate
        self._md_files: List[Path] = []
        pdf_md_paths = set()
        
        manifest_path = self._repo_dir / "manifest.json"
        if manifest_path.exists():
            try:
                import json
                with open(manifest_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for entry in data.get("entries", []):
                    if entry.get("file_type") == "pdf":
                        for key in ["base_markdown", "advanced_markdown", "manual_review"]:
                            if val := entry.get(key):
                                pdf_md_paths.add(str(Path(val)))
            except Exception as e:
                print(f"Erro ao filtrar PDFs no preview: {e}")

        if self._repo_dir.exists():
            all_mds = sorted(self._repo_dir.rglob("*.md"))
            if pdf_md_paths:
                # Filter to only show those listed in manifest as PDF outputs
                self._md_files = [f for f in all_mds if str(f.relative_to(self._repo_dir)) in pdf_md_paths]
            else:
                # Fallback: if no manifest or no pdf entries, show all (original behavior)
                self._md_files = all_mds

        for f in self._md_files:
            rel = f.relative_to(self._repo_dir)
            self._file_list.insert("end", str(rel))

        if not self._md_files:
            self._file_list.insert("end", "(nenhum .md encontrado)")

        # ── Right: content viewer ────────────────────────────────────
        right = ttk.Frame(pw)
        pw.add(right, weight=1)

        # Stats bar
        self._stats_var = tk.StringVar(value="Selecione um arquivo à esquerda.")
        ttk.Label(right, textvariable=self._stats_var, style="Muted.TLabel").pack(anchor="w", pady=(0, 6))

        self._text = tk.Text(right, wrap="word", font=("Consolas", 10), state="disabled")
        scroll = ttk.Scrollbar(right, orient="vertical", command=self._text.yview)
        self._text.configure(yscrollcommand=scroll.set)
        self._text.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # Tag configs for syntax
        self._text.tag_configure("heading", font=("Segoe UI", 12, "bold"), foreground="#89b4fa")
        self._text.tag_configure("latex", foreground="#f9e2af", font=("Consolas", 10, "italic"))
        self._text.tag_configure("code", background="#313244", font=("Consolas", 10))
        self._text.tag_configure("table_row", foreground="#a6e3a1")

    def _load_file(self, _event=None):
        sel = self._file_list.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx >= len(self._md_files):
            return
        fpath = self._md_files[idx]
        try:
            content = fpath.read_text("utf-8", errors="replace")
        except Exception as e:
            content = f"Erro ao ler arquivo: {e}"

        # Stats
        lines = content.split("\n")
        latex_count = content.count("$")
        latex_blocks = content.count("$$")
        img_refs = content.count("![")
        self._stats_var.set(
            f"📊  {len(lines)} linhas  |  "
            f"LaTeX inline: ~{latex_count - latex_blocks*2}  |  "
            f"LaTeX blocos: {latex_blocks}  |  "
            f"Imagens: {img_refs}"
        )

        # Display
        self._text.configure(state="normal")
        self._text.delete("1.0", "end")
        self._text.insert("1.0", content)

        # Highlight
        for i, line in enumerate(lines, 1):
            tag = f"{i}.0"
            tag_end = f"{i}.end"
            if line.startswith("#"):
                self._text.tag_add("heading", tag, tag_end)
            elif "$$" in line or line.strip().startswith("\\"):
                self._text.tag_add("latex", tag, tag_end)
            elif "$" in line:
                # Inline LaTeX — highlight dollar regions
                self._text.tag_add("latex", tag, tag_end)
            elif line.startswith("|") and "|" in line[1:]:
                self._text.tag_add("table_row", tag, tag_end)
            elif line.startswith("```"):
                self._text.tag_add("code", tag, tag_end)

        self._text.configure(state="disabled")


# ---------------------------------------------------------------------------
# GUI — FileEntryDialog & App
# ---------------------------------------------------------------------------

class FileEntryDialog(simpledialog.Dialog):
    def __init__(self, parent, path: str, initial: Optional[FileEntry] = None, default_mode: str = "auto", default_ocr_language: str = DEFAULT_OCR_LANGUAGE):
        self.path = path
        self.initial = initial
        self.default_mode = default_mode
        self.default_ocr_language = default_ocr_language
        self.result_entry: Optional[FileEntry] = None
        super().__init__(parent, title="Editar item")

    _FILE_TYPES = ["pdf", "image", "url"]

    def body(self, master):
        src = Path(self.path)
        if self.initial:
            self.file_type = self.initial.file_type
        else:
            self.file_type = "pdf" if src.suffix.lower() == ".pdf" else "image"

        ttk.Label(master, text=f"Arquivo: {src.name}", style="Accent.TLabel").grid(
            row=0, column=0, columnspan=4, sticky="w", pady=(0, 10))

        self.var_title = tk.StringVar(value=self.initial.title if self.initial else auto_detect_title(self.path))
        self.var_category = tk.StringVar(value=self.initial.category if self.initial else auto_detect_category(src.name, self.file_type == "image"))
        self.var_tags = tk.StringVar(value=self.initial.tags if self.initial else "")
        self.var_notes = tk.StringVar(value=self.initial.notes if self.initial else "")
        self.var_prof = tk.StringVar(value=self.initial.professor_signal if self.initial else "")
        self.var_bundle = tk.BooleanVar(value=self.initial.include_in_bundle if self.initial else True)
        self.var_exam = tk.BooleanVar(value=self.initial.relevant_for_exam if self.initial else True)

        self.var_mode = tk.StringVar(value=self.initial.processing_mode if self.initial else self.default_mode)
        self.var_profile = tk.StringVar(value=self.initial.document_profile if self.initial else "auto")
        self.var_backend = tk.StringVar(value=self.initial.preferred_backend if self.initial else "auto")
        self.var_formula = tk.BooleanVar(value=self.initial.formula_priority if self.initial else False)
        self.var_keep_images = tk.BooleanVar(value=self.initial.preserve_pdf_images_in_markdown if self.initial else True)
        self.var_force_ocr = tk.BooleanVar(value=self.initial.force_ocr if self.initial else False)
        self.var_previews = tk.BooleanVar(value=self.initial.export_page_previews if self.initial else True)
        self.var_imgs = tk.BooleanVar(value=self.initial.extract_images if self.initial else True)
        self.var_tables = tk.BooleanVar(value=self.initial.extract_tables if self.initial else True)
        self.var_page_range = tk.StringVar(value=self.initial.page_range if self.initial else "")
        self.var_ocr_lang = tk.StringVar(value=self.initial.ocr_language if self.initial else self.default_ocr_language)

        self.var_file_type = tk.StringVar(value=self.file_type)

        row = 1

        lbl_title = ttk.Label(master, text="Título")
        lbl_title.grid(row=row, column=0, sticky="w", pady=4)
        add_tooltip(lbl_title, "Nome legível do documento. Aparece nos metadados e no índice do repositório.")
        ttk.Entry(master, textvariable=self.var_title, width=54).grid(row=row, column=1, columnspan=3, sticky="ew")
        row += 1

        lbl_type = ttk.Label(master, text="Tipo")
        lbl_type.grid(row=row, column=0, sticky="w", pady=4)
        add_tooltip(lbl_type, "Tipo do item.\npdf → documento PDF\nimage → imagem (foto de prova, slide, etc.)\nurl → link web (YouTube, artigo, etc.)")
        cb_type = ttk.Combobox(master, textvariable=self.var_file_type, values=self._FILE_TYPES, state="readonly", width=22)
        cb_type.grid(row=row, column=1, sticky="ew")
        cb_type.bind("<<ComboboxSelected>>", self._on_type_changed)
        row += 1

        lbl_cat = ttk.Label(master, text="Categoria")
        lbl_cat.grid(row=row, column=0, sticky="w", pady=4)
        add_tooltip(lbl_cat, "Classifica o arquivo na estrutura do repositório.\nexams → provas | course-material → slides/notas | exercise-lists → listas | references → livros/artigos | photos-of-exams → fotos manuscritas")
        ttk.Combobox(master, textvariable=self.var_category, values=DEFAULT_CATEGORIES, state="readonly", width=22).grid(row=row, column=1, sticky="ew")

        lbl_mode = ttk.Label(master, text="Modo")
        lbl_mode.grid(row=row, column=2, sticky="w", padx=(12, 0))
        add_tooltip(lbl_mode, "Controla o pipeline de processamento.\nauto → decide pelo perfil do documento\nquick → só backend base (rápido)\nhigh_fidelity → base + avançado\nmanual_assisted → base + avançado + revisão humana guiada")
        ttk.Combobox(master, textvariable=self.var_mode, values=PROCESSING_MODES, state="readonly", width=20).grid(row=row, column=3, sticky="ew")
        row += 1

        lbl_profile = ttk.Label(master, text="Perfil")
        lbl_profile.grid(row=row, column=0, sticky="w", pady=4)
        add_tooltip(lbl_profile, "Descreve o tipo de conteúdo do PDF. Cada perfil ajusta modo e backend automaticamente.\n\nauto → detecta automaticamente\ngeneral → texto simples, sem fórmulas (pymupdf4llm, rápido)\nmath_light → algumas fórmulas (docling, high_fidelity)\nmath_heavy → muitas fórmulas/LaTeX (docling + enrich-formula)\nlayout_heavy → colunas, figuras, tabelas complexas (docling)\nscanned → PDF de scan/foto (ativa OCR)\nexam_pdf → prova/lista de exercícios")
        combo_profile = ttk.Combobox(master, textvariable=self.var_profile, values=DOCUMENT_PROFILES, state="readonly", width=22)
        combo_profile.grid(row=row, column=1, sticky="ew")
        combo_profile.bind("<<ComboboxSelected>>", self._on_profile_changed)

        lbl_backend = ttk.Label(master, text="Backend preferido")
        lbl_backend.grid(row=row, column=2, sticky="w", padx=(12, 0))
        add_tooltip(lbl_backend, "Backend de extração preferido.\nauto → seleção automática\npymupdf4llm → rápido e bom para PDFs digitais\npymupdf → fallback básico\ndocling → avançado: OCR, fórmulas, tabelas (CLI externo)\nmarker → avançado: equações e imagens (CLI externo)")
        ttk.Combobox(master, textvariable=self.var_backend, values=PREFERRED_BACKENDS, state="readonly", width=20).grid(row=row, column=3, sticky="ew")
        row += 1

        lbl_tags = ttk.Label(master, text="Tags")
        lbl_tags.grid(row=row, column=0, sticky="w", pady=4)
        add_tooltip(lbl_tags, "Palavras-chave separadas por vírgula para facilitar busca futura.\nExemplo: gabarito, integração, 2024-1")
        ttk.Entry(master, textvariable=self.var_tags, width=26).grid(row=row, column=1, sticky="ew")

        lbl_ocr = ttk.Label(master, text="OCR lang")
        lbl_ocr.grid(row=row, column=2, sticky="w", padx=(12, 0))
        add_tooltip(lbl_ocr, "Idioma(s) para o OCR.\npor,eng → Português + Inglês (padrão recomendado)\npor → só Português | eng → só Inglês")
        ttk.Combobox(master, textvariable=self.var_ocr_lang, values=OCR_LANGS, width=20).grid(row=row, column=3, sticky="ew")
        row += 1

        lbl_notes = ttk.Label(master, text="Notas")
        lbl_notes.grid(row=row, column=0, sticky="w", pady=4)
        add_tooltip(lbl_notes, "Observação livre sobre o arquivo. Não afeta o processamento, apenas fica registrado nos metadados.")
        ttk.Entry(master, textvariable=self.var_notes, width=54).grid(row=row, column=1, columnspan=3, sticky="ew")
        row += 1

        lbl_prof = ttk.Label(master, text="Pista do professor")
        lbl_prof.grid(row=row, column=0, sticky="w", pady=4)
        add_tooltip(lbl_prof, "Padrões observados no estilo do professor: tipo de cobrança, notação preferida, nível de detalhe.\nExemplo: cobra demonstração formal; mistura indução e recursão")
        ttk.Entry(master, textvariable=self.var_prof, width=54).grid(row=row, column=1, columnspan=3, sticky="ew")
        row += 1

        cb_exam = ttk.Checkbutton(master, text="Relevante para prova", variable=self.var_exam)
        cb_exam.grid(row=row, column=0, sticky="w", pady=4)
        add_tooltip(cb_exam, "Marca este material como importante para preparação de provas. Afeta priorização no bundle do tutor Claude.")

        cb_bundle = ttk.Checkbutton(master, text="Incluir no bundle inicial", variable=self.var_bundle)
        cb_bundle.grid(row=row, column=1, sticky="w")
        add_tooltip(cb_bundle, "Se marcado, o arquivo entra no bundle.seed.json para alimentar o tutor Claude como conhecimento base.")

        cb_formula = ttk.Checkbutton(master, text="Prioridade em fórmulas", variable=self.var_formula)
        cb_formula.grid(row=row, column=2, sticky="w")
        add_tooltip(cb_formula, "Força ativação do backend avançado (docling/marker) mesmo em modo auto ou quick.\nUse quando o documento tem muitas equações matemáticas críticas.")
        row += 1

        # --- PDF-only options frame ---
        self._pdf_frame = ttk.LabelFrame(master, text="Opções de PDF", padding=4)
        self._pdf_row = row  # remember grid row for show/hide

        pr = 0
        cb_keep = ttk.Checkbutton(self._pdf_frame, text="Preservar imagens do PDF no Markdown base", variable=self.var_keep_images)
        cb_keep.grid(row=pr, column=0, columnspan=2, sticky="w", pady=4)
        add_tooltip(cb_keep, "Se marcado, o pymupdf4llm extrai as imagens embutidas no PDF e as referencia no Markdown. Útil para manter figuras após a extração.")

        cb_ocr = ttk.Checkbutton(self._pdf_frame, text="Forçar OCR", variable=self.var_force_ocr)
        cb_ocr.grid(row=pr, column=2, sticky="w")
        add_tooltip(cb_ocr, "Ignora o texto digital do PDF e passa tudo pelo OCR.\nUse para PDFs com texto não selecionável, imagens de texto, ou codificação incorreta.")
        pr += 1

        cb_prev = ttk.Checkbutton(self._pdf_frame, text="Exportar previews das páginas", variable=self.var_previews)
        cb_prev.grid(row=pr, column=0, sticky="w")
        add_tooltip(cb_prev, "Gera imagens PNG de cada página (resolução 1.5x) em staging/assets/page-previews/.\nConsome mais espaço, mas facilita a revisão visual do conteúdo extraído.")

        cb_imgs = ttk.Checkbutton(self._pdf_frame, text="Extrair imagens do PDF", variable=self.var_imgs)
        cb_imgs.grid(row=pr, column=1, sticky="w")
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

        master.columnconfigure(1, weight=1)
        master.columnconfigure(3, weight=1)
        return master

    def _on_type_changed(self, _event=None):
        self.file_type = self.var_file_type.get()
        self._update_pdf_frame_visibility()

    def _on_profile_changed(self, _event=None):
        """Quando o perfil muda, ajusta backend e modo automaticamente.
        Presets baseados no nível de complexidade do documento."""
        profile = self.var_profile.get()
        # Reset para defaults antes de aplicar preset
        self.var_formula.set(False)
        self.var_force_ocr.set(False)

        if profile == "general":
            # Texto simples, sem fórmulas → rápido
            self.var_mode.set("auto")
            self.var_backend.set("auto")
        elif profile == "math_light":
            # Algumas fórmulas → docling sem enrich-formula
            self.var_mode.set("high_fidelity")
            self.var_backend.set("docling")
        elif profile == "math_heavy":
            # Muitas fórmulas → docling com enrich-formula
            self.var_mode.set("high_fidelity")
            self.var_backend.set("docling")
            self.var_formula.set(True)
        elif profile == "layout_heavy":
            # Layout complexo (colunas, muitas figuras/tabelas)
            self.var_mode.set("high_fidelity")
            self.var_backend.set("docling")
        elif profile == "scanned":
            # PDF digitalizado/foto → força OCR
            self.var_mode.set("auto")
            self.var_backend.set("auto")
            self.var_force_ocr.set(True)
        elif profile == "exam_pdf":
            # Prova/lista → auto com docling se disponível
            self.var_mode.set("auto")
            self.var_backend.set("auto")

    def _update_pdf_frame_visibility(self):
        if self.file_type == "pdf":
            self._pdf_frame.grid(row=self._pdf_row, column=0, columnspan=4, sticky="ew", pady=(4, 0))
        else:
            self._pdf_frame.grid_remove()


    def apply(self):
        self.result_entry = FileEntry(
            source_path=self.path,
            file_type=self.file_type,
            category=self.var_category.get(),
            title=self.var_title.get().strip() or Path(self.path).stem,
            tags=self.var_tags.get().strip(),
            notes=self.var_notes.get().strip(),
            professor_signal=self.var_prof.get().strip(),
            relevant_for_exam=self.var_exam.get(),
            include_in_bundle=self.var_bundle.get(),
            processing_mode=self.var_mode.get(),
            document_profile=self.var_profile.get(),
            preferred_backend=self.var_backend.get(),
            formula_priority=self.var_formula.get() if self.file_type == "pdf" else False,
            preserve_pdf_images_in_markdown=self.var_keep_images.get() if self.file_type == "pdf" else False,
            force_ocr=self.var_force_ocr.get() if self.file_type == "pdf" else False,
            export_page_previews=self.var_previews.get() if self.file_type == "pdf" else False,
            extract_images=self.var_imgs.get() if self.file_type == "pdf" else False,
            extract_tables=self.var_tables.get() if self.file_type == "pdf" else False,
            page_range=self.var_page_range.get().strip() if self.file_type == "pdf" else "",
            ocr_language=self.var_ocr_lang.get().strip() or self.default_ocr_language,
        )


class URLEntryDialog(tk.Toplevel):
    """Dialog specifically for entering a URL representing a web bibliography/document."""
    def __init__(self, parent, default_category: str = "references"):
        super().__init__(parent)
        self.title("🔗 Importar Link / Bibliografia")
        self.geometry("560x420")
        self.transient(parent)
        self.grab_set()
        
        self.result_entry: Optional[FileEntry] = None
        self.var_url = tk.StringVar()
        self.var_title = tk.StringVar()
        self.var_category = tk.StringVar(value=default_category)
        self.var_tags = tk.StringVar()
        self.var_notes = tk.StringVar()
        self.var_bundle = tk.BooleanVar(value=True)
        
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
        
    def _on_url_focus_out(self, _event=None):
        """Auto-busca o título da página quando o campo URL perde o foco."""
        url = self.var_url.get().strip()
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
            
        self.result_entry = FileEntry(
            source_path=url,
            file_type="url",
            category=self.var_category.get(),
            title=title,
            tags=self.var_tags.get().strip(),
            notes=self.var_notes.get().strip(),
            include_in_bundle=self.var_bundle.get(),
            document_profile="general",
            processing_mode="auto",
            preferred_backend="url_fetcher"
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
        row(f_ext, "docling CLI",  bool(DOCLING_CLI), DOCLING_CLI or "não encontrado no PATH")
        row(f_ext, "marker CLI",   bool(MARKER_CLI),  MARKER_CLI  or "não encontrado no PATH")

        # ── OCR / Tesseract ──────────────────────────────────────────────
        f_ocr = section("OCR (Tesseract)")
        tess_bin = shutil.which("tesseract")
        row(f_ocr, "Executável tesseract", bool(tess_bin), tess_bin or "não encontrado no PATH")
        row(f_ocr, "Dados de idioma (tessdata)", bool(TESSDATA_PATH),
            TESSDATA_PATH or "defina TESSDATA_PREFIX nas variáveis de ambiente")

        # ── IA / Auto-categorização ──────────────────────────────────────
        f_ai = section("IA / Auto-categorização")
        provider = config_obj.get("default_ai_provider", "gemini")
        openai_key = config_obj.get("openai_api_key", "")
        gemini_key = config_obj.get("gemini_api_key", "")

        tk.Label(f_ai, text=f"  Provider ativo: {provider}", bg=p["bg"], fg=p["accent"],
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 4))

        has_openai = bool(openai_key)
        has_gemini = bool(gemini_key)
        row(f_ai, "OpenAI API Key",
            has_openai, mask_key(openai_key) if has_openai else "não definida (OPENAI_API_KEY)")
        row(f_ai, "Gemini API Key",
            has_gemini, mask_key(gemini_key) if has_gemini else "não definida (GEMINI_API_KEY)")

        active_key_ok = (provider == "openai" and has_openai) or (provider == "gemini" and has_gemini)
        if not active_key_ok:
            warn_row(f_ai, f"Provider '{provider}' ativo mas sem chave configurada",
                     "configure em ⚙ Configurações > aba IA")

        # ── Perfil do Aluno ──────────────────────────────────────────────
        f_stu = section("Perfil do Aluno")
        profile = student_store.profile
        has_name = bool(getattr(profile, "full_name", ""))
        has_pers = bool(getattr(profile, "personality", ""))
        row(f_stu, "Nome configurado",         has_name, getattr(profile, "full_name", "") or "não definido")
        row(f_stu, "Personalidade/preferências", has_pers,
            (getattr(profile, "personality", "")[:60] + "...") if has_pers else "não definida")

        # ── Botão fechar ─────────────────────────────────────────────────
        ttk.Button(outer, text="Fechar", command=self.destroy).pack(pady=(4, 0))

        self.update_idletasks()
        self.geometry(f"{self.winfo_reqwidth() + 20}x{self.winfo_reqheight() + 10}")

