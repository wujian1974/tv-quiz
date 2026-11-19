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
