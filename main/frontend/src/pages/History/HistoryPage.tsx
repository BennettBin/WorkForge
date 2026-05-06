import { Button, Card, List, Tag, Typography } from "antd";
import { useState } from "react";
import { getJson } from "../../api/http";
import { useAppStore } from "../../store/appStore";
import { ApiEnvelope } from "../../types/api";

type TaskItem = {
  task_id: string;
  status: string;
  created_at: string;
};

export default function HistoryPage() {
  const { auth, setTask } = useAppStore();
  const [items, setItems] = useState<TaskItem[]>([]);

  async function load() {
    if (!auth.userId) {
      return;
    }
    const res = await getJson<ApiEnvelope<{ items: TaskItem[] }>>(`/v1/tasks/user/${auth.userId}`);
    setItems(res.data.items);
  }

  return (
    <Card>
      <Typography.Title level={4}>History</Typography.Title>
      <Button onClick={load}>Load History</Button>
      <List
        dataSource={items}
        renderItem={(t) => (
          <List.Item
            actions={[
              <Button key="use" onClick={() => setTask({ activeTaskId: t.task_id, activeTaskStatus: t.status })}>
                Use
              </Button>
            ]}
          >
            <Tag>{t.status}</Tag>
            <span>{t.task_id}</span>
          </List.Item>
        )}
      />
    </Card>
  );
}
