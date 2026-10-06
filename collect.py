#!/usr/bin/env python3
"""
김도훈 중령의 육군뉴스 — 자동 수집 스크립트

매시간 GitHub Actions가 실행합니다. 하는 일:
  1) 네이버 뉴스·블로그 검색 API로 육군·국방 관련 새 기사를 모아 data/news.json에 추가
  2) 기상청 단기예보 API로 11개 지역 날씨를 받아 data/brief.json에 기록
  3) 오늘의 일정·해외 군사·생활 정보 기사를 골라 data/brief.json에 기록
  4) 갱신 시각을 data/status.json에 기록

필요한 비밀값(GitHub 저장소 Settings → Secrets and variables → Actions):
  NAVER_CLIENT_ID, NAVER_CLIENT_SECRET   (필수)
  KMA_SERVICE_KEY                        (날씨, 없으면 날씨만 건너뜀)
  ANTHROPIC_API_KEY, ANTHROPIC_MODEL     (선택: 넣으면 Claude가 부제·요약·분류·묶기를 다듬음)

표준 라이브러리만 사용하므로 별도 설치가 필요 없습니다.
"""
import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

KST = timezone(timedelta(hours=9))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
MAX_ITEMS = 300
KEEP_DAYS = 14
WD = "월화수목금토일"

# ───────────────────────── 검색어 ─────────────────────────
# (검색어, 기본 분야). 분야: army social mnd navy-air nk industry
NEWS_QUERIES = [
    ("육군", "army"), ("육군 사단", "army"), ("육군 장병", "army"), ("군단 훈련", "army"),
    ("육군훈련소", "army"), ("예비군", "army"),
    ("국방부", "mnd"), ("국방부 브리핑", "mnd"), ("병역", "mnd"), ("국방위원회", "mnd"),
    ("해군", "navy-air"), ("공군", "navy-air"), ("해병대", "navy-air"),
    ("합참 북한", "nk"), ("북한 미사일", "nk"), ("DMZ 북한군", "nk"), ("한미동맹", "nk"),
    ("방산 수출", "industry"), ("방위산업", "industry"),
    ("육군 누리꾼", "social"), ("군대 온라인 화제", "social"), ("장병 영상 화제", "social"),
]
BLOG_QUERIES = ["육군 이슈", "군대 화제", "육군 부대 소식"]
SCHEDULE_QUERIES = ["[오늘의 주요일정] 국회", "[오늘의 주요일정] 정치", "오늘의 정치일정"]
OVERSEAS_QUERIES = ["미 국방부", "나토 군사", "우크라이나 전쟁", "중국군", "일본 자위대", "주한미군"]
LIFE_QUERIES = ["건강 생활 정보", "환절기 건강"]

# 제목 키워드로 분야를 바로잡습니다(위에서부터 먼저 맞는 것).
CATEGORY_RULES = [
    ("social", r"누리꾼|온라인서|온라인 커뮤니티|SNS|유튜브|틱톡|인스타|화제의 영상|갑론을박"),
    ("industry", r"방산|방위산업|한화에어로|한화시스템|현대로템|LIG|KAI|한국항공우주|수출 계약|수주"),
    ("navy-air", r"해군|공군|해병|함정|잠수함|전투기|KF-21|F-35|구축함"),
    ("nk", r"북한|北|합참|미사일|김정은|김여정|NLL|MDL|DMZ"),
    ("army", r"육군|사단|군단|여단|대대|장병|훈련병|예비군|지작사|지상작전"),
    ("mnd", r"국방부|국방장관|병역|병무청|국방위|국정감사|군 인권|군인권"),
]

# 언론사 도메인 → 이름
SOURCES = {
    "yna.co.kr": "연합뉴스", "yonhapnewstv.co.kr": "연합뉴스TV", "news1.kr": "뉴스1", "newsis.com": "뉴시스",
    "chosun.com": "조선일보", "joongang.co.kr": "중앙일보", "donga.com": "동아일보", "hani.co.kr": "한겨레",
    "khan.co.kr": "경향신문", "hankookilbo.com": "한국일보", "kmib.co.kr": "국민일보", "seoul.co.kr": "서울신문",
    "segye.com": "세계일보", "munhwa.com": "문화일보", "mk.co.kr": "매일경제", "hankyung.com": "한국경제",
    "mt.co.kr": "머니투데이", "edaily.co.kr": "이데일리", "fnnews.com": "파이낸셜뉴스", "sedaily.com": "서울경제",
    "asiae.co.kr": "아시아경제", "heraldcorp.com": "헤럴드경제", "news.kbs.co.kr": "KBS", "imnews.imbc.com": "MBC",
    "sbs.co.kr": "SBS", "jtbc.co.kr": "JTBC", "ytn.co.kr": "YTN", "mbn.co.kr": "MBN", "ichannela.com": "채널A",
    "tvchosun.com": "TV조선", "nocutnews.co.kr": "노컷뉴스", "ohmynews.com": "오마이뉴스", "pressian.com": "프레시안",
    "newspim.com": "뉴스핌", "dailian.co.kr": "데일리안", "etoday.co.kr": "이투데이", "ajunews.com": "아주경제",
    "kookbang.dema.mil.kr": "국방일보", "korea.kr": "정책브리핑", "kyeonggi.com": "경기일보", "kwnews.co.kr": "강원일보",
    "imaeil.com": "매일신문", "kookje.co.kr": "국제신문", "busan.com": "부산일보", "news.tf.co.kr": "더팩트",
    "wikitree.co.kr": "위키트리", "insight.co.kr": "인사이트", "g-enews.com": "글로벌이코노믹",
    "shinailbo.co.kr": "신아일보", "newdaily.co.kr": "뉴데일리", "dt.co.kr": "디지털타임스", "zdnet.co.kr": "지디넷코리아",
}

# 기상청 격자 좌표(nx, ny)
REGIONS = [
    ("서울", 60, 127), ("인천", 55, 124), ("수원(경기)", 60, 121), ("춘천(강원 영서)", 73, 134),
    ("강릉(강원 영동)", 92, 131), ("대전·계룡", 67, 100), ("전주", 63, 89), ("광주", 58, 74),
    ("대구", 89, 90), ("부산", 98, 76), ("제주", 52, 38),
]


# ───────────────────────── 공통 ─────────────────────────
def now_kst():
    return datetime.now(KST)


def load(name, default):
    try:
        with open(os.path.join(DATA, name), encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save(name, obj):
    os.makedirs(DATA, exist_ok=True)
    path = os.path.join(DATA, name)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def http_json(url, headers=None, data=None, timeout=20):
    req = urllib.request.Request(url, headers=headers or {}, data=data)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def clean(s):
    s = re.sub(r"<[^>]+>", "", s or "")
    return html.unescape(s).replace(" ", " ").strip()


def source_of(url):
    host = urllib.parse.urlparse(url).netloc.lower()
    host = host[4:] if host.startswith("www.") else host
    for dom, name in SOURCES.items():
        if host == dom or host.endswith("." + dom) or dom.endswith(host):
            return name
    return host or "출처 미상"


def categorize(title, default):
    for cat, pat in CATEGORY_RULES:
        if re.search(pat, title):
            # 블로그·SNS 검색에서 온 것은 그대로 social 유지
            return "social" if default == "social" else cat
    return default


def slug(title, url):
    base = re.sub(r"[^0-9A-Za-z]+", "-", urllib.parse.urlparse(url).path).strip("-")[-40:]
    if not base:
        base = str(abs(hash(title)) % 10**10)
    return base.lower()


def bigrams(t):
    t = re.sub(r"\[[^\]]*\]|[^0-9A-Za-z가-힣]", "", t)
    return {t[i:i + 2] for i in range(len(t) - 1)}


def similar(a, b):
    A, B = bigrams(a), bigrams(b)
    if not A or not B:
        return 0.0
    return len(A & B) / len(A | B)


def first_sentence(s, limit=70):
    s = re.split(r"(?<=[.다])\s", s.strip())[0]
    return s if len(s) <= limit else s[: limit - 1] + "…"


# ───────────────────────── 네이버 검색 ─────────────────────────
def naver(kind, query, display=20):
    cid, sec = os.environ.get("NAVER_CLIENT_ID"), os.environ.get("NAVER_CLIENT_SECRET")
    if not cid or not sec:
        raise SystemExit("NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 비밀값이 없습니다. 안내서 2단계를 확인하세요.")
    url = f"https://openapi.naver.com/v1/search/{kind}.json?" + urllib.parse.urlencode(
        {"query": query, "display": display, "sort": "date"})
    return http_json(url, {"X-Naver-Client-Id": cid, "X-Naver-Client-Secret": sec}).get("items", [])


def news_items(query, cat, since):
    out = []
    for it in naver("news", query):
        try:
            pub = parsedate_to_datetime(it["pubDate"]).astimezone(KST)
        except Exception:
            continue
        if pub < since:
            continue
        url = it.get("originallink") or it.get("link")
        title = clean(it.get("title"))
        desc = clean(it.get("description"))
        out.append({
            "title": title, "url": url, "source": source_of(url),
            "publishedAt": pub.isoformat(timespec="seconds"),
            "category": categorize(title, cat),
            "breaking": title.startswith("[속보]") or "[속보]" in title[:8],
            "summary": desc, "sub": "",
        })
    return out


def blog_items(query, since):
    out = []
    for it in naver("blog", query, 10):
        d = it.get("postdate", "")
        try:
            pub = datetime.strptime(d, "%Y%m%d").replace(hour=12, tzinfo=KST)
        except ValueError:
            continue
        if pub.date() < since.date():
            continue
        title = clean(it.get("title"))
        if not re.search(r"육군|군대|장병|부대|훈련|국방|전역|입대", title):
            continue
        out.append({
            "title": title, "url": it.get("link"), "source": "블로그 · " + clean(it.get("bloggername")),
            "publishedAt": pub.isoformat(timespec="seconds"), "category": "social", "breaking": False,
            "summary": clean(it.get("description")), "sub": "",
        })
    return out


def pick_links(queries, n, since, must=None):
    seen, out = set(), []
    for q in queries:
        try:
            items = naver("news", q, 10)
        except Exception as e:
            print("검색 실패:", q, e, file=sys.stderr)
            continue
        for it in items:
            try:
                pub = parsedate_to_datetime(it["pubDate"]).astimezone(KST)
            except Exception:
                continue
            title = clean(it.get("title"))
            if pub < since or title in seen or (must and not re.search(must, title)):
                continue
            seen.add(title)
            out.append({"title": title, "url": it.get("originallink") or it.get("link")})
            break
        if len(out) >= n:
            break
    return out


# ───────────────────────── 묶기 ─────────────────────────
def assign_groups(items):
    """같은 사건(제목이 비슷한 기사)끼리 같은 group 값을 줍니다."""
    recent = [i for i in items if i.get("publishedAt", "") >= (now_kst() - timedelta(days=3)).isoformat()]
    for i in recent:
        if i.get("group"):
            continue
        for j in recent:
            if j is i or similar(i["title"], j["title"]) < 0.32:
                continue
            g = j.get("group") or j["id"]
            i["group"] = g
            j.setdefault("group", g)
            break


# ───────────────────────── Claude로 다듬기(선택) ─────────────────────────
def polish_with_claude(new_items, existing_groups):
    key, model = os.environ.get("ANTHROPIC_API_KEY"), os.environ.get("ANTHROPIC_MODEL")
    if not key or not model or not new_items:
        return
    rows = [{"id": i["id"], "title": i["title"], "desc": i["summary"][:300], "category": i["category"]} for i in new_items]
    prompt = (
        "다음은 한국 육군·국방 관련 새 기사 목록입니다. 각 기사에 대해 JSON 객체 하나를 돌려주세요.\n"
        "형식: {\"<id>\": {\"category\": army|social|mnd|navy-air|nk|industry, "
        "\"sub\": 핵심 포인트 2~3개를 ' / '로 이은 한 줄(60자 이내), "
        "\"summary\": 한국어 1~2문장 요약, \"group\": 같은 사건끼리 같은 짧은 영문 키(기존 키 목록에 같은 사건이 있으면 그 키) 또는 null}}\n"
        "기사에 없는 내용을 지어내지 마세요. JSON만 출력하세요.\n"
        f"기존 group 키: {sorted(existing_groups)[:80]}\n기사: {json.dumps(rows, ensure_ascii=False)}"
    )
    body = json.dumps({"model": model, "max_tokens": 4000,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    try:
        res = http_json("https://api.anthropic.com/v1/messages", {
            "x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"}, body, 90)
        text = "".join(b.get("text", "") for b in res.get("content", []))
        text = text[text.find("{"): text.rfind("}") + 1]
        fix = json.loads(text)
    except Exception as e:
        print("Claude 다듬기 건너뜀:", e, file=sys.stderr)
        return
    for i in new_items:
        f = fix.get(i["id"]) or {}
        if f.get("category") in {"army", "social", "mnd", "navy-air", "nk", "industry"}:
            i["category"] = f["category"]
        for k in ("sub", "summary"):
            if isinstance(f.get(k), str) and f[k].strip():
                i[k] = f[k].strip()
        if isinstance(f.get("group"), str) and f["group"].strip():
            i["group"] = f["group"].strip()


# ───────────────────────── 기상청 날씨 ─────────────────────────
SKY = {"1": "☀️", "3": "⛅", "4": "☁️"}
PTY = {"1": "🌧️", "2": "🌨️", "3": "❄️", "4": "🌦️", "5": "🌧️", "6": "🌨️", "7": "❄️"}


def kma_region(nx, ny, base):
    key = os.environ["KMA_SERVICE_KEY"].strip()
    if "%" not in key:  # 일반(Decoding) 키면 주소용으로 인코딩
        key = urllib.parse.quote(key, safe="")
    q = urllib.parse.urlencode({"pageNo": 1, "numOfRows": 1500, "dataType": "JSON",
                                "base_date": base.strftime("%Y%m%d"), "base_time": base.strftime("%H%M"),
                                "nx": nx, "ny": ny})
    url = "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst?serviceKey=" + key + "&" + q
    res = http_json(url, timeout=30)
    items = res["response"]["body"]["items"]["item"]
    by_day = {}
    for it in items:
        d = by_day.setdefault(it["fcstDate"], {})
        d.setdefault(it["category"], {})[it["fcstTime"]] = it["fcstValue"]
    return by_day


def icon_at(day, hhmm):
    pty = day.get("PTY", {}).get(hhmm, "0")
    if pty not in ("0", None):
        return PTY.get(pty, "🌧️")
    return SKY.get(day.get("SKY", {}).get(hhmm, ""), "")


def to_num(v):
    try:
        return round(float(v))
    except (TypeError, ValueError):
        return None


def weather():
    if not os.environ.get("KMA_SERVICE_KEY"):
        return None
    now = now_kst()
    base = now.replace(hour=2, minute=0, second=0, microsecond=0)
    if now < base + timedelta(minutes=15):
        base -= timedelta(hours=3)  # 전날 23시 발표
    regions = []
    for name, nx, ny in REGIONS:
        try:
            by_day = kma_region(nx, ny, base)
        except Exception as e:
            print("날씨 실패:", name, e, file=sys.stderr)
            regions.append({"name": name, "days": [], "alerts": []})
            continue
        days, alerts = [], []
        for k in range(3):
            dt = now + timedelta(days=k)
            day = by_day.get(dt.strftime("%Y%m%d"), {})
            tmn = to_num(next(iter(day.get("TMN", {}).values()), None))
            tmx = to_num(next(iter(day.get("TMX", {}).values()), None))
            if tmn is None or tmx is None:
                tmps = [to_num(v) for v in day.get("TMP", {}).values()]
                tmps = [t for t in tmps if t is not None]
                if not tmps:
                    continue
                tmn, tmx = (tmn if tmn is not None else min(tmps)), (tmx if tmx is not None else max(tmps))
            wd = WD[dt.weekday()]
            days.append({"label": "오늘" if k == 0 else f"{'내일' if k == 1 else '모레'} ({wd})", "wd": wd,
                         "am": icon_at(day, "0900"), "pm": icon_at(day, "1500"), "min": tmn, "max": tmx})
            if k == 0:
                wsd = [to_num(v) or 0 for v in day.get("WSD", {}).values()]
                pop = [to_num(v) or 0 for v in day.get("POP", {}).values()]
                if wsd and max(wsd) >= 9:
                    alerts.append("강풍 주의")
                if pop and max(pop) >= 60:
                    alerts.append("비 소식")
                if tmn is not None and tmn <= 0:
                    alerts.append("영하권")
        regions.append({"name": name, "days": days, "alerts": alerts})
    seoul = next((r for r in regions if r["days"]), None)
    comment = ""
    if seoul:
        t = seoul["days"][0]
        sky = {"☀️": "맑음", "⛅": "구름 많음", "☁️": "흐림", "🌧️": "비", "🌦️": "소나기", "❄️": "눈", "🌨️": "비·눈"}
        comment = f"{sky.get(t['pm'] or t['am'], '')}, 일교차 {t['max'] - t['min']}℃".strip(", ")
    return {"region": "서울", "comment": comment, "regions": regions}


# ───────────────────────── 실행 ─────────────────────────
def main():
    now = now_kst()
    news = load("news.json", [])
    if isinstance(news, dict):
        news = news.get("items", [])
    known_urls = {i.get("url") for i in news}
    known_titles = [i.get("title", "") for i in news[:200]]
    since = now - timedelta(hours=6)

    fresh = []
    for q, cat in NEWS_QUERIES:
        try:
            fresh += news_items(q, cat, since)
        except SystemExit:
            raise
        except Exception as e:
            print("뉴스 검색 실패:", q, e, file=sys.stderr)
    for q in BLOG_QUERIES:
        try:
            fresh += blog_items(q, now - timedelta(days=1))
        except Exception as e:
            print("블로그 검색 실패:", q, e, file=sys.stderr)

    new_items, seen = [], set()
    for it in sorted(fresh, key=lambda x: x["publishedAt"], reverse=True):
        if not it["url"] or it["url"] in known_urls or it["url"] in seen:
            continue
        if any(similar(it["title"], t) > 0.8 for t in known_titles + [n["title"] for n in new_items]):
            continue  # 거의 같은 제목(같은 기사 재전송) 제외
        seen.add(it["url"])
        it["id"] = datetime.fromisoformat(it["publishedAt"]).strftime("%Y%m%d") + "-" + slug(it["title"], it["url"])
        it["sub"] = first_sentence(it["summary"]) if it["summary"] else ""
        new_items.append(it)
        if len(new_items) >= 25:
            break

    polish_with_claude(new_items, {i.get("group") for i in news if i.get("group")})

    news = new_items + news
    cutoff = (now - timedelta(days=KEEP_DAYS)).isoformat()
    news = [i for i in news if i.get("publishedAt", "") >= cutoff]
    news.sort(key=lambda x: x.get("publishedAt", ""), reverse=True)
    news = news[:MAX_ITEMS]
    assign_groups(news)
    save("news.json", news)

    brief = load("brief.json", {})
    today = now.strftime("%Y-%m-%d")
    if brief.get("date") != today or now.hour in (6, 12, 18):
        w = weather()
        if w:
            brief["weather"] = w
        brief["date"] = today
        day_since = now.replace(hour=0, minute=0, second=0) - timedelta(hours=12)
        brief["schedules"] = pick_links(SCHEDULE_QUERIES, 3, day_since, r"일정") or brief.get("schedules", [])
        brief["overseas"] = pick_links(OVERSEAS_QUERIES, 4, now - timedelta(days=1)) or brief.get("overseas", [])
        brief["life"] = pick_links(LIFE_QUERIES, 2, now - timedelta(days=2)) or brief.get("life", [])
        save("brief.json", brief)

    save("status.json", {"updatedAt": now_kst().isoformat(timespec="seconds"),
                         "note": f"{len(new_items)}건 추가" if new_items else "새 소식 없음"})
    print(f"새 기사 {len(new_items)}건 추가, 전체 {len(news)}건")
    for i in new_items:
        print(" -", i["category"], i["title"])


if __name__ == "__main__":
    main()
