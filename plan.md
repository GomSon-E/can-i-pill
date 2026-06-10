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
- [x] `backend/Dockerfile` 작성 — `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 3`
- [x] `ai_server/Dockerfile` 작성 — `uvicorn app.main:app --host 0.0.0.0 --port 8001 --workers 1`
- [x] 루트에 `docker-compose.yml` 작성 — 로컬 개발용 (backend:8000, ai_server:8001, frontend:80)
  - `backend`가 `ai_server` 서비스명으로 접근할 수 있도록 네트워크 구성
  - `.env` 파일로 환경변수 주입
- [x] `.dockerignore` 작성 (frontend, backend, ai_server 각각)
- [x] `docker-compose up` 후 `/analyze` end-to-end 정상 동작 확인

---

## E. AI Queue Scheduling, Metrics, Dashboard

> 서버 아키텍처 설계 문서의 "AI 동시 워커 20개" 목표를 실제 구현으로 연결한다.
> 목표: AI 요청을 큐로 제어하고, 장애상황/status code/throughput/latency를 수집해 간단한 대시보드에서 확인한다.

### E-1. Queue Scheduling 요구사항 확정

- [ ] AI 작업 대상 엔드포인트 범위 결정 (`/analyze` 우선, `/ocr`, `/label` 포함 여부 결정)
- [ ] 사용자-facing 처리 방식 결정: 기존 동기 응답 유지 vs `job_id` 기반 비동기 polling
- [ ] 목표 동시 실행 수를 설정값으로 정의 (`AI_MAX_CONCURRENT_JOBS=20`)
- [ ] 큐 대기 최대 개수 설정값 정의 (`AI_QUEUE_MAX_SIZE`)
- [ ] 큐 대기 timeout / 작업 실행 timeout 정책 정의
- [ ] 큐 포화 시 반환할 status code와 응답 body 정의 (`429` 또는 `503`)
- [ ] 작업 실패/timeout/취소 상태 모델 정의 (`queued | running | succeeded | failed | timeout | cancelled`)
- [ ] TDD 기준 API 계약을 문서화

### E-2. AI Job 모델 및 저장소

- [ ] `ai_server/app/job_store.py` 생성 — 인메모리 job 저장소 구현
- [ ] `AIJob` 모델 정의: `id`, `kind`, `status`, `created_at`, `started_at`, `finished_at`, `queue_wait_ms`, `run_ms`, `error`, `result`
- [ ] job id 생성 테스트 작성
- [ ] job 상태 전이 테스트 작성 (`queued → running → succeeded/failed/timeout`)
- [ ] 오래된 job 정리 TTL 설정값 추가 (`AI_JOB_TTL_SECONDS`)
- [ ] TTL 만료 job 정리 테스트 작성
- [ ] 서버 재시작 시 job 유실 가능성을 PoC 제약으로 문서화

### E-3. Queue Scheduler 구현

- [ ] `ai_server/app/scheduler.py` 생성 — `asyncio.Queue` + `asyncio.Semaphore` 기반 scheduler 구현
- [ ] 동시에 실행되는 job 수가 `AI_MAX_CONCURRENT_JOBS`를 넘지 않는 테스트 작성
- [ ] 큐 순서가 FIFO로 유지되는 테스트 작성
- [ ] 큐 포화 시 새 job이 거절되는 테스트 작성
- [ ] job timeout 발생 시 `timeout` 상태로 기록되는 테스트 작성
- [ ] scheduler 시작/종료 lifecycle을 FastAPI startup/shutdown에 연결
- [ ] `/health` 응답에 scheduler 상태 포함 (`queue_size`, `running_jobs`, `max_concurrent_jobs`)

### E-4. AI API Queue 적용

- [ ] `POST /analyze/jobs` 추가 — 분석 job 생성 후 `202 Accepted` + `job_id` 반환
- [ ] `GET /analyze/jobs/{job_id}` 추가 — job 상태/result 조회
- [ ] `POST /analyze` 기존 동기 API는 내부적으로 queue를 사용하도록 변경
- [ ] 동기 `/analyze`가 queue wait + run timeout을 넘으면 명확한 오류 응답 반환
- [ ] `/ocr/jobs`, `/label/jobs` 필요 여부 결정 후 동일 패턴 적용
- [ ] 백엔드 프록시에 job API 전달 테스트 추가
- [ ] 프론트엔드 기존 플로우가 동기 `/analyze`로 계속 동작하는 회귀 테스트 작성

### E-5. Status Code / 장애상황 표준화

- [ ] AI 서버 공통 오류 응답 스키마 정의: `{ error: { code, message, retryable, requestId } }`
- [ ] Gemini API timeout → `504 Gateway Timeout` 매핑 테스트
- [ ] Gemini API rate limit → `429 Too Many Requests` 매핑 테스트
- [ ] Gemini API 5xx/일시 장애 → `502 Bad Gateway` 또는 `503 Service Unavailable` 매핑 테스트
- [ ] JSON schema 파싱 실패/재시도 소진 → `502 Bad Gateway` 매핑 테스트
- [ ] 큐 포화 → `429` 또는 `503` 매핑 테스트
- [ ] 잘못된 사용자 입력 → `422` 유지 테스트
- [ ] 백엔드 프록시가 AI 서버 status code/body를 보존하는 테스트 작성

### E-6. Metrics 수집

- [ ] `ai_server/app/metrics.py` 생성 — 인메모리 metrics registry 구현
- [ ] 요청 counter 수집: endpoint, method, status_code, error_code
- [ ] job counter 수집: kind, status
- [ ] queue gauge 수집: `queue_size`, `running_jobs`, `max_concurrent_jobs`
- [ ] latency histogram 또는 bucket 수집: queue wait, AI run time, total request time
- [ ] throughput 계산용 rolling window 구현 (`requests_per_minute`, `jobs_per_minute`)
- [ ] p50/p95/p99 latency 계산 테스트 작성
- [ ] metrics 수집이 요청 실패 상황에서도 누락되지 않는 테스트 작성
- [ ] metrics 메모리 상한/rolling window 보관 기간 설정값 추가

### E-7. Metrics API

- [ ] `GET /metrics/summary` 추가 — dashboard용 JSON 반환
- [ ] `GET /metrics/recent` 추가 — 최근 N분 시계열 데이터 반환
- [ ] `GET /metrics/errors` 추가 — 최근 오류 목록/status code 분포 반환
- [ ] metrics API 응답 스키마 테스트 작성
- [ ] 빈 데이터 상태에서도 200 + 기본값 반환 테스트 작성
- [ ] metrics API에 관리자용 간단한 보호 장치 적용 여부 결정 (`METRICS_TOKEN`)
- [ ] 백엔드 프록시에서 `/ai-metrics/*` 또는 관리자 API 경로로 metrics 전달

### E-8. Dashboard 개발

- [ ] 프론트엔드 관리자/운영용 dashboard 라우트 추가 (`/admin/ai-dashboard`)
- [ ] summary 카드 표시: queue size, running jobs, throughput, p95 latency, error rate
- [ ] status code 분포 표시
- [ ] latency 추이 차트 표시 (최근 N분)
- [ ] queue depth / running jobs 추이 표시
- [ ] 최근 오류 리스트 표시: 시간, endpoint, status code, error code, message
- [ ] 자동 새로고침 interval 구현 (`5s` 기본)
- [ ] 로딩/빈 상태/metrics API 실패 상태 UI 구현
- [ ] dashboard 컴포넌트 테스트 작성
- [ ] Playwright 또는 RTL로 핵심 렌더링 확인

### E-9. 부하 테스트 및 검증

- [ ] 로컬 fake Gemini 응답 지연 서버 또는 monkeypatch 기반 부하 테스트 작성
- [ ] 50개 동시 `/analyze` 요청 시 동시 실행이 20개 이하인지 검증
- [ ] 50개 동시 요청이 3개 batch로 처리되는지 검증
- [ ] queue wait / run latency / total latency metrics가 기대 범위로 기록되는지 검증
- [ ] 큐 포화 시 오류율과 status code가 dashboard에 표시되는지 검증
- [ ] `backend` 전체 테스트 통과 확인
- [ ] `ai_server` 전체 테스트 통과 확인
- [ ] `docker-compose up` 환경에서 queue + metrics + dashboard smoke test 수행
