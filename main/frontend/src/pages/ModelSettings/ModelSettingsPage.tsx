import { QuestionCircleOutlined } from "@ant-design/icons";
import { Alert, Button, Card, Checkbox, Form, Input, List, Select, Space, Tooltip, Typography } from "antd";
import { useMemo, useState } from "react";
import { getJson, postJson } from "../../api/http";
import { useAppStore } from "../../store/appStore";
import { ApiEnvelope } from "../../types/api";

type ProviderType =
  | "deepseek_api"
  | "openai_api"
  | "anthropic_api"
  | "qwen_api"
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
  is_default: boolean;
};

type ProviderConfigPreset = {
  label: string;
  providerType: ProviderType;
  baseUrlExample: string;
  modelExample: string;
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

const PROVIDER_PRESETS: Record<ProviderType, ProviderConfigPreset> = {
  deepseek_api: {
    label: "Deepseek API",
    providerType: "deepseek_api",
    baseUrlExample: "https://api.deepseek.com",
    modelExample: "qwen3:8b",
    needsApiKey: true,
    needsChatModel: false,
    needsEmbeddingModel: false,
    defaultValues: { display_name: "Deepseek API", base_url: "https://api.deepseek.com", model_name: "qwen3:8b" },
  },
  openai_api: {
    label: "OpenAI API",
    providerType: "openai_api",
    baseUrlExample: "https://api.openai.com/v1",
    modelExample: "qwen3:8b",
    needsApiKey: true,
    needsChatModel: false,
    needsEmbeddingModel: false,
    defaultValues: { display_name: "OpenAI API", base_url: "https://api.openai.com/v1", model_name: "qwen3:8b" },
  },
  anthropic_api: {
    label: "Anthropic API",
    providerType: "anthropic_api",
    baseUrlExample: "https://api.anthropic.com/v1",
    modelExample: "qwen3:8b",
    needsApiKey: true,
    needsChatModel: false,
    needsEmbeddingModel: false,
    defaultValues: {
      display_name: "Anthropic API",
      base_url: "https://api.anthropic.com/v1",
      model_name: "qwen3:8b",
    },
  },
  qwen_api: {
    label: "Qwen API",
    providerType: "qwen_api",
    baseUrlExample: "https://dashscope.aliyuncs.com/compatible-mode/v1",
    modelExample: "qwen3:8b",
    needsApiKey: true,
    needsChatModel: false,
    needsEmbeddingModel: false,
    defaultValues: {
      display_name: "Qwen API",
      base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1",
      model_name: "qwen3:8b",
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
    label: "本地LLM调用",
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
  const [form] = Form.useForm();

  const providerType: ProviderType = Form.useWatch("provider_type", form) ?? "ollama";
  const preset = useMemo(() => PROVIDER_PRESETS[providerType] ?? PROVIDER_PRESETS.ollama, [providerType]);

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
    const res = await postJson<ApiEnvelope<ProviderItem>>("/v1/providers", {
      user_id: auth.userId,
      provider_type: values.provider_type,
      display_name: values.display_name,
      base_url: values.base_url || null,
      model_name: values.model_name || values.chat_model || null,
      chat_model: values.chat_model || null,
      embedding_model: values.embedding_model || null,
      api_key: values.api_key || null,
      is_default: !!values.is_default
    });
    setMessage(`Saved provider ${res.data.display_name}`);
    await loadProviders();
  }

  async function loadProviders() {
    if (!auth.userId) {
      return;
    }
    const res = await getJson<ApiEnvelope<{ items: ProviderItem[] }>>(`/v1/providers/${auth.userId}`);
    setProviders(res.data.items);
  }

  async function testCurrentConfig() {
    const values = await form.validateFields();
    const res = await postJson<ApiEnvelope<{ status: string; message: string }>>("/v1/providers/test", {
      provider_type: values.provider_type,
      base_url: values.base_url || null,
      model_name: values.model_name || values.chat_model || null,
      chat_model: values.chat_model || null
    });
    setMessage(`Test ${res.data.status}: ${res.data.message}`);
  }

  return (
    <Card>
      <Typography.Title level={4}>Model Settings</Typography.Title>
      <Space direction="vertical" style={{ width: "100%" }}>
        {message && <Alert type="success" message={message} />}
        {error && <Alert type="error" message={error} />}
      </Space>
      <Form
        form={form}
        layout="vertical"
        onFinish={save}
        initialValues={{
          provider_type: "ollama",
          ...PROVIDER_PRESETS.ollama.defaultValues,
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
          }
        }}
      >
        <Form.Item label="Provider" name="provider_type" initialValue="ollama">
          <Select
            options={Object.values(PROVIDER_PRESETS).map((x) => ({ label: x.label, value: x.providerType }))}
          />
        </Form.Item>
        <Form.Item
          label={requiredLabel("Display Name", "必填。示例：Deepseek API / Ollama Local")}
          name="display_name"
          rules={[{ required: true, message: "Display Name is required." }]}
        >
          <Input placeholder={preset.defaultValues.display_name} />
        </Form.Item>
        <Form.Item
          label={requiredLabel("Base URL", `必填。示例：${preset.baseUrlExample}`)}
          name="base_url"
          rules={[{ required: true, message: "Base URL is required." }]}
        >
          <Input placeholder={preset.baseUrlExample} />
        </Form.Item>
        {preset.needsChatModel ? (
          <>
            <Form.Item
              label={requiredLabel("Chat Model", "必填。示例：qwen3:8b")}
              name="chat_model"
              rules={[{ required: true, message: "Chat Model is required." }]}
            >
              <Input placeholder={OLLAMA_DEFAULT.chat_model} />
            </Form.Item>
            <Form.Item
              label={requiredLabel("Embedding Model", "必填。示例：qwen3-embedding:8b")}
              name="embedding_model"
              rules={[{ required: true, message: "Embedding Model is required." }]}
            >
              <Input placeholder={OLLAMA_DEFAULT.embedding_model} />
            </Form.Item>
          </>
        ) : (
          <Form.Item
            label={requiredLabel("Model Name", `必填。示例：${preset.modelExample}`)}
            name="model_name"
            rules={[{ required: true, message: "Model Name is required." }]}
          >
            <Input placeholder={preset.modelExample} />
          </Form.Item>
        )}
        {preset.needsApiKey && (
          <Form.Item
            label={requiredLabel("API Key", "必填。示例：sk-xxxx / hf_xxxx")}
            name="api_key"
            rules={[{ required: true, message: "API Key is required." }]}
          >
            <Input.Password placeholder="请输入 API Key" />
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
    </Card>
  );
}
