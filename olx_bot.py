import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request

SEARCH_URL = (
    "https://www.olx.pl/praca/kierowca/poznan/"
    "?search%5Bdist%5D=5&search%5Border%5D=created_at:desc"
    "&search%5Bfilter_enum_driving_license%5D%5B0%5D=catc"
    "&search%5Bfilter_enum_driving_license%5D%5B1%5D=catce"
    "&search%5Bfilter_enum_transport_range%5D%5B0%5D=national_transport"
)
SEEN_FILE = "seen.json"
TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]


def fetch(url):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            ),
            "Accept-Language": "pl-PL,pl;q=0.9",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def parse(page):
    items = {}
    pattern = r'<a[^>]+href="(/d/oferta/[^"#?]+)[^"]*"[^>]*>(.*?)</a>'
    for m in re.finditer(pattern, page, re.S):
        path, inner = m.groups()
        text = html.unescape(re.sub(r"<[^>]+>", " ", inner))
        text = re.sub(r"\s+", " ", text).strip()
        url = "https://www.olx.pl" + path
        if url not in items or len(text) > len(items[url]):
            items[url] = text
    return items


def send(text):
    data = urllib.parse.urlencode(
        {"chat_id": CHAT_ID, "text": text, "disable_web_page_preview": "false"}
    ).encode()
    urllib.request.urlopen(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage", data=data, timeout=30
    )


def main():
    items = parse(fetch(SEARCH_URL))
    if not items:
        print("Не знайдено жодного оголошення: сайт міг змінити верстку або заблокувати запит")
        sys.exit(1)

    first_run = not os.path.exists(SEEN_FILE)
    seen = set()
    if not first_run:
        with open(SEEN_FILE, encoding="utf-8") as f:
            seen = set(json.load(f))

    new = [(u, t) for u, t in items.items() if u not in seen]

    if first_run:
        send(f"Бот запущено. Зараз у пошуку {len(items)} оголошень, надалі надсилатиму лише нові.")
    else:
        for url, title in reversed(new):
            send(f"{title[:200]}\n{url}")

    seen.update(items.keys())
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(seen), f, ensure_ascii=False, indent=0)
    print(f"Нових: {0 if first_run else len(new)}")


if __name__ == "__main__":
    main()
  
