<template>
  <div>
    <h2 class="text-lg font-semibold text-gray-800 mb-4">时间线</h2>
    <div v-if="loading" class="flex justify-center py-12">
      <div class="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full"></div>
    </div>
    <template v-else>
      <div v-for="bucket in timeline" :key="bucket.month" class="mb-8">
        <div
          class="flex items-center gap-3 mb-3 cursor-pointer"
          @click="toggleMonth(bucket.month)"
        >
          <h3 class="text-base font-medium text-gray-700">{{ formatMonth(bucket.month) }}</h3>
          <span class="text-sm text-gray-400">{{ bucket.count }} 张</span>
        </div>
        <PhotoGrid v-if="expandedMonths.has(bucket.month)" :items="monthAssets[bucket.month] || []" />
        <!-- 收起状态显示代表图 -->
        <div v-else class="flex gap-1 overflow-hidden h-20">
          <img
            v-if="bucket.representative_id"
            :src="thumbnailUrl(bucket.representative_id, 'sm')"
            class="h-20 w-20 object-cover rounded"
          />
        </div>
      </div>
    </template>
    <PhotoDetail />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { fetchTimeline, fetchTimelineMonth, thumbnailUrl, type TimelineBucket, type AssetBrief } from '../api'
import PhotoGrid from '../components/gallery/PhotoGrid.vue'
import PhotoDetail from '../components/gallery/PhotoDetail.vue'

const timeline = ref<TimelineBucket[]>([])
const loading = ref(true)
const expandedMonths = reactive(new Set<string>())
const monthAssets = reactive<Record<string, AssetBrief[]>>({})

function formatMonth(m: string): string {
  const [year, month] = m.split('-')
  return `${year}年${parseInt(month)}月`
}

async function toggleMonth(month: string) {
  if (expandedMonths.has(month)) {
    expandedMonths.delete(month)
    return
  }
  expandedMonths.add(month)
  if (!monthAssets[month]) {
    const res = await fetchTimelineMonth(month, { page_size: 100 })
    monthAssets[month] = res.items
  }
}

onMounted(async () => {
  try {
    timeline.value = await fetchTimeline()
  } finally {
    loading.value = false
  }
})
</script>
