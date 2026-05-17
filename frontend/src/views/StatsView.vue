<template>
  <div class="stats-page">
    <el-card class="toolbar-card">
      <div class="toolbar">
        <span>统计范围</span>
        <el-radio-group v-model="hours" @change="loadAll">
          <el-radio-button :value="1">1 小时</el-radio-button>
          <el-radio-button :value="6">6 小时</el-radio-button>
          <el-radio-button :value="24">24 小时</el-radio-button>
          <el-radio-button :value="168">7 天</el-radio-button>
        </el-radio-group>
        <el-button type="primary" :loading="loading" @click="loadAll">刷新</el-button>
      </div>
    </el-card>

    <el-row :gutter="16" class="summary-row">
      <el-col :span="6" v-for="card in summaryCards" :key="card.label">
        <el-card shadow="hover" class="summary-card">
          <div class="summary-label">{{ card.label }}</div>
          <div class="summary-value" :style="{ color: card.color }">{{ card.value }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :span="16">
        <el-card>
          <template #header>请求量趋势</template>
          <div ref="volumeChartRef" class="chart" v-loading="loading" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>状态码分布</template>
          <div ref="statusChartRef" class="chart" v-loading="loading" />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="row-gap">
      <el-col :span="16">
        <el-card>
          <template #header>平均延迟趋势 (ms)</template>
          <div ref="latencyChartRef" class="chart" v-loading="loading" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>请求方法</template>
          <div ref="methodChartRef" class="chart" v-loading="loading" />
        </el-card>
      </el-col>
    </el-row>

    <el-card class="row-gap">
      <template #header>热门路径 TOP10</template>
      <el-table :data="topPaths" stripe size="small">
        <el-table-column prop="path" label="路径" show-overflow-tooltip />
        <el-table-column prop="count" label="请求数" width="100" />
        <el-table-column prop="avg_latency_ms" label="平均延迟(ms)" width="120" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, shallowRef } from "vue";
import * as echarts from "echarts";
import http from "@/api/http";

const hours = ref(24);
const loading = ref(false);
const overview = ref(null);
const timeline = ref(null);
const topPaths = ref([]);

const volumeChartRef = ref(null);
const latencyChartRef = ref(null);
const statusChartRef = ref(null);
const methodChartRef = ref(null);

const charts = shallowRef([]);

const summaryCards = computed(() => {
  const o = overview.value;
  if (!o) return [];
  return [
    { label: "总请求数", value: o.total, color: "#409eff" },
    { label: "成功率", value: `${o.success_rate}%`, color: "#67c23a" },
    { label: "平均延迟", value: `${o.avg_latency_ms} ms`, color: "#e6a23c" },
    { label: "5xx 错误", value: o.server_error, color: "#f56c6c" },
  ];
});

function initChart(el) {
  if (!el) return null;
  const chart = echarts.init(el);
  charts.value.push(chart);
  return chart;
}

function resizeCharts() {
  charts.value.forEach((c) => c.resize());
}

function renderVolumeChart() {
  const chart = initChart(volumeChartRef.value);
  if (!chart || !timeline.value) return;
  const points = timeline.value.points || [];
  chart.setOption({
    tooltip: { trigger: "axis" },
    legend: { data: ["总请求", "成功", "错误"] },
    grid: { left: 48, right: 24, bottom: 32, top: 40 },
    xAxis: { type: "category", data: points.map((p) => formatBucket(p.bucket)) },
    yAxis: { type: "value", minInterval: 1 },
    series: [
      { name: "总请求", type: "line", smooth: true, data: points.map((p) => p.total), areaStyle: { opacity: 0.08 } },
      { name: "成功", type: "line", smooth: true, data: points.map((p) => p.success) },
      { name: "错误", type: "line", smooth: true, data: points.map((p) => p.error), itemStyle: { color: "#f56c6c" } },
    ],
  });
}

function renderLatencyChart() {
  const chart = initChart(latencyChartRef.value);
  if (!chart || !timeline.value) return;
  const points = timeline.value.points || [];
  chart.setOption({
    tooltip: { trigger: "axis" },
    grid: { left: 48, right: 24, bottom: 32, top: 24 },
    xAxis: { type: "category", data: points.map((p) => formatBucket(p.bucket)) },
    yAxis: { type: "value", name: "ms" },
    series: [
      {
        name: "平均延迟",
        type: "line",
        smooth: true,
        data: points.map((p) => p.avg_latency_ms),
        itemStyle: { color: "#e6a23c" },
        areaStyle: { opacity: 0.12, color: "#e6a23c" },
      },
    ],
  });
}

function renderStatusChart(data) {
  const chart = initChart(statusChartRef.value);
  if (!chart) return;
  chart.setOption({
    tooltip: { trigger: "item" },
    legend: { bottom: 0 },
    series: [
      {
        type: "pie",
        radius: ["40%", "65%"],
        data: data.map((d) => ({ name: d.label, value: d.count })),
        label: { formatter: "{b}: {c}" },
      },
    ],
  });
}

function renderMethodChart(data) {
  const chart = initChart(methodChartRef.value);
  if (!chart) return;
  chart.setOption({
    tooltip: { trigger: "axis" },
    grid: { left: 48, right: 16, bottom: 32, top: 16 },
    xAxis: { type: "category", data: data.map((d) => d.method) },
    yAxis: { type: "value", minInterval: 1 },
    series: [{ type: "bar", data: data.map((d) => d.count), itemStyle: { color: "#409eff" } }],
  });
}

function formatBucket(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  if (timeline.value?.granularity === "day") {
    return `${d.getMonth() + 1}/${d.getDate()}`;
  }
  return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}

function disposeCharts() {
  charts.value.forEach((c) => c.dispose());
  charts.value = [];
}

async function loadAll() {
  loading.value = true;
  disposeCharts();
  try {
    const params = { hours: hours.value };
    const [ov, tl, st, me, tp] = await Promise.all([
      http.get("/logs/stats/overview", { params }),
      http.get("/logs/stats/timeline", { params }),
      http.get("/logs/stats/status", { params }),
      http.get("/logs/stats/methods", { params }),
      http.get("/logs/stats/top-paths", { params }),
    ]);
    overview.value = ov.data;
    timeline.value = tl.data;
    topPaths.value = tp.data;
    renderVolumeChart();
    renderLatencyChart();
    renderStatusChart(st.data);
    renderMethodChart(me.data);
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  loadAll();
  window.addEventListener("resize", resizeCharts);
});

onUnmounted(() => {
  window.removeEventListener("resize", resizeCharts);
  disposeCharts();
});
</script>

<style scoped>
.stats-page .toolbar {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}
.summary-row {
  margin-top: 16px;
}
.summary-card {
  text-align: center;
}
.summary-label {
  font-size: 13px;
  color: #909399;
}
.summary-value {
  font-size: 28px;
  font-weight: 700;
  margin-top: 8px;
}
.row-gap {
  margin-top: 16px;
}
.chart {
  height: 320px;
  width: 100%;
}
</style>
