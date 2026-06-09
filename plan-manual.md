# 사람이 직접 해야하는 것

> AI가 코드를 작성해도 클라우드 콘솔 설정, SSH 키 발급, 환경변수 등록은 사람이 직접 해야 한다.
> 서버 아키텍처 설계 문서 기준: 프론트엔드(AWS Lightsail $5) + 백엔드 GCP($13) + AI 서버 GCP($13), 총 $31/월.

---

## 1. GCP 설정 — 백엔드 서버 (CRUD 전용)

- [ ] [GCP Console](https://console.cloud.google.com) → Compute Engine → VM 인스턴스 → 만들기
  - 머신 유형: e2-small (1 vCPU, 2GB)
  - 리전: asia-northeast3 (서울) 권장
  - 부팅 디스크: Ubuntu 22.04 LTS
  - 방화벽: HTTP/HTTPS 허용 체크
- [ ] VPC 네트워크 → 방화벽 규칙 → 규칙 만들기
  - 이름: `allow-backend-8000`
  - 트래픽 방향: 수신
  - 소스 IP: `0.0.0.0/0` (또는 Lightsail IP만 허용해 보안 강화)
  - 프로토콜/포트: TCP 8000
- [ ] VM에 SSH 접속 후 Docker 설치
  ```bash
  sudo apt-get update
  sudo apt-get install -y docker.io
  sudo systemctl enable docker
  sudo usermod -aG docker $USER
  ```
- [ ] GitHub Actions 배포용 SSH 키 생성 및 `~/.ssh/authorized_keys`에 공개키 등록
  ```bash
  ssh-keygen -t ed25519 -C "github-actions-backend"
  cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys
  ```
  - 비공개키(id_ed25519) 내용을 GitHub Secrets에 등록 (아래 5번 참고)
- [ ] 외부 IP 주소 고정 (VPC 네트워크 → 외부 IP 주소 → 고정 주소로 변경)
- [ ] 백엔드 서버 외부 IP 메모해두기: `______________`

---

## 2. GCP 설정 — AI 서버 (OCR·분석 전용)

- [ ] [GCP Console](https://console.cloud.google.com) → Compute Engine → VM 인스턴스 → 만들기
  - 머신 유형: e2-small (1 vCPU, 2GB)
  - 리전: 백엔드 서버와 동일 리전 (내부 통신 레이턴시 최소화)
  - 부팅 디스크: Ubuntu 22.04 LTS
- [ ] VPC 네트워크 → 방화벽 규칙 → 규칙 만들기
  - 이름: `allow-ai-server-8001`
  - 소스 IP: 백엔드 서버 내부 IP만 허용 (보안상 public 오픈 금지)
  - 프로토콜/포트: TCP 8001
- [ ] VM에 SSH 접속 후 Docker 설치 (백엔드 서버와 동일)
- [ ] GitHub Actions 배포용 SSH 키 생성 및 등록
- [ ] 외부 IP 고정 (GitHub Actions 배포 접근용)
- [ ] AI 서버 외부 IP 메모: `______________`, 내부 IP 메모: `______________`
  - 백엔드 서버의 `.env`에 `AI_SERVER_URL=http://<내부 IP>:8001` 설정할 값

---

## 3. AWS Lightsail 설정 — 프론트엔드

- [ ] [AWS Lightsail Console](https://lightsail.aws.amazon.com) → 인스턴스 생성
  - 플랫폼: Linux/Unix
  - 블루프린트: OS Only → Ubuntu 22.04
  - 플랜: $5/월 (1 Core, 2GB, 1TB 전송)
- [ ] 인스턴스 → 네트워킹 → 방화벽 규칙 추가
  - HTTP: TCP 80
  - HTTPS: TCP 443
- [ ] 정적 IP 생성 후 인스턴스에 연결
- [ ] SSH 접속 후 nginx 설치
  ```bash
  sudo apt-get update
  sudo apt-get install -y nginx
  sudo systemctl enable nginx
  ```
- [ ] GitHub Actions 배포용 SSH 키 생성 및 `~/.ssh/authorized_keys` 등록
- [ ] Lightsail 외부 IP 메모: `______________`

---

## 4. 도메인 및 SSL (선택)

- [ ] 도메인 구매 (가비아, Route 53 등)
- [ ] DNS A 레코드: 도메인 → Lightsail 외부 IP 연결
- [ ] Lightsail SSH 접속 후 Let's Encrypt SSL 발급
  ```bash
  sudo apt-get install -y certbot python3-certbot-nginx
  sudo certbot --nginx -d yourdomain.com
  sudo certbot renew --dry-run  # 자동 갱신 확인
  ```

---

## 5. GitHub Actions Secrets 등록

> [GitHub 저장소] → Settings → Secrets and variables → Actions → New repository secret

| Secret 이름 | 값 | 설명 |
|---|---|---|
| `GCP_BACKEND_HOST` | 백엔드 서버 외부 IP | SSH 접속 대상 |
| `GCP_BACKEND_SSH_KEY` | 백엔드 서버 SSH 비공개키 전체 내용 | PEM 형식 |
| `GCP_BACKEND_USER` | `ubuntu` (또는 VM 사용자명) | SSH 사용자 |
| `GCP_AI_HOST` | AI 서버 외부 IP | SSH 접속 대상 |
| `GCP_AI_SSH_KEY` | AI 서버 SSH 비공개키 전체 내용 | PEM 형식 |
| `GCP_AI_USER` | `ubuntu` | SSH 사용자 |
| `LIGHTSAIL_HOST` | Lightsail 외부 IP | rsync 대상 |
| `LIGHTSAIL_SSH_KEY` | Lightsail SSH 비공개키 전체 내용 | PEM 형식 |
| `LIGHTSAIL_USER` | `ubuntu` | SSH 사용자 |
| `SUPABASE_URL` | Supabase 프로젝트 URL | |
| `SUPABASE_ANON_KEY` | Supabase anon key | |
| `SUPABASE_SERVICE_KEY` | Supabase service key | |
| `GEMINI_API_KEY` | Google AI Studio API key | |
| `DATA_GO_KR_API_KEY` | 공공데이터포털 API key | |
| `AI_SERVER_INTERNAL_URL` | `http://<AI 서버 내부 IP>:8001` | 백엔드 → AI 서버 통신 |

---

## 6. 각 서버 초기 실행 (SSH 접속 후 최초 1회)

**백엔드 서버**
```bash
git clone https://github.com/<your-org>/can-i-pill.git
cd can-i-pill/backend
cp .env.example .env
nano .env  # 실제 값 입력
docker build -t can-i-pill-backend .
docker run -d --name backend -p 8000:8000 --env-file .env can-i-pill-backend
```

**AI 서버**
```bash
git clone https://github.com/<your-org>/can-i-pill.git
cd can-i-pill/ai_server
cp .env.example .env
nano .env  # GEMINI_API_KEY 등 입력
docker build -t can-i-pill-ai .
docker run -d --name ai-server -p 8001:8001 --env-file .env can-i-pill-ai
```

**프론트엔드 서버 (nginx 설정)**
```bash
# AI가 생성한 nginx.conf를 /etc/nginx/sites-available/default에 복사
sudo cp nginx.conf /etc/nginx/sites-available/default
sudo nginx -t
sudo systemctl reload nginx
```

---

## 7. 멘토 피드백 대응 체크리스트

- [ ] AI 서버 분리 구현 후 멘토에게 서버 아키텍처 설계 문서와 함께 공유
  - 분리 이유: Gemini API 장애 독립 감지 + AI 분석 성능 독립 관측
  - 현재 선택: 별도 GCP 인스턴스 (Option B), 실측 후 재검토 가능
- [ ] Harness Engineering 구현 후 멘토에게 `analyze-agentic-redesign-proposal.md` 공유
  - validate_query → gather_context → analyze → finish 루프 시연
  - self-evaluate 재시도 시나리오 시연
