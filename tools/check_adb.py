# -*- coding: utf-8 -*-
"""一键自检：电视 ADB 还在不在、答题 APK 装没装、守护脚本状态如何。

电视重启后如果「ADB调试」被系统自动关掉，5555 端口会直接拒绝连接，
守护脚本再怎么重连也连不上，进门闸门和计时题都会停摆。这个脚本把它说清楚。

用法：双击 tv-quiz/check_adb.bat，或 python tools/check_adb.py
"""
import json
import socket
import subprocess
import sys
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
ENV = json.loads((ROOT / "toolchain" / "env.json").read_text(encoding="utf-8"))
CONF = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
ADB = ENV["adb"]
TARGET = CONF["tv_ip"]
HOST, PORT = TARGET.split(":")
STATUS = ROOT / "STATUS.json"


def adb(args, timeout=25):
    try:
        p = subprocess.run([ADB, "-s", TARGET] + args,
                           capture_output=True, timeout=timeout)
        return p.stdout.decode("utf-8", "replace").strip()
    except Exception as e:  # noqa: BLE001
        return "[ERR] " + str(e)


def port_open(host, port, sec=1.5):
    s = socket.socket()
    s.settimeout(sec)
    try:
        s.connect((host, int(port)))
        return True
    except Exception:  # noqa: BLE001
        return False
    finally:
        s.close()


def main():
    print("=" * 68)
    print("电视答题守护 · 连接自检   " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("电视地址：" + TARGET)
    print("=" * 68)

    opened = port_open(HOST, PORT)
    print("1) 5555 端口          ：" + ("开放" if opened else "拒绝连接"))

    if not opened:
        print()
        print("   结论：电视端的 adbd 没在监听。")
        print("   可能是：电视没开机 / 深度待机息屏 / 重启后「ADB调试」被自动关掉。")
        print()
        print("   请到电视上检查：设置 → 帐号与安全 → ADB调试，关了就重新打开。")
        print("   打开后电脑这边不用重新授权，守护脚本会自动连回来。")
        print("   弄好后双击一次本脚本复查，或看守护窗口是否打印「电视重新连上」。")
        return 2

    subprocess.run([ADB, "connect", TARGET], capture_output=True, timeout=25)
    state = adb(["get-state"])
    print("2) adb 连接状态       ：" + (state or "(空)"))

    if state != "device":
        print()
        print("   结论：连上了但没授权。")
        print("   请看电视屏幕，弹出「允许 USB 调试吗」时勾「一律允许」再点确定。")
        return 3

    enabled = adb(["shell", "settings get global adb_enabled"])
    tcp_persist = adb(["shell", "getprop persist.adb.tcp.port"])
    svc_persist = adb(["shell", "getprop persist.service.adb.enable"])
    apk = adb(["shell", "pm path com.wb.tvquiz"])
    fg = adb(["shell", "dumpsys activity activities | grep mResumedActivity | head -n 1"])

    print("3) ADB 调试开关       ：" + ("开 (1)" if enabled.strip() == "1" else enabled or "(未知)"))
    print("4) 端口持久属性       ：" + (tcp_persist or "(空)"))
    print("   服务持久属性       ：" + (svc_persist or "(空)"))
    print("5) 答题 APK           ：" + ("已安装" if "package:" in apk else "未安装！需重装 tvquiz.apk"))
    print("6) 当前前台           ：" + (fg.split("u0 ")[-1][:70] if "u0 " in fg else fg[:70]))

    print()
    if "package:" not in apk:
        print("   ⚠ 答题 APK 不在了，请用 adb install -r apk/tvquiz.apk 重装。")
    print("   结论：连接正常，进门闸门与计时题可以工作。")
    print("   提醒：上面几个 persist 属性都是「持久」的，理论上重启后仍在；")
    print("   但小米可能在开机时另把 ADB 调试开关清零，是否真的会关，重启一次最准。")

    if STATUS.exists():
        try:
            s = json.loads(STATUS.read_text(encoding="utf-8"))
            print()
            print("7) 守护脚本最近状态   ：%s（%s）" % (s.get("state"), s.get("time")))
            print("   " + str(s.get("message", ""))[:110])
        except Exception:  # noqa: BLE001
            pass
    else:
        print()
        print("7) 守护脚本最近状态   ：没有 STATUS.json，守护可能还没启动过。")
        print("   正式启用请双击 start_quiz.bat。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
