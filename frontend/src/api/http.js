import axios from "axios";
import { useAuthStore } from "@/stores/auth";
import router from "@/router";

const http = axios.create({
  baseURL: "/api",
  timeout: 30000,
});

http.interceptors.request.use((config) => {
  const auth = useAuthStore();
  if (auth.token) {
    config.headers.Authorization = `Bearer ${auth.token}`;
  }
  return config;
});

http.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      const auth = useAuthStore();
      auth.logout();
      router.push({ name: "login" });
    }
    return Promise.reject(err);
  }
);

export default http;
