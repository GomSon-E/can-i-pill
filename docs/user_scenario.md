# 이거뭐약 — User Scenario 문서
> Claude Code + TDD / Ralph Loop 개발용
> AI 기능(OCR, VLM, Agent)은 모두 Mock으로 처리

---

## 문서 사용 방법

- 각 시나리오는 **Given / When / Then** 구조로 작성됨
- `[MOCK]` 표시는 실제 AI 호출 대신 mock 데이터를 반환하는 지점
- `[API]` 표시는 FastAPI 백엔드 호출 지점 (데이터 저장/조회 → Supabase PostgreSQL)
- `[VALIDATE]` 표시는 입력값 검증 지점
- 각 시나리오는 독립적으로 테스트 가능해야 함

---

---

## 아키텍처

```
React (프론트)
    ↕ HTTP/REST
FastAPI (백엔드)
    ├── Supabase (PostgreSQL) — 데이터 저장/조회
    └── AI: [MOCK] → 나중에 실제 OCR/VLM/Agent 교체
```

**API 엔드포인트 목록**

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | /user | 기본정보 저장 |
| GET | /user | 기본정보 조회 |
| POST | /health | 지병·알레르기 저장 |
| GET | /health | 지병·알레르기 조회 |
| GET | /prescriptions | 처방전 목록 조회 |
| POST | /prescriptions | 처방전 추가 |
| PUT | /prescriptions/{id} | 처방전 교체 |
| DELETE | /prescriptions/{id} | 처방전 삭제 |
| GET | /supplements | 영양제 목록 조회 |
| POST | /supplements | 영양제 추가 |
| DELETE | /supplements/{id} | 영양제 삭제 |
| GET | /history | 문의 이력 조회 |
| POST | /history | 문의 이력 저장 |
| POST | /ocr | [MOCK] 처방전 OCR |
| POST | /label | [MOCK] 영양제 라벨 VLM |
| POST | /analyze | [MOCK] 약물 상호작용 분석 |
| PUT | /user | 기본정보 및 last_prescription_check 업데이트 |

---

## Supabase DB 스키마

```sql
-- 사용자 기본정보
CREATE TABLE user_profile (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  nickname VARCHAR(10),
  birth_year INTEGER,
  birth_month INTEGER,
  birth_day INTEGER,
  gender VARCHAR(10) CHECK (gender IN ('female', 'male', 'none')),
  onboarding_complete BOOLEAN DEFAULT FALSE,
  last_prescription_check TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 지병 및 알레르기
CREATE TABLE health_info (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES user_profile(id),
  conditions TEXT[] DEFAULT '{}',
  custom_conditions TEXT[] DEFAULT '{}',
  has_allergy BOOLEAN DEFAULT FALSE,
  allergies TEXT[] DEFAULT '{}',
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 처방전
CREATE TABLE prescriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES user_profile(id),
  name VARCHAR(50) NOT NULL,  -- '혈압 처방전'
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 약물 (처방전에 속함)
CREATE TABLE drugs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  prescription_id UUID REFERENCES prescriptions(id) ON DELETE CASCADE,
  usage_name VARCHAR(50) NOT NULL,      -- '혈압약'
  ingredient_name VARCHAR(100) NOT NULL, -- '암로디핀 5mg'
  is_condition BOOLEAN NOT NULL          -- true: 지병약 / false: 보조약
);

-- 영양제
CREATE TABLE supplements (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES user_profile(id),
  product_name VARCHAR(100) NOT NULL,  -- '오메가3'
  ingredients TEXT,                     -- 'EPA·DHA 800mg'
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 문의 이력
CREATE TABLE history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES user_profile(id),
  question TEXT NOT NULL,
  image_used BOOLEAN DEFAULT FALSE,
  level VARCHAR(10) CHECK (level IN ('safe', 'caution', 'danger')),
  doctor_summary TEXT,
  doctor_detail TEXT,
  pharmacist_summary TEXT,
  pharmacist_detail TEXT,
  alternatives TEXT[] DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 마지막 복용 확인일: user_profile.last_prescription_check 컬럼으로 관리
```

---

## 데이터 모델 (Supabase 기준)

```typescript
// 사용자 기본 정보
user: {
  nickname: string        // 최대 10자, 없으면 null
  birthYear: number       // 예: 1961
  birthMonth: number      // 1~12
  birthDay: number        // 1~31
  gender: 'female' | 'male' | 'none'
  onboardingComplete: boolean
}

// 지병 및 알레르기
health: {
  conditions: string[]    // 예: ['고혈압', '당뇨']
  customConditions: string[]  // '여기 없어요'로 직접 입력한 것
  hasAllergy: boolean
  allergies: string[]     // 예: ['복숭아', '페니실린']
}

// 처방전 단위 약물 관리
prescriptions: [
  {
    id: string            // UUID
    name: string          // 예: '혈압 처방전'
    createdAt: string     // ISO 날짜
    drugs: [
      {
        id: string
        usageName: string   // 용도명: '혈압약'
        ingredientName: string  // 성분명: '암로디핀 5mg'
      }
    ]
  }
]

// 영양제
supplements: [
  {
    id: string
    productName: string   // 예: '오메가3'
    ingredients: string   // 예: 'EPA·DHA 800mg'
    createdAt: string
  }
]

// 문의 이력
history: [
  {
    id: string
    createdAt: string
    question: string      // 예: '홍삼 먹어도 되나요?'
    imageUsed: boolean    // 라벨 사진 사용 여부
    level: 'safe' | 'caution' | 'danger'
    doctorOpinion: {
      summary: string
      detail: string
    }
    pharmacistOpinion: {
      summary: string
      detail: string
    }
    alternatives: string[]
  }
]

// 월간 복용 확인
lastPrescriptionCheck: string  // ISO 날짜
```

---

## Mock 데이터 정의

```typescript
// mockOCRResult — ob_03 촬영 후 반환
export const MOCK_OCR_RESULT = {
  drugs: [
    { ingredientName: '메트포르민 500mg', isCondition: true },
    { ingredientName: '암로디핀 5mg', isCondition: true },
    { ingredientName: '로사르탄 50mg', isCondition: true },
    { ingredientName: '오메프라졸 20mg', isCondition: false },
    { ingredientName: '이부프로펜 200mg', isCondition: false },
  ]
}

// mockLabelResult — main_03 촬영 후 반환
export const MOCK_LABEL_RESULT = {
  productName: '홍삼정 EX',
  ingredients: '홍삼농축액 70%, 진세노사이드 6mg, 비타민C 50mg'
}

// mockAnalysisResult — main_04 분석 후 반환
export const MOCK_ANALYSIS_RESULT = {
  level: 'caution',
  doctorOpinion: {
    summary: '혈압약과 같이 드시면 혈압이 더 떨어질 수 있어요',
    detail: '홍삼은 혈관을 넓혀 혈압을 낮추는 작용을 합니다. 현재 복용 중인 암로디핀·로사르탄과 함께 드시면 효과가 겹쳐 어지러움이 생길 수 있어요. 특히 아침에 일어나실 때 천천히 일어나시는 게 좋아요.'
  },
  pharmacistOpinion: {
    summary: '드시려면 약 드신 후 2시간 이상 간격을 두세요',
    detail: '당뇨약(메트포르민)과는 큰 문제 없지만, 혈압약과의 시간 간격을 두는 것이 안전합니다. 하루 1회, 소량(1g 이하)으로 시작해 보세요.'
  },
  alternatives: ['도라지청', '대추차', '비타민C']
}
```

---

# 시나리오 목록

| # | 시나리오 | 진입 조건 | 관련 화면 |
|---|---------|---------|---------|
| S-01 | 앱 최초 실행 — 워크스루 완주 | 앱 첫 실행 | INTRO-01~03 |
| S-02 | 앱 최초 실행 — 워크스루 건너뛰기 | 앱 첫 실행 | INTRO-01, OB-02 |
| S-03 | 온보딩 — 기본정보 입력 | 워크스루 완료 | OB-01 |
| S-04 | 온보딩 — 기본정보 건너뛰기 | 워크스루 완료 | OB-01 |
| S-05 | 온보딩 — 지병 선택 | OB-02 진입 시 | OB-02 |
| S-06 | 온보딩 — 지병 선택 건너뛰기 | OB-02 진입 시 | OB-02 |
| S-07 | 온보딩 — 처방전 촬영 및 약물 확인 | OB-02 완료 | OB-03, OB-04 |
| S-08 | 온보딩 — 처방전 건너뛰기 | OB-02 완료 | OB-03 |
| S-09 | 온보딩 — 영양제 등록 | OB-04 완료 | OB-05 |
| S-10 | 온보딩 — 영양제 건너뛰기 | OB-04 완료 | OB-05 |
| S-11 | 홈 진입 — 약물 등록 있음 | 온보딩 완료 | MAIN-01 |
| S-12 | 홈 진입 — 약물 미등록 | 온보딩 완료 | MAIN-01 |
| S-13 | 질문 입력 — 텍스트로 분석 요청 | MAIN-01 | MAIN-02, 04, 05 |
| S-14 | 질문 입력 — 라벨 사진으로 분석 요청 | MAIN-01 | MAIN-02, 03, 04, 05 |
| S-15 | 질문 입력 — 예시 질문 칩 탭 | MAIN-01 | MAIN-02, 04, 05 |
| S-16 | 분석 결과 — 안전 결과 확인 | MAIN-04 완료 | MAIN-05 |
| S-17 | 분석 결과 — 주의 결과 확인 | MAIN-04 완료 | MAIN-05 |
| S-18 | 분석 결과 — 위험 결과 확인 | MAIN-04 완료 | MAIN-05 |
| S-19 | 분석 결과 — 가족 공유 | MAIN-05 | MAIN-05 |
| S-20 | 내 약물 관리 — 처방전 카드 조회 | MAIN-01 탭바 | SUB-01 |
| S-21 | 내 약물 관리 — 처방전 추가 | SUB-01 | SUB-02, OB-04 |
| S-22 | 내 약물 관리 — 처방전 교체 | SUB-01 | SUB-03, OB-04 |
| S-23 | 내 약물 관리 — 처방전 삭제 | SUB-01 | SUB-01 |
| S-24 | 내 약물 관리 — 영양제 추가 | SUB-01 | SUB-01 |
| S-25 | 문의 이력 — 이력 있음 | MAIN-01 탭바 | SUB-04 |
| S-26 | 문의 이력 — 이력 없음 | MAIN-01 탭바 | SUB-05 |
| S-27 | 문의 이력 — 필터 탭 | SUB-04 | SUB-04 |
| S-28 | 문의 이력 — 과거 결과 재조회 | SUB-04 | MAIN-05 |
| S-29 | 월간 복용 확인 팝업 — 그대로 | 30일 경과 후 앱 실행 | SUB-06 |
| S-30 | 월간 복용 확인 팝업 — 변경 있음 | 30일 경과 후 앱 실행 | SUB-06, SUB-01 |
| S-31 | 재방문 — 앱 재실행 (30일 미경과) | 온보딩 완료 후 재실행 | MAIN-01 |

---

# 상세 시나리오

---

## S-01 | 앱 최초 실행 — 워크스루 완주

**Given** 앱을 처음 실행했다 (`onboardingComplete === false`)

**When** 사용자가 워크스루를 처음부터 끝까지 읽는다

**Then**
1. INTRO-01 표시
2. "다음" 탭 → INTRO-02 표시 (인디케이터 2번째 활성)
3. "다음" 탭 → INTRO-03 표시 (인디케이터 3번째 활성)
4. "시작하기" 탭 → OB-01으로 이동

**부가 조건**
- 좌우 스와이프로도 화면 전환 가능
- 어느 화면에서든 "건너뛰기" 탭 → OB-01로 즉시 이동

---

## S-02 | 앱 최초 실행 — 워크스루 건너뛰기

**Given** 앱을 처음 실행했다

**When** INTRO-01에서 "건너뛰기" 탭

**Then** OB-01로 즉시 이동 (INTRO-02, 03 건너뜀)

---

## S-03 | 온보딩 — 기본정보 입력

**Given** OB-01 화면에 진입했다

**When**
1. 닉네임 입력 ("영자")
2. 생년월일 선택 (1961년 3월 12일)
3. 성별 "여성" 선택
4. "다음" 탭

**Then**
- `[API]` 로컬스토리지에 저장:
  ```json
  { "nickname": "영자", "birthYear": 1961, "birthMonth": 3, "birthDay": 12, "gender": "female" }
  ```
- OB-02로 이동
- OB-02 지병 목록: 5060대 공통 Top 10 표시
  (고혈압, 당뇨, 고지혈증, 골다공증, 갑상선질환, 관절염, 위장질환, 심장질환, 빈혈, 우울·불안)

**[VALIDATE]**
- 닉네임 10자 초과 → 입력 불가 (maxLength)
- 닉네임·생년월일·성별 중 하나라도 미입력 시 "다음" 버튼 비활성화
- 모두 입력 완료 시 "다음" 버튼 활성화

---

## S-04 | 온보딩 — 기본정보 건너뛰기

**Given** OB-01 화면에 진입했다

**When** "나중에 입력하기" 탭

**Then**
- `[API]` 저장 안 함 (null 유지)
- OB-02로 이동
- OB-02 지병 목록: 5060대 공통 Top 10 표시
  (고혈압, 당뇨, 고지혈증, 골다공증, 갑상선질환, 관절염, 위장질환, 심장질환, 빈혈, 우울·불안)

---

## S-05 | 온보딩 — 지병 선택

**Given** OB-02 화면에 진입했다

**When**
1. "고혈압" 탭 → 선택됨 (강조 표시)
2. "당뇨" 탭 → 선택됨
3. "다음" 탭

**Then**
- `[API]` 저장:
  ```json
  { "conditions": ["고혈압", "당뇨"], "customConditions": [], "hasAllergy": false, "allergies": [] }
  ```
- OB-03으로 이동

**부가 조건 — "여기 없어요" 탭 시**
1. 텍스트 입력 필드 1개 노출
2. 입력 후 "+ 추가" 탭 → 항목 추가, 새 입력 필드 노출
3. 각 항목 개별 삭제(X) 가능
4. `[API]` customConditions에 저장

**부가 조건 — 알레르기 토글 ON 시**
1. 직접 입력 필드 노출 (지병의 "여기 없어요"와 동일한 구조)
2. 여러 개 추가 가능 (+ 추가 버튼) / 각 항목 개별 삭제(X) 가능
3. 입력한 알레르기 `allergies`에 저장

---

## S-06 | 온보딩 — 지병 선택 건너뛰기

**Given** OB-02 화면에 진입했다

**When** "지금은 건너뛰기" 탭

**Then**
- `[API]` 저장: `{ "conditions": [], "customConditions": [], "hasAllergy": false, "allergies": [] }`
- OB-03으로 이동

---

## S-07 | 온보딩 — 처방전 촬영 및 약물 확인

**Given** OB-03 화면에 진입했다

**When**
1. "처방전 사진 찍기" 탭
2. 카메라 UI에서 촬영 (또는 갤러리 선택)
3. `[MOCK]` OCR 실행 → MOCK_OCR_RESULT 반환
4. OB-04로 이동

**OB-04에서**
5. 처방전 이름 자동 제안: "혈압 처방전" (가장 많은 약 용도 기반)
6. 지병 약 섹션: 당뇨약(메트포르민), 혈압약(암로디핀), 혈압약(로사르탄)
7. 보조 약물 섹션: 위장보호약(오메프라졸), 염증약(이부프로펜)
8. "이게 맞아요, 다음" 탭

**Then**
- `[API]` 저장:
  ```json
  prescriptions: [{
    "id": "uuid-1",
    "name": "혈압 처방전",
    "createdAt": "2026-05-15T...",
    "drugs": [
      { "id": "d1", "usageName": "당뇨약", "ingredientName": "메트포르민 500mg", "isCondition": true },
      { "id": "d2", "usageName": "혈압약", "ingredientName": "암로디핀 5mg", "isCondition": true },
      { "id": "d3", "usageName": "혈압약", "ingredientName": "로사르탄 50mg", "isCondition": true },
      { "id": "d4", "usageName": "위장보호약", "ingredientName": "오메프라졸 20mg", "isCondition": false },
      { "id": "d5", "usageName": "염증약·진통제", "ingredientName": "이부프로펜 200mg", "isCondition": false }
    ]
  }]
  ```
- OB-05로 이동
- 토스트: "총 5개 약이 등록되었어요"

**부가 조건 — 처방전 여러 장**
- OB-03에서 촬영 완료 후 썸네일 표시 + "+ 처방전 추가" 버튼
- 추가 촬영 시 `[MOCK]` OCR 재실행 → 결과 누적
- "다 찍었어요" 탭 → OB-04로 이동 (누적 결과 표시)

**부가 조건 — OCR 실패**
- `[MOCK]` 빈 결과 반환 → "인식이 어렵네요. 다시 찍거나 직접 입력해주세요" 안내

---

## S-08 | 온보딩 — 처방전 건너뛰기

**Given** OB-03 화면에 진입했다

**When** "나중에 등록하기" 탭

**Then**
- 처방전 저장 안 함 (`prescriptions: []`)
- OB-05로 이동

---

## S-09 | 온보딩 — 영양제 등록

**Given** OB-05 화면에 진입했다

**When**
1. "영양제 라벨 사진 찍기" 탭
2. 촬영
3. `[MOCK]` VLM 실행 → MOCK_LABEL_RESULT 반환
4. 리스트에 "홍삼정 EX / 홍삼농축액 70%, 진세노사이드 6mg" 카드 추가
5. "+ 영양제 추가하기" 탭 → 반복 가능
6. "등록 완료, 시작하기" 탭

**Then**
- `[API]` 저장:
  ```json
  supplements: [{ "id": "s1", "productName": "홍삼정 EX", "ingredients": "홍삼농축액 70%, 진세노사이드 6mg", "createdAt": "..." }]
  ```
- `[API]` `onboardingComplete: true` 저장
- MAIN-01(홈)으로 이동

---

## S-10 | 온보딩 — 영양제 건너뛰기

**Given** OB-05 화면에 진입했다

**When** "지금 먹는 영양제가 없어요" 탭

**Then**
- `supplements: []` 저장
- `onboardingComplete: true` 저장
- MAIN-01(홈)으로 이동

---

## S-11 | 홈 진입 — 약물 등록 있음

**Given** 온보딩 완료 / 처방전 1개 등록됨 / 문의 이력 3건 있음

**When** 앱을 실행하거나 탭바 "홈" 탭

**Then**
- `[API]` 읽기: user, prescriptions, history
- 상단 인사: "영자님, 오늘도 건강하세요 👋"
- 약물 요약 카드: "현재 복용 중인 약 / 당뇨약, 혈압약 등 3개"
- 최근 문의 카드 최대 3개 표시 (최신순)
- 30일 경과 여부 확인 → 경과 시 SUB-06 팝업 노출

---

## S-12 | 홈 진입 — 약물 미등록

**Given** 온보딩 완료 / 처방전 미등록 / 문의 이력 없음

**When** 앱을 실행한다

**Then**
- 약물 요약 카드: "등록된 약이 없어요 / 처방전을 등록하면 더 정확해요" + 등록 버튼
- 최근 문의: 빈 상태 (SUB-05 스타일)

---

## S-13 | 질문 입력 — 텍스트로 분석 요청

**Given** MAIN-02 화면에 진입했다

**When**
1. 텍스트 입력: "홍삼 먹어도 되나요?"
2. "분석해줘" 탭

**Then**
1. MAIN-04(분석 중) 화면으로 이동
2. 단계 메시지 순차 표시 (1초 간격)
3. 타이머 카운트업 표시
4. `[MOCK]` 3초 딜레이 후 MOCK_ANALYSIS_RESULT 반환
5. MAIN-05(분석 결과)로 이동
6. `[API]` history에 결과 저장:
   ```json
   { "id": "h1", "createdAt": "...", "question": "홍삼 먹어도 되나요?", "imageUsed": false, "level": "caution", "doctorOpinion": {...}, "pharmacistOpinion": {...}, "alternatives": [...] }
   ```

**[VALIDATE]**
- 입력 없이 "분석해줘" 탭 → "무엇이 궁금하신가요?" 토스트, 이동 안 함

---

## S-14 | 질문 입력 — 라벨 사진으로 분석 요청

**Given** MAIN-02 화면에 진입했다

**When**
1. "영양제·라벨 사진" 탭 → MAIN-03으로 이동
2. 촬영
3. `[MOCK]` VLM 실행 → MOCK_LABEL_RESULT 반환
4. 하단 시트 슬라이드 업: "홍삼정 EX / 홍삼농축액 70%..."
5. "이 성분으로 분석하기" 탭

**Then**
1. MAIN-04로 이동
2. `[MOCK]` 분석 실행 → MOCK_ANALYSIS_RESULT 반환
3. MAIN-05로 이동
4. `[API]` history 저장 (`imageUsed: true`)

---

## S-15 | 질문 입력 — 예시 질문 칩 탭

**Given** MAIN-02 화면에 진입했다

**When** "홍삼 먹어도 되나요?" 칩 탭

**Then**
- 텍스트 입력 필드에 "홍삼 먹어도 되나요?" 자동 입력
- 사용자가 바로 "분석해줘" 탭 가능

---

## S-16 | 분석 결과 — 안전 결과 확인

**Given** MAIN-05에 `level: 'safe'` 결과로 진입

**Then**
- 위험도 배너: 초록 배경 / "드셔도 괜찮아요 ✓"
- 의사 소견 카드 + 약사 소견 카드 표시 (기본 접힘)
- 대안 제시 섹션 미표시

---

## S-17 | 분석 결과 — 주의 결과 확인

**Given** MAIN-05에 `level: 'caution'` 결과로 진입 (MOCK_ANALYSIS_RESULT 기본값)

**Then**
- 위험도 배너: 노란 배경 / "조심해서 드셔야 해요 ⚠"
- 의사 소견 카드 + 약사 소견 카드 표시 (기본 접힘)
- 대안 제시 섹션 표시
- "전문가에게 직접 상담하기" 버튼 표시

---

## S-18 | 분석 결과 — 위험 결과 확인

**Given** MAIN-05에 `level: 'danger'` 결과로 진입

**Then**
- 위험도 배너: 빨간 배경 / "드시면 안 돼요 ✕"
- 진동 피드백 (Haptic)
- 대안 제시 섹션 표시
- "전문가에게 직접 상담하기" 버튼 표시

---

## S-19 | 분석 결과 — 가족 공유

**Given** MAIN-05 화면에 있다

**When** "가족에게 공유" 아이콘 탭

**Then**
- 네이티브 공유 시트 호출 (Web Share API)
- 공유 텍스트: "이거뭐약 분석 결과\n[질문]: 홍삼 먹어도 되나요?\n[결과]: 조심해서 드셔야 해요\n[의사 소견]: ..."

---

## S-20 | 내 약물 관리 — 처방전 카드 조회

**Given** 처방전 2개 등록됨 (당뇨 처방전, 혈압 처방전)

**When** 탭바 "내 약물" 탭

**Then**
- `[API]` prescriptions, supplements 읽기
- 상단 현황: "처방전 2개 · 약 5개 · 영양제 2개"
- 처방전 카드 2개 표시 (접힌 상태)
- "탭하면 약 목록이 펼쳐져요" 안내 문구

**When** "당뇨 처방전" 카드 탭

**Then** 해당 처방전의 약 목록 펼쳐짐

---

## S-21 | 내 약물 관리 — 처방전 추가

**Given** SUB-01 화면에 있다

**When** "+ 처방전 추가" 탭 → SUB-02로 이동

**Then**
1. 상단 배너: "기존 약에 새 약이 추가돼요"
2. 촬영 → `[MOCK]` OCR → OB-04로 이동 (추가 모드)
3. OB-04에서 확인 후 저장
4. `[API]` prescriptions 배열에 새 처방전 추가
5. SUB-01로 복귀 / 현황 수치 업데이트

---

## S-22 | 내 약물 관리 — 처방전 교체

**Given** SUB-01 화면에 있다 / "혈압 처방전" 카드의 "교체" 탭

**When**
1. 경고 다이얼로그: "혈압 처방전의 3개 약이 삭제되고 새 처방전으로 교체됩니다. 계속할까요?"
2. "확인" 탭 → SUB-03으로 이동
3. 교체 대상: "혈압 처방전을 교체합니다" 배너 + 기존 약 목록 표시
4. 촬영 → `[MOCK]` OCR → OB-04로 이동 (교체 모드)
5. 확인 후 저장

**Then**
- `[API]` 해당 처방전 ID의 drugs 교체 (name은 유지 or 재제안)
- SUB-01로 복귀 / 현황 수치 업데이트

**부가 조건 — 취소**
- 경고 다이얼로그에서 "취소" → SUB-01 복귀, 변경 없음

---

## S-23 | 내 약물 관리 — 처방전 삭제

**Given** SUB-01 화면에 있다 / 처방전 2개 이상 등록됨

**When** "당뇨 처방전" 카드의 "삭제" 탭

**Then**
1. 확인 다이얼로그: "당뇨 처방전에 포함된 2개 약이 모두 삭제됩니다"
2. "삭제" 탭 → `[API]` 해당 처방전 제거
3. 현황 수치 업데이트

**부가 조건 — 처방전 1개뿐일 때**
- 삭제 버튼 비활성화 (최소 1개 유지)

---

## S-24 | 내 약물 관리 — 영양제 추가

**Given** SUB-01 화면에 있다

**When** 영양제 섹션의 "+ 영양제 추가" 탭

**Then**
1. 라벨 촬영 UI 노출 (MAIN-03과 동일)
2. `[MOCK]` VLM 실행 → 성분 추출
3. 영양제 카드 추가
4. `[API]` supplements 배열에 추가

---

## S-25 | 문의 이력 — 이력 있음

**Given** history에 6건 저장됨

**When** 탭바 "이력" 탭

**Then**
- `[API]` history 읽기 (최신순 정렬)
- 이력 카드 6개 표시: 날짜 + 질문 요약 + 위험도 색상 칩
- 필터 탭: 전체(6) / 주의 / 위험 / 안전

**When** "위험" 필터 탭

**Then** level: 'danger'인 카드만 표시

---

## S-26 | 문의 이력 — 이력 없음

**Given** history가 비어있음

**When** 탭바 "이력" 탭

**Then** SUB-05 표시
- "아직 문의 이력이 없어요"
- "첫 번째 질문을 해보세요!"
- "물어보러 가기" 탭 → MAIN-02로 이동

---

## S-27 | 문의 이력 — 과거 결과 재조회

**Given** SUB-04 화면에 있다

**When** 특정 이력 카드 탭

**Then**
- MAIN-05로 이동
- `[API]` 해당 history 항목 읽어 결과 렌더링
- 상단에 "이 결과는 5월 12일 기준이에요" 날짜 배너 표시

---

## S-28 | 월간 복용 확인 팝업 — 그대로

**Given**
- `lastPrescriptionCheck`가 30일 이상 경과
- 또는 최초 등록 후 30일 경과

**When** 앱 실행

**Then**
1. MAIN-01 위에 SUB-06 팝업 오버레이 (딤 배경)
2. 처방전별 "그대로예요 / 바뀌었어요" 버튼 표시
3. "확인 후 답해주세요" 안내
4. 모든 처방전 "그대로예요" 선택 후 "나중에 확인할게요" 탭

**Then**
- `[API]` `lastPrescriptionCheck` 오늘 날짜로 업데이트
- 토스트: "건강하게 잘 챙겨드시고 있네요! 👍"
- 팝업 닫힘

---

## S-29 | 월간 복용 확인 팝업 — 변경 있음

**Given** SUB-06 팝업이 열려 있다

**When**
1. "혈압 처방전" → "바뀌었어요" 탭 → 해당 카드 취소선 + 경고 표시
2. "나중에 확인할게요" 탭

**Then**
- 팝업 닫힘 (3일 후 재노출 예약)
- `[API]` `lastPrescriptionCheck` 업데이트 안 함

**When** (대신) 팝업에서 "변경된 약이 있어요" 탭

**Then** SUB-01로 이동 → 처방전 교체 플로우 진행

---

## S-30 | 재방문 — 앱 재실행 (30일 미경과)

**Given** `onboardingComplete: true` / 30일 미경과

**When** 앱을 다시 실행

**Then**
- INTRO 화면 표시 안 함 (워크스루 스킵)
- MAIN-01(홈) 바로 표시
- `[API]` 저장된 데이터 불러와 렌더링

---

# 화면 전환 맵

```
앱 실행
  └─ onboardingComplete === false → INTRO-01
  └─ onboardingComplete === true
       └─ 30일 경과 → MAIN-01 + SUB-06 팝업
       └─ 30일 미경과 → MAIN-01

INTRO-01 → (다음) → INTRO-02 → (다음) → INTRO-03 → (시작하기) → OB-01
INTRO-01/02/03 → (건너뛰기) → OB-01

OB-01 → (다음/건너뛰기) → OB-02
OB-02 → (다음/건너뛰기) → OB-03
OB-03 → (촬영완료) → OB-04
OB-03 → (건너뛰기) → OB-05
OB-04 → (확인) → OB-05
OB-05 → (완료/건너뛰기) → MAIN-01

MAIN-01 ←→ MAIN-02 → MAIN-03 → MAIN-04 → MAIN-05
MAIN-01 ←→ SUB-01
           SUB-01 → SUB-02 → OB-04
           SUB-01 → SUB-03 → OB-04
MAIN-01 ←→ SUB-04 (이력 없으면 SUB-05)
           SUB-04 → MAIN-05 (재조회)
```
