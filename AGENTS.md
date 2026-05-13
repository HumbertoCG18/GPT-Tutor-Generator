# GPT-Tutor-Generator

Read `.mex/AGENTS.md` for project identity, non-negotiables, and commands.
Read `.mex/ROUTER.md` before starting any task.

<claude-mem-context>
# Memory Context

# [GPT-Tutor-Generator] recent context, 2026-05-11 10:16pm GMT-3

Legend: 🎯session 🔴bugfix 🟣feature 🔄refactor ✅change 🔵discovery ⚖️decision 🚨security_alert 🔐security_note
Format: ID TIME TYPE TITLE
Fetch details: get_observations([IDs]) | Search: mem-search skill

Stats: 50 obs (19.160t read) | 320.825t work | 94% savings

### May 4, 2026
S28 Verificação se correções de agrupamento de cronograma foram aplicadas a todos os repositórios atuais e futuros (May 4, 10:13 AM)
S29 Investigate timeline block system and fix administrative block filtering (May 4, 10:17 AM)
73 10:24a 🔵 Timeline Block Manual Override System Architecture
74 10:26a 🔵 Timeline Block Automatic Matching Algorithm
75 " 🔵 Timeline Block Construction and Topic/Unit Assignment
76 10:27a 🟣 Timeline Administrative Block Filtering During Persistence
S30 Update MEX scaffold documentation files to fix outdated references and reflect current project state (May 4, 10:28 AM)
77 10:57a 🔵 setup.md contains duplicate of decisions.md content
78 10:58a 🔵 Repository missing standard Python setup files
79 10:59a 🔵 Project uses custom .env loader without .env.example template
80 11:05a ✅ MEX Scaffold Setup Documentation Created
81 " ✅ Pattern Index Updated with Build Artifact Pattern
S31 Fix documentation validation error for Ollama endpoint URL in stack.md (May 4, 11:06 AM)
82 11:34a 🔵 Documentation validation flagged URL as missing path in stack.md
S32 Complete tag scoring redesign implementation after partial manual integration (May 4, 11:34 AM)
### May 7, 2026
83 12:47a 🔵 Tag Scoring and Timeline Block Architecture State Retrieved from Memory
84 " 🔵 Tag Catalog and Scoring System Already Implemented in Codebase
85 12:48a 🔵 FileEntry Model Already Contains Manual and Auto Tags Fields
86 12:49a 🔵 Subunit Assignment Already Implemented as Topic-Based Hierarchical Scoring
87 12:50a 🔵 Content Taxonomy Already Implements Subtopic Hierarchy with Topic Kind Field
88 12:51a 🔵 Hierarchical Topic-Then-Unit Assignment Flow Already Implemented in Navigation
89 12:52a 🟣 Added Tag-to-Unit Index Builder for Topic-Based Unit Assignment Boost
90 2:01a 🔵 Test failure reveals function signature mismatch in navigation.py
91 2:02a 🔵 Parameter naming inconsistency found across navigation layers
92 " 🔴 Fixed parameter name mismatch in navigation template builder
93 2:03a 🔵 Second signature mismatch revealed after first fix
94 " 🔴 Fixed second parameter mismatch in auto_map_entry_subtopic call
95 " 🟣 Tag scoring redesign implementation completed - all tests passing
S33 Confirmed whether tag system generates tags automatically during repository reprocessing (May 7, 2:04 AM)
96 2:05a 🔵 Tag generation integrated into repository processing flow
S34 Diagnose why unit and sub-unit assignment failing for Sistemas Operacionais course entries (May 7, 2:05 AM)
97 2:12a 🔵 Unit and sub-unit assignment logic traced in file map generation
98 2:13a 🔵 Sistemas Operacionais manifest shows empty unit assignments across all entries
99 2:15a 🔵 Sistemas Operacionais SYLLABUS.md lacks unit definitions section
100 2:18a 🔵 Tag catalog contains hierarchical topic tags with unit numbering structure
101 2:20a 🔵 Content taxonomy exists but has course slug mismatch with tag catalog
102 " 🔵 Complete 7-unit taxonomy structure confirmed with topic-to-unit mappings
103 2:21a 🔵 Unit tag index mechanism maps topico tags to unit slugs with weighted scoring
104 2:22a 🔵 Unit tag index successfully generates 55 mappings but includes noise topics and misassignments
105 2:23a 🔵 Tag-based unit boosting fails for 13 of 16 entries due to missing topico tags
106 " 🔵 Unit assignments ARE generated in FILE_MAP but not persisted to manifest.json
107 2:24a 🔵 refresh_manifest_auto_tags generates auto_tags via infer_entry_auto_tags without topic classification
108 " 🔵 infer_entry_auto_tags uses strict token matching requiring exact or near-exact slug presence in content
109 2:25a 🔵 Semantic profile file missing from Sistemas Operacionais course directory
110 " 🔵 Inferred semantic profile identifies administrative markers as tools instead of OS concepts
111 " 🔵 Base semantic profile defaults are formal verification tools, not OS-specific vocabulary
112 2:26a 🔵 Regenerated tag catalog produces 29 clean topico tags but zero ferramenta tags
113 " 🔵 Unit index builder uses hardcoded formal methods vocabulary in UNIT_GENERIC_TOKENS
114 " 🔵 Content taxonomy infers course_slug from first unit title causing mismatch
115 2:27a 🔵 COURSE_MAP includes pedagogical metadata as topic checkboxes causing taxonomy noise
116 2:28a 🔵 Noise topic in Unit 1 captured "Programação Concorrente" aliases causing unit misassignment
S35 Cross-repository analysis to determine if SO unit assignment issues are systemic or course-specific (May 7, 2:28 AM)
117 2:29a 🔵 Noise topic pollution is systemic across all tutor repositories with SO worst affected
S36 Diagnose and fix unit/sub-unit assignment failures in Sistemas Operacionais with platform-wide improvements (May 7, 2:30 AM)
118 2:32a 🔵 Existing topic extraction already filters noise; pollution comes from strong_headings enrichment phase
119 2:33a 🔵 Topic 4.2 "Comunicação e sincronização" rejected by 6-word threshold in _looks_like_weak_heading_candidate
120 2:35a 🔵 Topic 4.2 rejected as tool candidate due to garbage known_tools containing common Portuguese words
121 " 🔵 Semantic profile tool extraction uses pattern matching and context cues without preposition filtering
122 2:36a 🔵 Tool extraction accepts 2-character tokens allowing prepositions if they have special shape or high frequency
S37 Deep diagnostic of SO unit assignment failures revealing 5 interconnected root causes requiring 4 code fixes plus artifact rebuild (May 7, 2:36 AM)
**Investigated**: Complete trace from initial "units not assigning" complaint through unit assignment pipeline, content_taxonomy generation, semantic profile inference, tool detection heuristics, and cross-repository comparison. Performed detailed execution traces showing exactly which validation checks reject legitimate topics. Tested topic extraction with real SO data to identify false positive patterns. Examined _infer_tool_candidates logic and _looks_like_tool_candidate substring matching behavior.

**Learned**: Five interconnected root causes identified: (1) Course metadata noise (pedagogical descriptions) creates taxonomy pollution; (2) Noise topics capture legitimate aliases causing tag misassignment; (3) Subtopic infrastructure exists but never displayed; (4) CRITICAL: _looks_like_tool_candidate uses substring matching - "so" in known_tools matches "proceso**so**s", silently excluding topic 4.2 "Comunicação e sincronização de processos"; (5) Semantic profile extracts course abbreviations (SO, P1, TP1, LM) as tools due to special shape heuristics accepting 2-char tokens with uppercase/digits. Problem 4 is most insidious - topics silently disappear without error when text contains tool substrings. Semantic profile's 2-char minimum allows prepositions and abbreviations to contaminate known_tools, cascading through tool detection and topic validation.

**Completed**: Full root cause analysis with 4 specific code changes identified: (1) Add word-boundary checking to _looks_like_tool_candidate for tools under 4 chars preventing substring false positives; (2) Filter noise topics without numeric codes in build_content_taxonomy using existing validation; (3) Add Subtópico column to FILE_MAP rendering preferred_topic_slug labels; (4) Increase minimum tool length to 3 chars in _infer_tool_candidates preventing course abbreviations from being classified as tools. Cross-repository audit confirmed fixes address both SO-specific severity (35% noise) and platform-wide gaps (missing subtopic display, garbage tool vocabulary).

**Next Steps**: Primary session awaiting final user confirmation to implement all 4 code changes across content_taxonomy.py, navigation.py, and semantic_config.py, then trigger full artifact rebuild for SO and other affected repositories to eliminate noise topics, garbage tags, and tool contamination.


Access 321k tokens of past work via get_observations([IDs]) or mem-search skill.
</claude-mem-context>