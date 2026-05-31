<template>
  <div>
    <h2 class="text-lg font-semibold text-gray-800 mb-4">
      搜索<span v-if="query" class="text-gray-400 font-normal">：{{ query }}</span>
    </h2>
    <div v-if="loading && !items.length" class="flex justify-center py-12">
      <div class="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full"></div>
    </div>
    <div v-else-if="searched && !items.length" class="text-center py-12 text-gray-400">
      没有找到匹配的图片
    </div>
    <template v-else>
      <p class="text-sm text-gray-400 mb-4">找到 {{ total }} 个结果</p>
      <PhotoGrid :items="items" />
      <div v-if="page < totalPages" class="flex justify-center mt-6">
        <button
          @click="loadMore"
          :disabled="loading"
          class="px-6 py-2 bg-primary-500 text-white rounded-full text-sm hover:bg-primary-600 disabled:opacity-50"
        >
          {{ loading ? '加载中...' : '加载更多' }}
        </button>
      </div>
    </template>
    <PhotoDetail />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { searchAssets, type AssetBrief } from '../api'
import PhotoGrid from '../components/gallery/PhotoGrid.vue'
import PhotoDetail from '../components/gallery/PhotoDetail.vue'

const route = useRoute()
const items = ref<AssetBrief[]>([])
const loading = ref(false)
const searched = ref(false)
const query = ref('')
const page = ref(1)
const totalPages = ref(1)
const total = ref(0)

async function doSearch(q: string) {
  if (!q.trim()) return
  query.value = q
  loading.value = true
  searched.value = true
  page.value = 1
  try {
    const res = await searchAssets(q, { page: 1, page_size: 50 })
    items.value = res.items
    total.value = res.total
    totalPages.value = res.total_pages
  } finally {
    loading.value = false
  }
}

async function loadMore() {
  loading.value = true
  try {
    page.value++
    const res = await searchAssets(query.value, { page: page.value })
    items.value.push(...res.items)
  } finally {
    loading.value = false
  }
}

watch(() => route.query.q, (q) => {
  if (q) doSearch(q as string)
}, { immediate: true })

onMounted(() => {
  if (route.query.q) doSearch(route.query.q as string)
})
</script>
