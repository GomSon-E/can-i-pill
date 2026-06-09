"""
Dockerfile 및 nginx.conf 파일 내용 검증 테스트.
"""
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))


class TestDockerignore:
    def _content(self, path):
        return open(os.path.join(ROOT, path)).read()

    def test_frontend_dockerignore_exists(self):
        assert os.path.exists(os.path.join(ROOT, "frontend", ".dockerignore"))

    def test_frontend_ignores_node_modules(self):
        assert "node_modules" in self._content("frontend/.dockerignore")

    def test_backend_dockerignore_exists(self):
        assert os.path.exists(os.path.join(ROOT, "backend", ".dockerignore"))

    def test_backend_ignores_pycache(self):
        content = self._content("backend/.dockerignore")
        assert "__pycache__" in content or "*.pyc" in content

    def test_ai_server_dockerignore_exists(self):
        assert os.path.exists(os.path.join(ROOT, "ai_server", ".dockerignore"))

    def test_ai_server_ignores_pycache(self):
        content = self._content("ai_server/.dockerignore")
        assert "__pycache__" in content or "*.pyc" in content


class TestDockerCompose:
    COMPOSE = os.path.join(ROOT, "docker-compose.yml")

    def test_file_exists(self):
        assert os.path.exists(self.COMPOSE), "docker-compose.yml이 없습니다"

    def test_has_backend_service(self):
        content = open(self.COMPOSE).read()
        assert "backend" in content

    def test_has_ai_server_service(self):
        content = open(self.COMPOSE).read()
        assert "ai_server" in content or "ai-server" in content

    def test_has_frontend_service(self):
        content = open(self.COMPOSE).read()
        assert "frontend" in content

    def test_backend_uses_port_8000(self):
        content = open(self.COMPOSE).read()
        assert "8000" in content

    def test_ai_server_uses_port_8001(self):
        content = open(self.COMPOSE).read()
        assert "8001" in content

    def test_has_env_file(self):
        content = open(self.COMPOSE).read()
        assert "env_file" in content or ".env" in content


class TestBackendDockerfile:
    DOCKERFILE = os.path.join(ROOT, "backend", "Dockerfile")

    def test_file_exists(self):
        assert os.path.exists(self.DOCKERFILE), "backend/Dockerfile이 없습니다"

    def test_has_python_base(self):
        content = open(self.DOCKERFILE).read()
        assert "FROM python" in content

    def test_has_uvicorn_command(self):
        content = open(self.DOCKERFILE).read()
        assert "uvicorn" in content and "app.main:app" in content

    def test_runs_on_port_8000(self):
        content = open(self.DOCKERFILE).read()
        assert "8000" in content

    def test_has_workers(self):
        content = open(self.DOCKERFILE).read()
        assert "--workers" in content


class TestAiServerDockerfile:
    DOCKERFILE = os.path.join(ROOT, "ai_server", "Dockerfile")

    def test_file_exists(self):
        assert os.path.exists(self.DOCKERFILE), "ai_server/Dockerfile이 없습니다"

    def test_has_python_base(self):
        content = open(self.DOCKERFILE).read()
        assert "FROM python" in content

    def test_has_uvicorn_command(self):
        content = open(self.DOCKERFILE).read()
        assert "uvicorn" in content and "app.main:app" in content

    def test_runs_on_port_8001(self):
        content = open(self.DOCKERFILE).read()
        assert "8001" in content


class TestFrontendNginxConf:
    CONF = os.path.join(ROOT, "frontend", "nginx.conf")

    def test_file_exists(self):
        assert os.path.exists(self.CONF), "frontend/nginx.conf가 없습니다"

    def test_has_spa_try_files(self):
        content = open(self.CONF).read()
        assert "try_files" in content and "/index.html" in content

    def test_has_gzip(self):
        content = open(self.CONF).read()
        assert "gzip" in content


class TestFrontendDockerfile:
    DOCKERFILE = os.path.join(ROOT, "frontend", "Dockerfile")

    def test_file_exists(self):
        assert os.path.exists(self.DOCKERFILE), "frontend/Dockerfile이 없습니다"

    def test_has_node_build_stage(self):
        content = open(self.DOCKERFILE).read()
        assert "FROM node" in content, "Node.js 빌드 스테이지가 없습니다"

    def test_has_npm_run_build(self):
        content = open(self.DOCKERFILE).read()
        assert "npm run build" in content, "npm run build 명령이 없습니다"

    def test_has_nginx_serve_stage(self):
        content = open(self.DOCKERFILE).read()
        assert "FROM nginx" in content, "nginx 서빙 스테이지가 없습니다"

    def test_has_copy_from_builder(self):
        content = open(self.DOCKERFILE).read()
        assert "--from=" in content, "multi-stage COPY --from 명령이 없습니다"

    def test_exposes_port_80(self):
        content = open(self.DOCKERFILE).read()
        assert "EXPOSE 80" in content, "EXPOSE 80 선언이 없습니다"
