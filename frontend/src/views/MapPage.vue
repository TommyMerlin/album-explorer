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
    pointLayer.addLayer(marker)
  }
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
