import { Alert, Button, Card, Form, Input, InputNumber, Select, Space, Tag, Typography } from "antd";
import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { postFile, postJson } from "../../api/http";
import { useAppStore } from "../../store/appStore";
import { ApiEnvelope } from "../../types/api";

type CreateTaskData = { task_id: string; status: string };
type InferTypeData = { task_type: TaskType };
type TaskType = "ppt" | "report" | "wechat_post" | "data_analysis" | "code_doc" | "paper_assistant";
type Step = "requirement" | "setting";

type SettingValues = {
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
  docFocus?: string;
  codingLanguage?: string;
  paperStage?: string;
  citationStyle?: string;
};

const taskTypeLabel: Record<TaskType, string> = {
  ppt: "PPT",
  report: "Report",
  wechat_post: "WeChat Post",
  data_analysis: "Data Analysis",
  code_doc: "Code Documentation",
  paper_assistant: "Paper Assistant"
};

function buildFinalRequirement(baseRequirement: string, taskType: TaskType, settings: SettingValues): string {
  const lines: string[] = [];
  lines.push(baseRequirement.trim());
  lines.push("");
  lines.push("[Task Settings]");
  lines.push(`TaskType=${taskType}`);
  lines.push(`Language=${settings.language}`);

  if (taskType === "ppt") {
    lines.push(`Pages=${settings.pages ?? 10}`);
    lines.push(`Style=${settings.style ?? "academic_simple"}`);
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

  return lines.join("\n");
}

export default function TaskCreatePage() {
  const navigate = useNavigate();
  const { auth, task, setTask } = useAppStore();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [step, setStep] = useState<Step>("requirement");
  const [requirement, setRequirement] = useState<string>("");
  const [inferredTaskType, setInferredTaskType] = useState<TaskType | null>(null);

  const [requirementForm] = Form.useForm();
  const [settingForm] = Form.useForm();

  const settingInitialValues = useMemo(
    () => ({
      language: "zh-CN",
      pages: 10,
      style: "academic_simple",
      audience: "General stakeholders",
      tone: "professional",
      length: "medium",
      includeExecutiveSummary: "yes",
      ctaStyle: "follow_and_comment",
      analysisDepth: "standard",
      outputFormat: "insight_report",
      docFocus: "readme_and_api",
      codingLanguage: "python",
      paperStage: "drafting",
      citationStyle: "apa"
    }),
    []
  );

  async function onInfer(values: { requirement: string }) {
    setError(null);
    setMessage(null);
    try {
      const inferRes = await postJson<ApiEnvelope<InferTypeData>>("/v1/tasks/infer-type", {
        requirement: values.requirement
      });
      const taskType = inferRes.data.task_type;
      setRequirement(values.requirement);
      setInferredTaskType(taskType);
      settingForm.setFieldsValue(settingInitialValues);
      setStep("setting");
    } catch (e) {
      setError(String(e));
    }
  }

  async function onStart(values: SettingValues) {
    setError(null);
    setMessage(null);
    if (!auth.userId) {
      setError("Please login first.");
      return;
    }
    if (!inferredTaskType) {
      setError("Task type is not inferred yet.");
      return;
    }
    if ((inferredTaskType === "data_analysis" || inferredTaskType === "code_doc") && !selectedFile) {
      setError("Data Analysis and Code Documentation tasks require a source file upload.");
      return;
    }
    const finalRequirement = buildFinalRequirement(requirement, inferredTaskType, values);

    try {
      const createRes = await postJson<ApiEnvelope<CreateTaskData>>("/v1/tasks", {
        user_id: auth.userId,
        user_requirement: finalRequirement,
        task_type: "auto",
        pages: inferredTaskType === "ppt" ? values.pages ?? 10 : 10,
        style: inferredTaskType === "ppt" ? values.style ?? "academic_simple" : "academic_simple",
        language: values.language
      });
      const taskId = createRes.data.task_id;
      setTask({ activeTaskId: taskId, activeTaskStatus: createRes.data.status });

      if (selectedFile) {
        await postFile(`/v1/tasks/${taskId}/upload`, selectedFile);
        await postJson(`/v1/tasks/${taskId}/parse`, { force: false });
      }
      navigate("/tasks/running");
      void postJson<ApiEnvelope<{ status: string; output_path: string }>>(`/v1/tasks/${taskId}/run`, { rerun: false })
        .then((runRes) => {
          setTask({ activeTaskId: taskId, activeTaskStatus: runRes.data.status });
        })
        .catch((runErr) => {
          setError(String(runErr));
        });
    } catch (e) {
      setError(String(e));
    }
  }

  function renderTaskSpecificSettings() {
    if (!inferredTaskType) return null;
    if (inferredTaskType === "ppt") {
      return (
        <>
          <Form.Item label="Pages" name="pages" rules={[{ required: true }]}>
            <InputNumber min={5} max={30} style={{ width: 240 }} />
          </Form.Item>
          <Form.Item label="Style" name="style" rules={[{ required: true }]}>
            <Select
              style={{ width: 280 }}
              options={[
                { label: "Academic Simple", value: "academic_simple" },
                { label: "Academic Report", value: "academic_report" }
              ]}
            />
          </Form.Item>
        </>
      );
    }
    if (inferredTaskType === "report") {
      return (
        <>
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
      return (
        <>
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

      {step === "setting" && inferredTaskType && (
        <>
          <Space style={{ marginBottom: 12 }}>
            <Typography.Text>Detected Task Type:</Typography.Text>
            <Tag color="blue">{taskTypeLabel[inferredTaskType]}</Tag>
          </Space>
          {(inferredTaskType === "data_analysis" || inferredTaskType === "code_doc") && !selectedFile && (
            <Alert
              type="warning"
              showIcon
              message="This task type requires a source file. Please go back and upload a file before running."
              style={{ marginBottom: 16 }}
            />
          )}
          <Form form={settingForm} layout="vertical" onFinish={onStart} initialValues={settingInitialValues}>
            <Form.Item label="Language" name="language" rules={[{ required: true }]}>
              <Select options={[{ label: "Chinese", value: "zh-CN" }, { label: "English", value: "en-US" }]} />
            </Form.Item>
            {renderTaskSpecificSettings()}
            <Space>
              <Button onClick={() => setStep("requirement")}>Back</Button>
              <Button htmlType="submit" type="primary">Create + Run</Button>
            </Space>
          </Form>
        </>
      )}
    </Card>
  );
}
