<template>
  <div class="app" :class="appClass">
    <!-- 动态网格背景 -->
    <div class="bg-grid"></div>
    <div class="bg-gradient-overlay"></div>

    <!-- ═══════════ 搜索区 ═══════════ -->
    <div class="search-layer">
      <transition name="logo-fade">
        <div class="brand" v-if="searchState === 'idle'">
          <div class="brand-emoji">🔍</div>
          <h1 class="brand-title">夸克资源搜索</h1>
          <p class="brand-desc">在全网搜索夸克网盘分享资源，智能识别剧集完整性</p>
        </div>
      </transition>

      <div class="search-box">
        <!-- 霓虹搜索栏 -->
        <div class="search-wrapper">
          <div class="search-bar-glow"></div>
          <div class="search-bar" :class="{ focused: searchFocused }">
            <div class="search-icon-wrap">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
                <circle cx="11" cy="11" r="8"/>
                <path d="m21 21-4.35-4.35"/>
              </svg>
            </div>
            <input
              ref="searchInput"
              v-model="query"
              class="search-input"
              placeholder="搜索资源，如「庆余年」「Python 教程」..."
              @keydown.enter="startSearch"
              @focus="searchFocused = true"
              @blur="searchFocused = false"
              :disabled="searching"
            />
            <button
              class="search-btn"
              @click="startSearch"
              :disabled="searching || !query.trim()"
            >
              <svg v-if="!searching" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <path d="M5 12h14"/>
                <path d="m12 5 7 7-7 7"/>
              </svg>
              <span v-else class="btn-spinner"></span>
            </button>
          </div>
        </div>

        <!-- 热词标签 -->
        <transition name="tags-fade">
          <div class="hot-tags" v-if="searchState === 'idle'">
            <button
              v-for="tag in quickTags"
              :key="tag"
              class="hot-tag"
              @click="query = tag; startSearch()"
            ># {{ tag }}</button>
          </div>
        </transition>
      </div>

      <!-- 演示模式提示 -->
      <div class="demo-banner" v-if="isDemoMode && searchState === 'idle'">
        <span>💡</span>
        <span>演示模式 — 展示搜索流程效果，实际使用需启动后端服务</span>
      </div>
    </div>

    <!-- ═══════════ 结果区 ═══════════ -->
    <div class="result-layer" v-if="searchState !== 'idle'">
      <!-- 状态头 -->
      <div class="result-header">
        <div class="result-info">
          <span class="query-label">「{{ currentQuery }}」</span>
          <span class="engine-badge" v-if="searchEngine">
            <span class="engine-dot"></span>
            {{ searchEngine }}
          </span>
        </div>
        <div class="result-meta">
          <span class="elapsed" v-if="elapsedSeconds > 0">{{ elapsedSeconds }}s</span>
          <span class="resource-count" v-if="resources.length > 0">
            {{ resources.length }} 资源
          </span>
          <button class="btn-new-search" @click="resetSearch" v-if="!searching">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M23 4v6h-6"/><path d="M1 20v-6h6"/>
              <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10"/>
              <path d="M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
            </svg>
            新搜索
          </button>
        </div>
      </div>

      <!-- 进度条 -->
      <div class="progress-container" v-if="searching">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
        </div>
        <div class="progress-text">
          {{ progressText }}
        </div>
      </div>

      <!-- 自动完成倒计时 -->
      <transition name="countdown-fade">
        <div class="countdown-banner" v-if="showAutoComplete && resources.length > 0">
          <div class="countdown-content">
            <span class="countdown-icon">⏱️</span>
            <span class="countdown-text">已找到 {{ resources.length }} 个资源，{{ autoCompleteCountdown }}秒后自动完成</span>
            <button class="btn-finish" @click="forceComplete">立即完成</button>
          </div>
        </div>
      </transition>

      <!-- ═══════════ 总结页面 ═══════════ -->
      <transition name="summary-fade">
        <div class="summary-page" v-if="searchState === 'complete' && resources.length > 0">
          <!-- 核心成功卡片 -->
          <div class="success-hero">
            <div class="success-emoji">🎉</div>
            <h2 class="success-title">哇，成功搜索到 {{ resources.length }} 条资源！</h2>
            <p class="success-subtitle">为「{{ currentQuery }}」找到 {{ linksFound }} 个夸克链接，耗时 {{ elapsedSeconds }} 秒</p>
          </div>

          <!-- 数据概览网格 -->
          <div class="summary-grid">
            <div class="summary-card primary">
              <div class="card-icon">📦</div>
              <div class="card-value">{{ resources.length }}</div>
              <div class="card-label">有效资源</div>
            </div>
            <div class="summary-card">
              <div class="card-icon">🔗</div>
              <div class="card-value">{{ linksFound }}</div>
              <div class="card-label">夸克链接</div>
            </div>
            <div class="summary-card">
              <div class="card-icon">📁</div>
              <div class="card-value">{{ totalFiles }}</div>
              <div class="card-label">文件总数</div>
            </div>
            <div class="summary-card">
              <div class="card-icon">⚡</div>
              <div class="card-value">{{ elapsedSeconds }}s</div>
              <div class="card-label">搜索耗时</div>
            </div>
          </div>

          <!-- 资源列表 -->
          <div class="section-divider">
            <div class="divider-dot"></div>
            <span>资源列表</span>
            <span class="divider-count">{{ resources.length }} 个</span>
          </div>

          <div class="resource-list">
            <div
              v-for="(res, idx) in resources"
              :key="idx"
              class="resource-item"
              :class="{ expanded: expandedResources.has(idx) }"
              @click="toggleResource(idx)"
            >
              <!-- 卡片头部 -->
              <div class="resource-header">
                <div class="resource-index">{{ String(idx + 1).padStart(2, '0') }}</div>
                <div class="resource-info">
                  <h3 class="resource-title">{{ res.title || '未命名资源' }}</h3>
                  <div class="resource-meta">
                    <span class="meta-chip files">
                      <span>📁</span>
                      {{ res.files?.length || 0 }} 文件
                    </span>
                    <span class="meta-chip password" v-if="res.password_hint">
                      <span>🔑</span>
                      提取码 {{ res.password_hint }}
                    </span>
                    <span class="meta-chip" :class="res.episode_match?.status" v-if="res.episode_match">
                      <span v-if="res.episode_match.status === 'complete'">✅</span>
                      <span v-else>⚠️</span>
                      {{ epBadgeText(res.episode_match) }}
                    </span>
                  </div>
                </div>
                <svg class="expand-icon" :class="{ open: expandedResources.has(idx) }" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="m6 9 6 6 6-6"/>
                </svg>
              </div>

              <!-- 夸克链接 -->
              <div class="link-row">
                <code class="link-url">{{ res.url }}</code>
                <a :href="res.url" target="_blank" class="btn-open" @click.stop>
                  <span>打开</span>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                    <polyline points="15 3 21 3 21 9"/>
                    <line x1="10" y1="14" x2="21" y2="3"/>
                  </svg>
                </a>
                <button class="btn-copy" @click.stop="copyUrl(res.url)" :class="{ copied: copiedUrl === res.url }">
                  {{ copiedUrl === res.url ? '✓ 已复制' : '复制链接' }}
                </button>
              </div>

              <!-- 展开详情 -->
              <transition name="expand">
                <div class="resource-detail" v-show="expandedResources.has(idx)">
                  <!-- 剧集比对 -->
                  <div class="episode-card" v-if="res.episode_match">
                    <div class="episode-header">
                      <span class="episode-label">📺 剧集完整性分析</span>
                      <span class="episode-status" :class="res.episode_match.status">
                        {{ res.episode_match.message }}
                      </span>
                    </div>
                    <div class="episode-stats" v-if="res.episode_match.official_total > 0">
                      <div class="stat">
                        <span class="stat-num">{{ res.episode_match.quark_count || 0 }}</span>
                        <span class="stat-text">夸克集数</span>
                      </div>
                      <div class="stat-divider">/</div>
                      <div class="stat">
                        <span class="stat-num">{{ res.episode_match.official_total }}</span>
                        <span class="stat-text">官方集数</span>
                      </div>
                      <div class="stat-divider" v-if="res.episode_match.missing_episodes?.length">/</div>
                      <div class="stat" v-if="res.episode_match.missing_episodes?.length">
                        <span class="stat-num warn">{{ res.episode_match.missing_episodes.length }}</span>
                        <span class="stat-text">缺失</span>
                      </div>
                    </div>
                    <div class="missing-episodes" v-if="res.episode_match.missing_episodes?.length">
                      <span class="missing-label">缺失集数：</span>
                      <span v-for="ep in res.episode_match.missing_episodes.slice(0, 30)" :key="ep" class="missing-ep">
                        {{ ep }}
                      </span>
                      <span v-if="res.episode_match.missing_episodes.length > 30" class="missing-more">...等</span>
                    </div>
                  </div>

                  <p class="resource-desc" v-if="res.description">{{ res.description }}</p>

                  <ul class="file-list" v-if="res.files?.length">
                    <li v-for="(file, fi) in res.files.slice(0, 50)" :key="fi">
                      <span class="file-dot"></span>
                      {{ file.name }}
                    </li>
                    <li v-if="res.files.length > 50" class="more-files">
                      ...还有 {{ res.files.length - 50 }} 个文件
                    </li>
                  </ul>
                </div>
              </transition>
            </div>
          </div>

          <!-- 站点访问记录 -->
          <details class="site-records">
            <summary class="site-summary">
              <span class="site-dot"></span>
              <span>站点访问记录</span>
              <span class="site-count">{{ siteVisits.length }} 个站点</span>
              <svg class="site-caret" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="m6 9 6 6 6-6"/>
              </svg>
            </summary>
            <div class="site-list">
              <div v-for="(visit, vi) in siteVisits" :key="vi" class="site-item" :class="visit.status">
                <div class="site-status">
                  <span v-if="visit.status === 'found'" class="status-icon success">✓</span>
                  <span v-else-if="visit.status === 'failed'" class="status-icon error">✗</span>
                  <span v-else class="status-icon pending">○</span>
                </div>
                <span class="site-url" :title="visit.url">{{ visit.shortUrl }}</span>
                <span class="site-tag" :class="visit.status">
                  {{ visit.status === 'found' ? '有资源' : visit.status === 'failed' ? '失败' : '跳过' }}
                </span>
              </div>
            </div>
          </details>
        </div>
      </transition>

      <!-- 空结果 -->
      <div class="empty-state" v-if="!searching && resources.length === 0 && searchState === 'complete'">
        <div class="empty-emoji">🔍</div>
        <p class="empty-text">未找到相关资源</p>
        <p class="empty-hint">试试更换更具体或更宽泛的关键词</p>
        <button class="btn-back" @click="resetSearch">返回搜索</button>
      </div>

      <!-- 错误状态 -->
      <div class="error-state" v-if="searchState === 'error'">
        <div class="error-emoji">❌</div>
        <p class="error-text">搜索出错</p>
        <p class="error-hint">{{ errorMessage }}</p>
        <button class="btn-back" @click="resetSearch">返回搜索</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'

const query = ref('')
const currentQuery = ref('')
const searching = ref(false)
const searchFocused = ref(false)
const searchState = ref('idle')
const errorMessage = ref('')
const steps = ref([])
const resources = ref([])
const siteVisits = ref([])
const expandedResources = ref(new Set())
const copiedUrl = ref(null)
const searchInput = ref(null)
const progressPercent = ref(0)
const linksFound = ref(0)
const startTime = ref(null)
const elapsedSeconds = ref(0)
const searchEngine = ref('')

// 超时逻辑配置
const TIMEOUT_CONFIG = {
  baseTimeout: 180000,       // 3分钟基础超时
  timeoutPerResource: 30000, // 每个资源增加30秒
  minResources: 3            // 最少资源数才启用超时
}

let elapsedTimer = null
let timeoutTimer = null
let lastResourceTime = null

// 自动完成逻辑
const showAutoComplete = ref(false)
const autoCompleteCountdown = ref(0)
let autoCompleteTimer = null
const AUTO_COMPLETE_DELAY = 6

const isDemoMode = computed(() => {
  return window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1'
    || new URLSearchParams(window.location.search).has('demo')
})

const quickTags = ['庆余年', 'Python教程', '繁花', 'PS教程', '电子书合集', 'AI课程']

const appClass = computed(() => ({
  'is-searching': searching.value,
  'has-result': searchState.value === 'complete' && resources.value.length > 0,
  'is-error': searchState.value === 'error',
}))

const progressText = computed(() => {
  const actions = ['正在搜索...', '正在挖掘二级页面...', '正在访问夸克链接...', '正在解析资源...']
  return actions[Math.floor(progressPercent.value / 25)] || '搜索中...'
})

const totalFiles = computed(() =>
  resources.value.reduce((a, r) => a + (r.files?.length || 0), 0)
)

function resetSearch() {
  searchState.value = 'idle'
  searching.value = false
  currentQuery.value = ''
  steps.value = []
  resources.value = []
  siteVisits.value = []
  linksFound.value = 0
  progressPercent.value = 0
  elapsedSeconds.value = 0
  searchEngine.value = ''
  showAutoComplete.value = false
  autoCompleteCountdown.value = 0
  if (elapsedTimer) clearInterval(elapsedTimer)
  if (timeoutTimer) clearTimeout(timeoutTimer)
  if (autoCompleteTimer) clearInterval(autoCompleteTimer)
  query.value = ''
  nextTick(() => searchInput.value?.focus())
}

function clearAutoComplete() {
  showAutoComplete.value = false
  autoCompleteCountdown.value = 0
  if (autoCompleteTimer) {
    clearInterval(autoCompleteTimer)
    autoCompleteTimer = null
  }
}

function startAutoCompleteTimer() {
  if (autoCompleteTimer) clearInterval(autoCompleteTimer)
  showAutoComplete.value = true
  autoCompleteCountdown.value = AUTO_COMPLETE_DELAY
  autoCompleteTimer = setInterval(() => {
    autoCompleteCountdown.value--
    if (autoCompleteCountdown.value <= 0) {
      forceComplete()
    }
  }, 1000)
}

// 动态超时逻辑
function setupDynamicTimeout() {
  clearTimeout(timeoutTimer)

  // 计算动态超时时间
  const timeoutMs = TIMEOUT_CONFIG.baseTimeout +
    (resources.value.length * TIMEOUT_CONFIG.timeoutPerResource)

  timeoutTimer = setTimeout(() => {
    if (searching.value && resources.value.length >= TIMEOUT_CONFIG.minResources) {
      console.log(`搜索超时，已有 ${resources.value.length} 个资源，自动完成`)
      forceComplete()
    }
  }, timeoutMs)
}

// 监听资源数量变化
watch(() => resources.value.length, (newLen) => {
  if (newLen > 0 && searching.value) {
    lastResourceTime = Date.now()
    startAutoCompleteTimer()
    setupDynamicTimeout()
  }
})

function forceComplete() {
  clearAutoComplete()
  if (timeoutTimer) clearTimeout(timeoutTimer)

  if (searching.value) {
    searchState.value = 'complete'
    searching.value = false
    progressPercent.value = 100
    if (elapsedTimer) clearInterval(elapsedTimer)
    elapsedSeconds.value = Math.floor((Date.now() - startTime.value) / 1000)
  }
}

function toggleResource(idx) {
  const s = new Set(expandedResources.value)
  if (s.has(idx)) s.delete(idx)
  else s.add(idx)
  expandedResources.value = s
}

function epBadgeText(em) {
  if (!em) return ''
  switch (em.status) {
    case 'complete': return '剧集完整'
    case 'incomplete': return `未更新完(${em.quark_max}/${em.official_total})`
    case 'partial': return `有缺集(${em.quark_count}/${em.official_total})`
    default: return '无法比对'
  }
}

async function copyUrl(url) {
  try {
    await navigator.clipboard.writeText(url)
  } catch {
    const input = document.createElement('textarea')
    input.value = url
    document.body.appendChild(input)
    input.select()
    document.execCommand('copy')
    document.body.removeChild(input)
  }
  copiedUrl.value = url
  setTimeout(() => { copiedUrl.value = null }, 2000)
}

async function startSearch() {
  const q = query.value.trim()
  if (!q || searching.value) return

  searching.value = true
  searchState.value = 'searching'
  currentQuery.value = q
  steps.value = []
  resources.value = []
  siteVisits.value = []
  expandedResources.value = new Set()
  errorMessage.value = ''
  progressPercent.value = 0
  linksFound.value = 0
  elapsedSeconds.value = 0
  searchEngine.value = ''
  showAutoComplete.value = false
  lastResourceTime = null
  startTime.value = Date.now()

  elapsedTimer = setInterval(() => {
    elapsedSeconds.value = Math.floor((Date.now() - startTime.value) / 1000)
  }, 1000)

  try {
    if (isDemoMode.value) {
      await runDemoSearch(q)
      return
    }

    const response = await fetch(`/api/search?query=${encodeURIComponent(q)}`)
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const dataStr = line.slice(6)
          if (dataStr === '[DONE]') {
            forceComplete()
            continue
          }
          try {
            const event = JSON.parse(dataStr)
            handleEvent(event)
          } catch (e) {}
        }
      }
    }
  } catch (err) {
    if (err.message?.includes('Failed to fetch') || err.message?.includes('NetworkError')) {
      await runDemoSearch(q)
    } else {
      searchState.value = 'error'
      errorMessage.value = err.message || '网络请求失败'
      searching.value = false
      if (elapsedTimer) clearInterval(elapsedTimer)
      clearAutoComplete()
    }
  }
}

function handleEvent(event) {
  steps.value.push(event)

  if (event.type === 'link_found') {
    linksFound.value++
    progressPercent.value = Math.min(progressPercent.value + 3, 25)
    if (event.data?.engine && !searchEngine.value) searchEngine.value = event.data.engine
    if (event.data?.url?.includes('quark.cn')) {
      siteVisits.value.push({
        url: event.data.url,
        shortUrl: shortenUrl(event.data.url),
        status: 'pending',
        title: '',
        filesCount: 0,
      })
    }
  } else if (event.type === 'resource_found') {
    if (event.data) {
      resources.value.push(event.data)
      const idx = siteVisits.value.length - 1
      if (idx >= 0 && siteVisits.value[idx].status === 'pending') {
        siteVisits.value[idx].status = 'found'
        siteVisits.value[idx].title = event.data.title || ''
        siteVisits.value[idx].filesCount = event.data.files?.length || 0
      }
    }
    progressPercent.value = Math.min(progressPercent.value + 20, 90)
  } else if (event.type === 'progress') {
    progressPercent.value = Math.min(progressPercent.value + 2, 80)
    if (event.data?.engine && !searchEngine.value) searchEngine.value = event.data.engine
  } else if (event.type === 'complete') {
    forceComplete()
    if (event.data?.engine) searchEngine.value = event.data.engine
    if (event.data?.resources) resources.value = event.data.resources
  } else if (event.type === 'error') {
    searchState.value = 'error'
    errorMessage.value = event.message
    searching.value = false
    if (elapsedTimer) clearInterval(elapsedTimer)
    clearAutoComplete()
  }
}

function shortenUrl(url) {
  try {
    const u = new URL(url)
    return u.hostname + u.pathname.slice(0, 40) + (u.pathname.length > 40 ? '...' : '')
  } catch { return url.slice(0, 60) }
}

// ──────────────────── 演示模式 ────────────────────

async function runDemoSearch(q) {
  const mockEvents = generateMockEvents(q)
  for (const evt of mockEvents) {
    await new Promise(r => setTimeout(r, evt._delay || 300))
    handleEvent(evt)
  }
  forceComplete()
}

function generateMockEvents(q) {
  const isSeries = ['庆余年', '繁花', '狂飙', '三体', '琅琊榜', '甄嬛传'].some(s => q.includes(s))
  const events = []

  events.push({ type: 'progress', message: '正在搜索: "' + q + ' 夸克网盘"', _delay: 400 })
  events.push({ type: 'progress', message: '正在通过 Baidu 搜索...', data: { engine: 'Baidu' }, _delay: 1000 })
  events.push({ type: 'progress', message: 'Baidu 找到 5 个夸克链接', data: { engine: 'Baidu' }, _delay: 400 })

  const mockLinks = [
    'https://pan.quark.cn/s/abc123def456',
    'https://pan.quark.cn/s/xyz789ghi012',
    'https://pan.quark.cn/s/mno345pqr678',
    'https://pan.quark.cn/s/stu901vwx234',
    'https://pan.quark.cn/s/yza567bcd890',
  ]

  mockLinks.forEach(link => {
    events.push({ type: 'link_found', message: '夸克链接: ' + link, data: { url: link, engine: 'Baidu' }, _delay: 200 })
  })

  events.push({ type: 'progress', message: '共收集 5 个夸克链接', _delay: 400 })

  const mockResources = [
    { title: q + ' 全集 1080P 蓝光版', files: Array.from({ length: 40 }, (_, i) => ({ name: `第${String(i+1).padStart(2,'0')}集.mkv` })), password: '', url: mockLinks[0] },
    { title: q + ' 1-40集完整版 高清', files: Array.from({ length: 40 }, (_, i) => ({ name: `${q} EP${String(i+1).padStart(2,'0')}.mp4` })), password: 'a1b2', url: mockLinks[1] },
    { title: q + ' 全季合集 4K HDR', files: Array.from({ length: 35 }, (_, i) => ({ name: `[${String(i+1).padStart(2,'0')}] ${q}.mkv` })), password: '', url: mockLinks[2] },
  ]

  mockResources.forEach((res, i) => {
    events.push({ type: 'progress', message: `正在访问 (${i+1}/5): ${res.url}...`, _delay: 500 })
    const resourceData = {
      url: res.url,
      title: res.title,
      description: i === 0 ? '高清完整版，包含全40集，画质优秀，推荐下载。' : '',
      files: res.files,
      password_hint: res.password,
    }
    if (isSeries && res.files.length >= 40) {
      resourceData.episode_match = {
        status: 'complete',
        message: '剧集完整（40/40集）',
        quark_max: 40,
        quark_count: 40,
        official_total: 40,
        missing_episodes: []
      }
    }
    events.push({ type: 'resource_found', message: `✅ [${res.title}] 提取到 ${res.files.length} 个资源`, data: resourceData, _delay: 800 })
  })

  return events
}

onMounted(() => {
  nextTick(() => searchInput.value?.focus())
})
</script>

<style>
/* ═══════════ CSS 变量 ═══════════ */
:root {
  /* 深色主题色彩系统 */
  --c-midnight: #0f172a;
  --c-surface: #1e293b;
  --c-surface-hover: #334155;
  --c-border: #334155;
  --c-border-light: #475569;

  /* 霓虹色系 */
  --c-neon-purple: #a855f7;
  --c-neon-cyan: #22d3ee;
  --c-neon-glow: rgba(168, 85, 247, 0.3);

  /* 状态色 */
  --c-success: #10b981;
  --c-warning: #fbbf24;
  --c-error: #ef4444;

  /* 文本色 */
  --c-text-main: #f8fafc;
  --c-text-sub: #94a3b8;
  --c-text-muted: #64748b;

  /* 尺寸 */
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 14px;
  --radius-xl: 18px;

  /* 字体 */
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif;
  --font-mono: 'JetBrains Mono', 'SF Mono', 'Fira Code', Consolas, monospace;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: var(--font-sans);
  background: var(--c-midnight);
  color: var(--c-text-main);
  -webkit-font-smoothing: antialiased;
  min-height: 100vh;
  overflow-x: hidden;
  line-height: 1.6;
}

/* ═══════════ 动态网格背景 ═══════════ */
.bg-grid {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background-image:
    linear-gradient(rgba(168, 85, 247, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(168, 85, 247, 0.03) 1px, transparent 1px);
  background-size: 40px 40px;
  animation: gridScroll 20s linear infinite;
}

@keyframes gridScroll {
  0% { background-position: 0 0; }
  100% { background-position: 40px 40px; }
}

.bg-gradient-overlay {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background: radial-gradient(ellipse at 50% 0%, rgba(168, 85, 247, 0.08) 0%, transparent 60%);
}

/* ═══════════ App ═══════════ */
.app {
  min-height: 100vh;
  padding: 0 20px 40px;
  position: relative;
  z-index: 1;
}

.app:not(.has-result):not(.is-error):not(.is-searching) {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
}

/* ═══════════ 搜索层 ═══════════ */
.search-layer {
  width: 100%;
  max-width: 580px;
  margin: 0 auto;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.app.is-searching .search-layer,
.app.has-result .search-layer,
.app.is-error .search-layer {
  max-width: 720px;
  margin-top: 32px;
  margin-bottom: 24px;
}

/* 品牌 */
.brand {
  text-align: center;
  margin-bottom: 48px;
  transition: all 0.4s ease;
}

.brand-emoji {
  font-size: 56px;
  margin-bottom: 20px;
  animation: emojiFloat 3s ease-in-out infinite;
}

@keyframes emojiFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

.brand-title {
  font-size: 2rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  margin-bottom: 12px;
  background: linear-gradient(135deg, var(--c-text-main) 0%, var(--c-text-sub) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.brand-desc {
  font-size: 0.92rem;
  color: var(--c-text-muted);
  line-height: 1.6;
}

/* 搜索框包装器 */
.search-wrapper {
  position: relative;
}

.search-bar-glow {
  position: absolute;
  inset: -2px;
  background: linear-gradient(135deg, var(--c-neon-purple), var(--c-neon-cyan));
  border-radius: var(--radius-xl);
  filter: blur(8px);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.search-bar.focused ~ .search-bar-glow {
  opacity: 0.6;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 0.9; }
}

.search-bar {
  position: relative;
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--c-surface);
  border: 2px solid var(--c-border);
  border-radius: var(--radius-xl);
  padding: 6px 8px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.search-bar.focused {
  border-color: var(--c-neon-purple);
  box-shadow: 0 0 0 4px var(--c-neon-glow);
}

.search-icon-wrap {
  color: var(--c-text-muted);
  flex-shrink: 0;
  padding-left: 6px;
}

.search-input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 0.95rem;
  padding: 12px 0;
  background: transparent;
  color: var(--c-text-main);
  font-family: var(--font-sans);
  min-width: 0;
}

.search-input::placeholder {
  color: var(--c-text-muted);
}

.search-input:disabled {
  opacity: 0.6;
}

.search-btn {
  width: 44px;
  height: 44px;
  border: none;
  border-radius: var(--radius-lg);
  background: linear-gradient(135deg, var(--c-neon-purple), var(--c-neon-cyan));
  color: var(--c-midnight);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  flex-shrink: 0;
  opacity: 0.5;
}

.search-btn:hover:not(:disabled) {
  opacity: 1;
  transform: scale(1.05);
  box-shadow: 0 4px 20px var(--c-neon-glow);
}

.search-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.btn-spinner {
  width: 18px;
  height: 18px;
  border: 2.5px solid rgba(15, 23, 42, 0.2);
  border-top-color: var(--c-midnight);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 热词标签 */
.hot-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 24px;
  justify-content: center;
}

.hot-tag {
  padding: 8px 16px;
  background: rgba(30, 41, 59, 0.6);
  border: 1px solid var(--c-border);
  border-radius: 20px;
  font-size: 0.85rem;
  color: var(--c-text-sub);
  cursor: pointer;
  font-family: var(--font-sans);
  transition: all 0.2s ease;
}

.hot-tag:hover {
  border-color: var(--c-neon-purple);
  color: var(--c-neon-purple);
  background: rgba(168, 85, 247, 0.1);
  transform: translateY(-2px);
}

/* 演示提示 */
.demo-banner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 24px;
  padding: 10px 20px;
  background: rgba(34, 211, 238, 0.1);
  border: 1px solid rgba(34, 211, 238, 0.3);
  border-radius: var(--radius-lg);
  font-size: 0.82rem;
  color: var(--c-neon-cyan);
}

/* ═══════════ 结果层 ═══════════ */
.result-layer {
  max-width: 880px;
  margin: 0 auto;
}

/* 结果头 */
.result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 0 20px;
  flex-wrap: wrap;
  gap: 12px;
}

.result-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.query-label {
  font-weight: 600;
  font-size: 1rem;
  color: var(--c-text-main);
  letter-spacing: -0.01em;
}

.engine-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.78rem;
  font-weight: 500;
  padding: 4px 12px;
  border-radius: 20px;
  background: rgba(30, 41, 59, 0.8);
  border: 1px solid var(--c-border);
  color: var(--c-text-sub);
}

.engine-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--c-success);
  animation: blink 1.5s ease-in-out infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.result-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.elapsed, .resource-count {
  font-size: 0.8rem;
  color: var(--c-text-muted);
}

.resource-count {
  font-weight: 500;
  color: var(--c-text-sub);
}

.btn-new-search {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border: 1px solid var(--c-border);
  border-radius: 20px;
  background: rgba(30, 41, 59, 0.8);
  font-size: 0.78rem;
  color: var(--c-text-sub);
  cursor: pointer;
  font-family: var(--font-sans);
  transition: all 0.2s ease;
}

.btn-new-search:hover {
  border-color: var(--c-neon-purple);
  color: var(--c-neon-purple);
}

/* 进度条 */
.progress-container {
  margin-bottom: 24px;
}

.progress-bar {
  height: 4px;
  background: var(--c-surface);
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--c-neon-purple), var(--c-neon-cyan));
  border-radius: 2px;
  transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.progress-text {
  font-size: 0.8rem;
  color: var(--c-text-muted);
  text-align: center;
}

/* 倒计时提示 */
.countdown-banner {
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.countdown-content {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  background: rgba(251, 191, 36, 0.1);
  border: 1px solid rgba(251, 191, 36, 0.3);
  border-radius: var(--radius-lg);
  margin-bottom: 20px;
}

.countdown-icon {
  font-size: 1.1rem;
}

.countdown-text {
  flex: 1;
  font-size: 0.85rem;
  color: var(--c-warning);
}

.btn-finish {
  margin-left: auto;
  padding: 6px 16px;
  border: none;
  border-radius: 20px;
  background: var(--c-warning);
  color: var(--c-midnight);
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  font-family: var(--font-sans);
  transition: all 0.2s ease;
}

.btn-finish:hover {
  filter: brightness(1.1);
  transform: translateY(-1px);
}

/* ═══════════ 总结页面 ═══════════ */
.summary-page {
  animation: fadeInUp 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 成功英雄区 */
.success-hero {
  text-align: center;
  padding: 32px 0 28px;
  background: rgba(16, 185, 129, 0.05);
  border: 1px solid rgba(16, 185, 129, 0.2);
  border-radius: var(--radius-xl);
  margin-bottom: 28px;
}

.success-emoji {
  font-size: 64px;
  margin-bottom: 16px;
  animation: bounce 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes bounce {
  0% { transform: scale(0); }
  100% { transform: scale(1); }
}

.success-title {
  font-size: 1.75rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  margin-bottom: 8px;
  background: linear-gradient(135deg, var(--c-success), var(--c-neon-cyan));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.success-subtitle {
  font-size: 0.9rem;
  color: var(--c-text-sub);
}

/* 概览网格 */
.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 32px;
}

.summary-card {
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--radius-lg);
  padding: 18px;
  text-align: center;
  transition: all 0.2s ease;
}

.summary-card:hover {
  border-color: var(--c-neon-purple);
  transform: translateY(-2px);
}

.summary-card.primary {
  border-color: var(--c-neon-purple);
  background: linear-gradient(135deg, rgba(168, 85, 247, 0.1), rgba(34, 211, 238, 0.05));
}

.card-icon {
  font-size: 28px;
  margin-bottom: 8px;
}

.card-value {
  font-size: 1.8rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--c-text-main);
  line-height: 1.2;
  margin-bottom: 4px;
}

.card-label {
  font-size: 0.75rem;
  color: var(--c-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* 分割标题 */
.section-divider {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--c-border);
}

.divider-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--c-neon-purple);
}

.section-divider span:nth-child(2) {
  font-size: 0.92rem;
  font-weight: 600;
  color: var(--c-text-main);
}

.divider-count {
  font-size: 0.78rem;
  color: var(--c-text-muted);
  margin-left: auto;
}

/* 资源列表 */
.resource-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.resource-item {
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: all 0.3s ease;
  cursor: pointer;
}

.resource-item:hover {
  border-color: var(--c-neon-purple);
  box-shadow: 0 4px 20px rgba(168, 85, 247, 0.1);
}

.resource-item.expanded {
  border-color: var(--c-neon-purple);
  box-shadow: 0 8px 30px rgba(168, 85, 247, 0.15);
}

/* 资源头部 */
.resource-header {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 16px 18px;
}

.resource-index {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--c-midnight);
  background: linear-gradient(135deg, var(--c-neon-purple), var(--c-neon-cyan));
  padding: 4px 10px;
  border-radius: var(--radius-sm);
  flex-shrink: 0;
  line-height: 1.4;
  margin-top: 2px;
}

.resource-info {
  flex: 1;
  min-width: 0;
}

.resource-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--c-text-main);
  line-height: 1.4;
  letter-spacing: -0.01em;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.resource-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  flex-wrap: wrap;
}

.meta-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.75rem;
  color: var(--c-text-muted);
  background: rgba(51, 65, 85, 0.6);
  padding: 3px 10px;
  border-radius: 20px;
}

.meta-chip.password {
  color: var(--c-warning);
  background: rgba(251, 191, 36, 0.15);
}

.meta-chip.complete {
  color: var(--c-success);
  background: rgba(16, 185, 129, 0.15);
}

.meta-chip.incomplete,
.meta-chip.partial {
  color: var(--c-warning);
  background: rgba(251, 191, 36, 0.15);
}

.expand-icon {
  color: var(--c-text-muted);
  flex-shrink: 0;
  transition: transform 0.3s ease;
  margin-top: 4px;
}

.expand-icon.open {
  transform: rotate(180deg);
  color: var(--c-neon-purple);
}

/* 链接行 */
.link-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 18px 16px;
}

.link-url {
  flex: 1;
  font-size: 0.8rem;
  font-family: var(--font-mono);
  color: var(--c-neon-cyan);
  background: rgba(34, 211, 238, 0.1);
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
  border: 1px solid rgba(34, 211, 238, 0.2);
}

.btn-open, .btn-copy {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border: 1px solid var(--c-border);
  border-radius: var(--radius-sm);
  background: var(--c-surface);
  font-size: 0.78rem;
  color: var(--c-text-sub);
  cursor: pointer;
  font-family: var(--font-sans);
  transition: all 0.2s ease;
  white-space: nowrap;
  text-decoration: none;
}

.btn-open {
  color: var(--c-neon-cyan);
  border-color: rgba(34, 211, 238, 0.3);
}

.btn-open:hover, .btn-copy:hover {
  border-color: var(--c-neon-purple);
  color: var(--c-neon-purple);
  transform: translateY(-1px);
}

.btn-copy.copied {
  background: rgba(16, 185, 129, 0.15);
  border-color: var(--c-success);
  color: var(--c-success);
}

/* 展开详情 */
.resource-detail {
  border-top: 1px solid var(--c-border-light);
  padding: 16px 18px 18px;
}

.expand-enter-active, .expand-leave-active {
  transition: all 0.3s ease;
}

.expand-enter-from, .expand-leave-to {
  opacity: 0;
  max-height: 0;
}

.expand-enter-to, .expand-leave-from {
  opacity: 1;
  max-height: 1000px;
}

/* 剧集卡片 */
.episode-card {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid var(--c-border);
  border-radius: var(--radius-md);
  padding: 14px 16px;
  margin-bottom: 14px;
}

.episode-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.episode-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--c-text-sub);
}

.episode-status {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 20px;
}

.episode-status.complete {
  background: rgba(16, 185, 129, 0.15);
  color: var(--c-success);
}

.episode-status.incomplete, .episode-status.partial {
  background: rgba(251, 191, 36, 0.15);
  color: var(--c-warning);
}

.episode-stats {
  display: flex;
  align-items: center;
  gap: 0;
  margin-bottom: 10px;
}

.stat {
  flex: 1;
  text-align: center;
}

.stat-num {
  display: block;
  font-size: 1.4rem;
  font-weight: 700;
  color: var(--c-text-main);
  line-height: 1.2;
}

.stat-num.warn {
  color: var(--c-error);
}

.stat-text {
  font-size: 0.7rem;
  color: var(--c-text-muted);
}

.stat-divider {
  color: var(--c-border);
  font-size: 1rem;
  padding: 0 8px;
}

.missing-episodes {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
}

.missing-label {
  font-size: 0.75rem;
  color: var(--c-text-muted);
  margin-right: 4px;
}

.missing-ep {
  font-size: 0.72rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 20px;
  background: rgba(239, 68, 68, 0.15);
  color: var(--c-error);
}

.missing-more {
  font-size: 0.72rem;
  color: var(--c-text-muted);
}

/* 描述和文件列表 */
.resource-desc {
  font-size: 0.85rem;
  color: var(--c-text-sub);
  line-height: 1.65;
  margin-bottom: 12px;
}

.file-list {
  list-style: none;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 4px 16px;
  max-height: 300px;
  overflow-y: auto;
}

.file-list li {
  font-size: 0.78rem;
  color: var(--c-text-sub);
  padding: 5px 0 5px 16px;
  position: relative;
  display: flex;
  align-items: center;
  gap: 6px;
}

.file-dot {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: var(--c-neon-purple);
  flex-shrink: 0;
  position: absolute;
  left: 4px;
}

.more-files {
  color: var(--c-text-muted) !important;
  font-style: italic;
  font-size: 0.78rem !important;
  padding-left: 16px !important;
}

/* 站点记录 */
.site-records {
  margin-top: 24px;
  border: 1px solid var(--c-border);
  border-radius: var(--radius-lg);
  background: var(--c-surface);
}

.site-summary {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  cursor: pointer;
  user-select: none;
  list-style: none;
}

.site-summary::-webkit-details-marker {
  display: none;
}

.site-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--c-neon-purple);
}

.site-summary span:nth-child(2) {
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--c-text-main);
}

.site-count {
  font-size: 0.78rem;
  color: var(--c-text-muted);
  margin-left: auto;
}

.site-caret {
  color: var(--c-text-muted);
  transition: transform 0.3s ease;
}

details[open] .site-caret {
  transform: rotate(180deg);
}

.site-list {
  padding: 0 18px 16px;
}

.site-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 0;
  font-size: 0.8rem;
}

.site-status {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.status-icon {
  font-size: 0.75rem;
  font-weight: 700;
}

.status-icon.success {
  color: var(--c-success);
}

.status-icon.error {
  color: var(--c-error);
}

.status-icon.pending {
  color: var(--c-text-muted);
}

.site-url {
  flex: 1;
  font-family: var(--font-mono);
  color: var(--c-text-sub);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
}

.site-tag {
  font-size: 0.7rem;
  padding: 3px 10px;
  border-radius: 20px;
  font-weight: 500;
  flex-shrink: 0;
}

.site-tag.found {
  background: rgba(16, 185, 129, 0.15);
  color: var(--c-success);
}

.site-tag.failed {
  background: rgba(239, 68, 68, 0.15);
  color: var(--c-error);
}

.site-tag.pending {
  background: rgba(100, 116, 139, 0.15);
  color: var(--c-text-muted);
}

/* 空状态和错误 */
.empty-state, .error-state {
  text-align: center;
  padding: 64px 20px;
}

.empty-emoji, .error-emoji {
  font-size: 72px;
  margin-bottom: 20px;
}

.empty-text, .error-text {
  font-size: 1.1rem;
  color: var(--c-text-main);
  font-weight: 600;
  margin-bottom: 8px;
}

.empty-hint, .error-hint {
  font-size: 0.9rem;
  color: var(--c-text-muted);
  margin-bottom: 24px;
}

.btn-back {
  padding: 12px 32px;
  background: linear-gradient(135deg, var(--c-neon-purple), var(--c-neon-cyan));
  color: var(--c-midnight);
  border: none;
  border-radius: var(--radius-lg);
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  font-family: var(--font-sans);
  transition: all 0.2s ease;
}

.btn-back:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 24px rgba(168, 85, 247, 0.3);
}

/* 过渡动画 */
.logo-fade-enter-active, .logo-fade-leave-active {
  transition: all 0.35s ease;
}

.logo-fade-enter-from, .logo-fade-leave-to {
  opacity: 0;
  transform: translateY(-12px);
}

.tags-fade-enter-active, .tags-fade-leave-active {
  transition: all 0.3s ease;
}

.tags-fade-enter-from, .tags-fade-leave-to {
  opacity: 0;
  transform: translateY(8px);
}

.summary-fade-enter-active {
  transition: all 0.4s ease;
}

.summary-fade-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.countdown-fade-enter-active {
  transition: all 0.3s ease;
}

.countdown-fade-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

/* 响应式 */
@media (max-width: 768px) {
  .app {
    padding: 0 16px 32px;
  }

  .brand-title {
    font-size: 1.5rem;
  }

  .brand-desc {
    font-size: 0.85rem;
  }

  .search-input {
    font-size: 0.9rem;
  }

  .summary-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .card-value {
    font-size: 1.5rem;
  }

  .resource-header {
    padding: 14px 16px;
  }

  .link-row {
    flex-wrap: wrap;
    padding: 0 16px 14px;
  }

  .file-list {
    grid-template-columns: 1fr;
  }

  .result-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .result-meta {
    width: 100%;
    justify-content: space-between;
  }
}
</style>