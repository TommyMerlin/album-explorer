<template>
  <Teleport to="body">
    <div
      v-if="ui.detailModalOpen"
      class="fixed inset-0 z-[100] flex items-center justify-center bg-black/70"
      @click.self="ui.closeDetail()"
    >
      <div class="relative bg-white rounded-2xl max-w-5xl w-full mx-4 max-h-[90vh] overflow-hidden flex">
        <!-- 图片区域 -->
        <div class="flex-1 bg-gray-900 flex items-center justify-center min-h-[400px]">
          <img
            v-if="detail"
            :src="fullImageUrl(detail.asset_id)"
            :alt="detail.caption_short || ''"
            class="max-w-full max-h-[85vh] object-contain"
          />
          <div v-else class="text-white">加载中...</div>
        </div>
        <!-- 信息面板 -->
        <div v-if="detail" class="w-80 p-5 overflow-y-auto border-l border-gray-200">
          <button @click="ui.closeDetail()" class="absolute top-3 right-3 p-1 hover:bg-gray-100 rounded-full">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
          <h3 class="text-base font-medium mb-3">{{ detail.caption_short }}</h3>
          <p class="text-sm text-gray-600 mb-4">{{ detail.caption_long }}</p>

          <div class="space-y-3 text-sm">
            <div v-if="detail.taken_at" class="flex items-center gap-2 text-gray-500">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
              <span>{{ detail.taken_at }}</span>
            </div>
            <div v-if="detail.city_name" class="flex items-center gap-2 text-gray-500">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/></svg>
              <span>{{ detail.province_name }} {{ detail.city_name }}</span>
            </div>
            <div v-if="detail.cluster_name" class="flex items-center gap-2 text-gray-500">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/></svg>
              <span>{{ detail.cluster_name }}</span>
            </div>
          </div>

          <div v-if="detail.tags.length" class="mt-4">
            <h4 class="text-xs font-medium text-gray-400 uppercase mb-2">标签</h4>
            <div class="flex flex-wrap gap-1.5">
              <span
                v-for="tag in detail.tags"
                :key="tag"
                class="px-2 py-0.5 bg-gray-100 text-gray-600 rounded-full text-xs"
              >{{ tag }}</span>
            </div>
          </div>

          <div v-if="detail.activities.length" class="mt-4">
            <h4 class="text-xs font-medium text-gray-400 uppercase mb-2">活动</h4>
            <p class="text-sm text-gray-600">{{ detail.activities.join('、') }}</p>
          </div>

          <div v-if="detail.main_subjects.length" class="mt-4">
            <h4 class="text-xs font-medium text-gray-400 uppercase mb-2">主体</h4>
            <p class="text-sm text-gray-600">{{ detail.main_subjects.join('、') }}</p>
          </div>

          <div class="mt-4 pt-3 border-t border-gray-100">
            <p class="text-xs text-gray-400 break-all">{{ detail.rel_path }}</p>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { watch, ref } from 'vue'
import { useUiStore } from '../../stores/ui'
import { fetchAssetDetail, fullImageUrl, type AssetDetail } from '../../api'

const ui = useUiStore()
const detail = ref<AssetDetail | null>(null)

watch(() => ui.detailAssetId, async (id) => {
  if (id !== null) {
    detail.value = null
    detail.value = await fetchAssetDetail(id)
  }
})
</script>
