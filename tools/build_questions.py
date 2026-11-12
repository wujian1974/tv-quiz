# -*- coding: utf-8 -*-
"""把错题库合并成电视端 questions.json（全部四选一）。

数据来源：
- config.json 的 cards_dir 指向的错题卡目录（题干、正确答案、孩子错答、批注）
- quiz_items.json       人工逐题核对后的四选一改造表
- textbook_items.json  教材补充题

原则：正确项严格取自卡片；干扰项来源逐题记在 opt_from，供家长抽查。
3 道原本自带 A/B/C/D 的题由脚本自动解析，不走人工表。
家长标记「不再重做」的卡片一律不进题库。
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
# 错题卡目录由本地 config.json 指定（不随仓库公开）；未配置时默认项目内 cards/
CARDS = Path(CONFIG.get("cards_dir") or (ROOT / "cards"))
OUT = ROOT
ITEMS = OUT / "quiz_items.json"
TEXTBOOK = OUT / "textbook_items.json"

OPT_RE = re.compile(r"(?<![A-Za-z0-9])([A-D])[\.、．）\)]\s*")
ANS_LETTER_RE = re.compile(r"^\s*([A-D])[。．、\s]")


def parse_options(text):
    """从题干里拆出 A/B/C/D 四个选项，返回 (题干, 选项列表)。"""
    seq = []
    for m in OPT_RE.finditer(text):
        letter = m.group(1)
        expected = "ABCD"[len(seq)] if len(seq) < 4 else None
        if letter == expected:
            seq.append(m)
        elif letter == "A":
            seq = [m]
    if len(seq) != 4:
        return None
    stem = text[: seq[0].start()].strip()
    options = []
    for i, m in enumerate(seq):
        end = seq[i + 1].start() if i + 1 < 4 else len(text)
        options.append(text[m.end():end].strip().strip("　 \n"))
    if not stem or any(not o for o in options):
        return None
    return stem, options


def load_cards():
    out = {}
    for f in sorted(CARDS.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        if f.name.startswith("_") or str(d.get("id", "")).startswith("YYYYMMDD"):
            continue
        out[d["id"]] = d
    return out


def main():
    cards = load_cards()
    manual = json.loads(ITEMS.read_text(encoding="utf-8"))["items"]
    manual_ids = {x["id"] for x in manual}

    # 人工表自检
    assert len(manual) == len(manual_ids), "人工表里有重复 id"
    for x in manual:
        assert x["id"] in cards, f'人工表 id 不在卡片里: {x["id"]}'
        assert len(x["options"]) == 4, f'{x["id"]} 选项不是 4 个'
        assert len(set(x["options"])) == 4, f'{x["id"]} 选项有重复'
        assert 0 <= x["answer"] <= 3, f'{x["id"]} 答案下标越界'
        assert x["stem"].strip(), f'{x["id"]} 题干为空'
        assert len(x["stem"]) <= 160, f'{x["id"]} 题干过长，电视放不下'

    questions, excluded, unmapped = [], [], []

    for x in manual:
        d = cards[x["id"]]
        assert not d.get("practice_excluded"), f'{x["id"]} 已被家长撤出，不该进题库'
        q = {
            "id": x["id"],
            "subject": d.get("subject", ""),
            "type": "choice4",
            "level": "converted",
            "enabled": True,
            "stem": x["stem"],
            "options": x["options"],
            "answer_index": x["answer"],
            "explain": x["explain"],
            "opt_from": x["opt_from"],
            "tags": d.get("knowledge_tags", []),
            "source": d.get("source", ""),
        }
        if x.get("open_ended"):
            q["open_ended"] = True
        if x.get("figure_note"):
            q["figure_note"] = x["figure_note"]
        questions.append(q)

    for cid, d in cards.items():
        if cid in manual_ids:
            continue
        if d.get("practice_excluded") or str(d.get("correct_answer", "")).startswith("未能确认"):
            excluded.append({
                "id": cid,
                "reason": d.get("practice_excluded_reason") or "家长已撤出练习单 / 答案未能确认",
            })
            continue
        q = str(d.get("question", ""))
        ans = str(d.get("correct_answer", ""))
        parsed = parse_options(q)
        am = ANS_LETTER_RE.match(ans)
        if parsed and am:
            stem, options = parsed
            questions.append({
                "id": cid,
                "subject": d.get("subject", ""),
                "type": "choice4",
                "level": "original",
                "enabled": True,
                "stem": stem,
                "options": options,
                "answer_index": "ABCD".index(am.group(1)),
                "explain": ans,
                "opt_from": "原题自带的 A/B/C/D 选项，原样照搬",
                "tags": d.get("knowledge_tags", []),
                "source": d.get("source", ""),
            })
        else:
            unmapped.append(cid)

    assert not unmapped, f"还有卡片没覆盖到: {unmapped}"

    # ima 资料库教材补充题：只放已学单元，进度往前走时在 config.json 里加单元名
    allowed = set(CONFIG.get("textbook_units", []))
    tb = json.loads(TEXTBOOK.read_text(encoding="utf-8"))
    tb_ids = set()
    tb_skipped = []
    for x in tb["items"]:
        assert x["id"] not in manual_ids and x["id"] not in tb_ids, f'重复 id: {x["id"]}'
        tb_ids.add(x["id"])
        assert len(x["options"]) == 4, f'{x["id"]} 选项不是 4 个'
        assert len(set(x["options"])) == 4, f'{x["id"]} 选项有重复'
        assert 0 <= x["answer"] <= 3, f'{x["id"]} 答案下标越界'
        assert len(x["stem"]) <= 160, f'{x["id"]} 题干过长，电视放不下'
        assert all(len(o) <= 40 for o in x["options"]), f'{x["id"]} 选项过长，按钮放不下'
        assert x.get("source"), f'{x["id"]} 没写教材来源'
        if allowed and x["unit"] not in allowed:
            tb_skipped.append({"id": x["id"], "reason": "单元尚未学到：" + x["unit"]})
            continue
        questions.append({
            "id": x["id"],
            "subject": x["subject"],
            "type": "choice4",
            "level": "textbook",
            "enabled": True,
            "stem": x["stem"],
            "options": x["options"],
            "answer_index": x["answer"],
            "explain": x["explain"],
            "opt_from": x["opt_from"],
            "unit": x["unit"],
            "tags": x.get("tags", []),
            "source": "ima 知识库 · " + x["source"],
        })
    excluded.extend(tb_skipped)

    questions.sort(key=lambda q: q["id"])
    data = {
        "version": 2,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": "错题库卡片 + 教材补充题",
        "rules": {
            "choice": "全部题目为四选一，电视端用方向键移焦点、确定键作答",
            "shuffle": "每次出题打乱选项顺序并重算正确答案位置",
            "no_image": "绝不使用 archive/ 原卷照片：上面有孩子作答和老师红笔勾叉，等于泄答案",
            "audit": "每题 opt_from 记录干扰项来源；open_ended=true 的题答案是参考例文，非唯一解",
            "pick": "抽题按间隔重复：出错多的、久没见的优先，不按「待重做」筛（本库几乎全是重做过）",
            "textbook": "补充题出自 ima 知识库五年级上册教材，按 config.json 的 textbook_units 限定已学范围；语文1-4单元、数学1-4单元、英语Unit1-3",
        },
        "stats": {
            "cards_total": len(cards),
            "questions": len(questions),
            "original": sum(1 for q in questions if q["level"] == "original"),
            "converted": sum(1 for q in questions if q["level"] == "converted"),
            "math": sum(1 for q in questions if q["subject"] == "数学"),
            "chinese": sum(1 for q in questions if q["subject"] == "语文"),
            "english": sum(1 for q in questions if q["subject"] == "英语"),
            "card_questions": len(questions) - sum(1 for q in questions if q["level"] == "textbook"),
            "textbook": sum(1 for q in questions if q["level"] == "textbook"),
            "excluded": len(excluded),
            "textbook_skipped": len(tb_skipped),
        },
        "questions": questions,
        "excluded": excluded,
    }

    payload = json.dumps(data, ensure_ascii=False, indent=2)
    (OUT / "questions.json").write_text(payload, encoding="utf-8")
    (OUT / "preview_data.js").write_text(
        "window.QUIZ_DATA = " + payload + ";\n", encoding="utf-8")

    print("卡片总数:", data["stats"]["cards_total"])
    print("入库题目:", data["stats"]["questions"],
          "（原题", data["stats"]["original"], "/ 改造", data["stats"]["converted"], "）")
    print("数学", data["stats"]["math"], " 语文", data["stats"]["chinese"],
          " 英语", data["stats"]["english"])
    print("其中错题卡改造", data["stats"]["card_questions"],
          " / 教材补充", data["stats"]["textbook"])
    print("家长已撤及未学单元跳过:", data["stats"]["excluded"])
    print("-" * 70)
    for q in questions:
        print(f'[{q["level"]:<9}] {q["id"]}  {q["stem"][:44]}')
        print("    " + " | ".join(q["options"])[:110])
    print("-" * 70)
    print("输出:", OUT / "questions.json")
    print("输出:", OUT / "preview_data.js")


if __name__ == "__main__":
    main()
