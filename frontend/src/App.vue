<template>
  <div class="app" :class="appClass">
    <!-- ═══════════ 搜索区 ═══════════ -->
    <div class="search-layer">
      <transition name="logo-fade">
        <div class="brand" v-if="searchState === 'idle'">
          <h1 class="brand-title">夸克资源搜索</h1>
          <p class="brand-desc">在夸克网盘的海量分享中，找到你要的资源</p>
        </div>
      </transition>

      <div class="search-box">
        <div class="search-bar" :class="{ focused: searchFocused }">
          <svg class="search-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round">
            <circle cx="11" cy="11" r="8"/>
            <path d="m21 21-4.35-4.35"/>
          </svg>
          <input
            ref="searchInput"
            v-model="query"
            class="search-input"
            placeholder="输入资源名称，如 Python 教程、电影合集..."
            @keydown.enter="startSearch"
            @focus="searchFocused = true"
            @blur="searchFocused = false"
            :disabled="searching"
          />
          <button
            class="search-submit"
            @click="startSearch"
            :disabled="searching || !query.trim()"
            :class="{ active: query.trim() && !searching }"
          >
            <svg v-if="!searching" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M5 12h14"/>
              <path d="m12 5 7 7-7 7"/>
            </svg>
            <span v-else class="btn-spinner"></span>
          </button>
        </div>

        <div class="hot-tags" v-if="searchState === 'idle'">
          <button
            v-for="tag in quickTags"
            :key="tag"
            class="hot-tag"
            @click="query = tag; startSearch()"
          >{{ tag }}</button>
        </div>
      </div>
    </div>

    <!-- ═══════════ 结果区 ═══════════ -->
    <div class="result-layer" v-if="searchState !== 'idle'">
      <!-- ──── 状态头 ──── -->
      <div class="result-header">
        <div class="result-header-left">
          <span class="query-chip">{{ currentQuery }}</span>
          <span class="divider-dot">·</span>
          <span class="header-badge" :class="searchState">
            {{ headerBadge }}
          </span>
          <span class="engine-badge" v-if="searchEngine">
            <svg class="engine-icon" width="14" height="14" viewBox="0 0 24 24" fill="none">
              <template v-if="searchEngine === 'Google'">
                <path d="M12 5a7 7 0 0 1 6.06 3.5l-2.47 2a3.5 3.5 0 0 0-6 2A3.5 3.5 0 0 0 12 16a3.5 3.5 0 0 0 3.09-1.78l2.47 2A7 7 0 1 1 12 5z" fill="#4285F4"/>
                <path d="M19.06 12.5H12v-3h9.35a7 7 0 0 1-2.29 5.28" fill="#34A853"/>
                <path d="M12 16a3.5 3.5 0 0 1-3.5-3.5A3.5 3.5 0 0 1 12 9v3.5H9.06" fill="#FBBC05"/>
                <path d="M21.06 14.78A7 7 0 0 0 12 5v3.5h.09a3.5 3.5 0 0 1 5.53 2.78" fill="#EA4335"/>
              </template>
              <template v-else-if="searchEngine === 'Bing'">
                <rect x="3" y="3" width="8" height="8" rx="1.5" fill="#00809D"/>
                <rect x="13" y="3" width="8" height="8" rx="1.5" fill="#00809D"/>
                <rect x="3" y="13" width="5" height="8" rx="1.5" fill="#00809D"/>
                <rect x="10" y="13" width="11" height="8" rx="1.5" fill="#00809D"/>
              </template>
              <template v-else>
                <circle cx="12" cy="12" r="10" stroke="#94a3b8" stroke-width="2"/>
                <text x="12" y="16" text-anchor="middle" font-size="10" fill="#94a3b8">?</text>
              </template>
            </svg>
            {{ searchEngine }}
          </span>
        </div>
        <div class="result-header-right">
          <span class="elapsed" v-if="elapsedSeconds > 0">{{ elapsedSeconds }}s</span>
          <span class="search-count" v-if="linksFound > 0">
            {{ linksFound }} 链接 · {{ resources.length }} 资源
          </span>
        </div>
      </div>

      <!-- 进度条 -->
      <div class="progress-line" v-if="searching">
        <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
      </div>

      <!-- ──── 搜索汇总面板 ──── -->
      <div class="summary-panel" v-if="!searching && searchState === 'complete'">
        <div class="summary-stat">
          <span class="summary-number">{{ summary.totalLinks }}</span>
          <span class="summary-label">夸克链接</span>
        </div>
        <div class="summary-divider"></div>
        <div class="summary-stat highlight">
          <span class="summary-number">{{ summary.totalResources }}</span>
          <span class="summary-label">有效资源</span>
        </div>
        <div class="summary-divider"></div>
        <div class="summary-stat">
          <span class="summary-number">{{ summary.totalFiles }}</span>
          <span class="summary-label">文件条目</span>
        </div>
        <div class="summary-divider"></div>
        <div class="summary-stat">
          <span class="summary-number">{{ summary.elapsed }}s</span>
          <span class="summary-label">耗时</span>
        </div>
      </div>

      <!-- ──── 站点访问记录（时间线） ──── -->
      <div class="section-block">
        <div class="section-head" @click="timelineOpen = !timelineOpen">
          <span class="section-dot" :class="{ done: searchState === 'complete' }"></span>
          <span class="section-label">站点访问记录</span>
          <span class="section-extra">{{ siteVisits.length }} 个站点</span>
          <svg class="section-caret" :class="{ open: timelineOpen }" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="m6 9 6 6 6-6"/>
          </svg>
        </div>

        <div class="timeline-container" v-show="timelineOpen">
          <!-- 空状态 -->
          <div class="timeline-empty" v-if="siteVisits.length === 0">
            <p>等待访问站点...</p>
          </div>

          <!-- 时间线条目 -->
          <div class="timeline-list">
            <div
              v-for="(visit, vi) in siteVisits"
              :key="vi"
              class="timeline-item"
              :class="visit.status"
            >
              <div class="timeline-track">
                <div class="timeline-node" :class="visit.status">
                  <svg v-if="visit.status === 'found'" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                  <svg v-else-if="visit.status === 'failed'" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                    <path d="M18 6 6 18"/><path d="m6 6 12 12"/>
                  </svg>
                  <svg v-else width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                    <circle cx="12" cy="12" r="3" fill="currentColor"/>
                  </svg>
                </div>
                <div class="timeline-line" v-if="vi < siteVisits.length - 1"></div>
              </div>

              <div class="timeline-card" @click="visit.expanded = !visit.expanded">
                <div class="visit-top">
                  <span class="visit-index">{{ vi + 1 }}</span>
                  <span class="visit-url" :title="visit.url">{{ visit.shortUrl }}</span>
                  <span class="visit-status-tag" :class="visit.status">
                    {{ visit.status === 'found' ? '有资源' : visit.status === 'failed' ? '失败' : '访问中' }}
                  </span>
                  <span class="visit-source-tag" v-if="visit.isSecondary">二级挖掘</span>
                </div>
                <div class="visit-meta" v-if="visit.title">
                  {{ visit.title }}
                </div>
                <div class="visit-extra" v-if="visit.filesCount > 0">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/></svg>
                  {{ visit.filesCount }} 个文件
                </div>
                <a :href="visit.url" target="_blank" class="visit-open" @click.stop>
                  打开链接
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ──── 资源结果 ──── -->
      <div class="section-block" v-if="resources.length > 0">
        <div class="section-head">
          <span class="section-dot accent"></span>
          <span class="section-label">找到的资源</span>
          <span class="section-extra">{{ resources.length }} 个</span>
        </div>

        <div class="resource-grid">
          <div
            v-for="(res, idx) in resources"
            :key="idx"
            class="resource-card"
            @click="toggleResource(idx)"
            :class="{ expanded: expandedResources.has(idx) }"
          >
            <!-- 卡片头部 -->
            <div class="rc-header">
              <div class="rc-index">#{{ idx + 1 }}</div>
              <div class="rc-info">
                <h3 class="rc-title">{{ res.title || '未命名资源' }}</h3>
                <div class="rc-meta">
                  <span v-if="res.files?.length">{{ res.files.length }} 个文件</span>
                  <span class="meta-sep" v-if="res.password_hint">·</span>
                  <span class="rc-password" v-if="res.password_hint">提取码 {{ res.password_hint }}</span>
                </div>
              </div>
              <svg class="rc-caret" :class="{ open: expandedResources.has(idx) }" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="m6 9 6 6 6-6"/>
              </svg>
            </div>

            <!-- 链接行 -->
            <div class="rc-link-row">
              <code class="rc-url">{{ res.url }}</code>
              <button class="rc-copy-btn" @click.stop="copyUrl(res.url)" :class="{ done: copiedUrl === res.url }">
                {{ copiedUrl === res.url ? '已复制' : '复制' }}
              </button>
            </div>

            <!-- 展开区 -->
            <div class="rc-expand" v-show="expandedResources.has(idx)">
              <p class="rc-desc" v-if="res.description">{{ res.description }}</p>
              <ul class="rc-files" v-if="res.files?.length">
                <li v-for="(file, fi) in res.files.slice(0, 50)" :key="fi">{{ file.name }}</li>
                <li class="rc-files-more" v-if="res.files.length > 50">
                  ...还有 {{ res.files.length - 50 }} 项
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <!-- ──── 空结果 ──── -->
      <div class="empty-block" v-if="!searching && resources.length === 0 && searchState === 'complete'">
        <div class="empty-illustration">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="1.2" stroke-linecap="round">
            <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/><line x1="8" y1="11" x2="14" y2="11"/>
          </svg>
        </div>
        <p class="empty-text">未找到相关资源</p>
        <p class="empty-hint">试试更换更具体或更宽泛的关键词</p>
        <button class="btn-back" @click="resetSearch">返回搜索</button>
      </div>

      <!-- ──── 错误 ──── -->
      <div class="empty-block" v-if="searchState === 'error'">
        <div class="empty-illustration">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="1.5" stroke-linecap="round">
            <circle cx="12" cy="12" r="10"/><path d="m12 8v4"/><circle cx="12" cy="16" r="0.5" fill="#ef4444"/>
          </svg>
        </div>
        <p class="empty-text">搜索出错</p>
        <p class="empty-hint">{{ errorMessage }}</p>
        <button class="btn-back" @click="resetSearch">返回搜索</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'

const query = ref('')
const currentQuery = ref('')
const searching = ref(false)
const searchFocused = ref(false)
const searchState = ref('idle')
const errorMessage = ref('')
const steps = ref([])
const resources = ref([])
const siteVisits = ref([])
const timelineOpen = ref(true)
const expandedResources = ref(new Set())
const copiedUrl = ref(null)
const searchInput = ref(null)
const progressPercent = ref(0)
const linksFound = ref(0)
const startTime = ref(null)
const elapsedSeconds = ref(0)
const searchEngine = ref('')
let elapsedTimer = null

const quickTags = ['Python 教程', '电影合集', '考研资料', 'PS 教程', '电子书合集', 'AI 课程']

const appClass = computed(() => ({
  'is-searching': searchState.value === 'searching',
  'has-result': searchState.value === 'complete',
  'is-error': searchState.value === 'error',
}))

const headerBadge = computed(() => {
  switch (searchState.value) {
    case 'searching': return '搜索中'
    case 'complete': return '已完成'
    case 'error': return '出错'
    default: return ''
  }
})

const summary = computed(() => ({
  totalLinks: siteVisits.value.length,
  totalResources: resources.value.length,
  totalFiles: resources.value.reduce((a, r) => a + (r.files?.length || 0), 0),
  elapsed: elapsedSeconds.value,
}))

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
  if (elapsedTimer) clearInterval(elapsedTimer)
  query.value = ''
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
  startTime.value = Date.now()

  elapsedTimer = setInterval(() => {
    elapsedSeconds.value = Math.floor((Date.now() - startTime.value) / 1000)
  }, 1000)

  try {
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
            searchState.value = 'complete'
            searching.value = false
            progressPercent.value = 100
            if (elapsedTimer) clearInterval(elapsedTimer)
            elapsedSeconds.value = Math.floor((Date.now() - startTime.value) / 1000)
            continue
          }
          try {
            const event = JSON.parse(dataStr)
            handleEvent(event)
          } catch (e) {
            // 忽略解析错误
          }
        }
      }
    }
  } catch (err) {
    searchState.value = 'error'
    errorMessage.value = err.message || '网络请求失败'
    searching.value = false
    if (elapsedTimer) clearInterval(elapsedTimer)
  }
}

function handleEvent(event) {
  steps.value.push(event)

  if (event.type === 'link_found') {
    linksFound.value++
    progressPercent.value = Math.min(progressPercent.value + 3, 25)
    if (event.data?.engine && !searchEngine.value) searchEngine.value = event.data.engine
    // 二级页面挖掘的链接以不同样式展示
    const isSecondary = event.data?.source === 'secondary'
    siteVisits.value.push({
      url: event.data?.url || '',
      shortUrl: shortenUrl(event.data?.url || ''),
      status: 'pending',
      title: '',
      filesCount: 0,
      expanded: false,
      isSecondary,
    })
  } else if (event.type === 'resource_found') {
    if (event.data) {
      resources.value.push(event.data)
      // 更新对应的站点访问记录
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
    // 检查是否暗示访问失败
    if (event.message?.includes('访问失败') || event.message?.includes('失败')) {
      const idx = siteVisits.value.length - 1
      if (idx >= 0 && siteVisits.value[idx].status === 'pending') {
        siteVisits.value[idx].status = 'failed'
      }
    }
  } else if (event.type === 'complete') {
    searchState.value = 'complete'
    searching.value = false
    progressPercent.value = 100
    if (elapsedTimer) clearInterval(elapsedTimer)
    elapsedSeconds.value = Math.floor((Date.now() - startTime.value) / 1000)
    if (event.data?.engine) searchEngine.value = event.data.engine
    if (event.data?.resources) {
      resources.value = event.data.resources
    }
  } else if (event.type === 'error') {
    searchState.value = 'error'
    errorMessage.value = event.message
    searching.value = false
    if (elapsedTimer) clearInterval(elapsedTimer)
  }
}

function shortenUrl(url) {
  try {
    const u = new URL(url)
    return u.hostname + u.pathname.slice(0, 40) + (u.pathname.length > 40 ? '...' : '')
  } catch { return url.slice(0, 60) }
}

function toggleResource(idx) {
  const s = new Set(expandedResources.value)
  if (s.has(idx)) s.delete(idx)
  else s.add(idx)
  expandedResources.value = s
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
</script>

<style>
/* ═══════════ CSS Variables ═══════════ */
:root {
  --c-bg:            #fafbfc;
  --c-surface:       #ffffff;
  --c-surface-hover: #f8fafc;
  --c-border:        #e8ecf1;
  --c-border-light:  #f1f5f9;

  --c-text:          #0f172a;
  --c-text-secondary:#475569;
  --c-text-muted:    #94a3b8;

  --c-accent:        #2563eb;
  --c-accent-light:  #dbeafe;
  --c-accent-soft:   #eff6ff;

  --c-success:       #059669;
  --c-success-light: #d1fae5;
  --c-warning:       #d97706;
  --c-warning-light: #fef3c7;
  --c-error:         #dc2626;
  --c-error-light:   #fee2e2;

  --radius-sm:  6px;
  --radius-md:  10px;
  --radius-lg:  14px;
  --radius-xl:  20px;

  --shadow-sm: 0 1px 2px rgba(0,0,0,.04);
  --shadow-md: 0 4px 12px rgba(0,0,0,.06);
  --shadow-lg: 0 8px 30px rgba(0,0,0,.08);

  --font-sans: -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif;
  --font-mono: "SF Mono", "Fira Code", "Consolas", monospace;
  --duration:  .25s;
  --ease:      cubic-bezier(.4,0,.2,1);
}

* { margin:0; padding:0; box-sizing:border-box; }

body {
  font-family: var(--font-sans);
  background: var(--c-bg);
  color: var(--c-text);
  -webkit-font-smoothing: antialiased;
  min-height: 100vh;
}

/* ═══════════ App ═══════════ */
.app {
  min-height: 100vh;
  padding: 0 20px;
  transition: padding var(--duration);
}
.app:not(.has-result):not(.is-error):not(.is-searching) {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding-top: 0;
}

/* ═══════════ 搜索层 ═══════════ */
.search-layer {
  width: 100%;
  max-width: 640px;
  margin: 0 auto;
  transition: all .4s var(--ease);
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
  transition: all .4s var(--ease);
}
.brand-title {
  font-size: 2rem;
  font-weight: 700;
  letter-spacing: -.02em;
  color: var(--c-text);
  margin-bottom: 8px;
}
.brand-desc {
  font-size: .95rem;
  color: var(--c-text-muted);
  line-height: 1.5;
}

/* Logo 过渡 */
.logo-fade-enter-active, .logo-fade-leave-active { transition: all .35s var(--ease); }
.logo-fade-enter-from, .logo-fade-leave-to { opacity: 0; transform: translateY(-12px); }

/* 搜索栏 */
.search-bar {
  display: flex;
  align-items: center;
  gap: 0;
  background: var(--c-surface);
  border: 1.5px solid var(--c-border);
  border-radius: var(--radius-xl);
  padding: 4px 6px 4px 18px;
  transition: all .25s var(--ease);
  box-shadow: var(--shadow-sm);
}
.search-bar.focused {
  border-color: var(--c-accent);
  box-shadow: 0 0 0 3px rgba(37,99,235,.08), var(--shadow-md);
}
.search-icon { color: var(--c-text-muted); flex-shrink: 0; }
.search-input {
  flex: 1;
  border: none;
  outline: none;
  font-size: .95rem;
  padding: 12px 12px;
  background: transparent;
  color: var(--c-text);
  font-family: var(--font-sans);
  min-width: 0;
}
.search-input::placeholder { color: var(--c-text-muted); }
.search-input:disabled { opacity: .6; }

.search-submit {
  width: 44px; height: 44px;
  border: none;
  border-radius: var(--radius-lg);
  background: var(--c-accent);
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all .2s var(--ease);
  flex-shrink: 0;
  opacity: .5;
}
.search-submit.active { opacity: 1; }
.search-submit.active:hover {
  filter: brightness(1.1);
  box-shadow: 0 2px 12px rgba(37,99,235,.3);
}
.search-submit:disabled { opacity: .4; cursor: not-allowed; }

/* 按钮 spinner */
.btn-spinner {
  width: 18px; height: 18px;
  border: 2.5px solid rgba(255,255,255,.25);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin .7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* 热词标签 */
.hot-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 20px;
  justify-content: center;
}
.hot-tag {
  padding: 6px 16px;
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--radius-sm);
  font-size: .8rem;
  color: var(--c-text-secondary);
  cursor: pointer;
  font-family: var(--font-sans);
  transition: all .18s var(--ease);
}
.hot-tag:hover {
  border-color: var(--c-accent);
  color: var(--c-accent);
  background: var(--c-accent-soft);
}

/* ═══════════ 结果层 ═══════════ */
.result-layer {
  max-width: 780px;
  margin: 0 auto 60px;
}

/* ─── 结果头 ─── */
.result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0 16px;
}
.result-header-left, .result-header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}
.query-chip {
  font-weight: 650;
  font-size: .95rem;
  color: var(--c-text);
  letter-spacing: -.01em;
}
.divider-dot { color: var(--c-border); font-weight: 400; }
.header-badge {
  font-size: .75rem;
  font-weight: 500;
  padding: 3px 10px;
  border-radius: var(--radius-sm);
}
.header-badge.searching { background: var(--c-accent-light); color: var(--c-accent); }
.header-badge.complete  { background: var(--c-success-light); color: var(--c-success); }
.header-badge.error     { background: var(--c-error-light); color: var(--c-error); }

.engine-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: .75rem;
  font-weight: 500;
  padding: 3px 10px;
  border-radius: var(--radius-sm);
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  color: var(--c-text-secondary);
}
.engine-icon { flex-shrink: 0; }

.elapsed, .search-count {
  font-size: .78rem;
  color: var(--c-text-muted);
}
.search-count { font-weight: 500; color: var(--c-text-secondary); }

/* 进度条 */
.progress-line {
  height: 3px;
  background: var(--c-border-light);
  border-radius: 2px;
  margin-bottom: 24px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: var(--c-accent);
  border-radius: 2px;
  transition: width .5s var(--ease);
}

/* 汇总面板 */
.summary-panel {
  display: flex;
  align-items: center;
  gap: 0;
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--radius-lg);
  padding: 20px 28px;
  margin-bottom: 24px;
  box-shadow: var(--shadow-sm);
  animation: slideUp .4s var(--ease);
}
@keyframes slideUp { from { opacity:0; transform:translateY(12px); } to { opacity:1; transform:translateY(0); } }

.summary-stat {
  flex: 1;
  text-align: center;
}
.summary-number {
  display: block;
  font-size: 1.75rem;
  font-weight: 700;
  letter-spacing: -.02em;
  color: var(--c-text);
  line-height: 1.2;
}
.summary-stat.highlight .summary-number { color: var(--c-accent); }
.summary-label {
  font-size: .75rem;
  color: var(--c-text-muted);
  margin-top: 2px;
  display: block;
}
.summary-divider {
  width: 1px; height: 36px;
  background: var(--c-border);
  flex-shrink: 0;
}

/* ═══════════ 通用区块 ═══════════ */
.section-block {
  margin-bottom: 20px;
}
.section-head {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 0;
  cursor: pointer;
  user-select: none;
  margin-bottom: 4px;
}
.section-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: var(--c-accent-light);
  flex-shrink: 0;
  transition: background .3s;
}
.section-dot.done { background: var(--c-success); }
.section-dot.accent { background: var(--c-accent); }
.section-label {
  font-size: .86rem;
  font-weight: 600;
  color: var(--c-text);
  letter-spacing: -.01em;
}
.section-extra {
  font-size: .75rem;
  color: var(--c-text-muted);
  margin-left: auto;
}
.section-caret {
  color: var(--c-text-muted);
  flex-shrink: 0;
  transition: transform .2s var(--ease);
}
.section-caret.open { transform: rotate(180deg); }

/* ═══════════ 时间线 ═══════════ */
.timeline-container { animation: slideUp .3s var(--ease); }
.timeline-empty { padding: 32px 0; text-align: center; color: var(--c-text-muted); font-size: .85rem; }

.timeline-list {
  padding: 4px 0 4px 16px;
  border-left: 2px solid transparent;
}
.timeline-item {
  position: relative;
  display: flex;
  gap: 16px;
  padding-bottom: 4px;
}
.timeline-item:last-child { padding-bottom: 0; }

/* 时间线节点 */
.timeline-track {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 24px;
  flex-shrink: 0;
  position: relative;
  left: -28px;
}
.timeline-node {
  width: 24px; height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  z-index: 1;
  transition: all .3s var(--ease);
  background: var(--c-border-light);
  color: var(--c-text-muted);
}
.timeline-node.found  { background: var(--c-success-light); color: var(--c-success); }
.timeline-node.failed { background: var(--c-error-light); color: var(--c-error); }
.timeline-node.pending { background: var(--c-accent-light); color: var(--c-accent); animation: pulse 1.5s infinite; }
@keyframes pulse { 0%,100%{ opacity:.7; } 50%{ opacity:1; } }

.timeline-line {
  width: 2px;
  flex: 1;
  min-height: 20px;
  background: var(--c-border);
  margin: 2px 0;
}

/* 时间线卡片 */
.timeline-card {
  flex: 1;
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--radius-md);
  padding: 12px 16px;
  cursor: pointer;
  transition: all .2s var(--ease);
  margin-bottom: 10px;
  min-width: 0;
}
.timeline-card:hover {
  border-color: var(--c-accent);
  box-shadow: var(--shadow-sm);
}
.visit-top {
  display: flex;
  align-items: center;
  gap: 8px;
}
.visit-index {
  font-size: .72rem;
  font-weight: 700;
  color: var(--c-text-muted);
  background: var(--c-border-light);
  padding: 1px 7px;
  border-radius: var(--radius-sm);
  flex-shrink: 0;
}
.visit-url {
  flex: 1;
  font-size: .8rem;
  font-family: var(--font-mono);
  color: var(--c-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.visit-status-tag {
  font-size: .7rem;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-weight: 500;
  flex-shrink: 0;
}
.visit-status-tag.found  { background: var(--c-success-light); color: var(--c-success); }
.visit-status-tag.failed { background: var(--c-error-light); color: var(--c-error); }
.visit-status-tag.pending { background: var(--c-accent-light); color: var(--c-accent); }
.visit-source-tag {
  font-size: .68rem;
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  font-weight: 500;
  flex-shrink: 0;
  background: var(--c-warning-light);
  color: var(--c-warning);
}

.visit-meta {
  font-size: .78rem;
  color: var(--c-text-muted);
  margin-top: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.visit-extra {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: .75rem;
  color: var(--c-text-secondary);
  margin-top: 6px;
  margin-right: 12px;
}
.visit-open {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: .75rem;
  color: var(--c-accent);
  text-decoration: none;
  margin-top: 6px;
  font-weight: 500;
  transition: gap .2s;
}
.visit-open:hover { gap: 6px; }

/* ═══════════ 资源卡片 ═══════════ */
.resource-grid {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.resource-card {
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: all .2s var(--ease);
  cursor: pointer;
}
.resource-card:hover {
  border-color: var(--c-accent);
  box-shadow: var(--shadow-md);
}
.resource-card.expanded {
  border-color: var(--c-accent);
  box-shadow: var(--shadow-sm);
}

.rc-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px 18px;
}
.rc-index {
  font-size: .72rem;
  font-weight: 700;
  color: #fff;
  background: var(--c-accent);
  padding: 3px 9px;
  border-radius: var(--radius-sm);
  flex-shrink: 0;
  line-height: 1.4;
  margin-top: 2px;
}
.rc-info { flex: 1; min-width: 0; }
.rc-title {
  font-size: .92rem;
  font-weight: 650;
  color: var(--c-text);
  line-height: 1.4;
  letter-spacing: -.01em;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.rc-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: .75rem;
  color: var(--c-text-muted);
  margin-top: 4px;
}
.rc-password {
  color: var(--c-warning);
  font-weight: 500;
}
.meta-sep { color: var(--c-border); }
.rc-caret {
  color: var(--c-text-muted);
  flex-shrink: 0;
  transition: transform .2s var(--ease);
  margin-top: 4px;
}
.rc-caret.open { transform: rotate(180deg); }

.rc-link-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 18px 14px;
}
.rc-url {
  flex: 1;
  font-size: .78rem;
  font-family: var(--font-mono);
  color: var(--c-accent);
  background: var(--c-accent-soft);
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
}
.rc-copy-btn {
  padding: 8px 16px;
  border: 1px solid var(--c-border);
  border-radius: var(--radius-sm);
  background: var(--c-surface);
  font-size: .78rem;
  color: var(--c-text-secondary);
  cursor: pointer;
  font-family: var(--font-sans);
  transition: all .18s var(--ease);
  white-space: nowrap;
}
.rc-copy-btn:hover { border-color: var(--c-accent); color: var(--c-accent); }
.rc-copy-btn.done {
  background: var(--c-success-light);
  border-color: #a7f3d0;
  color: var(--c-success);
}

.rc-expand {
  border-top: 1px solid var(--c-border-light);
  padding: 14px 18px 16px;
  animation: slideUp .25s var(--ease);
}
.rc-desc {
  font-size: .82rem;
  color: var(--c-text-secondary);
  line-height: 1.65;
  margin-bottom: 12px;
}
.rc-files {
  list-style: none;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 2px 16px;
  max-height: 300px;
  overflow-y: auto;
}
.rc-files li {
  font-size: .78rem;
  color: var(--c-text-secondary);
  padding: 5px 0 5px 18px;
  position: relative;
}
.rc-files li::before {
  content: '';
  position: absolute;
  left: 4px;
  top: 13px;
  width: 5px; height: 5px;
  border-radius: 50%;
  background: var(--c-border);
}
.rc-files-more {
  color: var(--c-text-muted) !important;
  font-style: italic;
}

/* ═══════════ 空状态 / 错误 ═══════════ */
.empty-block {
  text-align: center;
  padding: 48px 20px;
}
.empty-illustration { margin-bottom: 16px; }
.empty-text {
  font-size: .95rem;
  color: var(--c-text);
  font-weight: 600;
  margin-bottom: 6px;
}
.empty-hint {
  font-size: .82rem;
  color: var(--c-text-muted);
  margin-bottom: 20px;
}
.btn-back {
  padding: 10px 28px;
  background: var(--c-accent);
  color: #fff;
  border: none;
  border-radius: var(--radius-md);
  font-size: .85rem;
  font-weight: 500;
  cursor: pointer;
  font-family: var(--font-sans);
  transition: all .2s var(--ease);
}
.btn-back:hover {
  filter: brightness(1.08);
  box-shadow: 0 4px 14px rgba(37,99,235,.25);
}

/* ═══════════ 响应式 ═══════════ */
@media (max-width: 640px) {
  .app { padding: 0 12px; }
  .brand-title { font-size: 1.5rem; }
  .brand-desc { font-size: .85rem; }
  .search-input { font-size: .88rem; }
  .summary-panel { padding: 16px 20px; }
  .summary-number { font-size: 1.4rem; }
  .timeline-card { padding: 10px 12px; }
  .rc-header { padding: 12px 14px; }
  .rc-link-row { flex-direction: column; align-items: stretch; padding: 0 14px 12px; }
  .rc-copy-btn { text-align: center; }
  .rc-files { grid-template-columns: 1fr; }
}
</style>
