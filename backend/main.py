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
    """从文本中提取所有 quark.cn 链接"""
    pattern = r'https?://[^\s"\'<>]*quark\.cn[^\s"\'<>]*'
    links = re.findall(pattern, text)
    # 去重并清理
    seen = set()
    result = []
    for link in links:
        # 清理尾部标点
        link = re.sub(r'[,;.!?。，；！？)\]>}\'"]+$', '', link)
        if link not in seen:
            seen.add(link)
            result.append(link)
    return result


def is_quark_share_url(url: str) -> bool:
    """判断是否是夸克网盘分享链接"""
    return 'quark.cn' in url and ('/s/' in url or 'share' in url.lower())


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

            search_query = SEARCH_QUERY_TEMPLATE.format(query=query)
            yield emit("progress", f'正在搜索: "{search_query}"')

            # ──── 步骤 1: Google 搜索 ────
            try:
                encoded_query = quote(search_query)
                engine_name = "Google"
                google_url = f"https://www.google.com/search?q={encoded_query}&hl=zh-CN&num=20"
                yield emit("progress", "正在通过 Google 搜索...", {"engine": engine_name})

                await page.goto(google_url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(2)  # 等待加载

                # 检查是否被拦截
                title = await page.title()
                if "sorry" in title.lower() or "unusual traffic" in title.lower():
                    yield emit("progress", "Google 检测到异常流量，切换到 Bing 搜索...")
                    raise Exception("Google captcha")

                # 获取所有链接
                content = await page.content()
                links = extract_quark_links(content)

                # 也尝试获取搜索结果链接
                result_links = await page.evaluate('''
                    () => {
                        const links = [];
                        document.querySelectorAll('a[href]').forEach(a => {
                            const href = a.href;
                            if (href && href.includes('quark.cn')) {
                                links.push(href);
                            }
                        });
                        return links;
                    }
                ''')
                links.extend(result_links)
                links = list(set(links))

            except Exception as e:
                # Google 失败，尝试 Bing
                yield emit("progress", f"Google 搜索失败 ({str(e)[:50]})，尝试 Bing...")
                try:
                    engine_name = "Bing"
                    encoded_query = quote(search_query)
                    bing_url = f"https://www.bing.com/search?q={encoded_query}&count=20"
                    await page.goto(bing_url, wait_until="domcontentloaded", timeout=30000)
                    await asyncio.sleep(2)

                    content = await page.content()
                    links = extract_quark_links(content)

                    result_links = await page.evaluate('''
                        () => {
                            const links = [];
                            document.querySelectorAll('a[href]').forEach(a => {
                                const href = a.href;
                                if (href && href.includes('quark.cn')) {
                                    links.push(href);
                                }
                            });
                            return links;
                        }
                    ''')
                    links.extend(result_links)
                    links = list(set(links))
                except Exception as e2:
                    yield emit("error", f"所有搜索引擎均失败: {str(e2)[:100]}")
                    await browser.close()
                    return

            # ──── 同时提取搜索结果中的非夸克页面链接（用来做二级挖掘）────
            non_quark_result_links = await page.evaluate(f'''
                () => {{
                    const links = [];
                    const seen = new Set();
                    const selectors = [
                        '#search .g a[href]', '#search .yuRUbf a[href]',
                        '#rso a[href]', '#b_results .b_algo h2 a[href]',
                        '.b_algo a[href]', 'h2 a[href]', '.g h3 a[href]'
                    ];
                    for (const sel of selectors) {{
                        try {{
                            document.querySelectorAll(sel).forEach(a => {{
                                const href = a.href;
                                if (href && href.startsWith('http') && !href.includes('quark.cn')
                                    && !href.includes('google.com') && !href.includes('bing.com')
                                    && !href.includes('youtube.com') && !seen.has(href)) {{
                                    seen.add(href);
                                    links.push(href);
                                }}
                            }});
                        }} catch(e) {{}}
                    }}
                    return links.slice(0, 8);
                }}
            ''')
            non_quark_result_links = list(dict.fromkeys(non_quark_result_links))[:8]  # 去重，最多8个

            # ──── 过滤直接搜到的 quark.cn 链接 ────
            quark_links = [l for l in links if 'quark.cn' in l]
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
