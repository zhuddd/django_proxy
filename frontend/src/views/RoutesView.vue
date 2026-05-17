<template>
  <el-card>
    <template #header>
      <div class="toolbar">
        <span>代理路由（最长前缀优先）</span>
        <el-button type="primary" @click="openDialog()">新增路由</el-button>
      </div>
    </template>
    <el-table :data="routes" v-loading="loading" stripe>
      <el-table-column prop="prefix" label="前缀" width="180" />
      <el-table-column prop="target_url" label="上游地址" />
      <el-table-column prop="enabled" label="启用" width="80">
        <template #default="{ row }">
          <el-tag :type="row.enabled ? 'success' : 'info'">{{ row.enabled ? "是" : "否" }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="说明" />
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDialog(row)">编辑</el-button>
          <el-button link type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑路由' : '新增路由'" width="520px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="路径前缀">
          <el-input v-model="form.prefix" placeholder="/account" />
        </el-form-item>
        <el-form-item label="上游 URL">
          <el-input v-model="form.target_url" placeholder="http://192.168.1.2:8000" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="form.enabled" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="form.description" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import http from "@/api/http";

const routes = ref([]);
const loading = ref(false);
const dialogVisible = ref(false);
const editing = ref(null);
const form = reactive({
  prefix: "",
  target_url: "",
  enabled: true,
  description: "",
});

async function load() {
  loading.value = true;
  try {
    const { data } = await http.get("/routes");
    routes.value = data;
  } finally {
    loading.value = false;
  }
}

function openDialog(row = null) {
  editing.value = row;
  if (row) {
    Object.assign(form, row);
  } else {
    Object.assign(form, { prefix: "", target_url: "", enabled: true, description: "" });
  }
  dialogVisible.value = true;
}

async function save() {
  try {
    if (editing.value) {
      await http.put(`/routes/${editing.value.id}`, form);
    } else {
      await http.post("/routes", form);
    }
    ElMessage.success("已保存");
    dialogVisible.value = false;
    await load();
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || "保存失败");
  }
}

async function remove(row) {
  await ElMessageBox.confirm(`删除路由 ${row.prefix}？`, "确认");
  await http.delete(`/routes/${row.id}`);
  ElMessage.success("已删除");
  await load();
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
