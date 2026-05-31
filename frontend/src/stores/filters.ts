import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface ExploreQuery {
  q?: string
  month?: string
  city?: string
  province?: string
  cluster_id?: number
  tag?: string
  date_from?: string
  date_to?: string
  has_gps?: boolean
  sort_by?: string
  order?: string
  page?: number
  page_size?: number
}

export const useFiltersStore = defineStore('filters', () => {
  const q = ref<string>('')
  const selectedMonth = ref<string | null>(null)
  const selectedCity = ref<string | null>(null)
  const selectedProvince = ref<string | null>(null)
  const selectedClusterId = ref<number | null>(null)
  const selectedTag = ref<string | null>(null)
  const dateFrom = ref<string | null>(null)
  const dateTo = ref<string | null>(null)
  const hasGps = ref<boolean | null>(null)
  const sortBy = ref<string>('taken_at')
  const order = ref<string>('desc')
  const page = ref<number>(1)
  const pageSize = ref<number>(50)

  const activeParams = computed<Record<string, any>>(() => {
    const params: Record<string, any> = {}
    if (q.value) params.q = q.value
    if (selectedMonth.value) params.month = selectedMonth.value
    if (selectedCity.value) params.city = selectedCity.value
    if (selectedProvince.value) params.province = selectedProvince.value
    if (selectedClusterId.value !== null) params.cluster_id = selectedClusterId.value
    if (selectedTag.value) params.tag = selectedTag.value
    if (dateFrom.value) params.date_from = dateFrom.value
    if (dateTo.value) params.date_to = dateTo.value
    if (hasGps.value !== null) params.has_gps = hasGps.value
    if (sortBy.value !== 'taken_at') params.sort_by = sortBy.value
    if (order.value !== 'desc') params.order = order.value
    params.page = page.value
    params.page_size = pageSize.value
    return params
  })

  const hasFilters = computed(() => {
    return !!(q.value || selectedMonth.value || selectedCity.value || selectedProvince.value ||
      selectedClusterId.value !== null || selectedTag.value ||
      dateFrom.value || dateTo.value || hasGps.value !== null)
  })

  function applyFromRoute(query: Record<string, any>) {
    q.value = query.q || ''
    selectedMonth.value = query.month || null
    selectedCity.value = query.city || null
    selectedProvince.value = query.province || null
    selectedClusterId.value = query.cluster_id ? Number(query.cluster_id) : null
    selectedTag.value = query.tag || null
    dateFrom.value = query.date_from || null
    dateTo.value = query.date_to || null
    hasGps.value = query.has_gps === 'true' ? true : query.has_gps === 'false' ? false : null
    sortBy.value = query.sort_by || 'taken_at'
    order.value = query.order || 'desc'
    page.value = query.page ? Number(query.page) : 1
    pageSize.value = query.page_size ? Number(query.page_size) : 50
  }

  function toRouteQuery(): Record<string, string> {
    const rq: Record<string, string> = {}
    if (q.value) rq.q = q.value
    if (selectedMonth.value) rq.month = selectedMonth.value
    if (selectedCity.value) rq.city = selectedCity.value
    if (selectedProvince.value) rq.province = selectedProvince.value
    if (selectedClusterId.value !== null) rq.cluster_id = String(selectedClusterId.value)
    if (selectedTag.value) rq.tag = selectedTag.value
    if (dateFrom.value) rq.date_from = dateFrom.value
    if (dateTo.value) rq.date_to = dateTo.value
    if (hasGps.value !== null) rq.has_gps = String(hasGps.value)
    if (sortBy.value !== 'taken_at') rq.sort_by = sortBy.value
    if (order.value !== 'desc') rq.order = order.value
    if (page.value > 1) rq.page = String(page.value)
    if (pageSize.value !== 50) rq.page_size = String(pageSize.value)
    return rq
  }

  function setFilter(params: Partial<ExploreQuery>) {
    if (params.q !== undefined) q.value = params.q || ''
    if (params.month !== undefined) selectedMonth.value = params.month || null
    if (params.city !== undefined) selectedCity.value = params.city || null
    if (params.province !== undefined) selectedProvince.value = params.province || null
    if (params.cluster_id !== undefined) selectedClusterId.value = params.cluster_id ?? null
    if (params.tag !== undefined) selectedTag.value = params.tag || null
    if (params.date_from !== undefined) dateFrom.value = params.date_from || null
    if (params.date_to !== undefined) dateTo.value = params.date_to || null
    if (params.has_gps !== undefined) hasGps.value = params.has_gps ?? null
    if (params.sort_by !== undefined) sortBy.value = params.sort_by || 'taken_at'
    if (params.order !== undefined) order.value = params.order || 'desc'
    if (params.page !== undefined) page.value = params.page || 1
    if (params.page_size !== undefined) pageSize.value = params.page_size || 50
    // 切换筛选条件时重置页码
    if (params.page === undefined) page.value = 1
  }

  function clearAll() {
    q.value = ''
    selectedMonth.value = null
    selectedCity.value = null
    selectedProvince.value = null
    selectedClusterId.value = null
    selectedTag.value = null
    dateFrom.value = null
    dateTo.value = null
    hasGps.value = null
    sortBy.value = 'taken_at'
    order.value = 'desc'
    page.value = 1
    pageSize.value = 50
  }

  return {
    q, selectedMonth, selectedCity, selectedProvince, selectedClusterId,
    selectedTag, dateFrom, dateTo, hasGps, sortBy, order, page, pageSize,
    activeParams, hasFilters,
    applyFromRoute, toRouteQuery, setFilter, clearAll,
  }
})
