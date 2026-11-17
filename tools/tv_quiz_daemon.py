# -*- coding: utf-8 -*-
"""电脑端守护脚本：盯着小米电视，进云视听小电视先答题，之后每 3 分钟再弹一道。

用法：
  python tools/tv_quiz_daemon.py                 正式跑（读 config.json）
  python tools/tv_quiz_daemon.py --dry-run      只观察前台和计时，不弹题
  python tools/tv_quiz_daemon.py --fast 30      演示模式：30 秒当作一轮
  python tools/tv_quiz_daemon.py --minutes 15   临时改成 15 分钟
  python tools/tv_quiz_daemon.py --no-gate     临时关掉进门题（联调用）

设计要点：
  - 只在云视听小电视处于前台时累计；退出停表，答题期间也停表。
  - 进门闸门：从别的应用切进云视听小电视，先弹一道题；没作答就反复把答题页
    拉回前台（返回键在 APK 里已被拦住，主页键也绕不过去），答完才放行。
  - 答完自动发播放键续播；电视息屏后网络 ADB 会断，脚本自动重连等待。
  - 答题结果按 logcat 标签 + session 抓，写进 answer_log.jsonl。
  - 断连超过 offline_alert_seconds 就报警：电视重启后若「ADB调试」被系统关掉，
    5555 端口根本不监听，电脑端再怎么重连也没用，此时闸门与计时题全部失效。
    告警写进 STATUS.json，并在 Windows 上弹一次气泡提示，避免静默失效。
"""
import argparse
import json
import random
import re
import socket
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
ENV = json.loads((ROOT / "toolchain" / "env.json").read_text(encoding="utf-8"))
CONF = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))

ADB = ENV["adb"]
TARGET = CONF["tv_ip"]
BILI_PACKAGES = tuple(CONF["bili_packages"])
QUIZ_PKG = "com.wb.tvquiz"
QUIZ_ACT = QUIZ_PKG + "/.QuizActivity"

GATE_REQUIRE_CORRECT = bool(CONF.get("gate_require_correct", False))
GATE_TIMEOUT = int(CONF.get("gate_timeout_seconds", 90))
GATE_COOLDOWN = int(CONF.get("gate_cooldown_seconds", 0))
GATE_LEAVE_GRACE = int(CONF.get("gate_leave_grace_seconds", 8))

# 辅助模式：门禁已完全搬到电视端 APK 的 GateService（本地无障碍服务），
# 不依赖 ADB，开机断线期也能拦住。电脑守护退居辅助，只保留 ADB 自愈、
# 6095 拉起、CEC 防切源和状态记录，不再弹任何题（否则和电视端重复弹题）。
ASSIST_ONLY = bool(CONF.get("tv_gate_full_control", False))
RESUME_AFTER = bool(CONF.get("resume_after_quiz", True))
PAUSE_ON_QUIZ = bool(CONF.get("pause_on_quiz", False))
OFFLINE_ALERT = int(CONF.get("offline_alert_seconds", 90))

# 小米/Redmi 电视自带的局域网控制服务（6095 端口），独立于 ADB。
# 电视开机把「ADB调试」关掉后，5555 不通但 6095 仍在线，可以用它把答题应用
# 拉起来 —— 应用一启动就会把 adb_enabled 写回 1，等于一条不依赖 ADB 的自愈通道。
ASSISTANT_BASE = "http://" + TARGET.split(":")[0] + ":6095"
REVIVE_ENABLED = bool(CONF.get("adb_revive_via_assistant", True))
REVIVE_AFTER = int(CONF.get("adb_revive_after_offline_seconds", 60))
REVIVE_RETRY = int(CONF.get("adb_revive_retry_seconds", 60))

# 防 CEC 自动切源：关掉「直接播放信号源」之后仍可能被功放切走，
# 重连后的一段时间内，发现活动源变成外部 HDMI 就自动回电视桌面。
CEC_GUARD = bool(CONF.get("cec_guard_enabled", True))
CEC_GUARD_WINDOW = int(CONF.get("cec_guard_after_reconnect_seconds", 600))
CEC_GUARD_POLL = int(CONF.get("cec_guard_poll_seconds", 12))
# 设置界面「通用设置 → 直接播放信号源」对应的全局键：关掉后外接设备开机
# 不再把画面切过去，但 CEC 总开关、ARC/eARC 音频和功放联动开机都保留。
CEC_AUTO_SWITCH_KEY = "mitv.settings.db.video.auto_switch"

LOG = ROOT / "daemon.log"
STATUS_FILE = ROOT / "STATUS.json"
ANSWERS = ROOT / "answer_log.jsonl"
BANK = ROOT / "apk" / "assets" / "quiz_bank.json"
HIST_FILE = ROOT / "quiz_history.json"


def note(msg):
    line = datetime.now().strftime("%H:%M:%S") + "  " + msg
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def single_instance_lock():
    """绑定本机端口做单实例锁：开机启动项 + 手动双击时不会跑出两个守护。

    返回 socket 对象（必须一直持有），已被占用则返回 None。
    dry-run 是观察模式，不抢锁。
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", 54789))
        s.listen(1)
        return s
    except OSError:
        s.close()
        return None


def set_status(state, msg):
    """把当前守护状态写给别的脚本/家长看，避免「连不上但没人知道」。"""
    payload = {
        "state": state,
        "message": msg,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tv": TARGET,
    }
    try:
        STATUS_FILE.write_text(
            json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass


def windows_toast(title, text):
    """非阻塞的 Windows 气泡提示；弹不出来就算了，不影响守护主循环。"""
    if sys.platform != "win32":
        return
    ps = (
        "Add-Type -AssemblyName System.Windows.Forms;"
        "$n=New-Object System.Windows.Forms.NotifyIcon;"
        "$n.Icon=[System.Drawing.SystemIcons]::Warning;"
        "$n.BalloonTipTitle='" + title.replace("'", "''") + "';"
        "$n.BalloonTipText='" + text.replace("'", "''") + "';"
        "$n.Visible=$true;$n.ShowBalloonTip(10000);"
        "Start-Sleep -Seconds 11;$n.Dispose()"
    )
    try:
        subprocess.Popen(
            ["powershell.exe", "-NoProfile", "-NonInteractive",
             "-WindowStyle", "Hidden", "-Command", ps],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except Exception:  # noqa: BLE001
        pass


def run(args, timeout=30):
    try:
        p = subprocess.run([ADB, "-s", TARGET] + args,
                           capture_output=True, timeout=timeout)
        return p.stdout.decode("utf-8", "replace").strip()
    except Exception as e:  # noqa: BLE001
        return "[ERR] " + str(e)


def connect():
    """每次轮询都重连一次：电视息屏会停 adbd，连接记录也会掉。"""
    try:
        subprocess.run([ADB, "connect", TARGET], capture_output=True, timeout=20)
        return run(["get-state"], timeout=15) == "device"
    except Exception:  # noqa: BLE001
        return False


def shell(cmd, timeout=30):
    return run(["shell", cmd], timeout)


_NO_PROXY_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def assistant_get(path, timeout=4):
    """请求电视 6095 控制接口；强制不走系统代理，失败返回空串。"""
    try:
        req = urllib.request.Request(
            ASSISTANT_BASE + path, headers={"User-Agent": "tv-quiz-daemon"})
        with _NO_PROXY_OPENER.open(req, timeout=timeout) as r:
            return r.read(4096).decode("utf-8", "replace")
    except Exception:  # noqa: BLE001
        return ""


def assistant_alive():
    return '"status":0' in assistant_get("/request?action=isalive", 3)


def revive_adb_via_assistant():
    """5555 不通时，靠 6095 拉起答题应用，由它把 ADB 开关写回 1。

    实测（2026-11-13）：开机后 5555 拒绝连接、6095 仍应答；
    发出 startapp 后 3 秒 adb_enabled=1、adbd=running。
    """
    if not assistant_alive():
        return False
    assistant_get("/controller?action=startapp&type=packagename&packagename="
                  + QUIZ_PKG, 5)
    return True


def ensure_cec_setting():
    """连上电视时确认「直接播放信号源」仍为关；被系统还原就写回去。"""
    if not CEC_GUARD:
        return
    cur = shell("settings get global " + CEC_AUTO_SWITCH_KEY, timeout=10).strip()
    if cur and cur != "0":
        shell("settings put global " + CEC_AUTO_SWITCH_KEY + " 0", timeout=10)
        note("「直接播放信号源」被还原为 %s，已重新关掉" % cur)


GATE_COMP = "com.wb.tvquiz/.GateService"


def ensure_gate_accessibility():
    """确保电视端门禁无障碍服务仍在启用列表；被系统清掉就写回，不覆盖其它服务。

    这是电视端 AdbKeeper 之外的第二道保险：辅助模式守护只要连上 ADB，就定期
    复查一次。开机待机唤醒时门禁服务可能被系统从启用列表移除，而那条路径走的
    是 QuizActivity.kick()（已在 APK 端修复）。这里再用 ADB 兜一层，双保险。
    """
    try:
        cur = shell("settings get secure enabled_accessibility_services",
                    timeout=10).strip()
        if GATE_COMP in cur:
            return
        # 只追加自己的组件，保留 Aerial 桌面、语音、karaoke 等其它服务
        nxt = (cur + ":" + GATE_COMP).strip(":")
        shell("settings put secure enabled_accessibility_services '%s'" % nxt,
              timeout=10)
        shell("settings put secure accessibility_enabled 1", timeout=10)
        note("门禁无障碍服务被清掉，已通过 ADB 写回（双保险）")
    except Exception as e:  # noqa: BLE001
        note("门禁无障碍复查失败：%s" % e)


def cec_routing_path():
    """返回 HDMI-CEC 当前活动路由；0x0000 表示电视自己，非 0 是外部设备。"""
    out = shell("dumpsys hdmi_control | grep mActiveRoutingPath | head -n 1",
                timeout=12)
    m = re.search(r"0x[0-9a-fA-F]+", out)
    return m.group(0) if m else ""


def wake_keeper():
    """唤醒电视端 APK，让它排好 20/60/120/180 秒的 ADB 自检闹钟。

    实测：电视重启后 ADB 会先恢复约一分钟，随后又被关掉。只要守护在这段
    窗口里连上过一次，就发这条广播把闹钟排好；之后即使端口被关，应用也会
    自己把 adb_enabled 写回 1，5555 自动回来，闸门不会长期失效。
    -f 32 = FLAG_INCLUDE_STOPPED_PACKAGES，应用刚装完处于 stopped 也能唤醒。
    """
    try:
        shell("am broadcast -a com.wb.tvquiz.ADB_BOOTTEST -n "
              "com.wb.tvquiz/.AdbKeeper -f 32", timeout=15)
    except Exception:  # noqa: BLE001
        pass


def foreground():
    """返回当前前台应用包名；取不到返回空串。"""
    out = shell("dumpsys activity activities | grep mResumedActivity | head -n 1")
    m = re.search(r"u0\s+([\w.]+)/", out)
    if m:
        return m.group(1)
    out2 = shell("dumpsys activity activities | grep topResumedActivity | head -n 1")
    m = re.search(r"u0\s+([\w.]+)/", out2)
    return m.group(1) if m else ""


def load_bank():
    if not BANK.exists():
        return []
    return json.loads(BANK.read_text(encoding="utf-8"))


def pick_index(bank, history):
    """错得多、久没见的优先；history: {id: {wrong, last}}"""
    now = time.time()
    best, best_i = -1.0, 0
    for i, q in enumerate(bank):
        h = history.get(q["id"], {})
        wrong = h.get("wrong", 0)
        last = h.get("last", 0)
        days = 30 if not last else min((now - last) / 86400.0, 30)
        score = 1 + wrong * 2.0 + days * 0.5 + random.random()
        if score > best:
            best, best_i = score, i
    return best_i


def launch_quiz(idx, session, gate, clear_log):
    """强停再拉起，保证任何时候只有一个答题页，不会叠一摞旧实例。"""
    if clear_log:
        shell("logcat -c")
    shell("am force-stop " + QUIZ_PKG)
    cmd = ("am start -n " + QUIZ_ACT + " --ei q_index " + str(idx)
           + " --es q_session " + session)
    if gate:
        cmd += " --ez gate true"
    return shell(cmd)


def fetch_result(session):
    """必须按 tag 过滤：电视系统日志极密，用 -t N 取最后 N 行会被冲掉。
    再按 session 匹配，避免上一次作答的旧 RESULT 让新闸门误放行。"""
    text = shell("logcat -d -s TVQuiz:I", timeout=30)
    for line in text.splitlines():
        i = line.find("RESULT|")
        if i >= 0 and ("|session=" + session) in line[i:]:
            return line[i:].strip()
    return None


def save_result(raw, q, trigger, session, history):
    rec = {"time": datetime.now().isoformat(timespec="seconds"),
           "raw": raw, "id": q["id"], "trigger": trigger, "session": session}
    for part in raw.split("|"):
        if "=" in part:
            k, v = part.split("=", 1)
            rec[k] = v
    with ANSWERS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    h = history.setdefault(q["id"], {"wrong": 0, "last": 0})
    h["last"] = time.time()
    if rec.get("correct") == "0":
        h["wrong"] = h.get("wrong", 0) + 1
    note("答题结果：" + raw[:110])
    return rec


def pop_quiz(bank, history, index=None, gate=False, trigger="interval",
             timeout_sec=None, session=None):
    """弹一道题并等作答。返回记录 dict，没抓到结果返回 None。

    gate=True 时是「进门闸门」：只要没作答且答题页不在前台，就不断把它拉回来。
    """
    if ASSIST_ONLY:
        # 辅助模式：门禁全交电视端 GateService，电脑端绝不弹题。
        return None
    idx = index if index is not None else pick_index(bank, history)
    q = bank[idx]
    session = session or ("%d" % int(time.time() * 1000))
    if PAUSE_ON_QUIZ:
        shell("input keyevent 127")  # MEDIA_PAUSE
        time.sleep(0.3)
    note(("闸门题" if gate else "计时题") + "：" + q["id"] + " " + q["stem"][:34])
    launch_quiz(idx, session, gate, clear_log=True)

    if timeout_sec is None:
        timeout_sec = GATE_TIMEOUT if gate else 100
    started = time.time()
    deadline = started + timeout_sec
    last_launch = started
    away_rounds = 0

    while time.time() < deadline:
        time.sleep(2)
        raw = fetch_result(session)
        if raw:
            return save_result(raw, q, trigger, session, history)
        fg = foreground()
        if fg == "":                       # adbd 掉了，等重连
            connect()
            continue
        if gate:
            # 返回键在 APK 里被拦住；按主页键跑到桌面或又开 B 站，就拉回来。
            # 题目和 session 不变，避免「按一下主页键换一道更容易的题」。
            if fg != QUIZ_PKG and time.time() - last_launch > 3:
                note("闸门：还没作答，把答题页拉回前台（当前前台 %s）" % fg)
                launch_quiz(idx, session, gate, clear_log=False)
                last_launch = time.time()
            continue
        if fg != QUIZ_PKG and time.time() > started + 8:
            away_rounds += 1
            if away_rounds >= 3:          # 被主页键跳过
                break

    note("没抓到作答结果" + ("，下一轮继续挡住" if gate else "，30 秒后补弹一次"))
    return None


def run_gate(bank, history):
    """进门闸门：答完放行；若配置要求答对，最多换 3 道题，别把孩子卡死。"""
    for attempt in range(3):
        rec = pop_quiz(bank, history, gate=True, trigger="gate")
        if rec is None:
            return False
        if not GATE_REQUIRE_CORRECT or rec.get("correct") == "1":
            return True
        note("闸门：答错了，按要求再给一道（第 %d 道）" % (attempt + 2))
    note("闸门：连着 3 道没答对，先放行")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="只观察，不弹题")
    ap.add_argument("--fast", type=int, default=0, help="演示模式：N 秒当作一轮")
    ap.add_argument("--minutes", type=float, default=CONF["interval_minutes"],
                    help="每多少分钟一道题")
    ap.add_argument("--poll", type=int, default=CONF["poll_seconds"],
                    help="轮询间隔秒数")
    ap.add_argument("--once", action="store_true", help="弹一次就退出，用于联调")
    ap.add_argument("--no-gate", action="store_true", help="临时关掉进门题")
    args = ap.parse_args()

    lock = None
    if not args.dry_run:
        lock = single_instance_lock()
        if lock is None:
            print("已有一个守护进程在运行（本机端口 54789 被占用），本次启动退出。")
            print("如需重启守护，请先关闭原来的窗口。")
            return 0

    threshold = args.fast if args.fast else args.minutes * 60
    gate_on = bool(CONF.get("gate_on_enter", True)) and not args.no_gate and not ASSIST_ONLY
    if ASSIST_ONLY:
        # 辅助模式不弹题：把计时阈值设成极大，主循环永不进入计时弹题分支。
        # 门禁、计时全部由电视端 GateService 负责。
        threshold = 10 ** 12
    bank = load_bank()
    if not bank:
        note("题库为空，请先运行 tools/build_questions.py 和 tools/build_tv_apk.py")
        return 1

    try:
        history = json.loads(HIST_FILE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        history = {}

    if ASSIST_ONLY:
        note("★ 辅助模式：门禁已全权交给电视端 GateService（本地无障碍，不依赖 ADB），"
             "本守护只做 ADB 自愈/6095 拉起/CEC 防切源/状态记录，不弹任何题")
    note("守护启动：题库 %d 道，每 %d 秒一道，进门题=%s，续播=%s，B 站=%s，dry_run=%s"
         % (len(bank), threshold, gate_on, RESUME_AFTER,
            "/".join(BILI_PACKAGES), args.dry_run))
    note("闸门配置：冷却 %d 秒（按上次答完题算）、离开宽限 %d 秒"
         % (GATE_COOLDOWN, GATE_LEAVE_GRACE))
    note("自愈配置：6095 通道=%s（离线 %d 秒后启用，每 %d 秒重试）、防 CEC 切源=%s（重连后 %d 秒窗口）"
         % (REVIVE_ENABLED, REVIVE_AFTER, REVIVE_RETRY,
            CEC_GUARD, CEC_GUARD_WINDOW))
    online_at_start = connect()
    if online_at_start:
        set_status("online", "辅助模式在线：门禁由电视端负责，本守护只保 ADB/CEC"
                   if ASSIST_ONLY else "电视已连接，进门闸门与计时题正常工作")
        note("电视在线：" + TARGET)
        wake_keeper()
        ensure_cec_setting()
    else:
        set_status("offline", "守护启动时电视就不在线，正在等待")
        note("守护启动时电视不在线，持续等待")

    elapsed = 0.0
    last_tick = time.time()
    last_reported_minute = -1
    offline_since = None
    offline_alerted = False
    last_offline_notice = 0.0
    pending_retry = 0
    resume_deadline = 0.0
    last_wake = time.time()   # 上次唤醒电视端 ADB 自恢复闹钟的时间
    last_revive = 0.0         # 上次通过 6095 尝试拉起应用的时间
    revive_pending = False    # 刚拉起应用，恢复在线后要收掉临时答题页
    # 守护启动时就在线，也算一个「开机/刚连上」的会话起点，同样给一段防切源保护窗口
    reconnected_at = time.time() if online_at_start else 0.0
    last_cec_check = 0.0      # 上次查 HDMI-CEC 活动源的时间
    last_cec_home = 0.0       # 上次按主页键的时间：30 秒冷却，防止把孩子反复踢回桌面
    last_gate_check = 0.0     # 上次复查门禁无障碍服务的时间（辅助模式双保险）
    in_bili = False           # 是否处在这一次「看 B 站」的会话里
    last_exit = 0.0           # 上次真正离开 B 站的时间
    leave_since = 0.0         # 连续离开的起点（宽限期内不算真离开）
    last_gate_pass = 0.0      # 上次进门题答完的时间
    gate_required = False     # 闸门未通过：不许看、不许计时

    try:
        while True:
            time.sleep(args.poll)
            now = time.time()
            # 弹题是同步阻塞的（十几秒），ADB 偶尔也卡；不能把这段时间
            # 当成「在看视频」，否则下一轮凭空多出十几秒甚至立刻又弹一题。
            dt = min(now - last_tick, args.poll * 2)
            last_tick = now

            if not connect():
                if offline_since is None:
                    offline_since = now
                    set_status("offline", "电视连不上，正在等待（可能是息屏，也可能是 ADB 调试被关）")
                    note("电视不在线（多半是息屏了，adbd 停了），持续等待")
                waited = now - offline_since
                if waited >= OFFLINE_ALERT and not offline_alerted:
                    offline_alerted = True
                    last_offline_notice = now
                    msg = ("电视已连续 %.0f 秒连不上：若电视重启过，设置→帐号与安全→"
                           "ADB调试 很可能被系统自动关掉了。此时【进门闸门和计时题都不生效】，"
                           "请到电视上重新打开 ADB 调试，或双击 check_adb.bat 自检。" % waited)
                    set_status("ALERT", msg)
                    note("!! " + msg)
                    if not args.dry_run:
                        windows_toast("电视答题守护：闸门已失效",
                                      "ADB 调试可能被关，请到电视上重新打开")
                elif offline_alerted and now - last_offline_notice >= 60:
                    last_offline_notice = now
                    note("!! 电视仍离线（已 %.0f 秒），闸门未生效" % waited)
                # 不依赖 ADB 的自愈：6095 在线就拉起答题应用，让它把 ADB 写回 1。
                # 电视真关机时 6095 也不通，这里会安静跳过，不弹题、不打扰。
                if (REVIVE_ENABLED and not args.dry_run
                        and waited >= REVIVE_AFTER
                        and now - last_revive >= REVIVE_RETRY):
                    last_revive = now
                    if revive_adb_via_assistant():
                        revive_pending = True
                        note("6095 在线但 ADB 不通：已拉起答题应用，等它把 ADB 调试写回开")
                continue
            if offline_since is not None:
                note("电视重新连上，等待 %.0f 秒" % (now - offline_since))
                set_status("online", "辅助模式在线：门禁由电视端负责，本守护只保 ADB/CEC"
                           if ASSIST_ONLY else "电视已连接，进门闸门与 3 分钟计时题正常工作")
                offline_since = None
                offline_alerted = False
                last_tick = time.time()   # 别把离线时间算成观看时间
                wake_keeper()             # 刚开机回来，立刻排好自检闹钟
                ensure_cec_setting()      # 开机可能把「直接播放信号源」还原，写回关
                ensure_gate_accessibility()  # 双保险：确认门禁服务仍在无障碍列表
                last_wake = now
                reconnected_at = now      # 开机/唤醒后的 CEC 保护窗口从这里起算
                last_cec_check = 0.0
                last_cec_home = 0.0       # 重连后重新允许按主页键（开机回桌面）
            if revive_pending:
                # 为恢复 ADB 拉起的应用会显示一道没有 session 的空白题，收掉它，
                # 免得挡着用户；只有前台确实还是答题页时才发 HOME。
                revive_pending = False
                if foreground() == QUIZ_PKG:
                    shell("input keyevent 3")
                    note("已收掉用于恢复 ADB 的临时答题页")

            if now - last_wake >= 600:    # 每 10 分钟保活一次，防止闹钟链断掉
                wake_keeper()
                last_wake = now

            # 辅助模式双保险：每 60 秒确认门禁无障碍服务仍在启用列表。
            # 电视端 AdbKeeper 已负责恢复，这里只在它被系统清掉时补写，防止
            # 开机/待机唤醒后门禁静默失效（正是本次修复的场景）。
            if ASSIST_ONLY and not args.dry_run and now - last_gate_check >= 60:
                last_gate_check = now
                ensure_gate_accessibility()

            # 防 CEC 自动切源，两件事分开做：
            # 1) 「直接播放信号源」要持续保持关——系统开机流程会在 20/60/120/180 秒
            #    把它写回 1，只在重连那一刻写一次会扑空，之后功放就自动切源、卡在功放界面。
            #    这里在保护窗口内每轮复查写回，是纯设置操作、无感，不影响看片。
            # 2) 活动源真被抢到外接设备时按主页键回桌面，但 30 秒冷却 + 看片/答题不按，
            #    既不长时间卡在功放界面，也不会把刚进云视听的孩子反复踢回桌面。
            if (CEC_GUARD and not args.dry_run and reconnected_at
                    and now - reconnected_at <= CEC_GUARD_WINDOW
                    and now - last_cec_check >= CEC_GUARD_POLL):
                last_cec_check = now
                ensure_cec_setting()      # 每轮复查，压住开机流程写回 1
                path = cec_routing_path()
                if path and path.lower() not in ("0x0000", "0x0"):
                    # 用户已经在看视频或答题，就别按了，免得打断
                    fg_now = foreground()
                    if fg_now not in BILI_PACKAGES and fg_now != QUIZ_PKG:
                        if now - last_cec_home >= 30:
                            note("CEC 把活动源切到外接设备（routing=%s），按主页键回电视桌面" % path)
                            shell("input keyevent 3")
                            last_cec_home = now
                    # else: 正在看视频/答题，保持不打扰

            fg = foreground()
            watching = fg in BILI_PACKAGES

            # 状态迁移：答题页盖着不算「离开 B 站」，否则每答完一道题就会再设一次闸门。
            # 连续离开不足宽限秒数也不算真离开：电视在启动画面、播放器全屏
            # 切换、桌面浮层之间抖一下，不该把「进门题」的计时刷新掉。
            if watching:
                entered = not in_bili
                in_bili = True
                leave_since = 0.0
            elif fg == QUIZ_PKG or fg == "":
                entered = False
            elif in_bili and leave_since == 0.0:
                leave_since = now
                entered = False
            elif in_bili and now - leave_since < GATE_LEAVE_GRACE:
                entered = False
            else:
                entered = False
                if in_bili:
                    last_exit = now
                    note("离开 B 站，停表（累计 %.0f 秒保留）" % elapsed)
                in_bili = False
                leave_since = 0.0

            if gate_on and entered and not args.dry_run:
                # 每次「进入」都明确重设闸门状态，避免上一轮没答完的
                # gate_required 残留到这次短时间返回。
                # 冷却以「上次答完题」为基准，不能用「上次离开」——后者会被
                # 来回切换不断刷新，导致正经的进门也永远不弹题（2026-11-12 实测）。
                # --dry-run 是纯观察，不设闸，否则 gate_required 会把计时一直挡成 0。
                gap = now - last_gate_pass if last_gate_pass else float("inf")
                if gap >= GATE_COOLDOWN:
                    gate_required = True
                    note("检测到进入云视听小电视 → 先做一道题才能看")
                else:
                    gate_required = False
                    note("距上次答题才 %.0f 秒，不重复设闸" % gap)

            if args.dry_run:
                if watching and not gate_required:
                    elapsed += dt
                minute = int(elapsed) // 60
                if minute > last_reported_minute or elapsed >= threshold:
                    last_reported_minute = minute
                    note("[dry-run] 前台=%s | 累计观看 %.0f / %d 秒"
                         % (fg or "?", elapsed, threshold))
                continue

            # 闸门：没作答就一直挡在前面，也不累计观看时间
            if gate_required and watching:
                if run_gate(bank, history):
                    gate_required = False
                    last_gate_pass = time.time()
                    elapsed = 0.0
                    last_reported_minute = -1
                    resume_deadline = time.time() + 30
                    note("闸门通过，开始计时")
                else:
                    note("闸门未通过，下一轮继续挡住")
                HIST_FILE.write_text(json.dumps(history, ensure_ascii=False, indent=1),
                                     encoding="utf-8")
                last_tick = time.time()
                continue

            # 自动续播：等答题页关掉、回到播放界面后再发播放键
            if resume_deadline:
                if watching:
                    if RESUME_AFTER:
                        shell("input keyevent 126")  # MEDIA_PLAY
                        note("已发播放键，节目继续播")
                    resume_deadline = 0.0
                elif now > resume_deadline:
                    note("没等到回到播放界面，跳过本次续播")
                    resume_deadline = 0.0

            # 上一题没答成，30 秒后补弹
            if pending_retry and now >= pending_retry:
                pending_retry = 0
                rec = pop_quiz(bank, history, trigger="retry")
                if rec:
                    resume_deadline = time.time() + 30
                else:
                    pending_retry = time.time() + 30
                elapsed = 0.0
                last_reported_minute = -1
                last_tick = time.time()
                continue

            if watching and not gate_required:
                elapsed += dt

            minute = int(elapsed) // 60
            if minute > last_reported_minute or elapsed >= threshold:
                last_reported_minute = minute
                note("前台=%s | 累计观看 %.0f / %d 秒"
                     % (fg or "?", elapsed, threshold))

            if elapsed >= threshold:
                rec = pop_quiz(bank, history, trigger="interval")
                HIST_FILE.write_text(json.dumps(history, ensure_ascii=False, indent=1),
                                     encoding="utf-8")
                elapsed = 0.0
                last_reported_minute = -1
                last_tick = time.time()
                if rec:
                    resume_deadline = time.time() + 30
                else:
                    pending_retry = time.time() + 30
                if args.once:
                    note("--once 已完成，退出")
                    return 0
    except KeyboardInterrupt:
        note("手动停止")
        HIST_FILE.write_text(json.dumps(history, ensure_ascii=False, indent=1),
                             encoding="utf-8")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
