import { Alert, Button, Card, Form, Input, InputNumber, List, Space, Typography } from "antd";
import { useState } from "react";
import { getBaseUrl, getJson, postJson } from "../../api/http";
import { useAppStore } from "../../store/appStore";
import { ApiEnvelope } from "../../types/api";

type VersionItem = { output_id: string; version: number; file_path: string; exists?: boolean; download_url?: string };

export default function ResultPreviewPage() {
  const { task } = useAppStore();
  const [versions, setVersions] = useState<VersionItem[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadVersions() {
    if (!task.activeTaskId) {
      return;
    }
    setError(null);
    const res = await getJson<ApiEnvelope<{ items: VersionItem[] }>>(`/v1/tasks/${task.activeTaskId}/versions`);
    setVersions(res.data.items);
  }

  async function downloadLatest() {
    if (!task.activeTaskId) return;
    const res = await getJson<ApiEnvelope<{ file_path: string; exists: boolean; download_url: string }>>(
      `/v1/tasks/${task.activeTaskId}/download/latest`
    );
    setMessage(`Latest file: ${res.data.file_path} (exists=${res.data.exists ? "true" : "false"})`);
    window.open(`${getBaseUrl()}${res.data.download_url}`, "_blank");
  }

  async function onRevision(values: { page_index?: number; instruction: string }) {
    if (!task.activeTaskId) return;
    setError(null);
    try {
      const payload = {
        page_index: values.page_index ?? null,
        instruction: values.instruction,
      };
      const res = await postJson<ApiEnvelope<{ new_version: number; revised_pages?: number[] }>>(`/v1/tasks/${task.activeTaskId}/revisions`, payload);
      setMessage(`Revision done. New version: v${res.data.new_version}`);
      await loadVersions();
    } catch (e) {
      setError(String(e));
    }
  }

  async function onRollback(values: { target_version: number }) {
    if (!task.activeTaskId) return;
    setError(null);
    try {
      const res = await postJson<ApiEnvelope<{ new_version: number; source_version: number }>>(
        `/v1/tasks/${task.activeTaskId}/versions/rollback/${values.target_version}`,
        {}
      );
      setMessage(`Rollback done from v${res.data.source_version} to v${res.data.new_version}.`);
      await loadVersions();
    } catch (e) {
      setError(String(e));
    }
  }

  async function onCompare(values: { from_version: number; to_version: number }) {
    if (!task.activeTaskId) return;
    setError(null);
    try {
      const res = await getJson<ApiEnvelope<{ changed_page_count: number }>>(
        `/v1/tasks/${task.activeTaskId}/versions/compare?from_version=${values.from_version}&to_version=${values.to_version}`
      );
      setMessage(`Compare result: changed pages = ${res.data.changed_page_count}`);
    } catch (e) {
      setError(String(e));
    }
  }

  async function clearTaskCache() {
    if (!task.activeTaskId) return;
    setError(null);
    try {
      const res = await postJson<ApiEnvelope<{ removed: boolean; removed_files: number }>>(
        `/v1/tasks/${task.activeTaskId}/cache/clear`,
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
      <Typography.Paragraph>Task: {task.activeTaskId ?? "none"}</Typography.Paragraph>
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
              onClick={() => window.open(`${getBaseUrl()}/v1/tasks/${task.activeTaskId}/download/${v.version}/file`, "_blank")}
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
