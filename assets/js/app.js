/* Unity League — одностраничный сайт без сборки.
   Данные: window.LEAGUE_DATA (data/league.js). Маршруты: #/<раздел>?s=<турнир>&... */
(function () {
  'use strict';

  const D = window.LEAGUE_DATA || { league: {}, teams: [], seasons: [] };
  const app = document.getElementById('app');
  const sideL = document.getElementById('side-left');
  const sideR = document.getElementById('side-right');
  const select = document.getElementById('season-select');

  const PTS = (D.league && D.league.points) || { win: 3, draw: 1, loss: 0 };
  const TEAM = new Map(D.teams.map(t => [t.id, t]));
  const SEASONS = D.seasons.slice();
  const SBY = new Map(SEASONS.map(s => [s.id, s]));
  const MATCH = new Map();
  SEASONS.forEach(s => s.matches.forEach(m => { m.s = s; MATCH.set(m.id, m); }));
  const TG = (D.league.links && D.league.links.telegram) || 'https://t.me/unityleaguekz';

  // ---------------------------------------------------------------- helpers
  const esc = v => String(v == null ? '' : v).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const store = {
    get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* приватный режим */ } }
  };
  const parseISO = s => { const [y, m, d] = s.split('-').map(Number); return new Date(y, m - 1, d); };
  const pad = n => String(n).padStart(2, '0');
  const toISO = d => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
  const fmt = (iso, o) => new Intl.DateTimeFormat('ru-RU', o).format(parseISO(iso));
  const fmtDay = iso => fmt(iso, { weekday: 'short', day: 'numeric', month: 'short' });
  const fmtShort = iso => fmt(iso, { day: '2-digit', month: '2-digit' });
  const fmtFull = iso => fmt(iso, { day: 'numeric', month: 'long', year: 'numeric' });
  const fmtLong = iso => fmt(iso, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
  const plural = (n, a, b, c) => { const m10 = n % 10, m100 = n % 100; return m10 === 1 && m100 !== 11 ? a : (m10 >= 2 && m10 <= 4 && (m100 < 10 || m100 >= 20) ? b : c); };

  const sLabel = s => `${s.season} · ${s.name}`;
  const team = id => TEAM.get(id) || { id, name: id, short: String(id).slice(0, 3).toUpperCase(), color: '#5c7c99' };
  const tName = (id, s) => (s && s.names && s.names[id]) || team(id).name;
  function badge(id, s, size) {
    const t = team(id);
    const inner = t.logo ? `<img src="${esc(t.logo)}" alt="">` : esc(t.short || '');
    return `<span class="badge ${size || ''}" style="--c:${esc(t.color || '#5c7c99')}" title="${esc(tName(id, s))}">${inner}</span>`;
  }
  const played = m => Array.isArray(m.sc);
  function winner(m) {
    if (!played(m)) return null;
    if (m.sc[0] !== m.sc[1]) return m.sc[0] > m.sc[1] ? 'h' : 'a';
    if (m.pens) return m.pens[0] > m.pens[1] ? 'h' : 'a';
    return 'd';
  }
  const byDate = (a, b) => (a.d < b.d ? -1 : a.d > b.d ? 1 : (a.src || 0) - (b.src || 0));

  // ---------------------------------------------------------------- stats
  const cache = new Map();
  function stats(s) {
    if (cache.has(s.id)) return cache.get(s.id);
    const league = s.matches.filter(m => !m.st && played(m)).sort(byDate);
    const ids = new Set(s.teams);
    s.matches.forEach(m => { ids.add(m.h); ids.add(m.a); });
    const rows = new Map([...ids].map(id => [id, { team: id, p: 0, w: 0, d: 0, l: 0, gf: 0, ga: 0, pts: 0, form: [] }]));
    for (const m of league) {
      const h = rows.get(m.h), a = rows.get(m.a);
      const [x, y] = m.sc;
      h.p++; a.p++; h.gf += x; h.ga += y; a.gf += y; a.ga += x;
      if (x > y) { h.w++; a.l++; h.pts += PTS.win; a.pts += PTS.loss; h.form.push(['W', m]); a.form.push(['L', m]); }
      else if (x < y) { a.w++; h.l++; a.pts += PTS.win; h.pts += PTS.loss; h.form.push(['L', m]); a.form.push(['W', m]); }
      else { h.d++; a.d++; h.pts += PTS.draw; a.pts += PTS.draw; h.form.push(['D', m]); a.form.push(['D', m]); }
    }
    let table = [...rows.values()].filter(r => r.p > 0 || !s.matches.length);
    table.forEach(r => { r.gd = r.gf - r.ga; });
    // личные встречи среди команд с равными очками
    const groups = new Map();
    table.forEach(r => { if (!groups.has(r.pts)) groups.set(r.pts, []); groups.get(r.pts).push(r); });
    groups.forEach(g => {
      if (g.length < 2) { g.forEach(r => { r.h2h = 0; }); return; }
      const set = new Set(g.map(r => r.team));
      const hp = new Map(g.map(r => [r.team, 0]));
      league.forEach(m => {
        if (!set.has(m.h) || !set.has(m.a)) return;
        const [x, y] = m.sc;
        if (x > y) hp.set(m.h, hp.get(m.h) + PTS.win);
        else if (x < y) hp.set(m.a, hp.get(m.a) + PTS.win);
        else { hp.set(m.h, hp.get(m.h) + PTS.draw); hp.set(m.a, hp.get(m.a) + PTS.draw); }
      });
      g.forEach(r => { r.h2h = hp.get(r.team); });
    });
    table.sort((a, b) => b.pts - a.pts || b.h2h - a.h2h || b.gd - a.gd || b.gf - a.gf || b.w - a.w || tName(a.team, s).localeCompare(tName(b.team, s)));
    table.forEach((r, i) => { r.pos = i + 1; });

    const P = new Map();
    const pl = (name, tm) => {
      const k = tm + '|' + name;
      if (!P.has(k)) P.set(k, { name, team: tm, g: 0, pen: 0, a: 0, yc: 0, rc: 0, og: 0 });
      return P.get(k);
    };
    let goals = 0, cards = 0;
    for (const m of s.matches) {
      if (played(m)) goals += m.sc[0] + m.sc[1];
      for (const e of m.ev || []) {
        const tm = e[2] === 'h' ? m.h : m.a, other = e[2] === 'h' ? m.a : m.h;
        if (e[1] === 'goal' || e[1] === 'pen') {
          if (e[3]) { const p = pl(e[3], tm); p.g++; if (e[1] === 'pen') p.pen++; }
          if (e[4]) pl(e[4], tm).a++;
        } else if (e[1] === 'og') {
          if (e[3]) pl(e[3], other).og++;
        } else if (e[1] === 'yc') { cards++; if (e[3]) pl(e[3], tm).yc++; }
        else if (e[1] === 'rc') { cards++; if (e[3]) pl(e[3], tm).rc++; }
      }
    }
    const players = [...P.values()];
    const champion = s.champion || (s.championFromTable && table.length ? table[0].team : null);
    const playedCount = s.matches.filter(played).length;
    const res = {
      league, table, players, champion, goals, cards, playedCount,
      avg: playedCount ? goals / playedCount : 0,
      withEvents: s.matches.filter(m => m.ev && m.ev.length).length,
      topScorer: players.slice().sort((a, b) => b.g - a.g || b.a - a.a)[0] || null,
      topAssist: players.slice().sort((a, b) => b.a - a.a || b.g - a.g)[0] || null,
      halfLen: Math.max(0, ...s.matches.flatMap(m => (m.ev || []).map(e => e[0] || 0))) > 42 ? 25 : 20
    };
    cache.set(s.id, res);
    return res;
  }

  // ---------------------------------------------------------------- routing
  let cur = null;
  let lastPath = null;
  function parseRoute() {
    const raw = location.hash.replace(/^#\/?/, '');
    const qi = raw.indexOf('?');
    const pathPart = qi >= 0 ? raw.slice(0, qi) : raw;
    const q = Object.fromEntries(new URLSearchParams(qi >= 0 ? raw.slice(qi + 1) : ''));
    return { parts: pathPart.split('/').filter(Boolean).map(decodeURIComponent), q };
  }
  function link(path, params, season) {
    const q = new URLSearchParams();
    q.set('s', (season || cur).id);
    Object.entries(params || {}).forEach(([k, v]) => { if (v != null && v !== '') q.set(k, v); });
    return `#/${path}?${q}`;
  }
  const matchLink = m => link('match/' + m.id, null, m.s);
  const teamLink = (id, s) => link('team/' + id, null, s);
  const defaultSeason = () => SEASONS.slice().reverse().find(s => s.matches.length) || SEASONS[SEASONS.length - 1];

  function resolveSeason(q, parts) {
    if (parts[0] === 'match' && MATCH.has(parts[1])) return MATCH.get(parts[1]).s;
    if (q.s && SBY.has(q.s)) return SBY.get(q.s);
    const saved = store.get('ul-season');
    if (saved && SBY.has(saved)) return SBY.get(saved);
    return defaultSeason();
  }

  // ---------------------------------------------------------------- shared renderers
  function statusCell(m) {
    if (!played(m)) return '<span title="Счёт не опубликован">н/д</span>';
    let t = 'FT';
    if (m.tech) t = 'Тех.';
    else if (m.pens) t = 'Пен.';
    return `<span>${fmtShort(m.d)}</span><br><span>${t}</span>`;
  }
  function matchRow(m, opts) {
    opts = opts || {};
    const s = m.s, w = winner(m);
    const cls = side => (w === side ? 'win' : (w && w !== 'd' ? 'lose' : ''));
    const sc = played(m) ? m.sc : ['–', '–'];
    const extra = [];
    if (m.pens) extra.push(`серия пенальти ${m.pens[0]}:${m.pens[1]}`);
    if (m.tech) extra.push('технический результат');
    if (opts.round && m.r && opts.round !== m.r) extra.push(`матч ${m.r} тура`);
    if (opts.showStage && m.st) extra.push(m.st);
    if (opts.showSeason) extra.push(sLabel(s));
    if (!played(m) && m.note) extra.push('счёт не опубликован');
    return `<a class="match" href="${matchLink(m)}">
      <div class="m-status">${statusCell(m)}</div>
      <div class="m-teams">
        <div class="m-team ${cls('h')}">${badge(m.h, s)}<span class="name">${esc(tName(m.h, s))}</span></div>
        <div class="m-team ${cls('a')}">${badge(m.a, s)}<span class="name">${esc(tName(m.a, s))}</span></div>
      </div>
      <div class="m-score"><span class="${w === 'a' ? 'lose' : ''}">${sc[0]}</span><span class="${w === 'h' ? 'lose' : ''}">${sc[1]}</span></div>
      ${extra.length ? `<div class="m-extra">${esc(extra.join(' · '))}</div>` : ''}
    </a>`;
  }
  function dayGroups(matches) {
    const g = new Map();
    matches.forEach(m => { if (!g.has(m.d)) g.set(m.d, []); g.get(m.d).push(m); });
    return [...g.entries()];
  }
  function dominantRound(ms) {
    const rs = ms.filter(m => !m.st).map(m => m.r).filter(Boolean);
    if (!rs.length) return null;
    const c = new Map();
    rs.forEach(r => c.set(r, (c.get(r) || 0) + 1));
    return [...c.entries()].sort((a, b) => b[1] - a[1])[0][0];
  }
  function dayBlock(d, ms, opts) {
    const r = dominantRound(ms);
    const stages = [...new Set(ms.map(m => m.st).filter(Boolean))];
    const label = stages.length && stages.length === new Set(ms.map(m => m.st || '')).size ? stages.join(' · ') : (r ? `Тур ${r}` : 'Игровой день');
    return `<div class="group-h"><span class="flag"></span>${esc(label)}<span class="right">${esc(fmtDay(d))}</span></div>` +
      ms.map(m => matchRow(m, Object.assign({ round: r, showStage: true }, opts))).join('');
  }
  // ---- туры: если у всех матчей регулярного этапа есть номер тура, навигация идёт по турам
  const tourMode = s => { const lg = s.matches.filter(m => !m.st); return lg.length > 0 && lg.every(m => m.r); };
  function mainDates(ms) {
    const c = new Map();
    ms.forEach(m => c.set(m.d, (c.get(m.d) || 0) + 1));
    let ds = [...c.keys()].sort();
    if (ms.length > 2) {
      const multi = ds.filter(d => c.get(d) >= 2);
      if (multi.length) ds = multi;
    }
    if ((parseISO(ds[ds.length - 1]) - parseISO(ds[0])) / 864e5 > 3) ds = [[...c.entries()].sort((a, b) => b[1] - a[1] || (a[0] < b[0] ? -1 : 1))[0][0]];
    return ds;
  }
  function fmtSpan(ds) {
    const a = ds[0], b = ds[ds.length - 1];
    const short = x => fmt(x, { day: 'numeric', month: 'short' });
    if (a === b) return short(a);
    if (a.slice(0, 7) === b.slice(0, 7)) return `${parseISO(a).getDate()}–${short(b)}`;
    return `${short(a)} – ${short(b)}`;
  }
  function tourGroups(s) {
    const g = new Map();
    s.matches.slice().sort(byDate).forEach(m => {
      const key = m.st ? 'st:' + m.st : 'r' + m.r;
      if (!g.has(key)) g.set(key, { key, stage: m.st || null, r: m.st ? null : m.r, ms: [] });
      g.get(key).ms.push(m);
    });
    const list = [...g.values()];
    list.forEach(x => { x.label = x.stage || `Тур ${x.r}`; x.main = mainDates(x.ms); x.last = x.ms[x.ms.length - 1].d; });
    return list.sort((a, b) => (a.stage ? 1 : 0) - (b.stage ? 1 : 0) || (a.stage ? (a.main[0] < b.main[0] ? -1 : 1) : a.r - b.r));
  }
  const groupParams = g => (g.stage ? { st: g.stage } : { r: g.r });
  function tourBody(g) {
    return dayGroups(g.ms).map(([d, ms]) => `<div class="group-h"><span class="flag"></span>${esc(fmtDay(d))}</div>` + ms.map(m => matchRow(m)).join('')).join('');
  }
  function pickGroup(groups, q) {
    let i = -1;
    if (q.st) i = groups.findIndex(g => g.stage === q.st);
    else if (q.r) i = groups.findIndex(g => !g.stage && String(g.r) === String(q.r));
    else if (q.d) {
      let best = 0;
      groups.forEach((g, k) => { const n = g.ms.filter(m => m.d === q.d).length; if (n > best) { best = n; i = k; } });
    }
    if (i < 0) {
      i = 0;
      groups.forEach((g, k) => { if (g.last > groups[i].last || (g.last === groups[i].last && k > i)) i = k; });
    }
    return i;
  }

  function formHtml(form) {
    return `<span class="form">${form.slice(-5).map(([r, m]) => `<a class="${r}" href="${matchLink(m)}" title="${esc(tName(m.h, m.s))} ${m.sc[0]}:${m.sc[1]} ${esc(tName(m.a, m.s))}">${{ W: 'В', D: 'Н', L: 'П' }[r]}</a>`).join('')}</span>`;
  }
  function seasonInfoCard(s) {
    const st = stats(s);
    const champ = st.champion;
    return `<div class="card">
      <div class="card-h">${esc(s.season)}<span class="sub">${esc(s.name)}</span></div>
      ${champ ? `<a class="list-row" href="${teamLink(champ, s)}">${badge(champ, s, 'md')}<div class="grow"><div class="t"><span class="trophy">🏆</span> ${esc(tName(champ, s))}</div><div class="s">${s.champion ? 'Чемпион' : 'Первое место в таблице'}</div></div></a>` : ''}
      <div class="kpis">
        <div class="kpi"><div class="v">${s.matches.length}</div><div class="k">${plural(s.matches.length, 'матч', 'матча', 'матчей')}</div></div>
        <div class="kpi"><div class="v">${st.goals}</div><div class="k">голов</div></div>
        <div class="kpi"><div class="v">${st.avg ? st.avg.toFixed(1) : '—'}</div><div class="k">за матч</div></div>
      </div>
      ${s.matches.length ? `<div class="note">${esc(fmtFull(s.start))} — ${esc(fmtFull(s.end))}</div>` : ''}
    </div>`;
  }
  function emptySeason(s) {
    const st = stats(s);
    return `<div class="card"><div class="card-h">${esc(sLabel(s))}</div>
      ${st.champion ? `<a class="list-row" href="${teamLink(st.champion, s)}">${badge(st.champion, s, 'md')}<div class="grow"><div class="t"><span class="trophy">🏆</span> ${esc(tName(st.champion, s))}</div><div class="s">Чемпион</div></div></a>` : ''}
      <div class="note">${esc(s.note || 'Протоколы матчей этого турнира в канале не публиковались.')}</div></div>`;
  }
  const incompleteBanner = s => s.incomplete ? `<div class="banner">В Telegram-канале опубликованы протоколы только части матчей этого турнира (${s.matches.length}${s.expected ? ' из ' + s.expected : ''}). Таблица и статистика построены по опубликованным матчам и могут отличаться от официальных.</div>` : '';

  // ---------------------------------------------------------------- views
  function viewMatches(q) {
    const s = cur;
    if (!s.matches.length) return emptySeason(s);
    if (tourMode(s)) return viewTours(q);
    const dates = [...new Set(s.matches.map(m => m.d))].sort();
    const d = dates.includes(q.d) ? q.d : dates[dates.length - 1];
    const i = dates.indexOf(d);
    const ms = s.matches.filter(m => m.d === d).sort(byDate);
    const chips = dates.map(x => `<a class="chip ${x === d ? 'active' : ''}" href="${link('', { d: x })}" data-d="${x}">${esc(fmt(x, { day: 'numeric', month: 'short' }))}<small>${esc(fmt(x, { weekday: 'short' }))}</small></a>`).join('');
    return `
      <div class="page-title"><h1>Матчи</h1><span class="crumbs">${esc(sLabel(s))}</span></div>
      <div class="strip">
        <a class="chip-arrow" ${i > 0 ? `href="${link('', { d: dates[i - 1] })}"` : 'aria-disabled="true"'} title="Предыдущий игровой день">‹</a>
        <div class="strip-scroll" id="strip">${chips}</div>
        <a class="chip-arrow" ${i < dates.length - 1 ? `href="${link('', { d: dates[i + 1] })}"` : 'aria-disabled="true"'} title="Следующий игровой день">›</a>
      </div>
      <div class="card">
        <div class="card-h">${esc(fmtLong(d))}<span class="sub">${ms.length} ${plural(ms.length, 'матч', 'матча', 'матчей')}</span></div>
        ${dayBlock(d, ms)}
      </div>
      ${s.note ? `<div class="card"><div class="note">${esc(s.note)}</div></div>` : ''}`;
  }

  function viewTours(q) {
    const s = cur;
    const groups = tourGroups(s);
    const i = pickGroup(groups, q);
    const g = groups[i];
    const chips = groups.map((x, k) => `<a class="chip ${k === i ? 'active' : ''}" href="${link('', groupParams(x))}">${esc(x.label)}<small>${esc(fmtSpan(x.main))}</small></a>`).join('');
    return `
      <div class="page-title"><h1>Матчи</h1><span class="crumbs">${esc(sLabel(s))}</span></div>
      <div class="strip">
        <a class="chip-arrow" ${i > 0 ? `href="${link('', groupParams(groups[i - 1]))}"` : 'aria-disabled="true"'} title="Предыдущий тур">‹</a>
        <div class="strip-scroll" id="strip">${chips}</div>
        <a class="chip-arrow" ${i < groups.length - 1 ? `href="${link('', groupParams(groups[i + 1]))}"` : 'aria-disabled="true"'} title="Следующий тур">›</a>
      </div>
      <div class="card">
        <div class="card-h">${esc(g.label)}<span class="sub">${esc(fmtSpan(g.main))} · ${g.ms.length} ${plural(g.ms.length, 'матч', 'матча', 'матчей')}</span></div>
        ${tourBody(g)}
      </div>
      ${s.note ? `<div class="card"><div class="note">${esc(s.note)}</div></div>` : ''}`;
  }

  function viewResults(q) {
    const s = cur;
    if (!s.matches.length) return emptySeason(s);
    const st = stats(s);
    const teams = st.table.map(r => r.team).sort((a, b) => tName(a, s).localeCompare(tName(b, s)));
    const tf = teams.includes(q.t) ? q.t : '';
    const ms = s.matches.filter(m => !tf || m.h === tf || m.a === tf).sort(byDate).reverse();
    const has = m => !tf || m.h === tf || m.a === tf;
    const body = tourMode(s)
      ? tourGroups(s).reverse().map(g => {
        const list = g.ms.filter(has).reverse();
        return list.length ? `<div class="group-h"><span class="flag"></span>${esc(g.label)}<span class="right">${esc(fmtSpan(g.main))}</span></div>` + list.map(m => matchRow(m)).join('') : '';
      }).join('')
      : dayGroups(ms).map(([d, list]) => dayBlock(d, list)).join('');
    return `
      <div class="page-title"><h1>Результаты</h1>
        <div class="filters"><select id="team-filter" aria-label="Фильтр по команде"><option value="">Все команды</option>${teams.map(t => `<option value="${esc(t)}" ${t === tf ? 'selected' : ''}>${esc(tName(t, s))}</option>`).join('')}</select></div>
      </div>
      ${incompleteBanner(s)}
      <div class="card">${body || '<div class="empty">Матчей нет</div>'}</div>`;
  }

  function standingsTable(s, opts) {
    opts = opts || {};
    const st = stats(s);
    const rows = opts.limit ? st.table.slice(0, opts.limit) : st.table;
    const hl = opts.highlight;
    if (!rows.length) return '<div class="empty">Нет сыгранных матчей</div>';
    if (opts.mini) {
      return `<table class="tbl"><thead><tr><th>#</th><th class="l">Команда</th><th>И</th><th>О</th></tr></thead><tbody>
        ${rows.map(r => `<tr><td><span class="pos ${r.pos <= 3 && s.status === 'finished' ? 'p' + r.pos : ''}">${r.pos}</span></td>
        <td class="l team"><a class="team-cell" href="${teamLink(r.team, s)}">${badge(r.team, s, 'sm')}<span class="name">${esc(tName(r.team, s))}</span></a></td>
        <td>${r.p}</td><td class="pts">${r.pts}</td></tr>`).join('')}</tbody></table>`;
    }
    return `<div class="tbl-wrap"><table class="tbl"><thead><tr>
      <th>#</th><th class="l">Команда</th><th title="Игры">И</th><th class="hide-sm" title="Победы">В</th><th class="hide-sm" title="Ничьи">Н</th><th class="hide-sm" title="Поражения">П</th>
      <th title="Забито:Пропущено">Мячи</th><th title="Разница">±</th><th title="Очки">О</th><th class="hide-sm">Форма</th></tr></thead><tbody>
      ${rows.map(r => `<tr ${r.team === hl ? 'style="background:var(--accent-soft)"' : ''}>
        <td><span class="pos ${r.pos <= 3 && s.status === 'finished' ? 'p' + r.pos : ''}">${r.pos}</span></td>
        <td class="l team"><a class="team-cell" href="${teamLink(r.team, s)}">${badge(r.team, s)}<span class="name">${esc(tName(r.team, s))}</span>${r.team === st.champion ? ' <span class="trophy" title="Чемпион">🏆</span>' : ''}</a></td>
        <td>${r.p}</td><td class="hide-sm">${r.w}</td><td class="hide-sm">${r.d}</td><td class="hide-sm">${r.l}</td>
        <td>${r.gf}:${r.ga}</td><td>${r.gd > 0 ? '+' : ''}${r.gd}</td><td class="pts">${r.pts}</td>
        <td class="hide-sm">${formHtml(r.form)}</td></tr>`).join('')}
      </tbody></table></div>`;
  }

  function viewTable() {
    const s = cur;
    if (!s.matches.length) return emptySeason(s);
    const st = stats(s);
    const stageMs = s.matches.filter(m => m.st).sort(byDate);
    const stageNames = [...new Set(stageMs.map(m => m.st))];
    const champ = st.champion;
    return `
      <div class="page-title"><h1>Турнирная таблица</h1><span class="crumbs">${esc(sLabel(s))}</span></div>
      ${incompleteBanner(s)}
      ${champ ? `<div class="card"><a class="list-row" href="${teamLink(champ, s)}">${badge(champ, s, 'md')}<div class="grow"><div class="t"><span class="trophy">🏆</span> ${esc(tName(champ, s))}</div>
        <div class="s">${s.champion ? 'Чемпион турнира' : 'Первое место в итоговой таблице'}${s.runnerUp ? ' · серебро — ' + esc(tName(s.runnerUp, s)) : ''}${s.third ? ' · бронза — ' + esc(tName(s.third, s)) : ''}</div></div></a></div>` : ''}
      <div class="card">
        <div class="card-h">${stageNames.length ? 'Регулярный этап' : 'Таблица'}<span class="sub">${st.league.length} ${plural(st.league.length, 'матч', 'матча', 'матчей')}</span></div>
        ${standingsTable(s)}
        <div class="legend"><span><i style="background:var(--win)"></i>В — победа (${PTS.win} очка)</span><span><i style="background:var(--draw)"></i>Н — ничья (${PTS.draw})</span><span><i style="background:var(--loss)"></i>П — поражение</span><span>При равенстве очков: личные встречи, разница, забитые</span></div>
      </div>
      ${stageNames.map(n => `<div class="card"><div class="card-h">${esc(n)}</div>${stageMs.filter(m => m.st === n).map(m => matchRow(m)).join('')}</div>`).join('')}
      ${s.note ? `<div class="card"><div class="note">${esc(s.note)}</div></div>` : ''}`;
  }

  const STAT_TABS = [
    ['scorers', 'Бомбардиры', p => p.g, 'Голы'],
    ['assists', 'Ассистенты', p => p.a, 'Передачи'],
    ['points', 'Гол + пас', p => p.g + p.a, 'Г+П'],
    ['cards', 'Карточки', p => p.yc + p.rc * 2, 'ЖК / КК']
  ];
  function viewStats(q) {
    const s = cur;
    if (!s.matches.length) return emptySeason(s);
    const st = stats(s);
    const tab = STAT_TABS.find(t => t[0] === q.tab) || STAT_TABS[0];
    const all = q.all === '1';
    const list = st.players.filter(p => tab[2](p) > 0).sort((a, b) => tab[2](b) - tab[2](a) || (b.g - a.g) || (b.a - a.a) || a.name.localeCompare(b.name));
    const rows = all ? list : list.slice(0, 30);
    let rank = 0, prev = null;
    const body = rows.map((p, i) => {
      const v = tab[2](p);
      if (v !== prev) { rank = i + 1; prev = v; }
      const val = tab[0] === 'cards' ? `${p.yc} / ${p.rc}` : v;
      return `<tr><td class="muted">${rank}</td>
        <td class="l strong">${esc(p.name)}</td>
        <td class="l team"><a class="team-cell" href="${teamLink(p.team, s)}">${badge(p.team, s, 'sm')}<span class="name">${esc(tName(p.team, s))}</span></a></td>
        ${tab[0] === 'cards' ? '' : `<td class="hide-sm">${p.g}${p.pen ? ` <span class="muted">(${p.pen} пен.)</span>` : ''}</td><td class="hide-sm">${p.a}</td>`}
        <td class="pts">${val}</td></tr>`;
    }).join('');
    const coverage = st.withEvents < s.matches.length ? `<div class="note">Статистика игроков посчитана по ${st.withEvents} ${plural(st.withEvents, 'матчу', 'матчам', 'матчам')} из ${s.matches.length}, для которых в канале опубликованы протоколы. Голы, где автор не указан, в зачёт игроков не идут.</div>` : '';
    return `
      <div class="page-title"><h1>Статистика игроков</h1><span class="crumbs">${esc(sLabel(s))}</span></div>
      ${incompleteBanner(s)}
      <div class="card">
        <div class="subtabs">${STAT_TABS.map(t => `<a href="${link('stats', { tab: t[0] })}" class="${t === tab ? 'active' : ''}">${t[1]}</a>`).join('')}</div>
        ${list.length ? `<div class="tbl-wrap"><table class="tbl"><thead><tr><th>#</th><th class="l">Игрок</th><th class="l">Команда</th>
          ${tab[0] === 'cards' ? '' : '<th class="hide-sm">Голы</th><th class="hide-sm">Пасы</th>'}<th>${tab[3]}</th></tr></thead><tbody>${body}</tbody></table></div>
          ${!all && list.length > rows.length ? `<div class="note"><a class="btn" href="${link('stats', { tab: tab[0], all: 1 })}">Показать всех (${list.length})</a></div>` : ''}` : '<div class="empty">В протоколах этого турнира нет данных об игроках</div>'}
        ${coverage}
      </div>`;
  }

  function viewCalendar(q) {
    const s = cur;
    if (!s.matches.length) return emptySeason(s);
    const dates = [...new Set(s.matches.map(m => m.d))].sort();
    const months = [];
    const first = parseISO(dates[0]), last = parseISO(dates[dates.length - 1]);
    for (let d = new Date(first.getFullYear(), first.getMonth(), 1); d <= last; d.setMonth(d.getMonth() + 1)) months.push(`${d.getFullYear()}-${pad(d.getMonth() + 1)}`);
    const mKey = months.includes(q.m) ? q.m : dates[dates.length - 1].slice(0, 7);
    const mi = months.indexOf(mKey);
    const [y, mo] = mKey.split('-').map(Number);
    const start = new Date(y, mo - 1, 1);
    const offset = (start.getDay() + 6) % 7;
    const daysIn = new Date(y, mo, 0).getDate();
    const cells = Math.ceil((offset + daysIn) / 7) * 7;
    const byDay = new Map();
    s.matches.forEach(m => { if (!byDay.has(m.d)) byDay.set(m.d, []); byDay.get(m.d).push(m); });
    let html = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'].map(x => `<div class="dow">${x}</div>`).join('');
    for (let c = 0; c < cells; c++) {
      const day = new Date(y, mo - 1, 1 - offset + c);
      const iso = toISO(day);
      const out = day.getMonth() !== mo - 1;
      const ms = byDay.get(iso) || [];
      const inner = `<span class="dn">${day.getDate()}</span>` + ms.slice(0, 4).map(m => `<span class="mini">${esc(team(m.h).short)} <b>${played(m) ? m.sc[0] + ':' + m.sc[1] : '–'}</b> ${esc(team(m.a).short)}</span>`).join('') +
        (ms.length > 4 ? `<span class="mini">+ ещё ${ms.length - 4}</span>` : '') + (ms.length ? `<span class="cnt">${ms.length}</span>` : '');
      html += ms.length && !out ? `<a class="day has" href="${link('', { d: iso })}">${inner}</a>` : `<div class="day ${out ? 'out' : ''}">${inner}</div>`;
    }
    const monthName = new Intl.DateTimeFormat('ru-RU', { month: 'long', year: 'numeric' }).format(start);
    return `
      <div class="page-title"><h1>Календарь</h1><span class="crumbs">${esc(sLabel(s))}</span></div>
      <div class="card">
        <div class="cal-h">
          ${mi > 0 ? `<a class="btn" href="${link('calendar', { m: months[mi - 1] })}">‹</a>` : '<span class="btn" aria-disabled="true" style="opacity:.35">‹</span>'}
          <strong>${esc(monthName)}</strong>
          ${mi < months.length - 1 ? `<a class="btn" href="${link('calendar', { m: months[mi + 1] })}">›</a>` : '<span class="btn" aria-disabled="true" style="opacity:.35">›</span>'}
        </div>
        <div class="cal">${html}</div>
      </div>
      <div class="card"><div class="card-h">Игровые дни турнира<span class="sub">${dates.length}</span></div>
        <div class="card-b" style="display:flex;flex-wrap:wrap;gap:6px">${dates.map(x => `<a class="chip" href="${link('', { d: x })}">${esc(fmt(x, { day: 'numeric', month: 'short', year: '2-digit' }))}<small>${byDay.get(x).length} ${plural(byDay.get(x).length, 'матч', 'матча', 'матчей')}</small></a>`).join('')}</div></div>`;
  }

  function titlesOf(id) {
    return SEASONS.filter(s => stats(s).champion === id);
  }
  function viewTeams() {
    const s = cur;
    const st = stats(s);
    const inSeason = st.table.length ? st.table : s.teams.map(t => ({ team: t }));
    const allTeams = D.teams.map(t => ({ t, seasons: SEASONS.filter(x => stats(x).table.some(r => r.team === t.id) || x.champion === t.id), titles: titlesOf(t.id) }))
      .filter(x => x.seasons.length)
      .sort((a, b) => b.titles.length - a.titles.length || b.seasons.length - a.seasons.length || a.t.name.localeCompare(b.t.name));
    return `
      <div class="page-title"><h1>Команды</h1><span class="crumbs">${esc(sLabel(s))}</span></div>
      ${inSeason.length ? `<div class="grid-cards">${inSeason.map(r => `<a class="team-card" href="${teamLink(r.team, s)}">${badge(r.team, s, 'md')}<div><div class="t">${esc(tName(r.team, s))}</div><div class="s">${r.pos ? `${r.pos}-е место · ${r.pts} ${plural(r.pts, 'очко', 'очка', 'очков')}` : 'участник'}</div></div></a>`).join('')}</div>` : ''}
      <div class="card"><div class="card-h">Все команды лиги<span class="sub">${allTeams.length}</span></div>
        ${allTeams.map(x => `<a class="list-row" href="${teamLink(x.t.id)}">${badge(x.t.id)}<div class="grow"><div class="t">${esc(x.t.name)}</div><div class="s">${x.seasons.length} ${plural(x.seasons.length, 'турнир', 'турнира', 'турниров')}</div></div>${x.titles.length ? `<span class="pill gold">🏆 ${x.titles.length}</span>` : ''}</a>`).join('')}
      </div>`;
  }

  function viewTeam(id) {
    if (!TEAM.has(id)) return notFound();
    const history = SEASONS.filter(x => stats(x).table.some(r => r.team === id));
    let s = cur;
    if (!stats(s).table.some(r => r.team === id)) s = history[history.length - 1] || cur;
    const st = stats(s);
    const row = st.table.find(r => r.team === id);
    const titles = titlesOf(id);
    const ms = s.matches.filter(m => m.h === id || m.a === id).sort(byDate).reverse();
    const scorers = st.players.filter(p => p.team === id && (p.g || p.a)).sort((a, b) => b.g - a.g || b.a - a.a).slice(0, 10);
    const hist = history.slice().reverse().map(x => {
      const r = stats(x).table.find(t => t.team === id);
      const champ = stats(x).champion === id;
      return `<tr><td class="l"><a href="${link('table', null, x)}">${esc(x.season)}</a><div class="muted" style="font-size:11px">${esc(x.name)}</div></td>
        <td><span class="pos ${r.pos <= 3 && !x.incomplete ? 'p' + r.pos : ''}">${r.pos}</span>${champ ? ' 🏆' : ''}</td><td>${r.p}</td><td class="hide-sm">${r.w}-${r.d}-${r.l}</td><td>${r.gf}:${r.ga}</td><td class="pts">${r.pts}</td></tr>`;
    }).join('');
    const pages = history.length > 1 ? `<div class="filters"><select id="team-season" aria-label="Турнир команды">${history.slice().reverse().map(x => `<option value="${esc(x.id)}" ${x === s ? 'selected' : ''}>${esc(sLabel(x))}</option>`).join('')}</select></div>` : '';
    return `
      <div class="card"><div class="mh">
        <div style="display:flex;align-items:center;gap:14px;justify-content:flex-start;text-align:left">${badge(id, s, 'lg')}
          <div style="min-width:0"><div style="font-size:22px;font-weight:800">${esc(tName(id, s))}</div>
          <div class="muted">${history.length} ${plural(history.length, 'турнир', 'турнира', 'турниров')} в архиве${titles.length ? ` · <span class="trophy">🏆 ${titles.length} ${plural(titles.length, 'титул', 'титула', 'титулов')}</span>` : ''}</div>
          ${titles.length ? `<div class="titles" style="margin-top:6px">${titles.map(x => `<a class="pill gold" href="${link('table', null, x)}">${esc(x.season)} · ${esc(x.name)}</a>`).join('')}</div>` : ''}</div></div>
      </div></div>
      ${row ? `<div class="page-title"><h1 style="font-size:16px">${esc(sLabel(s))}</h1>${pages}</div>
      <div class="card"><div class="kpis">
        <div class="kpi"><div class="v">${row.pos}</div><div class="k">место</div></div>
        <div class="kpi"><div class="v">${row.pts}</div><div class="k">очки</div></div>
        <div class="kpi"><div class="v">${row.w}-${row.d}-${row.l}</div><div class="k">В-Н-П</div></div>
        <div class="kpi"><div class="v">${row.gf}:${row.ga}</div><div class="k">мячи</div></div>
      </div>${row.form.length ? `<div class="note">Последние матчи: ${formHtml(row.form)}</div>` : ''}</div>` : ''}
      ${scorers.length ? `<div class="card"><div class="card-h">Лучшие игроки<span class="sub">голы · передачи</span></div>
        ${scorers.map(p => `<div class="list-row"><div class="grow"><div class="t">${esc(p.name)}</div></div><span class="val">${p.g}</span><span class="muted num" style="min-width:34px;text-align:right">${p.a} п.</span></div>`).join('')}</div>` : ''}
      <div class="card"><div class="card-h">Матчи<span class="sub">${ms.length}</span></div>${ms.map(m => matchRow(m, { showStage: true })).join('') || '<div class="empty">Нет матчей</div>'}</div>
      ${hist ? `<div class="card"><div class="card-h">История выступлений</div><div class="tbl-wrap"><table class="tbl"><thead><tr><th class="l">Турнир</th><th>Место</th><th>И</th><th class="hide-sm">В-Н-П</th><th>Мячи</th><th>О</th></tr></thead><tbody>${hist}</tbody></table></div></div>` : ''}`;
  }

  function eventRow(e, m, run) {
    const s = m.s;
    const [min, t, side, p, a] = e;
    let icon = '', what = '';
    if (t === 'goal') { icon = '⚽'; what = a ? `<small>пас: ${esc(a)}</small>` : ''; }
    else if (t === 'pen') { icon = '⚽'; what = '<small>пенальти</small>'; }
    else if (t === 'og') { icon = '⚽'; what = '<small>автогол</small>'; }
    else if (t === 'yc') { icon = '<span class="card-yc" title="Жёлтая карточка"></span>'; }
    else if (t === 'rc') { icon = '<span class="card-rc" title="Красная карточка"></span>'; }
    else if (t === 'mp') { icon = '✖'; what = '<small>нереализованный пенальти</small>'; }
    const who = `<div class="who"><b>${esc(p || (t === 'og' ? 'Автогол' : 'Гол'))}</b>${run ? `<span class="run">${run}</span>` : ''}${what}</div>`;
    const content = side === 'h' ? `${who}<span class="icon">${icon}</span>` : `<span class="icon">${icon}</span>${who}`;
    return `<div class="ev"><div class="evs h">${side === 'h' ? content : ''}</div><div class="min">${min != null ? min + "'" : ''}</div><div class="evs a">${side === 'a' ? content : ''}</div></div>`;
  }

  function viewMatch(id) {
    const m = MATCH.get(id);
    if (!m) return notFound();
    const s = m.s, st = stats(s), w = winner(m);
    let h = 0, a = 0, half2 = false;
    const rows = [];
    const evs = m.ev || [];
    if (evs.length) rows.push('<div class="half">1-й тайм</div>');
    evs.forEach(e => {
      if (!half2 && e[0] != null && e[0] > st.halfLen) { half2 = true; rows.push('<div class="half">2-й тайм</div>'); }
      let run = '';
      if (['goal', 'pen', 'og'].includes(e[1])) { if (e[2] === 'h') h++; else a++; run = `${h}:${a}`; }
      rows.push(eventRow(e, m, run));
    });
    const h2h = [...MATCH.values()].filter(x => x !== m && played(x) && ((x.h === m.h && x.a === m.a) || (x.h === m.a && x.a === m.h))).sort(byDate).reverse();
    let hw = 0, dr = 0, aw = 0;
    h2h.forEach(x => { const r = winner(x); if (r === 'd') dr++; else if ((r === 'h' ? x.h : x.a) === m.h) hw++; else aw++; });
    const meta = [sLabel(s), m.st || (m.r ? `Тур ${m.r}` : null), fmtLong(m.d)].filter(Boolean).join(' · ');
    const status = !played(m) ? 'Итоговый счёт не опубликован' : m.tech ? 'Технический результат' : m.pens ? `Серия пенальти <b>${m.pens[0]}:${m.pens[1]}</b>` : 'Матч завершён';
    return `
      <div class="card"><div class="mh">
        <div class="mh-meta">${esc(meta)}</div>
        <div class="mh-row">
          <a class="mh-team" href="${teamLink(m.h, s)}">${badge(m.h, s, 'lg')}<span class="name">${esc(tName(m.h, s))}</span></a>
          <div><div class="mh-score ${played(m) ? '' : 'unknown'}">${played(m) ? `${m.sc[0]} : ${m.sc[1]}` : '? : ?'}</div><div class="mh-status">${status}</div></div>
          <a class="mh-team" href="${teamLink(m.a, s)}">${badge(m.a, s, 'lg')}<span class="name">${esc(tName(m.a, s))}</span></a>
        </div>
      </div>
      ${m.note ? `<div class="note" style="border-top:1px solid var(--border)">${esc(m.note)}</div>` : ''}
      </div>
      <div class="card timeline"><div class="card-h">Ход матча<span class="sub">${evs.length ? '' : 'нет данных'}</span></div>
        ${rows.join('') || '<div class="empty">В посте с результатом не было хронологии матча</div>'}
        ${m.src ? `<div class="note" style="border-top:1px solid var(--border)">Источник: <a href="${TG}/${m.src}" target="_blank" rel="noopener" style="color:var(--accent)">пост в Telegram</a></div>` : ''}
      </div>
      <div class="card"><div class="card-h">Личные встречи<span class="sub">${h2h.length ? `${esc(tName(m.h, s))}: ${hw} В · ${dr} Н · ${aw} П` : ''}</span></div>
        ${h2h.length ? h2h.map(x => matchRow(x, { showSeason: true })).join('') : '<div class="empty">Других очных встреч в архиве нет</div>'}
      </div>`;
  }

  function seasonCard(s) {
    const st = stats(s);
    const champ = st.champion;
    const ts = st.topScorer && st.topScorer.g ? st.topScorer : null;
    const ta = st.topAssist && st.topAssist.a ? st.topAssist : null;
    const runner = s.runnerUp || (!s.incomplete && st.table[1] && st.table[0].team === champ ? st.table[1].team : null);
    return `<div class="card season-card">
      <div class="card-h">${esc(s.season)}<span class="sub">${esc(s.name)}</span></div>
      <div class="champ">${champ ? `${badge(champ, s, 'md')}<div><div class="t">🏆 ${esc(tName(champ, s))}</div><div class="muted" style="font-size:12px">${s.champion ? 'чемпион' : 'первое место в таблице'}</div></div>` : '<div class="muted">Чемпион в канале не указан</div>'}</div>
      <div class="rows">
        ${runner ? `<div><span>Серебро</span><span>${esc(tName(runner, s))}</span></div>` : ''}
        ${s.third ? `<div><span>Бронза</span><span>${esc(tName(s.third, s))}</span></div>` : ''}
        ${ts ? `<div><span>Бомбардир</span><span>${esc(ts.name)} — ${ts.g}</span></div>` : ''}
        ${ta ? `<div><span>Ассистент</span><span>${esc(ta.name)} — ${ta.a}</span></div>` : ''}
        <div><span>Матчей / голов</span><span>${s.matches.length || '—'} / ${st.goals || '—'}</span></div>
      </div>
      <a class="open" href="${link(s.matches.length ? 'table' : '', null, s)}">Открыть турнир →</a>
    </div>`;
  }

  function viewArchive() {
    const champs = new Map();
    SEASONS.forEach(s => { const c = stats(s).champion; if (c) { if (!champs.has(c)) champs.set(c, []); champs.get(c).push(s); } });
    const hall = [...champs.entries()].sort((a, b) => b[1].length - a[1].length || team(a[0]).name.localeCompare(team(b[0]).name));
    return `
      <div class="page-title"><h1>Архив сезонов</h1><span class="crumbs">${SEASONS.length} ${plural(SEASONS.length, 'турнир', 'турнира', 'турниров')} с 2017 года</span></div>
      <div class="card"><div class="card-h">Зал славы<span class="sub">титулы по всем дивизионам</span></div>
        ${hall.map(([id, list]) => `<a class="list-row" href="${teamLink(id)}">${badge(id)}<div class="grow"><div class="t">${esc(team(id).name)}</div><div class="s">${list.map(x => esc(x.season + ' ' + x.name.replace(' Division', '') + (x.champion ? '' : '*'))).join(' · ')}</div></div><span class="pill gold">🏆 ${list.length}</span></a>`).join('')}
        <div class="note">* чемпион в канале явно не назван — указана команда, занявшая первое место в итоговой таблице по опубликованным результатам.</div>
      </div>
      <div class="grid-cards" style="grid-template-columns:repeat(auto-fill,minmax(260px,1fr))">${SEASONS.slice().reverse().map(seasonCard).join('')}</div>`;
  }

  function viewRecords() {
    const all = [...MATCH.values()].filter(m => played(m) && !m.tech);
    const wins = all.slice().sort((a, b) => Math.abs(b.sc[0] - b.sc[1]) - Math.abs(a.sc[0] - a.sc[1]) || (b.sc[0] + b.sc[1]) - (a.sc[0] + a.sc[1])).slice(0, 10);
    const goals = all.slice().sort((a, b) => (b.sc[0] + b.sc[1]) - (a.sc[0] + a.sc[1]) || byDate(b, a)).slice(0, 10);
    const hauls = [];
    all.forEach(m => {
      const c = new Map();
      (m.ev || []).forEach(e => { if ((e[1] === 'goal' || e[1] === 'pen') && e[3]) { const k = e[2] + '|' + e[3]; c.set(k, (c.get(k) || 0) + 1); } });
      c.forEach((n, k) => { if (n >= 4) { const [side, name] = k.split('|'); hauls.push({ m, n, name, team: side === 'h' ? m.h : m.a }); } });
    });
    hauls.sort((a, b) => b.n - a.n || byDate(b.m, a.m));
    const best = SEASONS.filter(s => stats(s).topScorer && stats(s).topScorer.g).map(s => ({ s, p: stats(s).topScorer })).sort((a, b) => b.p.g - a.p.g).slice(0, 10);
    const mrow = m => matchRow(m, { showSeason: true });
    return `
      <div class="page-title"><h1>Рекорды лиги</h1><span class="crumbs">по всем турнирам архива</span></div>
      <div class="card"><div class="card-h">Крупнейшие победы</div>${wins.map(mrow).join('')}</div>
      <div class="card"><div class="card-h">Самые результативные матчи</div>${goals.map(mrow).join('')}</div>
      <div class="card"><div class="card-h">Больше всего голов за матч<span class="sub">4 и более</span></div>
        ${hauls.slice(0, 15).map(x => `<a class="list-row" href="${matchLink(x.m)}">${badge(x.team, x.m.s)}<div class="grow"><div class="t">${esc(x.name)}</div><div class="s">${esc(tName(x.m.h, x.m.s))} ${x.m.sc[0]}:${x.m.sc[1]} ${esc(tName(x.m.a, x.m.s))} · ${esc(x.m.s.season)}</div></div><span class="val">${x.n}</span></a>`).join('') || '<div class="empty">Нет данных</div>'}</div>
      <div class="card"><div class="card-h">Лучшие бомбардиры сезонов</div>
        ${best.map(x => `<a class="list-row" href="${link('stats', null, x.s)}">${badge(x.p.team, x.s)}<div class="grow"><div class="t">${esc(x.p.name)}</div><div class="s">${esc(tName(x.p.team, x.s))} · ${esc(sLabel(x.s))}</div></div><span class="val">${x.p.g}</span></a>`).join('')}</div>`;
  }

  function notFound() {
    return `<div class="card"><div class="empty">Страница не найдена. <a href="#/" style="color:var(--accent)">На главную</a></div></div>`;
  }

  // ---------------------------------------------------------------- sidebars
  function renderSides() {
    const s = cur, st = stats(s);
    sideL.innerHTML = seasonInfoCard(s) + (st.table.length ? `<div class="card"><div class="card-h">Команды<span class="sub">${st.table.length}</span></div>
      ${st.table.slice().sort((a, b) => tName(a.team, s).localeCompare(tName(b.team, s))).map(r => `<a class="list-row" href="${teamLink(r.team, s)}">${badge(r.team, s, 'sm')}<div class="grow"><div class="t" style="font-weight:500">${esc(tName(r.team, s))}</div></div></a>`).join('')}</div>` : '');
    const top = (key, title, val, tab) => {
      const list = st.players.filter(p => val(p) > 0).sort((a, b) => val(b) - val(a) || b.g - a.g).slice(0, 5);
      return list.length ? `<div class="card"><div class="card-h">${title}<a class="more" href="${link('stats', { tab })}">Все</a></div>
        ${list.map(p => `<div class="list-row">${badge(p.team, s, 'sm')}<div class="grow"><div class="t">${esc(p.name)}</div><div class="s">${esc(tName(p.team, s))}</div></div><span class="val">${val(p)}</span></div>`).join('')}</div>` : '';
    };
    const links = D.league.links || {};
    sideR.innerHTML = (st.table.length ? `<div class="card"><div class="card-h">Таблица<a class="more" href="${link('table')}">Полная</a></div>${standingsTable(s, { mini: true, limit: 8 })}</div>` : seasonInfoCard(s)) +
      top('g', 'Бомбардиры', p => p.g, 'scorers') + top('a', 'Ассистенты', p => p.a, 'assists') +
      `<div class="card"><div class="card-h">Unity League</div><div class="card-b" style="display:flex;flex-direction:column;gap:8px">
        ${links.telegram ? `<a class="btn" href="${esc(links.telegram)}" target="_blank" rel="noopener">Telegram-канал</a>` : ''}
        ${links.instagram ? `<a class="btn" href="${esc(links.instagram)}" target="_blank" rel="noopener">Instagram</a>` : ''}
        ${links.youtube ? `<a class="btn" href="${esc(links.youtube)}" target="_blank" rel="noopener">YouTube</a>` : ''}
        <span class="muted" style="font-size:12px">${esc(D.league.slogan || '')}</span></div></div>`;
  }

  // ---------------------------------------------------------------- shell
  function buildSelect() {
    const groups = new Map();
    SEASONS.slice().reverse().forEach(s => { if (!groups.has(s.season)) groups.set(s.season, []); groups.get(s.season).push(s); });
    select.innerHTML = [...groups.entries()].map(([g, list]) => `<optgroup label="${esc(g)}">${list.map(s => `<option value="${esc(s.id)}">${esc(sLabel(s))}</option>`).join('')}</optgroup>`).join('');
  }

  const TAB_OF = { '': 'matches', results: 'results', table: 'table', stats: 'stats', calendar: 'calendar', teams: 'teams', team: 'teams', archive: 'archive', records: 'records' };

  function render() {
    const { parts, q } = parseRoute();
    cur = resolveSeason(q, parts);
    store.set('ul-season', cur.id);
    select.value = cur.id;
    const p0 = parts[0] || '';
    let html;
    switch (p0) {
      case '': html = viewMatches(q); break;
      case 'results': html = viewResults(q); break;
      case 'table': html = viewTable(q); break;
      case 'stats': html = viewStats(q); break;
      case 'calendar': html = viewCalendar(q); break;
      case 'teams': html = viewTeams(q); break;
      case 'team': html = viewTeam(parts[1]); break;
      case 'match': html = viewMatch(parts[1]); break;
      case 'archive': html = viewArchive(); break;
      case 'records': html = viewRecords(); break;
      default: html = notFound();
    }
    app.innerHTML = html;
    renderSides();
    document.querySelectorAll('#tabs a').forEach(a => {
      a.classList.toggle('active', a.dataset.tab === TAB_OF[p0]);
      const base = a.getAttribute('href').split('?')[0];
      a.setAttribute('href', base + '?s=' + encodeURIComponent(cur.id));
    });
    const key = p0 + '/' + (parts[1] || '') + '/' + cur.id;
    if (key !== lastPath) window.scrollTo(0, 0);
    lastPath = key;
    const strip = document.getElementById('strip');
    const act = strip && strip.querySelector('.chip.active');
    if (act) {
      const center = () => {
        const sr = strip.getBoundingClientRect(), ar = act.getBoundingClientRect();
        strip.style.scrollBehavior = 'auto';
        strip.scrollLeft += ar.left - sr.left - (sr.width - ar.width) / 2;
        strip.style.scrollBehavior = '';
      };
      center();
      requestAnimationFrame(center);
    }
    const tf = document.getElementById('team-filter');
    if (tf) tf.addEventListener('change', () => { location.hash = link('results', { t: tf.value }); });
    const ts = document.getElementById('team-season');
    if (ts) ts.addEventListener('change', () => { location.hash = link('team/' + parts[1], null, SBY.get(ts.value)); });
    document.title = `${{ matches: 'Матчи', results: 'Результаты', table: 'Таблица', stats: 'Статистика', calendar: 'Календарь', teams: 'Команды', archive: 'Архив', records: 'Рекорды' }[TAB_OF[p0]] || 'Матч'} — Unity League`;
  }

  select.addEventListener('change', () => {
    const { parts, q } = parseRoute();
    const s = SBY.get(select.value);
    let path = parts.join('/');
    if (parts[0] === 'match') path = '';
    const keep = {};
    if (parts[0] === 'stats' && q.tab) keep.tab = q.tab;
    location.hash = link(path, keep, s);
  });
  document.getElementById('theme-btn').addEventListener('click', () => {
    const t = document.documentElement.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', t);
    store.set('ul-theme', t);
  });

  buildSelect();
  window.addEventListener('hashchange', render);
  render();
})();
