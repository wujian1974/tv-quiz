# -*- coding: utf-8 -*-
"""真机联调「进门先答题」：启动守护 → 切进云视听小电视 → 模拟遥控器作答。

验证点：
  1. 切进云视听小电视时立刻弹题，题目标签写「先答题再看节目」
  2. RESULT 日志带 session，守护脚本能按 session 抓到并写入 answer_log.jsonl
  3. 答题页关闭、回到播放界面后自动发播放键续播
  4. 测试结束把电视切回原来的应用，不留下停在别处的画面
"""
import json
import subprocess
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
DAEMON_LOG = ROOT / "gate_test_daemon.log"


def answer_bot():
    deadline = time.time() + 60
    while time.time() < deadline:
        if t.foreground_activity() == "com.wb.tvquiz":
            time.sleep(2.0)
            print("[bot] 答题页出现，方向键下 ×2 + 确定键", flush=True)
            t.shell("input keyevent 20")
            time.sleep(0.35)
            t.shell("input keyevent 20")
            time.sleep(0.35)
            t.shell("input keyevent 66")
            print("[bot] 已作答", flush=True)
            return True
        time.sleep(0.8)
    print("[bot] 超时：没等到答题页", flush=True)
    return False


def last_records():
    if not d.ANSWERS.exists():
        return []
    return [json.loads(x) for x in d.ANSWERS.read_text(encoding="utf-8").strip().splitlines()]


def main():
    if not d.connect():
        print("电视不在线")
        return 3
    orig = d.foreground()
    print("测试前前台 =", orig, "| 是否在监测名单 =", orig in d.BILI_PACKAGES, flush=True)
    before = len(last_records())

    cmd = [sys.executable, str(HERE / "tv_quiz_daemon.py"),
           "--fast", "9999", "--poll", "2"]
    logf = DAEMON_LOG.open("w", encoding="utf-8")
    proc = subprocess.Popen(cmd, stdout=logf, stderr=subprocess.STDOUT,
                            cwd=str(ROOT))
    print("守护已启动 pid=%d，日志 %s" % (proc.pid, DAEMON_LOG.name), flush=True)
    time.sleep(5)

    bot = threading.Thread(target=answer_bot, daemon=True)
    bot.start()

    print("切进云视听小电视（com.bilibili.tv）…", flush=True)
    out = d.shell("monkey -p com.bilibili.tv -c android.intent.category.LAUNCHER 1")
    print("  ", out.strip()[:160], flush=True)
    time.sleep(2)
    print("当前前台 =", d.foreground(), flush=True)

    deadline = time.time() + 55
    rec = None
    while time.time() < deadline:
        rows = last_records()
        if len(rows) > before:
            rec = rows[-1]
            break
        time.sleep(1)
    bot.join(timeout=3)

    print("=" * 66, flush=True)
    if rec:
        print("抓到作答记录：", json.dumps(
            {k: rec.get(k) for k in ("time", "id", "trigger", "session",
                                     "picked", "right", "correct")},
            ensure_ascii=False), flush=True)
    else:
        print("没抓到作答记录", flush=True)

    # 等答题页关闭、守护发出续播键
    time.sleep(12)
    proc.terminate()
    try:
        proc.wait(timeout=8)
    except subprocess.TimeoutExpired:
        proc.kill()
    logf.close()
    dl = DAEMON_LOG.read_text(encoding="utf-8", errors="replace")
    print("-" * 66, flush=True)
    for line in dl.splitlines():
        if any(k in line for k in ("守护启动", "进入云视听", "闸门题", "答题结果",
                                   "闸门通过", "播放键", "拉回前台", "没抓到")):
            print(" ", line, flush=True)
    print("-" * 66, flush=True)

    gate_ok = bool(rec and rec.get("trigger") == "gate" and rec.get("session"))
    resume_ok = "已发播放键" in dl
    print("进门闸门生效 =", gate_ok, "| 自动续播已发 =", resume_ok, flush=True)

    # 别把电视留在别的应用上
    if orig and orig not in ("", "com.wb.tvquiz"):
        d.shell("monkey -p %s -c android.intent.category.LAUNCHER 1" % orig)
        print("已切回原应用:", orig, flush=True)
    return 0 if gate_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
