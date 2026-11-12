# -*- coding: utf-8 -*-
"""端到端联调：在真实 B 站前台下，走一遍 计时→弹题→遥控器作答→记录→恢复。"""
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


def answer_bot():
    """模拟小朋友：等答题页出现，按两下方向键再按确定。"""
    deadline = time.time() + 45
    while time.time() < deadline:
        if t.foreground_activity() == "com.wb.tvquiz":
            time.sleep(2.5)
            print("[bot] 答题页已出现，方向键下 ×2 + 确定键", flush=True)
            t.shell("input keyevent 20")
            time.sleep(0.4)
            t.shell("input keyevent 20")
            time.sleep(0.4)
            t.shell("input keyevent 66")
            print("[bot] 已作答", flush=True)
            return True
        time.sleep(1)
    print("[bot] 超时：没等到答题页", flush=True)
    return False


def main():
    if not d.connect():
        print("电视不在线")
        return 3

    fg = d.foreground()
    print("当前前台 =", fg, "| 判定在看 B 站 =", fg in d.BILI_PACKAGES)
    bank = d.load_bank()
    print("题库 =", len(bank), "道")
    if not bank:
        return 1

    before = d.ANSWERS.read_text(encoding="utf-8").count("\n") if d.ANSWERS.exists() else 0

    th = threading.Thread(target=answer_bot, daemon=True)
    th.start()
    print("--- 触发弹题（模拟计时已满）---", flush=True)
    ok = d.pop_quiz(bank, {}, 0, timeout_sec=70)
    th.join(timeout=5)

    after = d.ANSWERS.read_text(encoding="utf-8").count("\n") if d.ANSWERS.exists() else 0
    print("=" * 60)
    print("弹题闭环结果 =", ok, "| 新增答题记录 =", after - before, "条")
    print("答完后的前台 =", d.foreground())
    if d.ANSWERS.exists():
        print("最后一条记录:", d.ANSWERS.read_text(encoding="utf-8").strip().splitlines()[-1])
    return 0 if ok and after > before else 2


if __name__ == "__main__":
    raise SystemExit(main())
