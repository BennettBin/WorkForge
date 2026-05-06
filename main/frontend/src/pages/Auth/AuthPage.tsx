import { Alert, Button, Card, Form, Input, Space, Tabs, Typography } from "antd";
import { useState } from "react";
import { postJson, putJson } from "../../api/http";
import { useAppStore } from "../../store/appStore";
import { ApiEnvelope } from "../../types/api";

type AuthResult = { token: string; user_id: string; username: string; email: string };

export default function AuthPage() {
  const { auth, setAuth } = useAppStore();
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function onRegister(values: { email: string; username: string; password: string }) {
    setError(null);
    setMessage(null);
    try {
      await postJson<ApiEnvelope<{ user_id: string }>>("/v1/auth/register", values);
      setMessage("Register success. Please login.");
    } catch (e) {
      setError(String(e));
    }
  }

  async function onLogin(values: { email: string; password: string }) {
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

  async function onProfile(values: { username: string }) {
    setError(null);
    setMessage(null);
    try {
      const res = await putJson<ApiEnvelope<{ user_id: string; username: string; email: string }>>("/v1/auth/profile", values);
      localStorage.setItem("wf_username", res.data.username);
      setAuth({ ...auth, username: res.data.username });
      setMessage("Profile updated.");
    } catch (e) {
      setError(String(e));
    }
  }

  async function onPassword(values: { old_password: string; new_password: string }) {
    setError(null);
    setMessage(null);
    try {
      await putJson<ApiEnvelope<{ updated: boolean }>>("/v1/auth/password", values);
      setMessage("Password updated.");
    } catch (e) {
      setError(String(e));
    }
  }

  return (
    <Card>
      <Typography.Title level={4}>Authentication</Typography.Title>
      <Space direction="vertical" style={{ width: "100%" }}>
        {message && <Alert type="success" message={message} />}
        {error && <Alert type="error" message={error} />}
        <Alert type="info" message="Default admin: account admin / password 123456" />
      </Space>
      <Tabs
        items={[
          {
            key: "login",
            label: "Login",
            children: (
              <Form layout="vertical" onFinish={onLogin} initialValues={{ email: "admin", password: "123456" }}>
                <Form.Item label="Account" name="email" rules={[{ required: true }]}>
                  <Input />
                </Form.Item>
                <Form.Item label="Password" name="password" rules={[{ required: true }]}>
                  <Input.Password />
                </Form.Item>
                <Button htmlType="submit" type="primary">
                  Login
                </Button>
              </Form>
            )
          },
          {
            key: "register",
            label: "Register",
            children: (
              <Form layout="vertical" onFinish={onRegister}>
                <Form.Item label="Email" name="email" rules={[{ required: true }]}>
                  <Input />
                </Form.Item>
                <Form.Item label="Username" name="username" rules={[{ required: true }]}>
                  <Input />
                </Form.Item>
                <Form.Item label="Password" name="password" rules={[{ required: true }]}>
                  <Input.Password />
                </Form.Item>
                <Button htmlType="submit" type="primary">
                  Register
                </Button>
              </Form>
            )
          },
          {
            key: "profile",
            label: "Profile",
            children: (
              <Form layout="vertical" onFinish={onProfile} initialValues={{ username: auth.username ?? "" }}>
                <Form.Item label="Username" name="username" rules={[{ required: true }]}>
                  <Input />
                </Form.Item>
                <Button htmlType="submit" type="primary" disabled={!auth.token}>
                  Update Profile
                </Button>
              </Form>
            )
          },
          {
            key: "password",
            label: "Password",
            children: (
              <Form layout="vertical" onFinish={onPassword}>
                <Form.Item label="Old Password" name="old_password" rules={[{ required: true }]}>
                  <Input.Password />
                </Form.Item>
                <Form.Item label="New Password" name="new_password" rules={[{ required: true }]}>
                  <Input.Password />
                </Form.Item>
                <Button htmlType="submit" type="primary" disabled={!auth.token}>
                  Update Password
                </Button>
              </Form>
            )
          }
        ]}
      />
    </Card>
  );
}
