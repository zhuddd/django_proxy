<template>
  <el-card>
    <template #header>
      <div class="toolbar">
        <el-select v-model="filters.method" clearable placeholder="方法" style="width: 100px">
          <el-option v-for="m in methods" :key="m" :label="m" :value="m" />
        </el-select>
        <el-input v-model.number="filters.status_code" placeholder="状态码" style="width: 120px" clearable />
        <el-button type="primary" @click="load">查询</el-button>
      </div>
    </template>
    <el-table :data="logs" v-loading="loading" stripe max-height="600">
      <el-table-column prop="created_at" label="时间" width="180" />
      <el-table-column prop="method" label="方法" width="80" />
      <el-table-column prop="path" label="路径" show-overflow-tooltip />
      <el-table-column prop="target_url" label="目标 URL" show-overflow-tooltip />
      <el-table-column prop="status_code" label="状态" width="80" />
      <el-table-column prop="latency_ms" label="延迟(ms)" width="100">
        <template #default="{ row }">{{ row.latency_ms?.toFixed(1) }}</template>
      </el-table-column>
      <el-table-column prop="client_ip" label="客户端 IP" width="130" />
      <el-table-column label="详情" width="80">
        <template #default="{ row }">
          <el-button link @click="showDetail(row)">查看</el-button>
        </template>
      </el-table-column>
    </el-table>
    <div class="pager">
      <el-button :disabled="offset === 0" @click="prev">上一页</el-button>
      <el-button :disabled="logs.length < limit" @click="next">下一页</el-button>
    </div>

    <el-dialog v-model="detailVisible" title="请求详情" width="700px">
      <pre class="detail">{{ detailText }}</pre>
    </el-dialog>
  </el-card>
</template>

<script setup>
/** 分页浏览代理访问日志，支持按方法与状态码筛选。 */
import { onMounted, reactive, ref } from "vue";
import http from "@/api/http";

const methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"];
const logs = ref([]);
const loading = ref(false);
const limit = 50;
const offset = ref(0);
const filters = reactive({ method: "", status_code: null });
const detailVisible = ref(false);
const detailText = ref("");

async function load() {
  loading.value = true;
  try {
    const params = { limit, offset: offset.value };
    if (filters.method) params.method = filters.method;
    if (filters.status_code) params.status_code = filters.status_code;
    const { data } = await http.get("/logs", { params });
    logs.value = data;
  } finally {
    loading.value = false;
  }
}

function prev() {
  offset.value = Math.max(0, offset.value - limit);
  load();
}

function next() {
  offset.value += limit;
  load();
}

function showDetail(row) {
  detailText.value = JSON.stringify(row, null, 2);
  detailVisible.value = true;
}

onMounted(load);
</script>

<style scoped>
.toolbar {
  display: flex;
  gap: 8px;
}
.pager {
  margin-top: 16px;
  display: flex;
  gap: 8px;
}
.detail {
  max-height: 400px;
  overflow: auto;
  font-size: 12px;
}
</style>
