"""
夸克网盘资源搜索工具 - 后端服务
通过 Google/Bing 搜索 + Playwright 自动化，查找 quark.cn 分享资源
"""

import asyncio
import json
import re
import time
from typing import AsyncGenerator
from urllib.parse import quote, urlparse

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

app = FastAPI(title="资源搜索工具")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SearchRequest(BaseModel):
    query: str
    engine: str = "auto"  # auto, google, bing


class SearchStep(BaseModel):
    type: str  # info, progress, link_found, resource_found, error, complete
    message: str
    data: dict | None = None


# ──────────────────── Playwright 搜索引擎 ────────────────────

SEARCH_QUERY_TEMPLATE = "{query} 夸克网盘"


def extract_quark_links(text: str, base_url: str = "") -> list[str]:
    """从文本中提取所有 quark.cn 分享链接（仅 /s/ 格式）"""
    # 只匹配 pan.quark.cn/s/xxxxx 格式的分享链接
    pattern = r'https?://pan\.quark\.cn/s/[a-zA-Z0-9_\-]+'
    links = re.findall(pattern, text)
    # 也匹配可能出现的 quark.cn/s/ 格式（不带 pan 子域名）
    pattern2 = r'https?://(?:www\.)?quark\.cn/s/[a-zA-Z0-9_\-]+'
    links.extend(re.findall(pattern2, text))
    # 去重
    seen = set()
    result = []
    for link in links:
        if link not in seen:
            seen.add(link)
            result.append(link)
    return result


def is_quark_share_url(url: str) -> bool:
    """判断是否是夸克网盘分享链接（仅 /s/ 格式）"""
    return 'quark.cn' in url and '/s/' in url


def decode_bing_redirect(bing_url: str) -> str:
    """解码 Bing 重定向链接，提取真实 URL"""
    import base64
    try:
        # Bing 重定向格式: https://www.bing.com/ck/a?...&u=a1aHR0cHM6Ly...
        # u 参数前两个字符是前缀，后面是 base64 编码的真实 URL
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(bing_url)
        params = parse_qs(parsed.query)
        u_val = params.get('u', [''])[0]
        if u_val and len(u_val) > 2:
            # 去掉前2个字符前缀，base64 解码
            b64_str = u_val[2:]
            # 补齐 base64 padding
            b64_str += '=' * (4 - len(b64_str) % 4) if len(b64_str) % 4 else ''
            decoded = base64.b64decode(b64_str).decode('utf-8', errors='ignore')
            if decoded.startswith('http'):
                return decoded
    except Exception:
        pass
    return bing_url  # 解码失败返回原 URL


# ──────────────────── 剧集检测与集数比对 ────────────────────

# 剧集编号正则模式（按优先级排序，匹配文件名中的集数）
EPISODE_PATTERNS = [
    r'第\s*0*(\d{1,3})\s*[集話话回篇]',
    r'[Ee][Pp]\.?\s*0*(\d{1,3})\b',
    r'[Ss]\d{1,2}[Ee]0*(\d{1,3})\b',
    r'^0*(\d{1,3})\s*[\.．、]',
    r'0*(\d{1,3})\s*集\b',
    r'【0*(\d{1,3})】',
    r'\[0*(\d{1,3})\]',
    r'^0*(\d{1,3})\s',
    r'0*(\d{1,3})\s*话\b',
    r'第\s*0*(\d{1,3})\s*话\b',
]

# 集数搜索模式（用于从搜索结果文本中提取总集数）
EPISODE_SEARCH_PATTERNS = [
    r'集\s*数\s*[：:]\s*(\d{1,3})',
    r'共\s*(\d{1,3})\s*集',
    r'(\d{1,3})\s*集\s*全',
    r'全\s*(\d{1,3})\s*集',
    r'(\d{1,3})\s*集(?:电视剧|动漫|综艺|国产|韩剧|美剧|日剧)',
    r'更新至\s*(\d{1,3})\s*集',
    r'(\d{1,3})\s*集(?:完结|全)',
]


def parse_episode_number(filename: str) -> int | None:
    """从文件名中解析剧集编号"""
    for pattern in EPISODE_PATTERNS:
        match = re.search(pattern, filename)
        if match:
            num = int(match.group(1))
            if 0 < num < 1000:
                return num
    return None


def extract_episodes_from_files(files: list[dict]) -> dict:
    """从夸克资源文件列表中提取剧集信息"""
    episodes = []
    for f in files:
        name = f.get('name', '')
        ep_num = parse_episode_number(name)
        if ep_num is not None:
            episodes.append(ep_num)

    episodes = sorted(set(episodes))

    return {
        'has_episodes': len(episodes) > 0,
        'episode_list': episodes,
        'episode_count': len(episodes),
        'max_episode': max(episodes) if episodes else 0,
        'min_episode': min(episodes) if episodes else 0,
    }


def compare_episodes(quark_info: dict, total_episodes: int) -> dict:
    """比对夸克资源剧集与官方集数"""
    if not quark_info.get('has_episodes') or total_episodes <= 0:
        return {
            'status': 'unknown',
            'message': '无法从资源中识别剧集编号',
            'quark_max': 0,
            'quark_count': 0,
            'official_total': total_episodes,
            'missing_episodes': [],
        }

    quark_max = quark_info['max_episode']
    quark_count = quark_info['episode_count']
    found_set = set(quark_info['episode_list'])
    all_set = set(range(1, total_episodes + 1))
    missing = sorted(all_set - found_set)

    if quark_count >= total_episodes and len(missing) == 0:
        return {
            'status': 'complete',
            'message': f'剧集完整（{quark_count}/{total_episodes}集）',
            'quark_max': quark_max,
            'quark_count': quark_count,
            'official_total': total_episodes,
            'missing_episodes': [],
        }
    elif quark_max < total_episodes:
        if missing:
            missing_str = f'第{missing[0]}-{missing[-1]}集' if len(missing) > 1 else f'第{missing[0]}集'
        else:
            missing_str = ''
        return {
            'status': 'incomplete',
            'message': f'可能未更新完（已到第{quark_max}集/共{total_episodes}集）'
                       + (f'，缺少{missing_str}' if missing_str else ''),
            'quark_max': quark_max,
            'quark_count': quark_count,
            'official_total': total_episodes,
            'missing_episodes': missing,
        }
    else:
        return {
            'status': 'partial',
            'message': f'有缺集（{quark_count}/{total_episodes}集）',
            'quark_max': quark_max,
            'quark_count': quark_count,
            'official_total': total_episodes,
            'missing_episodes': missing,
        }


async def detect_series_info(context, query: str) -> dict:
    """
    检测关键词是否为电视剧/动漫，并获取总集数
    优先豆瓣，备用 Google/Bing，最后尝试爱奇艺/腾讯视频/优酷
    """
    result = {
        'is_series': False,
        'series_name': '',
        'total_episodes': 0,
        'source': '',
        'url': '',
        'query': query,
    }

    page = await context.new_page()

    try:
        # ──── 方式1: 豆瓣搜索 ────
        try:
            search_url = f'https://www.douban.com/search?q={quote(query)}&cat=1002'
            await page.goto(search_url, wait_until='domcontentloaded', timeout=15000)
            await asyncio.sleep(2)

            subject_link = await page.evaluate('''
                () => {
                    const links = document.querySelectorAll('a[href*="movie.douban.com/subject/"]');
                    for (const a of links) {
                        if (a.href.match(/movie\\.douban\\.com\\/subject\\/\\d+/)) return a.href;
                    }
                    return null;
                }
            ''')

            if subject_link:
                await page.goto(subject_link, wait_until='domcontentloaded', timeout=15000)
                await asyncio.sleep(2)

                page_text = await page.evaluate('() => document.body.innerText')

                ep_match = re.search(r'集\s*数\s*[：:]\s*(\d{1,3})', page_text)
                if ep_match:
                    total_eps = int(ep_match.group(1))
                    title = await page.evaluate('() => document.querySelector("h1")?.textContent?.trim() || ""')
                    result.update({
                        'is_series': True,
                        'series_name': title or query,
                        'total_episodes': total_eps,
                        'source': '豆瓣',
                        'url': subject_link,
                    })
                    return result
        except Exception:
            pass

        # ──── 方式2: Google 搜索 "{keyword} 多少集" ────
        try:
            search_query = f'{query} 多少集'
            google_url = f'https://www.google.com/search?q={quote(search_query)}&hl=zh-CN&num=10'
            await page.goto(google_url, wait_until='domcontentloaded', timeout=15000)
            await asyncio.sleep(2)

            title = await page.title()
            if 'sorry' not in title.lower():
                page_text = await page.evaluate('() => document.body.innerText')
                for pattern in EPISODE_SEARCH_PATTERNS:
                    match = re.search(pattern, page_text)
                    if match:
                        total_eps = int(match.group(1))
                        result.update({
                            'is_series': True,
                            'series_name': query,
                            'total_episodes': total_eps,
                            'source': 'Google',
                            'url': google_url,
                        })
                        return result
        except Exception:
            pass

        # ──── 方式3: Bing 搜索 ────
        try:
            search_query = f'{query} 多少集'
            bing_url = f'https://www.bing.com/search?q={quote(search_query)}&count=10'
            await page.goto(bing_url, wait_until='domcontentloaded', timeout=15000)
            await asyncio.sleep(2)

            page_text = await page.evaluate('() => document.body.innerText')
            for pattern in EPISODE_SEARCH_PATTERNS:
                match = re.search(pattern, page_text)
                if match:
                    total_eps = int(match.group(1))
                    result.update({
                        'is_series': True,
                        'series_name': query,
                        'total_episodes': total_eps,
                        'source': 'Bing',
                        'url': bing_url,
                    })
                    return result
        except Exception:
            pass

        # ──── 方式4: 爱奇艺搜索 ────
        try:
            iqiyi_url = f'https://so.iqiyi.com/so/q_{quote(query)}'
            await page.goto(iqiyi_url, wait_until='domcontentloaded', timeout=15000)
            await asyncio.sleep(2)

            page_text = await page.evaluate('() => document.body.innerText')
            for pattern in EPISODE_SEARCH_PATTERNS:
                match = re.search(pattern, page_text)
                if match:
                    total_eps = int(match.group(1))
                    result.update({
                        'is_series': True,
                        'series_name': query,
                        'total_episodes': total_eps,
                        'source': '爱奇艺',
                        'url': iqiyi_url,
                    })
                    return result
        except Exception:
            pass

        # ──── 方式5: 腾讯视频搜索 ────
        try:
            qq_url = f'https://v.qq.com/search?searchid={quote(query)}'
            await page.goto(qq_url, wait_until='domcontentloaded', timeout=15000)
            await asyncio.sleep(2)

            page_text = await page.evaluate('() => document.body.innerText')
            for pattern in EPISODE_SEARCH_PATTERNS:
                match = re.search(pattern, page_text)
                if match:
                    total_eps = int(match.group(1))
                    result.update({
                        'is_series': True,
                        'series_name': query,
                        'total_episodes': total_eps,
                        'source': '腾讯视频',
                        'url': qq_url,
                    })
                    return result
        except Exception:
            pass

        # ──── 方式6: 优酷搜索 ────
        try:
            youku_url = f'https://so.youku.com/search_video/q_{quote(query)}'
            await page.goto(youku_url, wait_until='domcontentloaded', timeout=15000)
            await asyncio.sleep(2)

            page_text = await page.evaluate('() => document.body.innerText')
            for pattern in EPISODE_SEARCH_PATTERNS:
                match = re.search(pattern, page_text)
                if match:
                    total_eps = int(match.group(1))
                    result.update({
                        'is_series': True,
                        'series_name': query,
                        'total_episodes': total_eps,
                        'source': '优酷',
                        'url': youku_url,
                    })
                    return result
        except Exception:
            pass

    finally:
        await page.close()

    return result


async def search_with_playwright(query: str) -> AsyncGenerator[dict, None]:
    """
    使用 Playwright 搜索并采集夸克网盘资源
    返回 SSE 事件流
    """
    from playwright.async_api import async_playwright

    steps: list[dict] = []
    quark_links: list[str] = []
    resources: list[dict] = []
    engine_name: str = "未知"

    def emit(step_type: str, message: str, data: dict | None = None):
        event = {"type": step_type, "message": message, "data": data}
        steps.append(event)
        return event

    try:
        async with async_playwright() as p:
            # 启动浏览器
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                ]
            )
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/131.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1920, "height": 1080},
                locale="zh-CN",
            )

            page = await context.new_page()

            # ──── 剧集检测 ────
            yield emit("progress", "正在检测剧集信息...")
            series_info = await detect_series_info(context, query)
            if series_info.get('is_series'):
                yield emit("series_detected",
                    f"检测到电视剧「{series_info['series_name']}」共 {series_info['total_episodes']} 集（来源: {series_info['source']}）",
                    series_info)
            else:
                yield emit("progress", "未检测到电视剧信息，继续搜索夸克资源...")

            search_query = SEARCH_QUERY_TEMPLATE.format(query=query)
            yield emit("progress", f'正在搜索: "{search_query}"')

            # ──── 多引擎级联搜索：Google → Bing → 百度 ────
            # 每个引擎搜完后检查是否找到夸克链接，没找到就试下一个
            encoded_query = quote(search_query)
            links = []
            raw_result_links = []

            # 定义搜索引擎配置
            engines = [
                {
                    "name": "Google",
                    "url": f"https://www.google.com/search?q={encoded_query}&hl=zh-CN&num=20",
                    "check_captcha": True,
                },
                {
                    "name": "Bing",
                    "url": f"https://cn.bing.com/search?q={encoded_query}&count=20&setlang=zh-Hans",
                    "check_captcha": False,
                },
                {
                    "name": "Baidu",
                    "url": f"https://www.baidu.com/s?wd={encoded_query}&rn=20",
                    "check_captcha": False,
                },
            ]

            for eng in engines:
                eng_name = eng["name"]
                eng_url = eng["url"]
                engine_name = eng_name
                yield emit("progress", f"正在通过 {eng_name} 搜索...", {"engine": eng_name})
                try:
                    await page.goto(eng_url, wait_until="domcontentloaded", timeout=30000)
                    await asyncio.sleep(2)

                    # Google CAPTCHA 检测
                    if eng["check_captcha"]:
                        current_url = page.url
                        title = await page.title()
                        if "sorry" in current_url or "sorry" in title.lower() or "unusual traffic" in title.lower():
                            yield emit("progress", f"{eng_name} 检测到 CAPTCHA，切换到下一个引擎...")
                            continue

                    # 从 HTML 中正则提取 quark 链接
                    content = await page.content()
                    eng_links = extract_quark_links(content)

                    # 也从 <a> 标签提取
                    result_links = await page.evaluate('''
                        () => {
                            const links = [];
                            document.querySelectorAll('a[href]').forEach(a => {
                                if (a.href && a.href.includes('quark.cn') && a.href.includes('/s/')) links.push(a.href);
                            });
                            return links;
                        }
                    ''')
                    eng_links.extend(result_links)
                    eng_links = list(set(eng_links))

                    # 提取非夸克搜索结果链接（用于二级挖掘）
                    eng_raw_links = await page.evaluate("""
                        () => {
                            const links = [];
                            const seen = new Set();
                            const selectors = [
                                '#search .g a[href]', '#search .yuRUbf a[href]',
                                '#rso a[href]', '#b_results .b_algo h2 a[href]',
                                '.b_algo a[href]', 'h2 a[href]', '.g h3 a[href]',
                                '.b_algo h2 a', 'h2 a',
                                '#content_left .result a[href]', '#content_left .c-container a[href]',
                                '.result a[href]', '.c-container h3 a[href]'
                            ];
                            for (const sel of selectors) {
                                try {
                                    document.querySelectorAll(sel).forEach(a => {
                                        const href = a.href;
                                        if (href && href.startsWith('http') && !seen.has(href)) {
                                            seen.add(href);
                                            links.push(href);
                                        }
                                    });
                                } catch(e) {}
                            }
                            return links;
                        }
                    """)

                    # 解码 Bing 重定向链接
                    for raw_link in eng_raw_links:
                        if 'bing.com/ck/' in raw_link:
                            real_url = decode_bing_redirect(raw_link)
                            if real_url != raw_link and 'quark.cn' in real_url:
                                eng_links.append(real_url)
                            elif real_url != raw_link and real_url.startswith('http'):
                                skip_domains = ['google.com', 'bing.com', 'youtube.com', 'microsoft.com', 'baidu.com']
                                if not any(d in real_url for d in skip_domains):
                                    raw_result_links.append(real_url)
                        elif not any(d in raw_link for d in ['google.com', 'bing.com', 'baidu.com', 'youtube.com']):
                            raw_result_links.append(raw_link)

                    eng_links = list(set(eng_links))
                    links.extend(eng_links)

                    yield emit("progress", f"{eng_name} 找到 {len(eng_links)} 个夸克链接", {"engine": eng_name})

                    if eng_links:
                        break
                    else:
                        yield emit("progress", f"{eng_name} 未找到夸克链接，尝试下一个引擎...", {"engine": eng_name})

                except Exception as e:
                    yield emit("progress", f"{eng_name} 搜索出错: {str(e)[:50]}，尝试下一个引擎...")
                    continue

            # 去重非夸克链接
            raw_result_links = list(dict.fromkeys(raw_result_links))[:8]
            non_quark_result_links = raw_result_links

            # ──── 过滤直接搜到的 quark.cn 分享链接 ────
            quark_links = [l for l in links if is_quark_share_url(l)]
            quark_links = list(set(quark_links))[:10]

            yield emit("progress",
                f"搜索引擎直接找到 {len(quark_links)} 个夸克链接，"
                f"另发现 {len(non_quark_result_links)} 个相关网页可深入挖掘",
                {"engine": engine_name}
            )

            # ──── 步骤 2: 访问非夸克页面，挖掘隐藏的 quark.cn 链接 ────
            secondary_quark_links: list[str] = []
            for idx, page_url in enumerate(non_quark_result_links):
                yield emit("progress",
                    f"🔍 挖掘二级页面 ({idx+1}/{len(non_quark_result_links)}): {page_url[:70]}...",
                    {"engine": engine_name, "type": "deep_crawl"}
                )
                try:
                    await page.goto(page_url, wait_until="domcontentloaded", timeout=15000)
                    await asyncio.sleep(2)

                    # 从页面中提取 quark.cn 链接
                    found_links = await page.evaluate('''
                        () => {
                            const links = [];
                            document.querySelectorAll('a[href*="quark.cn"]').forEach(a => {
                                if (a.href) links.push(a.href);
                            });
                            return links;
                        }
                    ''')
                    # 也通过正则从 HTML 提取
                    page_html = await page.content()
                    found_links.extend(extract_quark_links(page_html))
                    found_links = list(set(found_links))

                    if found_links:
                        yield emit("link_found",
                            f"📎 从 {page_url[:50]}... 发现 {len(found_links)} 个夸克链接",
                            {"url": page_url, "found_links": found_links, "source": "secondary"}
                        )
                        for fl in found_links[:3]:
                            yield emit("link_found", f"   ↳ {fl}", {"url": fl, "source": "secondary"})
                        secondary_quark_links.extend(found_links)
                    else:
                        yield emit("progress", f"   未发现夸克链接，跳过", {"engine": engine_name})

                except Exception as e:
                    yield emit("progress", f"   访问失败: {str(e)[:50]}", {"engine": engine_name})
                    continue

                await asyncio.sleep(0.5)

            # ──── 合并所有 quark.cn 链接 ────
            all_quark = list(set(quark_links + secondary_quark_links))[:15]
            direct_count = len(quark_links)
            secondary_count = len([l for l in all_quark if l not in quark_links])

            yield emit("progress",
                f"共收集 {len(all_quark)} 个夸克链接（直接搜索 {direct_count} + 二级挖掘 {secondary_count}）",
                {"engine": engine_name}
            )

            # 更新 quark_links 为合并后的列表
            quark_links = all_quark

            if not quark_links:
                yield emit("complete", "未找到夸克网盘链接，请尝试其他关键词",
                    {"links": [], "resources": [], "engine": engine_name})
                await browser.close()
                return

            for link in quark_links:
                yield emit("link_found", f"夸克链接: {link}",
                    {"url": link, "engine": engine_name})

            # ──── 步骤 2: 访问每个 quark.cn 链接 ────
            for idx, link in enumerate(quark_links):
                yield emit("progress", f"正在访问 ({idx+1}/{len(quark_links)}): {link[:80]}...")
                try:
                    await page.goto(link, wait_until="domcontentloaded", timeout=30000)
                    await asyncio.sleep(3)  # 等待页面渲染

                    # 获取页面标题
                    page_title = await page.title()
                    page_url = page.url

                    # 提取资源信息
                    resource_info = await page.evaluate('''
                        () => {
                            const result = {
                                title: document.title || '',
                                files: [],
                                description: '',
                                password_hint: ''
                            };

                            // 尝试获取分享标题
                            const titleEl = document.querySelector('.share-title, .title, h1, .folder-title, .share-info-title');
                            if (titleEl) result.title = titleEl.textContent.trim();

                            // 尝试获取文件列表
                            const fileEls = document.querySelectorAll('.file-item, .file-name, .file-title, .list-item, .file-info, [class*="file"], [class*="name"]');
                            fileEls.forEach(el => {
                                const name = el.textContent.trim();
                                if (name && name.length > 1 && name.length < 200) {
                                    // 去重
                                    if (!result.files.find(f => f.name === name)) {
                                        result.files.push({ name: name });
                                    }
                                }
                            });

                            // 获取描述
                            const descEl = document.querySelector('.share-desc, .description, .detail-desc, .intro');
                            if (descEl) result.description = descEl.textContent.trim();

                            // 获取提取码提示
                            const pageText = document.body.innerText;
                            const pwdMatch = pageText.match(/提取码[：:]\\s*(\\w+)/);
                            if (pwdMatch) result.password_hint = pwdMatch[1];

                            return result;
                        }
                    ''')

                    # 也尝试解析整体页面文本
                    page_text = await page.evaluate('() => document.body.innerText')
                    # 从页面文本中提取更多文件信息
                    if not resource_info.get('files') or len(resource_info['files']) == 0:
                        lines = page_text.strip().split('\n')
                        potential_files = []
                        for line in lines:
                            line = line.strip()
                            if not line or len(line) > 300:
                                continue
                            # 包含常见文件扩展名或看起来像文件名
                            if re.search(r'\.\w{2,5}\b', line) or any(
                                kw in line.lower() for kw in ['视频', '电影', '课程', '教程', '资料', '合集', '资源']
                            ):
                                if line not in potential_files:
                                    potential_files.append(line)
                        resource_info['files'] = [{'name': f} for f in potential_files[:20]]

                    resource_data = {
                        "url": page_url,
                        "original_url": link,
                        "title": resource_info.get('title', page_title),
                        "description": resource_info.get('description', ''),
                        "files": resource_info.get('files', []),
                        "password_hint": resource_info.get('password_hint', ''),
                        "page_text_preview": page_text[:500],
                    }

                    # 剧集比对
                    if series_info.get('is_series') and series_info.get('total_episodes', 0) > 0:
                        quark_ep = extract_episodes_from_files(resource_info.get('files', []))
                        ep_match = compare_episodes(quark_ep, series_info['total_episodes'])
                        resource_data['episode_match'] = ep_match
                        resource_data['quark_episodes'] = quark_ep

                    resources.append(resource_data)

                    file_count = len(resource_info.get('files', []))
                    yield emit("resource_found",
                        f"✅ [{page_title[:50]}] 提取到 {file_count} 个资源",
                        resource_data
                    )

                    # 达到 6 个有效资源，提前结束
                    if len(resources) >= 6:
                        yield emit("progress",
                            f"已收集 {len(resources)} 个有效资源，提前结束",
                            {"engine": engine_name})
                        break

                except Exception as e:
                    yield emit("progress", f"访问失败: {str(e)[:100]}")
                    continue

                # 短暂间隔，避免请求过快
                await asyncio.sleep(1)

            await browser.close()

            yield emit("complete",
                f"搜索完成！共找到 {len(resources)} 个有效资源",
                {
                    "query": query,
                    "engine": engine_name,
                    "series_info": series_info,
                    "total_links": len(quark_links),
                    "total_resources": len(resources),
                    "links": quark_links,
                    "resources": resources,
                    "steps": steps,
                }
            )

    except Exception as e:
        yield emit("error", f"搜索过程出错: {str(e)}")


# ──────────────────── API 路由 ────────────────────

@app.get("/api/search")
async def search_stream(query: str = Query(..., description="搜索关键词")):
    """
    SSE 流式搜索接口
    实时返回搜索进度和结果
    """
    async def event_generator():
        async for event in search_with_playwright(query):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.post("/api/search")
async def search_post(req: SearchRequest):
    """POST 方式搜索（同样返回 SSE 流）"""
    async def event_generator():
        async for event in search_with_playwright(req.query):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.get("/api/health")
async def health():
    return {"status": "ok", "timestamp": time.time()}


# ──────────────────── 启动入口 ────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
