import { Alert, Button, Card, Form, Input, Space, Typography } from "antd";
import { useState } from "react";
import { Link } from "react-router-dom";
import { postJson } from "../../api/http";
import { useAppStore } from "../../store/appStore";
import { ApiEnvelope } from "../../types/api";

type AuthResult = { token: string; user_id: string; username: string; email: string };

export default function AuthPage() {
  const { setAuth } = useAppStore();
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function onLogin(values: { account: string; password: string }) {
    setError(null);
    setMessage(null);
    try {
      const res = await postJson<ApiEnvelope<AuthResult>>("/v1/auth/login", values);
      const d = res.data;
      localStorage.setItem("wf_token", d.token);
      localStorage.setItem("wf_user_id", d.user_id);
      localStorage.setItem("wf_username", d.username);
      localStorage.setItem("wf_email", d.email);
      setAuth({ userId: d.user_id, username: d.username, email: d.email, token: d.token });
      setMessage("Login success.");
    } catch (e) {
      setError(String(e));
    }
  }

  return (
    <Card>
      <Typography.Title level={4}>Login</Typography.Title>
      <Space direction="vertical" style={{ width: "100%" }}>
        {message && <Alert type="success" message={message} />}
        {error && <Alert type="error" message={error} />}
        <Alert type="info" message="Default admin: account admin / password 123456" />
      </Space>
      <Form layout="vertical" onFinish={onLogin} initialValues={{ account: "admin", password: "123456" }}>
        <Form.Item label="Username" name="account" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item label="Password" name="password" rules={[{ required: true }]}>
          <Input.Password />
        </Form.Item>
        <Space>
          <Button htmlType="submit" type="primary">
            Login
          </Button>
          <Button>
            <Link to="/Register">Create Account</Link>
          </Button>
        </Space>
      </Form>
    </Card>
  );
}
