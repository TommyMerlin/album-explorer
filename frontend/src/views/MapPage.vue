<template>
  <div class="h-[calc(100vh-57px-48px)] flex flex-col">
    <h2 class="text-lg font-semibold text-gray-800 mb-4">地图视图</h2>
    <div class="flex-1 rounded-xl overflow-hidden border border-gray-200">
      <div ref="mapContainer" class="w-full h-full"></div>
    </div>
    <PhotoDetail />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { fetchMapPoints, thumbnailUrl, type MapPoint } from '../api'
import { useUiStore } from '../stores/ui'
import PhotoDetail from '../components/gallery/PhotoDetail.vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import 'leaflet.markercluster'
import 'leaflet.markercluster/dist/MarkerCluster.css'
import 'leaflet.markercluster/dist/MarkerCluster.Default.css'

const mapContainer = ref<HTMLElement | null>(null)
const ui = useUiStore()
const router = useRouter()
let map: L.Map | null = null

onMounted(async () => {
  if (!mapContainer.value) return

  map = L.map(mapContainer.value).setView([35.86, 104.19], 5)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 18,
  }).addTo(map)

  const points = await fetchMapPoints({ limit: 5000 })

  // @ts-ignore
  const markers = L.markerClusterGroup({
    chunkedLoading: true,
    maxClusterRadius: 60,
  })

  for (const p of points) {
    const marker = L.marker([p.lat, p.lng])
    marker.bindPopup(`
      <div style="text-align:center">
        <img src="${thumbnailUrl(p.asset_id, 'sm')}" style="width:120px;height:120px;object-fit:cover;border-radius:8px;margin-bottom:4px" />
        <p style="font-size:12px;margin:0">${p.caption_short || ''}</p>
      </div>
    `)
    marker.on('click', () => {
      ui.openDetail(p.asset_id)
    })
    markers.addLayer(marker)
  }

  // 聚合簇点击：获取视口范围跳转到 /explore
  markers.on('clusterclick', (e: any) => {
    const bounds = e.layer.getBounds()
    const south = bounds.getSouth()
    const north = bounds.getNorth()
    const west = bounds.getWest()
    const east = bounds.getEast()
    if (e.layer.getChildCount() <= 20) return
    router.push({
      path: '/explore',
      query: { has_gps: 'true' },
    })
  })

  map.addLayer(markers)
})

onUnmounted(() => {
  if (map) {
    map.remove()
    map = null
  }
})
</script>
