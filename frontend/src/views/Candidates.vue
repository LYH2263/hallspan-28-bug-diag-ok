<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api } from '../api'
const rows = ref<any[]>([])
const papers = ref<any[]>([])
const busy = ref<Set<number>>(new Set())
const error = ref('')
onMounted(async () => {
  [rows.value, papers.value] = await Promise.all([api('/candidates'), api('/papers')])
})
async function changePaper(r: any, ev: Event) {
  const newId = Number((ev.target as HTMLSelectElement).value)
  if (newId === r.paper_id) return
  const oldId = r.paper_id
  error.value = ''
  busy.value.add(r.id)
  try {
    // 后端在同一事务内提交 套别 + 最新图 + 违规；成功前不改动本地状态。
    const res = await api(`/candidates/${r.id}`, {
      method: 'PATCH',
      body: JSON.stringify({ paper_id: newId }),
    })
    r.paper_id = res.candidate.paper_id
  } catch (e: any) {
    ;(ev.target as HTMLSelectElement).value = String(oldId) // 整体失败：还原，不接受半成功
    error.value = `「${r.name}」改试卷套失败，已全部回滚（套别、排座图、违规均未变更）`
  } finally {
    busy.value.delete(r.id)
  }
}
</script>
<template>
  <h1>考生名册</h1>
  <p class="sub">夹板名册样式 · 可修改试卷套（已有排座图时套别、最新图、违规同成功或同失败）</p>
  <p v-if="error" class="hs-error">{{ error }}</p>
  <div class="hs-clipboard" style="max-width:480px">
    <h2>考生名册 · Clipboard</h2>
    <div v-for="r in rows" :key="r.id ?? JSON.stringify(r)" class="hs-roster-row">
      <div>
        <div>{{ r.name }}</div>
        <div class="hs-ticket">{{ r.ticket_no }}</div>
      </div>
      <div class="hs-paper-edit">
        <span>室{{ r.hall_id }}</span>
        <label>
          卷套
          <select :value="r.paper_id" :disabled="busy.has(r.id)" @change="changePaper(r, $event)">
            <option v-for="p in papers" :key="p.id" :value="p.id">{{ p.code }}</option>
          </select>
        </label>
      </div>
    </div>
  </div>
</template>

<style scoped>
.hs-paper-edit { display: flex; align-items: center; gap: 0.6rem; font-size: 0.9rem; }
.hs-paper-edit select { padding: 0.15rem 0.3rem; }
.hs-error { color: #c0392b; background: #fdecea; border: 1px solid #f5c6c0; padding: 0.5rem 0.75rem; border-radius: 6px; }
</style>
