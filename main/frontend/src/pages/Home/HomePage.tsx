import { Card, Space, Typography } from "antd";
import { useAppStore } from "../../store/appStore";

export default function HomePage() {
  const { auth, task } = useAppStore();
  return (
    <Card>
      <Typography.Title level={3}>WorkForge</Typography.Title>
      <Typography.Paragraph>User: {auth.username ?? "Not logged in"}</Typography.Paragraph>
      <Typography.Paragraph>Active Task: {task.activeTaskId ?? "none"}</Typography.Paragraph>
      <Typography.Paragraph>
        MVP-1 full loop: Auth {"->"} TaskCreate {"->"} TaskRunning {"->"} Result Preview.
      </Typography.Paragraph>
      <Space direction="vertical">
        <Typography.Text type="secondary">辅助功能悬浮按钮位于右下角</Typography.Text>
      </Space>
    </Card>
  );
}
