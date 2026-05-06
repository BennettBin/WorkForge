import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { ConfigProvider } from "antd";
import App from "./App";
import { AppStoreProvider } from "./store/appStore";
import "./styles/global.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ConfigProvider>
      <AppStoreProvider>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </AppStoreProvider>
    </ConfigProvider>
  </React.StrictMode>
);
