import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import Layout from "@/layouts/MainLayout.vue";

const routes = [
  {
    path: "/login",
    name: "login",
    component: () => import("@/views/LoginView.vue"),
    meta: { public: true },
  },
  {
    path: "/",
    component: Layout,
    children: [
      { path: "", redirect: "/routes" },
      { path: "routes", name: "routes", component: () => import("@/views/RoutesView.vue") },
      { path: "nodes", name: "nodes", component: () => import("@/views/NodesView.vue") },
      { path: "logs", name: "logs", component: () => import("@/views/LogsView.vue") },
      { path: "live", name: "live", component: () => import("@/views/LiveLogsView.vue") },
      { path: "config", name: "config", component: () => import("@/views/ConfigView.vue") },
    ],
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to) => {
  const auth = useAuthStore();
  if (!to.meta.public && !auth.isLoggedIn) {
    return { name: "login" };
  }
  if (to.name === "login" && auth.isLoggedIn) {
    return { name: "routes" };
  }
});

export default router;
