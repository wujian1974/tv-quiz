#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""连接电视后一次性采集设备信息、前台应用与 B 站包名，供后续开发使用。"""
import json
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
ENV = json.loads((ROOT / "toolchain" / "env.json").read_text(encoding="utf-8"))
ADB = ENV["adb"]
TARGET = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))["tv_ip"]


def run(args, timeout=25):
    try:
        p = subprocess.run([ADB, "-s", TARGET] + args, capture_output=True,
                           timeout=timeout)
        out = p.stdout.decode("utf-8", "replace").strip()
        err = p.stderr.decode("utf-8", "replace").strip()
        return out, err
    except Exception as e:  # noqa: BLE001
        return "", str(e)


def shell(cmd, timeout=25):
    out, err = run(["shell", cmd], timeout)
    return out if out else ("[ERR] " + err if err else "")


def main():
    # adb server 重启后连接记录会丢失，每次先重连（connect 不能带 -s）
    try:
        p = subprocess.run([ADB, "connect", TARGET], capture_output=True, timeout=25)
        print("connect =", p.stdout.decode("utf-8", "replace").strip())
    except Exception as e:  # noqa: BLE001
        print("connect failed =", e)

    out, err = run(["get-state"])
    state = out.strip()
    print("device state =", state or err)
    if state != "device":
        print("设备尚未授权或离线：请在电视上点「允许 USB 调试」，勾「始终允许」。")
        return 1

    props = {}
    keys = [
        "ro.product.manufacturer", "ro.product.model", "ro.product.name",
        "ro.build.version.release", "ro.build.version.sdk",
        "ro.build.display.id", "ro.product.cpu.abi",
        "ro.build.characteristics", "service.adb.tcp.port",
        "persist.adb.tcp.port", "ro.sf.lcd_density",
    ]
    for k in keys:
        props[k] = shell("getprop " + k)

    display = {
        "wm_size": shell("wm size"),
        "wm_density": shell("wm density"),
    }

    focus = shell("dumpsys activity activities | grep -E 'mResumedActivity|topResumedActivity|mCurrentFocus' | head -n 8")
    window = shell("dumpsys window | grep -E 'mCurrentFocus|mFocusedApp' | head -n 5")

    pkg_all, _ = run(["shell", "pm list packages"])
    packages = [l.replace("package:", "").strip() for l in pkg_all.splitlines() if l.startswith("package:")]
    third_party, _ = run(["shell", "pm list packages -3"])
    third = [l.replace("package:", "").strip() for l in third_party.splitlines() if l.startswith("package:")]
    bili = [p for p in packages if any(k in p.lower() for k in
            ("bili", "xmtv", "cloudtv", "cibn", "mgtv", "iqiyi", "youku",
             "tvplayer", "chinasoul", "cat3399", "bv2"))]

    probe = {
        "target": TARGET,
        "state": state,
        "props": props,
        "display": display,
        "foreground": {"activities": focus, "window": window},
        "package_count": len(packages),
        "third_party": third,
        "video_packages": bili,
    }
    dst = ROOT / "tv_probe.json"
    dst.write_text(json.dumps(probe, ensure_ascii=False, indent=2), encoding="utf-8")

    print("=" * 70)
    for k, v in props.items():
        print(f"{k:32s} = {v}")
    print("wm size  =", display["wm_size"].replace("\n", " | "))
    print("wm density =", display["wm_density"].replace("\n", " | "))
    print("--- foreground ---")
    print(focus or "(none)")
    print(window or "(none)")
    print("--- packages ---")
    print("total =", len(packages), " third-party =", len(third))
    print("video candidates =", bili)
    print("--- third-party apps ---")
    for p in third:
        print(" ", p)
    print("=" * 70)
    print("saved ->", dst)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
