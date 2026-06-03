<template>
  <div>
    <div v-if="loading" class="flex justify-center py-12">
      <div class="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full"></div>
    </div>
    <template v-else-if="person">
      <!-- 头部 -->
      <div class="flex items-center gap-4 mb-6">
        <div class="w-16 h-16 rounded-full overflow-hidden border-2 border-gray-200 dark:border-gray-600">
          <img :src="faceThumbUrl(person.representative_face_id)" class="w-full h-full object-cover" />
        </div>
        <div class="flex-1">
          <div class="flex items-center gap-2">
            <h2 v-if="!editing" class="text-lg font-semibold text-gray-800 dark:text-gray-100 cursor-pointer hover:text-primary-600" @click="startEdit">
              {{ person.name || $t('persons.unnamed') }}
            </h2>
            <input
              v-else
              ref="nameInput"
              v-model="editName"
              @keydown.enter="saveEdit"
              @blur="saveEdit"
              class="text-lg font-semibold border-b border-primary-400 bg-transparent outline-none dark:text-gray-100"
            />
          </div>
          <p class="text-sm text-gray-400">{{ $t('common.photos', { count: person.face_count }) }}</p>
        </div>
        <div class="flex gap-2">
          <button
            @click="showMerge = true"
            class="px-3 py-1.5 text-sm border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 dark:text-gray-300"
          >{{ $t('persons.merge') }}</button>
          <button
            @click="faceMode = !faceMode"
            class="px-3 py-1.5 text-sm border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 dark:text-gray-300"
            :class="faceMode ? 'bg-primary-50 dark:bg-primary-900/30 border-primary-300' : ''"
          >{{ $t('persons.manageFaces') }}</button>
        </div>
      </div>

      <!-- 人脸管理模式 -->
      <div v-if="faceMode" class="mb-6">
        <div class="flex items-center justify-between mb-3">
          <p class="text-sm text-gray-500">{{ $t('persons.selectToRemove') }}</p>
          <button
            v-if="selectedFaces.size > 0"
            @click="handleRemoveFaces"
            class="px-3 py-1.5 text-sm text-red-600 border border-red-200 rounded-lg hover:bg-red-50"
          >{{ $t('persons.removeFaces') }} ({{ selectedFaces.size }})</button>
        </div>
        <div class="grid grid-cols-6 sm:grid-cols-8 md:grid-cols-10 lg:grid-cols-12 gap-2">
          <div
            v-for="face in faces"
            :key="face.face_id"
            class="relative cursor-pointer"
            @click="toggleFaceSelect(face.face_id)"
          >
            <img
              :src="faceThumbUrl(face.face_id)"
              class="w-full aspect-square object-cover rounded-lg"
              :class="selectedFaces.has(face.face_id) ? 'ring-2 ring-red-400' : ''"
            />
            <div v-if="selectedFaces.has(face.face_id)" class="absolute top-1 right-1 w-4 h-4 bg-red-500 rounded-full flex items-center justify-center">
              <svg class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"/>
              </svg>
            </div>
          </div>
        </div>
      </div>

      <!-- 照片网格 -->
      <template v-if="!faceMode">
        <PhotoGrid :items="items" @open="handleOpen" />
        <div v-if="totalPages > 1" class="flex justify-center items-center gap-4 mt-6">
          <button
            :disabled="page <= 1"
            class="px-3 py-1.5 text-sm rounded-lg border border-gray-200 dark:border-gray-600 disabled:opacity-40"
            @click="page--; loadData()"
          >{{ $t('common.prevPage') }}</button>
          <span class="text-sm text-gray-500">{{ $t('common.pageInfo', { current: page, total: totalPages }) }}</span>
          <button
            :disabled="page >= totalPages"
            class="px-3 py-1.5 text-sm rounded-lg border border-gray-200 dark:border-gray-600 disabled:opacity-40"
            @click="page++; loadData()"
          >{{ $t('common.nextPage') }}</button>
        </div>
      </template>
    </template>

    <!-- 合并弹窗 -->
    <Teleport to="body">
      <div v-if="showMerge" class="fixed inset-0 z-[10000] flex items-center justify-center bg-black/50" @click.self="showMerge = false">
        <div class="bg-white dark:bg-gray-800 rounded-xl w-full max-w-md mx-4 p-5 max-h-[80vh] overflow-y-auto">
          <h3 class="text-base font-medium text-gray-800 dark:text-gray-100 mb-3">{{ $t('persons.mergeTitle') }}</h3>
          <p class="text-sm text-gray-500 mb-4">{{ $t('persons.mergeHint') }}</p>
          <div class="grid grid-cols-4 gap-3 mb-4">
            <div
              v-for="p in otherPersons"
              :key="p.person_id"
              class="flex flex-col items-center gap-1 cursor-pointer"
              @click="toggleMergeSelect(p.person_id)"
            >
              <div class="w-12 h-12 rounded-full overflow-hidden border-2 transition-colors"
                :class="mergeSelected.has(p.person_id) ? 'border-primary-500' : 'border-gray-200 dark:border-gray-600'"
              >
                <img :src="faceThumbUrl(p.representative_face_id)" class="w-full h-full object-cover" />
              </div>
              <span class="text-xs text-gray-500 line-clamp-1">{{ p.name || $t('persons.unnamed') }}</span>
            </div>
          </div>
          <div class="flex justify-end gap-2">
            <button @click="showMerge = false" class="px-3 py-1.5 text-sm text-gray-500 border border-gray-200 dark:border-gray-600 rounded-lg">{{ $t('common.cancel') }}</button>
            <button
              :disabled="mergeSelected.size === 0"
              @click="handleMerge"
              class="px-3 py-1.5 text-sm text-white bg-primary-500 rounded-lg hover:bg-primary-600 disabled:opacity-40"
            >{{ $t('persons.mergeConfirm') }} ({{ mergeSelected.size }})</button>
          </div>
        </div>
      </div>
    </Teleport>
    <PhotoDetail @deleted="onAssetDeleted" />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useUiStore } from '../stores/ui'
import {
  fetchPersonAssets, fetchPersonFaces, fetchPersons, renamePerson,
  mergePersons, removePersonFaces, faceThumbUrl,
  type PersonInfo, type PersonDetail, type FaceInfo, type AssetBrief,
} from '../api'
import PhotoGrid from '../components/gallery/PhotoGrid.vue'
import PhotoDetail from '../components/gallery/PhotoDetail.vue'

const route = useRoute()
const ui = useUiStore()

const loading = ref(true)
const person = ref<PersonDetail | null>(null)
const items = ref<AssetBrief[]>([])
const page = ref(1)
const totalPages = ref(1)

const editing = ref(false)
const editName = ref('')
const nameInput = ref<HTMLInputElement | null>(null)

const faceMode = ref(false)
const faces = ref<FaceInfo[]>([])
const selectedFaces = reactive(new Set<number>())

const showMerge = ref(false)
const otherPersons = ref<PersonInfo[]>([])
const mergeSelected = reactive(new Set<number>())

const personId = Number(route.params.id)

async function loadData() {
  const data = await fetchPersonAssets(personId, { page: page.value, page_size: ui.computedPageSize })
  person.value = data
  items.value = data.items
  totalPages.value = data.total_pages
}

async function loadFaces() {
  faces.value = await fetchPersonFaces(personId)
}

function handleOpen(assetId: number) {
  ui.openDetail(assetId, items.value.map(i => i.asset_id))
}

function onAssetDeleted(assetId: number) {
  items.value = items.value.filter(i => i.asset_id !== assetId)
}

function startEdit() {
  editName.value = person.value?.name || ''
  editing.value = true
  nextTick(() => nameInput.value?.focus())
}

async function saveEdit() {
  editing.value = false
  const newName = editName.value.trim()
  if (person.value && newName !== person.value.name) {
    await renamePerson(personId, newName)
    person.value.name = newName
  }
}

function toggleFaceSelect(faceId: number) {
  if (selectedFaces.has(faceId)) selectedFaces.delete(faceId)
  else selectedFaces.add(faceId)
}

async function handleRemoveFaces() {
  if (selectedFaces.size === 0) return
  await removePersonFaces(personId, [...selectedFaces])
  selectedFaces.clear()
  await loadFaces()
  await loadData()
}

function toggleMergeSelect(pid: number) {
  if (mergeSelected.has(pid)) mergeSelected.delete(pid)
  else mergeSelected.add(pid)
}

async function handleMerge() {
  if (mergeSelected.size === 0) return
  await mergePersons(personId, [...mergeSelected])
  mergeSelected.clear()
  showMerge.value = false
  await loadData()
  await loadFaces()
}

onMounted(async () => {
  try {
    await loadData()
    await loadFaces()
    const all = await fetchPersons()
    otherPersons.value = all.filter(p => p.person_id !== personId)
  } finally {
    loading.value = false
  }
})
</script>
