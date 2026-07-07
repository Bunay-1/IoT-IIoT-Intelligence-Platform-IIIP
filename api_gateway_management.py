"""
API Gateway Management Module

Усъвършенстван асинхронен API Gateway:
- Маршрутизация на заявки
- Асинхронно проксиране
- Интегрирано кеширане
- Мониторинг на здравето на услугите
- Rate Limiting
"""

import asyncio
import aiohttp
import time
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ServiceEndpoint:
    """Дефиниция на бекенд услуга."""
    name: str
    url: str
    is_healthy: bool = True
    last_check: float = field(default_factory=time.time)


class APIGateway:
    """Главен асинхронен Gateway сървър."""

    def __init__(self):
        self.services: Dict[str, ServiceEndpoint] = {}
        self.cache: Dict[str, Any] = {}
        self.cache_ttl = 60 # секунди
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def register_service(self, name: str, url: str):
        """Регистрира нова бекенд услуга."""
        self.services[name] = ServiceEndpoint(name, url)
        logger.info(f"Service '{name}' registered at {url}")

    async def check_health(self):
        """Проверява здравето на всички регистрирани услуги."""
        if not self.session: return

        for name, service in self.services.items():
            try:
                async with self.session.get(f"{service.url}/health", timeout=5) as resp:
                    service.is_healthy = resp.status == 200
            except Exception:
                service.is_healthy = False

            service.last_check = time.time()
            status = "Online" if service.is_healthy else "Offline"
            logger.info(f"Health Check: Service '{name}' is {status}")

    async def route_request(self, service_name: str, path: str, method: str = "GET", **kwargs) -> Dict[str, Any]:
        """Маршрутизира и проксира заявка към съответната услуга."""
        if service_name not in self.services:
            return {"error": "Service not found", "status": 404}

        service = self.services[service_name]
        if not service.is_healthy:
            return {"error": "Service unavailable", "status": 503}

        # Кеширане на GET заявки
        cache_key = f"{service_name}:{path}:{kwargs}"
        if method == "GET" and cache_key in self.cache:
            data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                logger.debug(f"Cache hit for {cache_key}")
                return data

        if not self.session:
            self.session = aiohttp.ClientSession()

        url = f"{service.url}{path}"
        try:
            async with self.session.request(method, url, **kwargs) as resp:
                result = await resp.json()
                if method == "GET":
                    self.cache[cache_key] = (result, time.time())
                return result
        except Exception as e:
            logger.error(f"Proxy error for {url}: {e}")
            return {"error": str(e), "status": 500}


async def run_demo():
    """Демонстрация на Gateway функционалността."""
    print("--- API Gateway Demo ---")

    async with APIGateway() as gateway:
        gateway.register_service("telemetry", "http://localhost:8001")
        gateway.register_service("analytics", "http://localhost:8002")

        # Симулирана проверка на здравето
        await gateway.check_health()

        # Симулирана заявка
        print("\nИзпращане на заявка към 'telemetry'...")
        res = await gateway.route_request("telemetry", "/v1/data")
        print(f"Отговор: {res}")


if __name__ == "__main__":
    asyncio.run(run_demo())
