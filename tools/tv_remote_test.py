# -*- coding: utf-8 -*-
"""真机遥控器回归测试：安装/启动答题页，模拟方向键与确定键，截图并读回 UI 状态。

注意：这台小米电视的 shell wrapper 会在 exec-out 输出最前面塞一行
"Init wrapper sys..."，必须按 PNG / XML 魔数裁掉，否则截图和 dump 都会坏。
"""
import json
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / "toolchain" / "env.json").read_text(encoding="utf-8"))
ADB = CFG["adb"]
TARGET = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))["tv_ip"]
APK = ROOT / "apk" / "tvquiz.apk"
QUIZ_PKG = "com.wb.tvquiz"
QUIZ_ACT = QUIZ_PKG + "/.QuizActivity"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def raw_adb(args, timeout=40):
    return subprocess.run([ADB, "-s", TARGET] + args,
                          capture_output=True, timeout=timeout).stdout


def adb(args, timeout=40):
    p = subprocess.run([ADB, "-s", TARGET] + args,
                       capture_output=True, timeout=timeout)
    return p.stdout.decode("utf-8", "replace").strip()


def connect():
    out = subprocess.run([ADB, "connect", TARGET], capture_output=True,
                         timeout=25).stdout.decode("utf-8", "replace").strip()
    state = adb(["get-state"])
    print("connect:", out, "| state:", state)
    return state == "device"


def shell(cmd, timeout=40):
    return adb(["shell", cmd], timeout)


def foreground_activity():
    """用 mResumedActivity 判断，比 uiautomator dump 可靠：系统浮窗盖着也不受影响。"""
    out = shell("dumpsys activity activities | grep mResumedActivity | head -n 1")
    m = re.search(r"u0\s+([\w.]+)/", out)
    return m.group(1) if m else ""


def shot(name):
    data = raw_adb(["exec-out", "screencap", "-p"], timeout=45)
    i = data.find(PNG_MAGIC)
    if i < 0:
        print("!! 截图无效，开头:", repr(data[:100]))
        return None, 0
    data = data[i:]
    path = ROOT / name
    path.write_bytes(data)
    return path, len(data)


def dump_ui():
    shell("uiautomator dump /sdcard/wb_ui.xml")
    text = raw_adb(["exec-out", "cat /sdcard/wb_ui.xml"]).decode("utf-8", "replace")
    i = text.find("<?xml")
    if i < 0:
        i = text.find("<hierarchy")
    if i < 0:
        print("!! UI dump 无效，开头:", repr(text[:120]))
        return []
    try:
        root = ET.fromstring(text[i:])
    except ET.ParseError as e:
        print("!! UI dump 解析失败:", e)
        return []
    rows = []
    for node in root.iter("node"):
        t = node.get("text", "")
        if t:
            rows.append({
                "text": t,
                "class": node.get("class", "").split(".")[-1],
                "focused": node.get("focused", "false"),
                "bounds": node.get("bounds", ""),
            })
    return rows


def show(rows, title):
    print("--- " + title + " ---")
    for r in rows:
        mark = " [焦点]" if r["focused"] == "true" else ""
        print(" ", r["class"], "|", r["text"][:70].replace("\n", " "), mark)


def logs():
    text = shell("logcat -d -t 300", timeout=50)
    return [l.strip() for l in text.splitlines()
            if any(k in l for k in ("TVQuiz", "AndroidRuntime", "com.wb.tvquiz",
                                    "FATAL", "ActivityManager"))]


def main():
    if not connect():
        print("设备不可用：电视可能息屏了，请按一下遥控器唤醒，再重试。")
        return 3

    if "--no-install" not in sys.argv:
        print("install:", adb(["install", "-r", str(APK)], timeout=90))

    if "--no-start" not in sys.argv:
        shell("logcat -c")
        shell("am force-stop " + QUIZ_PKG)
        print("start:", shell("am start -n " + QUIZ_ACT + " --ei q_index 0"))
        time.sleep(2.5)

    fg = foreground_activity()
    print("前台 Activity:", fg)
    rows = dump_ui()
    show(rows, "启动后界面")
    p, n = shot("tv_shot.png")
    print("截图:", p, n, "bytes")

    if fg != QUIZ_PKG:
        print("!! 答题页不在前台，拒绝发送任何按键。相关日志：")
        for l in logs()[-30:]:
            print("  ", l)
        return 2

    if not any("错题小测" in r["text"] for r in rows):
        # 系统设置浮窗可能盖在上面。BACK 只会退出浮窗/被答题页拦截，不会切换开关，
        # 与上次误触开关的 DPAD+ENTER 不同，这是安全的。
        print("界面被浮窗遮挡，发一次返回键尝试关闭浮窗")
        shell("input keyevent 4")
        time.sleep(1.0)
        rows = dump_ui()
        show(rows, "返回键之后")
        shot("tv_shot_after_back.png")
        if not any("错题小测" in r["text"] for r in rows):
            print("!! 仍看不到答题页，拒绝发送方向键/确定键，避免误触系统开关")
            return 2

    if "--check-only" in sys.argv:
        print("--check-only：只读检查完成，未发送方向键/确定键")
        return 0

    for _ in range(2):
        shell("input keyevent 20")
        time.sleep(0.35)
    rows2 = dump_ui()
    focused2 = [r["text"][:24] for r in rows2 if r["focused"] == "true"]
    print("按两次方向键下 后的焦点:", focused2)
    p2, n2 = shot("tv_shot_focus.png")
    print("焦点态截图:", p2, n2, "bytes")

    shell("input keyevent 66")
    time.sleep(1.5)
    rows3 = dump_ui()
    show(rows3, "作答后界面")
    p3, n3 = shot("tv_shot_answer.png")
    print("作答截图:", p3, n3, "bytes")

    print("--- 关键日志 ---")
    for l in logs():
        if "RESULT" in l or "load failed" in l or "FATAL" in l:
            print(" ", l)
    print("前台 Activity(答完):", foreground_activity())

    # 电视上 uiautomator dump 有明显滞后（截图已变绿变红，dump 仍旧文本），
    # 所以以 logcat 的 RESULT 行为准，UI dump 只作参考。
    result_lines = [l for l in logs() if "RESULT|" in l]
    ui_hit = any("答对了" in r["text"] or "答错了" in r["text"] for r in rows3)
    hit = bool(result_lines) or ui_hit
    print("=" * 60)
    print("遥控器作答生效 =", hit, "(logcat RESULT", len(result_lines),
          "条, UI 反馈", ui_hit, ")")
    print("dump 读到的焦点仅供参考:", focused2)
    print("请以 tv_shot_answer.png 截图为准")
    return 0 if hit else 2


if __name__ == "__main__":
    raise SystemExit(main())
