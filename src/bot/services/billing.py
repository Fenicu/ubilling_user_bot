"""Обёртка над UbillingClient."""

from pyubilling import UbillingClient


class BillingService:
    """Singleton-сервис для работы с Ubilling API."""

    def __init__(self, url: str, uber_key: str | None = None) -> None:
        """
        Инициализация сервиса.

        Args:
            url: URL Ubilling XMLAgent API
            uber_key: MD5 серийного номера для extended auth (опционально)
        """
        self._url = url
        self._uber_key = uber_key
        self._client: UbillingClient | None = None

    async def start(self) -> None:
        """Инициализирует httpx-клиент."""
        self._client = UbillingClient(self._url, uber_key=self._uber_key)
        await self._client.__aenter__()

    async def stop(self) -> None:
        """Закрывает httpx-клиент."""
        if self._client:
            await self._client.close()
            self._client = None

    @property
    def client(self) -> UbillingClient:
        """
        Возвращает активный клиент Ubilling.

        Raises:
            RuntimeError: если клиент не инициализирован
        """
        if self._client is None:
            raise RuntimeError("BillingService не запущен. Вызовите start() сначала.")
        return self._client
