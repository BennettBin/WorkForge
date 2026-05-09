import { Button, Card, List, Progress, Space, Tag, Tooltip, Typography } from "antd";
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getJson } from "../../api/http";
import { useAppStore } from "../../store/appStore";
import { ApiEnvelope } from "../../types/api";

type TaskData = {
  task: { task_id: string; status: string; user_requirement: string };
  agent_runs: Array<{ run_id: string; agent_name: string; status: string; output?: string }>;
  events: Array<{ event_id: string; stage: string; message: string; created_at?: string }>;
  skill_calls: Array<{ skill_call_id: string; skill_name: string; input?: string; output?: string; created_at?: string }>;
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
  if (!text) {
    return {};
  }
  try {
    return JSON.parse(text) as Record<string, unknown>;
  } catch {
    return {};
  }
}

function shortText(text: string, max = 160): string {
  if (text.length <= max) {
    return text;
  }
  return `${text.slice(0, max)}...`;
}

export default function TaskRunningPage() {
  const navigate = useNavigate();
  const { task, setTask } = useAppStore();
  const [status, setStatus] = useState<string>("idle");
  const [events, setEvents] = useState<Array<{ event_id: string; stage: string; message: string; created_at?: string }>>([]);
  const [runs, setRuns] = useState<Array<{ run_id: string; agent_name: string; status: string; output?: string }>>([]);
  const [skillCalls, setSkillCalls] = useState<Array<{ skill_call_id: string; skill_name: string; input?: string; output?: string; created_at?: string }>>([]);
  const [requirement, setRequirement] = useState<string>("");
  const wsRef = useRef<WebSocket | null>(null);
  const logPanelRef = useRef<HTMLDivElement | null>(null);

  async function refresh() {
    if (!task.activeTaskId) {
      return;
    }
    const res = await getJson<ApiEnvelope<TaskData>>(`/v1/tasks/${task.activeTaskId}`);
    setStatus(res.data.task.status);
    setTask({ activeTaskId: task.activeTaskId, activeTaskStatus: res.data.task.status });
    setRequirement(res.data.task.user_requirement || "");
    setEvents(res.data.events || []);
    setRuns(res.data.agent_runs || []);
    setSkillCalls(res.data.skill_calls || []);
  }

  const chatItems: ChatItem[] = [];
  if (requirement.trim()) {
    chatItems.push({
      id: "user_requirement",
      role: "user",
      title: "用户需求",
      content: requirement.trim(),
      sortKey: 0,
    });
  }
  for (const evt of events) {
    chatItems.push({
      id: `evt_${evt.event_id}`,
      role: "system",
      title: `系统事件 · ${evt.stage}`,
      content: evt.message || "",
      createdAt: evt.created_at,
      sortKey: evt.created_at ? Date.parse(evt.created_at) || 0 : 0,
    });
  }
  for (const call of skillCalls) {
    if (call.skill_name === "llm_text_generation" || call.skill_name === "llm_text_generation_failed") {
      const inObj = parseJsonSafe(call.input);
      const outObj = parseJsonSafe(call.output);
      const provider = String(inObj.provider_type || "");
      const model = String(inObj.model_name || "");
      const prompt = String(inObj.prompt || "");
      const text = call.skill_name === "llm_text_generation"
        ? String(outObj.text || "")
        : String(outObj.error || "");
      const suffix = provider || model ? ` (${provider}/${model})` : "";
      if (prompt) {
        chatItems.push({
          id: `llm_in_${call.skill_call_id}`,
          role: "llm",
          title: `大模型输入${suffix}`,
          content: prompt,
          createdAt: call.created_at,
          sortKey: call.created_at ? Date.parse(call.created_at) || 0 : 0,
        });
      }
      if (text) {
        chatItems.push({
          id: `llm_out_${call.skill_call_id}`,
          role: "llm",
          title: call.skill_name === "llm_text_generation" ? `大模型输出${suffix}` : `大模型错误${suffix}`,
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
    if (panel) {
      panel.scrollTop = panel.scrollHeight;
    }
  }, [chatItems.length]);

  useEffect(() => {
    refresh().catch(() => undefined);
    if (!task.activeTaskId) {
      return;
    }
    const ws = new WebSocket(`ws://127.0.0.1:8080/ws/tasks/${task.activeTaskId}`);
    wsRef.current = ws;
    ws.onmessage = (ev) => {
      const payload = JSON.parse(ev.data) as {
        status: string;
        task?: { user_requirement?: string };
        new_events: Array<{ event_id: string; stage: string; message: string; created_at?: string }>;
        new_skill_calls: Array<{ skill_call_id: string; skill_name: string; input?: string; output?: string; created_at?: string }>;
        agent_runs: Array<{ run_id: string; agent_name: string; status: string; output?: string }>;
      };
      setStatus(payload.status);
      setTask({ activeTaskId: task.activeTaskId, activeTaskStatus: payload.status });
      if (payload.task?.user_requirement) {
        setRequirement(payload.task.user_requirement);
      }
      setEvents((prev) => {
        const map = new Map(prev.map((x) => [x.event_id, x]));
        for (const evt of payload.new_events || []) {
          map.set(evt.event_id, evt);
        }
        return Array.from(map.values());
      });
      setSkillCalls((prev) => {
        const map = new Map(prev.map((x) => [x.skill_call_id, x]));
        for (const call of payload.new_skill_calls || []) {
          map.set(call.skill_call_id, call);
        }
        return Array.from(map.values());
      });
      if (payload.agent_runs) {
        setRuns(payload.agent_runs);
      }
    };
    return () => {
      ws.close();
    };
  }, [task.activeTaskId, setTask]);

  useEffect(() => {
    if (status === "completed" || status === "revision_completed") {
      navigate("/result");
    }
  }, [status, navigate]);

  return (
    <Card>
      <Typography.Title level={4}>Task Running</Typography.Title>
      <Space direction="vertical" style={{ width: "100%" }}>
        <Tag color="blue">Task: {task.activeTaskId ?? "none"}</Tag>
        <Tag color="purple">Status: {status}</Tag>
        <Progress percent={status === "completed" ? 100 : status === "idle" ? 0 : 60} />
        <Button onClick={() => refresh()}>Refresh</Button>
      </Space>
      <Typography.Title level={5}>Live Conversation</Typography.Title>
      <div
        ref={logPanelRef}
        style={{
          maxHeight: 320,
          overflowY: "auto",
          border: "1px solid #f0f0f0",
          borderRadius: 8,
          padding: 8
        }}
      >
        <List
          size="small"
          dataSource={chatItems}
          locale={{ emptyText: "暂无对话记录" }}
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
                  <Tooltip
                    title={<div style={{ maxWidth: 680, whiteSpace: "pre-wrap", wordBreak: "break-word" }}>{item.content}</div>}
                  >
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
