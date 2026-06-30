import { QuestionCircleOutlined } from "@ant-design/icons";
import { Alert, Button, Card, Checkbox, Form, Input, InputNumber, List, Select, Space, Tooltip, Typography } from "antd";
import { useEffect, useMemo, useState } from "react";
import { getJson, postJson, putJson } from "../../api/http";
import { useAppStore } from "../../store/appStore";
import { ApiEnvelope } from "../../types/api";

type ChatProviderType =
  | "deepseek_api"
  | "openai_api"
  | "anthropic_api"
  | "qwen_api"
  | "vllm"
  | "ollama"
  | "huggingface"
  | "local_llm";

type EmbeddingProviderType = "ollama" | "local_embedding" | "huggingface";

type ProviderItem = {
  provider_id: string;
  provider_type: string;
  display_name: string;
  base_url?: string | null;
  model_name: string;
  chat_model?: string | null;
  has_api_key?: boolean;
  is_default: boolean;
};

type EmbeddingProviderItem = {
  provider_id: string;
  provider_type: EmbeddingProviderType;
  display_name: string;
  model_name?: string | null;
  base_url?: string | null;
  local_path?: string | null;
  cache_dir?: string | null;
  dimension?: number | null;
  is_default: boolean;
};

type ProviderTestResult = {
  status: string;
  message: string;
  error_code?: string;
  reachable?: boolean;
  model_found?: boolean;
  dimension?: number;
};

type ChatProviderPreset = {
  label: string;
  providerType: ChatProviderType;
  baseUrlExample: string;
  modelExample: string;
  modelOptions?: string[];
  needsApiKey: boolean;
  needsChatModel: boolean;
  defaultValues: {
    display_name: string;
    base_url: string;
    model_name: string;
    chat_model?: string;
  };
};

type EmbeddingProviderPreset = {
  label: string;
  providerType: EmbeddingProviderType;
  defaultValues: {
    display_name: string;
    model_name?: string;
    base_url?: string;
    local_path?: string;
    cache_dir?: string;
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

const CHAT_PROVIDER_PRESETS: Record<ChatProviderType, ChatProviderPreset> = {
  deepseek_api: {
    label: "Deepseek API",
    providerType: "deepseek_api",
    baseUrlExample: "https://api.deepseek.com",
    modelExample: "deepseek-v4-flash",
    modelOptions: ["deepseek-v4-flash", "deepseek-v4-pro", "deepseek-chat", "deepseek-reasoner"],
    needsApiKey: true,
    needsChatModel: false,
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
    defaultValues: { display_name: "Anthropic API", base_url: "https://api.anthropic.com/v1", model_name: "claude-3-7-sonnet-latest" },
  },
  qwen_api: {
    label: "Qwen API",
    providerType: "qwen_api",
    baseUrlExample: "https://dashscope.aliyuncs.com/compatible-mode/v1",
    modelExample: "qwen-plus",
    modelOptions: ["qwen-plus", "qwen-max", "qwen-turbo", "qwen-long"],
    needsApiKey: true,
    needsChatModel: false,
    defaultValues: { display_name: "Qwen API", base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1", model_name: "qwen-plus" },
  },
  vllm: {
    label: "vLLM",
    providerType: "vllm",
    baseUrlExample: VLLM_DEFAULT.base_url,
    modelExample: VLLM_DEFAULT.model_name,
    needsApiKey: false,
    needsChatModel: false,
    defaultValues: { display_name: "vLLM Local", base_url: VLLM_DEFAULT.base_url, model_name: VLLM_DEFAULT.model_name },
  },
  ollama: {
    label: "Ollama",
    providerType: "ollama",
    baseUrlExample: OLLAMA_DEFAULT.base_url,
    modelExample: OLLAMA_DEFAULT.chat_model,
    needsApiKey: false,
    needsChatModel: true,
    defaultValues: { display_name: "Ollama Local", base_url: OLLAMA_DEFAULT.base_url, model_name: OLLAMA_DEFAULT.chat_model, chat_model: OLLAMA_DEFAULT.chat_model },
  },
  huggingface: {
    label: "HuggingFace(vLLM)",
    providerType: "huggingface",
    baseUrlExample: "http://127.0.0.1:8000/v1",
    modelExample: "meta-llama/Meta-Llama-3.1-8B-Instruct",
    needsApiKey: false,
    needsChatModel: false,
    defaultValues: { display_name: "HuggingFace via vLLM", base_url: "http://127.0.0.1:8000/v1", model_name: "meta-llama/Meta-Llama-3.1-8B-Instruct" },
  },
  local_llm: {
    label: "Local LLM",
    providerType: "local_llm",
    baseUrlExample: "http://127.0.0.1:8001/v1",
    modelExample: "qwen3:8b",
    needsApiKey: false,
    needsChatModel: false,
    defaultValues: { display_name: "Local LLM", base_url: "http://127.0.0.1:8001/v1", model_name: "qwen3:8b" },
  },
};

const EMBEDDING_PROVIDER_PRESETS: Record<EmbeddingProviderType, EmbeddingProviderPreset> = {
  huggingface: {
    label: "HuggingFace",
    providerType: "huggingface",
    defaultValues: {
      display_name: "Qwen Embedding",
      model_name: "Qwen/Qwen3-Embedding-8B",
      cache_dir: "",
    },
  },
  ollama: {
    label: "Ollama",
    providerType: "ollama",
    defaultValues: {
      display_name: "Ollama Embedding",
      model_name: OLLAMA_DEFAULT.embedding_model,
      base_url: OLLAMA_DEFAULT.base_url,
    },
  },
  local_embedding: {
    label: "Local Folder",
    providerType: "local_embedding",
    defaultValues: {
      display_name: "Local Embedding",
      local_path: "",
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
  const [embeddingProviders, setEmbeddingProviders] = useState<EmbeddingProviderItem[]>([]);
  const [currentProviderId, setCurrentProviderId] = useState<string | null>(null);
  const [currentProviderHasApiKey, setCurrentProviderHasApiKey] = useState<boolean>(false);
  const [currentEmbeddingProviderId, setCurrentEmbeddingProviderId] = useState<string | null>(null);
  const [maxParallelTasks, setMaxParallelTasks] = useState<number>(10);
  const [chatTestResult, setChatTestResult] = useState<ProviderTestResult | null>(null);
  const [embeddingTestResult, setEmbeddingTestResult] = useState<ProviderTestResult | null>(null);
  const [chatForm] = Form.useForm();
  const [embeddingForm] = Form.useForm();

  const chatProviderType: ChatProviderType = Form.useWatch("provider_type", chatForm) ?? "vllm";
  const chatPreset = useMemo(() => CHAT_PROVIDER_PRESETS[chatProviderType] ?? CHAT_PROVIDER_PRESETS.vllm, [chatProviderType]);
  const embeddingProviderType: EmbeddingProviderType = Form.useWatch("provider_type", embeddingForm) ?? "huggingface";
  const embeddingPreset = useMemo(
    () => EMBEDDING_PROVIDER_PRESETS[embeddingProviderType] ?? EMBEDDING_PROVIDER_PRESETS.huggingface,
    [embeddingProviderType]
  );

  async function saveChatProvider(values: {
    provider_type: ChatProviderType;
    display_name: string;
    base_url: string;
    model_name?: string;
    chat_model?: string;
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
      embedding_model: null,
      api_key: values.api_key || null,
      is_default: !!values.is_default,
    });
    await loadDefaultProvider(true);
    await loadProviders();
  }

  async function saveEmbeddingProvider(values: {
    provider_type: EmbeddingProviderType;
    display_name: string;
    model_name?: string;
    base_url?: string;
    local_path?: string;
    cache_dir?: string;
    is_default?: boolean;
  }) {
    if (!auth.userId) {
      setError("Please login first.");
      return;
    }
    setError(null);
    await postJson<ApiEnvelope<EmbeddingProviderItem>>("/v1/embedding-providers", {
      provider_id: currentEmbeddingProviderId,
      user_id: auth.userId,
      provider_type: values.provider_type,
      display_name: values.display_name,
      model_name: values.model_name || null,
      base_url: values.base_url || null,
      local_path: values.local_path || null,
      cache_dir: values.cache_dir || null,
      is_default: !!values.is_default,
    });
    await loadDefaultEmbeddingProvider(true);
    await loadEmbeddingProviders();
  }

  async function loadProviders() {
    if (!auth.userId) return;
    const res = await getJson<ApiEnvelope<{ items: ProviderItem[] }>>(`/v1/providers/${auth.userId}`);
    setProviders(res.data.items);
  }

  async function loadEmbeddingProviders() {
    if (!auth.userId) return;
    const res = await getJson<ApiEnvelope<{ items: EmbeddingProviderItem[] }>>(`/v1/embedding-providers/${auth.userId}`);
    setEmbeddingProviders(res.data.items);
  }

  async function loadDefaultProvider(showMessage = false) {
    if (!auth.userId) return;
    setError(null);
    const res = await getJson<ApiEnvelope<{ item: ProviderItem | null }>>("/v1/providers/default/me");
    const item = res.data.item;
    if (!item) {
      setCurrentProviderId(null);
      setCurrentProviderHasApiKey(false);
      chatForm.setFieldsValue({ provider_type: "vllm", ...CHAT_PROVIDER_PRESETS.vllm.defaultValues, api_key: null, is_default: true });
      if (showMessage) setMessage("Saved. No user default chat provider found; using vLLM preset.");
      return;
    }
    setCurrentProviderId(item.provider_id);
    setCurrentProviderHasApiKey(!!item.has_api_key);
    chatForm.setFieldsValue({
      provider_type: item.provider_type,
      display_name: item.display_name,
      base_url: item.base_url ?? "",
      model_name: item.model_name,
      chat_model: item.chat_model ?? null,
      api_key: null,
      is_default: item.is_default,
    });
    if (showMessage) setMessage(`Saved chat provider ${item.display_name}`);
  }

  async function loadDefaultEmbeddingProvider(showMessage = false) {
    if (!auth.userId) return;
    setError(null);
    const res = await getJson<ApiEnvelope<{ item: EmbeddingProviderItem | null }>>("/v1/embedding-providers/default/me");
    const item = res.data.item;
    if (!item) {
      setCurrentEmbeddingProviderId(null);
      embeddingForm.setFieldsValue({ provider_type: "huggingface", ...EMBEDDING_PROVIDER_PRESETS.huggingface.defaultValues, is_default: true });
      return;
    }
    setCurrentEmbeddingProviderId(item.provider_id);
    embeddingForm.setFieldsValue({
      provider_type: item.provider_type,
      display_name: item.display_name,
      model_name: item.model_name ?? null,
      base_url: item.base_url ?? "",
      local_path: item.local_path ?? "",
      cache_dir: item.cache_dir ?? "",
      is_default: item.is_default,
    });
    if (showMessage) setMessage(`Saved embedding provider ${item.display_name}`);
  }

  async function loadUserSettings() {
    try {
      const res = await getJson<ApiEnvelope<{ max_parallel_tasks: number }>>("/v1/users/settings/me");
      setMaxParallelTasks(Math.max(1, Math.min(10, Number(res.data.max_parallel_tasks || 10))));
    } catch (e) {
      if (String(e).includes("HTTP 404")) {
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
    loadDefaultEmbeddingProvider().catch((e) => setError(String(e)));
    loadEmbeddingProviders().catch((e) => setError(String(e)));
    loadUserSettings().catch((e) => setError(String(e)));
  }, [auth.userId]); // eslint-disable-line react-hooks/exhaustive-deps

  async function testChatConfig() {
    const values = await chatForm.validateFields();
    const res = await postJson<ApiEnvelope<ProviderTestResult>>("/v1/providers/test", {
      provider_type: values.provider_type,
      base_url: values.base_url || null,
      api_key: values.api_key || null,
      model_name: values.model_name || values.chat_model || null,
      chat_model: values.chat_model || null,
    });
    setChatTestResult(res.data);
    setMessage(`Chat test ${res.data.status}: ${res.data.message}`);
  }

  async function testEmbeddingConfig() {
    const values = await embeddingForm.validateFields();
    const res = await postJson<ApiEnvelope<ProviderTestResult>>("/v1/embedding-providers/test", {
      provider_type: values.provider_type,
      model_name: values.model_name || null,
      base_url: values.base_url || null,
      local_path: values.local_path || null,
      cache_dir: values.cache_dir || null,
    });
    setEmbeddingTestResult(res.data);
    setMessage(`Embedding test ${res.data.status}: ${res.data.message}`);
  }

  return (
    <Space direction="vertical" style={{ width: "100%" }} size={16}>
      <Typography.Title level={4}>Model Settings</Typography.Title>
      {message && <Alert type="success" message={message} />}
      {error && <Alert type="error" message={error} />}

      <Card title="Chat Model Provider">
        {chatTestResult && (
          <Alert
            type={chatTestResult.status === "ok" ? "success" : "warning"}
            showIcon
            message={`Connection Test: ${chatTestResult.status}`}
            description={chatTestResult.message}
            style={{ marginBottom: 12 }}
          />
        )}
        <Form
          form={chatForm}
          layout="vertical"
          onFinish={saveChatProvider}
          initialValues={{ provider_type: "vllm", ...CHAT_PROVIDER_PRESETS.vllm.defaultValues, is_default: true }}
          onValuesChange={(changed) => {
            if (changed.provider_type) {
              const preset = CHAT_PROVIDER_PRESETS[changed.provider_type as ChatProviderType];
              chatForm.setFieldsValue({ ...preset.defaultValues, api_key: null });
              setCurrentProviderHasApiKey(false);
            }
          }}
        >
          <Form.Item label="Provider" name="provider_type" initialValue="vllm">
            <Select options={Object.values(CHAT_PROVIDER_PRESETS).map((x) => ({ label: x.label, value: x.providerType }))} />
          </Form.Item>
          <Form.Item label={requiredLabel("Display Name", "Required. Example: Deepseek API / Ollama Local")} name="display_name" rules={[{ required: true }]}>
            <Input placeholder={chatPreset.defaultValues.display_name} />
          </Form.Item>
          <Form.Item label={requiredLabel("Base URL", `Required. Example: ${chatPreset.baseUrlExample}`)} name="base_url" rules={[{ required: true }]}>
            <Input placeholder={chatPreset.baseUrlExample} />
          </Form.Item>
          {chatPreset.needsChatModel ? (
            <Form.Item label={requiredLabel("Chat Model", "Required. Example: qwen3:8b")} name="chat_model" rules={[{ required: true }]}>
              <Input placeholder={OLLAMA_DEFAULT.chat_model} />
            </Form.Item>
          ) : (
            <Form.Item label={requiredLabel("Model Name", `Required. Example: ${chatPreset.modelExample}`)} name="model_name" rules={[{ required: true }]}>
              {chatPreset.modelOptions ? (
                <Select showSearch placeholder={chatPreset.modelExample} options={chatPreset.modelOptions.map((item) => ({ label: item, value: item }))} />
              ) : (
                <Input placeholder={chatPreset.modelExample} />
              )}
            </Form.Item>
          )}
          {chatPreset.needsApiKey && (
            <Form.Item
              label={requiredLabel("API Key", "Required. Existing saved key is kept when left blank.")}
              name="api_key"
              rules={[
                {
                  validator: (_, value) => {
                    if (String(value || "").trim() || currentProviderHasApiKey) return Promise.resolve();
                    return Promise.reject(new Error("API Key is required."));
                  },
                },
              ]}
            >
              <Input.Password placeholder={currentProviderHasApiKey ? "Leave empty to keep saved key" : "Enter API Key"} />
            </Form.Item>
          )}
          <Form.Item name="is_default" valuePropName="checked">
            <Checkbox>Default</Checkbox>
          </Form.Item>
          <Space>
            <Button htmlType="submit" type="primary">Save Chat Provider</Button>
            <Button onClick={() => testChatConfig().catch((e) => setError(String(e)))}>Test Chat Provider</Button>
            <Button onClick={() => loadDefaultProvider().catch((e) => setError(String(e)))}>Load Default</Button>
          </Space>
        </Form>
        <Typography.Title level={5} style={{ marginTop: 20 }}>Saved Chat Providers</Typography.Title>
        <List
          dataSource={providers}
          renderItem={(p) => (
            <List.Item>
              {p.display_name} ({p.provider_type}/{p.chat_model || p.model_name}) {p.is_default ? "[default]" : ""}
            </List.Item>
          )}
        />
      </Card>

      <Card title="Embedding Model Provider">
        {embeddingTestResult && (
          <Alert
            type={embeddingTestResult.status === "ok" ? "success" : "warning"}
            showIcon
            message={`Embedding Test: ${embeddingTestResult.status}`}
            description={
              embeddingTestResult.dimension
                ? `${embeddingTestResult.message} dimension=${embeddingTestResult.dimension}`
                : embeddingTestResult.message
            }
            style={{ marginBottom: 12 }}
          />
        )}
        <Form
          form={embeddingForm}
          layout="vertical"
          onFinish={saveEmbeddingProvider}
          initialValues={{ provider_type: "huggingface", ...EMBEDDING_PROVIDER_PRESETS.huggingface.defaultValues, is_default: true }}
          onValuesChange={(changed) => {
            if (changed.provider_type) {
              const preset = EMBEDDING_PROVIDER_PRESETS[changed.provider_type as EmbeddingProviderType];
              embeddingForm.setFieldsValue({ ...preset.defaultValues });
            }
          }}
        >
          <Form.Item label="Embedding Provider" name="provider_type">
            <Select options={Object.values(EMBEDDING_PROVIDER_PRESETS).map((x) => ({ label: x.label, value: x.providerType }))} />
          </Form.Item>
          <Form.Item label={requiredLabel("Display Name", "Required. Example: Qwen Embedding")} name="display_name" rules={[{ required: true }]}>
            <Input placeholder={embeddingPreset.defaultValues.display_name} />
          </Form.Item>
          {embeddingProviderType === "ollama" && (
            <>
              <Form.Item label={requiredLabel("Embedding Model", "Ollama embedding model name.")} name="model_name" rules={[{ required: true }]}>
                <Input placeholder={OLLAMA_DEFAULT.embedding_model} />
              </Form.Item>
              <Form.Item label="Base URL" name="base_url">
                <Input placeholder={OLLAMA_DEFAULT.base_url} />
              </Form.Item>
            </>
          )}
          {embeddingProviderType === "local_embedding" && (
            <Form.Item label={requiredLabel("Local Model Folder", "Full folder path containing the local embedding model.")} name="local_path" rules={[{ required: true }]}>
              <Input placeholder="D:\\models\\bge-large-zh-v1.5" />
            </Form.Item>
          )}
          {embeddingProviderType === "huggingface" && (
            <>
              <Form.Item label={requiredLabel("HuggingFace Model", "Downloaded into backend model cache on first use.")} name="model_name" rules={[{ required: true }]}>
                <Input placeholder="Qwen/Qwen3-Embedding-8B" />
              </Form.Item>
              <Form.Item label="Cache Directory (optional)" name="cache_dir">
                <Input placeholder="Leave empty to use runtime_data/storage/model_cache/embeddings" />
              </Form.Item>
            </>
          )}
          <Form.Item name="is_default" valuePropName="checked">
            <Checkbox>Default</Checkbox>
          </Form.Item>
          <Space>
            <Button htmlType="submit" type="primary">Save Embedding Provider</Button>
            <Button onClick={() => testEmbeddingConfig().catch((e) => setError(String(e)))}>Test Embedding Provider</Button>
            <Button onClick={() => loadDefaultEmbeddingProvider().catch((e) => setError(String(e)))}>Load Default</Button>
          </Space>
        </Form>
        <Typography.Title level={5} style={{ marginTop: 20 }}>Saved Embedding Providers</Typography.Title>
        <List
          dataSource={embeddingProviders}
          renderItem={(p) => (
            <List.Item>
              {p.display_name} ({p.provider_type}/{p.model_name || p.local_path}) {p.is_default ? "[default]" : ""}
            </List.Item>
          )}
        />
      </Card>

      <Card title="Task Concurrency">
        <Space>
          <Typography.Text>Max Parallel Tasks</Typography.Text>
          <InputNumber min={1} max={10} value={maxParallelTasks} onChange={(v) => setMaxParallelTasks(Number(v || 1))} />
          <Button type="primary" onClick={() => saveUserSettings().catch((e) => setError(String(e)))}>
            Save Limit
          </Button>
        </Space>
      </Card>
    </Space>
  );
}
