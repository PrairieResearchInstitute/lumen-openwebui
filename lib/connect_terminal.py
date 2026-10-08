# Register Open Terminal as a system terminal in Open WebUI, through its admin API.
# Runs INSIDE the open-webui container (python3 is there; nothing needed on the host).
# Called by `owui connect-terminal`. Reads from stdin, one per line:
#   1. the Open Terminal API key
#   2. an Open WebUI API key (empty in single-user mode)
# Safe to run again: it updates the existing connection instead of adding a second one.
import json
import sys
import urllib.error
import urllib.request
import uuid

BASE = "http://localhost:8080"
TERM_URL = sys.argv[1] if len(sys.argv) > 1 else "http://open-terminal:8000"
TERM_NAME = sys.argv[2] if len(sys.argv) > 2 else "Workspace"

lines = sys.stdin.read().splitlines() + ["", ""]
ot_key, api_key = lines[0].strip(), lines[1].strip()
if not ot_key:
    sys.exit("owui: no Open Terminal key given")


def call(method, path, token=None, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:300]
        sys.exit("owui: %s %s failed: HTTP %s %s" % (method, path, e.code, detail))
    except urllib.error.URLError as e:
        sys.exit("owui: cannot reach Open WebUI inside the container: %s" % e.reason)


# 1. Get an admin token. In single-user mode (WEBUI_AUTH=False) sign-in needs no password.
if api_key:
    token = api_key
else:
    res = call("POST", "/api/v1/auths/signin",
               body={"email": "admin@localhost", "password": "admin"})
    token = (res or {}).get("token")
    if not token:
        sys.exit("owui: sign-in returned no token")

# 2. Check that Open WebUI can reach the terminal with this key.
check = call("POST", "/api/v1/configs/terminal_servers/verify", token,
             {"url": TERM_URL, "key": ot_key, "auth_type": "bearer"}) or {}
if not check.get("status"):
    sys.exit("owui: Open WebUI could not verify the terminal at %s" % TERM_URL)
server_type = check.get("type") or "terminal"

# 3. Add or update the connection, keeping any other terminal connections as they are.
current = call("GET", "/api/v1/configs/terminal_servers", token) or {}
conns = current.get("TERMINAL_SERVER_CONNECTIONS") or []

entry = {
    "url": TERM_URL,
    "key": ot_key,
    "name": TERM_NAME,
    "path": "/openapi.json",
    "auth_type": "bearer",
    "forward_cookies": False,
    "enabled": True,
    "config": {"access_grants": []},
    "server_type": server_type,
}

action = "added"
for i, c in enumerate(conns):
    if (c.get("url") or "").rstrip("/") == TERM_URL.rstrip("/"):
        merged = dict(c)
        merged.update(entry)
        merged["id"] = c.get("id") or str(uuid.uuid4())
        merged["name"] = c.get("name") or TERM_NAME
        merged["config"] = dict(c.get("config") or {}, **{"access_grants": (c.get("config") or {}).get("access_grants", [])})
        conns[i] = merged
        action = "updated"
        break
else:
    entry["id"] = str(uuid.uuid4())
    conns.append(entry)

call("POST", "/api/v1/configs/terminal_servers", token,
     {"TERMINAL_SERVER_CONNECTIONS": conns})
print("owui: terminal connection %s: '%s' -> %s (%s)" % (action, TERM_NAME, TERM_URL, server_type))
