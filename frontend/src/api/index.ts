import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

export interface AssetBrief {
  asset_id: number
  rel_path: string
  asset_type: string
  source_format: string
  taken_at: string | null
  city_name: string | null
  province_name: string | null
  cluster_id: number | null
  cluster_name: string | null
  caption_short: string | null
  scene: string | null
  tags: string[]
  people_count: number | null
  gps_lat: number | null
  gps_lng: number | null
  month_bucket: string | null
}

export interface AssetDetail extends AssetBrief {
  caption_long: string | null
  activities: string[]
  main_subjects: string[]
  style_labels: string[]
  ocr_text: string | null
  confidence: number | null
  quality_flags: string[]
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface TimelineBucket {
  month: string
  count: number
  representative_id: number | null
}

export interface ClusterInfo {
  cluster_id: number
  cluster_name: string
  asset_count: number
  representative_asset_id: number | null
  top_tags: string[]
}

export interface MapPoint {
  asset_id: number
  lat: number
  lng: number
  caption_short: string | null
}

export interface TagNode {
  tag: string
  count: number
}

export interface TagEdge {
  source: string
  target: string
  weight: number
}

export interface TagGraph {
  nodes: TagNode[]
  edges: TagEdge[]
}

export interface StatsOverview {
  total: number
  with_time: number
  with_gps: number
  with_city: number
  cluster_count: number
  month_range: string[]
  top_cities: { city: string; count: number }[]
}

export function thumbnailUrl(assetId: number, size: 'sm' | 'md' = 'sm'): string {
  // 直接走静态文件，绕过路由逻辑，加载更快
  return `/static/thumbs/${size}/${assetId}.webp`
}

export function fullImageUrl(assetId: number): string {
  return `/api/thumbnails/image/${assetId}`
}

export async function fetchAssets(params: Record<string, any> = {}) {
  const res = await api.get<PaginatedResponse<AssetBrief>>('/assets', { params })
  return res.data
}

export async function fetchAssetDetail(id: number) {
  const res = await api.get<AssetDetail>(`/assets/${id}`)
  return res.data
}

export interface AssetContext {
  same_cluster: AssetBrief[]
  cluster_name?: string
  shared_tags: AssetBrief[]
}

export async function fetchAssetContext(id: number) {
  const res = await api.get<AssetContext>(`/assets/${id}/context`)
  return res.data
}

export async function fetchSimilarAssets(id: number, limit = 12) {
  const res = await api.get<AssetBrief[]>(`/assets/${id}/similar`, { params: { limit } })
  return res.data
}

export interface ClusterDetail {
  cluster_id: number
  cluster_name: string
  asset_count: number
  representative_asset_id: number | null
  top_tags: string[]
  summary_text: string | null
  cover_asset_ids: number[]
  top_scenes: string[]
  distinct_tags: string[]
}

export async function fetchClusterDetail(id: number) {
  const res = await api.get<ClusterDetail>(`/clusters/${id}/detail`)
  return res.data
}

export async function fetchTimeline() {
  const res = await api.get<TimelineBucket[]>('/timeline')
  return res.data
}

export async function fetchTimelineMonth(month: string, params: Record<string, any> = {}) {
  const res = await api.get<PaginatedResponse<AssetBrief>>(`/timeline/${month}`, { params })
  return res.data
}

export async function fetchMapPoints(params: Record<string, any> = {}) {
  const res = await api.get<MapPoint[]>('/map/points', { params })
  return res.data
}

export interface CityAggregate {
  city: string
  province: string
  count: number
  lat: number
  lng: number
  representative_asset_id: number
}

export async function fetchMapCities() {
  const res = await api.get<CityAggregate[]>('/map/cities')
  return res.data
}

export async function fetchClusters() {
  const res = await api.get<ClusterInfo[]>('/clusters')
  return res.data
}

export async function fetchClusterAssets(id: number, params: Record<string, any> = {}) {
  const res = await api.get<PaginatedResponse<AssetBrief>>(`/clusters/${id}`, { params })
  return res.data
}

export async function searchAssets(q: string, params: Record<string, any> = {}) {
  const res = await api.get<PaginatedResponse<AssetBrief>>('/search', { params: { q, ...params } })
  return res.data
}

export async function fetchTags(topN = 100) {
  const res = await api.get<TagNode[]>('/tags', { params: { top_n: topN } })
  return res.data
}

export async function fetchTagGraph(minWeight = 10) {
  const res = await api.get<TagGraph>('/tags/graph', { params: { min_weight: minWeight } })
  return res.data
}

export async function fetchStats() {
  const res = await api.get<StatsOverview>('/stats')
  return res.data
}

export interface SavedSearch {
  id: number
  name: string
  query_json: Record<string, any>
  created_at: string
  updated_at: string
}

export async function fetchSavedSearches() {
  const res = await api.get<SavedSearch[]>('/saved-searches')
  return res.data
}

export async function createSavedSearch(name: string, query_json: Record<string, any>) {
  const res = await api.post<SavedSearch>('/saved-searches', { name, query_json })
  return res.data
}

export async function deleteSavedSearch(id: number) {
  await api.delete(`/saved-searches/${id}`)
}

export default api
