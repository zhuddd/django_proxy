import { defineStore } from "pinia";
import http from "@/api/http";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    token: localStorage.getItem("token") || "",
    username: localStorage.getItem("username") || "",
  }),
  getters: {
    isLoggedIn: (s) => !!s.token,
  },
  actions: {
    async login(username, password) {
      const { data } = await http.post("/auth/login", { username, password });
      this.token = data.access_token;
      this.username = data.username;
      localStorage.setItem("token", this.token);
      localStorage.setItem("username", this.username);
    },
    logout() {
      this.token = "";
      this.username = "";
      localStorage.removeItem("token");
      localStorage.removeItem("username");
    },
  },
});
