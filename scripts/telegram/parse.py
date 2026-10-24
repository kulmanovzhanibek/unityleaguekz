"""Шаг 2: msgs.json -> raw_matches.json.

Находит в постах заголовки матчей («A 3:2 B», «A - B 5-3 (FT)», «A vs B FT» …)
и строки событий (голы, ассисты, карточки, пенальти) во всех форматах канала 2017–2026.
"""
import json, re, sys
from datetime import datetime

MONTHS = {'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4, 'мая': 5, 'июня': 6, 'июля': 7,
          'августа': 8, 'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12}


def parse_date(s):
    m = re.match(r'(\d+) (\S+) (\d{4}), (\d+):(\d+):(\d+)', s)
    d, mon, y, H, M, S = m.groups()
    return datetime(int(y), MONTHS[mon], int(d), int(H), int(M), int(S))


EMOJI_STRIP = re.compile('[☀-➿\U0001F000-\U0001FAFF️‍]')
SEP = r'\s*[-:–—]\s*'
H1 = re.compile(r'^(?P<h>.*?\S)\s*(?<!\d)(?P<hs>\d{1,2})' + SEP + r'(?P<as>\d{1,2})(?!\d)\s*(?P<a>[^\d\s(].*?)?\s*'
                r'(?P<tail>\([^)]*\)?|FT|Live!?|LIVE|live)?\s*$')
H2 = re.compile(r'^(?P<h>[^\d\s].*?)\s+(?:vs|Vs|VS|-|–)\s+(?P<a>[^\d].*?)\s*(?P<tail>FT|Live!?|LIVE)?\s*$')
CARD_OR_GOAL = re.compile(r'(⚽|⚠|🟨|🟥|🛑|ЖК|КК)')
SECTION = re.compile(r'^(\d+\s*(st|nd|rd|th|me)?\s*(half|time)|first half|second half|half time|full time|\d\s*-?\s*тайм|live!?|ft)\W*$', re.I)
TRAIL_SCORE = re.compile(r'\(?\s*(?<![\d])(\d{1,2})\s*[-:–]\s*(\d{1,2})\s*\)?\s*(\([^()]*\)?)?\s*$', re.I)


def clean(s):
    s = EMOJI_STRIP.sub(' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def split_name_paren(s):
    """'Name (Other)' -> ('Name', 'Other'); tolerant to unclosed parens."""
    s = s.strip()
    m = re.match(r'^(.*?)\s*\(\s*([^()]*?)\s*\)?\s*$', s)
    if m and m.group(1):
        return m.group(1).strip(' .,;:'), (m.group(2) or '').strip(' .,;:')
    return s.strip(' .,;:'), ''


def parse_event(line):
    """Return dict describing the event line or None."""
    raw = line
    s = line.strip()
    if not s or SECTION.match(clean(s)):
        return None
    low = s.lower()
    ev = {'raw': raw}
    # running score at the end
    score = None
    m = TRAIL_SCORE.search(s)
    if '+1D' in s:
        return None
    if m:
        score = (int(m.group(1)), int(m.group(2)))
        tail = m.group(3) or ''
        s = s[:m.start()].rstrip()
        if re.search(r'[аa]вто\s?гол|АГ', tail, re.I):
            ev['og'] = True
        elif tail:
            s = s + ' ' + tail
    # minute
    mm = re.search(r'(\d{1,3})\s*(?:\+\s*\d+)?\s*(?:\'|’|‘|′|`|,|;)?', s)
    minute = None
    pre = s[:mm.start()] if mm else ''
    pre2 = re.sub(r'ЖК|КК|АГ\.?|Нер\.?\s*(?:д\.?\s*)?пен\.?|Пен\.?', '', pre)
    if re.search(r'(^|[^а-я])Пен\.?', pre) and not re.search(r'Нер', pre):
        ev['pen_prefix'] = True
    if mm and len(pre) <= 14 and not re.search(r'[A-Za-zА-Яа-яЁёӘәҒғҚқҢңӨөҰұҮүҺһІі]', pre2):
        minute = int(mm.group(1))
        body = s[:mm.start()] + ' ' + s[mm.end():]
    else:
        body = s
    has_ball = '⚽' in body
    yel = body.count('⚠') + body.count('🟨') + (1 if re.search(r'(^|\s)ЖК(\s|:|$)', body) else 0) + (1 if re.search(r'yellow card', body, re.I) else 0)
    red = body.count('🟥') + body.count('🛑') + (1 if re.search(r'(^|\s)КК(\s|:|$)', body) else 0) + body.count('🔺') + (1 if re.search(r'red card', body, re.I) else 0)
    body = re.sub(r'(yellow|red) card', ' ', body, flags=re.I)
    missed = bool(re.search(r'Нер\.?\s*(?:д\.?\s*)?пен|Нереализ|Penatly|Penalty\)|🚫|❌', body)) and not score
    if '❌' in body and yel >= 2:
        red += 1
        missed = False
    is_og = ev.get('og') or bool(re.search(r'[аa]вто\s?гол|(^|\s|⚽\uFE0F?)АГ\.?(\s|\d|\'|’|$)', body, re.I))
    is_pen = (bool(re.search(r'\(\s*пен|\(\s*д\.?\s*пен|пенальти|penalty|(^|\s)Пен\.', body, re.I)) or ev.pop('pen_prefix', False)) and not missed
    text = clean(body)
    text = re.sub(r'^(ЖК|КК)\s*', '', text)
    text = re.sub(r'(^|\s)АГ\.?[\'’]?(\s|$)', ' ', text)
    text = re.sub(r'\(?\s*[аa]вто\s?гол\s*\)?', ' ', text, flags=re.I)
    text = re.sub(r'Нер\.?\s*(?:д\.?\s*)?пен\.?', '', text)
    text = re.sub(r'\(\s*(автогол|д\.?\s*пен\.?|пен\.?|пенальти|Double Penatly|Нереализованный ДП)\s*\)', '', text, flags=re.I)
    text = re.sub(r'\(\s*пен\.?\s+', '(', text, flags=re.I)
    text = re.sub(r'^\W*Пен\.?\s*', '', text)
    text = re.sub(r'(автогол|Автогол|Пенальти|пенальти)', '', text)
    text = re.sub(r'\+1D', '', text)
    text = text.strip(' :;.,-')
    text = re.sub(r'\s+', ' ', text)
    ev['min'] = minute
    if yel or red:
        name, extra = split_name_paren(text)
        if 'ЖК' in name:
            name = name.replace('ЖК', '').strip()
        ev['type'] = 'rc' if red or yel >= 2 else 'yc'
        ev['p'] = name
        ev['team'] = extra
        return ev
    if missed:
        name, extra = split_name_paren(text)
        ev['type'] = 'mp'
        ev['p'] = name
        ev['team'] = extra
        return ev
    if score is not None or has_ball:
        name, assist = split_name_paren(text)
        if not re.search(r'[A-Za-zА-Яа-яӘәҒғҚқҢңӨөҰұҮүҺһІі]{2,}', name + assist):
            return None
        ev['type'] = 'og' if is_og else ('pen' if is_pen else 'goal')
        ev['p'] = name
        ev['a'] = assist
        ev['score'] = score
        return ev
    if minute is not None and re.search(r'[A-Za-zА-Яа-яӘәҒғҚқҢңӨөҰұҮүҺһІі]{2,}', text):
        name, assist = split_name_paren(text)
        ev['type'] = 'og' if is_og else ('pen' if is_pen else 'goal')
        ev['p'] = name
        ev['a'] = assist
        ev['score'] = None
        ev['unscored'] = True
        return ev
    return None


def header_match(line):
    s = clean(line)
    if not s or re.match(r'^\d', s) or CARD_OR_GOAL.search(line):
        return None
    m = H1.match(s)
    if m:
        h, a = m.group('h').strip(), (m.group('a') or '').strip()
        tail = (m.group('tail') or '').strip()
        if a.upper().rstrip('!') in ('FT', 'LIVE'):
            tail, a = a, ''
        if not a:
            parts = re.split(r'\s+[-–]\s+|\s+vs\s+', h, flags=re.I)
            if len(parts) == 2:
                h, a = parts
            else:
                return None
        h = re.sub(r'\s*\(\s*\d+\s*(tour|тур)\s*\)\s*$', '', h, flags=re.I)
        return {'home': h.strip(' -:'), 'away': a.strip(' -:'), 'score': [int(m.group('hs')), int(m.group('as'))], 'tail': tail, 'line': s}
    return None


def header_noscore(line):
    s = clean(line)
    if not s or re.match(r'^\d', s) or CARD_OR_GOAL.search(line):
        return None
    m = H2.match(s)
    if m:
        return {'home': m.group('h').strip(), 'away': m.group('a').strip(), 'score': None, 'tail': (m.group('tail') or ''), 'line': s}
    return None


def assign_sides(events, final):
    """Use running scores to decide scoring side for each goal-like event."""
    h = a = 0
    goals = [e for e in events if e['type'] in ('goal', 'pen', 'og')]
    issues = []
    for i, e in enumerate(goals):
        sc = e.get('score')
        side = None
        if sc:
            if sc == (h + 1, a):
                side = 'h'
            elif sc == (h, a + 1):
                side = 'a'
            elif sc[0] > h and sc[1] <= a:
                side = 'h'
            elif sc[1] > a and sc[0] <= h:
                side = 'a'
            elif sc[0] - h > sc[1] - a:
                side = 'h'
            elif sc[1] - a > sc[0] - h:
                side = 'a'
        else:
            # look ahead to next scored goal
            nxt = next((g for g in goals[i + 1:] if g.get('score')), None)
            if nxt:
                k = goals.index(nxt) - i + 1  # number of goals up to and including nxt
                dh, da = nxt['score'][0] - h, nxt['score'][1] - a
                if dh + da == k:
                    # unknown distribution of earlier unscored goals: assume this one belongs where needed
                    side = 'h' if dh > 0 and (da == 0 or dh >= da) else 'a'
            elif final:
                dh, da = final[0] - h, final[1] - a
                if dh > 0 and da <= 0:
                    side = 'h'
                elif da > 0 and dh <= 0:
                    side = 'a'
        if side is None:
            issues.append(f"side? {e['raw']}")
        e['side'] = side
        if side == 'h':
            h += 1
        elif side == 'a':
            a += 1
    return (h, a), issues


def looks_event(line):
    ev = parse_event(line)
    if not ev:
        return False
    return ev.get('min') is not None or bool(re.search('⚽|⚠|🟨|🟥|ЖК|КК', line))


def parse_post(msg):
    lines = []
    for l in msg['text'].split('\n'):
        if lines and l.strip().startswith('(') and lines[-1].strip() and not TRAIL_SCORE.search(lines[-1]):
            lines[-1] = lines[-1] + ' ' + l.strip()
        else:
            lines.append(l)
    out = []
    pre = []
    i = 0
    cur = None
    in_shootout = False
    while i < len(lines):
        ln = lines[i]
        hm = header_match(ln)
        if hm is None and cur is None:
            nxt = next((l for l in lines[i + 1:] if l.strip()), '')
            if header_noscore(ln) and (looks_event(nxt) or SECTION.match(clean(nxt))):
                hm = header_noscore(ln)
        if hm:
            cur = dict(hm, pre=list(pre), events=[], shootout=[], notes=[])
            out.append(cur)
            in_shootout = False
            i += 1
            continue
        if cur is None:
            if ln.strip():
                pre.append(clean(ln))
            i += 1
            continue
        if re.search(r'серия\s+пенальти', ln, re.I):
            in_shootout = True
            i += 1
            continue
        if in_shootout:
            if ln.strip():
                cur['shootout'].append(ln.strip())
            i += 1
            continue
        if re.search(r'тех', ln, re.I) and re.search(r'пораж|поб', ln, re.I):
            cur['notes'].append(clean(ln))
            cur['technical'] = True
            i += 1
            continue
        ev = parse_event(ln)
        if ev:
            cur['events'].append(ev)
        elif ln.strip() and not SECTION.match(clean(ln)):
            cur['notes'].append(clean(ln))
        i += 1
    return out


def main():
    msgs = json.load(open(sys.argv[1]))
    allm = []
    for msg in msgs:
        if not msg['text']:
            continue
        dt = parse_date(msg['date'])
        for k, m in enumerate(parse_post(msg)):
            m['msg'] = msg['id']
            m['n'] = k
            m['dt'] = dt.isoformat()
            final = m['score']
            (gh, ga), issues = assign_sides(m['events'], final)
            m['computed'] = [gh, ga]
            m['issues'] = issues
            for e in m['events']:
                if 'score' in e and e['score']:
                    e['score'] = list(e['score'])
            if m['shootout']:
                sc = None
                for l in m['shootout']:
                    mm = re.search(r'(\d)\s*-\s*(\d)', l)
                    if mm:
                        sc = [int(mm.group(1)), int(mm.group(2))]
                m['pens'] = sc
            allm.append(m)
    json.dump(allm, open(sys.argv[2], 'w'), ensure_ascii=False, indent=1)
    print('matches', len(allm))


if __name__ == '__main__':
    main()
