import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Login',
    component: () => import('@/pages/Login.vue')
  },
  {
    path: '/interview',
    name: 'Interview',
    component: () => import('@/pages/Interview.vue')
  },
  {
    path: '/interview-manual',
    name: 'InterviewManual',
    component: () => import('@/pages/InterviewManual.vue')
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/pages/Register.vue')
  },
  {
    path: '/register-voice',
    name: 'RegisterVoice',
    component: () => import('@/pages/RegisterVoice.vue')
  },
  {
    path: '/training-progress',
    name: 'TrainingProgress',
    component: () => import('@/pages/TrainingProgress.vue')
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/pages/Profile.vue')
  },
  {
    path: '/admin-select',
    name: 'AdminSelect',
    component: () => import('@/pages/AdminSelect.vue')
  },
  {
    path: '/database',
    name: 'Database',
    component: () => import('@/pages/Database.vue')
  },
  {
    path: '/rekapitulasi-user',
    name: 'RekapitulasiUser',
    component: () => import('@/pages/RekapitulasiUser.vue')
  },
  {
    path: '/select-mode',
    name: 'SelectMode',
    component: () => import('@/pages/ModeSelect.vue')
  },
  {
    path: '/rekapitulasi',
    name: 'Rekapitulasi',
    component: () => import('@/pages/RekapitulasiPendataan.vue')
  },
  {
    path: '/about-us',
    name: 'AboutUs',
    component: () => import('@/pages/AboutUs.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  // Public pages that don't require authentication
  const publicPages = ['/', '/register', '/register-voice', '/about-us'];
  const authRequired = !publicPages.includes(to.path);

  // Check if user is logged in (using localStorage as source of truth for simplicity in guard)
  // We can also use the store if we import it, but localStorage is safer for persistence check
  const loggedIn = localStorage.getItem('auth_token');
  const userRole = localStorage.getItem('auth_user') ? JSON.parse(localStorage.getItem('auth_user') || '{}').role : null;

  if (authRequired && !loggedIn) {
    return next('/');
  }

  // Admin only routes
  if ((to.path === '/rekapitulasi-user' || to.path === '/admin-select' || to.path === '/database') && userRole !== 'admin') {
    return next('/interview');
  }

  next();
})

export default router