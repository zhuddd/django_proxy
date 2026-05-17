<template>
  <el-card>
    <template #header>
      <div class="toolbar">
        <span>WebSocket 实时日志</span>
        <el-tag :type="connected ? 'success' : 'danger'">{{ connected ? "已连接" : "未连接" }}</el-tag>
        <el-button @click="toggle">{{ connected ? "断开" : "连接" }}</el-button>
        <el-button @click="clear">清空</el-button>
      </div>
    </template>
    <div ref="logBox" class="log-box">
      <div v-for="(line, i) in lines" :key="i" class="log-line">
        <span class="ts">{{ line.ts }}</span>
        <span class="method">{{ line.method }}</span>
        <span>{{ line.path }}</span>
        <span class="muted">→ {{ line.target_url }}</span>
        <span :class="statusClass(line.status_code)">{{ line.status_code }}</span>
        <span class="muted">{{ line.latency_ms }}ms</span>
        <span class="muted">{{ line.client_ip }}</span>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from "vue";

const connected = ref(false);
const lines = ref([]);
const logBox = ref(null);
let ws = null;

function wsUrl() {
  const proto = location.protocol === "https:" ? "wss:" : "ws:";
  return `${proto}//${location.host}/ws/logs/`;
}

function connect() {
  ws = new WebSocket(wsUrl());
  ws.onopen = () => {
    connected.value = true;
  };
  ws.onclose = () => {
    connected.value = false;
  };
  ws.onmessage = (ev) => {
    const data = JSON.parse(ev.data);
    lines.value.push({ ...data, ts: new Date().toLocaleTimeString() });
    if (lines.value.length > 500) lines.value.shift();
    requestAnimationFrame(() => {
      if (logBox.value) logBox.value.scrollTop = logBox.value.scrollHeight;
    });
  };
}

function disconnect() {
  ws?.close();
  ws = null;
}

function toggle() {
  if (connected.value) disconnect();
  else connect();
}

function clear() {
  lines.value = [];
}

function statusClass(code) {
  if (!code) return "err";
  if (code >= 500) return "err";
  if (code >= 400) return "warn";
  return "ok";
}

onMounted(connect);
onUnmounted(disconnect);
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
}
.log-box {
  height: 520px;
  overflow: auto;
  background: #1e1e1e;
  color: #d4d4d4;
  font-family: ui-monospace, monospace;
  font-size: 12px;
  padding: 12px;
  border-radius: 6px;
}
.log-line {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 2px 0;
  border-bottom: 1px solid #333;
}
.ts { color: #888; }
.method { color: #4ec9b0; font-weight: 600; }
.muted { color: #888; }
.ok { color: #6a9955; }
.warn { color: #dcdcaa; }
.err { color: #f48771; }
</style>
