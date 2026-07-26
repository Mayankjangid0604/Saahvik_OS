import asyncio

from enterprise_os.interfaces.api import ceo_api


def test_startup_event_keeps_a_strong_reference_to_the_broadcast_task():
    """Regression test: startup_event() used to call
    asyncio.create_task(event_streamer.broadcast_loop()) without storing the
    returned Task anywhere. Per the asyncio docs, a task with no strong
    reference held elsewhere can be garbage-collected mid-execution -- which
    would silently kill the WebSocket dashboard's event stream with no error
    (found via `ruff check --select RUF006`). startup_event() now stores the
    task in the module-level _broadcast_task so it's kept alive for the
    lifetime of the app."""

    async def scenario():
        assert ceo_api._broadcast_task is None or ceo_api._broadcast_task.done()
        await ceo_api.startup_event()
        try:
            assert ceo_api._broadcast_task is not None
            assert isinstance(ceo_api._broadcast_task, asyncio.Task)
            assert not ceo_api._broadcast_task.done()
        finally:
            ceo_api._broadcast_task.cancel()
            try:
                await ceo_api._broadcast_task
            except asyncio.CancelledError:
                pass

    asyncio.run(scenario())
