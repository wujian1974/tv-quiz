# -*- coding: utf-8 -*-
"""构建电视端答题 APK（无 Gradle）：aapt2 -> javac -> jar -> d8 -> zipalign -> apksigner。

产物 tv-quiz/apk/tvquiz.apk，题库内置到 assets/quiz_bank.json。
界面只做一件事：显示一道四选一，用遥控器方向键移焦点、确定键作答。
计时与 B 站检测由电脑端守护脚本负责；本 APK 另带开机自恢复：
小米电视重启约一分钟后会把 ADB 调试关掉，AdbKeeper 收到开机广播后分多次
把 adb_enabled 写回 1，并每 5 分钟自检，让 5555 端口自己回来，守护即可重连。
为此申请 WRITE_SECURE_SETTINGS（需 adb pm grant 授予，见 tools/setup_adb_keeper.py）。
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

ROOT = Path(__file__).resolve().parents[1]
TC = ROOT / "toolchain"
CFG = json.loads((TC / "env.json").read_text(encoding="utf-8"))
JDK = Path(CFG["JAVA_HOME"])
SDK = Path(CFG["ANDROID_SDK"])
BT = SDK / "build-tools" / "34.0.0"
ANDROID_JAR = SDK / "platforms" / "android-34" / "android.jar"
W = ROOT / "apk"
SMOKE = ROOT / "apk-smoke"

ENV = os.environ.copy()
ENV["JAVA_HOME"] = str(JDK)
ENV["PATH"] = str(JDK / "bin") + os.pathsep + ENV.get("PATH", "")

MANIFEST = '''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.wb.tvquiz" android:versionCode="4" android:versionName="1.3">
  <uses-sdk android:minSdkVersion="23" android:targetSdkVersion="34" />
  <uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED" />
  <uses-permission android:name="android.permission.WRITE_SECURE_SETTINGS" />
  <uses-feature android:name="android.software.leanback" android:required="false" />
  <uses-feature android:name="android.hardware.touchscreen" android:required="false" />
  <application android:label="错题小测" android:allowBackup="false"
      android:debuggable="true">
    <activity android:name=".QuizActivity" android:exported="true"
        android:configChanges="keyboard|keyboardHidden|navigation"
        android:showWhenLocked="true" android:turnScreenOn="true">
      <intent-filter>
        <action android:name="android.intent.action.MAIN" />
        <category android:name="android.intent.category.LAUNCHER" />
      </intent-filter>
    </activity>
    <receiver android:name=".AdbKeeper" android:exported="true" android:enabled="true">
      <intent-filter>
        <action android:name="android.intent.action.BOOT_COMPLETED" />
        <action android:name="android.intent.action.QUICKBOOT_POWERON" />
        <action android:name="com.miui.intent.action.BOOT_COMPLETED" />
        <action android:name="android.intent.action.MY_PACKAGE_REPLACED" />
        <action android:name="com.wb.tvquiz.ADB_KEEP" />
        <action android:name="com.wb.tvquiz.ADB_SELFTEST" />
        <action android:name="com.wb.tvquiz.ADB_BOOTTEST" />
      </intent-filter>
    </receiver>
  </application>
</manifest>
'''

ADBKEEPER = r'''package com.wb.tvquiz;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.Build;
import android.os.SystemClock;
import android.provider.Settings;
import android.util.Log;

import java.io.FileOutputStream;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

/** 开机后把 ADB 调试开关写回 1，保证 5555 端口能自己回来。 */
public class AdbKeeper extends BroadcastReceiver {

    private static final String TAG = "TVQuizAdb";
    public static final String ACTION_KEEP = "com.wb.tvquiz.ADB_KEEP";
    public static final String ACTION_SELFTEST = "com.wb.tvquiz.ADB_SELFTEST";

    @Override
    public void onReceive(Context c, Intent i) {
        String act = (i == null) ? "" : String.valueOf(i.getAction());
        log(c, "onReceive action=" + act);
        if (ACTION_SELFTEST.equals(act)) {
            selftest(c);
        } else {
            checkAndFix(c, "trigger=" + act);
        }
        boolean boot = Intent.ACTION_BOOT_COMPLETED.equals(act)
                || "android.intent.action.QUICKBOOT_POWERON".equals(act)
                || "com.miui.intent.action.BOOT_COMPLETED".equals(act)
                || "android.intent.action.MY_PACKAGE_REPLACED".equals(act)
                || "com.wb.tvquiz.ADB_BOOTTEST".equals(act);
        if (boot) {
            // 实测：开机初期 adbd 会起来约一分钟，随后又被停掉。分多次补写覆盖这个窗口。
            schedule(c, 20);
            schedule(c, 60);
            schedule(c, 120);
            schedule(c, 180);
        }
        // 链式自检：只要本类被触发过一次，就会一直续下去，不单靠开机广播。
        schedule(c, 300);
    }

    /** 答题页每次启动都续一次命；守护每 5 分钟弹题 = 每 5 分钟续一次。 */
    public static void kick(Context c) {
        log(c, "kick from QuizActivity");
        checkAndFix(c, "quiz-start");
        schedule(c, 300);
    }

    public static void checkAndFix(Context c, String why) {
        int before = read(c);
        if (before == 1) {
            log(c, why + " | adb_enabled=1 已开启，无需修复");
            return;
        }
        // 已实测：把开关写成 0 后，写回 1 会让 adbd 自己重启、5555 自动恢复。
        // 这里只走 Java Settings API（已 pm grant WRITE_SECURE_SETTINGS）；
        // 应用 uid 执行 settings 命令会被 SELinux 拒绝，不做无用尝试。
        boolean api = false;
        try {
            Settings.Global.putInt(c.getContentResolver(),
                    Settings.Global.ADB_ENABLED, 1);
            api = true;
        } catch (Throwable e) {
            log(c, "putInt FAILED: " + e);
        }
        log(c, why + " | FIX before=" + before + " putInt=" + api
                + " after=" + read(c));
    }

    /** 不改状态，只验证权限够不够、广播通不通。 */
    private static void selftest(Context c) {
        boolean api = false;
        try {
            Settings.Global.putInt(c.getContentResolver(),
                    Settings.Global.ADB_ENABLED, 1);
            api = true;
        } catch (Throwable e) {
            log(c, "SELFTEST putInt FAILED: " + e);
        }
        log(c, "SELFTEST | read=" + read(c) + " putInt=" + api
                + " | putInt=true 表示 WRITE_SECURE_SETTINGS 已授予");
    }

    private static int read(Context c) {
        try {
            return Settings.Global.getInt(c.getContentResolver(),
                    Settings.Global.ADB_ENABLED, -1);
        } catch (Throwable e) {
            log(c, "read FAILED: " + e);
            return -1;
        }
    }

    private static void schedule(Context c, int seconds) {
        try {
            AlarmManager am = (AlarmManager) c.getSystemService(Context.ALARM_SERVICE);
            Intent it = new Intent(ACTION_KEEP).setPackage(c.getPackageName());
            int flags = PendingIntent.FLAG_UPDATE_CURRENT;
            if (Build.VERSION.SDK_INT >= 23) {
                flags |= PendingIntent.FLAG_IMMUTABLE;
            }
            PendingIntent pi = PendingIntent.getBroadcast(c, seconds, it, flags);
            long at = SystemClock.elapsedRealtime() + seconds * 1000L;
            if (Build.VERSION.SDK_INT >= 23) {
                am.setExactAndAllowWhileIdle(AlarmManager.ELAPSED_REALTIME_WAKEUP, at, pi);
            } else {
                am.setExact(AlarmManager.ELAPSED_REALTIME_WAKEUP, at, pi);
            }
            log(c, "schedule +" + seconds + "s");
        } catch (Throwable e) {
            log(c, "schedule FAILED: " + e);
        }
    }

    private static void log(Context c, String msg) {
        String line = new SimpleDateFormat("MM-dd HH:mm:ss", Locale.US)
                .format(new Date()) + " | " + msg;
        Log.i(TAG, line);
        try {
            FileOutputStream fos = c.openFileOutput("adb_keeper.log", Context.MODE_APPEND);
            fos.write((line + "\n").getBytes("UTF-8"));
            fos.close();
        } catch (Throwable ignored) {
        }
    }
}
'''

ACTIVITY = r'''package com.wb.tvquiz;

import android.app.Activity;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.os.Handler;
import android.text.TextUtils;
import android.util.Log;
import android.view.Gravity;
import android.view.KeyEvent;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Random;

/** 电视端答题页：四个大按钮、遥控器可操作、答完显示解析后自动关闭。 */
public class QuizActivity extends Activity {

    private static final String TAG = "TVQuiz";
    private static final String[] KEY = {"A", "B", "C", "D"};
    private static final int BG = 0xFF10182A;
    private static final int BTN_OFF = 0xFF1E2C46;
    private static final int BTN_FOCUS = 0xFF2D7FF9;
    private static final int GREEN = 0xFF1B8A5A;
    private static final int RED = 0xFFB93A32;

    private final Handler handler = new Handler();
    private final Button[] buttons = new Button[4];
    private TextView feedback;
    private boolean answered = false;
    private int rightIdx = 0;
    private String qid = "";
    private String stem = "";
    private String session = "";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        AdbKeeper.kick(this);   // 顺手给 ADB 自恢复续命，不改变界面
        session = getIntent().getStringExtra("q_session");
        if (session == null) session = "";
        final boolean gate = getIntent().getBooleanExtra("gate", false);
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().setFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN,
                WindowManager.LayoutParams.FLAG_FULLSCREEN);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(BG);
        root.setPadding(dp(52), dp(20), dp(52), dp(18));
        setContentView(root, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.MATCH_PARENT));

        TextView tag = new TextView(this);
        tag.setTextColor(0xFF8FA3C2);
        tag.setTextSize(18);
        tag.setSingleLine(true);
        tag.setLayoutParams(new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, dp(28)));
        root.addView(tag);

        TextView stemView = new TextView(this);
        stemView.setTextColor(Color.WHITE);
        stemView.setGravity(Gravity.CENTER_VERTICAL);
        stemView.setMaxLines(6);
        stemView.setEllipsize(TextUtils.TruncateAt.END);
        stemView.setLineSpacing(dp(4), 1.0f);
        stemView.setLayoutParams(new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, 0, 2.0f));
        root.addView(stemView);

        feedback = new TextView(this);
        feedback.setTextColor(0xFF8FA3C2);
        feedback.setTextSize(19);
        feedback.setMaxLines(4);
        feedback.setEllipsize(TextUtils.TruncateAt.END);
        feedback.setGravity(Gravity.CENTER_VERTICAL);
        feedback.setText(gate ? "先选一个答案，才能继续看节目" : "方向键选答案，确定键作答");
        feedback.setLayoutParams(new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, 0, 1.4f));

        LinearLayout optionBox = new LinearLayout(this);
        optionBox.setOrientation(LinearLayout.VERTICAL);
        optionBox.setLayoutParams(new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, dp(282)));
        root.addView(optionBox);

        for (int i = 0; i < 4; i++) {
            final Button b = new Button(this);
            b.setAllCaps(false);
            b.setTextColor(Color.WHITE);
            b.setGravity(Gravity.CENTER_VERTICAL | Gravity.LEFT);
            b.setPadding(dp(24), dp(4), dp(24), dp(4));
            b.setMaxLines(2);
            b.setEllipsize(TextUtils.TruncateAt.END);
            b.setFocusable(true);
            b.setFocusableInTouchMode(false);
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT, dp(66));
            if (i > 0) lp.topMargin = dp(6);
            optionBox.addView(b, lp);
            buttons[i] = b;
        }

        // 视觉顺序：题目标签 → 题干 → 四个选项 → 反馈解析
        root.addView(feedback);

        try {
            JSONArray bank = new JSONArray(readAsset("quiz_bank.json"));
            int idx = getIntent().getIntExtra("q_index", -1);
            if (idx < 0 || idx >= bank.length()) idx = pick(bank);
            JSONObject q = bank.getJSONObject(idx);
            qid = q.optString("id", "unknown");
            stem = q.optString("stem", "");
            String subject = q.optString("subject", "");
            String level = q.optBoolean("open_ended", false) ? "开放题" : "四选一";

            String unit = q.optString("unit", "");
            tag.setText((gate ? "先答题再看节目" : "错题小测") + "　·　" + subject
                    + (unit.length() > 0 ? "　·　" + unit : "")
                    + "　·　" + level + "　·　" + qid);
            stemView.setText(stem);
            stemView.setTextSize(fontSize(stem.length(), 30, 26, 22, 40, 70));

            JSONArray ja = q.getJSONArray("options");
            List<String> opts = new ArrayList<String>();
            for (int i = 0; i < ja.length() && i < 4; i++) opts.add(ja.getString(i));
            String correct = opts.get(q.getInt("answer_index"));
            Collections.shuffle(opts, new Random());
            rightIdx = opts.indexOf(correct);
            String explain = q.optString("explain", "");

            for (int i = 0; i < 4; i++) {
                final int pick = i;
                String text = KEY[i] + "　" + opts.get(i);
                buttons[i].setText(text);
                buttons[i].setTextSize(fontSize(opts.get(i).length(), 26, 22, 19, 16, 30));
                paint(buttons[i], false);
                buttons[i].setOnFocusChangeListener(new View.OnFocusChangeListener() {
                    public void onFocusChange(View v, boolean hasFocus) {
                        if (!answered) paint((Button) v, hasFocus);
                    }
                });
                buttons[i].setOnClickListener(new View.OnClickListener() {
                    public void onClick(View v) { answer(pick, correct, explain); }
                });
            }
            buttons[0].requestFocus();
        } catch (Exception e) {
            Log.e(TAG, "load failed", e);
            stemView.setText("题库读取失败：" + e.getMessage());
        }
    }

    private void answer(int picked, String correct, String explain) {
        if (answered) return;
        answered = true;
        boolean ok = picked == rightIdx;
        for (int i = 0; i < 4; i++) {
            buttons[i].setEnabled(false);
            GradientDrawable g = new GradientDrawable();
            g.setCornerRadius(dp(10));
            if (i == rightIdx) g.setColor(GREEN);
            else if (i == picked) g.setColor(RED);
            else g.setColor(BTN_OFF);
            buttons[i].setBackground(g);
        }

        String head = ok ? "答对了！　" : "答错了，正确答案是 " + KEY[rightIdx] + "　";
        String tail = explain.length() > 0 ? "\n" + explain : "";
        feedback.setText(head + tail);
        feedback.setTextColor(ok ? 0xFF7BE0A8 : 0xFFFFC7A1);
        feedback.setTextSize(19);

        SharedPreferences sp = getSharedPreferences("quiz_stats", MODE_PRIVATE);
        SharedPreferences.Editor ed = sp.edit();
        ed.putLong(qid + "_last", System.currentTimeMillis());
        ed.putInt(qid + "_wrong", sp.getInt(qid + "_wrong", 0) + (ok ? 0 : 1));
        ed.putInt("total", sp.getInt("total", 0) + 1);
        ed.putInt("right", sp.getInt("right", 0) + (ok ? 1 : 0));
        ed.apply();

        Log.i(TAG, "RESULT|id=" + qid + "|picked=" + KEY[picked]
                + "|right=" + KEY[rightIdx] + "|correct=" + (ok ? 1 : 0)
                + "|session=" + session
                + "|stem=" + stem.replace("\n", " "));

        Toast.makeText(this, ok ? "答对啦" : "再想想，看看解析", Toast.LENGTH_SHORT).show();
        handler.postDelayed(new Runnable() {
            public void run() { finish(); }
        }, ok ? 6000 : 10000);
    }

    @Override
    public boolean onKeyDown(int code, KeyEvent event) {
        if (code == KeyEvent.KEYCODE_BACK) {
            if (answered) { finish(); return true; }
            Toast.makeText(this, "先选一个答案哦", Toast.LENGTH_SHORT).show();
            return true;
        }
        if (answered && (code == KeyEvent.KEYCODE_ENTER
                || code == KeyEvent.KEYCODE_DPAD_CENTER
                || code == KeyEvent.KEYCODE_NUMPAD_ENTER)) {
            finish();
            return true;
        }
        return super.onKeyDown(code, event);
    }

    @Override
    protected void onDestroy() {
        handler.removeCallbacksAndMessages(null);
        super.onDestroy();
    }

    private void paint(Button b, boolean focused) {
        GradientDrawable g = new GradientDrawable();
        g.setColor(focused ? BTN_FOCUS : BTN_OFF);
        g.setCornerRadius(dp(10));
        g.setStroke(dp(3), focused ? 0xFF9FD0FF : 0xFF33456A);
        b.setBackground(g);
        b.setTextColor(Color.WHITE);
    }

    private int pick(JSONArray bank) throws Exception {
        SharedPreferences sp = getSharedPreferences("quiz_stats", MODE_PRIVATE);
        long now = System.currentTimeMillis();
        Random r = new Random();
        double best = -1;
        int bestIndex = 0;
        for (int i = 0; i < bank.length(); i++) {
            String id = bank.getJSONObject(i).optString("id", "");
            int wrong = sp.getInt(id + "_wrong", 0);
            long last = sp.getLong(id + "_last", 0L);
            double days = last == 0 ? 30 : Math.min((now - last) / 86400000.0, 30);
            double score = 1 + wrong * 2.0 + days * 0.5 + r.nextDouble();
            if (score > best) { best = score; bestIndex = i; }
        }
        return bestIndex;
    }

    private String readAsset(String name) throws Exception {
        InputStream in = getAssets().open(name);
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        byte[] buf = new byte[4096];
        int n;
        while ((n = in.read(buf)) > 0) out.write(buf, 0, n);
        in.close();
        return out.toString("UTF-8");
    }

    private int dp(float v) {
        return (int) (v * getResources().getDisplayMetrics().density + 0.5f);
    }

    private static int fontSize(int len, int big, int mid, int small, int t1, int t2) {
        if (len <= t1) return big;
        if (len <= t2) return mid;
        return small;
    }
}
'''


def run(args):
    print("  $", " ".join(str(a) for a in args[:3]), "...", flush=True)
    return subprocess.run(args, check=True, env=ENV,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          text=True, encoding="utf-8", errors="replace")


def bat(name, args):
    return run(["cmd.exe", "/c", str(BT / name)] + [str(a) for a in args])


def build_bank():
    src = ROOT / "questions.json"
    data = json.loads(src.read_text(encoding="utf-8"))
    keep = ("id", "subject", "stem", "options", "answer_index",
            "explain", "opt_from", "open_ended", "level", "unit")
    bank = []
    for q in data["questions"]:
        if not q.get("enabled"):
            continue
        bank.append({k: q[k] for k in keep if k in q})
    assets = W / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    (assets / "quiz_bank.json").write_text(
        json.dumps(bank, ensure_ascii=False, indent=1), encoding="utf-8")
    print("题库内置:", len(bank), "道 ->", assets / "quiz_bank.json")
    return len(bank)


def main():
    for p in (ANDROID_JAR, BT / "aapt2.exe", BT / "d8.bat", BT / "apksigner.bat"):
        assert p.exists(), "缺文件: " + str(p)

    if W.exists():
        shutil.rmtree(W)
    src = W / "src" / "com" / "wb" / "tvquiz"
    cls, dex = W / "classes", W / "dex"
    src.mkdir(parents=True)
    cls.mkdir()
    dex.mkdir()
    (W / "AndroidManifest.xml").write_text(MANIFEST, encoding="utf-8")
    (src / "QuizActivity.java").write_text(ACTIVITY, encoding="utf-8")
    (src / "AdbKeeper.java").write_text(ADBKEEPER, encoding="utf-8")
    build_bank()

    print("[1/8] aapt2 link（含 assets 题库）")
    run([str(BT / "aapt2.exe"), "link", "-o", str(W / "base.apk"),
         "-I", str(ANDROID_JAR), "--manifest", str(W / "AndroidManifest.xml"),
         "-A", str(W / "assets"),
         "--min-sdk-version", "23", "--target-sdk-version", "34"])

    print("[2/8] javac")
    run([str(JDK / "bin" / "javac.exe"), "-encoding", "UTF-8",
         "-source", "8", "-target", "8", "-Xlint:-options",
         "-classpath", str(ANDROID_JAR), "-d", str(cls),
         str(src / "QuizActivity.java"), str(src / "AdbKeeper.java")])

    print("[3/8] jar")
    run([str(JDK / "bin" / "jar.exe"), "cf", str(W / "classes.jar"),
         "-C", str(cls), "."])

    print("[4/8] d8")
    bat("d8.bat", ["--lib", ANDROID_JAR, "--min-api", "23",
                   "--output", dex, W / "classes.jar"])

    print("[5/8] 合入 classes.dex + zipalign")
    with zipfile.ZipFile(W / "base.apk", "a") as z:
        z.write(dex / "classes.dex", "classes.dex")
    run([str(BT / "zipalign.exe"), "-f", "4",
         str(W / "base.apk"), str(W / "aligned.apk")])

    print("[6/8] 复用签名密钥")
    ks = W / "tvquiz.keystore"
    if (SMOKE / "debug.keystore").exists():
        shutil.copy2(SMOKE / "debug.keystore", ks)
    else:
        run([str(JDK / "bin" / "keytool.exe"), "-genkeypair",
             "-keystore", str(ks), "-storepass", "android", "-keypass", "android",
             "-alias", "androiddebugkey", "-keyalg", "RSA", "-keysize", "2048",
             "-validity", "10000", "-dname", "CN=TVQuiz, OU=WB, O=WB, C=CN"])

    print("[7/8] apksigner 签名")
    bat("apksigner.bat", ["sign", "--ks", ks,
                          "--ks-pass", "pass:android", "--key-pass", "pass:android",
                          "--out", W / "tvquiz.apk", W / "aligned.apk"])

    print("[8/8] 校验签名与 assets")
    bat("apksigner.bat", ["verify", "--verbose", W / "tvquiz.apk"])
    with zipfile.ZipFile(W / "tvquiz.apk") as z:
        names = z.namelist()
        assert "assets/quiz_bank.json" in names, "题库没被打进 APK"
        assert "classes.dex" in names, "dex 缺失"
        bank = json.loads(z.read("assets/quiz_bank.json").decode("utf-8"))
        expected = sum(1 for q in json.loads(
            (ROOT / "questions.json").read_text(encoding="utf-8"))["questions"]
            if q.get("enabled"))
        assert len(bank) == expected, "题库数量不对: %d vs %d" % (len(bank), expected)
    apk = W / "tvquiz.apk"
    print("-" * 60)
    print("构建完成:", apk, "|", apk.stat().st_size, "bytes | 内置", len(bank), "道题")
    print("安装: adb -s <电视IP>:5555 install -r", apk)
    print("启动: adb shell am start -n com.wb.tvquiz/.QuizActivity --ei q_index 0")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print("FAILED:", e.cmd)
        print(e.stdout or "")
        sys.exit(1)
