"""Responsive, static SVG projections of the public dashboard presentation."""
from __future__ import annotations

from datetime import date, timedelta
from html import escape
import math
from pathlib import Path
import textwrap

from scripts.contracts.dashboard_summary import summary_facts
from scripts.core.config import CONTRIB_EMPTY, CONTRIB_RAMP, DASHBOARD_SUMMARY_COLORS
from scripts.rendering.components import donut_gauge
from scripts.rendering.icons import render as icon
from scripts.rendering.svg_utils import lang_color, truncate

COLORS = DASHBOARD_SUMMARY_COLORS
FONT = '-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif'


def _attrs(values):
    return " ".join(f'{name.replace("_", "-")}="{escape(str(value), quote=True)}"' for name, value in values.items() if value is not None)


class Canvas:
    def __init__(self, mobile):
        self.mobile = mobile
        self.width = 360 if mobile else 840
        self.pad = 18 if mobile else 28
        self.body = 18
        self.secondary = 15 if mobile else 16
        self.parts = []

    def text(self, value, x, y, *, size=None, color="text", anchor="start", weight=400, **attrs):
        self.parts.append('<text ' + _attrs(dict(x=x, y=y, font_size=size or self.body, fill=COLORS.get(color, color),
                                               text_anchor=anchor, font_weight=weight, **attrs)) + '>' + escape(str(value or "")) + '</text>')

    def rect(self, x, y, width, height, *, fill="panel", radius=0, **attrs):
        self.parts.append('<rect ' + _attrs(dict(x=x, y=y, width=round(max(0, width), 3), height=height,
                                               rx=radius, fill=COLORS.get(fill, fill), **attrs)) + '/>')

    def line(self, x1, y1, x2, y2, **attrs):
        self.parts.append('<line ' + _attrs(dict(x1=x1, y1=y1, x2=x2, y2=y2, stroke=COLORS["line"], **attrs)) + '/>')

    def wrap(self, value, x, y, width, *, size=None, color="text", weight=400):
        size = size or self.body
        lines = textwrap.wrap(str(value or ""), max(1, int(width / (size * .62))), break_long_words=True, break_on_hyphens=False) or [""]
        for line in lines:
            self.text(line, x, y, size=size, color=color, weight=weight)
            y += size * 1.4
        return y

    def group(self, **attrs):
        self.parts.append('<g ' + _attrs(attrs) + '>')

    def end(self):
        self.parts.append('</g>')

    def heading(self, title, y, x=None):
        self.text(title, self.pad if x is None else x, y, size=22, weight=600)
        return y + 30

    def fact(self, fact, x, y, width, *, size=25, qualify=False):
        self.group(data_metric_id=fact["metric_id"])
        self.text(fact["display_value"], x, y, size=size, weight=600, data_role="value")
        y = self.wrap(fact["label"], x, y + 25, width, size=self.secondary, color="muted")
        if qualify and fact["quality"].get("qualification"):
            qualifier = "Reported · unverified" if fact["quality"].get("status") == "unknown" and fact["metric_id"].startswith("inventory.") else fact["quality"]["qualification"]
            y = self.wrap(qualifier, x, y + 1, width, size=self.secondary, color="muted")
        if fact.get("range_start"):
            y = self.wrap(fact["range_start"] + " – " + fact["range_end"], x, y, width, size=self.secondary, color="muted")
        self.end()
        return y

    def panel(self, section, title, y, body):
        self.group(data_section=section)
        index = len(self.parts)
        self.parts.append("")
        bottom = body(self.pad + 16, self.heading(title, y + 31, self.pad + 16), self.width - 2 * self.pad - 32)
        height = bottom - y + 15
        self.parts[index] = '<rect ' + _attrs(dict(x=self.pad, y=y, width=self.width - 2*self.pad, height=height, rx=13,
                                                  fill=COLORS["panel"], stroke=COLORS["line"], data_role="panel")) + '/>'
        self.end()
        return y + height + 18


def render_svg(summary, *, mobile=False, generation=None):
    c = Canvas(mobile)
    facts = summary_facts(summary)
    def fact(key):
        return facts.get(key, {"metric_id": key, "value": None, "display_value": "n/a", "label": key.rsplit(".", 1)[-1].replace("_", " "), "quality": {"qualification": "Unavailable"}})
    width, pad = c.width, c.pad
    content = width - pad * 2
    c.group(data_section="overview")
    y = c.wrap("@" + str(summary.get("username", "")), pad, 34, content, weight=600)
    y = c.wrap("Snapshot " + str(summary.get("generated_at", "")), pad, y, content, size=c.secondary, color="muted") + 10
    y = c.fact(fact("calendar.total"), pad, y + 44, content, size=50, qualify=True)
    y = c.wrap(summary.get("calendar", {}).get("window", "Calendar unavailable"), pad, y, content, size=c.secondary, color="muted") + 18
    inventory = ("inventory.public_nonfork", "inventory.private_owned", "inventory.stargazers")
    cell = (content - 24) / 3
    bottoms = [c.fact(fact(key), pad + i*(cell + 12), y + 22, cell, size=25) for i, key in enumerate(inventory)]
    y = max(bottoms) + 4
    qualifiers = list(dict.fromkeys(fact(key)["quality"].get("qualification", "") for key in inventory))
    for qualifier in qualifiers:
        if qualifier:
            y = c.wrap("Inventory · unverified", pad, y, content, size=c.secondary, color="muted")
    c.end()
    y += 12

    c.group(data_section="weekly")
    c.line(pad, y, width-pad, y)
    y = c.heading("Weekly contributions", y+30)
    weekly = summary.get("weekly") or {}
    display, model = weekly.get("display") or {}, weekly.get("model") or {}
    if display.get("available"):
        y = c.wrap(display.get("window", ""), pad, y, content, size=c.secondary, color="muted")
        left, right, top, bottom = pad+48, width-pad-8, y+14, y+144
        points = model.get("points", [])
        maximum = max((p["contributions"] for p in points), default=0)
        step = max(1, math.ceil(maximum / 3))
        ceiling = step * 3
        for i in range(4):
            yy = bottom - i / 3 * (bottom-top)
            c.line(left, yy, right, yy)
            c.text(f"{step*i:,}", left-9, yy+5, size=c.secondary, color="muted", anchor="end")
        coords = [(left+(right-left)*i/max(1,len(points)-1), bottom-p["contributions"]/ceiling*(bottom-top)) for i,p in enumerate(points)]
        if len(coords) > 1:
            c.parts.append('<polyline ' + _attrs(dict(points=" ".join(f"{x:.3f},{yy:.3f}" for x,yy in coords), fill="none", stroke=COLORS["blue"], stroke_width=2.5, data_role="weekly-line")) + '/>')
        for (x, yy), point in zip(coords, points):
            c.parts.append('<circle ' + _attrs(dict(cx=round(x,3), cy=round(yy,3), r=4, fill=COLORS["blue"], data_role="weekly-point",
                data_week_start=point["week_start"], data_week_end=point["week_end"], data_observed_start=point["observed_start"], data_observed_end=point["observed_end"],
                data_date=point["observed_start"], data_count=point["contributions"], data_value=point["contributions"], data_partial=str(point["partial"]).lower())) + '><title>' + escape(f'{point["observed_start"]} – {point["observed_end"]}: {point["contributions"]:,} contributions' + (" (partial)" if point["partial"] else "")) + '</title></circle>')
        for i in sorted({0, len(points)//2, len(points)-1}):
            if i >= 0:
                day = date.fromisoformat(points[i]["observed_start"])
                c.text(day.strftime("%b %-d"), coords[i][0], bottom+26, size=c.secondary, color="muted", anchor="start" if i==0 else "end" if i==len(points)-1 else "middle")
        y = c.wrap(display.get("qualification", ""), pad, bottom+52, content, size=c.secondary, color="muted")
    else:
        y = c.wrap("Contribution trend unavailable", pad, y, content, color="muted")
    c.end()
    y += 16

    def rhythm(x, yy, span):
        c.group(data_section="rhythm")
        yy = c.heading("Contribution Rhythm", yy, x)
        rd = (summary.get("rhythm") or {}).get("display") or {}
        if rd.get("available"):
            yy = c.wrap(rd.get("caption", ""), x, yy, span, size=c.secondary, color="muted")+7
            rows = rd.get("rows", [])
            maximum = max((row["contributions"] for row in rows), default=0) or 1
            for row in rows:
                c.group(data_weekday=row["weekday"])
                c.text(row["weekday"], x, yy+8)
                c.rect(x+46, yy-1, span-122, 7, fill="track", radius=2)
                c.rect(x+46, yy-1, (span-122)*row["contributions"]/maximum, 7, fill="blue", radius=2, data_role="weekday-bar")
                c.text(row["count_text"], x+span, yy+8, anchor="end")
                c.end()
                yy += 33
            if rd.get("qualification"):
                yy = c.wrap(rd["qualification"], x, yy+4, span, size=c.secondary, color="muted")
        else:
            yy = c.wrap("Contribution rhythm unavailable", x, yy, span, color="muted")
        c.end()
        return yy
    def languages(x, yy, span):
        c.group(data_section="languages")
        yy = c.heading("Language composition", yy, x)
        lang = summary.get("languages") or {}
        for row in lang.get("rows", []):
            c.group(data_language=row["name"])
            yy = c.wrap(row["name"], x, yy+7, span-80)
            c.text(row["display_value"], x+span, yy-25.2, anchor="end")
            c.rect(x, yy-13, span, 5, fill="track", radius=2)
            c.rect(x, yy-13, span*row["percent"]/100, 5, fill=lang_color(row["name"]), radius=2, data_role="language-bar")
            c.end()
            yy += 12
        if not lang.get("rows"):
            yy = c.wrap("Language observations unavailable", x, yy, span, color="muted")
        if lang.get("quality") not in ("exact", "ok"):
            yy = c.wrap(str(lang.get("quality", "unknown")).capitalize() + " language observation", x, yy+4, span, size=c.secondary, color="muted")
        c.end()
        return yy
    if mobile:
        y = rhythm(pad, y, content)+20
        y = languages(pad, y, content)+15
    else:
        span = (content-32)/2
        y = max(rhythm(pad,y,span), languages(pad+span+32,y,span))+15

    c.group(data_section="automation")
    c.line(pad,y,width-pad,y)
    y = c.heading("Workflow configuration", y+32)
    ad = (summary.get("automation") or {}).get("display") or {}
    combined = ad.get("combined") or {}
    inner = y-7
    idx = len(c.parts)
    c.parts.append("")
    native = ((summary.get("automation") or {}).get("model") or {}).get("combined") or {}
    adoption = native.get("adoption_pct")
    radius = 34 if mobile else 40
    ring_x = pad+16+radius
    ring_index = len(c.parts)
    c.parts.append("")
    tx = pad+(100 if mobile else 112)
    tw = width-pad-16-tx
    y = c.wrap(f'{combined.get("configured_repos", "n/a")} of {combined.get("eligible_repos", "n/a")} eligible repositories', tx,y+21,tw,weight=600)
    y = c.wrap(f'{combined.get("workflow_files", "n/a")} workflow files',tx,y+6,tw)
    public, private = ad.get("public") or {}, ad.get("private") or {}
    y = c.wrap(f'{public.get("configured_repos","n/a")}/{public.get("eligible_repos","n/a")} public · {private.get("configured_repos","n/a")}/{private.get("eligible_repos","n/a")} private',tx,y+4,tw,size=c.secondary,color="muted")
    y = c.wrap("Configuration, not run success. Profile repository excluded.",tx,y+3,tw,size=c.secondary,color="muted")
    if combined.get("status") not in ("Exact", "Ok"):
        y = c.wrap(combined.get("qualification", "Unavailable"),tx,y+3,tw,size=c.secondary,color="muted")
    y = max(y,inner+2*(radius+16)-5)
    ring_y = (inner+y+5)/2
    if type(adoption) in (int, float) and math.isfinite(adoption) and 0 <= adoption <= 100:
        c.parts[ring_index] = donut_gauge(ring_x,ring_y,value=adoption,radius=radius,stroke=6,
                                         color=COLORS["blue"],label=escape(str(combined.get("adoption", "n/a"))),label_size=18)
    else:
        c.parts[ring_index] = '<circle '+_attrs(dict(cx=ring_x,cy=ring_y,r=radius,fill="none",stroke=COLORS["track"],stroke_width=6))+'/>'
        c.text("n/a",ring_x,ring_y+6,size=18,anchor="middle",color="muted")
    c.parts[idx] = '<rect ' + _attrs(dict(x=pad,y=inner,width=content,height=y-inner+5,rx=13,fill=COLORS["panel"],stroke=COLORS["line"])) + '/>'
    c.end()
    y += 25

    def working(x, yy, span):
        rows = summary.get("working") or []
        yy = c.wrap("Recently pushed repositories · last 7 days",x,yy,span,size=c.secondary,color="muted")+8
        counter_bottom = c.fact(fact("activity.active_repos_7d"), x, yy+28, span if mobile else 126, size=30, qualify=True)
        row_x, row_w = (x,span) if mobile else (x+158,span-158)
        row_y = counter_bottom+12 if mobile else yy
        first_y = row_y
        for row in rows:
            c.group(data_role="repository-row",data_repository=row.get("name",""))
            height = 86 if mobile else 64
            c.rect(row_x,row_y,row_w,height,fill="surface",radius=13,stroke=COLORS["line"])
            left, right = row_x+16, row_x+row_w-14
            name_y, detail_y = row_y+24, row_y+47
            c.parts.append('<circle '+_attrs(dict(cx=left,cy=name_y-5,r=4.5,fill=lang_color(row.get("language"))))+'/>')
            text_x = left+13
            if row.get("is_private"):
                c.parts.append(icon("lock",text_x,name_y-13,size=14,color=COLORS["muted"]))
                text_x += 19
            name_w = right-text_x-(0 if mobile else 158)
            c.text(truncate(str(row.get("name", "")),max(1,int(name_w/(c.body*.55)))),text_x,name_y,weight=500)
            detail_w = row_w-32-(0 if mobile else 166)
            if row.get("last_commit_msg"):
                c.text(truncate(str(row["last_commit_msg"]),max(1,int(detail_w/(c.secondary*.54)))),left+13,detail_y,size=c.secondary,color="muted")
            if mobile:
                c.text(truncate(str(row.get("language") or "Language unreported"),18),left,row_y+71,size=c.secondary,color="muted")
                c.text(row.get("push_age","Push date unavailable"),right,row_y+71,size=c.secondary,color="muted",anchor="end")
            else:
                c.text(row.get("push_age","Push date unavailable"),right,name_y,size=c.secondary,color="muted",anchor="end")
                c.text(truncate(str(row.get("language") or "Language unreported"),22),right,detail_y,size=c.secondary,color="muted",anchor="end")
            c.parts.append('<title>'+escape(" · ".join(str(row.get(key) or "") for key in ("name","language","pushed_at","last_commit_msg"))+" · repository push and headline are independent observations")+'</title>')
            c.end()
            row_y += height+8
        if not rows:
            row_y = c.wrap("No repositories pushed recently",row_x,row_y+25,row_w,color="muted")
        if not mobile:
            c.line(x+138,first_y,x+138,max(row_y,counter_bottom),data_role="divider")
        return max(row_y,counter_bottom)
    y = c.panel("working","Currently Working On",y,working)

    def focus(x,yy,span):
        lanes = summary.get("focus") or {}
        lane_w = span if mobile else (span-24)/3
        start = yy
        boxes = []
        for i,(key,title) in enumerate((("now","Now"),("next","Next"),("updates","Recent Updates"))):
            xx = x if mobile else x+i*(lane_w+12)
            top = yy if mobile else start
            index=len(c.parts);c.parts.append("")
            c.text(title,xx+12,top+25,weight=600)
            c.line(xx+12,top+38,xx+lane_w-12,top+38)
            pos=top+63
            rows=lanes.get(key) or []
            if not rows:
                pos=c.wrap("No planned item supplied" if key=="next" else "No reported items",xx+12,pos,lane_w-24,size=c.secondary,color="muted")
            for row in rows:
                tx=xx+12
                if row.get("is_private"):
                    c.parts.append(icon("lock",tx,pos-13,size=14,color=COLORS["muted"]))
                    tx+=19
                title_text=str(row.get("title") or "")
                detail_text=str(row.get("detail") or "")
                c.text(truncate(title_text,max(1,int((xx+lane_w-12-tx)/(c.body*.6)))),tx,pos,size=c.body)
                c.text(truncate(detail_text,max(1,int((lane_w-24)/(c.secondary*.6)))),xx+12,pos+22,size=c.secondary,color="muted")
                c.parts.append('<title>'+escape(title_text+" · "+detail_text)+'</title>')
                pos+=52
            bottom=max(top+72+52*len(rows),top+92)
            boxes.append((index,xx,top,bottom))
            if mobile:yy=bottom+12
        last=max(box[3] for box in boxes)
        for index,xx,top,bottom in boxes:
            c.parts[index]='<rect '+_attrs(dict(x=xx,y=top,width=lane_w,height=(bottom if mobile else last)-top,rx=15,fill=COLORS["surface"],stroke=COLORS["line"]))+'/>'
        return last+8
    y = c.panel("focus","Current Focus",y,focus)

    def projects(x,yy,span):
        rows = summary.get("projects") or []
        for row in rows:
            c.group(data_role="project-row",data_repository=row.get("name",""))
            c.rect(x,yy,span,96,fill="surface",radius=16,stroke=COLORS["line"])
            name=str(row.get("name") or "")
            description=str(row.get("description") or "")
            metadata=f'{row.get("language") or "Language unreported"} · {row.get("stars", 0)} stars · {row.get("forks", 0)} forks'
            c.text(truncate(name,max(1,int((span-26)/(c.body*.6)))),x+13,yy+25,weight=500)
            c.text(truncate(description,max(1,int((span-26)/(c.secondary*.6)))),x+13,yy+49,size=c.secondary,color="muted")
            c.text(truncate(metadata,max(1,int((span-26)/(c.secondary*.55)))),x+13,yy+73,size=c.secondary,color="muted")
            c.parts.append('<title>'+escape(name+" · "+description+" · "+metadata)+'</title>')
            c.end()
            yy+=116
        return yy if rows else c.wrap("No curated projects supplied",x,yy+10,span,color="muted")
    y=c.panel("projects","Curated projects",y,projects)

    def metrics(x,yy,span):
        keys=("activity.public_commits","activity.merged_prs","activity.releases_30d","inventory.public_forks","language.count")
        cols=2 if mobile else 3
        cw=(span-(cols-1)*18)/cols
        for start in range(0,len(keys),cols):
            yy=max(c.fact(fact(key),x+i*(cw+18),yy+25,cw,qualify=True) for i,key in enumerate(keys[start:start+cols]))+18
        total=(summary.get("languages") or {}).get("total_bytes")
        return c.wrap(f'{total:,} observed language bytes' if type(total) is int else "Language bytes unavailable",x,yy,span,size=c.secondary,color="muted")
    y=c.panel("metrics","Profile facts",y,metrics)

    c.group(data_section="calendar")
    c.line(pad,y,width-pad,y)
    y=c.heading("Contribution calendar",y+32)
    calendar=summary.get("calendar") or {}
    days=calendar.get("days") or []
    if days:
        y=c.wrap(calendar.get("window", ""),pad,y,content,size=c.secondary,color="muted")+12
        start=date.fromisoformat(days[0]["date"])
        monday=start-timedelta(days=start.weekday())
        columns=(date.fromisoformat(days[-1]["date"])-monday).days//7+1
        cell, gap = 11, 3
        max_columns=max(1,int((content+gap)//(cell+gap)))
        maximum=max(row["count"] for row in days) or 1
        for first_col in range(0,columns,max_columns):
            selected_days=[row for row in days if first_col <= (date.fromisoformat(row["date"])-monday).days//7 < first_col+max_columns]
            ncols=min(max_columns,columns-first_col)
            grid_width=ncols*cell+(ncols-1)*gap
            grid_x=pad+(content-grid_width)/2
            if mobile and columns>max_columns:
                y=c.wrap(selected_days[0]["date"]+" – "+selected_days[-1]["date"],pad,y,content,size=c.secondary,color="muted")+4
            last_month,last_x="",-1000
            for row in selected_days:
                day=date.fromisoformat(row["date"])
                month=day.strftime("%b")
                col=(day-monday).days//7-first_col
                if month!=last_month:
                    last_month=month
                    label_x=min(grid_x+col*(cell+gap),grid_x+grid_width-30)
                    if label_x-last_x>=46:
                        c.text(month,label_x,y+6,size=c.secondary,color="muted")
                        last_x=label_x
            y+=19
            for row in selected_days:
                day=date.fromisoformat(row["date"])
                col=(day-monday).days//7-first_col
                ratio=row["count"]/maximum
                level=0 if row["count"]==0 else 4 if ratio>=.75 else 3 if ratio>=.5 else 2 if ratio>=.25 else 1
                color=CONTRIB_RAMP[level-1] if level else CONTRIB_EMPTY
                c.parts.append('<rect '+_attrs(dict(x=round(grid_x+col*(cell+gap),3),y=round(y+day.weekday()*(cell+gap),3),width=cell,height=cell,rx=3,fill=color,fill_opacity=1 if level else .06,data_role="calendar-cell",data_date=row["date"],data_count=row["count"]))+'><title>'+escape(f'{row["date"]}: {row["count"]:,} contributions')+'</title></rect>')
            y+=7*(cell+gap)+22
        legend_x=width-pad-119
        c.text("Less",legend_x-9,y+10,size=c.secondary,color="muted",anchor="end")
        for i in range(5):
            c.rect(legend_x+i*15,y,11,11,radius=3,fill=CONTRIB_RAMP[i-1] if i else CONTRIB_EMPTY,fill_opacity=1 if i else .06)
        c.text("More",legend_x+82,y+10,size=c.secondary,color="muted")
        y+=40
        keys=("calendar.current_streak","calendar.longest_streak","calendar.active_days")
        cw=content if mobile else (content-32)/3
        bottoms=[]
        for i,key in enumerate(keys):
            xx=pad if mobile else pad+i*(cw+16)
            yy=y if mobile else y
            yy=c.fact(fact(key),xx,yy+25,cw,qualify=True)
            if mobile:y=yy+18
            bottoms.append(yy)
        y=max(bottoms)+12
    else:
        y=c.wrap("Contribution calendar unavailable",pad,y,content,color="muted")
        for key in ("calendar.current_streak","calendar.longest_streak","calendar.active_days"):
            y=c.fact(fact(key),pad,y+30,content,qualify=True)+8
    c.end()
    height=math.ceil(y+22)
    description=" ".join(filter(None,["One generated analytics summary.",(summary.get("rhythm") or {}).get("display",{}).get("scope"),
        (summary.get("rhythm") or {}).get("display",{}).get("explanation"),(summary.get("rhythm") or {}).get("display",{}).get("coverage_summary"),
        "Repository push dates and reported headlines are independent observations. Current streak is the observed positive suffix, with the profile-date cutoff. Exact links and data are in the README text."]))
    key=str((generation or {}).get("render_key", ""))
    return ('<svg xmlns="http://www.w3.org/2000/svg" '+_attrs(dict(width=width,height=height,viewBox=f"0 0 {width} {height}",role="img",aria_labelledby="summary-title summary-description",data_render_key=key))+'>'
            '<title id="summary-title">GitHub profile analytics</title><desc id="summary-description">'+escape(description)+'</desc>'
            '<g '+_attrs(dict(font_family=FONT))+'><rect '+_attrs(dict(x=1,y=1,width=width-2,height=height-2,rx=16 if mobile else 20,fill=COLORS["surface"],stroke=COLORS["line"]))+'/>'
            +''.join(c.parts)+'</g></svg>')


def generate(summary, *, generation=None):
    from scripts.pipeline.render_outputs import _public_dashboard_data
    public = _public_dashboard_data(summary or {})
    for mobile, name in ((False,"dashboard_summary.svg"),(True,"dashboard_summary_mobile.svg")):
        Path("assets",name).write_text(render_svg(public,mobile=mobile,generation=generation),encoding="utf-8")
