# Match Data v3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Seven fixes to match data modal: injury time monitoring, formation alignment, event cards, goal type differentiation, English names (remove Chinese), jersey numbers in events, scrollbar removal.

**Architecture:** Single-file changes to `worldcuppro.html`. Delete ~1000 lines of Chinese translation tables and functions. Replace event timeline with card-based layout. Keep ESPN_TEAM_CN only for internal _pollESPN matching (ALL_MATCHES has Chinese team names).

**Tech Stack:** Vanilla HTML/CSS/JS, ESPN public API, Supabase backend

**Key design decisions:**
- ESPN_TEAM_CN + _espnTeamToCN kept ONLY for _pollESPN matching bridge (ESPN English → ALL_MATCHES Chinese). Name changed to reflect limited scope.
- All display names use raw ESPN English values.
- Event goal type detected from text patterns (Own Goal, Penalty, free kick, No Goal/disallowed).
- Jersey numbers parsed from `ev.athletes[].jersey` array.

---

### Task 1: CSS — scrollbar, formation alignment, event cards, goal type legend

**Files:**
- Modify: `D:\websites\worldcuppro.html` (CSS sections)

- [ ] **Step 1: Hide scrollbar on match-data-body**

Add after line 223 (`.match-data-body`):
```css
.match-data-body::-webkit-scrollbar{width:0;display:none}
.match-data-body{scrollbar-width:none;-ms-overflow-style:none}
```

- [ ] **Step 2: Fix formation alignment — equal height columns**

Change line 742 `.data-lineups-grid`:
```css
.data-lineups-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;align-items:stretch}
```
Add to `.data-lineup-col` (line 743):
```css
.data-lineup-col{background:var(--slate);border:1px solid rgba(255,255,255,0.06);border-radius:var(--radius);padding:16px;display:flex;flex-direction:column}
```

- [ ] **Step 3: Replace event timeline CSS with card-based layout**

Delete lines 757-769 (`.data-event-list` through `.data-event-text`) and replace with:
```css
/* Event cards */
.data-event-cards{display:flex;flex-direction:column;gap:8px}
.data-event-card{background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.05);border-radius:8px;padding:10px 12px;display:flex;align-items:flex-start;gap:10px;position:relative;overflow:hidden}
.data-event-card::before{content:'';position:absolute;left:0;top:0;bottom:0;width:3px;border-radius:3px 0 0 3px}
.data-event-card.event-goal::before{background:var(--pitch)}
.data-event-card.event-penalty::before{background:#ff8c00}
.data-event-card.event-own-goal::before{background:#e03030}
.data-event-card.event-freekick::before{background:#9b59b6}
.data-event-card.event-disallowed::before{background:#666}
.data-event-card.event-yellow::before{background:#f0c040}
.data-event-card.event-red::before{background:#e03030}
.data-event-card.event-sub::before{background:var(--pitch)}
.data-event-card.event-period::before{background:rgba(255,255,255,0.15)}
.data-event-card-time{font-family:var(--font-mono);font-size:10px;color:var(--text-dim);min-width:36px;text-align:right;flex-shrink:0}
.data-event-card-icon{font-size:14px;flex-shrink:0;width:22px;text-align:center}
.data-event-card-text{font-size:12px;color:var(--text);flex:1;line-height:1.4}
.data-event-card-text.goal-text{color:#4caf50;font-weight:600}
.data-event-card-text.penalty-text{color:#ff8c00;font-weight:600}
.data-event-card-text.own-goal-text{color:#e03030;font-weight:600}
.data-event-card-text.freekick-text{color:#c39bdb;font-weight:600}
.data-event-card-text.disallowed-text{color:#888;text-decoration:line-through}
/* Legend */
.data-event-legend{display:flex;flex-wrap:wrap;gap:8px 14px;padding:8px 0 14px;font-size:10px;color:var(--text-dim)}
.data-event-legend span{display:flex;align-items:center;gap:4px}
.data-event-legend .leg-dot{width:8px;height:8px;border-radius:2px;flex-shrink:0}
```

- [ ] **Step 4: Commit**

```bash
git add worldcuppro.html
git commit -m "feat: match data v3 CSS — scrollbar, alignment, event cards, legend"
```

---

### Task 2: Delete Chinese translation code

**Files:**
- Modify: `D:\websites\worldcuppro.html`

- [ ] **Step 1: Delete POS_CN object + posCN() function (lines 1487-1489)**

Remove:
```javascript
/* ─── Position abbreviation → Chinese ─── */
var POS_CN={G:'门将',GK:'门将','CD-L':'左中卫','CD-R':'右中卫',...};
function posCN(abbr){if(!abbr)return'';return POS_CN[abbr]||POS_CN[abbr.toUpperCase()]||abbr;}
```

- [ ] **Step 2: Delete pcn() function (lines 1490-1505)**

Remove the entire `/* ─── Player name → Chinese ─── */` block and `function pcn(name){...}` through line 1505.

- [ ] **Step 3: Delete translateEvent() function (lines 1507-1567)**

Remove the entire `/* ─── Translate ESPN event text → Chinese ─── */` block and `function translateEvent(ev){...}` through line 1567.

- [ ] **Step 4: Delete PLAYER_SURNAME_CN object (line 2248)**

Remove the entire `var PLAYER_SURNAME_CN={...};` declaration (long single line).

- [ ] **Step 5: Delete TEAM_PLAYER_CN object (line 2249)**

Remove the entire `var TEAM_PLAYER_CN={...};` declaration (long single line).

- [ ] **Step 6: Commit**

```bash
git add worldcuppro.html
git commit -m "refactor: remove Chinese translation code (pcn, translateEvent, name tables)"
```

---

### Task 3: Update renderMatchData — English names, event cards, goal types, jersey numbers

**Files:**
- Modify: `D:\websites\worldcuppro.html` (renderMatchData function ~lines 1610-1740)

- [ ] **Step 1: Use English team names in modal header**

At line 1621, change:
```javascript
var hn=_espnTeamToCN(home.team.displayName),an=_espnTeamToCN(away.team.displayName);
```
To:
```javascript
var hn=home.team.displayName,an=away.team.displayName;
```

- [ ] **Step 2: Use English player names in formation grid**

At line 1681, change:
```javascript
var p=field[pi],nameCN=pcn(p.athlete.displayName);
html+='<div class="data-formation-player" title="'+p.athlete.displayName+'"><span class="data-fp-num">'+(p.jersey||'?')+'</span><span class="data-fp-name">'+nameCN+'</span></div>';
```
To:
```javascript
var p=field[pi],playerName=p.athlete.displayName;
html+='<div class="data-formation-player" title="'+playerName+'"><span class="data-fp-num">'+(p.jersey||'?')+'</span><span class="data-fp-name">'+playerName+'</span></div>';
```

At line 1688, change:
```javascript
html+='<div class="data-formation-row"><div class="data-formation-player" title="'+gk.athlete.displayName+' · 门将"><span class="data-fp-num">'+(gk.jersey||'?')+'</span><span class="data-fp-name">'+pcn(gk.athlete.displayName)+'</span></div></div>';
```
To:
```javascript
html+='<div class="data-formation-row"><div class="data-formation-player" title="'+gk.athlete.displayName+' · GK"><span class="data-fp-num">'+(gk.jersey||'?')+'</span><span class="data-fp-name">'+gk.athlete.displayName+'</span></div></div>';
```

At line 1691, change `pcn(p.athlete.displayName)` to `p.athlete.displayName` and `🔄 替补` to `Subs`:
```javascript
html+='<div style="font-size:10px;color:var(--text-dim);margin:8px 0 4px">Subs</div><div class="data-bench-grid">'+subs.map(function(p){return'<div class="data-bench-chip"><span class="bc-num">'+(p.jersey||'?')+'</span><span>'+p.athlete.displayName+'</span></div>';}).join('')+'</div>';
```

- [ ] **Step 3: Replace event rendering with card-based layout + goal type detection + jersey numbers**

Replace the entire events section (lines 1697-1727, from `/* ─── Events ─── */` through the end of the event list rendering) with:

```javascript
  /* ─── Events ─── */
  var events=summary.keyEvents||[];
  var seenEvents={},significant=[];
  for(var ei=0;ei<events.length;ei++){
    var ev=events[ei];
    if(!ev.type||!ev.type.text)continue;
    var eventKey=(ev.clock&&ev.clock.displayValue||'')+'|'+(ev.text||ev.shortText||'');
    if(seenEvents[eventKey])continue;
    seenEvents[eventKey]=true;
    var typeText=ev.type.text,rawText=(ev.text||ev.shortText||'').toLowerCase();
    // Filter: only show goals, cards, penalties, substitutions, and period markers
    var keep=false;
    if(typeText.indexOf('Goal')>=0||typeText.indexOf('Penalty')>=0||typeText.indexOf('Yellow')>=0||typeText.indexOf('Red')>=0||typeText.indexOf('Substitution')>=0)keep=true;
    if(!keep&&/halftime|half.time|end.regular.time|full.time|final.whistle|first.half|second.half|extra.time|penalty.shootout|own.goal|disallowed|no.goal|kickoff|kick.off|match.begins|match.starts/i.test(rawText))keep=true;
    if(!keep&&typeText.indexOf('VAR')>=0&&/no.goal|red.card|penalty/i.test(rawText))keep=true;
    if(!keep)continue;
    var type=typeText,isGoal=type.indexOf('Goal')>=0,isRed=type.indexOf('Red')>=0,isYel=type.indexOf('Yellow')>=0,isSub=type.indexOf('Substitution')>=0,isPen=type.indexOf('Penalty')>=0;
    // Detect goal sub-type
    var goalType='';
    if(isGoal){
      if(/own goal/i.test(rawText))goalType='own-goal';
      else if(/penalty/i.test(rawText)&&/scored|converts/i.test(rawText))goalType='penalty';
      else if(/free kick|direct.*free/i.test(rawText))goalType='freekick';
      else if(/disallowed|no goal|var.*no goal/i.test(rawText))goalType='disallowed';
      else goalType='goal';
    }
    // Determine CSS class
    var cls='';
    if(goalType==='goal')cls='event-goal';
    else if(goalType==='penalty')cls='event-penalty';
    else if(goalType==='own-goal')cls='event-own-goal';
    else if(goalType==='freekick')cls='event-freekick';
    else if(goalType==='disallowed')cls='event-disallowed';
    else if(isRed)cls='event-red';
    else if(isYel)cls='event-yellow';
    else if(isSub)cls='event-sub';
    else if(isPen)cls='event-penalty';
    else cls='event-period';
    // Icon
    var icon='';
    if(goalType==='goal')icon='⚽';
    else if(goalType==='penalty')icon='🎯';
    else if(goalType==='own-goal')icon='🔴';
    else if(goalType==='freekick')icon='⚡';
    else if(goalType==='disallowed')icon='❌';
    else if(isRed)icon='🟥';
    else if(isYel)icon='🟨';
    else if(isSub)icon='🔄';
    else if(isPen)icon='🎯';
    else icon='●';
    // Text class
    var textCls='';
    if(goalType==='goal')textCls='goal-text';
    else if(goalType==='penalty')textCls='penalty-text';
    else if(goalType==='own-goal')textCls='own-goal-text';
    else if(goalType==='freekick')textCls='freekick-text';
    else if(goalType==='disallowed')textCls='disallowed-text';
    // Build display text with jersey numbers
    var displayText=ev.text||ev.shortText||'';
    var athletes=ev.athletes||[];
    if(athletes.length>0){
      for(var ai=0;ai<athletes.length;ai++){
        var ath=athletes[ai],name=ath.displayName||'',jersey=ath.jersey||'';
        if(jersey&&name&&displayText.indexOf(name)>=0){
          displayText=displayText.split(name).join(name+' #'+jersey);
        }
      }
    }
    var cText=ev.clock&&ev.clock.displayValue?ev.clock.displayValue:'';
    significant.push({cls:cls,icon:icon,time:cText,text:displayText,textCls:textCls,goalType:goalType});
  }
  if(significant.length>0){
    // Determine if we need a legend (any goal events present)
    var hasGoals=significant.some(function(s){return s.goalType||s.cls.indexOf('event-goal')>=0||s.cls==='event-penalty'||s.cls==='event-own-goal'||s.cls==='event-freekick'||s.cls==='event-disallowed';});
    html+='<div class="data-stats-card" style="padding:18px 20px"><h3>Match Events</h3>';
    if(hasGoals){
      html+='<div class="data-event-legend"><span><span class="leg-dot" style="background:#4caf50"></span> Goal</span><span><span class="leg-dot" style="background:#ff8c00"></span> Penalty</span><span><span class="leg-dot" style="background:#c39bdb"></span> Free Kick</span><span><span class="leg-dot" style="background:#e03030"></span> Own Goal</span><span><span class="leg-dot" style="background:#666"></span> Disallowed</span></div>';
    }
    html+='<div class="data-event-cards">';
    for(var ei2=0;ei2<significant.length;ei2++){
      var se=significant[ei2];
      html+='<div class="data-event-card '+se.cls+'"><span class="data-event-card-time">'+se.time+'</span><span class="data-event-card-icon">'+se.icon+'</span><span class="data-event-card-text'+(se.textCls?' '+se.textCls:'')+'">'+se.text+'</span></div>';
    }
    html+='</div></div>';
  }
```

- [ ] **Step 4: Use English for MOTM**

At line 1733-1734, change:
```javascript
var motmName=motm.displayName||motm.name||'',motmCN=pcn(motmName);
var motmTeam=motm.team?_espnTeamToCN(motm.team.displayName||motm.team.name||''):'';
```
To:
```javascript
var motmName=motm.displayName||motm.name||'';
var motmTeam=motm.team?(motm.team.displayName||motm.team.name||''):'';
```

At line 1735, change:
```javascript
html+='<div class="data-stats-card" style="padding:18px 20px"><h3>⭐ 全场最佳球员</h3>...'+motmCN+(motmTeam?...)...'</div>';
```
To:
```javascript
html+='<div class="data-stats-card" style="padding:18px 20px"><h3>⭐ Man of the Match</h3><div class="data-motm"><span class="data-motm-star">⭐</span><div><div class="data-motm-name">'+motmName+(motmTeam?' <span style="font-size:13px;color:var(--text-dim);font-weight:400">('+motmTeam+')</span>':'')+'</div><div style="font-size:11px;color:var(--text-dim);margin-top:2px">Man of the Match</div></div></div></div>';
```

- [ ] **Step 5: Change section headers to English**

Replace Chinese headers in renderMatchData:
- Line 1640: `📊 比赛数据` → `Match Stats`
- Line 1663: `👥 首发阵容` → `Starting Lineups`

- [ ] **Step 6: Commit**

```bash
git add worldcuppro.html
git commit -m "feat: English names, event cards with goal types, jersey numbers in events"
```

---

### Task 4: Fix match status — injury time monitoring

**Files:**
- Modify: `D:\websites\worldcuppro.html` (`_pollESPN` ~lines 1430-1444, `formatMatchStatus` ~lines 1917-1926)

- [ ] **Step 1: Fix _pollESPN injury time logic**

Change lines 1436-1444 from:
```javascript
        // 上半场补时（分钟数≥45）→ 就是中场
        else if(period===1&&min>=45){
          dbSt='halftime';
        }
        // 下半场补时（分钟数≥90）→ 比赛已进入尾声
        else if(period===2&&min>=90){
          // 不直接设 finished（ESPN 可能在补时结束后才发 STATUS_FULL_TIME），
          // 但如果旧状态不是 halftime，保持 live 显示补时分钟数
        }
```
To:
```javascript
        // 上半场补时（分钟数≥45）→ 保持 live 显示补时分钟数
        // 仅当 ESPN 明确发送 STATUS_HALF_TIME 或 clock 含 HT 才设为 halftime
        else if(period===1&&min>=45){
          // keep live — injury time clock is still ticking
        }
        // 下半场补时（分钟数≥90）→ 保持 live 显示补时
        // 仅当 ESPN 发送 STATUS_FULL_TIME 才设为 finished
        else if(period===2&&min>=90){
          // keep live — injury time clock is still ticking
        }
```

- [ ] **Step 2: Fix resolveStatus — don't auto-set halftime on min>=45**

Change line 1289 from `if(s.match_minute>=45)return'halftime';` to:
```javascript
if(s.match_minute>=45&&s.match_minute<90)return'live'; // injury time still running
```

Change line 1294 from `if(s.match_minute>=45)return'halftime';` to:
```javascript
if(s.match_minute>=45&&s.match_minute<90)return'live';
```

- [ ] **Step 3: Fix formatMatchStatus — show injury time display**

Change lines 1917-1926 from:
```javascript
    if(st==='live'){
      statusBadge='<span class="match-live-badge" style="color:#0fa84a"><span class="live-dot-sm" style="background:#0fa84a"></span> 直播中</span>';
      var min=ms.match_minute||0,inj=ms.injury_time||0;
      if(!min||min<=0){minuteHTML='<span style="color:#0fa84a">0\'</span>';}
      else if(inj&&inj>0){var base=min<=45?45:90;minuteHTML='<span style="color:#0fa84a">'+base+'+'+inj+"'</span>";}
      else{minuteHTML='<span style="color:#0fa84a">'+min+"'</span>";}
      scoreColor='color:#0fa84a';liveClass=' live';liveScoreStatusHTML=minuteHTML;
    }else if(st==='halftime'){
      statusBadge='<span class="match-live-badge"><span class="live-dot-sm"></span> 中场</span>';
      minuteHTML='';liveScoreStatusHTML='<span style="color:#f39c12;font-size:11px">中场</span>';
      scoreColor='color:#f39c12';
```
To:
```javascript
    if(st==='live'){
      var min=ms.match_minute||0,inj=ms.injury_time||0;
      if(!min||min<=0){
        statusBadge='<span class="match-live-badge" style="color:#0fa84a"><span class="live-dot-sm" style="background:#0fa84a"></span> Live</span>';
        minuteHTML='<span style="color:#0fa84a">0\'</span>';
        liveScoreStatusHTML='<span style="color:#0fa84a">0\'</span>';
      }else if((min>=45&&min<90)||(min>=90)){
        // Injury time — show clock with orange styling
        var base=min>=90?90:45;
        var clockStr=inj&&inj>0?base+'+'+inj+"'":min+"'";
        statusBadge='<span class="match-live-badge" style="color:#f39c12"><span class="live-dot-sm" style="background:#f39c12"></span> '+clockStr+'</span>';
        minuteHTML='<span style="color:#f39c12">'+clockStr+'</span>';
        liveScoreStatusHTML='<span style="color:#f39c12">'+clockStr+'</span>';
        scoreColor='color:#f39c12';
      }else{
        statusBadge='<span class="match-live-badge" style="color:#0fa84a"><span class="live-dot-sm" style="background:#0fa84a"></span> Live</span>';
        minuteHTML='<span style="color:#0fa84a">'+min+"'</span>";
        scoreColor='color:#0fa84a';liveClass=' live';liveScoreStatusHTML=minuteHTML;
      }
    }else if(st==='halftime'){
      statusBadge='<span class="match-live-badge"><span class="live-dot-sm"></span> HT</span>';
      minuteHTML='';liveScoreStatusHTML='<span style="color:#f39c12;font-size:11px">HT</span>';
      scoreColor='color:#f39c12';
```

- [ ] **Step 4: Commit**

```bash
git add worldcuppro.html
git commit -m "fix: match status shows injury time clock instead of jumping to HT/FT"
```

---

### Task 5: Cleanup team page + search index references to deleted tables

**Files:**
- Modify: `D:\websites\worldcuppro.html` (lines 2253, 2257, 2441)

- [ ] **Step 1: Fix team page player cards (line 2257)**

Change:
```javascript
var playerCards=info.players.map(function(p){var cn=TEAM_PLAYER_CN[p.n]||'';var cc=TEAM_CLUB_CN[p.club]||'';return'<div class="tpc"><div class="tpt"><div class="tpn">'+(p.num||'—')+'</div><div><div class="tpna">'+p.n+(cn?' <span style="color:var(--text-dim);font-size:11px;font-weight:400">'+cn+'</span>':'')+'</div><div class="tppo">'+posCN[p.pos]+'</div></div></div><div class="tpi"><span class="tptag tpclub">'+(cc||p.club||'—')+'</span><span class="tptag tpage">'+(p.age||'—')+'岁</span><span class="tptag tpval">'+(p.val||'—')+'</span></div></div>';}).join('');
```
To:
```javascript
var playerCards=info.players.map(function(p){var cc=TEAM_CLUB_CN[p.club]||'';return'<div class="tpc"><div class="tpt"><div class="tpn">'+(p.num||'—')+'</div><div><div class="tpna">'+p.n+'</div><div class="tppo">'+p.pos+'</div></div></div><div class="tpi"><span class="tptag tpclub">'+(cc||p.club||'—')+'</span><span class="tptag tpage">'+(p.age||'—')+'岁</span><span class="tptag tpval">'+(p.val||'—')+'</span></div></div>';}).join('');
```

- [ ] **Step 2: Fix search index (line 2441)**

Change:
```javascript
t.players.forEach((p,pi)=>{var pcn=TEAM_PLAYER_CN[p.n]||'';idx.push({type:'player',icon:'👤',name:pcn||p.n,sub:t.name+' · '+p.club+' · '+p.pos,keywords:[p.n,t.name,p.club,p.pos,pcn].filter(Boolean),act:'player',data:{team:t.name,idx:pi}});});
```
To:
```javascript
t.players.forEach((p,pi)=>{idx.push({type:'player',icon:'👤',name:p.n,sub:t.name+' · '+p.club+' · '+p.pos,keywords:[p.n,t.name,p.club,p.pos].filter(Boolean),act:'player',data:{team:t.name,idx:pi}});});
```

- [ ] **Step 3: Commit**

```bash
git add worldcuppro.html
git commit -m "fix: remove dead references to deleted TEAM_PLAYER_CN table"
```

---

### Task 6: Verify and deploy

- [ ] **Step 1: Open the live site and test**

Navigate to `https://wc2026-1y8.pages.dev/worldcuppro` in Chrome.

- [ ] **Step 2: Test match data modal**

1. Find a finished match, click "📊 数据"
2. Verify: NO scrollbars on right or bottom of modal
3. Verify: formation grids for home/away aligned top and bottom
4. Verify: player names are in English (not Chinese)
5. Verify: events shown as individual cards with left color stripes
6. Verify: goal type legend shown above events (if goals present)
7. Verify: event descriptions in English
8. Verify: player jersey numbers shown in events
9. Test with 2+ different matches

- [ ] **Step 3: Test match status injury time**

1. Find a live match near 45' or 90'
2. Verify: when injury time is running, status shows "45'+X" or "90'+X" in orange
3. Verify: status doesn't jump to "HT" while injury time clock is still ticking
4. Verify: match goes to "HT" only when ESPN sends STATUS_HALF_TIME

- [ ] **Step 4: Check console for errors**

Open DevTools console — verify 0 JS errors.

- [ ] **Step 5: Verify other features unaffected**

Quick check: schedule expand/collapse, predictions, live scores, chat, standings, bracket, team pages.

- [ ] **Step 6: Commit any final fixes and push**

```bash
git add worldcuppro.html
git commit -m "fix: final verification tweaks for match data v3"
git push origin main
```
