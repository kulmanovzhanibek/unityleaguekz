"""Шаг 3: raw_matches.json -> data/league.js.

Здесь же описаны команды (TEAMS/ALIASES), турниры (T) и ручные правки опечаток из постов.
Запуск обычно через scripts/telegram/run.py.
"""
import json, re, sys, collections
from datetime import datetime, date

RAW = json.load(open(sys.argv[1]))
MSGS = {m['id']: m for m in json.load(open(sys.argv[2]))}
OUT = sys.argv[3]

# ---------------------------------------------------------------- teams
TEAMS = {
    'adal': 'Adal Guesthouse', 'aktel': 'AKTEL', 'aqsay': 'Aqsay', 'aksay-alumni': 'Aksay Alumni',
    'aksay-jr': 'Aksay Jr', 'aktel-jr': 'AKTEL Jr', 'aktel-nextgen': 'AKTEL NextGen', 'aktobe': 'Aktobe',
    'akzhayik': 'Akzhayik', 'akzhayik-jr': 'Akzhayik Jr', 'alash-2': 'Alash-2', 'altyn-adam': 'Altyn Adam',
    'altyn-adam-jr': 'Altyn Adam Jr', 'altyn-adam-ng': 'Altyn Adam NG', 'altyn-adam-pro': 'Altyn Adam Pro',
    'ansar-ali': 'Ansar Ali', 'astana': 'Astana', 'atyrau': 'Atyrau', 'aulie-ata': 'Aulie Ata',
    'baiterek': 'Baiterek', 'bmg': 'BMG', 'bukhar-zhyrau': 'Bukhar Zhyrau', 'caspiy': 'Caspiy',
    'elimay-semey': 'Elimay Semey', 'ertis': 'Ertis', 'ey': 'EY', 'miners': 'FC Miners', 'qostanay': 'Qostanay',
    'griffins': 'Griffins', 'zhetisu': 'Zhetisu', 'zhetisu-zhas': 'Zhetisu Zhas', 'jezgrads': 'JezGrads',
    'kaztour': 'Kaztour', 'maiqudyq': 'Maiqudyq', 'mib': 'MIB', 'munaishy': 'Munaishy', 'munaishy-jr': 'Munaishy Jr',
    'narxoz': 'Narxoz', 'okzhetpes': 'Okzhetpes', 'old-school': 'Old School', 'ordabasy': 'Ordabasy',
    'ordabasy-jr': 'Ordabasy Jr', 'otyrar': 'Otyrar', 'pride': 'Pride', 'qurmet': 'Qurmet', 'sdc': 'SDC',
    'sdcl': 'SDCL', 'sdu': 'SDU', 'semey': 'Spartak Semey', 'sever': 'Sever', 'sunkar': 'Sunkar',
    'syntez': 'Syntez', 'taraz': 'Taraz', 'turan': 'Turan', 'vernyi': 'Vernyi', 'vostok': 'Vostok',
    'young-boyz': 'Young Boyz', 'zavod': 'Zavod', 'syrdaria': 'Syrdaria', 'ulytau-jr': 'Ulytau Jr',
}
ALIASES = {
    'adal guesthouse': 'adal', 'afc aktel': 'aktel', 'aktel': 'aktel', 'aktel premix pro': 'aktel',
    'aksay': 'aqsay', 'aqsay': 'aqsay', 'aqsay saint germain': 'aqsay', 'aqsay sg': 'aqsay', 'asg': 'aqsay',
    'aksay alumni': 'aksay-alumni', 'aksay jr': 'aksay-jr', 'aktel jr': 'aktel-jr', 'aktel nextgen': 'aktel-nextgen',
    'aktobe': 'aktobe', 'aqtobe': 'aktobe', 'akzhaiyk': 'akzhayik', 'akzhayik': 'akzhayik', 'aqjaiyq': 'akzhayik',
    'aqjayiq': 'akzhayik', 'akzhayik jr': 'akzhayik-jr', 'alash-2': 'alash-2', 'alash2': 'alash-2', 'alash 2': 'alash-2',
    'altyn adam': 'altyn-adam', 'altyn adam jr': 'altyn-adam-jr', 'altyn adam ng': 'altyn-adam-ng',
    'altyn adam pro': 'altyn-adam-pro', 'ansar ali': 'ansar-ali', 'astana': 'astana', 'atyrau': 'atyrau',
    'aulie ata': 'aulie-ata', 'baiterek': 'baiterek', 'baiterek rise capital': 'baiterek', 'balykmunaigas': 'bmg',
    'balykmunaygas': 'bmg', 'bmg': 'bmg', 'bmg nova': 'bmg', 'bmg-nova': 'bmg', 'bukhar zhyrau': 'bukhar-zhyrau',
    'caspiy': 'caspiy', 'elimay semey': 'elimay-semey', 'ertis': 'ertis', 'ey': 'ey', 'fc miners': 'miners',
    'miners': 'miners', 'fc qostanay': 'qostanay', 'qostanay': 'qostanay', 'griffins': 'griffins',
    'jetisu': 'zhetisu', 'jetysu': 'zhetisu', 'zhetisu': 'zhetisu', 'zhetysu': 'zhetisu', 'zhetisu zhas': 'zhetisu-zhas',
    'jez grads': 'jezgrads', 'jezgrads': 'jezgrads', 'jezgrads team': 'jezgrads', 'jezgrads teams': 'jezgrads',
    'kaztour': 'kaztour', 'maiqudyk': 'maiqudyq', 'maiqudyq': 'maiqudyq', 'mib': 'mib', 'munaishy': 'munaishy',
    'munaishy jr': 'munaishy-jr', 'narxoz': 'narxoz', 'okzhetpes': 'okzhetpes', 'oqzhetpes': 'okzhetpes',
    'old school': 'old-school', 'ordabasy': 'ordabasy', 'ordabasy jr': 'ordabasy-jr', 'otrar': 'otyrar',
    'otyrar': 'otyrar', 'pride': 'pride', 'qurmet': 'qurmet', 'sdc': 'sdc', 'sdcl': 'sdcl', 'sdu': 'sdu',
    'semey': 'semey', 'semey spartak': 'semey', 'spartak': 'semey', 'spartak semey': 'semey', 'sever': 'sever',
    'sunkar': 'sunkar', 'syntez': 'syntez', 'taraz': 'taraz', 'turan': 'turan', 'verniy': 'vernyi',
    'vernyi': 'vernyi', 'vostok': 'vostok', 'young boyz': 'young-boyz', 'zavod': 'zavod',
}


def team_key(name):
    n = name.lower().replace('ı', 'i').strip(' .!:')
    n = re.sub(r'\s+', ' ', n)
    return ALIASES.get(n)


# ---------------------------------------------------------------- tournaments
T = [
    dict(id='2017-summer', season='Summer 2017', name='Summer Division', kind='summer', start='2017-06-01', end='2017-10-05',
         champion='syrdaria', status='finished', teams=[],
         note='Сезон из 7 команд. Syrdaria выиграла все 6 матчей и стала чемпионом во второй раз; серебро — BMG (BalykMunaiGas). Всего забито 95 мячей (4,5 за матч). Протоколы матчей в канале не публиковались.'),
    dict(id='2017-student', season='Autumn 2017', name='Student Division', kind='student', start='2017-10-06', end='2017-11-13',
         champion='ulytau-jr', status='finished', teams=[],
         note='Групповой этап, полуфиналы и финал. Ulytau Jr (Жезказган) стали чемпионами, отыгравшись и в полуфинале, и в финале. Результаты публиковались картинками.'),
    dict(id='2017-18-premier', season='Winter 2017/18', name='Premier Division', kind='winter', start='2017-11-20', end='2018-03-01',
         champion='aktel', status='finished',
         teams='aqsay munaishy aktel altyn-adam griffins altyn-adam-ng ansar-ali syntez zhetisu akzhayik vostok aksay-jr'.split()),
    dict(id='2017-18-super', season='Winter 2017/18', name='Super Division', kind='winter', start='2017-12-20', end='2018-02-06',
         champion='ey', status='finished',
         teams='kaztour sdu ey young-boyz alash-2 zavod otyrar altyn-adam'.split(),
         note='8 команд, два этапа: сначала круг «все со всеми», затем команды делятся на две четвёрки.'),
    dict(id='2018-student', season='Spring 2018', name='Student League', kind='student', start='2018-04-01', end='2018-04-30',
         status='finished', incomplete=True,
         note='В канале опубликованы результаты только части матчей студенческой лиги.',
         teams='vostok elimay-semey griffins ordabasy-jr zhetisu-zhas baiterek munaishy aulie-ata altyn-adam-jr akzhayik-jr turan qostanay aktel-jr sdcl altyn-adam'.split()),
    dict(id='2018-19-premier', season='Winter 2018/19', name='Premier Division', kind='winter', start='2018-11-01', end='2019-02-15',
         champion='aqsay', runnerUp='aktel', third='zhetisu', status='finished', incomplete=True, expected=66,
         teams='griffins sdu altyn-adam bukhar-zhyrau ansar-ali sdcl aktel zhetisu aqsay vernyi bmg sever'.split(),
         note='Aqsay — первый титул в истории (единственное поражение за сезон). AKTEL — серебро, Zhetisu — бронза. В канале опубликованы протоколы только части туров.'),
    dict(id='2018-19-super', season='Winter 2018/19', name='Super Division', kind='winter', start='2018-11-01', end='2019-02-15',
         champion='sunkar', status='finished', incomplete=True, expected=22,
         note='Чемпион определился в матче за чемпионство: Sunkar — Altyn Adam Pro 7:1. В канале опубликованы протоколы только части туров.',
         teams='narxoz mib old-school sunkar altyn-adam-pro otyrar alash-2'.split()),
    dict(id='2019-student', season='Autumn 2019', name='Student Division Autumn Cup', kind='student', start='2019-09-20', end='2019-10-07',
         champion='altyn-adam-jr', status='finished',
         teams='turan zhetisu-zhas atyrau aktel-nextgen altyn-adam-jr sdc munaishy-jr jezgrads'.split(),
         aliases={'munaishy': 'munaishy-jr'}),
    dict(id='2019-20-premier', season='Winter 2019/20', name='Premier Division', kind='winter', start='2019-11-25', end='2020-02-10',
         status='finished', incomplete=True, expected=36,
         note='В канале опубликованы протоколы только части туров; итоговая таблица и чемпион публиковались картинкой.',
         teams='altyn-adam akzhayik turan aktel sdu zhetisu jezgrads aqsay vernyi'.split()),
    dict(id='2019-20-super', season='Winter 2019/20', name='Super Division', kind='winter', start='2020-01-10', end='2020-02-06',
         status='finished',
         teams='ey adal ansar-ali altyn-adam-pro sunkar vernyi qurmet'.split(),
         note='Круговой турнир из 7 команд, затем полуфиналы и финал (5 февраля 2020, Qurmet — Vernyi). Итоговый счёт финала в канале не опубликован.'),
    dict(id='2020-21', season='2020/21', name='Qurmet League', kind='winter', start='2020-12-10', end='2021-02-01',
         champion='altyn-adam', status='finished',
         teams='altyn-adam semey aqsay turan vernyi akzhayik ansar-ali griffins aktel-nextgen zhetisu'.split(),
         note='Altyn Adam досрочно выиграли турнир после 8-го тура.'),
    dict(id='2021-22', season='2021/22', name='Premier Division', kind='winter', start='2021-11-19', end='2022-03-20',
         status='finished', names={'baiterek': 'Baiterek Rise Capital'}, championFromTable=True,
         teams='ertis turan vernyi okzhetpes qostanay ansar-ali griffins maiqudyq jezgrads altyn-adam zhetisu semey aktel aqsay baiterek vostok'.split()),
    dict(id='2022-23', season='2022/23', name='Premier Division', kind='winter', start='2022-11-25', end='2023-03-15',
         status='finished', championFromTable=True,
         teams='bmg ertis caspiy aktel turan jezgrads maiqudyq aqsay semey ansar-ali vostok vernyi zhetisu altyn-adam okzhetpes'.split()),
    dict(id='2023-24', season='2023/24', name='Premier Division', kind='winter', start='2023-11-17', end='2024-02-20',
         champion='aqsay', status='finished', names={'aqsay': 'Aqsay SG', 'aktel': 'AKTEL Premix Pro'},
         teams='semey zhetisu griffins ertis altyn-adam okzhetpes turan jezgrads vernyi bmg caspiy ansar-ali aqsay vostok aktel'.split()),
    dict(id='2024-25', season='2024/25', name='Premier Division', kind='winter', start='2024-11-29', end='2025-02-20',
         champion='bmg', status='finished', names={'semey': 'Semey', 'aqsay': 'Aqsay SG'},
         note='BMG и AKTEL набрали по 42 очка; чемпион — BMG (победа в личной встрече 3:2). Pride сыграли 7 матчей, Aktobe — 8. Матч Turan — Ertis в канале не опубликован.',
         teams='aqsay astana vernyi ordabasy semey ertis aktel zhetisu jezgrads turan bmg caspiy vostok ansar-ali pride altyn-adam aktobe'.split()),
    dict(id='2025-26', season='2025/26', name='Premier Division', kind='winter', start='2025-11-27', end='2026-02-05',
         status='finished', names={'semey': 'Semey', 'bmg': 'BMG Nova', 'akzhayik': 'Aqjaiyq'}, championFromTable=True,
         note='19 туров. Astana, Ertis и Aqtobe сыграли лишь 1–2 матча в начале сезона. Матч BMG Nova — Griffins в канале не опубликован.',
         teams='aqsay zhetisu ansar-ali semey aksay-alumni caspiy bmg aktobe miners ordabasy aktel taraz altyn-adam vostok astana akzhayik ertis griffins'.split()),
]


def find_tournament(d, h, a):
    cands = []
    for t in T:
        if not t['teams']:
            continue
        if not (t['start'] <= d <= t['end']):
            continue
        ali = t.get('aliases', {})
        hh, aa = ali.get(h, h), ali.get(a, a)
        if hh in t['teams'] and aa in t['teams']:
            cands.append((t, hh, aa))
    return cands


# ---------------------------------------------------------------- markers (tour numbers)
MARK_RE = re.compile(r'(?:(\d{1,2})\s*[-‑]?\s*(?:st|nd|rd|th|’th|\'th|-?й|-?го)?\s*(?:тур|tour|week|matchweek)\b)'
                     r'|(?:(?:tour|week|matchweek|match-day|тур)\s*#?\s*(\d{1,2})\b)', re.I)
SKIP_MARK = re.compile(r'Расписание|Результат|Таблиц|таблиц|Игрок|сборная|Пропуск|после|бомбард|ассистент|Видео|Фото', re.I)


def marker_of(text):
    if SKIP_MARK.search(text) or len(text) > 90:
        return None
    m = MARK_RE.search(text)
    if not m:
        return None
    n = int(m.group(1) or m.group(2))
    div = None
    if re.search(r'super', text, re.I):
        div = 'Super Division'
    elif re.search(r'premier', text, re.I):
        div = 'Premier Division'
    return n, div


markers = []  # (datetime, n, div)
# в постах с матчами отметкой тура считаются только строки до первого матча:
# "(2 tour)" в самом заголовке — это перенесённый матч, а не начало тура
PRE = {r['msg']: r['pre'] for r in RAW if r['n'] == 0}
for mid, msg in MSGS.items():
    if not msg['text']:
        continue
    lines = PRE[mid] if mid in PRE else [l for l in msg['text'].split('\n') if l.strip(' —-')]
    mk = marker_of(' '.join(lines[:3])) if lines else None
    if mk:
        markers.append((msg, mk))

MONTHS = {'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4, 'мая': 5, 'июня': 6, 'июля': 7,
          'августа': 8, 'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12}


def pdate(s):
    m = re.match(r'(\d+) (\S+) (\d{4}), (\d+):(\d+):(\d+)', s)
    d, mon, y, H, M, S = m.groups()
    return datetime(int(y), MONTHS[mon], int(d), int(H), int(M), int(S))


markers = sorted(((pdate(msg['date']), n, div, msg['id']) for msg, (n, div) in markers))


def msgnum(mid):
    return int(mid.replace('message', ''))


# ---------------------------------------------------------------- name normalisation
KZ = str.maketrans({'ә': 'а', 'ғ': 'г', 'қ': 'к', 'ң': 'н', 'ө': 'о', 'ұ': 'у', 'ү': 'у', 'һ': 'х', 'і': 'и',
                    'ё': 'е', 'й': 'и', 'ы': 'ы', 'Ә': 'а', 'Ғ': 'г', 'Қ': 'к', 'Ң': 'н', 'Ө': 'о', 'Ұ': 'у',
                    'Ү': 'у', 'Һ': 'х', 'І': 'и', 'Ё': 'е', 'Й': 'и'})


def norm_tokens(name):
    n = name.translate(KZ).lower()
    n = re.sub(r'[^a-zа-я\s-]', ' ', n)
    toks = [t for t in re.split(r'[\s]+', n) if t]
    return toks


def clean_name(name):
    n = re.sub(r'\s+', ' ', name).strip(' .,;:-')
    n = re.sub(r'\s*\.\s*$', '', n)
    return n


LETTERS = re.compile(r'[A-Za-zА-Яа-яЁёӘәҒғҚқҢңӨөҰұҮүҺһІі]')

# ---------------------------------------------------------------- build matches
report = []
matches = []
for r in RAW:
    h, a = team_key(r['home']), team_key(r['away'])
    if not h or not a:
        report.append(f"DROP unknown teams: {r['msg']} {r['line']!r}")
        continue
    d = r['dt'][:10]
    cands = find_tournament(d, h, a)
    if len(cands) != 1:
        report.append(f"DROP tournament? ({len(cands)}): {r['msg']} {d} {r['line']!r}")
        continue
    t, h, a = cands[0]
    r['t'] = t['id']
    r['h'], r['a'] = h, a
    r['date'] = d
    matches.append(r)


TBY = {t['id']: t for t in T}

# ---------------------------------------------------------------- manual fixes (verified against the posts)
DROP = {'message420',  # "Syntez 0-0 Akzhayik" — анонс, результат в следующем посте (2-6)
        'message672'}  # "Ansar Ali - Semey — Перенесён", сыгран позже (message702)
matches = [m for m in matches if m['msg'] not in DROP]
for m in matches:
    if m['msg'] == 'message263':  # анонс message262: "Altyn Adam NG - Zhetisu", в посте с результатом опечатка
        m['h'] = 'altyn-adam-ng'
    if m['msg'] == 'message519':  # голы перечислены: сначала хозяева, потом гости
        for e, sd in zip([e for e in m['events'] if e['type'] in ('goal', 'pen', 'og')], 'hhhhaa'):
            e['force'] = sd
    if m['msg'] == 'message518':  # три гола Олжамурата (Altyn Adam Jr) без счёта, затем 1-3
        for e, sd in zip([e for e in m['events'] if e['type'] in ('goal', 'pen', 'og')], 'aaahah'):
            e['force'] = sd
    if m['msg'] == 'message616':  # строка "41' Исмайл Карымсак +1D" и затем "3- 2" — гол гостей
        m['events'].append({'raw': "41' Исмайл Карымсак", 'type': 'goal', 'min': 41, 'p': 'Исмайл Карымсак', 'a': '', 'score': [3, 2]})
        m['events'].sort(key=lambda e: (e['min'] is None, e['min'] or 0))
    if m['msg'] == 'message259':  # "27' Байтурсын Данияр (Aksay Jr)" без счёта — счёт в следующей строке не меняется: это не гол
        for e in m['events']:
            if e.get('min') == 27 and 'Байтурсын Данияр' in (e.get('p') or ''):
                e['type'], e['team'] = 'yc', 'Aksay Jr'
    if m['msg'] == 'message646':
        m['status'] = 'unknown'
        m['note'] = 'Финал. Итоговый счёт в канале не опубликован — последнее обновление трансляции: 1:1 (43\').'

# ---------------------------------------------------------------- stages
STAGE = {('message553', 0): 'Матч за чемпионство',
         ('message574', 0): 'Полуфинал', ('message574', 1): 'Полуфинал', ('message574', 2): 'Финал',
         ('message643', 0): 'Полуфинал', ('message644', 0): 'Полуфинал', ('message646', 0): 'Финал'}
for m in matches:
    st = STAGE.get((m['msg'], m['n']))
    if st:
        m['stage'] = st
# Super Division 2017/18: second meeting of a pair = second stage
seen = set()
for m in sorted([m for m in matches if m['t'] == '2017-18-super'], key=lambda m: m['dt']):
    k = frozenset((m['h'], m['a']))
    if k in seen:
        m['stage'] = 'Второй этап'
    seen.add(k)


# ---------------------------------------------------------------- roster priors
def tkey(t, raw_team):
    k = team_key(raw_team or '')
    return TBY[t].get('aliases', {}).get(k, k) if k else None


def pkey(name):
    return tuple(sorted(norm_tokens(name)))


def is_team_label(t, text):
    return bool(text) and tkey(t, text) is not None


roster = collections.defaultdict(collections.Counter)  # (t, pkey) -> Counter(team)
for m in matches:
    side_team = {'h': m['h'], 'a': m['a']}
    for e in m['events']:
        if e['type'] in ('goal', 'pen', 'og') and e.get('side') and e.get('p'):
            sc = e.get('score')
            team = side_team[e['side']]
            other = side_team['a' if e['side'] == 'h' else 'h']
            if e['type'] == 'og':
                roster[(m['t'], pkey(e['p']))][other] += 1
            else:
                roster[(m['t'], pkey(e['p']))][team] += 1
                if e.get('a') and not is_team_label(m['t'], e['a']):
                    roster[(m['t'], pkey(e['a']))][team] += 1
        if e['type'] in ('yc', 'rc', 'mp') and e.get('team') and e.get('p'):
            tk = tkey(m['t'], e['team'])
            if tk in (m['h'], m['a']):
                roster[(m['t'], pkey(e['p']))][tk] += 1


def tok_match(q, full):
    """query tokens q (may contain initials) all match tokens of full key."""
    used = set()
    for qt in q:
        ok = False
        for i, ft in enumerate(full):
            if i in used:
                continue
            if qt == ft or (len(qt) <= 2 and ft.startswith(qt)) or (len(qt) >= 4 and len(ft) >= 4 and similar(qt, ft) >= 0.8):
                used.add(i)
                ok = True
                break
        if not ok:
            return False
    return True


import difflib


def similar(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio()


def roster_team(t, name, teams):
    if not name:
        return None
    q = pkey(name)
    if not q:
        return None
    exact = roster.get((t, q))
    cnt = collections.Counter()
    if exact:
        cnt.update(exact)
    else:
        for (tt, k), c in roster.items():
            if tt == t and len(k) >= len(q) and tok_match(q, k):
                cnt.update(c)
    cnt = collections.Counter({k: v for k, v in cnt.items() if k in teams})
    if not cnt:
        return None
    top = cnt.most_common(2)
    if len(top) == 1 or top[0][1] >= 2 * top[1][1]:
        return top[0][0]
    return None


# ---------------------------------------------------------------- side solver (exact DP with ambiguity detection)
def solve(m):
    goals = [e for e in m['events'] if e['type'] in ('goal', 'pen', 'og')]
    n = len(goals)
    final = m['score']
    teams = (m['h'], m['a'])
    prior = []
    for e in goals:
        if e.get('force'):
            prior.append(1 if e['force'] == 'h' else -1)
            continue
        pr = 0
        lab = e.get('a') if is_team_label(m['t'], e.get('a')) else None
        if lab:
            tk = tkey(m['t'], lab)
            if tk in teams:
                pr = 1 if tk == m['h'] else -1
                if e['type'] == 'og':
                    pr = -pr
            e['a'] = ''
        if not pr:
            rt = roster_team(m['t'], e.get('p'), teams)
            if rt:
                pr = 1 if rt == m['h'] else -1
                if e['type'] == 'og':
                    pr = -pr
            elif e.get('a') and e['type'] != 'og':
                rt = roster_team(m['t'], e['a'], teams)
                if rt:
                    pr = 1 if rt == m['h'] else -1
        prior.append(pr)

    def cost(i, h, side):
        nh, na = (h + 1, i - h) if side == 'h' else (h, i - h + 1)
        c = 0.0
        sc = goals[i].get('score')
        if sc:
            c += 0 if (sc[0], sc[1]) == (nh, na) else 1
        if goals[i].get('force'):
            c += 0 if goals[i]['force'] == side else 100
        pr = prior[i]
        if pr and (pr > 0) != (side == 'h'):
            c += 0.6
        return c

    INF = float('inf')
    use_final = final is not None and final[0] + final[1] == n
    f = [[INF] * (n + 2) for _ in range(n + 1)]
    f[0][0] = 0
    for i in range(n):
        for h in range(i + 1):
            if f[i][h] == INF:
                continue
            f[i + 1][h + 1] = min(f[i + 1][h + 1], f[i][h] + cost(i, h, 'h'))
            f[i + 1][h] = min(f[i + 1][h], f[i][h] + cost(i, h, 'a'))
    g = [[INF] * (n + 2) for _ in range(n + 1)]
    for h in range(n + 1):
        if not use_final or h == final[0]:
            g[n][h] = 0
    for i in range(n - 1, -1, -1):
        for h in range(i + 1):
            g[i][h] = min(cost(i, h, 'h') + g[i + 1][h + 1], cost(i, h, 'a') + g[i + 1][h])
    opt = g[0][0]
    if opt == INF:
        return ['unsolvable']
    issues = []
    for i in range(n):
        best = {}
        for side in ('h', 'a'):
            v = INF
            for h in range(i + 1):
                if f[i][h] == INF:
                    continue
                nh = h + 1 if side == 'h' else h
                v = min(v, f[i][h] + cost(i, h, side) + g[i + 1][nh])
            best[side] = v
        ok = [sd for sd in ('h', 'a') if abs(best[sd] - opt) < 1e-9]
        goals[i]['side'] = ok[0] if len(ok) == 1 else None
        if len(ok) != 1:
            issues.append(f"ambiguous: {goals[i]['raw']}")
    if opt >= 1:
        issues.append(f'cost={opt:.1f}')
    return issues


# cards: side from team label or roster
def card_side(m, e):
    teams = (m['h'], m['a'])
    if e.get('team'):
        tk = tkey(m['t'], e['team'])
        if tk in teams:
            return 'h' if tk == m['h'] else 'a'
    rt = roster_team(m['t'], e.get('p'), teams)
    if rt:
        return 'h' if rt == m['h'] else 'a'
    return None


def rebuild_roster():
    roster.clear()
    for m in matches:
        side_team = {'h': m['h'], 'a': m['a']}
        for e in m['events']:
            if e['type'] in ('goal', 'pen', 'og') and e.get('side') and e.get('p'):
                team = side_team[e['side']]
                other = side_team['a' if e['side'] == 'h' else 'h']
                roster[(m['t'], pkey(e['p']))][other if e['type'] == 'og' else team] += 1
                if e['type'] != 'og' and e.get('a') and not is_team_label(m['t'], e['a']):
                    roster[(m['t'], pkey(e['a']))][team] += 1
            if e['type'] in ('yc', 'rc', 'mp') and e.get('team') and e.get('p'):
                tk = tkey(m['t'], e['team'])
                if tk in (m['h'], m['a']):
                    roster[(m['t'], pkey(e['p']))][tk] += 1


for m in matches:
    solve(m)
rebuild_roster()

solve_report = []
for m in matches:
    iss = solve(m)
    for e in m['events']:
        if e['type'] in ('yc', 'rc', 'mp'):
            e['side'] = card_side(m, e)
    if m['score'] is None and m.get('status') != 'unknown':
        hs = sum(1 for e in m['events'] if e['type'] in ('goal', 'pen', 'og') and e['side'] == 'h')
        as_ = sum(1 for e in m['events'] if e['type'] in ('goal', 'pen', 'og') and e['side'] == 'a')
        unres = sum(1 for e in m['events'] if e['type'] in ('goal', 'pen', 'og') and e['side'] is None)
        m['score'] = [hs, as_]
        iss.append(f'score from events {hs}-{as_} unresolved={unres}')
    if iss:
        solve_report.append(f"{m['t']} {m['msg']} {m['line']} :: {'; '.join(iss)}")
if solve_report:
    print('Матчи, где хронология голов расходится со счётом или требует проверки:')
    print('\n'.join('  ' + r for r in solve_report))

# ---------------------------------------------------------------- rounds from tour markers
TOUR_INLINE = re.compile(r'\(\s*(\d{1,2})\s*(?:st|nd|rd|th)?\s*(?:tour|тур)\s*\)', re.I)
for m in matches:
    t = TBY[m['t']]
    rnd = None
    mm = TOUR_INLINE.search(m['line']) or next((TOUR_INLINE.search(p) for p in m['pre'] if TOUR_INLINE.search(p)), None)
    if mm:
        rnd = int(mm.group(1))
    else:
        for p in m['pre']:
            mk = marker_of(p)
            if mk and (mk[1] is None or mk[1] == t['name']):
                rnd = mk[0]
        if rnd is None:
            dt = datetime.fromisoformat(m['dt'])
            best = None
            for mdt, n, div, mid in markers:
                if mdt <= dt and mdt.date() == dt.date():
                    if div is None or div == t['name']:
                        if t['start'] <= mdt.date().isoformat() <= t['end']:
                            best = (mdt, n)
            if best:
                rnd = best[1]
    m['round'] = rnd
    m['round_inline'] = bool(mm)


# Туры, не помеченные в канале, восстанавливаются: в туре каждая команда играет не больше одного раза,
# тур укладывается в несколько соседних дней (посты иногда выходят на 1–2 дня позже), а явные отметки
# «N тур» из постов служат опорными точками. Если восстановить туры непротиворечиво не удаётся
# (неполные или нерегулярные турниры), матчи остаются без номера тура и сайт группирует их по дням.
def infer_rounds(ms, cap, use_marks, active=None, lookback=2, window=14, per_day=False):
    tours = {}
    front = 0
    out = {}
    prev_day = None

    def put(m, num, d):
        t = tours.setdefault(num, {'teams': set(), 'n': 0, 'last': d})
        t['teams'].update((m['h'], m['a']))
        t['n'] += 1
        t['last'] = max(t['last'], d)
        out[id(m)] = num

    for m in ms:
        d = date.fromisoformat(m['date'])
        if m['round_inline']:
            put(m, m['round_mark'], d)
            continue
        mk = m['round_mark'] if use_marks else None
        if mk is not None:
            front = max(front, mk)
            put(m, mk, d)
            prev_day = d
            continue
        if per_day:  # формат «один игровой день — один тур»
            if d != prev_day:
                front += 1
            prev_day = d
            t, pt = tours.get(front), tours.get(front - 1)
            busy = t and (m['h'] in t['teams'] or m['a'] in t['teams'])
            if busy and pt and pt['n'] < cap and m['h'] not in pt['teams'] and m['a'] not in pt['teams']:
                put(m, front - 1, d)  # доигрывали матч предыдущего тура
            else:
                put(m, front, d)
            continue
        # перенесённый матч: в каком-то из прошлых туров не сыграли ровно эти две команды
        num = None
        if active:
            for k, t in sorted(tours.items()):
                if k < front and t['n'] == cap - 1 and active - t['teams'] == {m['h'], m['a']}:
                    num = k
                    break
        # дыра в одном из последних туров (опоздавший пост) или следующий тур
        for k in ([] if num else range(max(1, front - lookback), front + 1)):
            t = tours.get(k)
            if t is None or (t['n'] < cap and m['h'] not in t['teams'] and m['a'] not in t['teams'] and (d - t['last']).days <= window):
                num = k
                break
        if num is None:
            front += 1
            num = front
        put(m, num, d)
    return out


def rounds_ok(ms, rounds, cap, allowed_max):
    per = collections.defaultdict(list)
    for m in ms:
        per[rounds[id(m)]].append(m)
    for r, lst in per.items():
        teams = [t for m in lst for t in (m['h'], m['a'])]
        if len(lst) > cap or len(teams) != len(set(teams)):
            return False
    return max(per) <= allowed_max


for m in matches:
    m['round_mark'] = m['round']
for t in T:
    ms = sorted([m for m in matches if m['t'] == t['id'] and not m.get('stage')], key=lambda m: (m['dt'], m['n']))
    if not ms:
        continue
    cnt = collections.Counter()
    for m in ms:
        cnt[m['h']] += 1
        cnt[m['a']] += 1
    top = max(cnt.values())
    n_active = sum(1 for v in cnt.values() if v >= top / 2)
    cap = max(1, n_active // 2)
    marks = [m['round_mark'] for m in ms if m['round_mark']]
    allowed = max([n_active - 1 if n_active % 2 == 0 else n_active] + marks)
    chosen = None
    if t['kind'] == 'winter' and not t.get('incomplete'):
        active = {t2 for t2, v in cnt.items() if v >= top / 2}
        for per_day, use_marks in ((True, True), (False, True), (False, False)):
            r = infer_rounds(ms, cap, use_marks, active=active, per_day=per_day)
            if rounds_ok(ms, r, cap, allowed):
                chosen = r
                break
    elif all(m['round_mark'] for m in ms):
        chosen = {id(m): m['round_mark'] for m in ms}
    for m in ms:
        m['round'] = chosen[id(m)] if chosen else None
    if '-v' in sys.argv:
        rc = collections.Counter(m['round'] for m in ms)
        print('tours', t['id'], 'cap', cap, ' '.join(f'{r}:{c}' for r, c in sorted(rc.items(), key=lambda kv: (kv[0] is None, kv[0] or 0))))

# ---------------------------------------------------------------- player names
def tidy(name):
    n = re.sub(r'\s+', ' ', (name or '')).strip(' .,;:-()')
    n = re.sub(r'\s*\(\s*$', '', n)
    n = re.sub(r'([A-Za-zА-Яа-яЁёӘәҒғҚқҢңӨөҰұҮүҺһІі])\.(?=\S)', r'\1. ', n)
    return n.strip()


def is_full(name):
    toks = norm_tokens(name)
    return len(toks) >= 2 and all(len(t) > 2 for t in toks)


# collect (t, team) -> Counter(display variants)
occ = collections.defaultdict(collections.Counter)
for m in matches:
    side_team = {'h': m['h'], 'a': m['a'], None: None}
    for e in m['events']:
        sd = e.get('side')
        if sd is None:
            continue
        if e['type'] in ('goal', 'pen'):
            team = side_team[sd]
            if e.get('p'):
                occ[(m['t'], team)][tidy(e['p'])] += 1
            if e.get('a'):
                occ[(m['t'], team)][tidy(e['a'])] += 1
        elif e['type'] == 'og':
            if e.get('p'):
                occ[(m['t'], side_team['a' if sd == 'h' else 'h'])][tidy(e['p'])] += 1
        elif e.get('p'):
            occ[(m['t'], side_team[sd])][tidy(e['p'])] += 1

canon = {}  # (t, team, variant) -> display
for (t, team), cnt in occ.items():
    variants = [v for v in cnt if v and LETTERS.search(v)]
    parent = {v: v for v in variants}

    def find(v):
        while parent[v] != v:
            parent[v] = parent[parent[v]]
            v = parent[v]
        return v

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra == rb:
            return
        # keep the more frequent / fuller name as root
        ka = (is_full(ra), cnt[ra], len(ra))
        kb = (is_full(rb), cnt[rb], len(rb))
        if kb > ka:
            ra, rb = rb, ra
        parent[rb] = ra

    keys = {v: pkey(v) for v in variants}
    # exact token-set equality (order / kazakh letters / й-и)
    byk = collections.defaultdict(list)
    for v in variants:
        byk[keys[v]].append(v)
    for vs in byk.values():
        for v in vs[1:]:
            union(vs[0], v)
    # fuzzy: same token count, each token similar
    vlist = sorted(variants, key=lambda v: -cnt[v])
    for i, a in enumerate(vlist):
        for b2 in vlist[i + 1:]:
            ka, kb = keys[a], keys[b2]
            if len(ka) == len(kb) >= 2 and all(len(x) > 2 for x in ka + kb):
                import itertools
                ok = any(all(similar(x, y) >= 0.75 for x, y in zip(ka, perm)) for perm in itertools.permutations(kb))
                if ok:
                    union(a, b2)
    # initials / single token -> unique full name
    fulls = [v for v in variants if is_full(v)]
    for v in variants:
        if is_full(v):
            continue
        q = keys[v]
        if not q:
            continue
        cands = {find(f) for f in fulls if tok_match(q, keys[f])}
        if len(cands) == 1:
            union(cands.pop(), v)
    for v in variants:
        canon[(t, team, v)] = find(v)


def cname(t, team, raw):
    v = tidy(raw)
    if not v or not LETTERS.search(v):
        return None
    if re.search(r'опазд|penal|пенальт|double|автогол|^аг$', v, re.I):
        return None
    return canon.get((t, team, v), v)


# ---------------------------------------------------------------- один игрок во всех сезонах
# Узел — (турнир, команда, имя). Полные имена объединяются по совпадению слов (порядок, казахские буквы)
# и по опечатке в одном слове; сокращения вида «Данияр О» присоединяются к полному имени, только если
# в той же команде (в любом сезоне) подходит ровно один игрок. Иначе сокращение — отдельный игрок команды.
def people(m, e):
    sd = e.get('side')
    if sd is None:
        return []
    st = {'h': m['h'], 'a': m['a']}
    other = st['a' if sd == 'h' else 'h']
    if e['type'] == 'og':
        return [(other, e.get('p'))]
    out = [(st[sd], e.get('p'))]
    if e['type'] in ('goal', 'pen') and e.get('a'):
        out.append((st[sd], e.get('a')))
    return out


node_cnt = collections.Counter()
for m in matches:
    for e in m['events']:
        if e['type'] not in ('goal', 'pen', 'og', 'yc', 'rc', 'mp'):
            continue
        for team, raw in people(m, e):
            n = cname(m['t'], team, raw) if raw else None
            if n:
                node_cnt[(m['t'], team, n)] += 1

P_PARENT = {k: k for k in node_cnt}


def pfind(k):
    while P_PARENT[k] != k:
        P_PARENT[k] = P_PARENT[P_PARENT[k]]
        k = P_PARENT[k]
    return k


def punion(a, b):
    ra, rb = pfind(a), pfind(b)
    if ra != rb:
        P_PARENT[rb] = ra


full_nodes = [k for k in node_cnt if is_full(k[2])]
by_key = collections.defaultdict(list)
for k in full_nodes:
    by_key[pkey(k[2])].append(k)
for ks in by_key.values():
    for k in ks[1:]:
        punion(ks[0], k)
key_teams = {key: {k[1] for k in ks} for key, ks in by_key.items()}
tok_index = collections.defaultdict(set)
for key in by_key:
    for tk in key:
        tok_index[tk].add(key)
for key in by_key:
    for tk in key:
        for other in tok_index[tk]:
            if other <= key or len(other) != len(key):
                continue
            ra = [x for x in key if x not in other]
            rb = [x for x in other if x not in key]
            if len(ra) != 1 or len(rb) != 1:
                continue
            need = 0.75 if key_teams[key] & key_teams[other] else 0.86
            if similar(ra[0], rb[0]) >= need:
                punion(by_key[key][0], by_key[other][0])

def initials_match(q, full):
    """«Данияр О» ~ «Олджамурат Данияр»: слова совпадают точно, однобуквенные — по первой букве."""
    used = set()
    for qt in q:
        hit = next((i for i, ft in enumerate(full) if i not in used and (
            qt == ft or (len(qt) <= 2 and ft.startswith(qt))
            or (min(len(qt), len(ft)) >= 6 and abs(len(qt) - len(ft)) <= 3 and (qt.startswith(ft) or ft.startswith(qt))))), None)
        if hit is None:
            return False
        used.add(hit)
    return True


team_full = collections.defaultdict(set)  # team -> {pkey of full names}
for k in full_nodes:
    team_full[k[1]].add(pkey(k[2]))
for k in node_cnt:
    if is_full(k[2]):
        continue
    q = pkey(k[2])
    if not q:
        continue
    roots = {pfind(by_key[fk][0]) for fk in team_full[k[1]] if len(fk) >= len(q) and initials_match(q, fk)}
    if len(roots) == 1:
        punion(roots.pop(), k)
abbr = collections.defaultdict(list)
for k in node_cnt:
    if pfind(k) == k and not is_full(k[2]):
        abbr[(k[1], pkey(k[2]))].append(k)
for ks in abbr.values():
    for k in ks[1:]:
        punion(ks[0], k)

groups = collections.defaultdict(list)
for k in node_cnt:
    groups[pfind(k)].append(k)


def display(ks):
    c = collections.Counter()
    for k in ks:
        c[k[2]] += node_cnt[k]
    full = [n for n, _ in c.most_common() if is_full(n)]
    return full[0] if full else c.most_common(1)[0][0]


PLAYERS = sorted(groups.values(), key=lambda ks: display(ks).lower())
PLAYER_NAMES = [display(ks) for ks in PLAYERS]
PID = {k: i for i, ks in enumerate(PLAYERS) for k in ks}


def pid(t, team, raw):
    n = cname(t, team, raw) if raw else None
    return PID.get((t, team, n)) if n else None


if '-v' in sys.argv:
    print('players', len(PLAYERS), 'from', len(node_cnt), 'season entries')


# ---------------------------------------------------------------- output
SHORT = {
    'altyn-adam': 'ALT', 'altyn-adam-ng': 'ANG', 'altyn-adam-jr': 'AJR', 'altyn-adam-pro': 'PRO', 'aksay-alumni': 'ALM',
    'aksay-jr': 'AKJ', 'aktel-jr': 'ATJ', 'aktel-nextgen': 'ANX', 'akzhayik-jr': 'AZJ', 'ansar-ali': 'ANS', 'aqsay': 'AQS',
    'semey': 'SEM', 'young-boyz': 'YB', 'old-school': 'OS', 'adal': 'ADL', 'bukhar-zhyrau': 'BZH', 'elimay-semey': 'ELS',
    'zhetisu-zhas': 'ZHZ', 'aulie-ata': 'AUL', 'munaishy-jr': 'MNJ', 'ordabasy-jr': 'ODJ', 'alash-2': 'AL2', 'jezgrads': 'JEZ',
    'miners': 'MIN', 'baiterek': 'BAI', 'aktobe': 'AKB', 'sdcl': 'SCL', 'akzhayik': 'AKZ', 'zhetisu': 'ZHE', 'ulytau-jr': 'ULY',
}


def short_of(name):
    words = re.findall(r'[A-Za-z0-9]+', name)
    if len(words) == 1:
        w = words[0]
        return w[:3].upper()
    return ''.join(w[0] for w in words[:3]).upper()


PALETTE = ['#e63946', '#1d8fe1', '#2bb673', '#f4a300', '#8e5cd9', '#00a6a6', '#ff6b35', '#5c7c99', '#d63384',
           '#3a86ff', '#06d6a0', '#c9a227', '#7b2cbf', '#ef476f', '#118ab2', '#8ac926', '#fb5607', '#6c757d']

used_teams = set()
out_t = []
for t in T:
    ms = sorted([m for m in matches if m['t'] == t['id']], key=lambda m: (m['dt'], m['n']))
    tm = []
    for i, m in enumerate(ms):
        side_team = {'h': m['h'], 'a': m['a']}
        ev = []
        for e in m['events']:
            sd = e.get('side')
            typ = e['type']
            if typ in ('goal', 'pen', 'og'):
                if sd is None:
                    continue
                if typ == 'og':
                    p = pid(t['id'], side_team['a' if sd == 'h' else 'h'], e.get('p'))
                    a = None
                else:
                    p = pid(t['id'], side_team[sd], e.get('p'))
                    a = pid(t['id'], side_team[sd], e.get('a')) if e.get('a') else None
                row = [e.get('min'), typ, sd, p]
                if a is not None:
                    row.append(a)
                ev.append(row)
            elif typ in ('yc', 'rc', 'mp'):
                if sd is None:
                    continue
                ev.append([e.get('min'), typ, sd, pid(t['id'], side_team[sd], e.get('p'))])
        rec = {'id': f"{t['id']}-{i + 1}", 'd': m['date'], 'h': m['h'], 'a': m['a'], 'sc': m['score']}
        if m.get('round'):
            rec['r'] = m['round']
        if m.get('stage'):
            rec['st'] = m['stage']
        if m.get('status') == 'unknown':
            rec['sc'] = None
            rec['s'] = 'unknown'
        if m.get('pens'):
            rec['pens'] = m['pens']
        if m.get('technical') or any('тех' in (x or '').lower() for x in [m.get('tail', '')]):
            rec['tech'] = True
        if m.get('note'):
            rec['note'] = m['note']
        if ev:
            rec['ev'] = ev
        rec['src'] = int(m['msg'].replace('message', ''))
        tm.append(rec)
        used_teams.update([m['h'], m['a']])
    o = {k: t[k] for k in ('id', 'season', 'name', 'status') if k in t}
    for k in ('champion', 'runnerUp', 'third', 'note', 'names', 'incomplete', 'expected', 'championFromTable'):
        if t.get(k):
            o[k] = t[k]
    o['teams'] = t['teams'] or []
    o['start'], o['end'] = (ms[0]['date'], ms[-1]['date']) if ms else (t['start'], t['end'])
    o['matches'] = tm
    if t.get('champion'):
        used_teams.add(t['champion'])
    out_t.append(o)

teams_out = []
for i, (tid, name) in enumerate(sorted(TEAMS.items(), key=lambda kv: kv[1].lower())):
    if tid in used_teams:
        teams_out.append({'id': tid, 'name': name, 'short': SHORT.get(tid) or short_of(name), 'color': PALETTE[i % len(PALETTE)]})

data = {
    'league': {
        'name': 'Unity League', 'tagline': 'Футзал 5×5 · лига выпускников лицеев Казахстана', 'slogan': 'Our game is Qurmet',
        'founded': '2013', 'points': {'win': 3, 'draw': 1, 'loss': 0},
        'links': {'telegram': 'https://t.me/unityleaguekz', 'instagram': 'https://www.instagram.com/unityleaguekz/',
                  'youtube': 'https://www.youtube.com/channel/UCghU9V5joWGX-ej4ZZlbrnw'},
        'source': 'Telegram-канал @unityleaguekz (экспорт сообщений 2017–2026)',
    },
    'teams': teams_out,
    'players': PLAYER_NAMES,
    'seasons': out_t,
}
js = ('// Данные Unity League, собранные из экспорта Telegram-канала @unityleaguekz.\n'
      '// Генерируется скриптом scripts/build_from_telegram.py — правки удобнее вносить в overrides скрипта\n'
      '// или прямо здесь (формат описан в README.md).\n'
      'window.LEAGUE_DATA = ' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';\n')
open(OUT, 'w').write(js)
print('written', OUT, len(js), 'bytes;', sum(len(t['matches']) for t in out_t), 'matches;', len(teams_out), 'teams')
