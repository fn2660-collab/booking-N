import os
import urllib.request
from playwright.sync_api import sync_playwright

URL = "https://m.booking.naver.com/booking/13/bizes/357208/items/4096831?lang=ko&startDate=2027-02-05&theme=place"
TOPIC = os.environ["NTFY_TOPIC"]


def notify(msg):
    req = urllib.request.Request(
        "https://ntfy.sh/" + TOPIC, data=msg.encode("utf-8"), method="POST"
    )
    urllib.request.urlopen(req, timeout=20)


def main():
    seen = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(locale="ko-KR")

        def on_response(r):
            ct = r.headers.get("content-type", "")
            if "json" in ct and "naver" in r.url:
                try:
                    seen.append((r.url, r.text()[:600]))
                except Exception:
                    pass

        page.on("response", on_response)
        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(5000)
        text = page.inner_text("body")
        browser.close()

    print("===== 화면 텍스트 =====")
    print(text[:3000])
    print("===== JSON 응답 =====")
    for u, t in seen:
        print(u)
        print(t)
        print("---")

    notify("진단 실행 완료: ntfy 알림 연결 테스트입니다.")


if __name__ == "__main__":
    main()
