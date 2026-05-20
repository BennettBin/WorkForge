import { Alert, Button, Card, List, Progress, Select, Space, Tag, Tooltip, Typography } from "antd";
import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { getBaseUrl, getJson, getWsBaseUrl } from "../../api/http";
import { useAppStore } from "../../store/appStore";
import { ApiEnvelope } from "../../types/api";

type TaskData = {
  task: { task_id: string; status: string; user_requirement: string; task_type?: string };
  agent_runs: Array<{ run_id: string; agent_name: string; status: string; output?: string }>;
  events: Array<{ event_id: string; stage: string; message: string; created_at?: string }>;
  skill_calls: Array<{ skill_call_id: string; skill_name: string; input?: string; output?: string; created_at?: string }>;
};

type TemplatePreviewData = {
  template_file?: { name?: string; download_url?: string; size_bytes?: number };
  preview_images?: Array<{ page: number; url: string; size_bytes: number; data_url?: string }>;
};

type ChatItem = {
  id: string;
  role: "system" | "user" | "llm";
  title: string;
  content: string;
  createdAt?: string;
  sortKey: number;
};

function parseJsonSafe(text?: string): Record<string, unknown> {
  if (!text) return {};
  try {
    return JSON.parse(text) as Record<string, unknown>;
  } catch {
    return {};
  }
}

function shortText(text: string, max = 160): string {
  if (text.length <= max) return text;
  return `${text.slice(0, max)}...`;
}

function templatePreviewCacheKey(taskId: string): string {
  return `wf_template_preview_${taskId}`;
}

function blobToDataUrl(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ""));
    reader.onerror = () => reject(reader.error || new Error("Failed to read image blob."));
    reader.readAsDataURL(blob);
  });
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

async function loadReadyTemplatePreview(taskId: string, onStep?: (message: string) => void): Promise<TemplatePreviewData> {
  const token = localStorage.getItem("wf_token") || "";
  let lastError: unknown = null;
  for (let attempt = 0; attempt < 30; attempt += 1) {
    try {
      onStep?.("Checking template preview metadata and screenshot.");
      const res = await getJson<ApiEnvelope<TemplatePreviewData>>(`/v1/tasks/${taskId}/template-preview`);
      const previewData = { ...res.data };
      const previewImages = (previewData.preview_images || []).slice(0, 1);
      if (previewImages.length === 0) {
        throw new Error("Template preview image is not ready.");
      }
      onStep?.("Downloading template preview screenshot.");
      for (const image of previewImages) {
        const imageRes = await fetch(`${getBaseUrl()}${image.url}`, {
          headers: token ? { Authorization: `Bearer ${token}` } : undefined,
        });
        if (!imageRes.ok) {
          throw new Error(`Template preview image failed: ${imageRes.status}`);
        }
        image.data_url = await blobToDataUrl(await imageRes.blob());
      }
      if (!previewImages[0]?.data_url) {
        throw new Error("Template preview image data is not ready.");
      }
      onStep?.("Template preview screenshot is ready.");
      return previewData;
    } catch (err) {
      lastError = err;
      await sleep(1000);
    }
  }
  throw lastError || new Error("Template preview image is not ready.");
}

function progressForStatus(status: string): number {
  if (status === "completed" || status === "revision_completed") return 100;
  if (status === "idle") return 0;
  if (status === "requires_user_completion") return 80;
  if (status.startsWith("failed")) return 100;
  return 60;
}

export default function TaskRunningPage() {
  const navigate = useNavigate();
  const { taskId: routeTaskId } = useParams<{ taskId?: string }>();
  const {
    task,
    setTask,
    upsertRunningTask,
    removeRunningTask,
    setSelectedRunningTaskId,
  } = useAppStore();

  const [status, setStatus] = useState<string>("idle");
  const [events, setEvents] = useState<Array<{ event_id: string; stage: string; message: string; created_at?: string }>>([]);
  const [runs, setRuns] = useState<Array<{ run_id: string; agent_name: string; status: string; output?: string }>>([]);
  const [skillCalls, setSkillCalls] = useState<Array<{ skill_call_id: string; skill_name: string; input?: string; output?: string; created_at?: string }>>([]);
  const [activeUsers, setActiveUsers] = useState<number>(0);
  const [requirement, setRequirement] = useState<string>("");
  const [taskType, setTaskType] = useState<string>("");
  const [isPreparingTemplatePreview, setIsPreparingTemplatePreview] = useState<boolean>(false);
  const [previewPreparationSteps, setPreviewPreparationSteps] = useState<string[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const activeUsersWsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<number | null>(null);
  const reconnectAttemptRef = useRef<number>(0);
  const logPanelRef = useRef<HTMLDivElement | null>(null);
  const templatePreviewNavigatingRef = useRef<string | null>(null);

  const currentTaskId = useMemo(
    () => routeTaskId || task.selectedRunningTaskId || task.activeTaskId || null,
    [routeTaskId, task.selectedRunningTaskId, task.activeTaskId]
  );
  const taskOptions = useMemo(() => {
    const base = task.runningTasks.map((x) => ({
      value: x.taskId,
      label: `${x.taskId} / ${x.taskType || "unknown"} / ${x.status}`,
    }));
    if (currentTaskId && !base.some((x) => x.value === currentTaskId)) {
      base.unshift({ value: currentTaskId, label: `${currentTaskId} / ${taskType || "unknown"} / ${status}` });
    }
    return base;
  }, [task.runningTasks, currentTaskId, taskType, status]);
  const isTemplateGenerationCompleted =
    taskType === "template_generation" && (status === "completed" || status === "revision_completed");

  async function refresh(targetTaskId: string) {
    const res = await getJson<ApiEnvelope<TaskData>>(`/v1/tasks/${targetTaskId}`);
    setStatus(res.data.task.status);
    setTask((prev) => ({ ...prev, activeTaskId: targetTaskId, activeTaskStatus: res.data.task.status }));
    setSelectedRunningTaskId(targetTaskId);
    setRequirement(res.data.task.user_requirement || "");
    setTaskType(res.data.task.task_type || "");
    setEvents(res.data.events || []);
    setRuns(res.data.agent_runs || []);
    setSkillCalls(res.data.skill_calls || []);
    upsertRunningTask({
      taskId: targetTaskId,
      status: res.data.task.status,
      taskType: res.data.task.task_type || "",
      title: res.data.task.user_requirement || "",
    });
  }

  const chatItems: ChatItem[] = [];
  if (requirement.trim()) {
    chatItems.push({
      id: "user_requirement",
      role: "user",
      title: "User Requirement",
      content: requirement.trim(),
      sortKey: 0,
    });
  }
  for (const evt of events) {
    chatItems.push({
      id: `evt_${evt.event_id}`,
      role: "system",
      title: `System Event / ${evt.stage}`,
      content: evt.message || "",
      createdAt: evt.created_at,
      sortKey: evt.created_at ? Date.parse(evt.created_at) || 0 : 0,
    });
  }
  previewPreparationSteps.forEach((step, index) => {
    chatItems.push({
      id: `preview_step_${index}`,
      role: "system",
      title: "System Event / preparing_preview",
      content: step,
      sortKey: Date.now() + index,
    });
  });
  for (const call of skillCalls) {
    if (call.skill_name === "llm_text_generation" || call.skill_name === "llm_text_generation_failed") {
      const inObj = parseJsonSafe(call.input);
      const outObj = parseJsonSafe(call.output);
      const provider = String(inObj.provider_type || "");
      const model = String(inObj.model_name || "");
      const prompt = String(inObj.prompt || "");
      const text = call.skill_name === "llm_text_generation" ? String(outObj.text || "") : String(outObj.error || "");
      const suffix = provider || model ? ` (${provider}/${model})` : "";
      if (prompt) {
        chatItems.push({
          id: `llm_in_${call.skill_call_id}`,
          role: "llm",
          title: `LLM Input${suffix}`,
          content: prompt,
          createdAt: call.created_at,
          sortKey: call.created_at ? Date.parse(call.created_at) || 0 : 0,
        });
      }
      if (text) {
        chatItems.push({
          id: `llm_out_${call.skill_call_id}`,
          role: "llm",
          title: call.skill_name === "llm_text_generation" ? `LLM Output${suffix}` : `LLM Error${suffix}`,
          content: text,
          createdAt: call.created_at,
          sortKey: call.created_at ? Date.parse(call.created_at) || 0 : 0,
        });
      }
    }
  }
  chatItems.sort((a, b) => a.sortKey - b.sortKey);

  useEffect(() => {
    const panel = logPanelRef.current;
    if (panel) panel.scrollTop = panel.scrollHeight;
  }, [chatItems.length]);

  useEffect(() => {
    if (!currentTaskId) return;
    refresh(currentTaskId).catch(() => undefined);
  }, [currentTaskId]);

  useEffect(() => {
    if (!currentTaskId) return;
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    const token = localStorage.getItem("wf_token") || "";
    const ws = new WebSocket(`${getWsBaseUrl()}/ws/tasks/${currentTaskId}?token=${encodeURIComponent(token)}`);
    wsRef.current = ws;
    ws.onmessage = (ev) => {
      const payload = JSON.parse(ev.data) as {
        status: string;
        task?: { user_requirement?: string; task_type?: string };
        new_events: Array<{ event_id: string; stage: string; message: string; created_at?: string }>;
        new_skill_calls: Array<{ skill_call_id: string; skill_name: string; input?: string; output?: string; created_at?: string }>;
        agent_runs: Array<{ run_id: string; agent_name: string; status: string; output?: string }>;
      };
      setStatus(payload.status);
      setTask((prev) => ({ ...prev, activeTaskId: currentTaskId, activeTaskStatus: payload.status }));
      setSelectedRunningTaskId(currentTaskId);
      upsertRunningTask({
        taskId: currentTaskId,
        status: payload.status,
        taskType: payload.task?.task_type || taskType,
        title: payload.task?.user_requirement || requirement,
      });
      if (payload.task?.user_requirement) setRequirement(payload.task.user_requirement);
      if (payload.task?.task_type) setTaskType(payload.task.task_type);
      setEvents((prev) => {
        const map = new Map(prev.map((x) => [x.event_id, x]));
        for (const evt of payload.new_events || []) map.set(evt.event_id, evt);
        return Array.from(map.values());
      });
      setSkillCalls((prev) => {
        const map = new Map(prev.map((x) => [x.skill_call_id, x]));
        for (const call of payload.new_skill_calls || []) map.set(call.skill_call_id, call);
        return Array.from(map.values());
      });
      if (payload.agent_runs) setRuns(payload.agent_runs);
    };
    return () => {
      ws.close();
    };
  }, [currentTaskId]);

  useEffect(() => {
    let stopped = false;
    const token = localStorage.getItem("wf_token");
    if (!token) {
      setActiveUsers(0);
      return;
    }
    const connect = () => {
      if (stopped) return;
      const ws = new WebSocket(`${getWsBaseUrl()}/ws/system/active-users?token=${encodeURIComponent(token)}`);
      activeUsersWsRef.current = ws;
      ws.onopen = () => {
        reconnectAttemptRef.current = 0;
      };
      ws.onmessage = (ev) => {
        const payload = JSON.parse(ev.data) as { active_users?: number };
        setActiveUsers(Number(payload.active_users || 0));
      };
      ws.onclose = () => {
        if (stopped) return;
        const attempt = reconnectAttemptRef.current + 1;
        reconnectAttemptRef.current = attempt;
        const delay = Math.min(10000, attempt <= 1 ? 2000 : attempt <= 3 ? 5000 : 10000);
        reconnectTimerRef.current = window.setTimeout(connect, delay);
      };
      ws.onerror = () => ws.close();
    };
    connect();
    return () => {
      stopped = true;
      if (reconnectTimerRef.current !== null) window.clearTimeout(reconnectTimerRef.current);
      if (activeUsersWsRef.current) activeUsersWsRef.current.close();
    };
  }, []);

  useEffect(() => {
    if (!currentTaskId) return;
    if (status === "completed" || status === "revision_completed") {
      if (!taskType) return;
      if (taskType !== "template_generation") {
        removeRunningTask(currentTaskId);
        navigate(`/result?taskId=${encodeURIComponent(currentTaskId)}`);
        return;
      }
      if (templatePreviewNavigatingRef.current === currentTaskId) return;
      templatePreviewNavigatingRef.current = currentTaskId;
      void (async () => {
        setIsPreparingTemplatePreview(true);
        setTask((prev) => ({ ...prev, activeTaskId: currentTaskId, activeTaskStatus: "preparing_preview" }));
        upsertRunningTask({
          taskId: currentTaskId,
          status: "preparing_preview",
          taskType,
          title: requirement,
        });
        setPreviewPreparationSteps(["Template generation completed. Preparing preview before opening the preview page."]);
        const addPreviewStep = (step: string) => {
          setPreviewPreparationSteps((prev) => (prev[prev.length - 1] === step ? prev : [...prev, step].slice(-6)));
        };
        const previewData = await loadReadyTemplatePreview(currentTaskId, addPreviewStep);
        addPreviewStep("Preview cache is ready. Opening template preview page.");
        sessionStorage.setItem(templatePreviewCacheKey(currentTaskId), JSON.stringify(previewData));
        removeRunningTask(currentTaskId);
        navigate(`/template-preview?taskId=${encodeURIComponent(currentTaskId)}`);
      })().catch(() => {
        setIsPreparingTemplatePreview(false);
        templatePreviewNavigatingRef.current = null;
      });
    }
  }, [status, navigate, taskType, currentTaskId, removeRunningTask, upsertRunningTask, requirement]);

  useEffect(() => {
    if (!currentTaskId) return;
    if (status !== "requires_user_completion") return;
    if (taskType !== "template_generation") return;
    navigate(`/template-generation/recovery?taskId=${encodeURIComponent(currentTaskId)}`);
  }, [status, taskType, currentTaskId, navigate]);

  useEffect(() => {
    const marker = events.find((e) => (e.message || "").startsWith("capability_setup_required:"));
    if (!marker || !currentTaskId) return;
    const capability = encodeURIComponent((marker.message || "").split(":", 2)[1] || "");
    navigate(`/capabilities/setup?taskId=${encodeURIComponent(currentTaskId)}&capability=${capability}`);
  }, [events, navigate, currentTaskId]);

  if (!currentTaskId) {
    return (
      <Card>
        <Typography.Title level={4}>Task Running</Typography.Title>
        <Typography.Paragraph>No active running task selected.</Typography.Paragraph>
      </Card>
    );
  }

  return (
    <Card>
      <Typography.Title level={4}>Task Running</Typography.Title>
      <Space direction="vertical" style={{ width: "100%" }}>
        <Space>
          <Tag color="blue">Task: {currentTaskId}</Tag>
          <Tag color="purple">Status: {status}</Tag>
          <Tag color="geekblue">Active Users (10m): {activeUsers}</Tag>
        </Space>
        <Select
          style={{ width: 420 }}
          value={currentTaskId}
          options={taskOptions}
          onChange={(value) => {
            setSelectedRunningTaskId(value);
            navigate(`/tasks/running/${encodeURIComponent(value)}`);
          }}
        />
        {status === "requires_user_completion" && taskType === "template_generation" ? (
          <Alert
            type="warning"
            showIcon
            message="Template generation requires user completion"
            description="The template bundle failed validation. Review the missing items, fill the suggested values, and resume the template build."
            action={
              <Button size="small" onClick={() => navigate(`/template-generation/recovery?taskId=${encodeURIComponent(currentTaskId)}`)}>
                Open Recovery
              </Button>
            }
          />
        ) : null}
        <Progress
          percent={isTemplateGenerationCompleted ? 95 : progressForStatus(status)}
          status={status.startsWith("failed") ? "exception" : (status === "requires_user_completion" || isTemplateGenerationCompleted || isPreparingTemplatePreview) ? "active" : undefined}
        />
        <Button onClick={() => refresh(currentTaskId)}>Refresh</Button>
      </Space>

      <Typography.Title level={5}>Live Conversation</Typography.Title>
      <div
        ref={logPanelRef}
        style={{ maxHeight: 320, overflowY: "auto", border: "1px solid #f0f0f0", borderRadius: 8, padding: 8 }}
      >
        <List
          size="small"
          dataSource={chatItems}
          locale={{ emptyText: "No conversation records yet" }}
          renderItem={(item) => (
            <List.Item>
              <Space align="start">
                <Tag color={item.role === "user" ? "blue" : item.role === "llm" ? "purple" : "geekblue"}>
                  {item.role === "user" ? "USER" : item.role === "llm" ? "LLM" : "SYSTEM"}
                </Tag>
                <div style={{ maxWidth: 760 }}>
                  <div>
                    <strong>{item.title}</strong>
                    {item.createdAt ? <span style={{ marginLeft: 8, color: "#888" }}>{item.createdAt}</span> : null}
                  </div>
                  <Tooltip title={<div style={{ maxWidth: 680, whiteSpace: "pre-wrap", wordBreak: "break-word" }}>{item.content}</div>}>
                    <Typography.Text>{shortText(item.content, 180)}</Typography.Text>
                  </Tooltip>
                </div>
              </Space>
            </List.Item>
          )}
        />
      </div>

      <Typography.Title level={5}>Events</Typography.Title>
      <List
        dataSource={events}
        renderItem={(item) => (
          <List.Item>
            <Tag>{item.stage}</Tag>
            <span>{item.message}</span>
          </List.Item>
        )}
      />
      <Typography.Title level={5}>Agent Timeline</Typography.Title>
      <List
        dataSource={runs}
        renderItem={(item) => (
          <List.Item>
            <Tag color={item.status === "failed" ? "red" : "green"}>{item.agent_name}</Tag>
            <span>{item.output}</span>
          </List.Item>
        )}
      />
    </Card>
  );
}
