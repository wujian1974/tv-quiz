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

    @Override
    public void onReceive(Context c, Intent i) {
        String act = (i == null) ? "" : String.valueOf(i.getAction());
        log(c, "onReceive action=" + act);
        // 门禁已搬到电视端本地无障碍服务 GateService。开机后必须确保它仍被启用，
        // 否则开机阶段 ADB 断线时就没门禁了。和 ADB 开关一样，分多次触发补写，
        // 覆盖开机初期系统可能把设置清掉的窗口。
        ensureGateAccessibility(c);
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
