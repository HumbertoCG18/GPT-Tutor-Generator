---
name: add-ui-feature
description: Adding a new feature to the Tkinter desktop UI — dialogs, tabs, dashboard widgets, or new entry controls.
triggers:
  - "UI"
  - "dialog"
  - "tkinter"
  - "tab"
  - "widget"
  - "button"
  - "dashboard"
  - "add setting"
edges:
  - target: context/conventions.md
    condition: always — check naming and verify checklist
  - target: context/architecture.md
    condition: when the UI feature triggers builder logic (understand the flow first)
  - target: patterns/add-builder-submodule.md
    condition: when the UI feature requires new processing logic in a builder subpackage
last_updated: 2026-04-22
---

# Add UI Feature

## Context

UI code lives in `src/ui/`. Key files:
- `src/ui/app.py` — main window, tab routing, entry list management, task queue integration
- `src/ui/dialogs.py` — settings dialog, entry edit dialogs, status dialog, help window
- `src/ui/repo_dashboard.py` — `RepoDashboard` widget and `collect_repo_metrics`
- `src/ui/curator_studio.py` — manual review / curation studio
- `src/ui/image_curator.py` — image curation and visual extraction
- `src/ui/theme.py` — `ThemeManager` and `AppConfig` (persisted preferences)

The app is single-threaded on the UI side. All builder work runs via `TaskQueueRunner` in a background thread. UI updates from threads must use `widget.after(0, callback)` — never update Tkinter widgets directly from a non-UI thread.

## Steps

1. Decide which file owns the feature: small standalone dialog → `dialogs.py`; new tab → `app.py`; dashboard column → `repo_dashboard.py`
2. If the feature needs a new persistent config key: add it to `AppConfig` in `theme.py` with a sensible default
3. If the feature triggers a build or task: enqueue a `RepoTask` via `RepoTaskStore` and let `TaskQueueRunner` run it — do NOT call `RepoBuilder` directly from a UI callback
4. If the feature needs to update the UI with build progress: use `builder.progress_callback` (set by the UI before starting the task) and call updates via `root.after(0, ...)`
5. For new dialogs: follow the pattern in `dialogs.py` — `tk.Toplevel`, grab focus with `dialog.grab_set()`, `dialog.wait_window()` for modal behavior

## Gotchas

- **Thread safety:** Any Tkinter widget update from a non-main thread will crash randomly. Always use `widget.after(0, fn)` for callbacks from `TaskQueueRunner`.
- **AppConfig** is loaded once on startup from JSON. Changes made at runtime must call `ThemeManager.save_config()` to persist — otherwise they are lost on restart.
- **Entry list state:** `FileEntry` objects are stored in `SubjectStore` (JSON persistence). After editing an entry, call the appropriate `SubjectStore.save()` — UI list refresh does not persist.
- **Dialog sizing:** Tkinter dialogs do not auto-resize on Windows with high-DPI screens. Use `dialog.geometry("NNNxNNN")` for new dialogs; check at 125% and 150% DPI.
- **`collect_repo_metrics`** in `repo_dashboard.py` reads from `manifest.json` — it is I/O heavy. Do not call it on every UI refresh tick; cache the result.

## Verify

- [ ] All widget updates from background threads go through `widget.after(0, callback)`
- [ ] New config keys added to `AppConfig` with defaults
- [ ] Build operations enqueued via `RepoTaskStore`, not called directly
- [ ] Dialog uses `grab_set()` + `wait_window()` if modal
- [ ] Manual test: open the feature, trigger the action, close the app, reopen — confirm state persisted correctly

## Update Scaffold
- [ ] Update `.mex/ROUTER.md` "Current Project State" if a significant UI feature was added
- [ ] If this introduced a new non-obvious pattern, update `context/conventions.md`
