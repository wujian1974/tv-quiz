# -*- coding: utf-8 -*-
"""安装带开机自恢复的答题 APK、授予 WRITE_SECURE_SETTINGS、并做无风险自检。

用法：
    python tools/setup_adb_keeper.py

只做三件事：覆盖安装 -> pm grant -> 发一条自检广播读回日志。
自检把已经是 1 的 adb_enabled 再写一次 1，不改变电视状态、不弹界面、
不影响正在播放的画面，仅用来确认「应用真的有权限写系统设置」。

结果写入 tv-quiz/adb_keeper_setup.json，失败时返回非 0。
"""
import json
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
PERM = "android.permission.WRITE_SECURE_SETTINGS"
APK = ROOT / "apk" / "tvquiz.apk"
REPORT = ROOT / "adb_keeper_setup.json"


def host_adb(args, timeout=180):
    """在电脑端执行 adb 命令（不是 adb shell）。"""
    p = subprocess.run([d.ADB, "-s", d.TARGET] + list(args),
                       capture_output=True, timeout=timeout)
    return (p.stdout + p.stderr).decode("utf-8", "replace").strip()


def sh(cmd, timeout=40):
    return d.shell(cmd, timeout)


def main():
    report = {"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
              "package": PKG, "apk": str(APK)}
    print("=== 1. 连接电视 ===")
    d.connect()
    state = d.run(["get-state"])
    print("state =", state)
    report["state_before"] = state
    if state.strip() != "device":
        print("!! 电视未授权或未连上，先双击 check_adb.bat")
        REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=1),
                          encoding="utf-8")
        return 2

    print("=== 2. 覆盖安装新版 APK ===")
    assert APK.exists(), "找不到 " + str(APK)
    out = host_adb(["install", "-r", str(APK)])
    print(out[-600:])
    report["install"] = out[-600:]
    if "Success" not in out:
        print("!! 安装失败")
        REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=1),
                          encoding="utf-8")
        return 3

    print("=== 3. 授予 WRITE_SECURE_SETTINGS ===")
    grant = host_adb(["shell", "pm", "grant", PKG, PERM])
    print("pm grant =", grant or "(无输出，通常表示成功)")
    report["pm_grant"] = grant
    perm = sh("dumpsys package " + PKG + " | grep -A2 WRITE_SECURE_SETTINGS")
    print("权限状态 =", perm.strip()[:300] or "(dumpsys 未列出)")
    report["perm_dump"] = perm.strip()[:300]
    granted = "granted=true" in perm

    print("=== 4. 自检广播（不改状态，只验证权限与接收器）===")
    sh("logcat -c")
    bcast = sh("am broadcast -a com.wb.tvquiz.ADB_SELFTEST -n " + RECV + " -f 32")
    print("broadcast =", bcast.strip()[:300])
    time.sleep(2.0)
    taglog = sh("logcat -d -s TVQuizAdb:I")
    filelog = sh("run-as " + PKG + " cat files/adb_keeper.log")
    report["broadcast"] = bcast.strip()[:300]
    report["tag_log"] = taglog[-2000:]
    report["file_log"] = filelog[-2000:]
    print("--- logcat (TVQuizAdb) ---")
    print(taglog[-1200:] or "(空)")
    print("--- 应用私有日志 ---")
    print(filelog[-1200:] or "(空)")

    both = taglog + "\n" + filelog
    selftest_ok = "SELFTEST" in both and "putInt=true" in both
    receiver_ok = "SELFTEST" in both
    adb_now = sh("settings get global adb_enabled").strip()
    report.update({
        "receiver_ok": receiver_ok,
        "selftest_ok": selftest_ok,
        "granted": granted,
        "adb_enabled_after": adb_now,
        "verdict": "READY" if (selftest_ok and granted) else "CHECK",
    })
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=1),
                      encoding="utf-8")
    print("=" * 60)
    print("接收器能收到广播 =", receiver_ok)
    print("应用有权限写系统设置 =", selftest_ok)
    print("adb_enabled 当前值 =", adb_now)
    print("结论 =", report["verdict"], "| 报告:", REPORT)
    return 0 if selftest_ok and granted else 4


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # noqa: BLE001
        print("FAILED:", type(e).__name__, e)
        sys.exit(1)
