/** 管理台路由：无登录守卫，默认进入路由管理页。 */
import { createRouter, createWebHistory } from "vue-router";
import Layout from "@/layouts/MainLayout.vue";

const routes = [
  {
    path: "/",
    component: Layout,
    children: [
      { path: "", redirect: "/routes" },
      { path: "routes", name: "routes", component: () => import("@/views/RoutesView.vue") },
      { path: "nodes", name: "nodes", component: () => import("@/views/NodesView.vue") },
      { path: "logs", name: "logs", component: () => import("@/views/LogsView.vue") },
      { path: "stats", name: "stats", component: () => import("@/views/StatsView.vue") },
      { path: "live", name: "live", component: () => import("@/views/LiveLogsView.vue") },
      { path: "config", name: "config", component: () => import("@/views/ConfigView.vue") },
    ],
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
