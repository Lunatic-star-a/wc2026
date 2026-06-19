# Match Data v3 — English names, injury time, event cards, goal types

## Scope
Single-file change to `worldcuppro.html`. Seven fixes to match data modal + match status display.

## 1. Match Status — Injury Time Monitoring
- In `_pollESPN`: `period=1 && min>=45` stays `'live'` (not `'halftime'`). Only set `'halftime'` on `STATUS_HALF_TIME` or clock contains "HT".
- In `_pollESPN`: `period=2 && min>=90` stays `'live'` (not finished). Only set `'finished'` on `STATUS_FULL_TIME`.
- In `formatMatchStatus`: `live` + min>=45 → badge "补时中" with "45'+X" in orange. `live` + min>=90 → badge "补时中" with "90'+X" in orange.

## 2. Formation Alignment
- `.data-lineups-grid`: `align-items:stretch`
- `.data-lineup-col`: flex column with `justify-content:space-between` so both columns fill equal height regardless of formation row count.

## 3. Event Cards
- Replace flat `.data-event-item` list with `.data-event-card` cards.
- Each card: left color stripe (event type), time badge, icon + text.

## 4. Goal Type Differentiation + Legend
- Regular goal: green ⚽
- Penalty goal: orange 🎯
- Own goal: red 🔴
- Free kick direct goal: purple ⚡
- Disallowed goal: grey ❌ with VAR reason text
- Legend bar above event list: "图例: ⚽ 进球 | 🎯 点球 | ⚡ 任意球破门 | 🔴 乌龙球 | ❌ 进球取消"

## 5. All Names → English, Delete Chinese Code
- Delete: `pcn()`, `translateEvent()`, `TEAM_PLAYER_CN`, `PLAYER_SURNAME_CN`, `POS_CN`, `posCN()`, `ESPN_TEAM_CN`, `_espnTeamToCN()`
- Use raw ESPN English names everywhere
- `_pollESPN`: match teams by English name directly
- Player search index: English names

## 6. Player Jersey Numbers in Events
- Parse `ev.athletes` array (ESPN includes `jersey` field per athlete)
- Prepend `#N` to player name in event text: `#7 Ronaldo (Portugal) scored...`

## 7. Scrollbar Removal
- `.match-data-body::-webkit-scrollbar { width: 0; display: none; }`
- `.match-data-body { -ms-overflow-style: none; scrollbar-width: none; }`

## Files
- `D:\websites\worldcuppro.html` — only file modified

## Non-changes
- Modal overlay/close, fetchMatchData, stats rendering, formation grid layout, open/close, KNOWN_FINISHED, all other features
