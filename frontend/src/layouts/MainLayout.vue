<template>
  <el-container class="layout">
    <el-aside width="220px" class="aside">
      <div class="logo">Proxy Gateway</div>
      <el-menu :default-active="route.name" router>
        <el-menu-item index="routes" :route="{ name: 'routes' }">
          <el-icon><Connection /></el-icon>
          <span>路由管理</span>
        </el-menu-item>
        <el-menu-item index="nodes" :route="{ name: 'nodes' }">
          <el-icon><Monitor /></el-icon>
          <span>节点状态</span>
        </el-menu-item>
        <el-menu-item index="logs" :route="{ name: 'logs' }">
          <el-icon><Document /></el-icon>
          <span>请求日志</span>
        </el-menu-item>
        <el-menu-item index="stats" :route="{ name: 'stats' }">
          <el-icon><TrendCharts /></el-icon>
          <span>请求统计</span>
        </el-menu-item>
        <el-menu-item index="live" :route="{ name: 'live' }">
          <el-icon><VideoPlay /></el-icon>
          <span>实时日志</span>
        </el-menu-item>
        <el-menu-item index="config" :route="{ name: 'config' }">
          <el-icon><Setting /></el-icon>
          <span>系统配置</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <span>{{ title }}</span>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
/** 管理台主布局：侧栏菜单 + 顶栏标题，无登录态。 */
import { computed } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();

const titles = {
  routes: "路由管理",
  nodes: "节点状态",
  logs: "请求日志",
  stats: "请求统计",
  live: "实时日志",
  config: "系统配置",
};

const title = computed(() => titles[route.name] || "控制台");
</script>

<style scoped>
.layout {
  height: 100vh;
}
.aside {
  background: #001529;
  color: #fff;
}
.logo {
  padding: 20px 16px;
  font-weight: 700;
  font-size: 16px;
  color: #fff;
  border-bottom: 1px solid #0d2a45;
}
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #e8e8e8;
}
.el-menu {
  border-right: none;
  background: transparent;
}
</style>
