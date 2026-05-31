import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useUiStore = defineStore('ui', () => {
  const sidebarCollapsed = ref(false)
  const detailModalOpen = ref(false)
  const detailAssetId = ref<number | null>(null)
  const detailList = ref<number[]>([])
  const dark = ref(
    localStorage.getItem('theme')
      ? localStorage.getItem('theme') === 'dark'
      : window.matchMedia('(prefers-color-scheme: dark)').matches
  )
  const gridColumns = ref(Number(localStorage.getItem('gridColumns')) || 6)

  const detailIndex = computed(() => {
    if (detailAssetId.value === null) return -1
    return detailList.value.indexOf(detailAssetId.value)
  })

  const hasPrev = computed(() => detailIndex.value > 0)
  const hasNext = computed(() => detailIndex.value >= 0 && detailIndex.value < detailList.value.length - 1)

  function applyTheme() {
    document.documentElement.classList.toggle('dark', dark.value)
  }
  applyTheme()

  function toggleTheme() {
    dark.value = !dark.value
    localStorage.setItem('theme', dark.value ? 'dark' : 'light')
    applyTheme()
  }

  function setGridColumns(n: number) {
    gridColumns.value = Math.max(4, Math.min(12, n))
    localStorage.setItem('gridColumns', String(gridColumns.value))
  }

  function openDetail(assetId: number, list?: number[]) {
    detailAssetId.value = assetId
    detailModalOpen.value = true
    if (list) detailList.value = list
  }

  function closeDetail() {
    detailModalOpen.value = false
    detailAssetId.value = null
  }

  function navigatePrev() {
    if (hasPrev.value) {
      detailAssetId.value = detailList.value[detailIndex.value - 1]
    }
  }

  function navigateNext() {
    if (hasNext.value) {
      detailAssetId.value = detailList.value[detailIndex.value + 1]
    }
  }

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  return { sidebarCollapsed, detailModalOpen, detailAssetId, detailList, dark, gridColumns, hasPrev, hasNext, openDetail, closeDetail, navigatePrev, navigateNext, toggleSidebar, toggleTheme, setGridColumns }
})
