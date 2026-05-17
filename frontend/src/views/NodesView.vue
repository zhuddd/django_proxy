<template>
  <el-card>
    <template #header>
      <div class="toolbar">
        <span>上游节点健康状态</span>
        <el-button @click="checkAll" :loading="checking">立即检测</el-button>
      </div>
    </template>
    <el-table :data="nodes" v-loading="loading" stripe>
      <el-table-column prop="route_prefix" label="路由前缀" width="160" />
      <el-table-column prop="target_url" label="上游" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_online ? 'success' : 'danger'">
            {{ row.is_online ? "在线" : "离线" }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="response_time_ms" label="响应(ms)" width="120">
        <template #default="{ row }">
          {{ row.response_time_ms != null ? row.response_time_ms.toFixed(1) : "-" }}
        </template>
      </el-table-column>
      <el-table-column prop="last_check" label="上次检测" width="180" />
      <el-table-column prop="error_message" label="错误" show-overflow-tooltip />
    </el-table>
  </el-card>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import http from "@/api/http";

const nodes = ref([]);
const loading = ref(false);
const checking = ref(false);

async function load() {
  loading.value = true;
  try {
    const { data } = await http.get("/nodes");
    nodes.value = data;
  } finally {
    loading.value = false;
  }
}

async function checkAll() {
  checking.value = true;
  try {
    await http.post("/nodes/check");
    ElMessage.success("检测完成");
    await load();
  } finally {
    checking.value = false;
  }
}

onMounted(load);
</script>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
