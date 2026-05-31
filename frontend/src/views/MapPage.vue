<template>
  <div class="h-[calc(100vh-57px-48px)] flex flex-col">
    <h2 class="text-lg font-semibold text-gray-800 mb-4">地图视图</h2>
    <div class="flex-1 rounded-xl overflow-hidden border border-gray-200 relative">
      <div ref="mapContainer" class="w-full h-full"></div>
      <!-- 聚合点击后的图片面板 -->
      <div
        v-if="clusterPhotos.length"
        class="absolute bottom-0 left-0 right-0 bg-white border-t border-gray-200 p-3 z-[500] max-h-[40%] overflow-y-auto"
      >
        <div class="flex items-center justify-between mb-2">
          <span class="text-sm text-gray-500">{{ clusterPhotos.length }} 张图片</span>
          <button @click="clusterPhotos = []" class="text-xs text-gray-400 hover:text-gray-600">关闭</button>
        </div>
        <div class="grid grid-cols-6 md:grid-cols-8 lg:grid-cols-10 gap-1">
          <img
            v-for="p in clusterPhotos"
            :key="p.asset_id"
            :src="thumbnailUrl(p.asset_id, 'sm')"
            class="w-full aspect-square object-cover rounded cursor-pointer hover:opacity-80"
            @click="ui.openDetail(p.asset_id)"
          />
        </div>
      </div>
    </div>
    <PhotoDetail />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { fetchMapPoints, fetchMapCities, thumbnailUrl, type MapPoint, type CityAggregate } from '../api'
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
const clusterPhotos = ref<{asset_id: number}[]>([])
let map: L.Map | null = null
let cityLayer: L.LayerGroup | null = null
let pointLayer: any = null

function addCityLayer(cities: CityAggregate[]) {
  if (!map) return
  cityLayer = L.layerGroup()
  for (const c of cities) {
    const size = Math.max(30, Math.min(60, 20 + Math.sqrt(c.count) * 3))
    const icon = L.divIcon({
      className: 'city-marker',
      html: `<div style="width:${size}px;height:${size}px;border-radius:50%;background:rgba(14,165,233,0.8);display:flex;align-items:center;justify-content:center;color:white;font-size:11px;font-weight:600;border:2px solid white;box-shadow:0 2px 6px rgba(0,0,0,0.3)">${c.count}</div>`,
      iconSize: [size, size],
      iconAnchor: [size / 2, size / 2],
    })
    const marker = L.marker([c.lat, c.lng], { icon })
    marker.bindTooltip(`${c.city}（${c.count}张）`, { direction: 'top' })
    marker.on('click', () => {
      router.push({ path: '/explore', query: { city: c.city } })
    })
    cityLayer.addLayer(marker)
  }
  cityLayer.addTo(map)
}

function addPointLayer(points: MapPoint[]) {
  if (!map) return
  // @ts-ignore
  pointLayer = L.markerClusterGroup({
    chunkedLoading: true,
    maxClusterRadius: 60,
    zoomToBoundsOnClick: false,
    spiderfyOnMaxZoom: false,
  })

  for (const p of points) {
    const marker = L.circleMarker([p.lat, p.lng], {
      radius: 6,
      fillColor: '#0ea5e9',
      fillOpacity: 0.8,
      color: '#fff',
      weight: 2,
    })
    if (p.caption_short) {
      marker.bindTooltip(p.caption_short, { direction: 'top', offset: [0, -8] })
    }
    // 存储 asset_id 供聚合点击使用
    ;(marker as any)._assetId = p.asset_id
    marker.on('click', (e) => {
      L.DomEvent.stopPropagation(e)
      ui.openDetail(p.asset_id)
    })
    pointLayer.addLayer(marker)
  }

  // 聚合数字点击：收集该簇内所有图片，展示在底部面板
  pointLayer.on('clusterclick', (e: any) => {
    const childMarkers = e.layer.getAllChildMarkers()
    const ids = childMarkers.map((m: any) => ({ asset_id: m._assetId })).filter((x: any) => x.asset_id)
    clusterPhotos.value = ids
  })
}

function updateLayers() {
  if (!map || !cityLayer || !pointLayer) return
  const zoom = map.getZoom()
  if (zoom >= 8) {
    if (!map.hasLayer(pointLayer)) map.addLayer(pointLayer)
    if (map.hasLayer(cityLayer)) map.removeLayer(cityLayer)
  } else {
    if (!map.hasLayer(cityLayer)) map.addLayer(cityLayer)
    if (map.hasLayer(pointLayer)) map.removeLayer(pointLayer)
  }
}

onMounted(async () => {
  if (!mapContainer.value) return

  map = L.map(mapContainer.value).setView([35.86, 104.19], 5)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 18,
  }).addTo(map)

  const [cities, points] = await Promise.all([
    fetchMapCities(),
    fetchMapPoints({ limit: 5000 }),
  ])

  addCityLayer(cities)
  addPointLayer(points)
  updateLayers()

  map.on('zoomend', updateLayers)
})

onUnmounted(() => {
  if (map) {
    map.remove()
    map = null
  }
})
</script>
