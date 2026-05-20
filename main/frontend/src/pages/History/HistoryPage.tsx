import { Button, Card, Modal, Popconfirm, Space, Table, Tag, Typography, message } from "antd";
import type { ColumnsType } from "antd/es/table";
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { deleteJson, downloadFile, getJson } from "../../api/http";
import { useAppStore } from "../../store/appStore";
import { ApiEnvelope } from "../../types/api";

type OutputVersion = {
  output_id: string;
  task_id: string;
  version: number;
  file_type: string;
  file_path: string;
  created_at: string;
};

type TaskItem = {
  task_id: string;
  task_type: string;
  user_requirement: string;
  status: string;
  created_at: string;
  updated_at?: string;
  versions?: OutputVersion[];
};

function taskTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    ppt: "PPT",
    report: "Report",
    wechat_post: "WeChat Post",
    data_analysis: "Data Analysis",
    code_doc: "Code Doc",
    paper_assistant: "Paper Assistant",
    generic_task: "Generic Task",
    template_generation: "Template Generation",
  };
  return labels[type] || type;
}

function fileNameForVersion(task: TaskItem, version: OutputVersion): string {
  const suffix = version.file_type ? `.${version.file_type}` : "";
  return `${task.task_type || "task"}-${task.task_id}-v${version.version}${suffix}`;
}

export default function HistoryPage() {
  const navigate = useNavigate();
  const { auth, setTask, upsertRunningTask, setSelectedRunningTaskId } = useAppStore();
  const [items, setItems] = useState<TaskItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [promptTask, setPromptTask] = useState<TaskItem | null>(null);
  const [api, contextHolder] = message.useMessage();

  async function load() {
    if (!auth.userId) {
      return;
    }
    setLoading(true);
    try {
      const res = await getJson<ApiEnvelope<{ items: TaskItem[] }>>(`/v1/tasks/user/${auth.userId}`);
      const sorted = [...res.data.items].sort((a, b) => String(b.updated_at || b.created_at).localeCompare(String(a.updated_at || a.created_at)));
      const withVersions = await Promise.all(
        sorted.map(async (task) => {
          try {
            const versions = await getJson<ApiEnvelope<{ items: OutputVersion[] }>>(`/v1/tasks/${task.task_id}/versions`);
            return { ...task, versions: versions.data.items };
          } catch {
            return { ...task, versions: [] };
          }
        }),
      );
      setItems(withVersions);
    } finally {
      setLoading(false);
    }
  }

  async function deleteTask(taskId: string) {
    await deleteJson<ApiEnvelope<{ task_id: string }>>(`/v1/tasks/${taskId}`);
    setItems((prev) => prev.filter((item) => item.task_id !== taskId));
    api.success("Deleted.");
  }

  async function copyPrompt(text: string) {
    await navigator.clipboard.writeText(text);
    api.success("Copied.");
  }

  useEffect(() => {
    load().catch((e) => api.error(String(e)));
  }, [auth.userId]); // eslint-disable-line react-hooks/exhaustive-deps

  const columns: ColumnsType<TaskItem> = useMemo(
    () => [
      {
        title: "Task ID",
        dataIndex: "task_id",
        key: "task_id",
        width: 210,
        ellipsis: true,
      },
      {
        title: "Task Type",
        dataIndex: "task_type",
        key: "task_type",
        width: 150,
        render: (value: string) => <Tag color="blue">{taskTypeLabel(value)}</Tag>,
      },
      {
        title: "Status",
        dataIndex: "status",
        key: "status",
        width: 150,
        render: (value: string) => <Tag>{value}</Tag>,
      },
      {
        title: "Original Prompt",
        dataIndex: "user_requirement",
        key: "user_requirement",
        ellipsis: true,
        render: (value: string, task) => (
          <Button type="link" onClick={() => setPromptTask(task)}>
            {value ? value.slice(0, 64) : "View prompt"}
            {value && value.length > 64 ? "..." : ""}
          </Button>
        ),
      },
      {
        title: "Updated",
        dataIndex: "updated_at",
        key: "updated_at",
        width: 190,
        render: (_: string, task) => new Date(task.updated_at || task.created_at).toLocaleString(),
      },
      {
        title: "Actions",
        key: "actions",
        width: 250,
        render: (_: unknown, task) => (
          <Space>
            <Button
              onClick={() => {
                setTask((prev) => ({ ...prev, activeTaskId: task.task_id, activeTaskStatus: task.status }));
                upsertRunningTask({ taskId: task.task_id, status: task.status, title: task.task_id });
                setSelectedRunningTaskId(task.task_id);
                navigate(`/result?taskId=${encodeURIComponent(task.task_id)}`);
              }}
            >
              Use
            </Button>
            <Button
              disabled={!task.versions?.length}
              onClick={() => {
                const latest = [...(task.versions || [])].sort((a, b) => b.version - a.version)[0];
                if (latest) {
                  downloadFile(`/v1/tasks/${task.task_id}/download/${latest.version}/file`, fileNameForVersion(task, latest)).catch((e) =>
                    api.error(String(e)),
                  );
                }
              }}
            >
              Download
            </Button>
            <Popconfirm
              title="Delete this task history?"
              description="This removes the task record, generated versions, and stored files."
              okText="Delete"
              okButtonProps={{ danger: true }}
              onConfirm={() => deleteTask(task.task_id).catch((e) => api.error(String(e)))}
            >
              <Button danger>Delete</Button>
            </Popconfirm>
          </Space>
        ),
      },
    ],
    [api, navigate, setSelectedRunningTaskId, setTask, upsertRunningTask],
  );

  return (
    <Card>
      {contextHolder}
      <Space direction="vertical" style={{ width: "100%" }} size="middle">
        <Space style={{ width: "100%", justifyContent: "space-between" }}>
          <Typography.Title level={4} style={{ margin: 0 }}>
            History
          </Typography.Title>
          <Button onClick={() => load().catch((e) => api.error(String(e)))} loading={loading}>
            Refresh
          </Button>
        </Space>
        <Table
          rowKey="task_id"
          loading={loading}
          dataSource={items}
          columns={columns}
          pagination={{ pageSize: 8 }}
          expandable={{
            expandedRowRender: (task) => (
              <Table
                rowKey="output_id"
                size="small"
                pagination={false}
                dataSource={task.versions || []}
                locale={{ emptyText: "No generated versions." }}
                columns={[
                  { title: "Version", dataIndex: "version", width: 100, render: (value: number) => <Tag>v{value}</Tag> },
                  { title: "File Type", dataIndex: "file_type", width: 120 },
                  { title: "Created", dataIndex: "created_at", render: (value: string) => new Date(value).toLocaleString() },
                  {
                    title: "Actions",
                    width: 140,
                    render: (_: unknown, version: OutputVersion) => (
                      <Button onClick={() => downloadFile(`/v1/tasks/${task.task_id}/download/${version.version}/file`, fileNameForVersion(task, version)).catch((e) => api.error(String(e)))}>
                        Download v{version.version}
                      </Button>
                    ),
                  },
                ]}
              />
            ),
          }}
        />
      </Space>
      <Modal
        open={!!promptTask}
        title="Original Prompt"
        onCancel={() => setPromptTask(null)}
        footer={[
          <Button key="copy" type="primary" onClick={() => promptTask && copyPrompt(promptTask.user_requirement).catch((e) => api.error(String(e)))}>
            Copy
          </Button>,
          <Button key="close" onClick={() => setPromptTask(null)}>
            Close
          </Button>,
        ]}
      >
        <Typography.Paragraph style={{ whiteSpace: "pre-wrap", maxHeight: 360, overflow: "auto" }}>
          {promptTask?.user_requirement}
        </Typography.Paragraph>
      </Modal>
    </Card>
  );
}
