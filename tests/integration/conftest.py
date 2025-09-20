import subprocess
import time

import pytest
import requests

from testcontainers.core.network import Network
from testcontainers.postgres import PostgresContainer
from testcontainers.core.container import DockerContainer


@pytest.fixture(scope="session")
def containers_network():
    with Network() as nw:
        yield nw


@pytest.fixture(scope="session")
def postgres_container(containers_network: Network):
    with (
        PostgresContainer("postgres:16-alpine")
        .with_network(containers_network)
        .with_network_aliases("db")
    ) as container:
        yield container


@pytest.fixture(scope="session")
def maildev_container(containers_network: Network):
    with (
        DockerContainer("maildev/maildev")
        .with_network(containers_network)
        .with_network_aliases("smtp")
        .with_exposed_ports(1025, 1080)
    ) as container:
        yield container


@pytest.fixture(scope="session")
def application_image():
    image_tag = "contacts-api:test"
    subprocess.check_call(["docker", "build", "-t", image_tag, "."])
    return image_tag


@pytest.fixture(scope="session")
def application_container(
    application_image: str,
    containers_network: Network,
    postgres_container: PostgresContainer,
    maildev_container: DockerContainer,
):
    database_exposed_port = postgres_container.get_exposed_port(5432)
    database_url = postgres_container.get_connection_url(host="db", driver="asyncpg")
    database_url = database_url.replace(str(database_exposed_port), str(5432))

    with (
        DockerContainer(application_image)
        .with_network(containers_network)
        .with_exposed_ports("8000/tcp")
        .with_env("DATABASE_URL", database_url)
        .with_env("SECRET_KEY", "integration-tests-secret")
        .with_env("JWT_ALGORITHM", "HS256")
        .with_env("MAIL_SERVER", "smtp")
        .with_env("MAIL_PORT", str(1025))
        .with_env("MAIL_FROM", "no-reply@example.com")
        .with_env("MAIL_USE_CREDENTIALS", "false")
        .with_env("PUBLIC_BASE_URL", "http://localhost")
        .with_command(
            'sh -c "poetry run alembic upgrade head && exec poetry run fastapi run --host 0.0.0.0 --port 8000"'
        )
    ) as container:
        yield container


@pytest.fixture(scope="session")
def test_client(
    application_container,
):
    host = application_container.get_container_host_ip()
    port = int(application_container.get_exposed_port(8000))
    base_url = f"http://{host}:{port}"

    deadline = time.time() + 60
    ready = False
    while time.time() < deadline:
        try:
            r = requests.get(f"{base_url}/health", timeout=2)
            if r.status_code < 500:
                ready = True
                break
        except Exception:
            pass
        time.sleep(0.5)
    if not ready:
        stdout, stderr = b"", b""
        try:
            stdout, stderr = application_container.get_logs()
        except Exception:
            pass
        print(stdout.decode("utf-8", errors="ignore"))
        print(stderr.decode("utf-8", errors="ignore"))
        raise RuntimeError("API container did not become ready in time")

    class Client:
        def __init__(self, base: str):
            self.base = base
            self.session = requests.Session()

        def _url(self, path: str) -> str:
            if path.startswith("http://") or path.startswith("https://"):
                return path
            if not path.startswith("/"):
                path = "/" + path
            return self.base + path

        def get(self, path: str, **kwargs):
            return self.session.get(self._url(path), **kwargs)

        def post(self, path: str, **kwargs):
            return self.session.post(self._url(path), **kwargs)

        def put(self, path: str, **kwargs):
            return self.session.put(self._url(path), **kwargs)

        def delete(self, path: str, **kwargs):
            return self.session.delete(self._url(path), **kwargs)

    yield Client(base_url)
