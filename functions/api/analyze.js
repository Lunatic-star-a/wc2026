// Cloudflare Pages Function — POST /api/analyze
// 作用：把 AI 分析请求转发给 DeepSeek，让 API key 只留在服务器端，永不出现在浏览器里。
//
// 接入步骤：
//   1. Cloudflare 控制台 → 你的 Pages 项目 → Settings → Environment variables
//   2. 新增变量 DEEPSEEK_API_KEY = 你的 DeepSeek 密钥（在 platform.deepseek.com 申请）
//   3. 重新部署。前端 myteam.html 里把 generateStaticAnalysis(...) 换成 getAIAnalysis(...) 即可。
//
// 前端调用：POST /api/analyze  body: {team, en, rank, group}  →  返回 {text}

export async function onRequestPost(context) {
  const { request, env } = context;

  if (!env.DEEPSEEK_API_KEY) {
    return Response.json({ error: 'DEEPSEEK_API_KEY 未配置' }, { status: 500 });
  }

  let body;
  try { body = await request.json(); }
  catch (e) { return Response.json({ error: 'invalid json' }, { status: 400 }); }

  const { team, en, rank, group } = body || {};
  const prompt =
    `你是资深足球数据分析师。请用中文为「${team}」(${en || ''}，FIFA排名#${rank || '?'}，` +
    `${group || '?'}组) 撰写一段约 200 字的 2026 世界杯前景分析，` +
    `涵盖：小组出线形势、阵容攻防特点、核心球员、晋级概率与潜在风险。语气专业客观。`;

  try {
    const r = await fetch('https://api.deepseek.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + env.DEEPSEEK_API_KEY,
      },
      body: JSON.stringify({
        model: 'deepseek-chat',
        messages: [{ role: 'user', content: prompt }],
        temperature: 0.7,
        max_tokens: 600,
      }),
    });
    const j = await r.json();
    const text = (j && j.choices && j.choices[0] && j.choices[0].message && j.choices[0].message.content) || '';
    return Response.json({ text });
  } catch (e) {
    return Response.json({ error: String(e) }, { status: 502 });
  }
}
