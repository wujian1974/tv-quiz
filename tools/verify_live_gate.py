# -*- coding: utf-8 -*-
"""验证「已经在运行的」守护进程的进门闸门，不另起第二个守护。

前提：tv_quiz_daemon.py 已在常驻运行（正式模式）。
动作：切进 config.json 里指定的 B 站客户端 → 等答题页出现 → 模拟遥控器作答
      → 检查 answer_log.jsonl 新增 gate 记录 → 检查自动续播 → 切回原应用。
"""
import argparse
import json
import sys
import threading
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import tv_quiz_daemon as d  # noqa: E402
import tv_remote_test as t  # noqa: E402

ROOT = HERE.parent


def records():
    if not d.ANSWERS.exists():
        return []
    return [json.loads(x) for x in
            d.ANSWERS.read_text(encoding="utf-8").strip().splitlines() if x.strip()]


def log_lines():
    p = ROOT / "daemon.log"
    if not p.exists():
        return []
    return p.read_text(encoding="utf-8", errors="replace").splitlines()


def answer_bot():
    deadline = time.time() + 45
    while time.time() < deadline:
        if t.foreground_activity() == "com.wb.tvquiz":
            time.sleep(1.6)
            print("[bot] 答题页出现 → 方向键下×2 + 确定键", flush=True)
            t.shell("input keyevent 20")
            time.sleep(0.35)
            t.shell("input keyevent 20")
            time.sleep(0.35)
            t.shell("input keyevent 66")
            print("[bot] 已作答", flush=True)
            return True
        time.sleep(0.6)
    print("[bot] 超时：没等到答题页", flush=True)
    return False


def one_round(n, pkg):
    """切进 B 站 → 等进门题 → 遥控器作答，返回是否弹了 gate 题。"""
    before = len(records())
    print("[第 %d 次] 切进云视听小电视 ..." % n, flush=True)
    bot = threading.Thread(target=answer_bot, daemon=True)
    bot.start()
    out = d.shell("monkey -p %s -c android.intent.category.LAUNCHER 1" % pkg)
    print("  ", out.strip()[:120], flush=True)

    rec = None
    deadline = time.time() + 50
    while time.time() < deadline:
        rows = records()
        if len(rows) > before:
            rec = rows[-1]
            break
        time.sleep(0.8)
    bot.join(timeout=3)

    gate_ok = bool(rec and rec.get("trigger") == "gate" and rec.get("session"))
    print("[第 %d 次] 进门题 = %s | %s" % (
        n, "弹了" if gate_ok else "没弹",
        json.dumps({k: rec.get(k) for k in ("time", "id", "trigger", "session")},
                   ensure_ascii=False) if rec else "无作答记录"), flush=True)
    return gate_ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rounds", type=int, default=1,
                    help="连续进出几次；>1 时中间回桌面等 12 秒，专门验证冷却期修复")
    args = ap.parse_args()

    if not d.connect():
        print("电视不在线")
        return 3
    pkg = d.BILI_PACKAGES[0]
    orig = d.foreground()
    log_start = len(log_lines())
    print("=" * 66, flush=True)
    print("目标客户端 =", pkg)
    print("测试前前台 =", orig, "| 在监测名单 =", orig in d.BILI_PACKAGES,
          "| 连续验证次数 =", args.rounds, flush=True)

    results = []
    for n in range(1, args.rounds + 1):
        round_start = len(log_lines())
        results.append(one_round(n, pkg))
        # 等答题页关闭、守护发播放键（守护轮询 3 秒，实测常在 10~15 秒后落日志）
        deadline = time.time() + 30
        while time.time() < deadline:
            if any("已发播放键" in l for l in log_lines()[round_start:]):
                break
            time.sleep(1)
        resume_ok = any("已发播放键" in l for l in log_lines()[round_start:])
        print("[第 %d 次] 自动续播 = %s | 现在前台 = %s"
              % (n, resume_ok, d.foreground()), flush=True)
        if n < args.rounds:
            print("  → 回桌面等 12 秒后重进（旧版会被 120 秒冷却挡掉）", flush=True)
            d.shell("input keyevent 3")
            time.sleep(12)

    print("-" * 66, flush=True)
    print("--- 守护日志（本次验证新增）---", flush=True)
    for l in log_lines()[log_start:][-20:]:
        print("  ", l, flush=True)
    all_ok = all(results)
    print("=" * 66, flush=True)
    print("每次进门都弹题 =", all_ok, "| 逐次 =", results, flush=True)

    if orig and orig not in ("", "com.wb.tvquiz", pkg):
        d.shell("monkey -p %s -c android.intent.category.LAUNCHER 1" % orig)
        print("已切回原应用:", orig, flush=True)
    return 0 if all_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
