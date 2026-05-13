import { Button, FloatButton, Layout, Menu, Space, Typography } from "antd";
import { AppstoreAddOutlined, BulbOutlined, FileAddOutlined, FileSearchOutlined, ToolOutlined } from "@ant-design/icons";
import { Link, Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import HomePage from "./pages/Home/HomePage";
import TaskCreatePage from "./pages/TaskCreate/TaskCreatePage";
import TaskRunningPage from "./pages/TaskRunning/TaskRunningPage";
import ResultPreviewPage from "./pages/ResultPreview/ResultPreviewPage";
import ModelSettingsPage from "./pages/ModelSettings/ModelSettingsPage";
import HistoryPage from "./pages/History/HistoryPage";
import AuthPage from "./pages/Auth/AuthPage";
import RegisterPage from "./pages/Auth/RegisterPage";
import CapabilitySetupPage from "./pages/CapabilitySetup/CapabilitySetupPage";
import TemplateGenerationPage from "./pages/TemplateGeneration/TemplateGenerationPage";
import TemplateGenerationSettingsPage from "./pages/TemplateGeneration/TemplateGenerationSettingsPage";
import TemplateGenerationRecoveryPage from "./pages/TemplateGeneration/TemplateGenerationRecoveryPage";
import TemplatePreviewPage from "./pages/TemplatePreview/TemplatePreviewPage";
import { useAppStore } from "./store/appStore";
import RunningTasksFloatingPanel from "./components/RunningTasksFloatingPanel";

const { Header, Content } = Layout;

const navItems = [
  { key: "/", label: <Link to="/">Home</Link> },
  { key: "/tasks/create", label: <Link to="/tasks/create">Task Create</Link> },
  { key: "/models", label: <Link to="/models">Model Settings</Link> },
  { key: "/history", label: <Link to="/history">History</Link> }
];

export default function App() {
  const location = useLocation();
  const navigate = useNavigate();
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
            <Route path="/Register" element={<RegisterPage />} />
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
          <Route path="/tasks/running/:taskId" element={<TaskRunningPage />} />
          <Route path="/result" element={<ResultPreviewPage />} />
          <Route path="/models" element={<ModelSettingsPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/capabilities/setup" element={<CapabilitySetupPage />} />
          <Route path="/template-generation" element={<TemplateGenerationPage />} />
          <Route path="/template-generation/settings" element={<TemplateGenerationSettingsPage />} />
          <Route path="/template-generation/recovery" element={<TemplateGenerationRecoveryPage />} />
          <Route path="/template-preview" element={<TemplatePreviewPage />} />
          <Route path="/Login" element={<Navigate to="/" replace />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Content>
      <RunningTasksFloatingPanel />
      <FloatButton.Group
        shape="circle"
        trigger="click"
        icon={<AppstoreAddOutlined />}
        tooltip={<div>辅助功能</div>}
        style={{ right: 24, bottom: 24, zIndex: 2000 }}
      >
        <FloatButton
          icon={<FileAddOutlined />}
          tooltip={<div>模板生成</div>}
          onClick={() => navigate("/template-generation")}
        />
        <FloatButton
          icon={<FileSearchOutlined />}
          tooltip={<div>知识助手</div>}
          onClick={() => navigate("/tasks/create?aux=knowledge_assistant")}
        />
        <FloatButton
          icon={<ToolOutlined />}
          tooltip={<div>格式转换</div>}
          onClick={() => navigate("/tasks/create?aux=format_conversion")}
        />
        <FloatButton
          icon={<BulbOutlined />}
          tooltip={<div>灵感草案</div>}
          onClick={() => navigate("/tasks/create?aux=idea_draft")}
        />
        <FloatButton
          icon={<AppstoreAddOutlined />}
          tooltip={<div>自定义能力</div>}
          onClick={() => navigate("/capabilities/setup")}
        />
      </FloatButton.Group>
    </Layout>
  );
}
