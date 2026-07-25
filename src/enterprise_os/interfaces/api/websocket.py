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
        
        # Subscribe to all events
        self.dispatcher.subscribe(Event, self._handle_event)
        
    def _handle_event(self, event: Event) -> None:
        try:
            event_data = {
                "type": type(event).__name__,
                "data": dataclasses.asdict(event)
            }
            self._queue.put_nowait(json.dumps(event_data))
        except Exception:
            pass

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            
    async def broadcast_loop(self):
        while True:
            message = await self._queue.get()
            for connection in self.active_connections:
                try:
                    await connection.send_text(message)
                except Exception:
                    self.disconnect(connection)
