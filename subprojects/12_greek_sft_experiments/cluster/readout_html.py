#!/usr/bin/env python3
"""Render results/READOUT_provisional.md (headers, paragraphs, pipe tables, bullet lists, links) as a content-only HTML
page for the Artifact tool. Usage: readout_html.py <in.md> <out.html> [title]"""
import sys, re, html
src, out = sys.argv[1], sys.argv[2]; title = sys.argv[3] if len(sys.argv) > 3 else 'Round One Readout'
lines = open(src, encoding='utf-8').read().split('\n')
def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t)
    t = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', t)
    t = re.sub(r'(https?://[^\s)]+)', r'<a href="\1">\1</a>', t)
    return t
body = []; i = 0; para = []
def flush():
    global para
    if para: body.append('<p>' + inline(' '.join(para)) + '</p>'); para = []
while i < len(lines):
    l = lines[i]
    if l.startswith('|') and i + 1 < len(lines) and re.match(r'^\|[-:| ]+\|$', lines[i + 1].strip()):
        flush(); hdr = [c.strip() for c in l.strip().strip('|').split('|')]; i += 2; rows = []
        while i < len(lines) and lines[i].startswith('|'):
            rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')]); i += 1
        body.append('<div class="tw"><table><thead><tr>' + ''.join(f'<th>{inline(c)}</th>' for c in hdr) + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in r) + '</tr>' for r in rows) + '</tbody></table></div>'); continue
    m = re.match(r'^(#{1,3})\s+(.*)', l)
    if m: flush(); body.append(f'<h{len(m.group(1))}>{inline(m.group(2))}</h{len(m.group(1))}>'); i += 1; continue
    if re.match(r'^\s*[-*]\s+', l):
        flush(); items = []
        while i < len(lines) and re.match(r'^\s*[-*]\s+', lines[i]): items.append(re.sub(r'^\s*[-*]\s+', '', lines[i])); i += 1
        body.append('<ul>' + ''.join(f'<li>{inline(x)}</li>' for x in items) + '</ul>'); continue
    if re.match(r'^\s*\d+\.\s+', l):
        flush(); items = []
        while i < len(lines) and re.match(r'^\s*\d+\.\s+', lines[i]): items.append(re.sub(r'^\s*\d+\.\s+', '', lines[i])); i += 1
        body.append('<ol>' + ''.join(f'<li>{inline(x)}</li>' for x in items) + '</ol>'); continue
    if not l.strip(): flush(); i += 1; continue
    para.append(l.strip()); i += 1
flush()
css = '''<style>
:root{--bg:#f5f3ee;--paper:#fffdf9;--ink:#1e1c18;--muted:#5e5a51;--rule:#d9d3c6;--accent:#1f5f7a;--band:#e9eef0;
--sans:"IBM Plex Sans",-apple-system,Segoe UI,Helvetica,Arial,sans-serif;--serif:"Source Serif 4",Georgia,serif;--mono:"IBM Plex Mono",ui-monospace,Menlo,monospace}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#15171a;--paper:#1d2024;--ink:#e8e4da;--muted:#a49d90;--rule:#3a3f46;--accent:#7fb8d1;--band:#242a30}}
:root[data-theme="dark"]{--bg:#15171a;--paper:#1d2024;--ink:#e8e4da;--muted:#a49d90;--rule:#3a3f46;--accent:#7fb8d1;--band:#242a30}
body{background:var(--bg);color:var(--ink);font-family:var(--sans);font-size:15px;line-height:1.55;margin:0}
main{max-width:1060px;margin:0 auto;padding:36px 26px 64px}
h1{font-family:var(--serif);font-size:34px;line-height:1.15;margin:0 0 6px;text-wrap:balance}
h2{font-family:var(--serif);font-size:23px;margin:38px 0 10px;text-wrap:balance;border-bottom:1px solid var(--rule);padding-bottom:6px}
h3{font-size:15px;margin:22px 0 6px}
p{max-width:76ch} li{max-width:76ch;margin:4px 0}
code{font-family:var(--mono);font-size:13px;background:var(--band);padding:1px 5px;border-radius:3px}
a{color:var(--accent)}
.tw{overflow-x:auto;background:var(--paper);border:1px solid var(--rule);margin:12px 0}
table{border-collapse:collapse;width:100%;font-size:13.5px;font-variant-numeric:tabular-nums}
th{background:var(--band);text-align:left;padding:7px 10px;font-weight:600;border-bottom:1px solid var(--rule);white-space:nowrap}
td{padding:6px 10px;border-bottom:1px solid var(--rule);vertical-align:top}
tr:last-child td{border-bottom:none}
.eyebrow{font-family:var(--mono);font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin-bottom:8px}
</style>'''
fonts = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">'
html_out = f'<title>{html.escape(title)}</title>\n{fonts}\n{css}\n<main>\n<div class="eyebrow">train-apertus-with-glossapi · subproject 12 · autonomous run 2026-09-04</div>\n' + '\n'.join(body) + '\n</main>'
open(out, 'w', encoding='utf-8').write(html_out.replace('�', '&#xFFFD;')); print('wrote', out, len(html_out), 'chars')
