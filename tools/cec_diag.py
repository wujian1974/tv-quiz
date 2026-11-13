"""诊断小米电视的 HDMI-CEC / 输入源状态（只读，不改任何设置）。

用法：python tools/cec_diag.py
输出写到 cec_diag.txt，并把关键信息打印到屏幕。
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADB = str(ROOT / "toolchain" / "android-sdk" / "platform-tools" / "adb.exe")
TARGET = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))["tv_ip"]

KEY_RE = ("hdmi", "cec", "source", "power", "wakeup", "standby", "one_touch", "earc", "arc")

CMDS = [
    ("global 设置", ["shell", "settings", "list", "global"]),
    ("system 设置", ["shell", "settings", "list", "system"]),
    ("secure 设置", ["shell", "settings", "list", "secure"]),
    ("HdmiControlService", ["shell", "dumpsys", "hdmi_control"]),
    ("TvInputManager", ["shell", "dumpsys", "tv_input"]),
    ("当前窗口焦点", ["shell", "dumpsys", "window", "windows"]),
    ("前台 Activity", ["shell", "dumpsys", "activity", "activities"]),
    ("输入设备", ["shell", "dumpsys", "input"]),
    ("系统属性(hdmi/cec)", ["shell", "getprop"]),
    ("相关包", ["shell", "pm", "list", "packages"]),
]


def sh(args, timeout=25):
    try:
        r = subprocess.run([ADB, "-s", TARGET] + args,
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout)
        return (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        return "ERR: %s\n" % e


def picked(text, keys, limit=60):
    out = []
    for line in text.splitlines():
        low = line.lower()
        if any(k in low for k in keys):
            out.append(line.rstrip())
            if len(out) >= limit:
                break
    return out


def main():
    state = sh(["get-state"]).strip()
    print("设备状态 =", state, flush=True)
    if state != "device":
        print("设备不在线，无法诊断", flush=True)
        return 2

    report = ["电视 HDMI-CEC 诊断", "=" * 70, ""]
    for name, args in CMDS:
        text = sh(args)
        report.append("## %s" % name)
        report.append("")
        if name.endswith("设置"):
            keys = KEY_RE
        elif name == "HdmiControlService":
            report.extend(text.splitlines()[:70])
            report.append("")
            continue
        elif name == "TvInputManager":
            report.extend(text.splitlines()[:60])
            report.append("")
            continue
        elif name in ("当前窗口焦点", "前台 Activity"):
            keys = ("mcurrentfocus", "mfocusedapp", "mresumedactivity",
                    "topresumedactivity", "resumedactivity")
        elif name == "输入设备":
            keys = ("hdmi", "cec", "tv_input")
        elif name.startswith("系统属性"):
            keys = ("hdmi", "cec", "earc", "audio")
        else:
            keys = ("tvinput", "hdmi", "cec", "mitv", "settings")
        hits = picked(text, keys)
        report.extend(hits if hits else ["（没有匹配项）"])
        report.append("")

    out = ROOT / "cec_diag.txt"
    out.write_text("\n".join(report), encoding="utf-8")
    print("已写入", out, flush=True)
    print("\n".join(report[:110]), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
