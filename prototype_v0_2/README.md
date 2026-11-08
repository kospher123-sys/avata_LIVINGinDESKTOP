# v0.2 prototype — character state separation

This directory is intentionally separate from the user's locally working v0.1 `main.py`.

## Run (Windows PowerShell)

From the repository root, with `.venv` activated:

```powershell
python -m pip install PySide6
python prototype_v0_2/main.py
```

## Check

- Character alternates between walking and standing still.
- Character turns around at both desktop work-area edges.
- Character is transparent and click-through.
- Character stays above ordinary windows.
- Quit via the system tray icon's '종료' action.

## Structure

- `avatar.py`: state machine and movement, no GUI
- `overlay.py`: PySide6 display, timer, tray, procedural fallback art
- `main.py`: application entry point

Status: **v0.2 locally verified by the user on 2026-11-08**: IDLE/WALK switching, edge turns, click-through and Always on Top. This documentation update did not rerun the app or change code. Multi-monitor and exclusive fullscreen behavior have not been tested.
