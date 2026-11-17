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
    private static final String PREFS = "gate_state";
    private static final long INTERVAL_MS = 3 * 60 * 1000L;   // 3 分钟计时题
    private static final long LEAVE_GRACE_MS = 8000L;         // 离开宽限，过滤播放器切屏抖动

    private final Handler handler = new Handler();
    private String currentFront = "";
    private long lastSeenBili = 0L;
    private long lastPopup = 0L;
    private boolean quizOnScreen = false;
    private int ticks = 0;

    private final Runnable ticker = new Runnable() {
        @Override
        public void run() {
            try { onTick(); } catch (Throwable t) { Log.e(TAG, "tick error", t); }
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
