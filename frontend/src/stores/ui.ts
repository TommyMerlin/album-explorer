import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUiStore = defineStore('ui', () => {
  const sidebarCollapsed = ref(false)
  const detailModalOpen = ref(false)
  const detailAssetId = ref<number | null>(null)

  function openDetail(assetId: number) {
    detailAssetId.value = assetId
    detailModalOpen.value = true
  }

  function closeDetail() {
    detailModalOpen.value = false
    detailAssetId.value = null
  }

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  return { sidebarCollapsed, detailModalOpen, detailAssetId, openDetail, closeDetail, toggleSidebar }
})
