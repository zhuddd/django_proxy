<template>
  <div class="login-page">
    <el-card class="login-card">
      <h2>透明反向代理网关</h2>
      <el-form :model="form" @submit.prevent="onSubmit">
        <el-form-item label="用户名">
          <el-input v-model="form.username" autocomplete="username" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" show-password autocomplete="current-password" />
        </el-form-item>
        <el-button type="primary" native-type="submit" :loading="loading" style="width: 100%">
          登录
        </el-button>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { useAuthStore } from "@/stores/auth";

const router = useRouter();
const auth = useAuthStore();
const loading = ref(false);
const form = reactive({ username: "admin", password: "" });

async function onSubmit() {
  loading.value = true;
  try {
    await auth.login(form.username, form.password);
    ElMessage.success("登录成功");
    router.push({ name: "routes" });
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || "登录失败");
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a2a6c, #2d6a8f);
}
.login-card {
  width: 380px;
  padding: 12px;
}
h2 {
  text-align: center;
  margin-bottom: 24px;
}
</style>
