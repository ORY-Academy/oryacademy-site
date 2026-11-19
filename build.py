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
FORM = site["join_form"].rsplit("/", 1)[-1]

def signup(heading, text):
    return f'''<section class="invite signup on-navy" id="join"><div class="in">
  <div class="pitch">
    <h2>{heading}</h2>
    <p>{text}</p>
  </div>
  <div class="formbox">
    <iframe data-tally-src="https://tally.so/embed/{FORM}?alignLeft=1&hideTitle=1&transparentBackground=1&dynamicHeight=1" loading="lazy" width="100%" height="480" frameborder="0" marginheight="0" marginwidth="0" title="Join the ORY Academy mailing list"></iframe>
    <p class="fallback">If the form does not appear, <a href="{site["join_form"]}" target="_blank" rel="noopener">open the sign-up form in a new tab</a>.</p>
  </div>
</div></section>
<script async src="https://tally.so/widgets/embed.js"></script>'''

import hashlib
CSSV = hashlib.md5(open(os.path.join(root, "site.css"), "rb").read()).hexdigest()[:8]
JSV = hashlib.md5(open(os.path.join(root, "site.js"), "rb").read()).hexdigest()[:8]

# Links that leave the site open in a new tab: full web addresses on other sites, and the
# short links (/join/, /mrm2register/ and so on) that forward to Tally, Drive or a calendar file.
import re
SHORT = {site["join"].strip("/")}
for _ev in data["events"]:
    SHORT.update(_ev["slug"] + s for s in ("register", "programme", "calendar"))
NEWTAB = re.compile(r'<a\b([^>]*?)href="([^"]+)"([^>]*)>')
def newtab(m):
    pre, url, post = m.groups()
    attrs = pre + post
    out = url.startswith(("http://", "https://")) and not re.match(r"https?://(www\.)?oryacademy\.com(/|$)", url)
    out = out or url.strip("/") in SHORT
    if not out or "target=" in attrs:
        return m.group(0)
    attrs = re.sub(r'\s*rel="[^"]*"', "", attrs)
    pre2 = re.sub(r'\s*rel="[^"]*"', "", pre); post2 = re.sub(r'\s*rel="[^"]*"', "", post)
    return f'<a{pre2}href="{url}"{post2} target="_blank" rel="noopener">'

def write(path, text):
    # The version on the stylesheet link makes phones fetch the new styles straight after a change.
    text = text.replace('href="/site.css"', f'href="/site.css?v={CSSV}"').replace('src="/site.js"', f'src="/site.js?v={JSV}"')
    if 'http-equiv="refresh"' not in text:  # the forwarding pages themselves stay in the same tab
        text = NEWTAB.sub(newtab, text)
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
             '<li><a href="/#join">Join the mailing list</a></li>']
    if site.get("linkedin"): links.append(f'<li>{linkedin(site["linkedin"], "ORY Academy on LinkedIn")}</li>')
    links.append('<li><a href="/">All meetings</a></li>')
    links.append('<li><a href="/privacy/">Privacy notice</a></li>')
    links.append('<li><a href="/privacy/#cookies" data-cookie-settings>Cookie settings</a></li>')
    return f'''<footer class="foot"><div class="in">
  <div class="sig">
    <img src="/ory-logo.svg" alt="ORY Academy logo" width="84" height="84">
    <p class="line"><span>Learning from experience,</span><span>Teaching with purpose.</span></p>
  </div>
  <ul>{"".join(links)}</ul>
  <p class="legal">ORY Academy CIC is a community interest company registered in England and Wales. Company number 17488094.</p>
</div></footer>
<div class="cookie-bar" id="cookieBar" role="region" aria-label="Cookies" hidden>
  <p>This site uses only the cookies it needs to work. With your permission it may also use analytics cookies to see how it is used. See the <a href="/privacy/#cookies">privacy notice</a>.</p>
  <div class="cookie-actions">
    <button type="button" class="cookie-btn cookie-accept" data-choice="accepted">Accept</button>
    <button type="button" class="cookie-btn cookie-decline" data-choice="declined">Decline</button>
  </div>
</div>
<script src="/site.js"></script>'''

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
    fb = ""
    if p.get("feedback"):
        f = p["feedback"]
        stats = "".join(f'<div class="stat"><div class="fig">{e(a)}</div><div class="lab">{e(l)}</div></div>' for a, l in f["stats"])
        quotes = "".join(f'<blockquote><p>{e(q)}</p></blockquote>' for q in f.get("quotes", []))
        fb = f'<section id="feedback"><h2>What delegates said</h2><hr class="rule"><div class="stats">{stats}</div><div class="quotes">{quotes}</div><p class="note">{e(f["note"])}</p></section>'
        nav = nav.replace('<a href="#programme">', '<a href="#feedback">Feedback</a><a href="#programme">')
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
        ctasec = signup('Hear about the next meeting', 'Join the mailing list and we will email you when registration opens for future ORY Academy meetings and courses. We only email about ORY Academy meetings and courses, and you can unsubscribe at any time.')
        hero = prog + '<a class="btn gold" href="#join">Hear about the next meeting</a>'
    else:
        took = ""
        ctasec = f'<section class="invite on-navy"><div class="in"><div><h2>Join us on {e(ev["date"])}</h2><p>{e(ev["venue"])}</p></div>{reg}</div></section>'
        hero = reg + prog + cal
    tpl = open(os.path.join(root, "event.template.html"), encoding="utf-8").read()
    vals = dict(TITLE=e(ev["title"]), DATE=e(ev["date"]), VENUE=e(ev["venue"]), TIMES=e(p["times"]), TAGLINE=e(p["tagline"]),
        LOGO=e(ev.get("logo_large") or ev["logo"]), INTRO=intro, TOPICS=topics, TOPICSH="What the meeting covered" if past else "What the meeting will cover",
        ORGS=orgs, ROWS=rows, FACULTY=fac, FEESSECTION=fees, VENUELINKS=vl, NAV=nav, TOOK=took, HEROBTNS=hero,
        CTASECTION=ctasec, SPONSORS=spons, POSTS=posts, FEEDBACK=fb, FOOTER=footer())
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
    events += f'  <div class="empty"><p>No meetings are open for registration at the moment. Join the mailing list and we will email you when the next one opens.</p><a class="btn" href="#join">Join the mailing list</a></div>\n'
if past:
    events += '  <h2 style="margin-top:56px">Past meetings</h2>\n  <hr class="rule">\n  <ul class="meetings">\n' + "\n".join(row(x) for x in past) + "\n  </ul>\n"

tpl = open(os.path.join(root, "index.template.html"), encoding="utf-8").read()
vals = dict(JOIN=JOIN, SIGNUP=signup('Hear about the next meeting', 'Join the mailing list and we will email you when registration opens. We only email about ORY Academy meetings and courses, and you can unsubscribe at any time.'), ABOUT="".join(f"<p>{e(x)}</p>" for x in site["about"]),
            DIRECTORS="".join(person(d) for d in site["directors"]), FOOTER=footer())
for k, v in vals.items(): tpl = tpl.replace("{{"+k+"}}", v)
write("index.html", tpl.replace("<!--EVENTS-->", events))

PRIVACY = """<p>ORY Academy CIC organises meetings and courses for clinicians. This notice explains what personal information we collect through this website and our sign-up and registration forms, and how we use it.</p>
<h2>Who we are</h2>
<p>ORY Academy CIC is a community interest company registered in England and Wales, company number 17488094. Our registered office is Suite 10, Capital House, 61 Amhurst Road, London E8 1LL. We decide how the information described here is used. You can contact us at <a href="mailto:EMAIL">EMAIL</a>.</p>
<h2>What this website collects</h2>
<p>This website does not ask you to create an account and does not collect personal information itself. We do not use advertising or tracking cookies. If we add analytics in future, they will load only after you choose Accept.</p>
<h2>Forms and emails</h2>
<p><strong>Mailing list.</strong> If you join our mailing list we collect your name and email address, and your consent. We use them to tell you about future ORY Academy meetings and courses, and we send a confirmation by email. Every email contains an unsubscribe link, and you can leave at any time.</p>
<p><strong>Registration, feedback and certificates.</strong> If you register for a meeting or course, we collect the details you enter, such as your name, role, workplace, email address, dietary requirements and the details needed to take payment (we do not collect card numbers on this website). We use them to run the meeting, to take payment, to keep a record of attendance, to ask for your feedback and to issue certificates. The feedback form asks whether we may share your email address with the meeting&rsquo;s sponsors, and we share it only if you say yes. Sponsors receive the names, roles and workplaces of people who attended, but not their contact details unless you agreed.</p>
<p>We rely on your consent for the mailing list, and on our legitimate interest in running the meetings you register for, and on the need to take payment, for registrations.</p>
<h2>Services this website relies on</h2>
<p>Our forms are provided by Tally, which stores what you submit on our behalf. Our emails are sent using Resend. This website is hosted on GitHub Pages, and its fonts are supplied by Google Fonts. Programmes and calendar files may open from Google Drive. These services may record technical information, such as your IP address, when their content loads or when you follow a link to them.</p>
<h2 id="cookies">Cookies</h2>
<p>This website sets only the cookies and similar storage it needs to work, plus a note of your cookie choice on your own device. Declining does not affect how you use the site. Forms and other content supplied by Tally, Google and others may set their own cookies when they load. You can change your choice at any time with Cookie settings in the footer.</p>
<h2>How long we keep information</h2>
<p>We keep mailing list details until you unsubscribe. We keep registration and attendance records for as long as we need them to run our meetings, to issue certificates and to meet our accounting duties.</p>
<h2>Your rights</h2>
<p>You can ask to see, correct or delete the information we hold about you, or to object to how we use it, by emailing <a href="mailto:EMAIL">EMAIL</a>. If you are unhappy with how your information has been handled you can complain to the Information Commissioner&rsquo;s Office at <a href="https://ico.org.uk">ico.org.uk</a>.</p>""".replace("EMAIL", site["email"])
write("privacy/index.html", f'''<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Privacy notice | ORY Academy</title>
<meta name="description" content="How ORY Academy CIC uses personal information collected through this website and its forms.">
<link rel="icon" type="image/svg+xml" href="/ory-logo.svg">
<link rel="alternate icon" type="image/png" href="/ory-logo.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600&family=Source+Serif+4:ital,opsz,wght@0,8..60,600;1,8..60,500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/site.css">
</head>
<body>
<div class="top"><div class="in"><a class="brand" href="/"><img src="/ory-logo.svg" alt="" width="44" height="44">ORY Academy</a></div></div>
<section class="band"><div class="in prose">
  <h1 style="font-size:38px;margin-bottom:18px">Privacy notice</h1>
  <hr class="rule">
  {PRIVACY}
</div></section>
{footer()}
</body>
</html>
''')
known.append("/privacy")

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
  <div class="btns"><a class="btn" href="/">Go to the home page</a><a class="btn alt" href="/#join">Join the mailing list</a></div>
</div></section>
{footer()}
</body>
</html>
''')
print("Built", len(data["events"]), "event(s)")
