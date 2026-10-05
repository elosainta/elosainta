"""Render the contribution calendar as a themed SVG banner. Usage: GITHUB_TOKEN=... python3 contrib.py > contributions.svg"""
import json
import os
import urllib.request
from datetime import date, timedelta

USER = os.environ.get("GH_USER", "elosainta")
QUERY = """query($u:String!){user(login:$u){contributionsCollection{contributionCalendar{
  totalContributions weeks{contributionDays{date contributionCount contributionLevel}}}}}}"""
LEVEL = {"NONE": "#2a1426", "FIRST_QUARTILE": "#5a1840", "SECOND_QUARTILE": "#a8245c",
         "THIRD_QUARTILE": "#ff4f8b", "FOURTH_QUARTILE": "#ffb35c"}
STEP, CELL, X0, Y0 = 19, 15, 112, 108


def fetch():
    body = json.dumps({"query": QUERY, "variables": {"u": USER}}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", body,
                                 {"Authorization": f"bearer {os.environ['GITHUB_TOKEN']}"})
    return json.load(urllib.request.urlopen(req))["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def streaks(days):
    longest = run = 0
    for d in days:
        run = run + 1 if d["contributionCount"] else 0
        longest = max(longest, run)
    counts = {d["date"]: d["contributionCount"] for d in days}
    day = date.fromisoformat(days[-1]["date"])
    if not counts.get(day.isoformat()):
        day -= timedelta(days=1)  # today not over yet, don't break the streak
    current = 0
    while counts.get(day.isoformat()):
        current += 1
        day -= timedelta(days=1)
    return longest, current


def render(cal):
    weeks = cal["weeks"]
    days = [d for w in weeks for d in w["contributionDays"]]
    longest, current = streaks(days)
    out = []
    last_month = None
    for i, w in enumerate(weeks):
        x = X0 + i * STEP
        month = w["contributionDays"][0]["date"][5:7]
        if month != last_month and i < len(weeks) - 2:
            name = date.fromisoformat(w["contributionDays"][0]["date"]).strftime("%b").upper()
            out.append(f'<text x="{x}" y="{Y0 - 10}" class="mono" font-size="11" fill="#a8708f">{name}</text>')
            last_month = month
        for d in w["contributionDays"]:
            y = Y0 + date.fromisoformat(d["date"]).isoweekday() % 7 * STEP
            out.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="3" fill="{LEVEL[d["contributionLevel"]]}"/>')
    for row, label in ((1, "MON"), (3, "WED"), (5, "FRI")):
        out.append(f'<text x="{X0 - 12}" y="{Y0 + row * STEP + 12}" class="mono" font-size="11" fill="#a8708f" text-anchor="end">{label}</text>')
    legend = "".join(f'<rect x="{1030 + i * 19}" y="250" width="15" height="15" rx="3" fill="{c}"/>' for i, c in enumerate(LEVEL.values()))
    stats = (f'<tspan fill="#fff4ec" font-weight="600">{cal["totalContributions"]:,}</tspan> contributions'
             f'<tspan fill="#ff4f8b">  ·  </tspan>longest streak <tspan fill="#fff4ec" font-weight="600">{longest}d</tspan>'
             f'<tspan fill="#ff4f8b">  ·  </tspan>current <tspan fill="#fff4ec" font-weight="600">{current}d</tspan>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 300" width="1200" height="300" role="img" aria-label="{cal["totalContributions"]} contributions in the last year">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#0e0710"/><stop offset="0.6" stop-color="#1f0b1c"/><stop offset="1" stop-color="#3d0f2e"/>
    </linearGradient>
    <clipPath id="r"><rect width="1200" height="300" rx="14"/></clipPath>
    <style>.mono {{ font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace; }}</style>
  </defs>
  <g clip-path="url(#r)">
    <rect width="1200" height="300" fill="url(#bg)"/>
    <path d="M28 44V28H44M1156 28H1172V44M1172 256V272H1156M44 272H28V256" stroke="#ff4f8b" stroke-opacity="0.5" stroke-width="1.5" fill="none"/>
    <text x="72" y="62" class="mono" font-size="13" letter-spacing="3" fill="#ffb35c">CONTRIBUTIONS · LAST 12 MONTHS</text>
    <text x="1128" y="62" class="mono" font-size="14" fill="#d6f5f2" text-anchor="end">{stats}</text>
    {"".join(out)}
    <text x="1020" y="262" class="mono" font-size="11" fill="#a8708f" text-anchor="end">LESS</text>
    {legend}
    <text x="1128" y="262" class="mono" font-size="11" fill="#a8708f">MORE</text>
  </g>
</svg>'''


if __name__ == "__main__":
    assert streaks([{"date": "2026-01-01", "contributionCount": 1}, {"date": "2026-01-02", "contributionCount": 2},
                    {"date": "2026-01-03", "contributionCount": 0}]) == (2, 2)
    print(render(fetch()))
