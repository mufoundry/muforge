import asyncio
from pathlib import Path

from hypercorn import Config
from hypercorn.asyncio import serve
from loguru import logger

from muforge.application import BaseApplication

from .fastapi import assemble_fastapi


class Application(BaseApplication):
    name = "game"

    def __init__(self, settings):
        super().__init__(settings)
        self.fastapi_config = None
        self.fastapi_instance = None

    async def setup_fastapi(self):
        settings = self.settings["webserver"]
        self.fastapi_config = Config()
        self.fastapi_config.title = self.complete_settings["MUFORGE"]["name"]

        self.fastapi_config.websocket_ping_interval = 30
        self.fastapi_config.websocket_ping_timeout = 10

        external = settings["bind_address"]
        bind_to = f"{external}:{settings['port']}"
        self.fastapi_config.bind = [bind_to]
        self.fastapi_config._quic_bind = [bind_to]

        if settings.get("tls", False):
            tls = self.complete_settings["TLS"]
            if Path(tls["certificate"]).exists():
                self.fastapi_config.certfile = str(Path(tls["certificate"]).absolute())
            if Path(tls["key"]).exists():
                self.fastapi_config.keyfile = str(Path(tls["key"]).absolute())

        self.fastapi_instance = await assemble_fastapi(self, self.fastapi_config)

    async def setup(self):
        await super().setup()
        await self.setup_fastapi()
        await self.setup_plugins_final()

    

    async def start(self):
        await serve(
            self.fastapi_instance,
            self.fastapi_config,
            shutdown_trigger=self.shutdown_event.wait,
        )
