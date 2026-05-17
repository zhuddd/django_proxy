<template>
  <el-card>
    <template #header>系统配置</template>
    <el-table :data="configs" v-loading="loading">
      <el-table-column prop="key" label="键" width="220" />
      <el-table-column label="值">
        <template #default="{ row }">
          <el-input v-model="row.value" />
        </template>
      </el-table-column>
      <el-table-column prop="description" label="说明" />
      <el-table-column label="操作" width="100">
        <template #default="{ row }">
          <el-button type="primary" link @click="save(row)">保存</el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup>
/** 编辑 SystemConfig 键值（健康检查间隔、超时等）。 */
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import http from "@/api/http";

const configs = ref([]);
const loading = ref(false);

async function load() {
  loading.value = true;
  try {
    const { data } = await http.get("/config");
    configs.value = data;
  } finally {
    loading.value = false;
  }
}

async function save(row) {
  await http.put(`/config/${row.key}`, { value: row.value });
  ElMessage.success("已保存");
}

onMounted(load);
</script>
