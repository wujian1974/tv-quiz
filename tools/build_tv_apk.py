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
  <uses-permission android:name="android.permission.BIND_ACCESSIBILITY_SERVICE" />
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
    <service android:name=".GateService" android:exported="true"
        android:permission="android.permission.BIND_ACCESSIBILITY_SERVICE">
      <intent-filter>
        <action android:name="android.accessibilityservice.AccessibilityService" />
      </intent-filter>
      <meta-data android:name="android.accessibilityservice"
          android:resource="@xml/accessibility_service_config" />
    </service>
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

# 无障碍服务静态配置：关键是 canRetrieveWindowContent=true，
# 否则系统给服务的 capabilities=0，getRootInActiveWindow() 永远返回 null。
ACCESSIBILITY_XML = '''<?xml version="1.0" encoding="utf-8"?>
<accessibility-service xmlns:android="http://schemas.android.com/apk/res/android"
    android:accessibilityEventTypes="typeWindowStateChanged"
    android:accessibilityFlags="flagIncludeNotImportantViews|flagRetrieveInteractiveWindows"
    android:canRetrieveWindowContent="true"
    android:notificationTimeout="0" />
'''

ADBKEEPER = r'''
package com.wb.tvquiz;

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
    // 小米私有全局键「直接播放信号源」(One Touch Play)：外接设备(HDMI 功放)一通电/有信号，
    // 电视就自动切到那个 HDMI 口。开机时系统会把它写回 1，导致画面卡在 HDMI 输入源界面、
    // 把 Aerial 桌面顶掉。这里在电视端开机阶段就锁成 0，不依赖电脑守护(开机断线期它瞎着)。
    private static final String KEY_AUTO_SWITCH = "mitv.settings.db.video.auto_switch";

    @Override
    public void onReceive(Context c, Intent i) {
        String act = (i == null) ? "" : String.valueOf(i.getAction());
        log(c, "onReceive action=" + act);
        // 门禁已搬到电视端本地无障碍服务 GateService。开机后必须确保它仍被启用，
        // 否则开机阶段 ADB 断线时就没门禁了。和 ADB 开关一样，分多次触发补写，
        // 覆盖开机初期系统可能把设置清掉的窗口。
        ensureGateAccessibility(c);
        ensureAutoSwitchOff(c);   // 锁住「直接播放信号源」为 0，防开机切到 HDMI 界面
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
        // 关键：开机/待机唤醒后是本方法（QuizActivity 裸启动）被触发，而不是
        // BOOT_COMPLETED 广播。此前这里只恢复 ADB 开关，漏了门禁无障碍服务，
        // 导致门禁服务被系统清掉后开机不恢复 —— 必须在这里也补写。
        ensureGateAccessibility(c);
        ensureAutoSwitchOff(c);   // 待机唤醒走 kick 路径，这里也要锁 auto_switch
        checkAndFix(c, "quiz-start");
        // 开机后 Aerial 桌面守护会重新注册无障碍服务，可能把门禁从列表里挤掉。
        // 20/60 秒再补写两次，覆盖这个窗口；链式 300 秒继续兜底。
        schedule(c, 20);
        schedule(c, 60);
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

    /**
     * 确保电视端门禁无障碍服务被启用。
     * 只往 enabled_accessibility_services 里追加自己的组件，绝不覆盖 Aerial 桌面守护、
     * 语音、karaoke 等其它服务（它们是冒号分隔的多个组件）。用 Settings.Secure API
     * （已授予 WRITE_SECURE_SETTINGS），不用 settings 命令（会被 SELinux 拒绝）。
     */
    private static void ensureGateAccessibility(Context c) {
        String key = Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES;
        String self = c.getPackageName() + "/.GateService";
        try {
            String cur = Settings.Secure.getString(c.getContentResolver(), key);
            if (cur == null) cur = "";
            if (cur.contains("com.wb.tvquiz/.GateService")
                    || cur.contains("com.wb.tvquiz/com.wb.tvquiz.GateService")) {
                log(c, "门禁无障碍服务已在启用列表，无需重复写");
            } else {
                String next = cur.isEmpty() ? self : cur + ":" + self;
                Settings.Secure.putString(c.getContentResolver(), key, next);
                log(c, "已追加门禁无障碍服务: " + self);
            }
            Settings.Secure.putInt(c.getContentResolver(),
                    Settings.Secure.ACCESSIBILITY_ENABLED, 1);
        } catch (Throwable e) {
            log(c, "ensureGateAccessibility FAILED: " + e);
        }
    }

    /**
     * 把小米私有键「直接播放信号源」锁成 0：HDMI 上的设备(功放)通电/有信号时，
     * 电视不再自动切到那个 HDMI 口，从而保住 Aerial 桌面。
     * 这是纯设置写入，不动 CEC 总开关、不动 eARC，功放照常联动开机、声音照常回传。
     * 值和电脑守护保持一致用字符串 "0"（该键在小米上是字符串类型）。
     */
    public static void ensureAutoSwitchOff(Context c) {
        try {
            String cur = Settings.Global.getString(c.getContentResolver(), KEY_AUTO_SWITCH);
            if ("0".equals(cur)) return;   // 已经是 0，不写、不刷日志
            Settings.Global.putString(c.getContentResolver(), KEY_AUTO_SWITCH, "0");
            String after = Settings.Global.getString(c.getContentResolver(), KEY_AUTO_SWITCH);
            log(c, "auto_switch 锁回 0 | before=" + cur + " after=" + after);
        } catch (Throwable e) {
            log(c, "ensureAutoSwitchOff FAILED: " + e);
        }
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

ACTIVITY = r'''
package com.wb.tvquiz;

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
    private boolean localGate = false;   // 本地门禁服务弹的题，答完要回写状态
    private boolean gateKind = false;    // true=进门题 false=计时题

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        AdbKeeper.kick(this);   // 顺手给 ADB 自恢复续命，不改变界面
        // 只有守护带着 q_index 拉起时才是真正的出题；开机的 6095 通道只传包名、
        // 裸启动本应用（目的是触发 AdbKeeper 写回 ADB 开关），这种情况不弹题、
        // 直接结束，避免「一开机就让你做题」。桌面图标手动点开同理。
        if (!getIntent().hasExtra("q_index")) {
            Log.i(TAG, "silent launch (no q_index): ADB keeper only, no quiz UI");
            finish();
            return;
        }
        session = getIntent().getStringExtra("q_session");
        if (session == null) session = "";
        final boolean gate = getIntent().getBooleanExtra("gate", false);
        gateKind = gate;
        localGate = getIntent().getBooleanExtra("local_gate", false);
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

        // 本地门禁：答完即放行（对错都算，符合「答完才能看」的约定），
        // 写回 gate_state，GateService 据此恢复播放并开始 3 分钟计时。
        if (localGate) {
            SharedPreferences gs = getSharedPreferences("gate_state", MODE_PRIVATE);
            gs.edit()
              .putBoolean("gate_ok", true)
              .putLong("last_quiz_ms", System.currentTimeMillis())
              .putString("last_qid", qid)
              .apply();
            Log.i(TAG, "本地门禁状态已回写：gate_ok=true, last_quiz_ms=now");
        }

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
        if (localGate) {
            try { GateService.notifyQuizClosed(this); } catch (Throwable ignored) {}
        }
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

GATESERVICE = r'''
package com.wb.tvquiz;

import android.accessibilityservice.AccessibilityService;
import android.accessibilityservice.AccessibilityServiceInfo;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Handler;
import android.util.Log;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;

/**
 * 本地门禁服务（主动轮询版）。
 *
 * 完全在电视端判断「进云视听先答题、每 3 分钟一道题」，不依赖电脑守护和 ADB，
 * 所以开机后 ADB 断线的那几十秒也能拦住。
 *
 * 2026-11-17 修正：小米电视不给无障碍服务派发云视听的 TYPE_WINDOW_STATE_CHANGED
 * 事件（实测服务 connected 后打开云视听，onAccessibilityEvent 一次都没被调用）。
 * 故改为在定时器里主动调用 getRootInActiveWindow() / getWindows() 查询前台窗口包名，
 * 只要服务活着就能识别云视听，不再依赖事件派发。
 */
public class GateService extends AccessibilityService {

    private static final String TAG = "TVQuizGate";
    private static final String PKG_BILI = "com.xiaodianshi.tv.yst";
    private static final String PKG_SELF = "com.wb.tvquiz";
    private static final String PKG_MITV_HOME = "com.xiaomi.eetv.home";  // 小米桌面 + HDMI 输入源界面同包
    private static final String PKG_AERIAL = "app.orchard.tv";           // Aerial 桌面，到了就是成功
    private static final String PREFS = "gate_state";
    private static final long INTERVAL_MS = 3 * 60 * 1000L;   // 3 分钟计时题
    private static final long LEAVE_GRACE_MS = 8000L;         // 离开宽限，过滤播放器切屏抖动
    // 开机回桌面自愈：开机后若卡在小米桌面/信号源界面（HDMI 2 接功放，开机常被 CEC
    // 拉到 InputsPlayerActivity 全屏），用户又没主动打开任何应用，就按 HOME 让 Aerial
    // 接管。看片时前台是云视听/BT/直播的包，不等于 PKG_MITV_HOME，永不触发。
    private static final long BOOT_HOME_WINDOW_MS = 6 * 60 * 1000L;  // 仅服务重连后 6 分钟内看护
    private static final long STUCK_MS = 20000L;                      // 连续停留 20 秒才算卡住
    private static final long HOME_COOLDOWN_MS = 15000L;             // 两次 HOME 间隔
    private static final int MAX_BOOT_HOME = 3;                       // 最多按 3 次，防死循环

    private final Handler handler = new Handler();
    private String currentFront = "";
    private long lastSeenBili = 0L;
    private long lastPopup = 0L;
    private boolean quizOnScreen = false;
    private int ticks = 0;
    // 开机自愈状态
    private long bootWindowStart = 0L;
    private long stuckSince = 0L;
    private long lastBootHome = 0L;
    private int bootHomeCount = 0;
    private boolean bootHomeDone = false;
    private String otherFront = "";      // 连续出现的非桌面包（判定用户是否真在看片）
    private int otherFrontTicks = 0;
    private long awaySince = 0L;         // 离开小米桌面包的起始时刻，用于容忍抖动

    private final Runnable ticker = new Runnable() {
        @Override
        public void run() {
            try { onTick(); } catch (Throwable t) { Log.e(TAG, "tick error", t); }
            // 电视端持续锁住「直接播放信号源」=0：系统开机流程会把 auto_switch
            // 写回 1，这里是端上最后一道防线，不依赖电脑守护(开机断线期它连不上)。
            // AdbKeeper.ensureAutoSwitchOff 内部判断已是 0 就不写，开销极小。
            if (ticks % 4 == 0) {   // 每 4 个 tick ≈ 12 秒复查一次，和电脑守护节奏一致
                try { AdbKeeper.ensureAutoSwitchOff(GateService.this); }
                catch (Throwable t) { Log.e(TAG, "auto_switch recheck error", t); }
            }
            handler.postDelayed(this, 3000);   // 每 3 秒轮询一次前台窗口
        }
    };

    @Override
    protected void onServiceConnected() {
        super.onServiceConnected();
        // 服务的能力/eventTypes 全部由 res/xml/accessibility_service_config.xml 静态声明，
        // 关键是不能在这里调用 setServiceInfo()——那会用代码里的 info 覆盖 XML 配置，
        // 导致系统判定 capabilities=0、getRootInActiveWindow() 永远返回 null。
        Log.i(TAG, "GateService connected (主动轮询版), watching " + PKG_BILI);

        // 关键修复：服务每次 connected（开机/待机唤醒后都会重新连接）时，清掉上一次
        // 会话遗留的门禁状态。否则昨晚答完题 gate_ok=true 会跨夜保留，今早开机进
        // 云视听被当成「已答过」直接放行——正是用户反馈的开机后不弹题。开机就是新
        // 的一次观看，必须重新答进门题。
        getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                .edit().putBoolean("gate_ok", false).apply();
        currentFront = "";        // 重置前台标记，让下次进入云视听能触发 onEnterBili
        lastSeenBili = 0L;
        lastPopup = 0L;
        quizOnScreen = false;
        // 开机自愈窗口从服务重连这一刻算起（小米电视深度待机 uptime 不归零，
        // 每次 connected 就是一次新会话/唤醒，正是要重新看护的时机）。
        bootWindowStart = System.currentTimeMillis();
        stuckSince = 0L;
        lastBootHome = 0L;
        bootHomeCount = 0;
        bootHomeDone = false;
        otherFront = "";
        otherFrontTicks = 0;
        awaySince = 0L;
        Log.i(TAG, "已清除跨会话门禁状态，下次进云视听需重新答进门题");
        Log.i(TAG, "开机回桌面看护窗口开启 " + (BOOT_HOME_WINDOW_MS / 1000) + "s");

        handler.post(ticker);
    }

    /** 主动查询前台窗口包名：活跃/聚焦窗口优先，取其根节点的 packageName。 */
    private String frontPkg() {
        String active = "";
        try {
            AccessibilityNodeInfo root = getRootInActiveWindow();
            if (root != null) {
                CharSequence p = root.getPackageName();
                if (p != null) active = p.toString();
            }
        } catch (Throwable t) {}

        // 反射枚举所有窗口，找活跃窗口的包名（stub android.jar 隐藏了 AccessibilityWindowInfo，
        // 只能用反射，运行时类仍然存在）。getRootInActiveWindow 有时拿不到自绘应用，靠这个兜底。
        try {
            java.lang.reflect.Method mGetWindows =
                    AccessibilityService.class.getMethod("getWindows");
            Object wins = mGetWindows.invoke(this);
            if (wins instanceof java.util.List) {
                java.util.List<?> list = (java.util.List<?>) wins;
                for (Object w : list) {
                    Object r = w.getClass().getMethod("getRoot").invoke(w);
                    if (r == null) continue;
                    Object pnObj = r.getClass().getMethod("getPackageName").invoke(r);
                    if (pnObj == null) continue;
                    String pn = pnObj.toString();
                    if (ticks % 3 == 0) {
                        Object activeObj = w.getClass().getMethod("isActive").invoke(w);
                        Object focusObj = w.getClass().getMethod("isFocused").invoke(w);
                        Log.i(TAG, "win=" + pn + " active=" + activeObj
                                + " focused=" + focusObj);
                    }
                    Object activeObj = w.getClass().getMethod("isActive").invoke(w);
                    Object focusObj = w.getClass().getMethod("isFocused").invoke(w);
                    if (Boolean.TRUE.equals(activeObj) || Boolean.TRUE.equals(focusObj)) {
                        active = pn;
                    }
                }
            }
        } catch (Throwable t) {}
        return active;
    }

    private void onTick() {
        long now = System.currentTimeMillis();
        ticks++;
        String front = frontPkg();
        if (ticks % 2 == 0) {
            Log.i(TAG, "tick front=" + front + " cur=" + currentFront
                    + " quizOn=" + quizOnScreen);
        }
        if (front.isEmpty()) return;

        if (PKG_SELF.equals(front)) {
            quizOnScreen = true;
            return;
        }
        quizOnScreen = false;

        // 开机回桌面自愈（与门禁判断彼此独立）：开机/唤醒后若卡在小米桌面包，
        // 用户又没主动开任何应用，就按 HOME 让 Aerial 接管。看片时前台是别的包，
        // 永不触发。放在门禁弹题判断之前，互不干扰。
        maybeGoHome(front, now);

        if (PKG_BILI.equals(front)) {
            if (!PKG_BILI.equals(currentFront)) {
                Log.i(TAG, "enter Bili");
                onEnterBili();
            }
            currentFront = PKG_BILI;
            lastSeenBili = now;

            SharedPreferences sp = getSharedPreferences(PREFS, Context.MODE_PRIVATE);
            if (sp.getBoolean("gate_ok", false)) {
                long last = sp.getLong("last_quiz_ms", 0L);
                if (last > 0L && now - last >= INTERVAL_MS && now - lastPopup >= 10000L) {
                    Log.i(TAG, "计时题：距上次答题 " + ((now - last) / 1000) + " 秒");
                    popup(false);
                }
            }
        } else {
            if (PKG_BILI.equals(currentFront) && now - lastSeenBili >= LEAVE_GRACE_MS) {
                Log.i(TAG, "leave Bili -> " + front);
                onLeaveBili();
            }
            currentFront = front;
        }
    }

    /**
     * 开机回桌面自愈：只在「服务重连后的看护窗口内 + 前台连续卡在小米桌面包 +
     * 用户没主动打开任何应用」三个条件同时满足时，按 HOME 让 Aerial 接管桌面。
     *
     * 为什么设窗口：小米电视「关机」= 深度待机，开机时序是 小米桌面→功放界面→
     * Aerial，头 1-2 分钟会短暂经过信号源界面，这是正常的，不该按 HOME。只有
     * 卡住超过 20 秒才出手。窗口过了就不再管，避免白天正常使用被误触发。
     *
     * 为什么不误伤看片：看云视听/BT/直播时前台是各自的包，不是 PKG_MITV_HOME；
     * 一旦检测到这些「用户主动打开的应用」，立即永久结束本次看护。
     */
    private void maybeGoHome(String front, long now) {
        if (bootHomeDone) return;

        long elapsed = now - bootWindowStart;
        if (elapsed < 0L || elapsed > BOOT_HOME_WINDOW_MS) {
            bootHomeDone = true;
            Log.i(TAG, "开机看护结束：超出 " + (BOOT_HOME_WINDOW_MS / 1000) + "s 窗口");
            return;
        }

        boolean onMHome = PKG_MITV_HOME.equals(front);
        boolean onAerial = PKG_AERIAL.equals(front);

        if (onAerial) {
            // 已经到 Aerial 桌面，说明桌面起来了，看护成功结束。
            bootHomeDone = true;
            Log.i(TAG, "开机看护结束：已在 Aerial 桌面");
            return;
        }

        if (onMHome) {
            // 回到小米桌面包（HDMI 输入源界面 / Launcher）：视为仍在卡住状态。
            // 清掉「非桌面包」连续计数，重置离开计时。
            otherFront = "";
            otherFrontTicks = 0;
            awaySince = 0L;
            if (stuckSince == 0L) stuckSince = now;
        } else {
            // 非桌面包：云视听/BT/直播/其它。可能是后台窗口短暂冒头，也可能用户真打开了。
            // 连续 3 个 tick（约 9 秒）同一个包才算「用户真的在看」，避免一闪就放弃看护。
            if (front.equals(otherFront)) {
                otherFrontTicks++;
            } else {
                otherFront = front;
                otherFrontTicks = 1;
            }
            if (otherFrontTicks >= 3) {
                // 用户确实打开了应用并在看 → 永不干预，这是看片保护的核心。
                bootHomeDone = true;
                Log.i(TAG, "开机看护结束：用户已打开 " + front + "，不再按 HOME");
                return;
            }
            // 短暂冒头：容忍，但记录离开时刻。连续离开超过 9 秒也清零卡住计时，
            // 防止「桌面 12s + BT 冒头 3s + 桌面 12s」被误累积成 20s。
            if (awaySince == 0L) awaySince = now;
            if (now - awaySince >= 9000L) {
                stuckSince = 0L;
            }
            return;
        }

        // 走到这里 front 必是 PKG_MITV_HOME，且 awaySince 已清零。
        long dwell = now - stuckSince;
        if (dwell < STUCK_MS) return;   // 不足 20 秒，开机正常过渡

        if (now - lastBootHome < HOME_COOLDOWN_MS) return;   // 两次 HOME 冷却
        if (bootHomeCount >= MAX_BOOT_HOME) {
            bootHomeDone = true;
            Log.i(TAG, "开机看护结束：已按 " + bootHomeCount + " 次 HOME 仍未进 Aerial，停止");
            return;
        }
        bootHomeCount++;
        lastBootHome = now;
        stuckSince = now;   // 重新计连续停留，避免每 3 秒狂按
        Log.i(TAG, "开机自愈：卡在小米桌面/信号源界面 " + (dwell / 1000)
                + "s，按第 " + bootHomeCount + " 次 HOME 回桌面");
        try {
            performGlobalAction(AccessibilityService.GLOBAL_ACTION_HOME);
        } catch (Throwable t) {
            Log.e(TAG, "performGlobalAction(HOME) 失败", t);
        }
    }

    /** 进入云视听：没答过进门题就弹。 */
    private void onEnterBili() {
        SharedPreferences sp = getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        boolean gateOk = sp.getBoolean("gate_ok", false);
        if (!gateOk) {
            Log.i(TAG, "进门题：需要作答");
            popup(true);
        } else {
            Log.i(TAG, "进门已通过，放行（距上次答题 "
                    + ((System.currentTimeMillis() - sp.getLong("last_quiz_ms", 0L)) / 1000) + " 秒）");
        }
    }

    /** 离开云视听：清掉进门标记，下次进来要重新答。 */
    private void onLeaveBili() {
        getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                .edit().putBoolean("gate_ok", false).apply();
        Log.i(TAG, "离开云视听，进门标记已清除");
    }

    /** 弹题：把答题页盖到前台。gate=true 进门题，false 计时题。 */
    private void popup(boolean gate) {
        long now = System.currentTimeMillis();
        if (now - lastPopup < 10000L) {
            Log.i(TAG, "刚弹过题，跳过");
            return;
        }
        lastPopup = now;
        quizOnScreen = true;
        String session = "local-" + now;
        try {
            Intent it = new Intent(this, QuizActivity.class);
            it.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK
                    | Intent.FLAG_ACTIVITY_CLEAR_TOP
                    | Intent.FLAG_ACTIVITY_SINGLE_TOP);
            it.putExtra("q_index", -1);          // -1 = 答题页自己按错题优先挑
            it.putExtra("q_session", session);
            it.putExtra("gate", gate);
            it.putExtra("local_gate", true);     // 告诉答题页：答完要回写本地门禁状态
            startActivity(it);
            Log.i(TAG, "已弹" + (gate ? "进门" : "计时") + "题 session=" + session);
        } catch (Throwable t) {
            Log.e(TAG, "弹题失败", t);
            quizOnScreen = false;
        }
    }

    /** 答题页 finish 时调用：标记答题页已关闭、恢复云视听前台标记。 */
    public static void notifyQuizClosed(Context c) {
        if (sInstance != null) {
            sInstance.quizOnScreen = false;
            sInstance.lastSeenBili = System.currentTimeMillis();
            sInstance.currentFront = PKG_BILI;
            Log.i(TAG, "答题页关闭，恢复云视听前台标记");
        }
    }

    private static GateService sInstance;

    @Override
    public void onCreate() {
        super.onCreate();
        sInstance = this;
    }

    @Override
    public void onDestroy() {
        handler.removeCallbacksAndMessages(null);
        sInstance = null;
        super.onDestroy();
    }

    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {
        // 小米电视不派发云视听的窗口事件，这里只留空实现，状态判断全靠 onTick 主动轮询。
    }

    @Override
    public void onInterrupt() {
        Log.w(TAG, "onInterrupt");
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
    (src / "GateService.java").write_text(GATESERVICE, encoding="utf-8")
    # 无障碍服务静态配置（canRetrieveWindowContent=true 才能读前台窗口）
    xmlres = W / "res" / "xml"
    xmlres.mkdir(parents=True, exist_ok=True)
    (xmlres / "accessibility_service_config.xml").write_text(
        ACCESSIBILITY_XML, encoding="utf-8")
    build_bank()

    print("[1/8] aapt2 link（含 assets 题库 + 无障碍配置）")
    # 先把 res/xml 下的 xml 编译成 .flat
    flat = W / "compiled_flat"
    flat.mkdir(exist_ok=True)
    run([str(BT / "aapt2.exe"), "compile", "-o", str(flat),
         str(xmlres / "accessibility_service_config.xml")])
    run([str(BT / "aapt2.exe"), "link", "-o", str(W / "base.apk"),
         "-I", str(ANDROID_JAR), "--manifest", str(W / "AndroidManifest.xml"),
         "-A", str(W / "assets"),
         "-R", str(flat / "xml_accessibility_service_config.xml.flat"),
         "--min-sdk-version", "23", "--target-sdk-version", "34"])

    print("[2/8] javac")
    run([str(JDK / "bin" / "javac.exe"), "-encoding", "UTF-8",
         "-source", "8", "-target", "8", "-Xlint:-options",
         "-classpath", str(ANDROID_JAR), "-d", str(cls),
         str(src / "QuizActivity.java"), str(src / "AdbKeeper.java"),
         str(src / "GateService.java")])

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
