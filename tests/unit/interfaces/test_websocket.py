import asyncio
import json
import threading

from enterprise_os.interfaces.api.websocket import EventStreamer
from enterprise_os.runtime.events import EventDispatcher, GoalCreated


class FakeWebSocket:
    def __init__(self):
        self.sent: list[str] = []

    async def accept(self) -> None:
        pass

    async def send_text(self, message: str) -> None:
        self.sent.append(message)


def test_handle_event_puts_directly_when_no_loop_captured():
    dispatcher = EventDispatcher()
    streamer = EventStreamer(dispatcher)

    dispatcher.dispatch(GoalCreated(session_id="s1", goal_id="g1", description="d"))

    assert streamer._queue.qsize() == 1


def test_handle_event_from_worker_thread_is_delivered_safely():
    """Regression test for P1-2: dispatch() can run on a non-event-loop thread
    (FastAPI BackgroundTasks executes sync handlers in a worker thread), so
    _handle_event must not call the non-thread-safe asyncio.Queue.put_nowait()
    directly once a loop is running elsewhere."""

    async def scenario():
        dispatcher = EventDispatcher()
        streamer = EventStreamer(dispatcher)
        ws = FakeWebSocket()
        await streamer.connect(ws)

        broadcast_task = asyncio.create_task(streamer.broadcast_loop())
        await asyncio.sleep(0.05)  # let broadcast_loop capture the running loop
        assert streamer._loop is asyncio.get_running_loop()

        def dispatch_from_thread():
            dispatcher.dispatch(
                GoalCreated(session_id="s2", goal_id="g2", description="cross-thread")
            )

        thread = threading.Thread(target=dispatch_from_thread)
        thread.start()
        thread.join()

        for _ in range(25):
            if ws.sent:
                break
            await asyncio.sleep(0.02)

        broadcast_task.cancel()
        try:
            await broadcast_task
        except asyncio.CancelledError:
            pass

        assert len(ws.sent) == 1
        payload = json.loads(ws.sent[0])
        assert payload["type"] == "GoalCreated"
        assert payload["data"]["goal_id"] == "g2"

    asyncio.run(scenario())
