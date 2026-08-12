<template>
  <div class="app" :class="appClass">
    <!-- 背景装饰 -->
    <div class="bg-deco">
      <div class="bg-blob blob-1"></div>
      <div class="bg-blob blob-2"></div>
      <div class="bg-blob blob-3"></div>
    </div>

    <!-- ═══════════ 搜索区 ═══════════ -->
    <div class="search-layer">
      <transition name="logo-fade">
        <div class="brand" v-if="searchState === 'idle'">
          <div class="brand-icon">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
              <circle cx="9" cy="10" r="1.2" fill="currentColor"/>
              <circle cx="13" cy="10" r="1.2" fill="currentColor"/>
              <circle cx="17" cy="10" r="1.2" fill="currentColor"/>
            </svg>
          </div>
          <h1 class="brand-title">夸克资源搜索</h1>
          <p class="brand-desc">在全网搜索夸克网盘分享资源，智能识别剧集完整性</p>
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
            placeholder="输入资源名称，如 庆余年、Python 教程..."
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

        <transition name="tags-fade">
          <div class="hot-tags" v-if="searchState === 'idle'">
            <button
              v-for="tag in quickTags"
              :key="tag"
              class="hot-tag"
              @click="query = tag; startSearch()"
            >{{ tag }}</button>
          </div>
        </transition>
      </div>

      <!-- 演示模式提示 -->
      <div class="demo-banner" v-if="isDemoMode && searchState === 'idle'">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>
        <span>演示模式 — 展示搜索流程效果，实际使用需启动后端服务</span>
      </div>
    </div>

    <!-- ═══════════ 结果区 ═══════════ -->
    <div class="result-layer" v-if="searchState !== 'idle'">
      <!-- ──── 状态头 ──── -->
      <div class="result-header">
        <div class="result-header-left">
          <span class="query-chip">{{ currentQuery }}</span>
          <span class="divider-dot" v-if="searchEngine">·</span>
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
              <template v-else-if="searchEngine === 'Baidu'">
                <path d="M8 3a5 5 0 0 0-5 5v8a5 5 0 0 0 5 5h3a5 5 0 0 0 5-5V8a5 5 0 0 0-5-5H8z" fill="#2932E1"/>
                <path d="M14 8c0-2.8 2.2-5 5-5s5 2.2 5 5v8c0 2.8-2.2 5-5 5s-5-2.2-5-5V8z" fill="#2932E1" opacity="0.6"/>
                <text x="9" y="17" text-anchor="middle" font-size="10" font-weight="bold" fill="#fff">B</text>
              </template>
              <template v-else>
                <circle cx="12" cy="12" r="10" stroke="#94a3b8" stroke-width="2"/>
                <text x="12" y="16" text-anchor="middle" font-size="10" fill="#94a3b8">?</text>
              </template>
            </svg>
            {{ searchEngine }}
          </span>
          <span class="header-badge" :class="searchState">
            {{ headerBadge }}
          </span>
        </div>
        <div class="result-header-right">
          <span class="elapsed" v-if="elapsedSeconds > 0">{{ elapsedSeconds }}s</span>
          <span class="search-count" v-if="linksFound > 0">
            {{ linksFound }} 链接 · {{ resources.length }} 资源
          </span>
          <button class="btn-new-search" @click="resetSearch" v-if="!searching">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 4v6h-6"/><path d="M1 20v-6h6"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10"/><path d="M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>
            新搜索
          </button>
        </div>
      </div>

      <!-- 进度条 -->
      <div class="progress-line" v-if="searching">
        <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
      </div>

      <!-- 自动完成倒计时 -->
      <div class="auto-complete-hint" v-if="showAutoComplete">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
        已找到 {{ resources.length }} 个资源，{{ autoCompleteCountdown }}s 后自动完成
        <button class="btn-complete-now" @click="forceComplete">立即完成</button>
      </div>

      <!-- ──── 剧集信息面板 ──── -->
      <div class="series-panel" v-if="seriesInfo?.is_series">
        <div class="series-icon">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <rect x="2" y="3" width="20" height="14" rx="2"/>
            <line x1="8" y1="21" x2="16" y2="21"/>
            <line x1="12" y1="17" x2="12" y2="21"/>
          </svg>
        </div>
        <div class="series-content">
          <div class="series-title">{{ seriesInfo.series_name }}</div>
          <div class="series-meta">
            <span class="series-eps">共 {{ seriesInfo.total_episodes }} 集</span>
            <span class="series-sep">·</span>
            <span class="series-source-tag">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none">
                <template v-if="seriesInfo.source === '豆瓣'">
                  <circle cx="12" cy="12" r="10" fill="#007722"/>
                  <text x="12" y="16" text-anchor="middle" font-size="9" fill="#fff" font-weight="bold">豆</text>
                </template>
                <template v-else-if="seriesInfo.source === 'Google'">
                  <path d="M12 5a7 7 0 1 0 0 14 7 7 0 0 0 0-14" fill="#4285F4"/>
                  <path d="M5 12h14" stroke="#EA4335" stroke-width="2"/>
                </template>
                <template v-else-if="seriesInfo.source === 'Bing'">
                  <rect x="3" y="3" width="18" height="18" rx="3" fill="#00809D"/>
                  <text x="12" y="16" text-anchor="middle" font-size="9" fill="#fff" font-weight="bold">b</text>
                </template>
                <template v-else-if="seriesInfo.source === '爱奇艺'">
                  <rect x="3" y="3" width="18" height="18" rx="3" fill="#00BE06"/>
                  <text x="12" y="16" text-anchor="middle" font-size="8" fill="#fff">IQY</text>
                </template>
                <template v-else-if="seriesInfo.source === '腾讯视频'">
                  <rect x="3" y="3" width="18" height="18" rx="3" fill="#FF6022"/>
                  <text x="12" y="16" text-anchor="middle" font-size="9" fill="#fff">TV</text>
                </template>
                <template v-else-if="seriesInfo.source === '优酷'">
                  <rect x="3" y="3" width="18" height="18" rx="3" fill="#1EBEFF"/>
                  <text x="12" y="16" text-anchor="middle" font-size="8" fill="#fff">YK</text>
                </template>
                <template v-else>
                  <circle cx="12" cy="12" r="10" stroke="#94a3b8" stroke-width="2"/>
                </template>
              </svg>
              来源: {{ seriesInfo.source }}
            </span>
          </div>
        </div>
      </div>

      <!-- ──── 搜索步骤日志 ──── -->
      <div class="steps-log" v-if="searching">
        <transition-group name="step-fade" tag="div">
          <div v-for="(step, si) in visibleSteps" :key="si" class="step-item" :class="step.type">
            <span class="step-icon" v-if="step.type === 'resource_found'">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
            </span>
            <span class="step-icon spin" v-else-if="step.type === 'progress'">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 12a9 9 0 1 1-6.22-8.56"/></svg>
            </span>
            <span class="step-text">{{ step.message }}</span>
          </div>
        </transition-group>
      </div>

      <!-- ═══════════ 总览页面 ═══════════ -->
      <transition name="overview-fade">
        <div class="overview-page" v-if="!searching && searchState === 'complete' && resources.length > 0">
          <!-- 总览头部 -->
          <div class="overview-header">
            <div class="overview-success-ring">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22 4 12 14.01 9 11.01"/>
              </svg>
            </div>
            <h2 class="overview-title">搜索完成</h2>
            <p class="overview-subtitle">为「{{ currentQuery }}」找到 {{ resources.length }} 个有效资源</p>
          </div>

          <!-- 统计卡片 -->
          <div class="stats-grid">
            <div class="stat-card" :class="{ highlight: true }">
              <div class="stat-icon-wrap accent">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
              </div>
              <div class="stat-body">
                <span class="stat-num">{{ animatedResources }}</span>
                <span class="stat-label">有效资源</span>
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-icon-wrap">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
              </div>
              <div class="stat-body">
                <span class="stat-num">{{ animatedLinks }}</span>
                <span class="stat-label">夸克链接</span>
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-icon-wrap">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14 2z"/><polyline points="14 2 14 8 20 8"/></svg>
              </div>
              <div class="stat-body">
                <span class="stat-num">{{ animatedFiles }}</span>
                <span class="stat-label">文件条目</span>
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-icon-wrap">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
              </div>
              <div class="stat-body">
                <span class="stat-num">{{ elapsedSeconds }}s</span>
                <span class="stat-label">搜索耗时</span>
              </div>
            </div>
          </div>

          <!-- 资源卡片网格 -->
          <div class="overview-section-title">
            <span class="ost-dot"></span>
            <span>资源列表</span>
            <span class="ost-count">{{ resources.length }} 个</span>
          </div>

          <div class="resource-grid">
            <div
              v-for="(res, idx) in resources"
              :key="idx"
              class="resource-card"
              :class="{ expanded: expandedResources.has(idx) }"
              :style="{ '--card-delay': idx * 0.08 + 's' }"
              @click="toggleResource(idx)"
            >
              <!-- 卡片头部 -->
              <div class="rc-header">
                <div class="rc-index">#{{ idx + 1 }}</div>
                <div class="rc-info">
                  <h3 class="rc-title">{{ res.title || '未命名资源' }}</h3>
                  <div class="rc-meta">
                    <span v-if="res.files?.length" class="rc-meta-chip">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14 2z"/></svg>
                      {{ res.files.length }} 文件
                    </span>
                    <span class="rc-meta-chip password" v-if="res.password_hint">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                      提取码 {{ res.password_hint }}
                    </span>
                    <span class="rc-ep-badge" v-if="res.episode_match" :class="res.episode_match.status">
                      {{ epBadgeText(res.episode_match) }}
                    </span>
                  </div>
                </div>
                <svg class="rc-caret" :class="{ open: expandedResources.has(idx) }" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="m6 9 6 6 6-6"/>
                </svg>
              </div>

              <!-- 链接行 -->
              <div class="rc-link-row">
                <code class="rc-url">{{ res.url }}</code>
                <a :href="res.url" target="_blank" class="rc-open-btn" @click.stop>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
                  打开
                </a>
                <button class="rc-copy-btn" @click.stop="copyUrl(res.url)" :class="{ done: copiedUrl === res.url }">
                  {{ copiedUrl === res.url ? '已复制' : '复制链接' }}
                </button>
              </div>

              <!-- 展开区 -->
              <transition name="expand">
                <div class="rc-expand" v-show="expandedResources.has(idx)">
                  <!-- 剧集比对详情 -->
                  <div class="rc-episode-detail" v-if="res.episode_match">
                    <div class="rc-ep-detail-header">
                      <span class="rc-ep-detail-label">剧集比对</span>
                      <span class="rc-ep-status" :class="res.episode_match.status">
                        {{ res.episode_match.message }}
                      </span>
                    </div>
                    <div class="rc-ep-stats" v-if="res.episode_match.official_total > 0">
                      <div class="rc-ep-stat">
                        <span class="rc-ep-stat-num">{{ res.episode_match.quark_count || 0 }}</span>
                        <span class="rc-ep-stat-label">夸克集数</span>
                      </div>
                      <div class="rc-ep-stat-divider"></div>
                      <div class="rc-ep-stat">
                        <span class="rc-ep-stat-num">{{ res.episode_match.official_total }}</span>
                        <span class="rc-ep-stat-label">官方总集数</span>
                      </div>
                      <div class="rc-ep-stat-divider" v-if="res.episode_match.missing_episodes?.length"></div>
                      <div class="rc-ep-stat" v-if="res.episode_match.missing_episodes?.length">
                        <span class="rc-ep-stat-num warn">{{ res.episode_match.missing_episodes.length }}</span>
                        <span class="rc-ep-stat-label">缺失集数</span>
                      </div>
                    </div>
                    <div class="rc-ep-missing" v-if="res.episode_match.missing_episodes?.length">
                      <span class="rc-ep-missing-label">缺失：</span>
                      <span v-for="ep in res.episode_match.missing_episodes.slice(0, 30)" :key="ep" class="rc-missing-ep">{{ ep }}</span>
                      <span v-if="res.episode_match.missing_episodes.length > 30" class="rc-missing-more">...</span>
                    </div>
                  </div>

                  <p class="rc-desc" v-if="res.description">{{ res.description }}</p>
                  <ul class="rc-files" v-if="res.files?.length">
                    <li v-for="(file, fi) in res.files.slice(0, 50)" :key="fi">
                      <span class="rc-file-icon"></span>
                      {{ file.name }}
                    </li>
                    <li class="rc-files-more" v-if="res.files.length > 50">
                      ...还有 {{ res.files.length - 50 }} 项
                    </li>
                  </ul>
                </div>
              </transition>
            </div>
          </div>

          <!-- 站点访问记录折叠 -->
          <details class="site-details">
            <summary class="site-details-summary">
              <span class="sd-dot"></span>
              <span>站点访问记录</span>
              <span class="sd-count">{{ siteVisits.length }} 个站点</span>
              <svg class="sd-caret" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m6 9 6 6 6-6"/></svg>
            </summary>
            <div class="site-list">
              <div v-for="(visit, vi) in siteVisits" :key="vi" class="site-row" :class="visit.status">
                <span class="site-node" :class="visit.status">
                  <svg v-if="visit.status === 'found'" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>
                  <svg v-else-if="visit.status === 'failed'" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
                  <span v-else class="site-node-dot"></span>
                </span>
                <span class="site-url" :title="visit.url">{{ visit.shortUrl }}</span>
                <span class="site-tag" :class="visit.status">
                  {{ visit.status === 'found' ? '有资源' : visit.status === 'failed' ? '失败' : '跳过' }}
                </span>
                <span class="site-source" v-if="visit.isSecondary">二级</span>
              </div>
            </div>
          </details>
        </div>
      </transition>

      <!-- ──── 空结果 ──── -->
      <div class="empty-block" v-if="!searching && resources.length === 0 && searchState === 'complete'">
        <div class="empty-illustration">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#cbd5e1" stroke-width="1.2" stroke-linecap="round">
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
import { ref, reactive, computed, onMounted, watch, nextTick } from 'vue'

const query = ref('')
const currentQuery = ref('')
const searching = ref(false)
const searchFocused = ref(false)
const searchState = ref('idle') // idle, searching, complete, error
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
const seriesInfo = ref(null)
let elapsedTimer = null

// 自动完成逻辑
const showAutoComplete = ref(false)
const autoCompleteCountdown = ref(0)
let autoCompleteTimer = null
let lastResourceTime = null
const AUTO_COMPLETE_DELAY = 6 // 找到资源后 6 秒无新资源就自动完成

// 动画数字
const animatedResources = ref(0)
const animatedLinks = ref(0)
const animatedFiles = ref(0)

// 演示模式检测
const isDemoMode = computed(() => {
  return window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1'
    || new URLSearchParams(window.location.search).has('demo')
})

const quickTags = ['庆余年', 'Python 教程', '繁花', 'PS 教程', '电子书合集', 'AI 课程']

const appClass = computed(() => ({
  'is-searching': searching.value,
  'has-result': searchState.value === 'complete' && resources.value.length > 0,
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

const visibleSteps = computed(() => {
  // 搜索中只显示最近 5 条
  return steps.value.slice(-5)
})

const totalFiles = computed(() => resources.value.reduce((a, r) => a + (r.files?.length || 0), 0))

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
  seriesInfo.value = null
  showAutoComplete.value = false
  autoCompleteCountdown.value = 0
  animatedResources.value = 0
  animatedLinks.value = 0
  animatedFiles.value = 0
  if (elapsedTimer) clearInterval(elapsedTimer)
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

// 当新资源到达时重置计时器
watch(() => resources.value.length, (newLen, oldLen) => {
  if (newLen > 0 && searching.value) {
    lastResourceTime = Date.now()
    if (newLen >= 1) {
      startAutoCompleteTimer()
    }
  }
})

function forceComplete() {
  clearAutoComplete()
  if (searching.value) {
    searchState.value = 'complete'
    searching.value = false
    progressPercent.value = 100
    if (elapsedTimer) clearInterval(elapsedTimer)
    elapsedSeconds.value = Math.floor((Date.now() - startTime.value) / 1000)
    // 触发数字动画
    animateNumbers()
  }
}

function animateNumbers() {
  // 数字递增动画
  const targets = {
    res: resources.value.length,
    links: linksFound.value,
    files: totalFiles.value,
  }
  const duration = 800
  const start = Date.now()
  const tick = () => {
    const elapsed = Date.now() - start
    const t = Math.min(elapsed / duration, 1)
    const easeOut = 1 - Math.pow(1 - t, 3)
    animatedResources.value = Math.round(targets.res * easeOut)
    animatedLinks.value = Math.round(targets.links * easeOut)
    animatedFiles.value = Math.round(targets.files * easeOut)
    if (t < 1) requestAnimationFrame(tick)
  }
  tick()
}

async function startSearch() {
  const q = query.value.trim()
  if (!q || searching.value) return

  // 重置
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
  seriesInfo.value = null
  showAutoComplete.value = false
  lastResourceTime = null
  startTime.value = Date.now()

  elapsedTimer = setInterval(() => {
    elapsedSeconds.value = Math.floor((Date.now() - startTime.value) / 1000)
  }, 1000)

  try {
    // 演示模式：使用 mock 数据
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
            if (searching.value) {
              searchState.value = 'complete'
              searching.value = false
              progressPercent.value = 100
              if (elapsedTimer) clearInterval(elapsedTimer)
              elapsedSeconds.value = Math.floor((Date.now() - startTime.value) / 1000)
              clearAutoComplete()
              animateNumbers()
            }
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
    // 如果后端不可用，回退到演示模式
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

  if (event.type === 'series_detected') {
    seriesInfo.value = event.data
    progressPercent.value = Math.min(progressPercent.value + 10, 30)
  } else if (event.type === 'link_found') {
    linksFound.value++
    progressPercent.value = Math.min(progressPercent.value + 3, 25)
    if (event.data?.engine && !searchEngine.value) searchEngine.value = event.data.engine
    const isSecondary = event.data?.source === 'secondary'
    // 只为真正的夸克分享链接创建站点记录
    if (event.data?.url && event.data.url.includes('quark.cn')) {
      siteVisits.value.push({
        url: event.data.url,
        shortUrl: shortenUrl(event.data.url),
        status: 'pending',
        title: '',
        filesCount: 0,
        isSecondary,
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
    if (event.data?.series_info) seriesInfo.value = event.data.series_info
    if (event.data?.resources) {
      resources.value = event.data.resources
    }
    clearAutoComplete()
    animateNumbers()
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

// ──────────────────── 演示模式 ────────────────────

async function runDemoSearch(q) {
  const mockEvents = generateMockEvents(q)
  for (const evt of mockEvents) {
    await new Promise(r => setTimeout(r, evt._delay || 300))
    handleEvent(evt)
  }
  // 确保完成
  if (searching.value) {
    searchState.value = 'complete'
    searching.value = false
    progressPercent.value = 100
    if (elapsedTimer) clearInterval(elapsedTimer)
    elapsedSeconds.value = Math.floor((Date.now() - startTime.value) / 1000)
    clearAutoComplete()
    animateNumbers()
  }
}

function generateMockEvents(q) {
  const isSeries = ['庆余年', '繁花', '狂飙', '三体', '琅琊榜', '甄嬛传', '隐秘的', '雪中'].some(s => q.includes(s))
  const events = []

  if (isSeries) {
    events.push({ type: 'progress', message: '正在检测剧集信息...', _delay: 500 })
    events.push({ type: 'progress', message: '正在通过豆瓣搜索...', _delay: 800 })
    events.push({
      type: 'series_detected',
      message: '检测到电视剧「' + q + '」共 40 集（来源: 豆瓣）',
      data: { is_series: true, series_name: q, total_episodes: 40, source: '豆瓣' },
      _delay: 600,
    })
  }

  events.push({ type: 'progress', message: '正在搜索: "' + q + ' 夸克网盘"', _delay: 400 })
  events.push({ type: 'progress', message: '正在通过 Google 搜索...', data: { engine: 'Google' }, _delay: 1000 })
  events.push({ type: 'progress', message: 'Google 检测到 CAPTCHA，切换到下一个引擎...', _delay: 600 })
  events.push({ type: 'progress', message: '正在通过 Bing 搜索...', data: { engine: 'Bing' }, _delay: 1000 })
  events.push({ type: 'progress', message: 'Bing 未找到夸克链接，尝试下一个引擎...', data: { engine: 'Bing' }, _delay: 500 })
  events.push({ type: 'progress', message: '正在通过 Baidu 搜索...', data: { engine: 'Baidu' }, _delay: 1200 })
  events.push({ type: 'progress', message: 'Baidu 找到 5 个夸克链接', data: { engine: 'Baidu' }, _delay: 400 })

  // 模拟找到链接
  const mockLinks = [
    'https://pan.quark.cn/s/abc123def456',
    'https://pan.quark.cn/s/xyz789ghi012',
    'https://pan.quark.cn/s/mno345pqr678',
    'https://pan.quark.cn/s/stu901vwx234',
    'https://pan.quark.cn/s/yza567bcd890',
  ]
  for (const link of mockLinks) {
    events.push({ type: 'link_found', message: '夸克链接: ' + link, data: { url: link, engine: 'Baidu' }, _delay: 200 })
  }

  // 模拟二级挖掘
  events.push({ type: 'progress', message: '搜索引擎直接找到 5 个夸克链接，另发现 3 个相关网页可深入挖掘', data: { engine: 'Baidu' }, _delay: 300 })
  events.push({ type: 'progress', message: '挖掘二级页面 (1/3): https://www.csdn.net/article/...', _delay: 600 })
  events.push({ type: 'link_found', message: '从 www.csdn.net... 发现 1 个夸克链接', data: { url: 'https://pan.quark.cn/s/extra123', source: 'secondary' }, _delay: 200 })
  events.push({ type: 'progress', message: '挖掘二级页面 (2/3): https://www.zhihu.com/question/...', _delay: 500 })
  events.push({ type: 'progress', message: '未发现夸克链接，跳过', _delay: 300 })
  events.push({ type: 'progress', message: '挖掘二级页面 (3/3): https://www.bilibili.com/read/...', _delay: 500 })
  events.push({ type: 'link_found', message: '从 www.bilibili.com... 发现 2 个夸克链接', data: { url: 'https://pan.quark.cn/s/bili456', source: 'secondary' }, _delay: 200 })
  events.push({ type: 'progress', message: '共收集 7 个夸克链接（直接搜索 5 + 二级挖掘 2）', _delay: 400 })

  // 模拟访问每个夸克链接
  const mockResources = [
    { title: q + ' 全集 1080P 蓝光版', files: Array.from({ length: 40 }, (_, i) => ({ name: `第${String(i+1).padStart(2,'0')}集.mkv` })), password: '', url: mockLinks[0] },
    { title: q + ' 1-40集完整版 高清', files: Array.from({ length: 40 }, (_, i) => ({ name: `${q} EP${String(i+1).padStart(2,'0')}.mp4` })), password: 'a1b2', url: mockLinks[1] },
    { title: q + ' 全季合集 4K HDR', files: Array.from({ length: 35 }, (_, i) => ({ name: `[${String(i+1).padStart(2,'0')}] ${q}.mkv` })), password: '', url: mockLinks[2] },
    { title: q + ' 国语中字 全40集', files: Array.from({ length: 40 }, (_, i) => ({ name: `${q} 第${i+1}集.mp4` })), password: 'qwer', url: mockLinks[3] },
    { title: q + ' 粤语版 1-38集', files: Array.from({ length: 38 }, (_, i) => ({ name: `0${i+1}.${q}.mkv` })), password: '', url: mockLinks[4] },
  ]

  mockResources.forEach((res, i) => {
    events.push({ type: 'progress', message: `正在访问 (${i+1}/7): ${res.url}...`, _delay: 500 })
    const resourceData = {
      url: res.url,
      title: res.title,
      description: i === 0 ? '高清完整版，包含全40集，画质优秀，推荐下载。' : '',
      files: res.files,
      password_hint: res.password,
    }
    if (isSeries) {
      const quarkEp = { has_episodes: true, episode_list: res.files.map((_,i)=>i+1), episode_count: res.files.length, max_episode: res.files.length }
      let epMatch
      if (res.files.length >= 40) {
        epMatch = { status: 'complete', message: '剧集完整（40/40集）', quark_max: res.files.length, quark_count: res.files.length, official_total: 40, missing_episodes: [] }
      } else if (res.files.length < 40) {
        const missing = Array.from({length: 40 - res.files.length}, (_,i) => res.files.length + i + 1)
        epMatch = { status: 'incomplete', message: `可能未更新完（已到第${res.files.length}集/共40集）`, quark_max: res.files.length, quark_count: res.files.length, official_total: 40, missing_episodes: missing }
      }
      resourceData.episode_match = epMatch
    }
    events.push({ type: 'resource_found', message: `✅ [${res.title}] 提取到 ${res.files.length} 个资源`, data: resourceData, _delay: 800 })
  })

  events.push({
    type: 'complete',
    message: '搜索完成！共找到 5 个有效资源',
    data: {
      query: q,
      engine: 'Baidu',
      series_info: isSeries ? { is_series: true, series_name: q, total_episodes: 40, source: '豆瓣' } : null,
      total_links: 7,
      total_resources: 5,
      links: mockLinks,
      resources: mockResources.map((res, i) => {
        const resourceData = {
          url: res.url,
          title: res.title,
          description: i === 0 ? '高清完整版，包含全40集，画质优秀，推荐下载。' : '',
          files: res.files,
          password_hint: res.password,
        }
        if (isSeries) {
          if (res.files.length >= 40) {
            resourceData.episode_match = { status: 'complete', message: '剧集完整（40/40集）', quark_max: 40, quark_count: 40, official_total: 40, missing_episodes: [] }
          } else {
            const missing = Array.from({length: 40 - res.files.length}, (_,i) => res.files.length + i + 1)
            resourceData.episode_match = { status: 'incomplete', message: `可能未更新完（已到第${res.files.length}集/共40集）`, quark_max: res.files.length, quark_count: res.files.length, official_total: 40, missing_episodes: missing }
          }
        }
        return resourceData
      }),
    },
    _delay: 300,
  })

  return events
}

onMounted(() => {
  nextTick(() => searchInput.value?.focus())
})
</script>

<style>
/* ═══════════ CSS Variables ═══════════ */
:root {
  --c-bg:            #f8fafc;
  --c-surface:       #ffffff;
  --c-surface-hover: #f8fafc;
  --c-border:        #e2e8f0;
  --c-border-light:  #f1f5f9;

  --c-text:          #0f172a;
  --c-text-secondary:#475569;
  --c-text-muted:    #94a3b8;

  --c-accent:        #3b82f6;
  --c-accent-dark:   #2563eb;
  --c-accent-light:  #dbeafe;
  --c-accent-soft:   #eff6ff;

  --c-success:       #10b981;
  --c-success-light: #d1fae5;
  --c-warning:      #f59e0b;
  --c-warning-light: #fef3c7;
  --c-error:         #ef4444;
  --c-error-light:   #fee2e2;

  --radius-sm:  8px;
  --radius-md:  12px;
  --radius-lg:  16px;
  --radius-xl:  24px;

  --shadow-sm: 0 1px 2px rgba(0,0,0,.04), 0 1px 3px rgba(0,0,0,.03);
  --shadow-md: 0 4px 6px -1px rgba(0,0,0,.05), 0 2px 4px -2px rgba(0,0,0,.04);
  --shadow-lg: 0 10px 30px -5px rgba(0,0,0,.08), 0 4px 12px -2px rgba(0,0,0,.04);
  --shadow-xl: 0 20px 50px -10px rgba(0,0,0,.1);

  --font-sans: -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif;
  --font-mono: "SF Mono", "Fira Code", "Cascadia Code", Consolas, monospace;
  --duration:  .25s;
  --ease:      cubic-bezier(.4,0,.2,1);
  --ease-spring: cubic-bezier(.34,1.56,.64,1);
}

* { margin:0; padding:0; box-sizing:border-box; }

body {
  font-family: var(--font-sans);
  background: var(--c-bg);
  color: var(--c-text);
  -webkit-font-smoothing: antialiased;
  min-height: 100vh;
  overflow-x: hidden;
}

/* ═══════════ 背景装饰 ═══════════ */
.bg-deco {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;
}
.bg-blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.5;
}
.blob-1 { width: 400px; height: 400px; background: #dbeafe; top: -100px; right: -50px; animation: float 20s ease-in-out infinite; }
.blob-2 { width: 300px; height: 300px; background: #e0e7ff; bottom: -50px; left: -80px; animation: float 25s ease-in-out infinite reverse; }
.blob-3 { width: 200px; height: 200px; background: #f0fdf4; top: 40%; left: 50%; animation: float 30s ease-in-out infinite; }
@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30px, -30px) scale(1.1); }
  66% { transform: translate(-20px, 20px) scale(0.95); }
}

/* ═══════════ App ═══════════ */
.app {
  min-height: 100vh;
  padding: 0 20px 60px;
  position: relative;
  z-index: 1;
  transition: padding var(--duration);
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
  max-width: 600px;
  margin: 0 auto;
  transition: all .4s var(--ease);
}
.app.is-searching .search-layer,
.app.has-result .search-layer,
.app.is-error .search-layer {
  max-width: 720px;
  margin-top: 40px;
  margin-bottom: 24px;
}

/* 品牌 */
.brand {
  text-align: center;
  margin-bottom: 48px;
  transition: all .4s var(--ease);
}
.brand-icon {
  width: 72px;
  height: 72px;
  margin: 0 auto 20px;
  border-radius: var(--radius-lg);
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 24px rgba(59,130,246,.25);
  animation: brandPulse 3s ease-in-out infinite;
}
@keyframes brandPulse {
  0%, 100% { box-shadow: 0 8px 24px rgba(59,130,246,.25); }
  50% { box-shadow: 0 8px 32px rgba(59,130,246,.4); }
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

/* 过渡 */
.logo-fade-enter-active, .logo-fade-leave-active { transition: all .35s var(--ease); }
.logo-fade-enter-from, .logo-fade-leave-to { opacity: 0; transform: translateY(-12px); }
.tags-fade-enter-active, .tags-fade-leave-active { transition: all .3s var(--ease); }
.tags-fade-enter-from, .tags-fade-leave-to { opacity: 0; transform: translateY(8px); }

/* 搜索栏 */
.search-bar {
  display: flex;
  align-items: center;
  gap: 0;
  background: var(--c-surface);
  border: 2px solid var(--c-border);
  border-radius: var(--radius-xl);
  padding: 4px 6px 4px 18px;
  transition: all .25s var(--ease);
  box-shadow: var(--shadow-md);
}
.search-bar.focused {
  border-color: var(--c-accent);
  box-shadow: 0 0 0 4px rgba(59,130,246,.1), var(--shadow-lg);
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
  box-shadow: 0 2px 12px rgba(59,130,246,.3);
  transform: scale(1.05);
}
.search-submit:disabled { opacity: .4; cursor: not-allowed; }

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
  padding: 7px 18px;
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: 20px;
  font-size: .82rem;
  color: var(--c-text-secondary);
  cursor: pointer;
  font-family: var(--font-sans);
  transition: all .2s var(--ease);
}
.hot-tag:hover {
  border-color: var(--c-accent);
  color: var(--c-accent);
  background: var(--c-accent-soft);
  transform: translateY(-2px);
  box-shadow: var(--shadow-sm);
}

/* 演示模式提示 */
.demo-banner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 24px;
  padding: 10px 20px;
  background: var(--c-accent-soft);
  border: 1px solid var(--c-accent-light);
  border-radius: var(--radius-md);
  font-size: .8rem;
  color: var(--c-accent-dark);
}

/* ═══════════ 结果层 ═══════════ */
.result-layer {
  max-width: 800px;
  margin: 0 auto;
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
.divider-dot { color: var(--c-border); }
.header-badge {
  font-size: .75rem;
  font-weight: 500;
  padding: 3px 10px;
  border-radius: 20px;
}
.header-badge.searching { background: var(--c-accent-light); color: var(--c-accent-dark); }
.header-badge.complete  { background: var(--c-success-light); color: var(--c-success); }
.header-badge.error     { background: var(--c-error-light); color: var(--c-error); }

.engine-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: .75rem;
  font-weight: 500;
  padding: 3px 10px;
  border-radius: 20px;
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  color: var(--c-text-secondary);
}

.elapsed, .search-count {
  font-size: .78rem;
  color: var(--c-text-muted);
}
.search-count { font-weight: 500; color: var(--c-text-secondary); }

.btn-new-search {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 14px;
  border: 1px solid var(--c-border);
  border-radius: 20px;
  background: var(--c-surface);
  font-size: .78rem;
  color: var(--c-text-secondary);
  cursor: pointer;
  font-family: var(--font-sans);
  transition: all .2s var(--ease);
}
.btn-new-search:hover { border-color: var(--c-accent); color: var(--c-accent); }

/* 进度条 */
.progress-line {
  height: 4px;
  background: var(--c-border-light);
  border-radius: 2px;
  margin-bottom: 20px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--c-accent), #6366f1);
  border-radius: 2px;
  transition: width .5s var(--ease);
}

/* 自动完成提示 */
.auto-complete-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: var(--c-warning-light);
  border: 1px solid #fde68a;
  border-radius: var(--radius-md);
  margin-bottom: 16px;
  font-size: .82rem;
  color: var(--c-warning);
  animation: slideUp .3s var(--ease);
}
.auto-complete-hint svg { color: var(--c-warning); flex-shrink: 0; }
.btn-complete-now {
  margin-left: auto;
  padding: 4px 14px;
  border: none;
  border-radius: 20px;
  background: var(--c-warning);
  color: #fff;
  font-size: .78rem;
  cursor: pointer;
  font-family: var(--font-sans);
  transition: all .2s var(--ease);
}
.btn-complete-now:hover { filter: brightness(1.1); }

/* ═══════════ 剧集信息面板 ═══════════ */
.series-panel {
  display: flex;
  align-items: center;
  gap: 14px;
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--radius-lg);
  padding: 16px 20px;
  margin-bottom: 20px;
  box-shadow: var(--shadow-sm);
  animation: slideUp .4s var(--ease);
}
.series-icon {
  width: 44px; height: 44px;
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, var(--c-accent-soft), #e0e7ff);
  color: var(--c-accent);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.series-content { flex: 1; min-width: 0; }
.series-title {
  font-size: .95rem;
  font-weight: 650;
  color: var(--c-text);
  letter-spacing: -.01em;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.series-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 4px;
}
.series-eps {
  font-size: .8rem;
  font-weight: 600;
  color: var(--c-accent-dark);
}
.series-sep { color: var(--c-border); }
.series-source-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: .75rem;
  color: var(--c-text-muted);
}

/* ═══════════ 步骤日志 ═══════════ */
.steps-log {
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--radius-lg);
  padding: 12px 16px;
  margin-bottom: 20px;
  max-height: 180px;
  overflow-y: auto;
  box-shadow: var(--shadow-sm);
}
.step-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
  font-size: .8rem;
}
.step-icon {
  width: 18px; height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.step-item.resource_found { color: var(--c-success); }
.step-item.resource_found .step-icon { color: var(--c-success); }
.step-item.progress { color: var(--c-text-muted); }
.step-item.progress .step-icon { color: var(--c-accent); }
.step-icon.spin svg { animation: spin 1.2s linear infinite; }
.step-text {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.step-fade-enter-active { transition: all .3s var(--ease); }
.step-fade-enter-from { opacity: 0; transform: translateX(-12px); }

/* ═══════════ 总览页面 ═══════════ */
.overview-page {
  animation: overviewIn .5s var(--ease);
}
@keyframes overviewIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.overview-header {
  text-align: center;
  padding: 24px 0 20px;
}
.overview-success-ring {
  width: 64px; height: 64px;
  margin: 0 auto 16px;
  border-radius: 50%;
  background: var(--c-success-light);
  color: var(--c-success);
  display: flex;
  align-items: center;
  justify-content: center;
  animation: successPop .5s var(--ease-spring);
}
@keyframes successPop {
  0% { transform: scale(0); }
  100% { transform: scale(1); }
}
.overview-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--c-text);
  letter-spacing: -.02em;
  margin-bottom: 6px;
}
.overview-subtitle {
  font-size: .9rem;
  color: var(--c-text-muted);
}

/* 统计卡片网格 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 28px;
}
.stat-card {
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--radius-lg);
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  box-shadow: var(--shadow-sm);
  transition: all .2s var(--ease);
}
.stat-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}
.stat-card.highlight { border-color: var(--c-accent); }
.stat-icon-wrap {
  width: 40px; height: 40px;
  border-radius: var(--radius-md);
  background: var(--c-border-light);
  color: var(--c-text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.stat-icon-wrap.accent { background: var(--c-accent-soft); color: var(--c-accent); }
.stat-body { min-width: 0; }
.stat-num {
  display: block;
  font-size: 1.5rem;
  font-weight: 700;
  letter-spacing: -.02em;
  color: var(--c-text);
  line-height: 1.2;
}
.stat-card.highlight .stat-num { color: var(--c-accent); }
.stat-label {
  font-size: .72rem;
  color: var(--c-text-muted);
}

.overview-section-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}
.ost-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: var(--c-accent);
}
.overview-section-title span:nth-child(2) {
  font-size: .9rem;
  font-weight: 600;
  color: var(--c-text);
}
.ost-count {
  font-size: .75rem;
  color: var(--c-text-muted);
  margin-left: auto;
}

/* ═══════════ 资源卡片 ═══════════ */
.resource-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.resource-card {
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: all .25s var(--ease);
  cursor: pointer;
  box-shadow: var(--shadow-sm);
  animation: cardIn .4s var(--ease) backwards;
  animation-delay: var(--card-delay, 0s);
}
@keyframes cardIn {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}
.resource-card:hover {
  border-color: var(--c-accent);
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}
.resource-card.expanded {
  border-color: var(--c-accent);
  box-shadow: var(--shadow-lg);
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
  background: linear-gradient(135deg, var(--c-accent), #6366f1);
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
  gap: 8px;
  margin-top: 6px;
  flex-wrap: wrap;
}
.rc-meta-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: .72rem;
  color: var(--c-text-muted);
  background: var(--c-border-light);
  padding: 2px 8px;
  border-radius: 20px;
}
.rc-meta-chip.password { color: var(--c-warning); background: var(--c-warning-light); }

.rc-ep-badge {
  font-size: .7rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 20px;
  flex-shrink: 0;
}
.rc-ep-badge.complete { background: var(--c-success-light); color: var(--c-success); }
.rc-ep-badge.incomplete { background: var(--c-warning-light); color: var(--c-warning); }
.rc-ep-badge.partial { background: #fff3e0; color: #e65100; }
.rc-ep-badge.unknown { background: var(--c-border-light); color: var(--c-text-muted); }

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
  gap: 8px;
  padding: 0 18px 14px;
}
.rc-url {
  flex: 1;
  font-size: .78rem;
  font-family: var(--font-mono);
  color: var(--c-accent-dark);
  background: var(--c-accent-soft);
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
}
.rc-open-btn, .rc-copy-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 8px 14px;
  border: 1px solid var(--c-border);
  border-radius: var(--radius-sm);
  background: var(--c-surface);
  font-size: .78rem;
  color: var(--c-text-secondary);
  cursor: pointer;
  font-family: var(--font-sans);
  transition: all .18s var(--ease);
  white-space: nowrap;
  text-decoration: none;
}
.rc-open-btn { color: var(--c-accent); }
.rc-open-btn:hover, .rc-copy-btn:hover { border-color: var(--c-accent); color: var(--c-accent); }
.rc-copy-btn.done {
  background: var(--c-success-light);
  border-color: #a7f3d0;
  color: var(--c-success);
}

/* 展开区 */
.rc-expand {
  border-top: 1px solid var(--c-border-light);
  padding: 14px 18px 16px;
}

.expand-enter-active, .expand-leave-active { transition: all .25s var(--ease); }
.expand-enter-from, .expand-leave-to { opacity: 0; max-height: 0; }
.expand-enter-to, .expand-leave-from { opacity: 1; max-height: 1000px; }

/* 剧集比对详情 */
.rc-episode-detail {
  background: var(--c-bg);
  border: 1px solid var(--c-border);
  border-radius: var(--radius-md);
  padding: 14px 16px;
  margin-bottom: 14px;
}
.rc-ep-detail-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}
.rc-ep-detail-label {
  font-size: .78rem;
  font-weight: 600;
  color: var(--c-text-secondary);
}
.rc-ep-status {
  font-size: .75rem;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 20px;
}
.rc-ep-status.complete { background: var(--c-success-light); color: var(--c-success); }
.rc-ep-status.incomplete { background: var(--c-warning-light); color: var(--c-warning); }
.rc-ep-status.partial { background: #fff3e0; color: #e65100; }
.rc-ep-status.unknown { background: var(--c-border-light); color: var(--c-text-muted); }

.rc-ep-stats {
  display: flex;
  align-items: center;
  gap: 0;
  margin-bottom: 10px;
}
.rc-ep-stat { flex: 1; text-align: center; }
.rc-ep-stat-num {
  display: block;
  font-size: 1.3rem;
  font-weight: 700;
  color: var(--c-text);
  line-height: 1.2;
}
.rc-ep-stat-num.warn { color: var(--c-error); }
.rc-ep-stat-label {
  font-size: .7rem;
  color: var(--c-text-muted);
}
.rc-ep-stat-divider {
  width: 1px; height: 32px;
  background: var(--c-border);
  flex-shrink: 0;
}

.rc-ep-missing {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
}
.rc-ep-missing-label {
  font-size: .75rem;
  color: var(--c-text-muted);
  margin-right: 4px;
}
.rc-missing-ep {
  font-size: .72rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 20px;
  background: var(--c-error-light);
  color: var(--c-error);
}
.rc-missing-more { font-size: .72rem; color: var(--c-text-muted); }

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
  display: flex;
  align-items: center;
  gap: 6px;
}
.rc-file-icon {
  width: 4px; height: 4px;
  border-radius: 50%;
  background: var(--c-accent);
  flex-shrink: 0;
  position: absolute;
  left: 4px;
}
.rc-files-more {
  color: var(--c-text-muted) !important;
  font-style: italic;
}

/* ═══════════ 站点记录折叠 ═══════════ */
.site-details {
  margin-top: 20px;
  border: 1px solid var(--c-border);
  border-radius: var(--radius-lg);
  background: var(--c-surface);
  box-shadow: var(--shadow-sm);
}
.site-details-summary {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  cursor: pointer;
  user-select: none;
  list-style: none;
}
.site-details-summary::-webkit-details-marker { display: none; }
.sd-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: var(--c-accent-light);
}
.site-details-summary span:nth-child(2) {
  font-size: .86rem;
  font-weight: 600;
  color: var(--c-text);
}
.sd-count {
  font-size: .75rem;
  color: var(--c-text-muted);
  margin-left: auto;
}
.sd-caret {
  color: var(--c-text-muted);
  transition: transform .2s var(--ease);
}
details[open] .sd-caret { transform: rotate(180deg); }

.site-list { padding: 0 16px 12px; }
.site-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 0;
  font-size: .8rem;
}
.site-node {
  width: 18px; height: 18px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.site-node.found { background: var(--c-success-light); color: var(--c-success); }
.site-node.failed { background: var(--c-error-light); color: var(--c-error); }
.site-node.pending { background: var(--c-border-light); color: var(--c-text-muted); }
.site-node-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--c-text-muted);
}
.site-url {
  flex: 1;
  font-family: var(--font-mono);
  color: var(--c-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
}
.site-tag {
  font-size: .68rem;
  padding: 2px 8px;
  border-radius: 20px;
  font-weight: 500;
  flex-shrink: 0;
}
.site-tag.found { background: var(--c-success-light); color: var(--c-success); }
.site-tag.failed { background: var(--c-error-light); color: var(--c-error); }
.site-tag.pending { background: var(--c-border-light); color: var(--c-text-muted); }
.site-source {
  font-size: .65rem;
  padding: 2px 6px;
  border-radius: 20px;
  background: var(--c-warning-light);
  color: var(--c-warning);
  flex-shrink: 0;
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
  box-shadow: 0 4px 14px rgba(59,130,246,.25);
  transform: translateY(-1px);
}

/* ═══════════ 动画 ═══════════ */
@keyframes slideUp { from { opacity:0; transform:translateY(12px); } to { opacity:1; transform:translateY(0); } }

.overview-fade-enter-active { transition: all .4s var(--ease); }
.overview-fade-enter-from { opacity: 0; transform: translateY(20px); }

/* ═══════════ 响应式 ═══════════ */
@media (max-width: 640px) {
  .app { padding: 0 12px 40px; }
  .brand-title { font-size: 1.5rem; }
  .brand-desc { font-size: .85rem; }
  .search-input { font-size: .88rem; }
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
  .stat-num { font-size: 1.2rem; }
  .rc-header { padding: 12px 14px; }
  .rc-link-row { flex-wrap: wrap; padding: 0 14px 12px; }
  .rc-files { grid-template-columns: 1fr; }
  .result-header { flex-wrap: wrap; gap: 8px; }
}
</style>
