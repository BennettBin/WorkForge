import { Upload } from "antd";

export default function FileUploader() {
  return <Upload.Dragger multiple={false}>Drop file here</Upload.Dragger>;
}
