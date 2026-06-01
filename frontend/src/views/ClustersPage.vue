<template>
  <div>
    <h2 class="text-lg font-semibold text-gray-800 mb-4">{{ $t('clusters.title') }}</h2>
    <div v-if="loading" class="flex justify-center py-12">
      <div class="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full"></div>
    </div>
    <div v-else-if="!clusters.length" class="text-center py-12 text-gray-400">
      <p>{{ $t('clusters.empty') }}</p>
      <p class="text-sm mt-1">{{ $t('clusters.emptyHint') }}</p>
    </div>
    <div v-else class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
      <router-link
        v-for="cluster in clusters"
        :key="cluster.cluster_id"
        :to="`/clusters/${cluster.cluster_id}`"
        class="group bg-white rounded-xl overflow-hidden border border-gray-100 shadow-sm hover:shadow-md transition-shadow"
      >
        <div class="aspect-[4/3] bg-gray-100 overflow-hidden">
          <img
            v-if="cluster.representative_asset_id"
            :src="thumbnailUrl(cluster.representative_asset_id, 'md')"
            class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
        </div>
        <div class="p-3">
          <h3 class="text-sm font-medium text-gray-800 line-clamp-1">{{ cluster.cluster_name }}</h3>
          <p class="text-xs text-gray-400 mt-1">{{ $t('common.photos', { count: cluster.asset_count }) }}</p>
          <div v-if="cluster.top_tags.length" class="flex flex-wrap gap-1 mt-2">
            <span
              v-for="tag in cluster.top_tags.slice(0, 3)"
              :key="tag"
              class="px-1.5 py-0.5 bg-gray-50 text-gray-500 rounded text-[10px]"
            >{{ tag }}</span>
          </div>
        </div>
      </router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { fetchClusters, thumbnailUrl, type ClusterInfo } from '../api'

const clusters = ref<ClusterInfo[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    clusters.value = await fetchClusters()
  } finally {
    loading.value = false
  }
})
</script>
