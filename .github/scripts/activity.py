"""Write recent public GitHub activity between the activity markers in README.md."""
import json, os, re, urllib.request
from datetime import datetime, timezone

USER = os.environ.get("GH_USER", "Dinesh-Sunny")
MAX_LINES = 8
req = urllib.request.Request(
    f"https://api.github.com/users/{USER}/events/public?per_page=100",
    headers={"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}", "Accept": "application/vnd.github+json"},
)
events = json.load(urllib.request.urlopen(req))

def link(repo):
    return f"[{repo.split('/')[-1]}](https://github.com/{repo})"

lines, seen = [], set()
for e in events:
    repo, p, kind = e["repo"]["name"], e.get("payload", {}), e["type"]
    day = datetime.fromisoformat(e["created_at"].replace("Z", "+00:00")).strftime("%d %b %Y")
    if repo.endswith(f"/{USER}"):  # skip the profile repo itself
        continue
    if kind == "PushEvent":
        key, text = ("push", repo), f"Pushed to {link(repo)}"
    elif kind == "CreateEvent" and p.get("ref_type") == "repository":
        key, text = ("create", repo), f"Created {link(repo)}"
    elif kind == "ReleaseEvent":
        key, text = ("rel", repo), f"Released {p['release'].get('tag_name', '')} of {link(repo)}"
    elif kind == "PullRequestEvent" and p.get("action") in ("opened", "closed"):
        pr = p["pull_request"]
        verb = "Merged" if pr.get("merged") else ("Opened" if p["action"] == "opened" else "Closed")
        key, text = ("pr", repo, pr["number"]), f"{verb} PR [#{pr['number']}]({pr['html_url']}) in {link(repo)}"
    elif kind == "IssuesEvent" and p.get("action") in ("opened", "closed"):
        i = p["issue"]
        key, text = ("is", repo, i["number"]), f"{p['action'].title()} issue [#{i['number']}]({i['html_url']}) in {link(repo)}"
    elif kind == "WatchEvent":
        key, text = ("star", repo), f"Starred [{repo}](https://github.com/{repo})"
    elif kind == "ForkEvent":
        key, text = ("fork", repo), f"Forked [{repo}](https://github.com/{repo})"
    else:
        continue
    if key in seen:
        continue
    seen.add(key)
    lines.append(f"{len(lines) + 1}. {text} <sub>{day}</sub>")
    if len(lines) >= MAX_LINES:
        break

body = "\n".join(lines) or "Quiet week in public - building in private repos."
readme = open("README.md", encoding="utf-8").read()
new = re.sub(r"(<!--START_SECTION:activity-->).*?(<!--END_SECTION:activity-->)",
             lambda m: f"{m.group(1)}\n{body}\n{m.group(2)}", readme, flags=re.S)
open("README.md", "w", encoding="utf-8").write(new)
print(body)
