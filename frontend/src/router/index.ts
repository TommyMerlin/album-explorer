import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('../views/HomeView.vue'),
    },
    {
      path: '/timeline',
      name: 'timeline',
      component: () => import('../views/TimelinePage.vue'),
    },
    {
      path: '/map',
      name: 'map',
      component: () => import('../views/MapPage.vue'),
    },
    {
      path: '/clusters',
      name: 'clusters',
      component: () => import('../views/ClustersPage.vue'),
    },
    {
      path: '/clusters/:id',
      name: 'cluster-detail',
      component: () => import('../views/ClusterDetailPage.vue'),
    },
    {
      path: '/tags',
      name: 'tags',
      component: () => import('../views/TagsPage.vue'),
    },
    {
      path: '/search',
      name: 'search',
      component: () => import('../views/SearchPage.vue'),
    },
  ],
})

export default router
