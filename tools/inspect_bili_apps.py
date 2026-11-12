# -*- coding: utf-8 -*-
"""核实电视上所有 B 站类客户端的真实应用名与最近使用时间。

用户口中的「云视听小电视」未必等于 com.bilibili.tv，用 aapt2 读 APK 的
application-label，再用 usagestats 看谁真的被打开过，避免名单配错。
"""
import json
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
ENV = json.loads((ROOT / "toolchain" / "env.json").read_text(encoding="utf-8"))
CONF = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
ADB = ENV["adb"]
AAPT = ENV["aapt2"]
TARGET = CONF["tv_ip"]
TMP = ROOT / "tmp_labels"
TMP.mkdir(exist_ok=True)

KEY = ("bili", "xiaodianshi", "yst", "chinasoul", "cat3399",
       "aaa1115", "cibn", "cloudtv", "xmtv", "b23")


def shell(cmd, timeout=60):
    p = subprocess.run([ADB, "-s", TARGET, "shell", cmd],
                       capture_output=True, timeout=timeout)
    return p.stdout.decode("utf-8", "replace").strip()


def main():
    subprocess.run([ADB, "connect", TARGET], capture_output=True, timeout=25)
    listed = shell("pm list packages")
    pkgs = [l.split(":", 1)[1].strip() for l in listed.splitlines()
            if l.startswith("package:")]
    cand = [p for p in pkgs if any(k in p.lower() for k in KEY)]
    print("=" * 78)
    print("电视上 B 站类客户端共 %d 个" % len(cand))
    print("当前配置 bili_packages = %s" % CONF["bili_packages"])
    print("=" * 78)

    usage = shell("dumpsys usagestats", timeout=90).splitlines()

    for p in cand:
        path = shell("pm path " + p).replace("package:", "").splitlines()
        label = "(读不到)"
        ver = ""
        if path:
            local = TMP / (p.replace(".", "_") + ".apk")
            subprocess.run([ADB, "-s", TARGET, "pull", path[0], str(local)],
                           capture_output=True, timeout=180)
            if local.exists():
                out = subprocess.run([AAPT, "dump", "badging", str(local)],
                                     capture_output=True, timeout=90)
                txt = out.stdout.decode("utf-8", "replace")
                for l in txt.splitlines():
                    if l.startswith("application-label:"):
                        label = l.split(":", 1)[1].strip().strip("'")
                        break
                    if "versionName=" in l and not ver:
                        i = l.find("versionName='")
                        ver = l[i + 13:].split("'")[0] if i >= 0 else ""
        last = "-"
        for l in usage:
            if ("package=" + p + " ") in l and "lastTime=" in l:
                last = l.strip().split("lastTime=")[-1].split(" ")[0].strip('"')
        print("包名 : %s" % p)
        print("名称 : %s   版本 %s" % (label, ver))
        print("最近使用 : %s   %s" % (last, "  <== 配置中" if p in CONF["bili_packages"] else ""))
        print("-" * 78)

    print()
    print("当前前台：", shell("dumpsys activity activities | grep mResumedActivity | head -n 1"))


if __name__ == "__main__":
    main()
