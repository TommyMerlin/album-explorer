<template>
  <div class="h-[calc(100vh-57px-48px)] flex flex-col">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-lg font-semibold text-gray-800">标签图谱</h2>
      <div class="flex items-center gap-3">
        <label class="text-sm text-gray-500">最小共现：</label>
        <input
          v-model.number="minWeight"
          type="range"
          min="3"
          max="50"
          class="w-32"
          @change="loadGraph"
        />
        <span class="text-sm text-gray-600 w-6">{{ minWeight }}</span>
      </div>
    </div>
    <div class="flex-1 rounded-xl overflow-hidden border border-gray-200 bg-white relative">
      <div v-if="loading" class="absolute inset-0 flex justify-center items-center bg-white/80 z-10">
        <div class="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full"></div>
      </div>
      <svg ref="svgRef" :width="svgWidth" :height="svgHeight" class="block"></svg>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { fetchTagGraph, type TagGraph } from '../api'
import * as d3 from 'd3'

const router = useRouter()
const svgRef = ref<SVGSVGElement | null>(null)
const loading = ref(true)
const minWeight = ref(10)
const svgWidth = ref(800)
const svgHeight = ref(600)

let simulation: d3.Simulation<any, any> | null = null
let resizeObserver: ResizeObserver | null = null

async function loadGraph() {
  loading.value = true
  try {
    const graph = await fetchTagGraph(minWeight.value)
    await nextTick()
    updateSize()
    renderGraph(graph)
  } finally {
    loading.value = false
  }
}

function updateSize() {
  if (!svgRef.value) return
  const parent = svgRef.value.parentElement
  if (parent) {
    svgWidth.value = parent.clientWidth
    svgHeight.value = parent.clientHeight
  }
}

function renderGraph(graph: TagGraph) {
  if (!svgRef.value) return

  const svg = d3.select(svgRef.value)
  svg.selectAll('*').remove()

  const width = svgWidth.value
  const height = svgHeight.value

  if (!width || !height) return

  const maxCount = Math.max(...graph.nodes.map(n => n.count), 1)
  const maxWeight = Math.max(...graph.edges.map(e => e.weight), 1)

  const nodeScale = d3.scaleSqrt().domain([0, maxCount]).range([4, 24])
  const linkScale = d3.scaleLinear().domain([0, maxWeight]).range([0.5, 4])

  const nodes = graph.nodes.map(n => ({ ...n, id: n.tag }))
  const links = graph.edges.map(e => ({ ...e }))

  if (simulation) simulation.stop()

  simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(links).id((d: any) => d.id).distance(80))
    .force('charge', d3.forceManyBody().strength(-120))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius((d: any) => nodeScale(d.count) + 4))

  const g = svg.append('g')

  svg.call(
    d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.3, 5])
      .on('zoom', (event) => g.attr('transform', event.transform))
  )

  g.append('g')
    .selectAll('line')
    .data(links)
    .join('line')
    .attr('stroke', '#e5e7eb')
    .attr('stroke-width', (d: any) => linkScale(d.weight))

  const node = g.append('g')
    .selectAll('g')
    .data(nodes)
    .join('g')
    .call(d3.drag<any, any>()
      .on('start', (event, d) => {
        if (!event.active) simulation!.alphaTarget(0.3).restart()
        d.fx = d.x
        d.fy = d.y
      })
      .on('drag', (event, d) => {
        d.fx = event.x
        d.fy = event.y
      })
      .on('end', (event, d) => {
        if (!event.active) simulation!.alphaTarget(0)
        d.fx = null
        d.fy = null
      })
    )

  node.append('circle')
    .attr('r', (d: any) => nodeScale(d.count))
    .attr('fill', '#0ea5e9')
    .attr('fill-opacity', 0.7)
    .attr('stroke', '#fff')
    .attr('stroke-width', 1.5)
    .style('cursor', 'pointer')
    .on('click', (_event: any, d: any) => {
      router.push({ path: '/explore', query: { tag: d.tag } })
    })

  node.append('text')
    .text((d: any) => d.tag)
    .attr('font-size', (d: any) => Math.max(9, Math.min(14, nodeScale(d.count))))
    .attr('text-anchor', 'middle')
    .attr('dy', (d: any) => nodeScale(d.count) + 12)
    .attr('fill', '#374151')

  const linkElements = g.selectAll('line')

  simulation.on('tick', () => {
    linkElements
      .attr('x1', (d: any) => d.source.x)
      .attr('y1', (d: any) => d.source.y)
      .attr('x2', (d: any) => d.target.x)
      .attr('y2', (d: any) => d.target.y)

    node.attr('transform', (d: any) => `translate(${d.x},${d.y})`)
  })
}

onMounted(() => {
  // 监听容器尺寸变化
  if (svgRef.value?.parentElement) {
    resizeObserver = new ResizeObserver(() => {
      updateSize()
    })
    resizeObserver.observe(svgRef.value.parentElement)
  }
  loadGraph()
})

onUnmounted(() => {
  if (simulation) simulation.stop()
  if (resizeObserver) resizeObserver.disconnect()
})
</script>
