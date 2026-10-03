#!/usr/bin/env python3
"""Rebuilds index.html and the short link folders from events.json.
Short links are /<slug>register/, /<slug>programme/ and /<slug>calendar/.
Set status to "upcoming" or "past". Leave a link out to hide it."""
import json, os, html, re
root = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(root, "events.json")))
e = html.escape

def redirect(path, title, url, msg):
    os.makedirs(os.path.join(root, path), exist_ok=True)
    open(os.path.join(root, path, "index.html"), "w").write(f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)} | ORY Academy</title>
<meta name="robots" content="noindex">
<meta http-equiv="refresh" content="0; url={e(url)}">
<link rel="canonical" href="{e(url)}">
<script>location.replace("{url}");</script>
<style>body{{font-family:Arial,sans-serif;color:#1F3864;background:#fff;margin:0;padding:40px 16px;text-align:center}}a{{color:#1F3864}}</style>
</head>
<body>
<p>{e(msg)}&hellip;</p>
<p>If nothing happens, <a href="{e(url)}">click here</a>.</p>
</body>
</html>
''')

labels = {"register": ("registration", "Opening the {t} registration"),
          "programme": ("programme", "Opening the {t} programme"),
          "calendar": ("calendar file", "Downloading the {t} calendar file")}

def card(ev):
    btns = []
    if ev["status"] == "upcoming":
        if ev.get("register"): btns.append(f'<a class="btn" href="/{ev["slug"]}register/">Register</a>')
        if ev.get("programme"): btns.append(f'<a class="btn alt" href="/{ev["slug"]}programme/">View the programme</a>')
    else:
        if ev.get("programme"): btns.append(f'<a class="btn alt" href="/{ev["slug"]}programme/">View the programme</a>')
    img = f'<img src="{ev["logo"]}" alt="{e(ev["title"])} logo" width="88" height="88">' if ev.get("logo") else ""
    return f'''  <section class="card">
    {img}
    <div>
      <h3>{e(ev["title"])}</h3>
      <p class="meta">{e(ev["date"])} &middot; {e(ev["venue"])}</p>
      <div class="buttons">{" ".join(btns)}</div>
    </div>
  </section>'''

for ev in data["events"]:
    for k, (name, msg) in labels.items():
        if ev.get(k):
            redirect(f'{ev["slug"]}{k}', f'{ev["title"]} {name}', ev[k], msg.format(t=ev["title"]))

def block(title, evs):
    if not evs: return ""
    return f'  <h2 class="section-title">{title}</h2>\n' + "\n".join(card(x) for x in evs) + "\n"

up = [x for x in data["events"] if x["status"] == "upcoming"]
past = [x for x in data["events"] if x["status"] != "upcoming"]
tpl = open(os.path.join(root, "index.template.html")).read()
open(os.path.join(root, "index.html"), "w").write(
    tpl.replace("<!--EVENTS-->", block("Upcoming meetings", up) + block("Past meetings", past)))
print("Built", len(data["events"]), "event(s)")
