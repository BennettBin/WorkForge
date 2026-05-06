import { Button, Layout, Menu, Space, Typography } from "antd";
import { Link, Navigate, Route, Routes, useLocation } from "react-router-dom";
import HomePage from "./pages/Home/HomePage";
import TaskCreatePage from "./pages/TaskCreate/TaskCreatePage";
import TaskRunningPage from "./pages/TaskRunning/TaskRunningPage";
import ResultPreviewPage from "./pages/ResultPreview/ResultPreviewPage";
import ModelSettingsPage from "./pages/ModelSettings/ModelSettingsPage";
import HistoryPage from "./pages/History/HistoryPage";
import AuthPage from "./pages/Auth/AuthPage";
import { useAppStore } from "./store/appStore";

const { Header, Content } = Layout;

const navItems = [
  { key: "/", label: <Link to="/">Home</Link> },
  { key: "/tasks/create", label: <Link to="/tasks/create">Task Create</Link> },
  { key: "/tasks/running", label: <Link to="/tasks/running">Task Running</Link> },
  { key: "/result", label: <Link to="/result">Result</Link> },
  { key: "/models", label: <Link to="/models">Model Settings</Link> },
  { key: "/history", label: <Link to="/history">History</Link> }
];

export default function App() {
  const location = useLocation();
  const { auth, setAuth } = useAppStore();

  function logout() {
    localStorage.removeItem("wf_token");
    localStorage.removeItem("wf_user_id");
    localStorage.removeItem("wf_username");
    localStorage.removeItem("wf_email");
    setAuth({ userId: null, username: null, email: null, token: null });
  }

  if (!auth.token) {
    return (
      <Layout style={{ minHeight: "100vh" }}>
        <Header>
          <Typography.Text style={{ color: "#fff", fontSize: 16 }}>WorkForge</Typography.Text>
        </Header>
        <Content style={{ padding: 16 }}>
          <Routes>
            <Route path="/Login" element={<AuthPage />} />
            <Route path="*" element={<Navigate to="/Login" replace />} />
          </Routes>
        </Content>
      </Layout>
    );
  }

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Header>
        <Space style={{ width: "100%", justifyContent: "space-between" }}>
          <Menu theme="dark" mode="horizontal" selectedKeys={[location.pathname]} items={navItems} style={{ flex: 1 }} />
          <Button onClick={logout}>Logout</Button>
        </Space>
      </Header>
      <Content style={{ padding: 16 }}>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/tasks/create" element={<TaskCreatePage />} />
          <Route path="/tasks/running" element={<TaskRunningPage />} />
          <Route path="/result" element={<ResultPreviewPage />} />
          <Route path="/models" element={<ModelSettingsPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/Login" element={<Navigate to="/" replace />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Content>
    </Layout>
  );
}
