"""Шаг 1: messages.html (экспорт Telegram Desktop) -> msgs.json + msgs.txt."""
import sys, json, re
from html.parser import HTMLParser

class P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.msgs = []; self.cur = None; self.depth = 0; self.text_depth = None; self.in_date = False
        self.media = None
    def handle_starttag(self, tag, attrs):
        a = dict(attrs); cls = (a.get('class') or '').split()
        if tag == 'div':
            self.depth += 1
            if 'message' in cls and 'default' in cls:
                self.cur = {'id': a.get('id', ''), 'date': None, 'text': '', 'media': [], 'joined': 'joined' in cls}
                self.msgs.append(self.cur)
            elif self.cur is not None and 'date' in cls and 'details' in cls and a.get('title'):
                self.cur['date'] = a['title']
            elif self.cur is not None and 'text' in cls and self.text_depth is None:
                self.text_depth = self.depth
        elif tag == 'br' and self.text_depth is not None:
            self.cur['text'] += '\n'
        elif tag in ('a', 'img') and self.cur is not None:
            h = a.get('href') or a.get('src')
            if h and ('photos/' in h or 'video' in h or 'files/' in h): self.cur['media'].append(h)
    def handle_endtag(self, tag):
        if tag == 'div':
            if self.text_depth is not None and self.depth == self.text_depth: self.text_depth = None
            self.depth -= 1
    def handle_data(self, d):
        if self.text_depth is not None: self.cur['text'] += d

p = P(); p.feed(open(sys.argv[1], encoding='utf-8').read())
out = []
last_date = None
for m in p.msgs:
    if m['date']: last_date = m['date']
    m['date'] = m['date'] or last_date
    m['text'] = re.sub(r'[ \t]+\n', '\n', m['text']).strip()
    out.append(m)
json.dump(out, open(sys.argv[2], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
with open(sys.argv[3], 'w', encoding='utf-8') as f:
    for m in out:
        if not m['text']: continue
        f.write(f"=== {m['id']} | {m['date']}\n{m['text']}\n\n")
print(len(out), 'messages;', sum(1 for m in out if m['text']), 'with text')
