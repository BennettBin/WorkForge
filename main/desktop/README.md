# Desktop Integration (Step 10)

## Purpose
- Keep Tauri desktop shell config isolated in `main/desktop`.
- Provide scripts for local backend start/stop during desktop development.

## Files
- `tauri.conf.json`: Tauri v2 app config for local development.
- `capabilities/default.json`: baseline capability permissions.
- `scripts/start-backend.ps1`: starts FastAPI backend in background with logs.
- `scripts/stop-backend.ps1`: stops backend process by PID file.

## Local Dev Flow
1. Start backend:
   `powershell -ExecutionPolicy Bypass -File .\main\desktop\scripts\start-backend.ps1`
2. Start frontend:
   `npm --prefix .\main\frontend run dev`
3. (Optional) run Tauri dev shell:
   `npm --prefix .\main\frontend run tauri:dev`
