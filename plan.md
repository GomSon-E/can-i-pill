# 이거뭐약 — Plan

---

## Phase 1. 프로젝트 기반 세팅

- [x] Frontend: 테스트 환경 세팅 (Vitest + React Testing Library) 동작 확인
- [x] Backend: FastAPI 프로젝트 생성, GET /health 엔드포인트 200 응답 확인
- [x] Backend: pytest 환경 세팅, 기본 테스트 동작 확인
- [x] Backend: Supabase 연결 확인 (환경변수 로드, DB ping 성공)

---

## Phase 2. 온보딩 플로우 (S-01 ~ S-10)

### S-01 워크스루 완주
- [x] 앱 실행 시 INTRO-01 화면 표시
- [x] INTRO-01에서 "다음" 탭 시 INTRO-02로 이동
- [x] INTRO-02에서 "다음" 탭 시 INTRO-03으로 이동
- [x] INTRO-03에서 "시작하기" 탭 시 OB-01로 이동
- [x] 좌우 스와이프로 INTRO 화면 전환

### S-02 워크스루 건너뛰기
- [x] INTRO-01에서 "건너뛰기" 탭 시 OB-01로 이동

### S-03 기본정보 입력
- [x] 닉네임·생년월일·성별 모두 미입력 시 "다음" 버튼 비활성화
- [x] 닉네임만 입력 시 "다음" 버튼 비활성화
- [x] 닉네임·생년월일·성별 모두 입력 시 "다음" 버튼 활성화
- [x] 닉네임 10자 초과 입력 불가
- [x] "다음" 탭 시 POST /user API 호출, 응답 200
- [x] "다음" 탭 시 OB-02로 이동

### S-04 기본정보 건너뛰기
- [x] "나중에 입력하기" 탭 시 API 호출 없이 OB-02로 이동

### S-05 지병 선택
- [x] OB-02 진입 시 5060대 공통 Top 10 지병 버튼 표시
- [x] 지병 버튼 탭 시 선택/해제 토글
- [x] 여러 개 동시 선택 가능
- [x] "여기 없어요" 탭 시 직접 입력 필드 노출
- [x] 직접 입력 후 "+ 추가" 탭 시 항목 추가
- [x] 추가된 항목 개별 삭제(X) 가능
- [x] 알레르기 토글 ON 시 직접 입력 필드 노출
- [x] 알레르기 항목 추가/삭제 가능
- [x] "다음" 탭 시 POST /health API 호출, 응답 200
- [x] "다음" 탭 시 OB-03으로 이동

### S-06 지병 선택 건너뛰기
- [x] "지금은 건너뛰기" 탭 시 API 호출 없이 OB-03으로 이동

### S-07 처방전 촬영 및 약물 확인
- [x] OB-03에서 "처방전 사진 찍기" 탭 시 POST /ocr [MOCK] 호출
- [x] OCR Mock 결과로 OB-04 이동
- [x] OB-04에서 지병 약 섹션 / 보조 약물 섹션 분리 표시
- [x] OB-04에서 처방전 이름 자동 제안 표시
- [x] 처방전 이름 수정 가능
- [x] 약물 카드에서 용도명 변경 가능 (칩 버튼)
- [x] 약물 카드 개별 삭제 가능
- [x] "이게 맞아요, 다음" 탭 시 POST /prescriptions API 호출, 응답 200
- [x] "다음" 탭 시 OB-05로 이동
- [x] 완료 토스트 "총 N개 약이 등록되었어요" 표시

### S-08 처방전 건너뛰기
- [x] "나중에 등록하기" 탭 시 API 호출 없이 OB-05로 이동

### S-09 영양제 등록
- [x] OB-05에서 "영양제 라벨 사진 찍기" 탭 시 POST /label [MOCK] 호출
- [x] Mock 결과로 영양제 카드 추가
- [x] 현재 N개 등록됨 카운터 업데이트
- [x] 영양제 카드 개별 삭제 가능
- [x] "등록 완료, 시작하기" 탭 시 POST /supplements API 호출, 응답 200
- [x] MAIN-01로 이동

### S-10 영양제 건너뛰기
- [x] "지금 먹는 영양제가 없어요" 탭 시 API 호출 없이 MAIN-01으로 이동

---

## Phase 3. 메인 플로우 (S-11 ~ S-19)

### S-11 홈 진입 — 약물 등록 있음
- [x] MAIN-01 진입 시 GET /user, GET /prescriptions, GET /history API 호출
- [x] 닉네임 있으면 "영자님, 오늘도 건강하세요 👋" 표시
- [x] 약물 요약 카드에 등록된 약 이름 표시
- [x] 최근 문의 이력 최대 3개 표시 (최신순)
- [x] 문의 이력 위험도 색상 칩 표시 (safe/caution/danger)

### S-12 홈 진입 — 약물 미등록
- [x] 처방전 없을 시 "등록된 약이 없어요" + 등록 버튼 표시
- [x] 문의 이력 없을 시 빈 상태 표시

### S-13 질문 입력 — 텍스트 분석
- [x] 입력 없이 "분석해줘" 탭 시 토스트 표시, 이동 안 함
- [x] 텍스트 입력 후 "분석해줘" 탭 시 MAIN-04로 이동
- [x] MAIN-04에서 단계 메시지 순차 표시
- [x] MAIN-04에서 타이머 카운트업 표시
- [x] POST /analyze [MOCK] 호출 후 MAIN-05로 이동
- [x] POST /history API 호출, 응답 200
- [x] MAIN-05에서 위험도 배너 표시 (safe/caution/danger)

### S-14 질문 입력 — 라벨 사진 분석
- [x] "영양제·라벨 사진" 탭 시 MAIN-03으로 이동
- [x] MAIN-03에서 촬영 시 POST /label [MOCK] 호출
- [x] 하단 시트 슬라이드 업, 추출 성분 표시
- [x] "이 성분으로 분석하기" 탭 시 MAIN-04로 이동

### S-15 예시 질문 칩 탭
- [x] 예시 칩 탭 시 입력 필드에 텍스트 자동 입력

### S-16 분석 결과 — 안전
- [x] level: 'safe' 시 초록 배너 + "드셔도 괜찮아요 ✓" 표시
- [x] 대안 제시 섹션 미표시

### S-17 분석 결과 — 주의
- [x] level: 'caution' 시 노란 배너 + "조심해서 드셔야 해요 ⚠" 표시
- [x] 대안 제시 섹션 표시

### S-18 분석 결과 — 위험
- [x] level: 'danger' 시 빨간 배너 + "드시면 안 돼요 ✕" 표시
- [x] 대안 제시 섹션 표시
- [x] "전문가에게 직접 상담하기" 버튼 표시

### S-19 분석 결과 — 가족 공유
- [x] "가족에게 공유" 탭 시 Web Share API 호출

---

## Phase 4. 서브 플로우 (S-20 ~ S-30)

### S-20 내 약물 관리 조회
- [x] 탭바 "내 약물" 탭 시 GET /prescriptions, GET /supplements API 호출
- [x] 상단 "처방전 N개 · 약 N개 · 영양제 N개" 표시
- [x] 처방전 카드 단위로 표시
- [x] 처방전 카드 탭 시 약 목록 펼치기/접기

### S-21 처방전 추가
- [x] "+ 처방전 추가" 탭 시 SUB-02로 이동
- [x] 촬영 → [MOCK] OCR → OB-04로 이동 (추가 모드)
- [x] 저장 후 POST /prescriptions API 호출
- [x] SUB-01 현황 수치 업데이트

### S-22 처방전 교체
- [x] "교체" 탭 시 경고 다이얼로그 표시
- [x] 확인 시 SUB-03으로 이동
- [x] 교체 대상 처방전 이름 + 포함 약 목록 표시
- [x] 저장 후 PUT /prescriptions/{id} API 호출

### S-23 처방전 삭제
- [x] "삭제" 탭 시 확인 다이얼로그 표시
- [x] 처방전 1개뿐일 때 삭제 버튼 비활성화
- [x] 확인 시 DELETE /prescriptions/{id} API 호출
- [x] 현황 수치 업데이트

### S-24 영양제 추가
- [x] "+ 영양제 추가" 탭 시 라벨 촬영 UI 노출
- [x] [MOCK] VLM → POST /supplements API 호출
- [x] 영양제 카드 추가

### S-25 문의 이력 — 이력 있음
- [x] 탭바 "이력" 탭 시 GET /history API 호출
- [x] 이력 카드 최신순 표시
- [x] 위험도 색상 칩 표시

### S-26 문의 이력 — 이력 없음
- [x] 이력 없을 시 SUB-05 표시
- [x] "물어보러 가기" 탭 시 MAIN-02로 이동

### S-27 문의 이력 필터
- [x] "위험" 필터 탭 시 level: 'danger' 카드만 표시
- [x] "주의" 필터 탭 시 level: 'caution' 카드만 표시
- [x] "안전" 필터 탭 시 level: 'safe' 카드만 표시
- [x] "전체" 필터 탭 시 전체 표시

### S-28 과거 결과 재조회
- [x] 이력 카드 탭 시 MAIN-05로 이동
- [x] GET /history/{id} API 호출, 해당 결과 렌더링
- [x] "이 결과는 ○○일 기준이에요" 날짜 배너 표시

### S-29 월간 복용 확인 팝업 — 그대로
- [x] last_prescription_check 30일 경과 시 앱 실행 시 SUB-06 팝업 표시
- [x] 딤(dim) 배경 표시
- [x] 처방전별 "그대로예요 / 바뀌었어요" 버튼 표시
- [x] 모두 "그대로예요" 후 닫기 시 PUT /user (last_prescription_check 업데이트) 호출
- [x] 토스트 "건강하게 잘 챙겨드시고 있네요! 👍" 표시

### S-30 월간 복용 확인 팝업 — 변경 있음
- [x] "바뀌었어요" 탭 시 해당 카드 취소선 표시
- [x] "변경된 약이 있어요" 탭 시 SUB-01로 이동

### S-31 재방문
- [x] onboardingComplete === true 시 INTRO 스킵, MAIN-01 바로 표시
- [x] 30일 미경과 시 SUB-06 팝업 미표시

---

## Phase 5. 백엔드 API (FastAPI)

### 기본
- [x] POST /user — 기본정보 저장, Supabase user_profile 레코드 생성
- [x] GET /user — 기본정보 조회
- [x] PUT /user — 기본정보 업데이트 (last_prescription_check 포함)
- [x] POST /health — 지병·알레르기 저장
- [x] GET /health — 지병·알레르기 조회

### 처방전
- [x] GET /prescriptions — 처방전 + 약물 목록 조회 (JOIN)
- [x] POST /prescriptions — 처방전 + 약물 저장
- [x] PUT /prescriptions/{id} — 처방전 교체 (기존 drugs 삭제 후 재저장)
- [x] DELETE /prescriptions/{id} — 처방전 + 약물 삭제 (CASCADE)

### 영양제
- [x] GET /supplements — 영양제 목록 조회
- [x] POST /supplements — 영양제 저장
- [x] DELETE /supplements/{id} — 영양제 삭제

### 문의 이력
- [x] GET /history — 문의 이력 조회 (최신순)
- [x] GET /history/{id} — 특정 이력 조회
- [x] POST /history — 문의 이력 저장

### Mock AI
- [x] POST /ocr — [MOCK] 처방전 OCR 결과 반환
- [x] POST /label — [MOCK] 영양제 라벨 VLM 결과 반환
- [x] POST /analyze — [MOCK] 약물 상호작용 분석 결과 반환

---

## Phase 6. AI 실제 연동 — 백엔드

#### 6-1. 의존성 및 환경
- [x] `requirements.txt`에 `google-genai` 추가 및 `import google.genai` 성공 테스트

#### 6-2. 처방전 OCR 실제 연동
- [x] `POST /ocr`에 이미지(multipart) 없이 호출 시 422 반환
- [x] `POST /ocr`에 처방전 이미지 전송 시 Gemini 호출, 약품명/투약량/횟수/일수/용법/주의사항 포함 JSON 반환
  - 응답 스키마: `{ drugs: [{ name, dosage, frequency, days, usage, cautions }] }`
  - 모델: AI Agent와 동일 모델 (`gemini-3.1-flash-lite`)
  - 환경변수 `GEMINI_API_KEY` 사용

#### 6-3. 영양제 라벨 VLM 실제 연동
- [x] `POST /label`에 이미지(multipart) 없이 호출 시 422 반환
- [x] `POST /label`에 영양제 라벨 이미지 전송 시 Gemini 호출, 제품명/영양 성분 반환
  - 응답 스키마: `{ name, nutrients: [{ ingredient, amount, unit }] }`
  - 절대 함량만 추출 (비율 % 제외), 천 단위 쉼표 제거
  - 모델: `gemini-3.1-flash-lite`

#### 6-4. 약물-영양제-음식 상호작용 AI Agent 실제 연동
- [x] `POST /analyze` body `{ question, context }` 전송 시 Gemini 호출, 새 스키마로 응답 반환
  - 응답 스키마:
    ```json
    {
      "level": "safe | caution | danger",
      "doctorOpinion": { "summary": "...", "detail": "..." },
      "pharmacistOpinion": { "summary": "...", "detail": "..." },
      "alternatives": ["..."]
    }
    ```
  - 모델: `gemini-3.1-flash-lite`
  - JSON 구조화 실패 시 재시도 (최대 2회)
- [x] `level` 값이 항상 `safe | caution | danger` 중 하나임을 단언
- [x] 기존 테스트의 `"warning"` → `"caution"` 수정 (test_mock_ai.py 버그 수정)

---

## Phase 7. 카메라 촬영 기능 — 프론트엔드

#### 7-1. Sub02 — 처방전 추가 (카메라 촬영)
- [x] "처방전 촬영하기" 탭 시 `input[type=file accept="image/*" capture="environment"]` 트리거 (카메라 전용)
- [x] 촬영 후 `FormData`에 담아 `POST /ocr` 전송, 결과를 `ocrStore`에 저장 후 `/sub-07` 이동

#### 7-2. Sub03 — 처방전 교체 (카메라 촬영)
- [x] "처방전 촬영하기" 탭 시 `input[type=file accept="image/*" capture="environment"]` 트리거
- [x] 촬영 후 `FormData`로 `POST /ocr` 전송, `ocrStore` 저장 → `/sub-07` 이동

#### 7-3. Sub08 — 영양제 추가 (카메라 촬영)
- [x] "영양제 라벨 사진 찍기" 탭 시 `input[type=file accept="image/*" capture="environment"]` 트리거 (카메라 전용)
- [x] 촬영 후 `FormData`로 `POST /label` 전송, 응답의 `name`/`nutrients`로 폼 자동 채움
- [x] 기존 하드코딩 fallback 제거

---

## Phase 8. AI 연동 스키마 통일 — 프론트엔드

#### 8-1. analyzeStore 스키마 업데이트
- [x] `analyzeStore` 타입을 새 스키마로 변경
  - `summary: string`, `detail: string` → `doctorOpinion: { summary, detail }`, `pharmacistOpinion: { summary, detail }`
  - `level: 'safe' | 'caution' | 'danger'` 유지

#### 8-2. Main05 화면 업데이트
- [x] `doctorOpinion.summary` / `pharmacistOpinion.summary` 표시
- [x] "자세히 보기" 토글 시 `doctorOpinion.detail` / `pharmacistOpinion.detail` 표시

---

## 배포를 위해 AI가 해야하는 것

> 서버 아키텍처 설계 문서 기준: 프론트엔드(AWS Lightsail $5) + 백엔드 GCP($13) + AI 서버 GCP($13), 총 $31/월.
> 백엔드는 CRUD 전용, AI 서버는 OCR/라벨/분석 전용으로 별도 인스턴스 배포.

### D-1. AI 서버 코드 분리

- [x] 루트에 `ai_server/` 디렉토리 생성
- [x] `ai_server/app/main.py` 생성 — 독립 FastAPI 앱, `/health` 엔드포인트 포함
- [x] `ai_server/app/routers/ai.py` 생성 — `backend/app/routers/ai.py`의 OCR·라벨·분석 라우터 이동
- [x] `ai_server/requirements.txt` 생성 — `google-genai`, `fastapi`, `uvicorn` 등 AI 서버 의존성만
- [x] `backend/app/routers/ai.py` 제거 — AI 라우터를 백엔드에서 삭제
- [x] `backend/app/main.py` 에서 AI 라우터 등록 제거
- [x] 백엔드에 `httpx` 추가 — `/ocr`, `/label`, `/analyze` 요청을 AI 서버로 포워딩하는 프록시 라우터 작성
  - 백엔드가 요청을 받아 `http://ai-server:8001`로 전달, 응답을 그대로 반환
  - 프론트엔드·Vite proxy 설정 변경 없이 투명하게 동작
- [x] `backend/tests/`에서 AI 관련 테스트를 `ai_server/tests/`로 이동
- [x] 로컬 테스트: 백엔드 8000, AI 서버 8001로 동시 실행 후 `/analyze` 정상 응답 확인

### D-2. 도커화

- [x] `frontend/Dockerfile` 작성 — `npm run build` → nginx로 정적 파일 서빙
- [x] `frontend/nginx.conf` 작성 — SPA 라우팅(`try_files $uri /index.html`), gzip 압축
- [x] `backend/Dockerfile` 작성 — `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1` (초기값, 부하 테스트 후 조정)
- [x] `ai_server/Dockerfile` 작성 — `uvicorn app.main:app --host 0.0.0.0 --port 8001 --workers 1`
- [x] 루트에 `docker-compose.yml` 작성 — 로컬 개발용 (backend:8000, ai_server:8001, frontend:80)
  - `backend`가 `ai_server` 서비스명으로 접근할 수 있도록 네트워크 구성
  - `.env` 파일로 환경변수 주입
- [x] `.dockerignore` 작성 (frontend, backend, ai_server 각각)
- [x] `docker-compose up` 후 `/analyze` end-to-end 정상 동작 확인

---

## AI 서버 동시성 제어 및 모니터링

> 서버 아키텍처 설계 문서(C.2, C.3) 기준: AI 서버는 동시 워커 20개로 설계, 메트릭 버퍼로 Gemini 응답 시간·에러율 수집.

### E-1. 동시 워커 20개 Queue Scheduling

- [x] `ai_server/tests/test_concurrency.py` 작성 — `ai_server/app/concurrency.py`에 `MAX_CONCURRENT_GEMINI_CALLS = 20`, `GEMINI_SEMAPHORE = asyncio.Semaphore(20)` 존재 검증
- [x] `ai_server/app/concurrency.py` 생성 — 위 상수/세마포어 정의
- [x] `ai_server/tests/test_concurrency.py`에 동시성 제한 테스트 추가 — 25개의 가짜 비동기 작업(`asyncio.sleep`)을 세마포어로 감싸 동시 실행 시, 동시 실행 개수가 20을 절대 넘지 않음을 카운터로 검증
- [x] `ai_server/app/routers/ai.py` 수정 — `/ocr`, `/label`, `/analyze` 각각에서 Gemini 호출 구간을 `async with GEMINI_SEMAPHORE:`로 감쌈
  - `/analyze`는 현재 `def`(동기)이므로 `async def`로 변경하고, 블로킹 호출인 `_client.models.generate_content(...)`는 `await asyncio.to_thread(...)`로 실행
- [x] `ai_server/tests/test_ai_router.py`, `test_mock_ai.py` 등 기존 테스트가 세마포어 적용 후에도 통과하는지 확인 (회귀 테스트)

### E-2. Gemini API 장애/처리량/지연시간 메트릭 수집 및 대시보드

- [x] `ai_server/tests/test_metrics.py` 작성 — `ai_server/app/metrics.py`의 `record_metric(endpoint, status_code, latency_ms, success)`가 호출 시 인메모리 버퍼에 기록되는지 검증
- [x] `ai_server/app/metrics.py` 생성 — 인메모리 리스트 기반 메트릭 버퍼(최근 N건 캡, 예: 1000건)와 `record_metric()` 구현
- [x] `ai_server/tests/test_metrics.py`에 집계 테스트 추가 — `get_metrics_summary()`가 엔드포인트별 총 요청 수, 성공/실패 수, status_code별 에러 분포, 평균/최소/최대 지연시간(ms), 최근 1분간 처리량(req/min)을 반환하는지 검증
- [x] `ai_server/app/metrics.py`에 `get_metrics_summary()` 구현
- [x] `ai_server/app/routers/ai.py` 수정 — `/ocr`, `/label`, `/analyze`에서 Gemini 호출 시작/종료 시각을 측정해 `record_metric()` 호출
  - 성공 시 `status_code=200, success=True`
  - Gemini 호출 예외 발생 시, 예외에서 status_code 추출 가능하면 사용(예: `google.genai.errors.APIError.code`), 없으면 `500`으로 기록 후 예외 재발생
- [x] `ai_server/tests/test_metrics.py`에 라우터 통합 테스트 추가 — Gemini 클라이언트를 mock하여 `/analyze` 성공/실패 호출 후 메트릭 버퍼에 기록되는지 검증
- [x] `ai_server/tests/test_metrics_router.py` 작성 — `GET /metrics`가 `get_metrics_summary()` 결과를 JSON으로 반환하는지 검증 (TestClient)
- [x] `ai_server/app/routers/metrics.py` 생성 — `GET /metrics` 라우터 구현
- [x] `ai_server/app/main.py` 수정 — `metrics.router` 등록
- [x] `ai_server/tests/test_dashboard.py` 작성 — `GET /dashboard`가 200과 `text/html` 응답을 반환하는지 검증 (TestClient)
- [x] `ai_server/app/static/dashboard.html` 생성 — 외부 라이브러리 없는 vanilla HTML+JS 페이지. 5초 주기로 `/metrics`를 fetch해 엔드포인트별 요청 수/성공·실패 수/status_code별 에러 분포/평균·최소·최대 지연시간/최근 1분 처리량을 표 + 퍼센트 너비 div 막대로 시각화
- [x] `ai_server/app/routers/metrics.py` 또는 `main.py` 수정 — `GET /dashboard`가 `dashboard.html`을 `HTMLResponse`로 반환하도록 라우트 추가 (StaticFiles 마운트 대신 단일 라우트로 단순화)
- [x] 로컬 통합 확인: `ai_server` 8001 단독 실행 후 `/analyze` 몇 차례 호출(mock 또는 실제 Gemini) → `http://localhost:8001/dashboard`에서 메트릭 반영 확인

---

## 하네스를 위해 AI가 해야하는 것

> `ai_server/app/routers/ai.py`의 단발성 Gemini 호출을 Harness 루프 기반 Agentic AI로 전환.
> Agent가 validate → gather_context → analyze → finish 순서를 자율 결정,
> Harness가 allowed_actions / max_steps / completion_conditions로 행동 범위 제어.
> 범위는 AI 분석 경로로 한정한다. Supabase, user_id 발급, 인증/권한, 사용자별 저장소 분리는 도입하지 않는다.
> 현재처럼 `backend/app/store.py`의 인메모리 싱글톤 데이터를 사용하며, `gather_context`는 백엔드 API에서 현재 사용자 데이터를 읽는다.
> TDD 원칙: 각 체크박스는 테스트 1개 작성(Red) → 최소 구현(Green) → 필요한 구조 정리(Refactor) 순서로 진행한다.

### H-1. 파일 구조 생성

- [x] 테스트: `ai_server/tests/test_harness_tools.py`에서 `app.harness.tools` import 가능성 검증 → `ai_server/app/harness/__init__.py`, `tools.py` 생성
- [x] 테스트: `ai_server/tests/test_harness_loop.py`에서 `app.harness.harness` import 가능성 검증 → `harness.py` 생성
- [x] 테스트: `HARNESS_POLICY`에 `allowed_actions`, `max_steps`, `completion_conditions`가 존재하고 완료 action이 allowed action에 포함되는지 검증 → 최소 상수 정의

### H-2. Gemini function calling 연동 확인

- [x] `tools=` 파라미터로 단순 tool 1개 호출 성공하는 smoke 테스트 작성 및 통과
- [x] 6개 tool의 Gemini function declaration JSON Schema 정의
  - `validate_query` / `gather_context` / `ask_clarification` / `analyze` / `reject` / `finish`
- [x] `_call_with_tools(messages, tool_declarations) → (action_name, action_args)` 헬퍼 작성
- [x] 테스트: Gemini가 allowed action 밖의 이름을 반환하지 않는 정상 케이스를 mock으로 검증

### H-3. Tools 구현 (tools.py)

- [x] `validate_query(question: str) → dict` 구현 — Gemini 호출해 `{ is_relevant, is_clear, items, missing_info }` 반환
- [x] `validate_query` 테스트: `"오늘 날씨 어때?"` → `is_relevant: false`
- [x] `validate_query` 테스트: `"이거 먹어도 돼요?"` → `is_clear: false`
- [x] `validate_query` 테스트: `"홍삼 먹어도 되나요?"` → `is_relevant: true, is_clear: true`
- [x] `gather_context() → dict` 구현 — Supabase/user_id 없이 현재 백엔드 API의 인메모리 싱글톤 데이터 조회 (`GET /prescriptions`, `GET /supplements`, `GET /health-info`, `/health-info` 404는 정상적인 빈 프로필로 처리)
- [x] `gather_context` 테스트: 백엔드 API가 모두 비어있거나 404인 경우 → `drugs: [], supplements: [], health_conditions: [], allergies: []`
- [x] `gather_context` 테스트: 처방전/영양제/건강정보 응답이 있는 경우 → 분석용 dict로 정규화
- [x] `ask_clarification(reason: str) → dict` 구현 — `{ clarification_prompt: str }` 반환
- [x] `analyze(question: str, context: str) → dict` 구현 — 기존 analyze 로직 재사용
- [x] `analyze` 테스트: level이 항상 `safe | caution | danger` 중 하나
- [x] `reject(reason: str) → dict` 구현 — `{ type: "rejection", message: str }` 반환
- [x] `finish(result: dict) → dict` 구현 — `{ type: "analysis", **result }` 반환

### H-4. Harness 루프 구현 (harness.py)

- [x] `HARNESS_POLICY` 상수 정의 (goal, allowed_actions, max_steps: 7, completion_conditions) — validate → gather_context → analyze → finish 기본 4 step과 self-evaluate 재시도 최대 2회를 수용
- [x] `HARNESS_POLICY`의 completion_conditions에 `finish`, `reject`, `ask_clarification` 포함
- [x] `execute_tool(name, args) → dict` 구현
- [x] `execute_tool` 테스트: allowed_actions 외 이름 → `PermissionError`
- [x] `run_agent(question: str) → dict` 구현 — messages 초기화 → for step in range(max_steps) → _call_with_tools → execute_tool → observation 추가 → completion_conditions 확인
- [x] `run_agent` 분기 규칙: `is_relevant=false` → `reject`
- [x] `run_agent` 분기 규칙: `is_relevant=true, is_clear=false` → `ask_clarification`
- [x] `run_agent` 분기 규칙: `is_relevant=false, is_clear=true`처럼 애매한 조합 → 무관 질문으로 보고 `reject`
- [x] `run_agent` 분기 규칙: `is_relevant=false, is_clear=false` → 서비스 범위 밖이거나 정보 부족한 질문으로 보고 `reject` 우선
- [x] `run_agent` 테스트: 무관한 질문 → reject 2 step 내 종료
- [x] `run_agent` 테스트: 불명확한 질문 → clarification 2 step 내 종료
- [x] `run_agent` 테스트: 정상 질문 → finish → analysis 결과 반환
- [x] `run_agent` 테스트: max_steps 도달 → `{ type: "error", message: "분석 한도 초과" }` 반환
- [x] trace 기록 — 각 step의 action/args/observation 리스트 누적

### H-5. Harness.evaluate() 품질 검증 루프

- [ ] `evaluate(result, question) → (bool, int, list)` 구현 — score >= 70 → True
- [ ] `evaluate`: detail 2문장 이상 여부 (-20점 미달 시)
- [ ] `evaluate`: 행동 지침 키워드(복용 시간, 간격 등) 포함 여부 (-20점)
- [ ] `evaluate`: 상담 권유 문구(의사, 약사) 포함 여부 (-20점)
- [ ] `evaluate` 테스트: 짧은 detail → score < 70 / 충분한 detail + 행동지침 + 상담권유 → score >= 70
- [ ] `run_agent`에 self-evaluate 재시도 통합 — evaluate() False → issues를 memory에 기록 + strategy 수정 후 analyze 재호출 (최대 2회)
- [ ] self-evaluate 재시도 테스트: 1차 짧은 응답 → evaluate 실패 → 재시도 → 더 긴 응답 반환

### H-6. /analyze 엔드포인트 통합

- [ ] `AnalyzeRequest` 스키마는 `{ question: str, context: str = "" }` 유지 — 프론트/백엔드의 기존 요청 계약을 최대한 유지한다.
- [ ] Harness 전환 후 기본 context는 `gather_context()`가 백엔드 API에서 구성한다.
- [ ] 기존 클라이언트가 보내는 `context`는 호환용으로 받되, 새 하네스 경로에서는 우선순위를 낮추거나 분석 보조 정보로만 사용한다.
- [ ] `ai.py`의 `analyze()` 핸들러에서 `harness.run_agent(question)` 호출로 교체
- [ ] 응답 스키마에 `type` 필드 포함: `"analysis" | "clarification" | "rejection" | "error"`
- [ ] 통합 테스트: 무관한 질문 → `{ type: "rejection" }` 반환
- [ ] 통합 테스트: 불명확한 질문 → `{ type: "clarification", clarification_prompt }` 반환
- [ ] 통합 테스트: 정상 질문 → `{ type: "analysis", level, doctorOpinion, ... }` 반환

### H-7. 프론트엔드 대응

- [ ] userId 상태 추가 없음 — POST /user 응답/저장 구조 변경하지 않음
- [ ] `/analyze` 요청 body는 기존 `{ question, context }` 형태 유지
- [ ] `analyzeStore`에 `responseType: "analysis" | "clarification" | "rejection" | "error" | null` 필드 추가
- [ ] `Main04.tsx`: 응답 type이 `"clarification"`이면 clarification_prompt 표시 후 Main02 복귀
- [ ] `Main04.tsx`: 응답 type이 `"rejection"`이면 message 토스트 표시 후 Main02 복귀
- [ ] `Main04.tsx`: 응답 type이 `"error"`이면 message 표시 후 Main02 복귀
- [ ] `Main04.tsx`: 응답 type이 `"analysis"`이면 기존대로 Main05 이동
- [ ] `Main02.tsx`: clarification_prompt 있으면 입력 필드 위에 힌트 표시
