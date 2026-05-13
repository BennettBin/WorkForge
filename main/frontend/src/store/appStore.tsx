import { createContext, useContext, useMemo, useState } from "react";

type AuthState = {
  userId: string | null;
  username: string | null;
  email: string | null;
  token: string | null;
};

type TaskState = {
  activeTaskId: string | null;
  activeTaskStatus: string | null;
  runningTasks: RunningTask[];
  selectedRunningTaskId: string | null;
};

export type RunningTask = {
  taskId: string;
  status: string;
  taskType?: string;
  title?: string;
  updatedAt?: string;
};

type TemplateGenerationDraft = {
  requirement: string;
  file: File | null;
  inferredSettings?: {
    templateType?: "ppt" | "wechat_post" | "report";
    templateName?: string;
    language?: "zh-CN" | "en-US";
    templateIntent?: string;
    targetAudience?: string;
  };
};

type AppStoreValue = {
  auth: AuthState;
  task: TaskState;
  templateGenerationDraft: TemplateGenerationDraft;
  setAuth: (next: AuthState) => void;
  setTask: React.Dispatch<React.SetStateAction<TaskState>>;
  upsertRunningTask: (task: RunningTask) => void;
  removeRunningTask: (taskId: string) => void;
  setSelectedRunningTaskId: (taskId: string | null) => void;
  hydrateRunningTasks: (tasks: RunningTask[]) => void;
  setTemplateGenerationDraft: (next: TemplateGenerationDraft) => void;
};

const AppStoreContext = createContext<AppStoreValue | null>(null);

export function AppStoreProvider({ children }: { children: React.ReactNode }) {
  const [auth, setAuth] = useState<AuthState>({
    userId: localStorage.getItem("wf_user_id"),
    username: localStorage.getItem("wf_username"),
    email: localStorage.getItem("wf_email"),
    token: localStorage.getItem("wf_token")
  });
  const [task, setTask] = useState<TaskState>({
    activeTaskId: null,
    activeTaskStatus: null,
    runningTasks: [],
    selectedRunningTaskId: null,
  });
  const [templateGenerationDraft, setTemplateGenerationDraft] = useState<TemplateGenerationDraft>({ requirement: "", file: null, inferredSettings: {} });

  function upsertRunningTask(nextTask: RunningTask) {
    setTask((prev) => {
      const list = [...prev.runningTasks];
      const idx = list.findIndex((x) => x.taskId === nextTask.taskId);
      if (idx >= 0) {
        list[idx] = { ...list[idx], ...nextTask };
      } else {
        list.unshift(nextTask);
      }
      return {
        ...prev,
        runningTasks: list.slice(0, 10),
      };
    });
  }

  function removeRunningTask(taskId: string) {
    setTask((prev) => {
      const list = prev.runningTasks.filter((x) => x.taskId !== taskId);
      const selected = prev.selectedRunningTaskId === taskId ? null : prev.selectedRunningTaskId;
      const activeId = prev.activeTaskId === taskId ? (list[0]?.taskId ?? null) : prev.activeTaskId;
      const activeStatus = prev.activeTaskId === taskId ? (list[0]?.status ?? null) : prev.activeTaskStatus;
      return {
        ...prev,
        runningTasks: list,
        selectedRunningTaskId: selected,
        activeTaskId: activeId,
        activeTaskStatus: activeStatus,
      };
    });
  }

  function setSelectedRunningTaskId(taskId: string | null) {
    setTask((prev) => ({ ...prev, selectedRunningTaskId: taskId }));
  }

  function hydrateRunningTasks(tasks: RunningTask[]) {
    setTask((prev) => {
      const currentSelected = prev.selectedRunningTaskId;
      const selectedStillExists = currentSelected ? tasks.some((x) => x.taskId === currentSelected) : false;
      const fallbackSelected = selectedStillExists ? currentSelected : (tasks[0]?.taskId ?? null);
      return {
        ...prev,
        runningTasks: tasks.slice(0, 10),
        selectedRunningTaskId: fallbackSelected,
      };
    });
  }

  const value = useMemo(
    () => ({
      auth,
      task,
      templateGenerationDraft,
      setAuth,
      setTask,
      upsertRunningTask,
      removeRunningTask,
      setSelectedRunningTaskId,
      hydrateRunningTasks,
      setTemplateGenerationDraft,
    }),
    [auth, task, templateGenerationDraft]
  );

  return <AppStoreContext.Provider value={value}>{children}</AppStoreContext.Provider>;
}

export function useAppStore() {
  const context = useContext(AppStoreContext);
  if (!context) {
    throw new Error("useAppStore must be used within AppStoreProvider.");
  }
  return context;
}
