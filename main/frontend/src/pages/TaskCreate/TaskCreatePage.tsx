import { Alert, Button, Card, Form, Input, InputNumber, Select, Space, Typography } from "antd";
import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { getJson, postFile, postJson } from "../../api/http";
import AuthImage from "../../components/AuthImage";
import { useAppStore } from "../../store/appStore";
import { ApiEnvelope } from "../../types/api";

type CreateTaskData = { task_id: string; status: string };
type InferTypeData = { task_type: string };
type InferTemplateSettingsData = {
  templateType?: string;
  templateTarget?: string;
  template_target?: string;
  templateName?: string;
  template_name?: string;
  language?: string;
};
type TaskType = string;
type Step = "requirement" | "setting";
type PptTemplateItem = {
  name: string;
  style_value: string;
  is_valid?: boolean;
  missing_files?: string[];
  schema_version?: string;
  preview_images?: Array<{ page: number; url: string }>;
  sample_preview_images?: Array<{ page: number; url: string }>;
};

type PptStyleItem = {
  name: string;
  description: string;
};

type SettingValues = {
  taskType?: string;
  language: string;
  pages?: number;
  style?: string;
  audience?: string;
  tone?: string;
  length?: string;
  includeExecutiveSummary?: string;
  ctaStyle?: string;
  analysisDepth?: string;
  outputFormat?: string;
  targetColumn?: string;
  docFocus?: string;
  codingLanguage?: string;
  paperStage?: string;
  citationStyle?: string;
  templateTarget?: string;
  templateName?: string;
  templateChoice?: string;
  styleGuide?: string;
};

const PPT_STYLE_STORAGE_KEY = "wf_ppt_custom_styles";
const BUILTIN_PPT_STYLES: PptStyleItem[] = [
  {
    name: "academic_simple",
    description: "采用学术简洁风格：结构清晰、论点明确、表达克制，优先呈现核心结论、证据和逻辑链条，避免营销化措辞。",
  },
  {
    name: "academic_report",
    description: "采用学术报告风格：内容信息密度较高，强调背景、方法、发现和启示，语言专业严谨，适合正式汇报与研究型展示。",
  },
];

const taskTypeLabel: Record<string, string> = {
  ppt: "PPT",
  report: "Report",
  wechat_post: "WeChat Post",
  data_analysis: "Data Analysis",
  code_doc: "Code Documentation",
  paper_assistant: "Paper Assistant",
  generic_task: "Generic Task",
  template_generation: "Template Generation"
};

function taskTypeDisplayLabel(value: string): string {
  const normalized = (value || "").trim();
  const preset = taskTypeLabel[normalized];
  if (preset) return `${preset} (${normalized})`;
  return normalized;
}

function buildFinalRequirement(baseRequirement: string, taskType: TaskType, settings: SettingValues): string {
  const lines: string[] = [];
  lines.push(baseRequirement.trim());
  lines.push("");
  lines.push("[Task Settings]");
  lines.push(`TaskType=${taskType}`);
  lines.push(`Language=${settings.language}`);
  if (settings.templateChoice) {
    lines.push(`TemplateChoice=${settings.templateChoice}`);
  }

  if (taskType === "ppt") {
    lines.push(`Pages=${settings.pages ?? 10}`);
    lines.push(`Style=${settings.style ?? "academic_simple"}`);
    if (settings.styleGuide) {
      lines.push(`StyleGuide=${settings.styleGuide}`);
    }
  }
  if (taskType === "report") {
    lines.push(`Audience=${settings.audience ?? "General stakeholders"}`);
    lines.push(`Tone=${settings.tone ?? "professional"}`);
    lines.push(`Length=${settings.length ?? "medium"}`);
    lines.push(`IncludeExecutiveSummary=${settings.includeExecutiveSummary ?? "yes"}`);
  }
  if (taskType === "wechat_post") {
    lines.push(`Audience=${settings.audience ?? "General readers"}`);
    lines.push(`Tone=${settings.tone ?? "engaging"}`);
    lines.push(`CTAStyle=${settings.ctaStyle ?? "follow_and_comment"}`);
    lines.push(`Length=${settings.length ?? "medium"}`);
  }
  if (taskType === "data_analysis") {
    lines.push(`AnalysisDepth=${settings.analysisDepth ?? "standard"}`);
    lines.push(`OutputFormat=${settings.outputFormat ?? "insight_report"}`);
    lines.push(`TargetColumn=${settings.targetColumn ?? "cate"}`);
    lines.push(`Audience=${settings.audience ?? "Business users"}`);
  }
  if (taskType === "code_doc") {
    lines.push(`DocFocus=${settings.docFocus ?? "readme_and_api"}`);
    lines.push(`CodingLanguage=${settings.codingLanguage ?? "python"}`);
    lines.push(`Audience=${settings.audience ?? "developers"}`);
  }
  if (taskType === "paper_assistant") {
    lines.push(`PaperStage=${settings.paperStage ?? "drafting"}`);
    lines.push(`CitationStyle=${settings.citationStyle ?? "apa"}`);
    lines.push(`Tone=${settings.tone ?? "academic"}`);
  }
  if (taskType === "template_generation") {
    lines.push(`TemplateTarget=${settings.templateTarget ?? "ppt"}`);
    lines.push(`TemplateName=${settings.templateName ?? "generated_template"}`);
  }

  return lines.join("\n");
}

function inferTemplateTargetFromFile(file: File | null): string {
  const ext = (file?.name.split(".").pop() || "").toLowerCase();
  if (ext === "ppt" || ext === "pptx") return "ppt";
  if (ext === "doc" || ext === "docx" || ext === "pdf") return "report";
  return "ppt";
}

function normalizeTemplateTarget(value: unknown, fallback: string): string {
  const target = String(value || "").trim().toLowerCase();
  return ["ppt", "wechat_post", "report"].includes(target) ? target : fallback;
}

function fallbackTemplateName(requirement: string, file: File | null): string {
  const base = (file?.name || requirement || "generated_template").replace(/\.[^.]+$/, "");
  const slug = base.toLowerCase().replace(/[^a-z0-9_\-\u4e00-\u9fa5]+/g, "_").replace(/^_+|_+$/g, "");
  return slug || "generated_template";
}

export default function TaskCreatePage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const aux = (searchParams.get("aux") || "").trim().toLowerCase();
  const { auth, task, setTask, upsertRunningTask, setSelectedRunningTaskId } = useAppStore();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [step, setStep] = useState<Step>("requirement");
  const [requirement, setRequirement] = useState<string>("");
  const [inferredTaskType, setInferredTaskType] = useState<TaskType | null>(null);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [pptTemplates, setPptTemplates] = useState<PptTemplateItem[]>([]);
  const [reportTemplates, setReportTemplates] = useState<PptTemplateItem[]>([]);
  const [wechatTemplates, setWechatTemplates] = useState<PptTemplateItem[]>([]);
  const [taskTypes, setTaskTypes] = useState<string[]>([]);
  const [pptStyles, setPptStyles] = useState<PptStyleItem[]>(BUILTIN_PPT_STYLES);
  const [customStyleName, setCustomStyleName] = useState<string>("");

  const [requirementForm] = Form.useForm();
  const [settingForm] = Form.useForm();
  const selectedTemplateChoice = Form.useWatch("templateChoice", settingForm);
  const selectedPptTemplate = useMemo(
    () => pptTemplates.find((item) => item.style_value === selectedTemplateChoice || item.name === selectedTemplateChoice) || null,
    [pptTemplates, selectedTemplateChoice],
  );

  async function reloadTemplates() {
    try {
      const [pptRes, reportRes, wechatRes] = await Promise.all([
        getJson<ApiEnvelope<{ items: PptTemplateItem[] }>>("/v1/tasks/ppt/templates"),
        getJson<ApiEnvelope<{ items: PptTemplateItem[] }>>("/v1/tasks/templates/report"),
        getJson<ApiEnvelope<{ items: PptTemplateItem[] }>>("/v1/tasks/templates/wechat_post"),
      ]);
      setPptTemplates((pptRes.data.items ?? []).filter((item) => item.is_valid !== false));
      setReportTemplates(reportRes.data.items ?? []);
      setWechatTemplates(wechatRes.data.items ?? []);
    } catch {
      setPptTemplates([]);
      setReportTemplates([]);
      setWechatTemplates([]);
    }
  }

  async function reloadTaskTypes() {
    try {
      const res = await getJson<ApiEnvelope<{ items: string[] }>>("/v1/tasks/task-types/me");
      const items = (res.data.items || []).map((x) => String(x || "").trim()).filter(Boolean);
      setTaskTypes(items);
    } catch {
      setTaskTypes(Object.keys(taskTypeLabel));
    }
  }

  async function registerTaskType(taskType: string) {
    const normalized = (taskType || "").trim().toLowerCase().replace(/[^a-z0-9_ -]/g, "").replace(/[ -]+/g, "_");
    if (!normalized) return;
    try {
      await postJson<ApiEnvelope<{ task_type: string }>>("/v1/tasks/task-types/me", { task_type: normalized });
      setTaskTypes((prev) => (prev.includes(normalized) ? prev : [...prev, normalized]));
    } catch {
      // no-op; keep local value so user can still proceed
    }
  }

  const settingInitialValues = useMemo(
    () => ({
      language: "zh-CN",
      pages: 10,
      style: "academic_simple",
      templateChoice: "system_default",
      audience: "General stakeholders",
      tone: "professional",
      length: "medium",
      includeExecutiveSummary: "yes",
      ctaStyle: "follow_and_comment",
      analysisDepth: "standard",
      outputFormat: "insight_report",
      targetColumn: "cate",
      docFocus: "readme_and_api",
      codingLanguage: "python",
      paperStage: "drafting",
      citationStyle: "apa"
    }),
    []
  );

  useEffect(() => {
    void reloadTemplates();
    void reloadTaskTypes();
    try {
      const saved = JSON.parse(localStorage.getItem(PPT_STYLE_STORAGE_KEY) || "[]") as PptStyleItem[];
      if (Array.isArray(saved) && saved.length) {
        setPptStyles([...BUILTIN_PPT_STYLES, ...saved.filter((item) => item?.name && item?.description)]);
      }
    } catch {
      setPptStyles(BUILTIN_PPT_STYLES);
    }
  }, []);

  function saveCustomPptStyle(style: PptStyleItem) {
    const trimmed = { name: style.name.trim(), description: style.description.trim() };
    if (!trimmed.name || !trimmed.description) return;
    const custom = pptStyles.filter((item) => !BUILTIN_PPT_STYLES.some((builtin) => builtin.name === item.name));
    const nextCustom = [trimmed, ...custom.filter((item) => item.name !== trimmed.name)].slice(0, 20);
    localStorage.setItem(PPT_STYLE_STORAGE_KEY, JSON.stringify(nextCustom));
    setPptStyles([...BUILTIN_PPT_STYLES, ...nextCustom]);
  }

  async function ensurePptStyleGuide(styleName: string): Promise<string> {
    const name = (styleName || "academic_simple").trim();
    const existing = pptStyles.find((item) => item.name === name);
    if (existing?.description) return existing.description;
    const res = await postJson<ApiEnvelope<{ style_name: string; description: string }>>("/v1/tasks/ppt/styles/infer", {
      user_id: auth.userId,
      style_name: name,
      requirement,
    });
    const generated = {
      name: res.data.style_name || name,
      description: res.data.description || `采用${name}风格生成PPT内容。`,
    };
    saveCustomPptStyle(generated);
    return generated.description;
  }

  function applyTaskTypeChange(nextType: string) {
    const normalized = (nextType || "").trim();
    setInferredTaskType(normalized || null);
    settingForm.setFieldValue("taskType", normalized || undefined);
    if (normalized && !taskTypes.includes(normalized)) {
      void registerTaskType(normalized);
    }
    const current = settingForm.getFieldsValue() as SettingValues;
    const nextSettings: Partial<SettingValues> = {
      ...settingInitialValues,
      language: current.language || settingInitialValues.language,
    };
    if (normalized === "template_generation") {
      nextSettings.templateTarget = current.templateTarget || inferTemplateTargetFromFile(selectedFile);
      nextSettings.templateName = current.templateName || fallbackTemplateName(requirement, selectedFile);
    }
    if (normalized === "ppt") {
      nextSettings.templateChoice = current.templateChoice || settingInitialValues.templateChoice;
      nextSettings.pages = current.pages || settingInitialValues.pages;
      nextSettings.style = current.style || settingInitialValues.style;
    }
    settingForm.setFieldsValue(nextSettings);
  }

  async function onInfer(values: { requirement: string }) {
    setError(null);
    setMessage(null);
    try {
      const taskType: TaskType = aux === "template_generation"
        ? "template_generation"
        : (await postJson<ApiEnvelope<InferTypeData>>("/v1/tasks/infer-type", {
            requirement: values.requirement,
            user_id: auth.userId
          })).data.task_type;
      await reloadTemplates();
      await reloadTaskTypes();
      setRequirement(values.requirement);
      setInferredTaskType(taskType);
      const nextSettings: Partial<SettingValues> = { ...settingInitialValues };
      nextSettings.taskType = taskType;
      if (taskType) {
        await registerTaskType(taskType);
      }
      if (taskType === "template_generation") {
        const fallbackTarget = inferTemplateTargetFromFile(selectedFile);
        nextSettings.templateTarget = fallbackTarget;
        nextSettings.templateName = fallbackTemplateName(values.requirement, selectedFile);
        try {
          const fileHint = selectedFile
            ? `\n\n[Uploaded File]\nName=${selectedFile.name}\nExtension=${selectedFile.name.split(".").pop() || ""}\nMimeType=${selectedFile.type || ""}`
            : "";
          const inferred = await postJson<ApiEnvelope<InferTemplateSettingsData>>("/v1/tasks/template-generation/infer-settings", {
            requirement: `${values.requirement}${fileHint}`,
            user_id: auth.userId
          });
          const data = inferred.data || {};
          nextSettings.templateTarget = normalizeTemplateTarget(
            data.templateTarget ?? data.templateType ?? data.template_target,
            fallbackTarget
          );
          nextSettings.templateName = String(data.templateName ?? data.template_name ?? "").trim() || nextSettings.templateName;
          if (data.language === "zh-CN" || data.language === "en-US") {
            nextSettings.language = data.language;
          }
        } catch {
          // Keep deterministic defaults so the required fields are still editable and non-empty.
        }
      }
      settingForm.setFieldsValue(nextSettings);
      setStep("setting");
    } catch (e) {
      setError(String(e));
    }
  }

  async function onStart(values: SettingValues) {
    setError(null);
    setMessage(null);
    setIsSubmitting(true);
    if (!auth.userId) {
      setError("Please login first.");
      setIsSubmitting(false);
      return;
    }
    if (!inferredTaskType) {
      setError("Task type is not inferred yet.");
      setIsSubmitting(false);
      return;
    }
    if ((inferredTaskType === "data_analysis" || inferredTaskType === "code_doc" || inferredTaskType === "template_generation") && !selectedFile) {
      setError("This task type requires a source file upload.");
      setIsSubmitting(false);
      return;
    }

    try {
      if (inferredTaskType) {
        await registerTaskType(inferredTaskType);
      }
      const effectiveValues = { ...values };
      if (inferredTaskType === "ppt") {
        effectiveValues.style = (values.style || "academic_simple").trim();
        effectiveValues.styleGuide = await ensurePptStyleGuide(effectiveValues.style);
      }
      const finalRequirement = buildFinalRequirement(requirement, inferredTaskType, effectiveValues);
      const createRes = await postJson<ApiEnvelope<CreateTaskData>>("/v1/tasks", {
        user_id: auth.userId,
        user_requirement: finalRequirement,
        task_type: inferredTaskType,
        pages: inferredTaskType === "ppt" ? effectiveValues.pages ?? 10 : 10,
        style: inferredTaskType === "ppt" ? effectiveValues.style ?? "academic_simple" : "academic_simple",
        template_choice: effectiveValues.templateChoice ?? null,
        language: effectiveValues.language
      });
      const taskId = createRes.data.task_id;
      setTask((prev) => ({ ...prev, activeTaskId: taskId, activeTaskStatus: createRes.data.status }));
      upsertRunningTask({
        taskId,
        status: createRes.data.status,
        taskType: inferredTaskType,
        title: requirement,
      });
      setSelectedRunningTaskId(taskId);

      const runTask = async () => {
        if (selectedFile) {
          await postFile(`/v1/tasks/${taskId}/upload`, selectedFile);
          await postJson(`/v1/tasks/${taskId}/parse`, { force: false });
        }
        const runRes = await postJson<ApiEnvelope<{ status: string; output_path: string }>>(
          `/v1/tasks/${taskId}/run`,
          { rerun: false }
        );
        setTask((prev) => ({ ...prev, activeTaskId: taskId, activeTaskStatus: runRes.data.status }));
        upsertRunningTask({
          taskId,
          status: runRes.data.status,
          taskType: inferredTaskType,
          title: requirement,
        });
        return runRes;
      };

      navigate(`/tasks/running/${encodeURIComponent(taskId)}`);
      void runTask().catch((runErr) => {
        setError(String(runErr));
      });
    } catch (e) {
      setError(String(e));
    } finally {
      setIsSubmitting(false);
    }
  }

  function renderTaskSpecificSettings() {
    if (!inferredTaskType) return null;
    if (inferredTaskType === "ppt") {
      const selectedTemplatePreviews = selectedPptTemplate?.sample_preview_images?.length
        ? selectedPptTemplate.sample_preview_images
        : selectedPptTemplate?.preview_images || [];
      const styleOptions = pptStyles.map((item) => ({
        label: item.name,
        value: item.name,
        title: item.description,
      }));
      const templateOptions = pptTemplates
        .filter((t) => t.is_valid !== false)
        .map((t) => ({
          label: t.schema_version ? `${t.name} (${t.schema_version})` : t.name,
          value: t.style_value,
        }));
      return (
        <>
          <Form.Item label="Pages" name="pages" rules={[{ required: true }]}>
            <InputNumber min={5} max={30} style={{ width: 240 }} />
          </Form.Item>
          <Form.Item label="Style" name="style" rules={[{ required: true }]}>
            <Space.Compact>
              <Select
                showSearch
                style={{ width: 280 }}
                options={styleOptions}
                optionFilterProp="label"
                placeholder="Select a style"
              />
              <Input
                style={{ width: 220 }}
                value={customStyleName}
                onChange={(e) => setCustomStyleName(e.target.value)}
                placeholder="Custom style"
              />
              <Button
                onClick={async () => {
                  const name = customStyleName.trim();
                  if (!name) return;
                  try {
                    await ensurePptStyleGuide(name);
                    settingForm.setFieldValue("style", name);
                    setCustomStyleName("");
                  } catch (e) {
                    setError(String(e));
                  }
                }}
              >
                Add
              </Button>
            </Space.Compact>
          </Form.Item>
          <Form.Item label="Template Choice" name="templateChoice" rules={[{ required: true, message: "Please select a PPT template." }]}>
            <Select
              style={{ width: 320 }}
              options={templateOptions}
              placeholder="Select validated PPT template"
            />
          </Form.Item>
          {selectedTemplatePreviews.length ? (
            <div style={{ marginBottom: 16 }}>
              <Space wrap align="start">
                {selectedTemplatePreviews.slice(0, 1).map((img) => (
                  <Space key={img.url} direction="vertical" size={4}>
                    <AuthImage
                      src={img.url}
                      alt={`${selectedPptTemplate?.name || "template"} page ${img.page}`}
                      style={{ width: 220, height: 124, objectFit: "contain", border: "1px solid #e5e7eb" }}
                    />
                    <Typography.Text type="secondary">Page {img.page}</Typography.Text>
                  </Space>
                ))}
              </Space>
            </div>
          ) : null}
        </>
      );
    }
    if (inferredTaskType === "report") {
      const templateOptions = reportTemplates.map((t) => ({ label: t.name, value: t.style_value }));
      return (
        <>
          <Form.Item label="Template" name="templateChoice">
            <Select allowClear options={templateOptions} placeholder="Select report template" />
          </Form.Item>
          <Form.Item label="Audience" name="audience"><Input /></Form.Item>
          <Form.Item label="Tone" name="tone">
            <Select options={[{ label: "Professional", value: "professional" }, { label: "Neutral", value: "neutral" }, { label: "Persuasive", value: "persuasive" }]} />
          </Form.Item>
          <Form.Item label="Length" name="length">
            <Select options={[{ label: "Short", value: "short" }, { label: "Medium", value: "medium" }, { label: "Long", value: "long" }]} />
          </Form.Item>
          <Form.Item label="Executive Summary" name="includeExecutiveSummary">
            <Select options={[{ label: "Include", value: "yes" }, { label: "Skip", value: "no" }]} />
          </Form.Item>
        </>
      );
    }
    if (inferredTaskType === "wechat_post") {
      const templateOptions = wechatTemplates.map((t) => ({ label: t.name, value: t.style_value }));
      return (
        <>
          <Form.Item label="Template" name="templateChoice">
            <Select allowClear options={templateOptions} placeholder="Select wechat template" />
          </Form.Item>
          <Form.Item label="Audience" name="audience"><Input /></Form.Item>
          <Form.Item label="Tone" name="tone">
            <Select options={[{ label: "Engaging", value: "engaging" }, { label: "Practical", value: "practical" }, { label: "Storytelling", value: "storytelling" }]} />
          </Form.Item>
          <Form.Item label="Length" name="length">
            <Select options={[{ label: "Short", value: "short" }, { label: "Medium", value: "medium" }, { label: "Long", value: "long" }]} />
          </Form.Item>
          <Form.Item label="CTA Style" name="ctaStyle">
            <Select options={[{ label: "Follow + Comment", value: "follow_and_comment" }, { label: "Read More", value: "read_more" }, { label: "Share", value: "share" }]} />
          </Form.Item>
        </>
      );
    }
    if (inferredTaskType === "data_analysis") {
      return (
        <>
          <Form.Item label="Analysis Depth" name="analysisDepth">
            <Select options={[{ label: "Quick", value: "quick" }, { label: "Standard", value: "standard" }, { label: "Deep", value: "deep" }]} />
          </Form.Item>
          <Form.Item label="Output Format" name="outputFormat">
            <Select options={[{ label: "Insight Report", value: "insight_report" }, { label: "Step-by-step", value: "step_by_step" }, { label: "Executive Summary", value: "executive_summary" }]} />
          </Form.Item>
          <Form.Item label="Target Column" name="targetColumn" rules={[{ required: true }]}>
            <Input placeholder="e.g. cate / industry / segment" />
          </Form.Item>
          <Form.Item label="Audience" name="audience"><Input /></Form.Item>
        </>
      );
    }
    if (inferredTaskType === "code_doc") {
      return (
        <>
          <Form.Item label="Doc Focus" name="docFocus">
            <Select options={[{ label: "README + API", value: "readme_and_api" }, { label: "README only", value: "readme_only" }, { label: "API only", value: "api_only" }]} />
          </Form.Item>
          <Form.Item label="Coding Language" name="codingLanguage">
            <Select options={[{ label: "Python", value: "python" }, { label: "TypeScript", value: "typescript" }, { label: "Java", value: "java" }, { label: "Go", value: "go" }]} />
          </Form.Item>
          <Form.Item label="Audience" name="audience"><Input /></Form.Item>
        </>
      );
    }
    if (inferredTaskType === "generic_task") {
      return (
        <>
          <Alert
            type="info"
            showIcon
            message="This request is classified as a new/other task type. The system may ask you to set up new capability during execution."
            style={{ marginBottom: 12 }}
          />
        </>
      );
    }
    if (inferredTaskType === "paper_assistant") {
      return (
        <>
          <Form.Item label="Paper Stage" name="paperStage">
            <Select options={[{ label: "Drafting", value: "drafting" }, { label: "Revision", value: "revision" }, { label: "Submission polishing", value: "submission_polishing" }]} />
          </Form.Item>
          <Form.Item label="Citation Style" name="citationStyle">
            <Select options={[{ label: "APA", value: "apa" }, { label: "IEEE", value: "ieee" }, { label: "MLA", value: "mla" }, { label: "Chicago", value: "chicago" }]} />
          </Form.Item>
          <Form.Item label="Tone" name="tone">
            <Select options={[{ label: "Academic", value: "academic" }, { label: "Concise", value: "concise" }, { label: "Formal", value: "formal" }]} />
          </Form.Item>
        </>
      );
    }
    if (inferredTaskType === "template_generation") {
      return (
        <>
          <Form.Item label="Template Target" name="templateTarget" rules={[{ required: true }]}>
            <Select options={[{ label: "PPT Template", value: "ppt" }, { label: "WeChat Template", value: "wechat_post" }, { label: "Report Template", value: "report" }]} />
          </Form.Item>
          <Form.Item label="Template Name" name="templateName" rules={[{ required: true, message: "Template name is required." }]}>
            <Input placeholder="e.g. oncology_pitch_v1" />
          </Form.Item>
        </>
      );
    }
    return (
      <Alert
        type="info"
        showIcon
        message="This is a custom task type. The system will run it with the general task workflow."
        style={{ marginBottom: 12 }}
      />
    );
  }

  return (
    <Card>
      <Typography.Title level={4}>{step === "requirement" ? "Create Task" : "Task Setting"}</Typography.Title>
      <Typography.Paragraph>Active task: {task.activeTaskId ?? "none"}</Typography.Paragraph>
      <Space direction="vertical" style={{ width: "100%", marginBottom: 12 }}>
        {message && <Alert type="success" message={message} />}
        {error && <Alert type="error" message={error} />}
      </Space>

      {step === "requirement" && (
        <Form form={requirementForm} layout="vertical" onFinish={onInfer}>
          <Form.Item label="Requirement" name="requirement" rules={[{ required: true, message: "Please input requirement" }]}>
            <Input.TextArea rows={5} />
          </Form.Item>
          <Form.Item label="Source File">
            <input type="file" onChange={(e) => setSelectedFile(e.target.files && e.target.files[0] ? e.target.files[0] : null)} />
          </Form.Item>
          {!selectedFile && (
            <Alert
              type="info"
              showIcon
              message="No source file: the model will search and summarize before generating the output."
              style={{ marginBottom: 16 }}
            />
          )}
          <Button htmlType="submit" type="primary">Start</Button>
        </Form>
      )}

      {step === "setting" && (
        <>
          {(inferredTaskType === "data_analysis" || inferredTaskType === "code_doc" || inferredTaskType === "template_generation") && !selectedFile && (
            <Alert
              type="warning"
              showIcon
              message="This task type requires a source file. Please go back and upload a file before running."
              style={{ marginBottom: 16 }}
            />
          )}
          <Form form={settingForm} layout="vertical" onFinish={onStart} initialValues={settingInitialValues}>
            <Form.Item label="Task Type" name="taskType" rules={[{ required: true, message: "Please select task type." }]}>
              <Select
                mode="tags"
                maxCount={1}
                value={inferredTaskType ? [inferredTaskType] : []}
                options={taskTypes.map((value) => ({ value, label: taskTypeDisplayLabel(value) }))}
                onChange={(values) => {
                  const list = Array.isArray(values) ? values : [];
                  const latest = list.length ? String(list[list.length - 1]) : "";
                  applyTaskTypeChange(latest);
                }}
                showSearch
                optionFilterProp="label"
                placeholder="Select or type task type"
                style={{ maxWidth: 360 }}
              />
            </Form.Item>
            <Form.Item label="Language" name="language" rules={[{ required: true }]}>
              <Select options={[{ label: "Chinese", value: "zh-CN" }, { label: "English", value: "en-US" }]} />
            </Form.Item>
            {renderTaskSpecificSettings()}
            <Space>
              <Button onClick={() => setStep("requirement")} disabled={isSubmitting}>Back</Button>
              <Button htmlType="submit" type="primary" loading={isSubmitting}>
                {inferredTaskType === "template_generation" ? "Create Template" : "Create + Run"}
              </Button>
            </Space>
          </Form>
        </>
      )}
    </Card>
  );
}
