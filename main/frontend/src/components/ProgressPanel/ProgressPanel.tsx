import { Progress } from "antd";

export default function ProgressPanel({ percent = 0 }: { percent?: number }) {
  return <Progress percent={percent} />;
}
