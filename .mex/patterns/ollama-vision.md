---
name: ollama-vision
description: Working with the Ollama vision pipeline — classification, image description, LaTeX extraction, and debugging vision failures. High-gotcha integration area.
triggers:
  - "vision"
  - "ollama"
  - "image description"
  - "classify image"
  - "image classifier"
  - "qwen"
  - "describe image"
  - "extract latex from image"
  - "image curation"
  - "OllamaClient"
edges:
  - target: context/architecture.md
    condition: when understanding how vision fits into the overall build flow
  - target: context/decisions.md
    condition: when understanding why Ollama is the only vision backend
  - target: context/pdf-pipeline.md
    condition: when vision is used after PDF image extraction (images_dir → Ollama classification)
  - target: patterns/debug-build-failure.md
    condition: when a vision failure causes a build entry to fail
last_updated: 2026-04-22
---

# Ollama Vision

## Context

Key files:
- `src/builder/vision/vision_client.py` — factory: `get_vision_client(config)` always returns `OllamaClient`
- `src/builder/vision/ollama_client.py` — `OllamaClient`, `IMAGE_TYPE_PROMPTS`, `LATEX_EXTRACT_PROMPT`, `_clean_thinking_artifacts`
- `src/builder/vision/image_classifier.py` — `classify_image(path)` (heuristic, no Pillow), `group_images_by_page`, `extract_page_number`
- `src/builder/vision/card_evidence.py` — card-level evidence aggregation for the Image Curator

Ollama runs as an **independent service** — the app never starts it. It must be running before any vision call is made.

## Task: Add or Modify Vision Behavior

### Steps

1. Determine what changes: prompt text, image type, or classification heuristic
2. For new image types: add a key to `IMAGE_TYPE_PROMPTS` in `ollama_client.py`; use Portuguese key names (e.g. `"mapa"`, `"gráfico"`) consistent with the existing keys (`"diagrama"`, `"tabela"`, `"fórmula"`, `"código"`, `"genérico"`)
3. For prompt changes: edit the relevant string in `IMAGE_TYPE_PROMPTS` or `LATEX_EXTRACT_PROMPT`; keep the Portuguese instruction style
4. For heuristic classification changes: edit `classify_image` in `image_classifier.py`; thresholds are module-level constants (`MIN_FILE_SIZE`, `MIN_DIMENSION`, `MAX_ASPECT_RATIO`, `MAX_NOISE_COLORS`)
5. For adding a new classification stage in the UI: update `src/ui/image_curator.py` — calls go through `vision_client.get_vision_client(config).describe_image(path, type, context)`
6. Any call to `OllamaClient` methods is a long blocking operation (up to 600s per image). Do NOT call from the UI thread. Dispatch via `TaskQueueRunner` or a `threading.Thread`; update UI via `widget.after(0, callback)`

### Gotchas

- **DEFAULT_MODEL is `qwen3-vl:235b-cloud`** — this is the configured default but it causes 500 errors when combined with Marker. If Marker is the PDF backend, ensure Ollama model is `qwen3-vl:8b q4_K_M`. These are independent pipelines but can conflict when both run concurrently.
- **`check_availability()` mutates `self.model`** — if the primary model is not found, it silently falls back to `FALLBACK_MODEL` (`qwen3-vl:8b`) and modifies the instance. This means the client object is stateful after the first availability check.
- **Thinking artifacts leak** — Qwen3-VL sometimes ignores `"think": False` and emits reasoning in English before the Portuguese answer. `_clean_thinking_artifacts` handles this; if responses look garbled, check if this function stripped too aggressively.
- **`classify_image` uses pure PNG parsing** — it does NOT use Pillow; it reads PNG IHDR directly. Only PNG files are classified by dimension/color; other formats default to `"genérico"`. Don't add Pillow imports — the design is intentional.
- **`group_images_by_page` searches 3 directories**: `images_dir/` (standard), `images_dir/scanned/{entry_prefix}/` (scanned pages), `images_dir/manual-crops/` (curator crops). New image sources must be added to this function or they won't appear in the curator.
- **`image_type` keys are Portuguese strings** — passing an unknown key returns the `"genérico"` prompt silently. Test with `IMAGE_TYPE_PROMPTS.get("yourkey")` before wiring.

### Verify

- [ ] New image type keys are Portuguese strings matching existing style
- [ ] No blocking vision calls in UI thread callbacks
- [ ] `classify_image` changes tested with PNG files (non-PNG files always return `"genérico"`)
- [ ] `group_images_by_page` updated if a new image source location was added
- [ ] `ollama serve` running with at least `qwen3-vl:8b` pulled before testing

## Task: Debug Vision Failures

### Steps

1. Check if Ollama is running: `curl http://localhost:11434/api/tags` — should return JSON with `models` list
2. Check which model is available: confirm `qwen3-vl:8b` or `qwen3-vl:235b-cloud` appears in the list
3. Check app logs for `[Ollama]` prefix lines — `ollama_client.py` logs every request with payload size and response time
4. If response is empty: check for `"Ollama retornou uma resposta vazia"` in logs — means the model returned no content; verify the model supports multimodal input
5. If response is garbled English: `_clean_thinking_artifacts` may have missed the transition point — inspect `response_text` before cleaning in the logs
6. If 500 error: check if Marker and Ollama cloud model are running concurrently — switch to local model
7. If `FileNotFoundError` in `_encode_image`: `images_dir` is wrong or `BackendRunResult.images_dir` was not propagated from the PDF pipeline

### Failure Reference

| Symptom | Cause | Fix |
|---------|-------|-----|
| `URLError: Connection refused` | Ollama not running | `ollama serve` |
| `RuntimeError: resposta vazia` | Model doesn't support vision | Pull `qwen3-vl:8b`: `ollama pull qwen3-vl:8b` |
| Response in English only | Thinking artifact leak not cleaned | Check `_clean_thinking_artifacts` patterns |
| 500 error from Ollama | `qwen3-vl:235b-cloud` + concurrency | Use `qwen3-vl:8b q4_K_M` |
| No images in Image Curator | `images_dir` is None or wrong prefix | Check `BackendRunResult.images_dir` in manifest |
| Image classified as `decorativa` incorrectly | Heuristic too aggressive | Adjust `MAX_ASPECT_RATIO` or `MIN_FILE_SIZE` constants |

## Update Scaffold

- [ ] Update `context/decisions.md` if a second vision backend is added or Ollama is replaced
- [ ] Update `context/architecture.md` VisionClient entry if the factory pattern changes
- [ ] Update `.mex/ROUTER.md` "Current Project State" if vision now works with a new model
