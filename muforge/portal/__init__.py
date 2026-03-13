import asyncio
import uuid

from muforge.application import BaseApplication
from muforge.portal.connections import BaseConnection
from muforge.portal.connections.link import ConnectionLink


class Application(BaseApplication):
    name = "portal"

    def __init__(self, settings):
        super().__init__(settings)
        self.parsers: dict[str, type] = dict()
        self.connections: dict[uuid.UUID, BaseConnection] = dict()
        self.pending_links = asyncio.Queue()

    async def setup_parsers(self):
        for p in self.plugin_load_order:
            self.parsers.update(p.portal_parsers())

    async def setup(self):
        await super().setup()
        await self.setup_parsers()

    async def handle_connection(self, link: ConnectionLink):
        conn_class = self.classes.get("connection", BaseConnection)
        conn = conn_class(self, link)
        self.connections[link.info.connection_id] = conn
        await conn.run()
        del self.connections[link.info.connection_id]

    async def start(self):
        while link := await self.pending_links.get():
            self.task_group.create_task(self.handle_connection(link))
