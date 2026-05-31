<template>
  <div>
    <div class="flex items-center gap-3 mb-4">
      <router-link to="/clusters" class="text-gray-400 hover:text-gray-600">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </router-link>
      <h2 class="text-lg font-semibold text-gray-800">{{ clusterName }}</h2>
      <span class="text-sm text-gray-400">{{ total }} 张</span>
    </div>

    <!-- 聚类增强信息 -->
    <div v-if="clusterInfo" class="mb-6 bg-white rounded-xl border border-gray-100 p-4">
      <p v-if="clusterInfo.summary_text" class="text-sm text-gray-600 mb-3">{{ clusterInfo.summary_text }}</p>
      <div v-if="clusterInfo.cover_asset_ids.length" class="flex gap-2 mb-3">
        <img
          v-for="aid in clusterInfo.cover_asset_ids"
          :key="aid"
          :src="thumbnailUrl(aid, 'sm')"
          class="w-20 h-20 object-cover rounded-lg"
        />
      </div>
      <div v-if="clusterInfo.distinct_tags.length" class="flex flex-wrap gap-1.5">
        <router-link
          v-for="tag in clusterInfo.distinct_tags"
          :key="tag"
          :to="{ path: '/explore', query: { tag } }"
          class="px-2 py-0.5 bg-gray-100 text-gray-600 rounded-full text-xs hover:bg-primary-50 hover:text-primary-700"
        >{{ tag }}</router-link>
      </div>
    </div>

    <div v-if="loading && !items.length" class="flex justify-center py-12">
      <div class="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full"></div>
    </div>
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
    <PhotoDetail />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { fetchClusterAssets, fetchClusterDetail, thumbnailUrl, type AssetBrief, type ClusterDetail } from '../api'
import PhotoGrid from '../components/gallery/PhotoGrid.vue'
import PhotoDetail from '../components/gallery/PhotoDetail.vue'

const route = useRoute()
const items = ref<AssetBrief[]>([])
const loading = ref(true)
const page = ref(1)
const totalPages = ref(1)
const total = ref(0)
const clusterName = ref('')
const clusterInfo = ref<ClusterDetail | null>(null)

async function loadMore() {
  loading.value = true
  try {
    page.value++
    const res = await fetchClusterAssets(Number(route.params.id), { page: page.value })
    items.value.push(...res.items)
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  const id = Number(route.params.id)
  try {
    const [res, detail] = await Promise.all([
      fetchClusterAssets(id, { page: 1, page_size: 100 }),
      fetchClusterDetail(id).catch(() => null),
    ])
    items.value = res.items
    total.value = res.total
    totalPages.value = res.total_pages
    clusterInfo.value = detail
    clusterName.value = detail?.cluster_name || (res.items.length > 0 ? res.items[0].cluster_name || '未分类' : '未分类')
  } finally {
    loading.value = false
  }
})
</script>
