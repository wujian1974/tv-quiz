# -*- coding: utf-8 -*-
"""重启小米电视，全程记录网络 ADB 会不会被系统自动关掉。

采样项：ICMP ping / 5555 端口 / adb 授权状态 / adb_enabled / 三个 persist 属性。
只有「端口先关过、之后重新开放且能 adb shell」才算真正重启完成，避免把
关机前那几秒仍在线的假象当成结论。

用法：
  python tools/watch_reboot.py                 下发 reboot 并监视（默认 240 秒）
  python tools/watch_reboot.py --wait 300     延长观察
  python tools/watch_reboot.py --no-reboot    只采样当前状态，不下发重启

产物：reboot_watch.json（逐次采样）、reboot_watch.md（结论）
"""
import argparse
import json
import socket
import subprocess
import sys
import time
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
JSON_OUT = ROOT / "reboot_watch.json"
MD_OUT = ROOT / "reboot_watch.md"


def adb(args, timeout=15):
    try:
        p = subprocess.run([ADB, "-s", TARGET] + args,
                           capture_output=True, timeout=timeout)
        return p.stdout.decode("utf-8", "replace").strip()
    except Exception as e:  # noqa: BLE001
        return "[ERR] " + str(e)


def adb_connect(timeout=15):
    try:
        p = subprocess.run([ADB, "connect", TARGET],
                           capture_output=True, timeout=timeout)
        return p.stdout.decode("utf-8", "replace").strip()
    except Exception as e:  # noqa: BLE001
        return "[ERR] " + str(e)


def port_open(sec=0.8):
    s = socket.socket()
    s.settimeout(sec)
    try:
        s.connect((HOST, int(PORT)))
        return True
    except Exception:  # noqa: BLE001
        return False
    finally:
        s.close()


def ping():
    try:
        p = subprocess.run(["ping", "-n", "1", "-w", "800", HOST],
                           capture_output=True, timeout=3)
        return p.returncode == 0
    except Exception:  # noqa: BLE001
        return False


def snapshot():
    return {
        "adb_enabled": adb(["shell", "settings get global adb_enabled"]),
        "persist_port": adb(["shell", "getprop persist.adb.tcp.port"]),
        "persist_svc": adb(["shell", "getprop persist.service.adb.enable"]),
        "adbd": adb(["shell", "getprop init.svc.adbd"]),
        "uptime": adb(["shell", "cat /proc/uptime"]).split(" ")[0],
        "apk": "installed" if "package:" in adb(["shell", "pm path com.wb.tvquiz"])
               else "missing",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wait", type=int, default=420)
    ap.add_argument("--settle", type=int, default=150,
                    help="首次恢复后再稳定观察多少秒，防止把「开机短暂恢复又被关掉」误判成不会关")
    ap.add_argument("--no-reboot", action="store_true")
    args = ap.parse_args()

    print("=" * 74)
    print("电视重启 · ADB 状态监视   " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("目标：" + TARGET)
    print("=" * 74)

    adb_connect()
    base_state = adb(["get-state"])
    base = snapshot() if base_state == "device" else {}
    print("基线：state=%s  %s" % (base_state, json.dumps(base, ensure_ascii=False)))

    if not args.no_reboot:
        if base_state != "device":
            print("!! 当前不是 device 状态，无法下发 reboot（请先确认电视在线并已授权）")
            return 2
        print(">> 下发 adb reboot ...")
        p = subprocess.run([ADB, "-s", TARGET, "reboot"],
                           capture_output=True, timeout=30)
        print("   reboot 返回码 = %d  %s" % (p.returncode,
              p.stdout.decode("utf-8", "replace").strip()[:100]))
        subprocess.run([ADB, "disconnect", TARGET],
                       capture_output=True, timeout=10)

    t0 = time.time()
    samples = []
    saw_port_down = False
    recovered_at = None
    lost_since = None
    settle_deadline = None
    conclusion = ""
    verdict = ""
    late_off_events = []   # 稳定观察期内出现过的长时间掉线起点
    recovery_events = []   # 掉线后自行恢复的时间点
    ever_late_off = False

    while time.time() - t0 < args.wait:
        dt = round(time.time() - t0, 1)
        pg = ping()
        po = port_open()
        if not po:
            saw_port_down = True
        state = ""
        extra = {}
        if po:
            adb_connect(timeout=12)
            state = adb(["get-state"], timeout=12)
            if state == "device":
                extra = snapshot()
        row = {"t": dt, "ping": pg, "port": po, "state": state}
        row.update(extra)
        samples.append(row)
        print("%5.1fs  ping=%-5s port=%-5s state=%-12s %s"
              % (dt, pg, po, state or "-",
                 ("adb_enabled=%s persist=%s/%s" %
                  (extra.get("adb_enabled"), extra.get("persist_port"),
                   extra.get("persist_svc"))) if extra else ""))

        is_back = saw_port_down and po and state == "device" and dt > 15
        if is_back and recovered_at is None:
            recovered_at = dt
            settle_deadline = time.time() + args.settle
            print(">> 首次恢复（+%.0fs），进入 %d 秒稳定观察期，"
                  "专门抓「开机后又被关掉」" % (dt, args.settle))

        if recovered_at is not None:
            online = po and state == "device"
            if not online:
                if lost_since is None:
                    lost_since = time.time()
                elif not ever_late_off and time.time() - lost_since >= 20:
                    ever_late_off = True
                    late_off_events.append(round(dt, 1))
                    # 掉线后再给一个完整观察期，专门等电视端自愈把 ADB 拉回来
                    settle_deadline = time.time() + args.settle
                    print(">> 观察期内出现长时间掉线（+%.1fs，已持续 20 秒），"
                          "继续看是否由电视端自愈拉回" % dt)
            else:
                if lost_since is not None:
                    recovery_events.append(round(dt, 1))
                    print(">> 掉线后自行恢复（+%.1fs），adb_enabled=%s"
                          % (dt, extra.get("adb_enabled", "-")))
                lost_since = None
            if (settle_deadline and time.time() >= settle_deadline
                    and lost_since is None and not ever_late_off):
                verdict = "KEEP_ON"
                conclusion = ("重启后 5555 恢复，且连续稳定观察 %d 秒没有再断开，"
                              "adb_enabled=1。这台电视重启不会自动关掉 ADB 调试。" % args.settle)
                break
        time.sleep(2)

    if not conclusion:
        last = samples[-1] if samples else {}
        final_online = bool(last.get("port")) and last.get("state") == "device"
        if recovered_at is not None and ever_late_off and final_online:
            verdict = "SELF_HEALED"
            conclusion = ("重启后 ADB 在 +%.0fs 首次恢复；稳定观察期内又被系统关掉"
                          "（掉线起于 +%s 秒），随后在 +%s 秒自行恢复；观察结束时 "
                          "5555 开放、state=device、adb_enabled=%s、adbd=%s。"
                          "确认「应用开机自启 + AdbKeeper 写回 adb_enabled」生效，"
                          "这次重启全程没有人工打开 ADB 开关。"
                          % (recovered_at,
                             "/".join(str(x) for x in late_off_events) or "-",
                             "/".join(str(x) for x in recovery_events) or "-",
                             last.get("adb_enabled", "-"), last.get("adbd", "-")))
        elif recovered_at is not None and ever_late_off:
            verdict = "ADB_OFF_LATE"
            conclusion = ("重启后 ADB 在 +%.0fs 短暂恢复，稳定观察期内又断开并持续到观察结束。"
                          "电视端自愈没能拉回，需要人工打开 ADB 开关，"
                          "或检查应用开机自启白名单是否被系统回收。" % recovered_at)
        elif recovered_at is not None:
            verdict = "UNKNOWN"
            conclusion = ("重启后曾在 +%.0fs 恢复，但观察窗口结束前没能得出稳定结论，"
                          "请加大 --wait 重跑。" % recovered_at)
        elif last.get("port") and last.get("state") == "unauthorized":
            verdict = "NEED_AUTH"
            conclusion = "电视回来了，但要求重新授权：请在电视上点「允许 USB 调试」。"
        elif last.get("ping") and not last.get("port"):
            verdict = "ADB_OFF"
            conclusion = ("电视已回到网络（ping 通），但 5555 端口全程不监听。"
                          "证实：重启后 ADB 调试开关确实被系统关掉了，"
                          "电脑端无法自行恢复，必须到电视 设置→帐号与安全→ADB调试 手动打开，"
                          "或做开机自启自动恢复方案。")
        elif not last.get("ping"):
            verdict = "NO_NETWORK"
            conclusion = "电视在观察期内没有回到网络，可能还在重启或进了深度待机，需要人工唤醒确认。"
        else:
            verdict = "UNKNOWN"
            conclusion = "未观察到明确的重启完成信号，请延长 --wait 再试。"

    keeper_log = ""
    if recovered_at is not None:
        keeper_log = adb(["shell", "logcat", "-d", "-s", "TVQuizAdb:I"], timeout=25)

    print()
    print("=" * 74)
    print("结论 [%s]：%s" % (verdict, conclusion))
    print("=" * 74)

    payload = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "target": TARGET,
        "reboot_sent": not args.no_reboot,
        "baseline": {"state": base_state, "props": base},
        "duration": round(time.time() - t0, 1),
        "samples": samples,
        "verdict": verdict,
        "first_recovery_sec": recovered_at,
        "late_off_events": late_off_events,
        "recovery_events": recovery_events,
        "keeper_log": keeper_log,
        "conclusion": conclusion,
    }
    JSON_OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1),
                        encoding="utf-8")

    lines = ["# 电视重启 · ADB 状态实测", "",
             "- 时间：%s" % payload["time"],
             "- 设备：%s（MiTV-MFTP0 / alita / Android 9）" % TARGET,
             "- 是否下发重启：%s" % ("是" if payload["reboot_sent"] else "否（只观察）"),
             "- 观察时长：%.0f 秒，采样 %d 次" % (payload["duration"], len(samples)),
             "", "## 基线", "",
             "```", json.dumps(payload["baseline"], ensure_ascii=False), "```", "",
             "## 结论", "", "**[%s] %s**" % (verdict, conclusion), "",
             "## 掉线 / 自愈事件", "",
             "- 长时间掉线起点（秒）：%s" % (", ".join(str(x) for x in late_off_events) or "无"),
             "- 自行恢复点（秒）：%s" % (", ".join(str(x) for x in recovery_events) or "无"),
             "", "## 电视端 AdbKeeper 日志（本次开机）", "", "```",
             (keeper_log or "（未取到日志）")[-4000:], "```", "",
             "## 时间线（节选）", "",
             "| 秒 | ping | 5555 | adb 状态 | adb_enabled |",
             "|---:|:---:|:---:|---|---|"]
    # 状态变化点 + 首尾各留几行，避免表格太长
    picked = []
    prev = None
    for i, s in enumerate(samples):
        key = (s["ping"], s["port"], s["state"], s.get("adb_enabled", ""))
        if i < 3 or i >= len(samples) - 3 or key != prev:
            picked.append(s)
        prev = key
    for s in picked[:60]:
        lines.append("| %.1f | %s | %s | %s | %s |" % (
            s["t"], "通" if s["ping"] else "断",
            "开" if s["port"] else "关", s["state"] or "-",
            s.get("adb_enabled", "-")))
    MD_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("已写入 %s 和 %s" % (JSON_OUT.name, MD_OUT.name))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
