"""THE SYSTEM - scheduled job (runs on GitHub Actions, standard library only).

    python scripts/job.py sync              refresh data/leetcode.json
    python scripts/job.py remind morning    push the morning brief
    python scripts/job.py remind evening    push the evening check
    python scripts/job.py remind last       push the last call

Environment:
    LEETCODE_USER, CODEFORCES_USER   your handles
    NTFY_TOPIC                       private ntfy topic (repo secret). Unset = dry run, prints only.
    NTFY_SERVER                      default https://ntfy.sh
    TZ_OFFSET_MIN                    your offset from UTC in minutes, default 330 (India)
    APP_URL                          opened when the notification is tapped (auto-derived on GitHub)
"""
import datetime
import json
import os
import sys
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import serve  # noqa: E402  (reuses the LeetCode queries)

DATA = os.path.join(ROOT, "data", "leetcode.json")
LC_USER = os.environ.get("LEETCODE_USER", "").strip()
CF_USER = os.environ.get("CODEFORCES_USER", "").strip()
TZ = datetime.timezone(datetime.timedelta(minutes=int(os.environ.get("TZ_OFFSET_MIN", "330"))))  # 330 = India (UTC+5:30)
KEEP = 400  # submissions kept in the data file


def load():
    try:
        with open(DATA, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {"ok": True, "user": LC_USER, "generated": 0, "submissions": [], "contests": []}


def sync():
    """Merge the latest public LeetCode submissions into data/leetcode.json. Returns the merged data."""
    old = load()
    if not LC_USER:
        print("LEETCODE_USER not set - skipping LeetCode sync")
        return old
    try:
        fresh = serve.leetcode_profile(LC_USER)
    except Exception as exc:  # LeetCode down or blocking this runner
        print("LeetCode fetch failed:", exc)
        return old
    if not fresh.get("ok"):
        print("LeetCode:", fresh.get("error"))
        return old
    same_user = str(old.get("user", "")).lower() == LC_USER.lower()
    merged = {(s["slug"], s["ts"]): s for s in (old["submissions"] if same_user else [])}
    before = set(merged)
    for s in fresh["submissions"]:
        merged[(s["slug"], s["ts"])] = s
    subs = sorted(merged.values(), key=lambda s: -s["ts"])[:KEEP]
    contests = {c["title"]: c for c in (old.get("contests", []) if same_user else []) + fresh.get("contests", [])}
    out = {"ok": True, "user": LC_USER, "generated": old.get("generated", 0),
           "submissions": subs, "contests": sorted(contests.values(), key=lambda c: c["ts"])[-40:]}
    changed = set(merged) != before or len(contests) != len(old.get("contests", [])) or not same_user
    if changed or not os.path.exists(DATA):
        out["generated"] = int(time.time())
        os.makedirs(os.path.dirname(DATA), exist_ok=True)
        with open(DATA, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(out, fh, indent=1)
        print("data/leetcode.json updated: %d submissions (%d new)" % (len(subs), len(set(merged) - before)))
    else:
        print("No new LeetCode submissions")
    return out


def codeforces_today(day_start):
    if not CF_USER:
        return set()
    try:
        url = "https://codeforces.com/api/user.status?handle=%s&from=1&count=60" % urllib.parse.quote(CF_USER)
        with urllib.request.urlopen(url, timeout=15) as res:
            data = json.loads(res.read().decode())
        return {"cf:%s-%s" % (s["problem"].get("contestId"), s["problem"].get("index"))
                for s in data.get("result", []) if s.get("verdict") == "OK" and s["creationTimeSeconds"] >= day_start}
    except Exception as exc:
        print("Codeforces fetch failed:", exc)
        return set()


def app_url():
    if os.environ.get("APP_URL"):
        return os.environ["APP_URL"]
    repo = os.environ.get("GITHUB_REPOSITORY", "")  # "owner/name" on GitHub Actions
    if "/" in repo:
        owner, name = repo.split("/", 1)
        return "https://%s.github.io/%s/" % (owner.lower(), "" if name.lower() == owner.lower() + ".github.io" else name)
    return ""


def remind(mode):
    data = sync()
    now = datetime.datetime.now(TZ)
    day_start = int(now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
    solved = {"lc:" + s["slug"] for s in data["submissions"] if s.get("accepted") and s["ts"] >= day_start}
    solved |= codeforces_today(day_start)
    n, weekend = len(solved), now.weekday() >= 5
    target = 2
    if mode == "morning":
        title, prio, tags = "Daily Quest assigned", "default", "crossed_swords"
        body = ("Weekend raid: timed contest or mock, 3 h project work, 1 h system design, weekly review. About 5.5 h."
                if weekend else
                "2 problems (1 medium + 1 pattern drill), 1 h build/learn, 30 min review. About 2.5 h.")
    else:
        last = mode == "last"
        left = now.replace(hour=23, minute=59) - now
        hrs = max(0, int(left.total_seconds() // 3600))
        if weekend:
            status = "%d accepted submission%s today." % (n, "" if n == 1 else "s")
            todo = "Contest/mock, project, design and review still need ticking in the app."
        elif n >= target:
            status = "%d/%d problems verified today." % (n, target)
            todo = "Coding is done. Tick build/learn and review in the app to clear the day."
        else:
            status = "%d/%d problems submitted so far." % (n, target)
            todo = "Solve, submit, then open the app and sync."
        title = "Last call - quest resets at midnight" if last else "Daily Quest check"
        body = "%s %s About %d h left." % (status, todo, hrs)
        behind = (not weekend and n < target) or (weekend and n == 0)
        prio = "high" if last and behind else "default"
        tags = "warning" if last and behind else "hourglass_flowing_sand"
    send(title, body, prio, tags)


def send(title, body, priority="default", tags=""):
    topic = os.environ.get("NTFY_TOPIC", "").strip()
    print("[%s] %s\n    %s" % (priority, title, body))
    if not topic:
        print("NTFY_TOPIC not set - dry run, nothing sent")
        return
    server = os.environ.get("NTFY_SERVER", "https://ntfy.sh").rstrip("/")
    headers = {"Title": title, "Priority": priority}
    if tags:
        headers["Tags"] = tags
    if app_url():
        headers["Click"] = app_url()
    req = urllib.request.Request("%s/%s" % (server, urllib.parse.quote(topic, safe="")), data=body.encode("utf-8"), headers=headers)
    with urllib.request.urlopen(req, timeout=15) as res:
        print("ntfy:", res.status)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "sync"
    if cmd == "sync":
        sync()
    elif cmd == "remind" and len(sys.argv) > 2 and sys.argv[2] in ("morning", "evening", "last"):
        remind(sys.argv[2])
    else:
        sys.exit(__doc__)
