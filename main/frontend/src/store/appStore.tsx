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
};

type AppStoreValue = {
  auth: AuthState;
  task: TaskState;
  setAuth: (next: AuthState) => void;
  setTask: (next: TaskState) => void;
};

const AppStoreContext = createContext<AppStoreValue | null>(null);

export function AppStoreProvider({ children }: { children: React.ReactNode }) {
  const [auth, setAuth] = useState<AuthState>({
    userId: localStorage.getItem("wf_user_id"),
    username: localStorage.getItem("wf_username"),
    email: localStorage.getItem("wf_email"),
    token: localStorage.getItem("wf_token")
  });
  const [task, setTask] = useState<TaskState>({ activeTaskId: null, activeTaskStatus: null });

  const value = useMemo(() => ({ auth, task, setAuth, setTask }), [auth, task]);

  return <AppStoreContext.Provider value={value}>{children}</AppStoreContext.Provider>;
}

export function useAppStore() {
  const context = useContext(AppStoreContext);
  if (!context) {
    throw new Error("useAppStore must be used within AppStoreProvider.");
  }
  return context;
}
