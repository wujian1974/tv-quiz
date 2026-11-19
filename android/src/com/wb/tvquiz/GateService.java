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
