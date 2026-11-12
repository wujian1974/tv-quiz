# -*- coding: utf-8 -*-
"""验证「ADB 被关掉 -> 答题 APK 自己写回 -> 5555 自己回来」。

用法：
    python tools/test_adb_selfheal.py --alarms-only   # 只验闹钟能否触发（完全无风险）
    python tools/test_adb_selfheal.py                # 完整自愈实验

完整实验会把 settings global adb_enabled 写成 0（等同于在电视上关掉 ADB 调试），
**电视画面与播放完全不受影响**，只是电脑端 adb 会短暂断开。
随后靠 APK 的定时自检写回 1，电脑端用纯 socket 探测 5555 是否自己恢复。
若最终没恢复，只需到电视 设置→帐号与安全→ADB调试 再打开一次即可。

结果写入 tv-quiz/adb_selfheal.md / .json。
"""
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
sys.path.insert(0, str(ROOT / "tools"))
import tv_quiz_daemon as d  # noqa: E402

PKG = "com.wb.tvquiz"
RECV = PKG + "/.AdbKeeper"
_TARGET, _, _PORT = d.CONF["tv_ip"].partition(":")
IP = _TARGET
PORT = int(_PORT or 5555)
REPORT_MD = ROOT / "adb_selfheal.md"
REPORT_JSON = ROOT / "adb_selfheal.json"


def sh(cmd, timeout=40):
    try:
        return d.shell(cmd, timeout)
    except Exception as e:  # noqa: BLE001
        return "ERR:" + str(e)[:120]


def port_open(timeout=0.8):
    s = socket.socket()
    s.settimeout(timeout)
    try:
        s.connect((IP, PORT))
        return True
    except Exception:
        return False
    finally:
        s.close()


def tag_log():
    return sh("logcat -d -s TVQuizAdb:I")


def keeper_log():
    return sh("run-as " + PKG + " cat files/adb_keeper.log")


def boot_broadcast():
    return sh("am broadcast -a com.wb.tvquiz.ADB_BOOTTEST -n " + RECV + " -f 32")


def main():
    alarms_only = "--alarms-only" in sys.argv
    res = {"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
           "mode": "alarms-only" if alarms_only else "full", "tv": IP}
    d.connect()
    print("=== 阶段 A：定时自检闹钟能否在这台电视上触发 ===")
    sh("logcat -c")
    print("BOOTTEST 广播 =", boot_broadcast().strip()[:200])
    t0 = time.time()
    print("等待 26 秒（20 秒闹钟应在此时触发）...")
    time.sleep(26)
    lg = tag_log()
    fired = "trigger=com.wb.tvquiz.ADB_KEEP" in lg
    print("--- TVQuizAdb 日志 ---")
    print(lg[-1500:] or "(空)")
    print("20 秒闹钟已触发 =", fired)
    res["alarm_fired"] = fired
    res["alarm_log"] = lg[-2000:]

    if alarms_only or not fired:
        res["verdict"] = "ALARM_OK" if fired else "ALARM_BLOCKED"
        write_reports(res, [
            "## ADB 自恢复：闹钟验证",
            "",
            "- 时间：" + res["time"],
            "- 20 秒自检闹钟触发：**" + ("是" if fired else "否") + "**",
            "- 结论：" + ("APK 的定时自检在电视上能正常运行。" if fired else
                        "闹钟被系统的后台/停止状态策略挡住了，需改用开机后由守护主动唤醒。"),
        ])
        return 0 if fired else 5

    print("=== 阶段 B：把 ADB 开关写 0，看能否自己回来 ===")
    print("（电视画面不受影响；若没回来，最后需要你在电视上手动打开一次 ADB 调试）")
    boot_broadcast()          # 重新排 20/60/120/180 秒闹钟
    time.sleep(2)
    before = sh("settings get global adb_enabled").strip()
    print("写入前 adb_enabled =", before)
    res["adb_before"] = before
    # 这条命令执行后 adbd 通常会立刻停掉，adb 连接随之断开，属预期
    print("写 0 =", sh("settings put global adb_enabled 0", timeout=12).strip()[:200])
    t1 = time.time()
    down_seen = False
    recovered_at = None
    while time.time() - t1 < 200:
        time.sleep(3)
        op = port_open()
        if not op:
            down_seen = True
        elif down_seen and op:
            recovered_at = round(time.time() - t1, 1)
            break
        if int(time.time() - t1) % 30 == 0:
            print("  +%.0fs  5555=%s" % (time.time() - t1, "开放" if op else "关闭"))
    print("端口曾断开 =", down_seen, "| 自行恢复耗时 =", recovered_at, "秒")
    res["port_went_down"] = down_seen
    res["recovered_seconds"] = recovered_at

    # 端口刚恢复的那一两秒 adbd 还没就绪，settings 会返回空串；
    # 必须重试读回，否则会把「已经修好」误判成失败。
    after, kl, tagl = "", "", ""
    for attempt in range(5):
        time.sleep(2)
        subprocess.run([d.ADB, "connect", d.TARGET],
                       capture_output=True, timeout=25)
        after = sh("settings get global adb_enabled").strip()
        kl = keeper_log()
        tagl = tag_log()
        print("  读回第 %d 次：adb_enabled=%r，FIX 记录=%s"
              % (attempt + 1, after, "FIX" in kl))
        if after.strip() == "1" and "FIX" in kl:
            break
    res["adb_after"] = after
    res["fix_log"] = [l for l in kl.splitlines() if "FIX" in l or "kick" in l][-12:]
    res["keeper_log_tail"] = kl[-1500:]
    print("最终 adb_enabled =", after)
    print("--- 修复记录 ---")
    for l in res["fix_log"]:
        print("  ", l)

    ok = bool(down_seen and recovered_at is not None and after.strip() == "1")
    res["verdict"] = "SELF_HEAL_OK" if ok else "SELF_HEAL_FAILED"
    lines = [
        "## ADB 自恢复实测",
        "",
        "- 时间：" + res["time"],
        "- 20 秒自检闹钟触发：**是**",
        "- 人为把 `adb_enabled` 写成 0 后，5555 端口确实断开：**" +
        ("是" if down_seen else "否（写 setting 未停掉 adbd，本次不构成有效验证）") + "**",
        "- 端口自行恢复：**" + (("是，耗时 %.1f 秒" % recovered_at) if recovered_at else "否") + "**",
        "- 最终 `adb_enabled` = `" + after + "`",
        "",
        "### 应用侧修复记录",
        "```",
    ]
    lines += res["fix_log"] or ["(无)"]
    lines += ["```", "", "### 结论", ""]
    if ok:
        lines.append("**验证通过**：电视之后再把 ADB 调试关掉，答题应用会自行写回，"
                     "5555 端口自动恢复，电脑端守护自动重连，进门闸门与 5 分钟计时题不会失效。")
    else:
        lines.append("**未通过**：需要到电视 设置→帐号与安全→ADB调试 手动打开一次；"
                     "并考虑改用「把闸门/计时搬进电视端 APK」的方案。")
    write_reports(res, lines)
    return 0 if ok else 6


def write_reports(res, lines):
    REPORT_JSON.write_text(json.dumps(res, ensure_ascii=False, indent=1),
                           encoding="utf-8")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("=" * 60)
    print("结论 =", res["verdict"])
    print("报告：", REPORT_MD, "|", REPORT_JSON)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # noqa: BLE001
        print("FAILED:", type(e).__name__, e)
        sys.exit(1)
