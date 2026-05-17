/**
 * 管理 API HTTP 客户端。
 * 后端未启用登录鉴权，无需附加 Token。
 */
import axios from "axios";

const http = axios.create({
  baseURL: "/api",
  timeout: 30000,
});

export default http;
