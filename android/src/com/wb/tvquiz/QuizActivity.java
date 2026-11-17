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
