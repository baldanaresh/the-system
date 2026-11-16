"""THE SYSTEM - local launcher.

    python serve.py            -> http://localhost:8123

Serves index.html from this folder and relays ONE read-only request to
LeetCode's public profile API, because LeetCode does not let a web page call
it directly. Nothing is stored, no login is used, and the server only listens
on this computer (127.0.0.1). Standard library only - nothing to install.
"""
import json
import os
import re
import socket
import sys
import urllib.request
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

# Some networks advertise IPv6 but cannot route it, which makes every request
# wait ~20 s for a timeout. Try IPv4 addresses first; IPv6 stays as a fallback.
_getaddrinfo = socket.getaddrinfo
def _ipv4_first(*args, **kwargs):
    return sorted(_getaddrinfo(*args, **kwargs), key=lambda r: r[0] != socket.AF_INET)
socket.getaddrinfo = _ipv4_first

PORT = 8123
ROOT = os.path.dirname(os.path.abspath(__file__))
LEETCODE = "https://leetcode.com/graphql"
USER_RE = re.compile(r"^[A-Za-z0-9_.-]{1,40}$")
SLUG_RE = re.compile(r"^[a-z0-9-]{1,120}$")
QUESTION_CACHE = {}  # slug -> {"difficulty": ..., "tags": [...]}

PROFILE_QUERY = """
query($u: String!) {
  matchedUser(username: $u) { username }
  recentSubmissionList(username: $u, limit: 40) { title titleSlug timestamp statusDisplay }
  recentAcSubmissionList(username: $u, limit: 20) { id title titleSlug timestamp }
  userContestRankingHistory(username: $u) { attended contest { title startTime } }
}"""


def gql(query, variables=None):
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(LEETCODE, data=body, headers={
        "Content-Type": "application/json",
        "Referer": "https://leetcode.com",
        "User-Agent": "Mozilla/5.0 (local study tracker)",
    })
    with urllib.request.urlopen(req, timeout=15) as res:
        return json.loads(res.read().decode()).get("data") or {}


def question_details(slugs):
    missing = [s for s in dict.fromkeys(slugs) if s not in QUESTION_CACHE and SLUG_RE.match(s)]
    for i in range(0, len(missing), 20):
        chunk = missing[i:i + 20]
        query = "{" + " ".join(
            'q%d: question(titleSlug: "%s") { difficulty topicTags { name } }' % (n, s)
            for n, s in enumerate(chunk)) + "}"
        data = gql(query)
        for n, s in enumerate(chunk):
            q = data.get("q%d" % n) or {}
            QUESTION_CACHE[s] = {
                "difficulty": (q.get("difficulty") or "Medium").lower(),
                "tags": [t["name"] for t in (q.get("topicTags") or [])],
            }
    return QUESTION_CACHE


def leetcode_profile(user):
    data = gql(PROFILE_QUERY, {"u": user})
    if not data.get("matchedUser"):
        return {"ok": False, "error": "LeetCode user not found: " + user}
    subs = data.get("recentSubmissionList") or []
    acs = data.get("recentAcSubmissionList") or []
    details = question_details([s["titleSlug"] for s in subs + acs])
    out, seen = [], set()
    for s in subs + [dict(a, statusDisplay="Accepted") for a in acs]:
        key = (s["titleSlug"], s["timestamp"])
        if key in seen:
            continue
        seen.add(key)
        d = details.get(s["titleSlug"], {})
        out.append({
            "slug": s["titleSlug"], "title": s["title"], "ts": int(s["timestamp"]),
            "accepted": s.get("statusDisplay") == "Accepted",
            "difficulty": d.get("difficulty", "medium"), "tags": d.get("tags", []),
        })
    contests = [{"title": c["contest"]["title"], "ts": int(c["contest"]["startTime"])}
                for c in (data.get("userContestRankingHistory") or []) if c.get("attended")]
    return {"ok": True, "user": user, "submissions": out, "contests": contests[-30:]}


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        url = urlparse(self.path)
        if url.path != "/api/leetcode":
            return super().do_GET()
        user = (parse_qs(url.query).get("user") or [""])[0]
        if not USER_RE.match(user):
            return self.send_json(400, {"ok": False, "error": "Invalid username"})
        try:
            self.send_json(200, leetcode_profile(user))
        except Exception as exc:  # network down, LeetCode changed, etc.
            self.send_json(502, {"ok": False, "error": "LeetCode unreachable: %s" % exc})

    def send_json(self, code, payload):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self):
        if not self.path.startswith("/api/"):
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def log_message(self, fmt, *args):
        if "/api/" in (args[0] if args else ""):
            super().log_message(fmt, *args)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        PORT = int(sys.argv[1])
    server = ThreadingHTTPServer(("127.0.0.1", PORT), partial(Handler, directory=ROOT))
    print("THE SYSTEM is running at http://localhost:%d  (Ctrl+C to stop)" % PORT)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
