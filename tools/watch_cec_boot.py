# -*- coding: utf-8 -*-
"""真实重启电视，监视「功放联动开机 / 不自动切到功放界面 / ADB 自愈」。

用法：python tools/watch_cec_boot.py --wait 240
输出：cec_boot_watch.md / cec_boot_watch.json
"""
import argparse
import json
import re
import subprocess
import time
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADB = str(ROOT / "toolchain" / "android-sdk" / "platform-tools" / "adb.exe")
TARGET = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))["tv_ip"]
HOST = TARGET.split(":")[0]
BASE = "http://" + HOST + ":6095"
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def http(path, timeout=3):
    try:
        req = urllib.request.Request(BASE + path,
                                     headers={"User-Agent": "cec-boot-watch"})
        with OPENER.open(req, timeout=timeout) as r:
            return r.read(2048).decode("utf-8", "replace")
    except Exception:  # noqa: BLE001
        return ""


def alive6095():
    return '"status":0' in http("/request?action=isalive", 2)


def adb(args, timeout=10):
    try:
        p = subprocess.run([ADB, "-s", TARGET] + args,
                           capture_output=True, text=True, timeout=timeout)
        return (p.stdout + p.stderr).strip()
    except Exception as e:  # noqa: BLE001
        return "ERR:" + str(e)


def probe():
    """一次采样；ADB 不通时只返回网络层状态。"""
    d = {"t": round(time.time() - T0, 1),
         "clock": datetime.now().strftime("%H:%M:%S"),
         "p6095": alive6095()}
    try:
        subprocess.run([ADB, "connect", TARGET], capture_output=True, timeout=8)
    except Exception:  # noqa: BLE001
        pass
    state = adb(["get-state"], timeout=8)
    d["state"] = state
    if state != "device":
        return d
    d["adb_enabled"] = adb(["shell", "settings", "get", "global", "adb_enabled"])
    d["auto_switch"] = adb(
        ["shell", "settings", "get", "global", "mitv.settings.db.video.auto_switch"])
    hd = adb(["shell", "dumpsys", "hdmi_control"], timeout=15)
    m = re.search(r"mActiveRoutingPath:\s*(0x[0-9a-fA-F]+)", hd)
    d["routing"] = m.group(1) if m else ""
    m = re.search(r"mActiveSource:\s*\((\w+),\s*(\w+)\)", hd)
    d["active_source"] = "/".join(m.groups()) if m else ""
    amps = re.findall(r"device_type: 5 vendor_id: \d+ display_name: ([^\s]+) "
                      r"power_status: (\S+)", hd)
    d["amp_power"] = ",".join("%s=%s" % x for x in amps) or ""
    d["cec_on"] = "true" if "mHdmiControlEnabled: true" in hd else "false"
    fg = adb(["shell", "dumpsys", "activity", "activities"], timeout=12)
    m = re.search(r"mResumedActivity:.*?u0\s+([\w.]+)/", fg)
    d["foreground"] = m.group(1) if m else ""
    return d


def main():
    global T0
    ap = argparse.ArgumentParser()
    ap.add_argument("--wait", type=int, default=240, help="重启后监视秒数")
    ap.add_argument("--no-reboot", action="store_true", help="只观察不重启")
    args = ap.parse_args()

    T0 = time.time()
    print("重启前基线：", json.dumps(probe(), ensure_ascii=False), flush=True)
    if not args.no_reboot:
        print("下发 adb reboot ...", flush=True)
        print(adb(["reboot"], timeout=15), flush=True)
        time.sleep(3)

    samples = []
    deadline = time.time() + args.wait
    while time.time() < deadline:
        d = probe()
        samples.append(d)
        print("+%6.1fs 6095=%-5s adb=%-9s enabled=%-3s switch=%-3s "
              "routing=%-8s amp=%-18s fg=%s" % (
                  d["t"], d["p6095"], d["state"], d.get("adb_enabled", "-"),
                  d.get("auto_switch", "-"), d.get("routing", "-"),
                  d.get("amp_power", "-") or "-", d.get("foreground", "-") or "-"),
              flush=True)
        time.sleep(6)

    online = [x for x in samples if x["state"] == "device"]
    first = online[0]["t"] if online else None
    last = online[-1] if online else {}
    external = [x["t"] for x in online
                if x.get("routing") and x["routing"].lower() not in ("0x0000", "0x0")]
    amp_on = [x for x in online if x.get("amp_power", "").endswith("=0")
              or "=0," in x.get("amp_power", "")]
    switch_kept = all(x.get("auto_switch") == "0" for x in online) if online else False
    stayed_home = bool(last.get("foreground") in (
        "com.xiaomi.eetv.home", "com.mitv.tvhome", ""))

    if first is None:
        verdict = "ADB_NEVER_BACK"
        conclusion = "整个观察窗口内 ADB 一直没恢复，需要人工检查。"
    elif external:
        verdict = "CEC_SWITCHED"
        conclusion = ("开机后活动源曾被切到外部 HDMI（+%s 秒），说明「直接播放信号源」"
                      "没拦住；需要看守护是否把它拉回了桌面。" %
                      ",".join(str(x) for x in external[:8]))
    else:
        verdict = "NO_CEC_SWITCH"
        conclusion = ("开机后 HDMI-CEC 活动源始终为 0x0000（电视自己），"
                      "没有切到功放界面；功放电源=%s，功放照常联动。"
                      % (last.get("amp_power") or "未读到"))

    summary = {
        "verdict": verdict,
        "conclusion": conclusion,
        "first_adb_recovery_sec": first,
        "auto_switch_stayed_0": switch_kept,
        "external_routing_events": external,
        "amp_on_samples": len(amp_on),
        "final": last,
        "cec_enabled_final": last.get("cec_on", "-"),
        "final_foreground": last.get("foreground", "-"),
        "stayed_on_tv_ui": stayed_home,
    }
    (ROOT / "cec_boot_watch.json").write_text(
        json.dumps({"summary": summary, "samples": samples},
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md = ["# 真实开机验证：功放联动 / 防切源 / ADB 自愈", "",
          "时间：" + datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "",
          "## 结论", "", "**[%s] %s**" % (verdict, conclusion), "",
          "- ADB 首次恢复：+%s 秒" % (first if first is not None else "从未"),
          "- 「直接播放信号源」保持为 0：%s" % switch_kept,
          "- CEC 活动源被切到外部设备的时刻：%s" % (external or "无"),
          "- 读到功放处于开机态的采样数：%d" % len(amp_on),
          "- CEC 总开关最终：%s" % summary["cec_enabled_final"],
          "- 最终前台：%s" % summary["final_foreground"],
          "- 最终停在电视自己的界面：%s" % stayed_home, "",
          "## 时间线（节选）", "",
          "| 秒 | 6095 | ADB | adb_enabled | 开关 | routing | 功放电源 | 前台 |",
          "|---|---|---|---|---|---|---|---|"]
    step = max(1, len(samples) // 40)
    for x in samples[::step]:
        md.append("| %.1f | %s | %s | %s | %s | %s | %s | %s |" % (
            x["t"], x["p6095"], x["state"], x.get("adb_enabled", "-"),
            x.get("auto_switch", "-"), x.get("routing", "-"),
            x.get("amp_power", "-") or "-", x.get("foreground", "-") or "-"))
    (ROOT / "cec_boot_watch.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n" + "=" * 70, flush=True)
    print("结论 [%s]：%s" % (verdict, conclusion), flush=True)
    print("报告：cec_boot_watch.md / cec_boot_watch.json", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
