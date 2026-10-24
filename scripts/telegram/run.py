#!/usr/bin/env python3
"""Пересобрать data/league.js из экспорта Telegram-канала.

    python3 scripts/telegram/run.py путь/к/messages.html [data/league.js]

Экспорт: Telegram Desktop → канал → ⋮ → Export chat history → формат HTML
(медиа можно не выгружать). Если экспорт разбит на messages.html, messages2.html …,
передайте все файлы — они будут склеены по порядку.
"""
import json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    if not args:
        print(__doc__)
        sys.exit(1)
    htmls = [a for a in args if a.endswith('.html')]
    out = next((a for a in args if a.endswith('.js')), os.path.join(ROOT, 'data', 'league.js'))
    py = [sys.executable, '-I']
    with tempfile.TemporaryDirectory() as tmp:
        msgs = []
        for i, h in enumerate(htmls):
            part = os.path.join(tmp, f'msgs{i}.json')
            subprocess.run(py + [os.path.join(HERE, 'extract.py'), h, part, os.path.join(tmp, f'msgs{i}.txt')], check=True)
            msgs += json.load(open(part))
        allm = os.path.join(tmp, 'msgs.json')
        json.dump(msgs, open(allm, 'w'), ensure_ascii=False)
        raw = os.path.join(tmp, 'raw_matches.json')
        subprocess.run(py + [os.path.join(HERE, 'parse.py'), allm, raw], check=True)
        subprocess.run(py + [os.path.join(HERE, 'build.py'), raw, allm, out] + [a for a in sys.argv[1:] if a == '-v'], check=True)


if __name__ == '__main__':
    main()
