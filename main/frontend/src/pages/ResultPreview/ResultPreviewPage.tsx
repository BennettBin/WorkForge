import { Alert, Button, Card, Form, Input, InputNumber, List, Select, Space, Typography } from "antd";
import { useEffect, useMemo, useState } from "react";
import { downloadFile, getJson, postJson } from "../../api/http";
import { useAppStore } from "../../store/appStore";
import { ApiEnvelope } from "../../types/api";

type VersionItem = { output_id: string; version: number; file_path: string; exists?: boolean; download_url?: string };
type TaskItem = {
  task_id: string;
  status: string;
  task_type?: string;
  user_requirement?: string;
};

export default function ResultPreviewPage() {
  const { task, auth, setTask } = useAppStore();
  const [versions, setVersions] = useState<VersionItem[]>([]);
  const [completedTasks, setCompletedTasks] = useState<TaskItem[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const effectiveTaskId = useMemo(() => selectedTaskId || task.activeTaskId, [selectedTaskId, task.activeTaskId]);

  useEffect(() => {
    loadCompletedTasks().catch((e) => setError(String(e)));
  }, [auth.userId]); // eslint-disable-line react-hooks/exhaustive-deps

  async function loadCompletedTasks() {
    if (!auth.userId) return;
    const res = await getJson<ApiEnvelope<{ items: TaskItem[] }>>(`/v1/tasks/user/${auth.userId}`);
    const done = (res.data.items || []).filter((x) =>
      ["completed", "revision_completed"].includes(String(x.status || "").toLowerCase())
    );
    setCompletedTasks(done);
    if (!selectedTaskId && done.length > 0) {
      const preferred = task.activeTaskId && done.some((x) => x.task_id === task.activeTaskId) ? task.activeTaskId : done[0].task_id;
      setSelectedTaskId(preferred);
      setTask((prev) => ({ ...prev, activeTaskId: preferred }));
    }
  }

  async function loadVersions() {
    if (!effectiveTaskId) {
      return;
    }
    setError(null);
    const res = await getJson<ApiEnvelope<{ items: VersionItem[] }>>(`/v1/tasks/${effectiveTaskId}/versions`);
    setVersions(res.data.items);
  }

  async function downloadLatest() {
    if (!effectiveTaskId) return;
    const res = await getJson<ApiEnvelope<{ file_path: string; exists: boolean; download_url: string }>>(
      `/v1/tasks/${effectiveTaskId}/download/latest`
    );
    setMessage(`Latest file: ${res.data.file_path} (exists=${res.data.exists ? "true" : "false"})`);
    await downloadFile(res.data.download_url, `task-${effectiveTaskId}-latest`);
  }

  async function onRevision(values: { page_index?: number; instruction: string }) {
    if (!effectiveTaskId) return;
    setError(null);
    try {
      const payload = {
        page_index: values.page_index ?? null,
        instruction: values.instruction,
      };
      const res = await postJson<ApiEnvelope<{ new_version: number; revised_pages?: number[] }>>(`/v1/tasks/${effectiveTaskId}/revisions`, payload);
      setMessage(`Revision done. New version: v${res.data.new_version}`);
      await loadVersions();
    } catch (e) {
      setError(String(e));
    }
  }

  async function onRollback(values: { target_version: number }) {
    if (!effectiveTaskId) return;
    setError(null);
    try {
      const res = await postJson<ApiEnvelope<{ new_version: number; source_version: number }>>(
        `/v1/tasks/${effectiveTaskId}/versions/rollback/${values.target_version}`,
        {}
      );
      setMessage(`Rollback done from v${res.data.source_version} to v${res.data.new_version}.`);
      await loadVersions();
    } catch (e) {
      setError(String(e));
    }
  }

  async function onCompare(values: { from_version: number; to_version: number }) {
    if (!effectiveTaskId) return;
    setError(null);
    try {
      const res = await getJson<ApiEnvelope<{ changed_page_count: number }>>(
        `/v1/tasks/${effectiveTaskId}/versions/compare?from_version=${values.from_version}&to_version=${values.to_version}`
      );
      setMessage(`Compare result: changed pages = ${res.data.changed_page_count}`);
    } catch (e) {
      setError(String(e));
    }
  }

  async function clearTaskCache() {
    if (!effectiveTaskId) return;
    setError(null);
    try {
      const res = await postJson<ApiEnvelope<{ removed: boolean; removed_files: number }>>(
        `/v1/tasks/${effectiveTaskId}/cache/clear`,
        {}
      );
      setMessage(`Cache cleared: removed=${res.data.removed ? "true" : "false"}, files=${res.data.removed_files}`);
    } catch (e) {
      setError(String(e));
    }
  }

  return (
    <Card>
      <Typography.Title level={4}>Result Preview</Typography.Title>
      <Typography.Paragraph>Task: {effectiveTaskId ?? "none"}</Typography.Paragraph>
      <Space style={{ marginBottom: 12 }}>
        <Button onClick={() => loadCompletedTasks().catch((e) => setError(String(e)))}>Load Completed Tasks</Button>
        <Select
          style={{ width: 460 }}
          placeholder="Select completed task"
          value={effectiveTaskId || undefined}
          options={completedTasks.map((t) => ({
            value: t.task_id,
            label: `${t.task_id} / ${t.task_type || "unknown"} / ${t.status}`,
          }))}
          onChange={(v) => {
            setSelectedTaskId(v);
            setTask((prev) => ({ ...prev, activeTaskId: v }));
            setVersions([]);
          }}
        />
      </Space>
      <Space direction="vertical" style={{ width: "100%" }}>
        {message && <Alert type="success" message={message} />}
        {error && <Alert type="error" message={error} />}
      </Space>
      <Space style={{ marginBottom: 12 }}>
        <Button onClick={loadVersions}>Load Versions</Button>
        <Button onClick={downloadLatest}>Download Latest Path</Button>
        <Button danger onClick={clearTaskCache}>
          Clear Task Cache
        </Button>
      </Space>
      <List
        bordered
        dataSource={versions}
        renderItem={(v) => (
          <List.Item>
            <span>
              v{v.version}: {v.file_path} {v.exists === false ? "(missing)" : ""}
            </span>
            <Button
              size="small"
              onClick={() => {
                if (!effectiveTaskId) return;
                void downloadFile(`/v1/tasks/${effectiveTaskId}/download/${v.version}/file`, `task-${effectiveTaskId}-v${v.version}`);
              }}
            >
              Download
            </Button>
          </List.Item>
        )}
      />
      <Typography.Title level={5}>Revision</Typography.Title>
      <Form layout="vertical" onFinish={onRevision}>
        <Form.Item name="page_index">
          <InputNumber min={1} placeholder="Page (Optional)" style={{ width: 220 }} />
        </Form.Item>
        <Form.Item name="instruction" rules={[{ required: true }]}>
          <Input.TextArea rows={4} placeholder="Instruction" />
        </Form.Item>
        <Typography.Paragraph type="secondary">
          If page is empty, the model will infer intent and revise one or multiple related slides.
        </Typography.Paragraph>
        <Button htmlType="submit" type="primary">
          Revise
        </Button>
      </Form>
      <Typography.Title level={5}>Rollback</Typography.Title>
      <Form layout="inline" onFinish={onRollback}>
        <Form.Item name="target_version" rules={[{ required: true }]}>
          <InputNumber min={1} placeholder="Target version" />
        </Form.Item>
        <Button htmlType="submit">Rollback</Button>
      </Form>
      <Typography.Title level={5}>Compare</Typography.Title>
      <Form layout="inline" onFinish={onCompare}>
        <Form.Item name="from_version" rules={[{ required: true }]}>
          <InputNumber min={1} placeholder="From" />
        </Form.Item>
        <Form.Item name="to_version" rules={[{ required: true }]}>
          <InputNumber min={1} placeholder="To" />
        </Form.Item>
        <Button htmlType="submit">Compare</Button>
      </Form>
    </Card>
  );
}
