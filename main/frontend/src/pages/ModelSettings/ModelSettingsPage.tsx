import { QuestionCircleOutlined } from "@ant-design/icons";
import { Alert, Button, Card, Checkbox, Form, Input, InputNumber, List, Select, Space, Tooltip, Typography } from "antd";
import { useEffect, useMemo, useState } from "react";
import { getJson, postJson, putJson } from "../../api/http";
import { useAppStore } from "../../store/appStore";
import { ApiEnvelope } from "../../types/api";

type ProviderType =
  | "deepseek_api"
  | "openai_api"
  | "anthropic_api"
  | "qwen_api"
  | "vllm"
  | "ollama"
  | "huggingface"
  | "local_llm";

type ProviderItem = {
  provider_id: string;
  provider_type: string;
  display_name: string;
  base_url?: string;
  model_name: string;
  chat_model?: string;
  embedding_model?: string;
  has_api_key?: boolean;
  is_default: boolean;
};

type ProviderDefaultResponse = {
  item: ProviderItem | null;
};

type ProviderTestResult = {
  status: string;
  message: string;
  error_code?: string;
  reachable?: boolean;
  model_found?: boolean;
};

type ProviderConfigPreset = {
  label: string;
  providerType: ProviderType;
  baseUrlExample: string;
  modelExample: string;
  modelOptions?: string[];
  needsApiKey: boolean;
  needsChatModel: boolean;
  needsEmbeddingModel: boolean;
  defaultValues: {
    display_name: string;
    base_url: string;
    model_name: string;
    chat_model?: string;
    embedding_model?: string;
  };
};

const OLLAMA_DEFAULT = {
  chat_model: "qwen3:8b",
  embedding_model: "qwen3-embedding:8b",
  base_url: "http://localhost:11434",
};

const VLLM_DEFAULT = {
  model_name: "D:\\pycharm\\LLMs\\Qwen3.5-9B-Base",
  base_url: "http://127.0.0.1:8000/v1",
};

const PROVIDER_PRESETS: Record<ProviderType, ProviderConfigPreset> = {
  deepseek_api: {
    label: "Deepseek API",
    providerType: "deepseek_api",
    baseUrlExample: "https://api.deepseek.com",
    modelExample: "deepseek-v4-flash",
    modelOptions: ["deepseek-v4-flash", "deepseek-v4-pro", "deepseek-chat", "deepseek-reasoner"],
    needsApiKey: true,
    needsChatModel: false,
    needsEmbeddingModel: false,
    defaultValues: { display_name: "Deepseek API", base_url: "https://api.deepseek.com", model_name: "deepseek-v4-flash" },
  },
  openai_api: {
    label: "OpenAI API",
    providerType: "openai_api",
    baseUrlExample: "https://api.openai.com/v1",
    modelExample: "gpt-4.1-mini",
    modelOptions: ["gpt-4.1-mini", "gpt-4.1", "gpt-4o-mini", "gpt-4o"],
    needsApiKey: true,
    needsChatModel: false,
    needsEmbeddingModel: false,
    defaultValues: { display_name: "OpenAI API", base_url: "https://api.openai.com/v1", model_name: "gpt-4.1-mini" },
  },
  anthropic_api: {
    label: "Anthropic API",
    providerType: "anthropic_api",
    baseUrlExample: "https://api.anthropic.com/v1",
    modelExample: "claude-3-7-sonnet-latest",
    modelOptions: ["claude-3-7-sonnet-latest", "claude-3-5-sonnet-latest", "claude-3-5-haiku-latest"],
    needsApiKey: true,
    needsChatModel: false,
    needsEmbeddingModel: false,
    defaultValues: {
      display_name: "Anthropic API",
      base_url: "https://api.anthropic.com/v1",
      model_name: "claude-3-7-sonnet-latest",
    },
  },
  qwen_api: {
    label: "Qwen API",
    providerType: "qwen_api",
    baseUrlExample: "https://dashscope.aliyuncs.com/compatible-mode/v1",
    modelExample: "qwen-plus",
    modelOptions: ["qwen-plus", "qwen-max", "qwen-turbo", "qwen-long"],
    needsApiKey: true,
    needsChatModel: false,
    needsEmbeddingModel: false,
    defaultValues: {
      display_name: "Qwen API",
      base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1",
      model_name: "qwen-plus",
    },
  },
  vllm: {
    label: "vLLM",
    providerType: "vllm",
    baseUrlExample: VLLM_DEFAULT.base_url,
    modelExample: VLLM_DEFAULT.model_name,
    needsApiKey: false,
    needsChatModel: false,
    needsEmbeddingModel: false,
    defaultValues: {
      display_name: "vLLM Local",
      base_url: VLLM_DEFAULT.base_url,
      model_name: VLLM_DEFAULT.model_name,
    },
  },
  ollama: {
    label: "Ollama",
    providerType: "ollama",
    baseUrlExample: "http://localhost:11434",
    modelExample: "qwen3:8b",
    needsApiKey: false,
    needsChatModel: true,
    needsEmbeddingModel: true,
    defaultValues: {
      display_name: "Ollama Local",
      base_url: OLLAMA_DEFAULT.base_url,
      model_name: OLLAMA_DEFAULT.chat_model,
      chat_model: OLLAMA_DEFAULT.chat_model,
      embedding_model: OLLAMA_DEFAULT.embedding_model,
    },
  },
  huggingface: {
    label: "HuggingFace(vLLM)",
    providerType: "huggingface",
    baseUrlExample: "http://127.0.0.1:8000/v1",
    modelExample: "meta-llama/Meta-Llama-3.1-8B-Instruct",
    needsApiKey: false,
    needsChatModel: false,
    needsEmbeddingModel: false,
    defaultValues: {
      display_name: "HuggingFace via vLLM",
      base_url: "http://127.0.0.1:8000/v1",
      model_name: "meta-llama/Meta-Llama-3.1-8B-Instruct",
    },
  },
  local_llm: {
    label: "Local LLM",
    providerType: "local_llm",
    baseUrlExample: "http://127.0.0.1:8001/v1",
    modelExample: "qwen3:8b",
    needsApiKey: false,
    needsChatModel: false,
    needsEmbeddingModel: false,
    defaultValues: {
      display_name: "Local LLM",
      base_url: "http://127.0.0.1:8001/v1",
      model_name: "qwen3:8b",
    },
  },
};

function requiredLabel(label: string, tooltip: string) {
  return (
    <span>
      {label}{" "}
      <Tooltip title={tooltip}>
        <QuestionCircleOutlined />
      </Tooltip>
    </span>
  );
}

export default function ModelSettingsPage() {
  const { auth } = useAppStore();
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [providers, setProviders] = useState<ProviderItem[]>([]);
  const [currentProviderId, setCurrentProviderId] = useState<string | null>(null);
  const [currentProviderHasApiKey, setCurrentProviderHasApiKey] = useState<boolean>(false);
  const [maxParallelTasks, setMaxParallelTasks] = useState<number>(10);
  const [testResult, setTestResult] = useState<ProviderTestResult | null>(null);
  const [form] = Form.useForm();

  const providerType: ProviderType = Form.useWatch("provider_type", form) ?? "vllm";
  const preset = useMemo(() => PROVIDER_PRESETS[providerType] ?? PROVIDER_PRESETS.vllm, [providerType]);

  async function save(values: {
    provider_type: ProviderType;
    display_name: string;
    base_url: string;
    model_name?: string;
    chat_model?: string;
    embedding_model?: string;
    api_key?: string;
    is_default?: boolean;
  }) {
    if (!auth.userId) {
      setError("Please login first.");
      return;
    }
    setError(null);
    await postJson<ApiEnvelope<ProviderItem>>("/v1/providers", {
      provider_id: currentProviderId,
      user_id: auth.userId,
      provider_type: values.provider_type,
      display_name: values.display_name,
      base_url: values.base_url || null,
      model_name: values.model_name || values.chat_model || null,
      chat_model: values.chat_model || null,
      embedding_model: values.provider_type === "ollama" ? values.embedding_model || null : null,
      api_key: values.api_key || null,
      is_default: !!values.is_default,
    });
    await loadDefaultProvider(true);
    await loadProviders();
  }

  async function loadProviders() {
    if (!auth.userId) {
      return;
    }
    const res = await getJson<ApiEnvelope<{ items: ProviderItem[] }>>(`/v1/providers/${auth.userId}`);
    setProviders(res.data.items);
  }

  async function loadDefaultProvider(showMessage = false) {
    if (!auth.userId) {
      return;
    }
    setError(null);
    const res = await getJson<ApiEnvelope<ProviderDefaultResponse>>("/v1/providers/default/me");
    const item = res.data.item;
    if (!item) {
      setCurrentProviderId(null);
      setCurrentProviderHasApiKey(false);
      form.setFieldsValue({
        provider_type: "vllm",
        ...PROVIDER_PRESETS.vllm.defaultValues,
        api_key: null,
        is_default: true,
      });
      if (showMessage) {
        setMessage("Saved. No user default provider found; using vLLM preset.");
      }
      return;
    }
    setCurrentProviderId(item.provider_id);
    setCurrentProviderHasApiKey(!!item.has_api_key);
    form.setFieldsValue({
      provider_type: item.provider_type,
      display_name: item.display_name,
      base_url: item.base_url ?? "",
      model_name: item.model_name,
      chat_model: item.chat_model ?? null,
      embedding_model: item.embedding_model ?? null,
      api_key: null,
      is_default: item.is_default,
    });
    if (showMessage) {
      setMessage(`Saved provider ${item.display_name}`);
    }
  }

  async function loadUserSettings() {
    try {
      const res = await getJson<ApiEnvelope<{ max_parallel_tasks: number }>>("/v1/users/settings/me");
      setMaxParallelTasks(Math.max(1, Math.min(10, Number(res.data.max_parallel_tasks || 10))));
    } catch (e) {
      const msg = String(e);
      if (msg.includes("HTTP 404")) {
        setMaxParallelTasks(10);
        return;
      }
      throw e;
    }
  }

  async function saveUserSettings() {
    setError(null);
    const res = await putJson<ApiEnvelope<{ max_parallel_tasks: number }>>("/v1/users/settings/me", {
      max_parallel_tasks: maxParallelTasks,
    });
    setMaxParallelTasks(Number(res.data.max_parallel_tasks || 10));
    setMessage(`Saved max parallel tasks = ${res.data.max_parallel_tasks}`);
  }

  useEffect(() => {
    loadDefaultProvider().catch((e) => setError(String(e)));
    loadProviders().catch((e) => setError(String(e)));
    loadUserSettings().catch((e) => setError(String(e)));
  }, [auth.userId]); // eslint-disable-line react-hooks/exhaustive-deps

  async function testCurrentConfig() {
    const values = await form.validateFields();
    const res = await postJson<ApiEnvelope<{ status: string; message: string; error_code?: string; reachable?: boolean; model_found?: boolean }>>("/v1/providers/test", {
      provider_type: values.provider_type,
      base_url: values.base_url || null,
      api_key: values.api_key || null,
      model_name: values.model_name || values.chat_model || null,
      chat_model: values.chat_model || null,
    });
    setTestResult(res.data);
    const extra = [
      res.data.error_code ? `error_code=${res.data.error_code}` : "",
      typeof res.data.reachable === "boolean" ? `reachable=${String(res.data.reachable)}` : "",
      typeof res.data.model_found === "boolean" ? `model_found=${String(res.data.model_found)}` : "",
    ].filter(Boolean).join(", ");
    setMessage(`Test ${res.data.status}: ${res.data.message}${extra ? ` (${extra})` : ""}`);
  }

  return (
    <Card>
      <Typography.Title level={4}>Model Settings</Typography.Title>

      <Space direction="vertical" style={{ width: "100%" }}>
        {message && <Alert type="success" message={message} />}
        {error && <Alert type="error" message={error} />}
        {testResult && (
          <Alert
            type={testResult.status === "ok" ? "success" : "warning"}
            showIcon
            message={`Connection Test: ${testResult.status}`}
            description={
              <div>
                <div>{testResult.message}</div>
                <div>
                  {typeof testResult.reachable === "boolean" ? `reachable=${String(testResult.reachable)} ` : ""}
                  {typeof testResult.model_found === "boolean" ? `model_found=${String(testResult.model_found)} ` : ""}
                  {testResult.error_code ? `error_code=${testResult.error_code}` : ""}
                </div>
              </div>
            }
          />
        )}
        {testResult?.error_code === "CONNECTION_REFUSED" && (
          <Alert
            type="warning"
            showIcon
            message="vLLM Connection Refused"
            description="请检查 vLLM 进程是否已启动；确认 host/port 与 Base URL 一致；确认防火墙已放行该端口。"
          />
        )}
      </Space>

      <Form
        form={form}
        layout="vertical"
        onFinish={save}
        initialValues={{
          provider_type: "vllm",
          ...PROVIDER_PRESETS.vllm.defaultValues,
          is_default: true,
        }}
        onValuesChange={(changed) => {
          if (changed.provider_type) {
            const changedType = changed.provider_type as ProviderType;
            const changedPreset = PROVIDER_PRESETS[changedType];
            form.setFieldsValue({
              display_name: changedPreset.defaultValues.display_name,
              base_url: changedPreset.defaultValues.base_url,
              model_name: changedPreset.defaultValues.model_name,
              chat_model: changedPreset.defaultValues.chat_model || null,
              embedding_model: changedPreset.defaultValues.embedding_model || null,
              api_key: null,
            });
            setCurrentProviderHasApiKey(false);
          }
        }}
      >
        <Form.Item label="Provider" name="provider_type" initialValue="vllm">
          <Select options={Object.values(PROVIDER_PRESETS).map((x) => ({ label: x.label, value: x.providerType }))} />
        </Form.Item>
        <Form.Item
          label={requiredLabel("Display Name", "Required. Example: Deepseek API / Ollama Local")}
          name="display_name"
          rules={[{ required: true, message: "Display Name is required." }]}
        >
          <Input placeholder={preset.defaultValues.display_name} />
        </Form.Item>
        <Form.Item
          label={requiredLabel("Base URL", `Required. Example: ${preset.baseUrlExample}`)}
          name="base_url"
          rules={[{ required: true, message: "Base URL is required." }]}
        >
          <Input placeholder={preset.baseUrlExample} />
        </Form.Item>
        {providerType === "vllm" && (
          <Alert
            type="info"
            showIcon
            message="vLLM"
            description="Base URL must be like http://<host>:<port>/v1. Model Name should match one id returned by /models (or your served-model-name)."
          />
        )}
        {preset.needsChatModel ? (
          <>
            <Form.Item
              label={requiredLabel("Chat Model", "Required. Example: qwen3:8b")}
              name="chat_model"
              rules={[{ required: true, message: "Chat Model is required." }]}
            >
              <Input placeholder={OLLAMA_DEFAULT.chat_model} />
            </Form.Item>
            <Form.Item
              label={requiredLabel("Embedding Model", "Required. Example: qwen3-embedding:8b")}
              name="embedding_model"
              rules={[{ required: true, message: "Embedding Model is required." }]}
            >
              <Input placeholder={OLLAMA_DEFAULT.embedding_model} />
            </Form.Item>
          </>
        ) : (
          <Form.Item
            label={requiredLabel("Model Name", `Required. Example: ${preset.modelExample}`)}
            name="model_name"
            rules={[{ required: true, message: "Model Name is required." }]}
          >
            {preset.modelOptions ? (
              <Select
                showSearch
                placeholder={preset.modelExample}
                options={preset.modelOptions.map((item) => ({ label: item, value: item }))}
              />
            ) : (
              <Input placeholder={preset.modelExample} />
            )}
          </Form.Item>
        )}
        {preset.needsApiKey && (
          <Form.Item
            label={requiredLabel("API Key", "Required. Example: sk-xxxx / hf_xxxx")}
            name="api_key"
            rules={[
              {
                validator: (_, value) => {
                  const hasValue = Boolean(String(value || "").trim());
                  if (hasValue || currentProviderHasApiKey) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error("API Key is required."));
                },
              },
            ]}
            extra={currentProviderHasApiKey ? "API Key already saved for this provider. Leave blank to keep current key." : undefined}
          >
            <Input.Password placeholder={currentProviderHasApiKey ? "Leave empty to keep saved key" : "Enter API Key"} />
          </Form.Item>
        )}
        <Form.Item name="is_default" valuePropName="checked">
          <Checkbox>Default</Checkbox>
        </Form.Item>
        <Space>
          <Button htmlType="submit" type="primary">
            Save
          </Button>
          <Button onClick={() => testCurrentConfig().catch((e) => setError(String(e)))}>Test Current Config</Button>
          <Button onClick={() => loadDefaultProvider().catch((e) => setError(String(e)))}>Load Default</Button>
          <Button onClick={loadProviders}>Load Providers</Button>
        </Space>
      </Form>

      <Typography.Title level={5}>Saved Providers</Typography.Title>
      <List
        dataSource={providers}
        renderItem={(p) => (
          <List.Item>
            {p.display_name} ({p.provider_type}/{p.chat_model || p.model_name})
            {p.embedding_model ? ` | embedding: ${p.embedding_model}` : ""} {p.is_default ? "[default]" : ""}
          </List.Item>
        )}
      />

      <Typography.Title level={5} style={{ marginTop: 20 }}>Task Concurrency</Typography.Title>
      <Space>
        <Typography.Text>Max Parallel Tasks</Typography.Text>
        <InputNumber min={1} max={10} value={maxParallelTasks} onChange={(v) => setMaxParallelTasks(Number(v || 1))} />
        <Button type="primary" onClick={() => saveUserSettings().catch((e) => setError(String(e)))}>
          Save Limit
        </Button>
      </Space>
    </Card>
  );
}
