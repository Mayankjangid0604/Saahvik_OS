import json
import asyncio
from typing import Any
from fastapi import WebSocket
from enterprise_os.runtime.events import EventDispatcher, Event
import dataclasses

class EventStreamer:
    def __init__(self, dispatcher: EventDispatcher):
        self.dispatcher = dispatcher
        self.active_connections: list[WebSocket] = []
        self._queue: asyncio.Queue = asyncio.Queue()
        self._loop: asyncio.AbstractEventLoop | None = None

        # Subscribe to all events
        self.dispatcher.subscribe(Event, self._handle_event)

    def _handle_event(self, event: Event) -> None:
        try:
            event_data = {
                "type": type(event).__name__,
                "data": dataclasses.asdict(event)
            }
            message = json.dumps(event_data)
            # dispatch() can be called from a non-event-loop thread (e.g. FastAPI
            # BackgroundTasks runs sync handlers in a worker thread), and
            # asyncio.Queue is not thread-safe. Once broadcast_loop() has captured
            # the running loop, hand the put back to it safely; before that (e.g.
            # in tests with no running loop), put directly.
            if self._loop is not None:
                self._loop.call_soon_threadsafe(self._queue.put_nowait, message)
            else:
                self._queue.put_nowait(message)
        except Exception:
            pass

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            
    async def broadcast_loop(self):
        self._loop = asyncio.get_running_loop()
        while True:
            message = await self._queue.get()
            for connection in self.active_connections:
                try:
                    await connection.send_text(message)
                except Exception:
                    self.disconnect(connection)
