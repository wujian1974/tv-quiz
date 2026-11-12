# -*- coding: utf-8 -*-
"""工具链冒烟测试：不依赖 Gradle，用 aapt2 + javac + d8 + apksigner 编出最小 APK。

编出来的是「答题界面占位」的空壳，仅用于证明这条链路通了；
正式 APK 会沿用同一套构建步骤，把界面换成读 questions.json 的答题页。
"""
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
TC = ROOT / "toolchain"
CFG = json.loads((TC / "env.json").read_text(encoding="utf-8"))
JDK = Path(CFG["JAVA_HOME"])
SDK = Path(CFG["ANDROID_SDK"])
BT = SDK / "build-tools" / "34.0.0"
ANDROID_JAR = SDK / "platforms" / "android-34" / "android.jar"
W = ROOT / "apk-smoke"

ENV = os.environ.copy()
ENV["JAVA_HOME"] = str(JDK)
ENV["PATH"] = str(JDK / "bin") + os.pathsep + ENV.get("PATH", "")

MANIFEST = '''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.wb.tvquiz" android:versionCode="1" android:versionName="1.0">
  <uses-sdk android:minSdkVersion="23" android:targetSdkVersion="34" />
  <application android:label="TVQuiz" android:allowBackup="false">
    <activity android:name=".QuizActivity" android:exported="true">
      <intent-filter>
        <action android:name="android.intent.action.MAIN" />
        <category android:name="android.intent.category.LAUNCHER" />
      </intent-filter>
    </activity>
  </application>
</manifest>
'''

ACTIVITY = '''package com.wb.tvquiz;
import android.app.Activity;
import android.os.Bundle;
import android.view.Gravity;
import android.widget.TextView;

public class QuizActivity extends Activity {
    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        TextView t = new TextView(this);
        t.setText("答题界面占位");
        t.setTextSize(36);
        t.setGravity(Gravity.CENTER);
        setContentView(t);
    }
}
'''


def run(args):
    print("  $", " ".join(str(a) for a in args[:4]), "...", flush=True)
    return subprocess.run(args, check=True, env=ENV,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


def bat(name, args):
    return run(["cmd.exe", "/c", str(BT / name)] + [str(a) for a in args])


def main():
    for p in (ANDROID_JAR, BT / "aapt2.exe", BT / "d8.bat", BT / "apksigner.bat"):
        assert p.exists(), f"缺文件: {p}"

    if W.exists():
        import shutil
        shutil.rmtree(W)
    src = W / "src" / "com" / "wb" / "tvquiz"
    cls = W / "classes"
    dex = W / "dex"
    src.mkdir(parents=True)
    cls.mkdir()
    dex.mkdir()
    (W / "AndroidManifest.xml").write_text(MANIFEST, encoding="utf-8")
    (src / "QuizActivity.java").write_text(ACTIVITY, encoding="utf-8")

    print("[1/7] aapt2 link 生成 APK 骨架")
    run([str(BT / "aapt2.exe"), "link", "-o", str(W / "base.apk"),
         "-I", str(ANDROID_JAR), "--manifest", str(W / "AndroidManifest.xml"),
         "--min-sdk-version", "23", "--target-sdk-version", "34"])

    print("[2/7] javac 编译 Activity")
    run([str(JDK / "bin" / "javac.exe"), "-encoding", "UTF-8",
         "-source", "8", "-target", "8", "-Xlint:-options",
         "-classpath", str(ANDROID_JAR), "-d", str(cls),
         str(src / "QuizActivity.java")])

    print("[3/7] 打 class jar")
    run([str(JDK / "bin" / "jar.exe"), "cf", str(W / "classes.jar"),
         "-C", str(cls), "."])

    print("[4/7] d8 转 dex")
    bat("d8.bat", ["--lib", ANDROID_JAR, "--min-api", "23",
                   "--output", dex, W / "classes.jar"])

    print("[5/7] 把 dex 装进 APK 并 zipalign")
    with zipfile.ZipFile(W / "base.apk", "a") as z:
        z.write(dex / "classes.dex", "classes.dex")
    run([str(BT / "zipalign.exe"), "-f", "4",
         str(W / "base.apk"), str(W / "aligned.apk")])

    print("[6/7] 生成签名密钥")
    run([str(JDK / "bin" / "keytool.exe"), "-genkeypair",
         "-keystore", str(W / "debug.keystore"),
         "-storepass", "android", "-keypass", "android",
         "-alias", "androiddebugkey", "-keyalg", "RSA", "-keysize", "2048",
         "-validity", "10000", "-dname", "CN=TVQuiz, OU=WB, O=WB, C=CN"])

    print("[7/7] 签名并校验")
    bat("apksigner.bat", ["sign", "--ks", W / "debug.keystore",
                          "--ks-pass", "pass:android", "--key-pass", "pass:android",
                          "--out", W / "tvquiz-smoke.apk", W / "aligned.apk"])
    bat("apksigner.bat", ["verify", "--verbose", W / "tvquiz-smoke.apk"])

    apk = W / "tvquiz-smoke.apk"
    print("-" * 60)
    print("编译链路通过，产物:", apk)
    print("大小:", apk.stat().st_size, "bytes")
    print("可以用 adb install 装到电视上做遥控器实测")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print("FAILED:", e.cmd)
        print(e.stdout or "")
        sys.exit(1)
