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
    if ev["status"] == "upcoming" and ev.get("register"): btns.append(f'<a class="btn" href="/{ev["slug"]}register/">Register</a>')
    if ev.get("page"): btns.append(f'<a class="btn alt" href="/{ev["slug"]}/">Find out more</a>')
    elif ev.get("programme"): btns.append(f'<a class="btn alt" href="/{ev["slug"]}programme/">View the programme</a>')
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

def page(ev):
    p = ev["page"]; slug = ev["slug"]
    li = lambda a: "".join(a)
    topics = "".join(f'<div class="tile"><h3>{e(t)}</h3><p>{e(d)}</p></div>' for t, d in p["topics"])
    orgs = "".join(f'<div class="person"><div class="pn">{e(n)}</div><div class="pr">{e(r)}</div></div>' for n, r in p["organisers"])
    rows = ""
    for r in p["programme"]:
        sp = f'<div class="sp">{e(r["speakers"])}</div>' if r.get("speakers") else ""
        cls = ' class="brk"' if r.get("break") else ""
        rows += f'<tr{cls}><td class="tm">{e(r["time"])}</td><td><div class="st">{e(r["title"])}</div>{sp}</td></tr>'
    fac = "".join(f'<div class="person"><div class="pn">{e(n)}</div><div class="pr">{e(r)}</div></div>' for n, r in p["faculty"])
    fees = "".join(f'<tr><td>{e(a)}</td><td class="fee">{e(b)}</td></tr>' for a, b in p["fees"])
    intro = "".join(f"<p>{e(x)}</p>" for x in p["intro"])
    vl = " &middot; ".join(f'<a href="{e(u)}">{e(t)}</a>' for t, u in p["venue_links"])
    reg = f'<a class="btn" href="/{slug}register/">Register</a>' if ev.get("register") else ""
    prog = f'<a class="btn alt" href="/{slug}programme/">Programme (PDF)</a>' if ev.get("programme") else ""
    cal = f'<a class="btn alt" href="/{slug}calendar/">Add to calendar</a>' if ev.get("calendar") else ""
    spons = ""
    if p.get("sponsors"):
        imgs = "".join(f'<div class="lg"><img src="{e(s["logo"])}" alt="{e(s["name"])}"></div>' for s in p["sponsors"])
        spons = f'<section><h2>With thanks to our sponsors</h2><div class="logos">{imgs}</div></section>'
    tpl = open(os.path.join(root, "event.template.html")).read()
    vals = dict(TITLE=e(ev["title"]), DATE=e(ev["date"]), VENUE=e(ev["venue"]), TIMES=e(p["times"]), TAGLINE=e(p["tagline"]),
        LOGO=e(ev["logo"]), INTRO=intro, TOPICS=topics, ORGS=orgs, ROWS=rows, FACULTY=fac, FEES=fees, FEESNOTE=e(p["fees_note"]),
        VENUELINKS=vl, REG=reg, PROG=prog, CAL=cal, SPONSORS=spons)
    for k, v in vals.items(): tpl = tpl.replace("{{"+k+"}}", v)
    os.makedirs(os.path.join(root, slug), exist_ok=True)
    open(os.path.join(root, slug, "index.html"), "w").write(tpl)

for ev in data["events"]:
    if ev.get("page"): page(ev)

def block(title, evs):
    if not evs: return ""
    return f'  <h2 class="section-title">{title}</h2>\n' + "\n".join(card(x) for x in evs) + "\n"

up = [x for x in data["events"] if x["status"] == "upcoming"]
past = [x for x in data["events"] if x["status"] != "upcoming"]
tpl = open(os.path.join(root, "index.template.html")).read()
open(os.path.join(root, "index.html"), "w").write(
    tpl.replace("<!--EVENTS-->", block("Upcoming meetings", up) + block("Past meetings", past)))
print("Built", len(data["events"]), "event(s)")
