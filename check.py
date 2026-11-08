import os
import re
import urllib.request
from playwright.sync_api import sync_playwright

URL = "https://m.booking.naver.com/booking/13/bizes/357208/items/4096831?lang=ko&startDate=2027-02-05&theme=place"
TOPIC = os.environ["NTFY_TOPIC"]
TARGETS = [5, 4, 3]
BLOCKED = ("마감", "휴무", "연휴", "설날")


def notify(msg):
    req = urllib.request.Request(
        "https://ntfy.sh/" + TOPIC,
        data=msg.encode("utf-8"),
        method="POST",
        headers={"Priority": "3", "Click": URL},
    )
    urllib.request.urlopen(req, timeout=20)


def parse_days(text):
    lines = [l.strip() for l in text.splitlines()]
    seg = lines[lines.index("2027.2"):]
    seg = seg[seg.index("1"):]
    result = {}
    cur = None
    for line in seg:
        if re.fullmatch(r"\d{1,2}", line):
            cur = int(line)
            if cur in result:
                break
            result[cur] = ""
        elif line and cur is not None:
            result[cur] = line
    if not any("마감" in v for v in result.values()):
        raise RuntimeError("달력 해석 실패: 마감 표시를 찾지 못함")
    return result


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(locale="ko-KR")
        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(5000)
        text = page.inner_text("body")
        browser.close()

    days = parse_days(text)
    for d in TARGETS:
        if d not in days:
            raise RuntimeError(f"{d}일을 달력에서 찾지 못함")
    print({d: days[d] for d in TARGETS})

    open_days = [d for d in TARGETS if not any(b in days[d] for b in BLOCKED)]
    if open_days:
        names = ", ".join(f"2월 {d}일" for d in open_days)
        notify(f"예약 가능 자리 발생: {names}. 바로 확인하세요.")
    elif os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch":
        notify("수동 확인: 2월 3·4·5일 모두 마감 상태입니다. (정상 작동 중)")


if __name__ == "__main__":
    main()
