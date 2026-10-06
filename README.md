# 김도훈 중령의 육군뉴스 — 설치 안내서

로그인 없이 누구나 볼 수 있는 웹사이트로 올리는 방법입니다. 모두 무료이고, 한 번만 설정하면 매시간 자동으로 갱신됩니다.

- 주소: `https://armyteam12.github.io/army-news/`  (GitHub 아이디: ARMYTEAM12)
- 갱신: 한국시간 06:50 ~ 23:50 매시간 (GitHub 사정에 따라 5~20분 늦을 수 있음)
- 휴대폰: 주소를 열고 **홈 화면에 추가**를 하면 앱처럼 아이콘으로 열립니다

준비물은 아래 3가지이고, 30분 정도 걸립니다.

| 준비물 | 어디서 | 용도 |
|---|---|---|
| GitHub 계정 | github.com (구글 계정으로 가입 가능) | 웹사이트를 올리고 매시간 자동 실행 |
| 네이버 검색 API 키 | developers.naver.com | 뉴스·블로그 검색 |
| 기상청 단기예보 API 키 | data.go.kr (공공데이터포털) | 지역별 날씨 |

---

## 1단계. GitHub 저장소 만들기

1. github.com에 로그인 → 오른쪽 위 **＋** → **New repository**
2. Repository name: `army-news`
3. **Public** 선택 (무료로 웹사이트를 열려면 공개여야 합니다)
4. **Create repository**

## 2단계. 파일 올리기

1. 받은 zip 파일의 압축을 풉니다.
2. 새 저장소 화면에서 **uploading an existing file** (또는 **Add file → Upload files**)을 누릅니다.
3. 압축을 푼 폴더 **안의 내용 전체**(index.html, data 폴더, scripts 폴더 등)를 끌어다 놓고 **Commit changes**를 누릅니다.

> **꼭 확인하세요:** `.github` 폴더는 이름이 점(.)으로 시작해서 맥이나 윈도우에서 숨김 폴더로 보이지 않을 수 있습니다. 올린 뒤 저장소에 `.github/workflows/collect.yml`이 없으면 이렇게 만드세요.
> 1. **Add file → Create new file**
> 2. 파일 이름 칸에 `.github/workflows/collect.yml` 입력 (슬래시를 치면 폴더가 저절로 생깁니다)
> 3. 압축 푼 폴더의 `.github/workflows/collect.yml`을 메모장으로 열어 내용을 그대로 붙여넣고 **Commit changes**

## 3단계. 네이버 검색 API 키 받기

1. developers.naver.com 로그인 → **Application → 애플리케이션 등록**
2. 애플리케이션 이름: `육군뉴스` (아무 이름이나 가능)
3. 사용 API: **검색**
4. 비로그인 오픈 API 서비스 환경: **WEB 설정** → 웹 서비스 URL에 `https://armyteam12.github.io` 입력
5. 등록 후 나오는 **Client ID**와 **Client Secret**을 메모합니다.

## 4단계. 기상청 API 키 받기 (날씨)

1. data.go.kr 로그인 → 검색창에 `기상청_단기예보` 검색
2. **기상청_단기예보 ((구)_동네예보) 조회서비스** → **활용신청** (보통 바로 승인됨)
3. 마이페이지 → 데이터활용 → 개발계정에서 **일반 인증키(Encoding)** 값을 복사합니다.

> 승인 직후 1~2시간은 키가 동작하지 않을 수 있습니다. 그동안 날씨만 비어 있고 뉴스는 정상으로 수집됩니다.

## 5단계. 키를 저장소에 넣기 (비밀값)

키는 채팅이나 파일에 붙여넣지 말고 여기에만 넣으세요. 남에게 보이지 않습니다.

1. 저장소 → **Settings → Secrets and variables → Actions → New repository secret**
2. 아래 3개를 하나씩 만듭니다.

| Name | Secret에 넣을 값 |
|---|---|
| `NAVER_CLIENT_ID` | 3단계의 Client ID |
| `NAVER_CLIENT_SECRET` | 3단계의 Client Secret |
| `KMA_SERVICE_KEY` | 4단계의 일반 인증키(Encoding) |

## 6단계. 자동 저장 권한 켜기

1. 저장소 → **Settings → Actions → General**
2. 맨 아래 **Workflow permissions** → **Read and write permissions** 선택 → **Save**

## 7단계. 웹사이트 켜기

1. 저장소 → **Settings → Pages**
2. Source: **Deploy from a branch**
3. Branch: **main**, 폴더 **/(root)** → **Save**
4. 1~2분 뒤 화면 위에 사이트 주소가 나옵니다.

## 8단계. 첫 수집 돌리기

1. 저장소 → **Actions** 탭 → (처음이면 **I understand… enable** 버튼) → 왼쪽 **육군뉴스 자동 수집**
2. 오른쪽 **Run workflow → Run workflow**
3. 1~2분 뒤 초록색 체크가 뜨면 성공입니다. 사이트를 새로고침하면 최신 기사와 날씨가 보입니다.

빨간 X가 뜨면 눌러서 오류 문장을 확인하세요. 대부분 5단계 이름 오타나 6단계 권한 문제입니다.

---

## 쓰는 법

- **공유:** 사이트 주소를 카톡으로 보내면 됩니다. 받는 사람은 로그인할 필요가 없습니다.
- **앱처럼 쓰기:** 아이폰은 사파리 공유 버튼 → **홈 화면에 추가**, 안드로이드는 크롬 메뉴(⋮) → **홈 화면에 추가** 또는 **앱 설치**
- **지금 바로 새로 모으기:** 저장소 Actions 탭 → **Run workflow**를 누르면 됩니다(관리자만 가능). 사이트의 '↻ 새로고침' 버튼은 이미 모인 최신 데이터를 다시 읽어 옵니다.
- **카톡 스크린 / 저장:** Claude에서 쓰던 것과 똑같습니다. '보관함에 저장'은 각자 자기 기기(브라우저)에만 저장됩니다.
- 사이트는 1분마다 새 데이터가 있는지 확인해 저절로 바뀝니다.

## 바꾸고 싶을 때

- **검색어:** `scripts/collect.py` 위쪽 `NEWS_QUERIES` 목록을 고치면 됩니다(GitHub 화면에서 연필 아이콘으로 바로 수정 가능).
- **갱신 시간:** `.github/workflows/collect.yml`의 `cron` 두 줄. UTC 기준이라 한국시간에서 9시간을 빼서 적습니다.
- **날씨 지역:** `scripts/collect.py`의 `REGIONS` (기상청 격자 좌표).

## 선택: Claude로 부제·요약 다듬기

기본 상태에서는 네이버 검색 결과의 설명을 그대로 요약으로 씁니다. 지금 Claude 버전처럼 부제를 깔끔하게 뽑고 같은 사건끼리 정확히 묶으려면 Claude API를 연결하세요. Anthropic API 사용료가 따로 듭니다.

1. console.anthropic.com에서 API 키 발급
2. Secrets에 `ANTHROPIC_API_KEY` 추가
3. **Secrets and variables → Actions → Variables** 탭 → `ANTHROPIC_MODEL` 추가 (값은 docs.claude.com 모델 목록의 모델 이름)

## 알아두실 점

- 저장소가 공개(Public)라서 기사 목록 데이터도 공개됩니다. 기사 링크와 요약만 들어 있습니다.
- GitHub는 저장소에 60일 동안 아무 활동이 없으면 예약 실행을 멈출 수 있습니다. 멈췄다는 메일이 오면 Actions 탭에서 다시 켜 주세요.
- 네이버 검색 API는 하루 25,000회까지 무료이고, 이 설정은 하루 700회 안팎을 씁니다.
