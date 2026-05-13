import asyncio
from datetime import datetime

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect

from app.services.auth_service import AuthService

router = APIRouter(tags=["ws"])


@router.websocket("/ws/tasks/{task_id}")
async def task_progress_ws(websocket: WebSocket, task_id: str):
    token = (websocket.query_params.get("token") or "").strip()
    if not token:
        await websocket.close(code=1008)
        return
    auth = AuthService(websocket.app.state.repositories)
    try:
        user = auth.validate_token(token)
    except Exception:
        await websocket.close(code=1008)
        return

    task = websocket.app.state.repositories.tasks.get_by_id(task_id)
    if task is None or task.user_id != user.user_id:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    app = websocket.app
    repos = app.state.repositories
    sent_event_ids: set[str] = set()
    sent_skill_call_ids: set[str] = set()
    try:
        while True:
            task = repos.tasks.get_by_id(task_id)
            events = repos.task_events.list_by_task(task_id)
            agent_runs = repos.agent_runs.list_by_task(task_id)
            skill_calls = repos.skill_calls.list_by_task(task_id)

            new_events = []
            for e in events:
                if e.event_id not in sent_event_ids:
                    sent_event_ids.add(e.event_id)
                    new_events.append(e.model_dump(mode="json"))

            new_skill_calls = []
            for call in skill_calls:
                if call.skill_call_id not in sent_skill_call_ids:
                    sent_skill_call_ids.add(call.skill_call_id)
                    new_skill_calls.append(call.model_dump(mode="json"))

            payload = {
                "task_id": task_id,
                "status": task.status if task else "unknown",
                "task": task.model_dump(mode="json") if task else None,
                "event_count": len(events),
                "new_events": new_events,
                "new_skill_calls": new_skill_calls,
                "agent_runs": [r.model_dump(mode="json") for r in agent_runs[-5:]],
                "server_time": datetime.utcnow().isoformat() + "Z",
            }
            await websocket.send_json(payload)
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        return


@router.websocket("/ws/system/active-users")
async def active_users_ws(websocket: WebSocket):
    token = (websocket.query_params.get("token") or "").strip()
    if not token:
        await websocket.close(code=1008)
        return

    auth = AuthService(websocket.app.state.repositories)
    try:
        user = auth.validate_token(token)
    except Exception:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    websocket.app.state.active_user_tracker.touch(user.user_id)
    try:
        while True:
            await websocket.send_json(websocket.app.state.active_user_tracker.snapshot())
            await asyncio.sleep(3.0)
    except WebSocketDisconnect:
        return
