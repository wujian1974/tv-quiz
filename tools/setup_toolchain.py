# -*- coding: utf-8 -*-
"""安装 Android 工具链，全部落在 tv-quiz/toolchain 下，不写系统目录、不改注册表。

包含：platform-tools(adb)、Microsoft OpenJDK 17、Android SDK 命令行工具，
再用 sdkmanager 装 platforms;android-34 与 build-tools;34.0.0。
"""
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent / "toolchain"
DL = ROOT / "_downloads"
SDK = ROOT / "android-sdk"
ROOT.mkdir(parents=True, exist_ok=True)
DL.mkdir(exist_ok=True)
SDK.mkdir(exist_ok=True)

SOURCES = {
    "platform-tools.zip": "https://dl.google.com/android/repository/platform-tools-latest-windows.zip",
    "jdk17.zip": "https://repo.huaweicloud.com/openjdk/17/openjdk-17_windows-x64_bin.zip",
    "cmdline-tools.zip": "https://dl.google.com/android/repository/commandlinetools-win-11076708_latest.zip",
}


def log(*a):
    print(*a, flush=True)


def fetch(name, url):
    dst = DL / name
    if dst.exists() and zipfile.is_zipfile(dst):
        log(f"[skip] {name} 已下载 {dst.stat().st_size // 1048576} MB")
        return dst
    if dst.exists():
        log(f"[clean] 删掉上次没下完的 {name}")
        dst.unlink()
    part = DL / (name + ".part")
    if part.exists():
        part.unlink()
    log(f"[get ] {name} <- {url}")
    subprocess.run(
        ["curl.exe", "-sS", "-L", "--fail", "--retry", "3", "--retry-delay", "2",
         "-o", str(part), url],
        check=True,
    )
    if not zipfile.is_zipfile(part):
        raise RuntimeError(f"{name} 不是完整 zip，下载中断了")
    part.replace(dst)
    log(f"[ok  ] {name} {dst.stat().st_size // 1048576} MB")
    return dst


def extract(zf, dest):
    dest.mkdir(parents=True, exist_ok=True)
    log(f"[unzip] {zf.name} -> {dest}")
    with zipfile.ZipFile(zf) as z:
        z.extractall(dest)


def main():
    pt = fetch("platform-tools.zip", SOURCES["platform-tools.zip"])
    jdk = fetch("jdk17.zip", SOURCES["jdk17.zip"])
    ct = fetch("cmdline-tools.zip", SOURCES["cmdline-tools.zip"])

    # platform-tools -> android-sdk/platform-tools
    if not (SDK / "platform-tools" / "adb.exe").exists():
        extract(pt, ROOT)
        shutil.move(str(ROOT / "platform-tools"), str(SDK / "platform-tools"))
    log("[ok  ] adb: " + str(SDK / "platform-tools" / "adb.exe"))

    # JDK -> toolchain/jdk
    jdk_home = ROOT / "jdk"
    if not (jdk_home / "bin" / "java.exe").exists():
        tmp = ROOT / "_jdtmp"
        if tmp.exists():
            shutil.rmtree(tmp)
        extract(jdk, tmp)
        src = next(p for p in tmp.iterdir() if (p / "bin" / "java.exe").exists())
        shutil.move(str(src), str(jdk_home))
        shutil.rmtree(tmp)
    log("[ok  ] JDK: " + str(jdk_home))

    # cmdline-tools -> android-sdk/cmdline-tools/latest
    latest = SDK / "cmdline-tools" / "latest"
    if not (latest / "bin" / "sdkmanager.bat").exists():
        tmp = SDK / "cmdline-tools" / "_tmp"
        if tmp.exists():
            shutil.rmtree(tmp)
        extract(ct, tmp)
        shutil.move(str(tmp / "cmdline-tools"), str(latest))
        shutil.rmtree(tmp)
    log("[ok  ] sdkmanager: " + str(latest / "bin" / "sdkmanager.bat"))

    # 预置许可，避免交互式询问
    lic = SDK / "licenses"
    lic.mkdir(exist_ok=True)
    (lic / "android-sdk-license").write_text(
        "8933bad161af4178b1185d1a37fbf41ea5269c55\n"
        "d56f5187479451eabf01fb78af6dfcb131a6481e\n", encoding="utf-8")
    (lic / "android-sdk-preview-license").write_text(
        "84831b9409646a918e30573bab4c9c91346e8\n", encoding="utf-8")

    env = os.environ.copy()
    env["JAVA_HOME"] = str(jdk_home)
    env["PATH"] = str(jdk_home / "bin") + os.pathsep + env.get("PATH", "")

    if not (SDK / "platforms" / "android-34" / "android.jar").exists() or \
       not (SDK / "build-tools" / "34.0.0" / "aapt2.exe").exists():
        log("[sdk ] 安装 platforms;android-34 与 build-tools;34.0.0 ...")
        subprocess.run(
            ["cmd.exe", "/c", str(latest / "bin" / "sdkmanager.bat"),
             f"--sdk_root={SDK}", "platforms;android-34", "build-tools;34.0.0"],
            env=env, input="y\ny\ny\ny\ny\n", text=True, check=True,
        )
    log("[ok  ] android.jar: " + str(SDK / "platforms" / "android-34" / "android.jar"))

    # 验证
    log("-" * 60)
    subprocess.run([str(SDK / "platform-tools" / "adb.exe"), "version"], check=True)
    subprocess.run([str(jdk_home / "bin" / "java.exe"), "-version"], check=True)
    checks = {
        "adb": SDK / "platform-tools" / "adb.exe",
        "java": jdk_home / "bin" / "java.exe",
        "android.jar": SDK / "platforms" / "android-34" / "android.jar",
        "aapt2": SDK / "build-tools" / "34.0.0" / "aapt2.exe",
        "d8": SDK / "build-tools" / "34.0.0" / "d8.bat",
        "apksigner": SDK / "build-tools" / "34.0.0" / "apksigner.bat",
        "zipalign": SDK / "build-tools" / "34.0.0" / "zipalign.exe",
    }
    for k, v in checks.items():
        log(f'{"OK " if v.exists() else "MISS"} {k}: {v}')

    (ROOT / "env.json").write_text(json.dumps(
        {"JAVA_HOME": str(jdk_home), "ANDROID_SDK": str(SDK), **{k: str(v) for k, v in checks.items()}},
        ensure_ascii=False, indent=2), encoding="utf-8")
    log("-" * 60)
    log("DONE 工具链路径记在 toolchain/env.json")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log("FAILED: " + repr(e))
        sys.exit(1)
