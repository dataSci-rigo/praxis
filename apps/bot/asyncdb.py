"""Single helper for calling sync Django ORM code from PTB's async handlers."""

from asgiref.sync import sync_to_async


async def db(func, *args, **kwargs):
    return await sync_to_async(func, thread_sensitive=True)(*args, **kwargs)
