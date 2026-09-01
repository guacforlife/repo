#!/usr/bin/env python3
"""Regenerate index.html's package list from the Packages index.

The list used to be hand-written, and drifted: it advertised one tweak while
the repo served seven. Generating it from Packages means the page cannot
disagree with what Sileo actually installs.
"""
import html, io, re, sys

ARCH = {'iphoneos-arm64': 'rootless', 'iphoneos-arm': 'rootful'}
# Depends every tweak has; not worth showing as a requirement.
BORING = {'mobilesubstrate', 'preferenceloader', 'firmware'}


def records(path='Packages'):
    out = []
    for chunk in io.open(path, encoding='utf-8').read().split('\n\n'):
        if not chunk.strip():
            continue
        f = {}
        key = None
        for line in chunk.split('\n'):
            if line.startswith(' ') and key:      # folded continuation
                f[key] += ' ' + line.strip()
            elif ':' in line:
                key, _, val = line.partition(':')
                f[key] = val.strip()
        if f.get('Package'):
            out.append(f)
    return out


def merge(recs):
    """One entry per package, collecting the architectures it ships."""
    by = {}
    for r in recs:
        pkg = r['Package']
        if pkg in by:
            by[pkg]['_arch'].add(r.get('Architecture', ''))
        else:
            r['_arch'] = {r.get('Architecture', '')}
            by[pkg] = r
    return [by[k] for k in sorted(by, key=lambda k: by[k].get('Name', k).lower())]


def requires(dep_field):
    deps = [d.split('(')[0].strip() for d in dep_field.split(',') if d.strip()]
    return [d for d in deps if d and d.lower() not in BORING]


def render(r):
    name = r.get('Name') or r['Package']
    e = html.escape
    flavours = ' + '.join(sorted({ARCH.get(a, a) for a in r['_arch'] if a}))
    bits = ['v' + e(r.get('Version', '?'))]
    if flavours:
        bits.append(e(flavours))
    req = requires(r.get('Depends', ''))
    if req:
        bits.append('requires ' + e(', '.join(req)))
    meta = ' &nbsp;·&nbsp; '.join(bits)
    # Description's first sentence keeps the card readable; the rest is in Sileo.
    desc = r.get('Description', '').strip()
    return f'''            <div class="pkg">
                <div class="pkg-name">{e(name)}</div>
                <div class="pkg-version">{meta}</div>
                <div class="pkg-desc">{e(desc)}</div>
                <a class="pkg-source" href="https://github.com/guacforlife/{e(name)}">Source →</a>
            </div>'''


def main():
    entries = merge(records())
    body = '\n'.join(render(r) for r in entries)
    page = io.open('index.html', encoding='utf-8').read()
    pat = re.compile(r'(<!-- PACKAGES:BEGIN.*?-->\n).*?(\s*<!-- PACKAGES:END -->)', re.S)
    if not pat.search(page):
        sys.exit('index.html is missing its PACKAGES:BEGIN/END markers')
    page = pat.sub(lambda m: m.group(1) + body + '\n' + m.group(2).lstrip('\n'), page)
    io.open('index.html', 'w', encoding='utf-8').write(page)
    print(f'index.html: listed {len(entries)} packages')


if __name__ == '__main__':
    main()
