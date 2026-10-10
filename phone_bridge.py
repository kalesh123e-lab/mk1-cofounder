#!/usr/bin/env python3
"""MK.1 phone bridge -- runs on YOUR Android phone inside Termux, so MK.1 can use the phone.

One-time setup (Termux from F-Droid, plus the "Termux:API" app from F-Droid):
    pkg update && pkg install python termux-api
Run (use the Render URL and the BRIDGE_TOKEN shown in Render -> Environment):
    termux-wake-lock
    python phone_bridge.py https://YOUR-APP.onrender.com YOUR_BRIDGE_TOKEN

Actions MK.1 can send: notify, open (URL / WhatsApp chat), speak, toast, vibrate, clip, sms.
Only the owner can queue these (from /admin). Nothing else runs on your phone.
Android 10+ may block "open" while the screen is off -- allow Termux "Display over other apps".
"""
import sys, json, time, subprocess, urllib.request

if len(sys.argv) < 3:
    sys.exit(__doc__)
BASE, TOKEN = sys.argv[1].rstrip("/"), sys.argv[2]


def call(path, data=None):
    req = urllib.request.Request(BASE + path, data=None if data is None else json.dumps(data).encode(),
                                 headers={"X-Bridge-Token": TOKEN, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read() or b"{}")


def run(action, p):
    cmds = {
        "notify": lambda: ["termux-notification", "--title", p.get("title", "MK.1"), "--content", p.get("text", "")],
        "open": lambda: ["termux-open-url", p["url"]],
        "speak": lambda: ["termux-tts-speak", p["text"]],
        "toast": lambda: ["termux-toast", p["text"]],
        "vibrate": lambda: ["termux-vibrate", "-d", "500"],
        "clip": lambda: ["termux-clipboard-set", p["text"]],
        "sms": lambda: ["termux-sms-send", "-n", p["to"], p["text"]],
    }
    if action not in cmds:
        return False, "unknown action"
    r = subprocess.run(cmds[action](), capture_output=True, text=True, timeout=30)
    return r.returncode == 0, (r.stdout + r.stderr).strip()[:200]


print("MK.1 bridge connected to", BASE)
while True:
    try:
        c = call("/api/phone/pull")
        if c.get("id"):
            ok, res = run(c["action"], c.get("payload", {}))
            call("/api/phone/done", {"id": c["id"], "ok": ok, "result": res})
            print(c["action"], "ok" if ok else "FAILED", res)
            continue
    except Exception as e:
        print("bridge error:", e)
        time.sleep(15)
    time.sleep(10)
