#!/usr/bin/env python3
"""Rebuilds the ORY Academy website from events.json.

Run:  python3 build.py

events.json holds two things:
  "site"   - the mailing list link, About text, directors and LinkedIn links.
             Leave a "linkedin" value empty to hide that link.
  "events" - one entry per meeting. "posts" in a page lists "Read about the day" links.
              Set "status" to "upcoming" or "past".
             Leave a link out ("register", "programme", "calendar") to hide it.

Short links are /<slug>register/, /<slug>programme/, /<slug>calendar/ and /join/.
The look of the site lives in site.css, index.template.html and event.template.html."""
import json, os, html, re
root = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(root, "events.json"), encoding="utf-8"))
site = data["site"]
e = html.escape
JOIN = site["join"]

def write(path, text):
    full = os.path.join(root, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full, "w", encoding="utf-8").write(text)

def redirect(path, title, url, msg):
    write(os.path.join(path, "index.html"), f'''<!doctype html>
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

def linkedin(url, label):
    return f'<a href="{e(url)}" rel="noopener">{e(label)}</a>' if url else ""

def person(p):
    li = linkedin(p.get("linkedin"), "LinkedIn profile")
    li = f'<div>{li}</div>' if li else ""
    return f'<div class="person"><div class="pn">{e(p["name"])}</div><div class="pr">{e(p["role"])}</div>{li}</div>'

def footer():
    links = [f'<li><a href="mailto:{e(site["email"])}">{e(site["email"])}</a></li>',
             f'<li><a href="{JOIN}">Join the mailing list</a></li>']
    if site.get("linkedin"): links.append(f'<li>{linkedin(site["linkedin"], "ORY Academy on LinkedIn")}</li>')
    links.append('<li><a href="/">All meetings</a></li>')
    return f'''<footer class="foot"><div class="in">
  <div class="sig">
    <img src="/ory-logo.svg" alt="ORY Academy logo" width="84" height="84">
    <p class="line"><span>Learning from experience,</span><span>Teaching with purpose.</span></p>
  </div>
  <ul>{"".join(links)}</ul>
  <p class="legal">ORY Academy CIC is a community interest company registered in England and Wales. Company number 17488094.</p>
</div></footer>'''

def when(ev):
    m = re.match(r"(\w+) (\d+) (\w+ \d{4})$", ev["date"])
    if not m: return f'<div class="when"><span class="m">{e(ev["date"])}</span></div>'
    return f'<div class="when"><span class="d">{m.group(2)}</span><span class="m">{m.group(3)}<br>{m.group(1)}</span></div>'

def row(ev):
    slug = ev["slug"]; btns = []
    if ev["status"] == "upcoming" and ev.get("register"): btns.append(f'<a class="btn" href="/{slug}register/">Register</a>')
    if ev.get("page"): btns.append(f'<a class="btn alt" href="/{slug}/">{"Find out more" if ev["status"] == "upcoming" else "Programme and faculty"}</a>')
    elif ev.get("programme"): btns.append(f'<a class="btn alt" href="/{slug}programme/">View the programme</a>')
    img = f'<img src="{e(ev["logo"])}" alt="" width="76" height="76">' if ev.get("logo") else "<span></span>"
    title = f'<a href="/{slug}/">{e(ev["title"])}</a>' if ev.get("page") else e(ev["title"])
    summ = f'<p class="sum">{e(ev["page"]["tagline"])}</p>' if ev.get("page") else ""
    return f'''  <li class="meeting">
    {when(ev)}
    {img}
    <div><h3>{title}</h3><p class="where">{e(ev["venue"])}</p>{summ}</div>
    <div class="btns">{"".join(btns)}</div>
  </li>'''

labels = {"register": ("registration", "Opening the {t} registration"),
          "programme": ("programme", "Opening the {t} programme"),
          "calendar": ("calendar file", "Downloading the {t} calendar file")}
known = ["/join"]
for ev in data["events"]:
    for k, (name, msg) in labels.items():
        if ev.get(k):
            redirect(f'{ev["slug"]}{k}', f'{ev["title"]} {name}', ev[k], msg.format(t=ev["title"]))
            known.append(f'/{ev["slug"]}{k}')
    if ev.get("page"): known.append(f'/{ev["slug"]}')
if site.get("join_form"):
    redirect("join", "Join the ORY Academy mailing list", site["join_form"], "Opening the ORY Academy mailing list sign-up")

def page(ev):
    p = ev["page"]; slug = ev["slug"]; past = ev["status"] != "upcoming"
    topics = "".join(f'<div class="topic"><h3>{e(t)}</h3><p>{e(d)}</p></div>' for t, d in p["topics"])
    orgs = "".join(person({"name": n, "role": r}) for n, r in p["organisers"])
    rows = ""
    for r in p["programme"]:
        sp = f'<div class="sp">{e(r["speakers"])}</div>' if r.get("speakers") else ""
        cls = ' class="brk"' if r.get("break") else ""
        rows += f'<tr{cls}><td class="tm">{e(r["time"])}</td><td><div class="st">{e(r["title"])}</div>{sp}</td></tr>'
    fac = "".join(person({"name": n, "role": r}) for n, r in p["faculty"])
    intro = "".join(f"<p>{e(x)}</p>" for x in (p.get("past_intro") if past and p.get("past_intro") else p["intro"]))
    vl = " ".join(f'<a href="{e(u)}">{e(t)}</a>.' for t, u in p["venue_links"])
    reg = f'<a class="btn gold" href="/{slug}register/">Register</a>' if ev.get("register") and not past else ""
    prog = f'<a class="btn alt" href="/{slug}programme/">Programme (PDF)</a>' if ev.get("programme") else ""
    cal = f'<a class="btn alt" href="/{slug}calendar/">Add to calendar</a>' if ev.get("calendar") and not past else ""
    nav = '<a href="#about">About</a><a href="#programme">Programme</a><a href="#faculty">Faculty</a>'
    fees = ""
    if not past:
        nav += '<a href="#fees">Fees</a>'
        frows = "".join(f'<tr><td>{e(a)}</td><td class="fee">{e(b)}</td></tr>' for a, b in p["fees"])
        fees = f'<section id="fees" class="fees"><h2>Fees and registration</h2><table>{frows}</table><p class="note">{e(p["fees_note"])}</p><div class="btns">{reg.replace("btn gold", "btn")}</div></section>'
    nav += '<a href="#venue">Venue</a>'
    posts = ""
    if p.get("posts") and p["posts"].get("links"):
        items = "".join(f'<li><a class="btn alt" href="{e(u)}" rel="noopener">{e(t)}</a></li>' for t, u in p["posts"]["links"])
        posts = f'<section id="posts"><h2>Read about the day</h2><hr class="rule"><p class="posts-by">{e(p["posts"]["intro"])}</p><ul class="posts">{items}</ul></section>'
        nav = nav.replace('<a href="#programme">', '<a href="#posts">Read about the day</a><a href="#programme">')
    spons = ""
    if p.get("sponsors"):
        imgs = "".join(f'<div class="lg"><img src="{e(s["logo"])}" alt="{e(s["name"])}"></div>' for s in p["sponsors"])
        spons = f'<section><h2>With thanks to our sponsors</h2><div class="logos">{imgs}</div></section>'
    if past:
        took = '<p class="took">This meeting has taken place</p>'
        cta = f'<div><h2>Hear about the next meeting</h2><p>Join the mailing list and we will email you when registration opens for future ORY Academy meetings and courses.</p></div><a class="btn gold" href="{JOIN}">Join the mailing list</a>'
        hero = prog + f'<a class="btn gold" href="{JOIN}">Hear about the next meeting</a>'
    else:
        took = ""
        cta = f'<div><h2>Join us on {e(ev["date"])}</h2><p>{e(ev["venue"])}</p></div>{reg}'
        hero = reg + prog + cal
    tpl = open(os.path.join(root, "event.template.html"), encoding="utf-8").read()
    vals = dict(TITLE=e(ev["title"]), DATE=e(ev["date"]), VENUE=e(ev["venue"]), TIMES=e(p["times"]), TAGLINE=e(p["tagline"]),
        LOGO=e(ev["logo"]), INTRO=intro, TOPICS=topics, TOPICSH="What the meeting covered" if past else "What the meeting will cover",
        ORGS=orgs, ROWS=rows, FACULTY=fac, FEESSECTION=fees, VENUELINKS=vl, NAV=nav, TOOK=took, HEROBTNS=hero, CTA=cta,
        SPONSORS=spons, POSTS=posts, FOOTER=footer())
    for k, v in vals.items(): tpl = tpl.replace("{{"+k+"}}", v)
    write(os.path.join(slug, "index.html"), tpl)

for ev in data["events"]:
    if ev.get("page"): page(ev)

up = [x for x in data["events"] if x["status"] == "upcoming"]
past = [x for x in data["events"] if x["status"] != "upcoming"]
events = '  <h2>Upcoming meetings</h2>\n  <hr class="rule">\n'
if up:
    events += '  <ul class="meetings">\n' + "\n".join(row(x) for x in up) + "\n  </ul>\n"
else:
    events += f'  <div class="empty"><p>No meetings are open for registration at the moment. Join the mailing list and we will email you when the next one opens.</p><a class="btn" href="{JOIN}">Join the mailing list</a></div>\n'
if past:
    events += '  <h2 style="margin-top:56px">Past meetings</h2>\n  <hr class="rule">\n  <ul class="meetings">\n' + "\n".join(row(x) for x in past) + "\n  </ul>\n"

tpl = open(os.path.join(root, "index.template.html"), encoding="utf-8").read()
vals = dict(JOIN=JOIN, ABOUT="".join(f"<p>{e(x)}</p>" for x in site["about"]),
            DIRECTORS="".join(person(d) for d in site["directors"]), FOOTER=footer())
for k, v in vals.items(): tpl = tpl.replace("{{"+k+"}}", v)
write("index.html", tpl.replace("<!--EVENTS-->", events))

write("404.html", f'''<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Page not found | ORY Academy</title>
<meta name="robots" content="noindex">
<script>
  // Short links work whatever the capitals, e.g. /MRM2Programme and /mrm2programme.
  (function () {{
    var p = location.pathname.replace(/\\/+$/, "");
    var lower = p.toLowerCase();
    var known = {json.dumps(known)};
    if (p !== lower && known.indexOf(lower) !== -1) location.replace(lower + "/");
  }})();
</script>
<link rel="icon" type="image/svg+xml" href="/ory-logo.svg">
<link rel="stylesheet" href="/site.css">
</head>
<body>
<div class="top"><div class="in"><a class="brand" href="/"><img src="/ory-logo.svg" alt="" width="44" height="44">ORY Academy</a></div></div>
<section class="band"><div class="in prose">
  <h1 style="font-size:38px;margin-bottom:18px">Page not found</h1>
  <hr class="rule">
  <p>This address does not match a page on our site. Please check it, or start again from the home page.</p>
  <div class="btns"><a class="btn" href="/">Go to the home page</a><a class="btn alt" href="{JOIN}">Join the mailing list</a></div>
</div></section>
{footer()}
</body>
</html>
''')
print("Built", len(data["events"]), "event(s)")
