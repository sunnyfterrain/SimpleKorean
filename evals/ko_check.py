#!/usr/bin/env python3
"""한국어 답변에서 독자가 보는 것을 regex로 셉니다.

서식(bold, header, bullet, table 줄), em-dash와 세미콜론, 여닫는 말,
번역투와 금지어, 어절 수와 문장 수, 가장 긴 문장의 어절 수를 셉니다.
문장이 자연스러운지는 세지 못합니다. 측정에만 쓰고 hook으로는 쓰지 않습니다.

    python3 evals/ko_check.py reply.md
    python3 evals/ko_check.py --self-test
"""
import json
import re
import sys

EM_DASH = re.compile(r"—|–")
SEMICOLON = re.compile(r";")
BOLD = re.compile(r"\*\*[^*\n]+\*\*|__[^_\n]+__")
HEADER = re.compile(r"^\s{0,3}#{1,6}\s", re.M)
BULLET = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+", re.M)
TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$", re.M)
CODE_FENCE = re.compile(r"```[\s\S]*?```")
INLINE_CODE = re.compile(r"`[^`\n]+`")

OPENER = re.compile(
    r"^\W*(좋은 질문|훌륭한 질문|물론입니다|네,? 물론|당연히|기꺼이|확인해 ?드리겠|설명해 ?드리겠|말씀해 ?주신|질문하신|질문해 ?주신|안녕하세요)"
)
CLOSER = re.compile(
    r"(도움이 되(길|셨|었으면|기를)|추가 질문|궁금한 점이|더 궁금|언제든|말씀해 ?주세요|문의해 ?주세요|정리하면 다음과 같|요약하면 다음과 같|이상입니다|감사합니다)"
)

# 번역투. 패턴 하나가 규칙 하나입니다.
TRANSLATIONESE = {
    "에_대하여": re.compile(r"에 대하?여|에 대해서?|에 관하?여|에 관해서?"),
    "되어지": re.compile(r"되어[지집진질]|되어 [지집진질]"),
    "적인": re.compile(r"[가-힣]적인 "),
    "에_있어": re.compile(r"에 있어서?"),
    "함에_따라": re.compile(r"[가-힣]함에 따라|[가-힣]됨에 따라"),
    "를_통해": re.compile(r"[를을] 통해서?"),
}

# 금지어. 중요성을 말하는 꾸밈말과 접속 장식입니다.
SLOP = re.compile(r"원활|강력한|강력하게|매우 중요|참고로|결론적으로|뿐만 아니라|핵심적인|필수적인|효과적으로|성공적으로")

HEDGE = re.compile(r"것 같습니다|것 같아요|것으로 생각됩니다|듯합니다|듯 합니다")
MAY = re.compile(r"[ㄹ을]? ?수 있습니다|[ㄹ을]? ?수도 있습니다|[ㄹ을]? ?수 있어요")

# 문장 경계. 마침표, 물음표, 느낌표 뒤 공백, 또는 한국어 종결 어미 뒤 공백이나 줄끝.
SENTENCE_END = re.compile(r"(?<=[.!?])\s+|(?<=[다요죠])\s*\n+|(?<=[다요죠]\.)\s+")


def strip_code(text):
    text = CODE_FENCE.sub(" ", text)
    return INLINE_CODE.sub(" ", text)


def sentences(text):
    plain = strip_code(text)
    plain = re.sub(r"^\s{0,3}#{1,6}\s.*$", "", plain, flags=re.M)
    plain = BULLET.sub("", plain)
    plain = re.sub(r"\|", " ", plain)
    parts = [p.strip() for p in SENTENCE_END.split(plain)]
    return [p for p in parts if re.search(r"[가-힣A-Za-z0-9]", p)]


def words(text):
    return len(strip_code(text).split())


def check(text):
    sents = sentences(text)
    lengths = [len(s.split()) for s in sents]
    first = sents[0] if sents else ""
    counts = {
        "em_dash": len(EM_DASH.findall(strip_code(text))),
        "semicolon": len(SEMICOLON.findall(strip_code(text))),
        "bold": len(BOLD.findall(text)),
        "header": len(HEADER.findall(text)),
        "bullet": len(BULLET.findall(text)),
        "table_row": len(TABLE_ROW.findall(text)),
        "opener": int(bool(OPENER.search(first))),
        "closer": int(bool(CLOSER.search(text))),
        "hedge": len(HEDGE.findall(text)),
        "may": len(MAY.findall(text)),
        "slop": len(SLOP.findall(text)),
    }
    translationese = {k: len(p.findall(strip_code(text))) for k, p in TRANSLATIONESE.items()}
    counts["translationese"] = sum(translationese.values())
    visible = counts["em_dash"] + counts["bold"] + counts["header"] + counts["bullet"] + counts["table_row"]
    return {
        "words": words(text),
        "sentences": len(sents),
        "longest_sentence_words": max(lengths) if lengths else 0,
        "visible_total": visible,
        "counts": counts,
        "translationese": translationese,
    }


SELF_TEST = """## 제목

좋은 질문입니다. 이 설정에 대해서 설명하면 — 서버가 재시작됨에 따라 캐시가 비워지게 되어집니다; 이것은 매우 중요합니다.

- **첫째**: 원활하게 동작할 것 같습니다.
- 둘째

| a | b |
|---|---|
| 1 | 2 |

`code —` 안의 것은 세지 않습니다.

도움이 되길 바랍니다.
"""


def self_test():
    r = check(SELF_TEST)
    c = r["counts"]
    expect = {"em_dash": 1, "semicolon": 1, "bold": 1, "header": 1, "bullet": 2, "table_row": 3,
              "opener": 1, "closer": 1, "hedge": 1, "slop": 2}
    bad = {k: (c[k], v) for k, v in expect.items() if c[k] != v}
    t = r["translationese"]
    for key in ("에_대하여", "되어지", "함에_따라"):
        if t[key] != 1:
            bad[key] = (t[key], 1)
    if bad:
        print("self-test 실패:", json.dumps(bad, ensure_ascii=False))
        return 1
    print("self-test 통과")
    return 0


def main(argv):
    if len(argv) == 2 and argv[1] == "--self-test":
        return self_test()
    if len(argv) < 2:
        print(__doc__)
        return 2
    for path in argv[1:]:
        with open(path, encoding="utf-8") as f:
            text = f.read()
        print(json.dumps({"file": path, **check(text)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
