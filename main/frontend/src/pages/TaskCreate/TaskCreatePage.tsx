import { Alert, Button, Card, Form, Input, InputNumber, Select, Space, Typography } from "antd";
import { useState } from "react";
import { postFile, postJson } from "../../api/http";
import { useAppStore } from "../../store/appStore";
import { ApiEnvelope } from "../../types/api";

type CreateTaskData = { task_id: string; status: string };

export default function TaskCreatePage() {
  const { auth, task, setTask } = useAppStore();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function onStart(values: { requirement: string; pages: number; style: string; language: string }) {
    setError(null);
    setMessage(null);
    if (!auth.userId) {
      setError("Please login first.");
      return;
    }
    const noSourceFile = !selectedFile;

    try {
      const createRes = await postJson<ApiEnvelope<CreateTaskData>>("/v1/tasks", {
        user_id: auth.userId,
        user_requirement: values.requirement,
        pages: values.pages,
        style: values.style,
        language: values.language
      });
      const taskId = createRes.data.task_id;
      setTask({ activeTaskId: taskId, activeTaskStatus: createRes.data.status });

      if (selectedFile) {
        await postFile(`/v1/tasks/${taskId}/upload`, selectedFile);
        await postJson(`/v1/tasks/${taskId}/parse`, { force: false });
      }
      const runRes = await postJson<ApiEnvelope<{ status: string; output_path: string }>>(`/v1/tasks/${taskId}/run`, { rerun: false });
      setTask({ activeTaskId: taskId, activeTaskStatus: runRes.data.status });
      if (noSourceFile) {
        setMessage(`未上传文件：系统已按“先检索并总结，再回答与制作PPT”模式执行。Output: ${runRes.data.output_path}`);
      } else {
        setMessage(`Task completed. Output: ${runRes.data.output_path}`);
      }
    } catch (e) {
      setError(String(e));
    }
  }

  return (
    <Card>
      <Typography.Title level={4}>Create Task</Typography.Title>
      <Typography.Paragraph>Active task: {task.activeTaskId ?? "none"}</Typography.Paragraph>
      <Space direction="vertical" style={{ width: "100%" }}>
        {message && <Alert type="success" message={message} />}
        {error && <Alert type="error" message={error} />}
      </Space>
      <Form layout="vertical" onFinish={onStart} initialValues={{ pages: 10, style: "academic_simple", language: "zh-CN" }}>
        <Form.Item label="Requirement" name="requirement" rules={[{ required: true }]}>
          <Input.TextArea rows={4} />
        </Form.Item>
        <Form.Item label="Pages" name="pages">
          <InputNumber min={5} max={30} />
        </Form.Item>
        <Form.Item label="Style" name="style">
          <Select
            options={[
              { label: "Academic Simple", value: "academic_simple" },
              { label: "Academic Report", value: "academic_report" },
            ]}
          />
        </Form.Item>
        <Form.Item label="Language" name="language">
          <Select options={[{ label: "Chinese", value: "zh-CN" }, { label: "English", value: "en-US" }]} />
        </Form.Item>
        <Form.Item label="Source File (Optional)">
          <input
            type="file"
            onChange={(e) => setSelectedFile(e.target.files && e.target.files[0] ? e.target.files[0] : null)}
          />
        </Form.Item>
        {!selectedFile && (
          <Alert
            type="info"
            showIcon
            message="未上传文件时，系统会先自行检索资料并总结，再进行回答与PPT制作。"
            style={{ marginBottom: 16 }}
          />
        )}
        <Button htmlType="submit" type="primary">
          Create + Run
        </Button>
      </Form>
    </Card>
  );
}
