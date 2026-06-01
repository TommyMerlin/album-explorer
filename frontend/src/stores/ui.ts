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
  const windowHeight = ref(window.innerHeight)
  const windowWidth = ref(window.innerWidth)

  let resizeTimer: ReturnType<typeof setTimeout> | null = null
  function onResize() {
    if (resizeTimer) clearTimeout(resizeTimer)
    resizeTimer = setTimeout(() => {
      windowHeight.value = window.innerHeight
      windowWidth.value = window.innerWidth
    }, 150)
  }
  window.addEventListener('resize', onResize)

  const computedPageSize = computed(() => {
    const sidebarWidth = sidebarCollapsed.value ? 64 : 256
    const contentWidth = windowWidth.value - sidebarWidth - 48
    const gap = 8
    const cellWidth = (contentWidth - (gridColumns.value - 1) * gap) / gridColumns.value
    const rowHeight = cellWidth + gap
    const overhead = 180
    const availableHeight = windowHeight.value - overhead
    const rows = Math.max(2, Math.floor(availableHeight / rowHeight))
    return gridColumns.value * rows
  })

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

  function removeFromList(assetId: number) {
    detailList.value = detailList.value.filter(id => id !== assetId)
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

  return { sidebarCollapsed, detailModalOpen, detailAssetId, detailList, dark, gridColumns, computedPageSize, hasPrev, hasNext, openDetail, closeDetail, removeFromList, navigatePrev, navigateNext, toggleSidebar, toggleTheme, setGridColumns }
})
