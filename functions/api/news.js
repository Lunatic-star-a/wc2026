// Cloudflare Pages Function — GET /api/news?team=西班牙
// 作用：把球队资讯请求转发给新闻提供商，让 API key 只留在服务器端。
// 同时解决浏览器跨域(CORS)问题 —— 因为前端调用的是同源的 /api/news。
//
// 接入步骤：
//   1. 选择一个新闻 API 提供商（示例用 NewsAPI.org；国内可换成聚合数据、天行数据等）
//   2. Cloudflare 控制台 → Pages 项目 → Settings → Environment variables
//      新增 NEWS_API_KEY = 你的密钥
//   3. 按所选提供商的返回格式调整下面的解析逻辑，重新部署
//   4. 前端 myteam.html 的 loadTeamNews 改为先请求 /api/news，失败再回退到内置缓存
//
// 前端调用：GET /api/news?team=西班牙  →  返回 {items:[{title,snippet,url}]}

export async function onRequestGet(context) {
  const { request, env } = context;
  const url = new URL(request.url);
  const team = url.searchParams.get('team') || '';

  if (!env.NEWS_API_KEY) {
    // 未配置时返回空，前端会自动回退到内置资讯缓存
    return Response.json({ items: [], note: 'NEWS_API_KEY 未配置，使用内置资讯' });
  }

  const q = encodeURIComponent(team + ' 世界杯 2026');
  try {
    // ── 示例：NewsAPI.org。换提供商时改这一段即可。 ──
    const r = await fetch(
      `https://newsapi.org/v2/everything?q=${q}&language=zh&sortBy=publishedAt&pageSize=4&apiKey=${env.NEWS_API_KEY}`
    );
    const j = await r.json();
    const items = (j.articles || []).map(a => ({
      title: a.title || '',
      snippet: a.description || '',
      url: a.url || '#',
    }));
    return Response.json({ items });
  } catch (e) {
    return Response.json({ items: [], error: String(e) }, { status: 502 });
  }
}
