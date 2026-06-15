"""Ponte entre o Streamlit (síncrono) e o SQLAlchemy async (asyncpg).

Problema: asyncpg amarra cada conexão ao event loop que a criou. O Streamlit
roda o script de forma síncrona e re-executa a cada interação, em threads de
ScriptRunner distintas. Usar ``asyncio.run`` por chamada criaria um loop novo a
cada vez — incompatível com um pool de conexões reaproveitado.

Solução: um único event loop rodando numa thread de fundo dedicada, criado uma
vez e mantido vivo. Todas as coroutines são submetidas a esse loop via
``run_coroutine_threadsafe``, garantindo que o engine e o pool de conexões vivam
sempre no mesmo loop.

No Streamlit, instancie ``AsyncRunner`` uma única vez com ``@st.cache_resource``.
"""

from __future__ import annotations

import asyncio
import threading
from typing import Any, Coroutine, TypeVar

_T = TypeVar("_T")


class AsyncRunner:
    """Executa coroutines num event loop dedicado e persistente."""

    def __init__(self) -> None:
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._run_loop, name="async-runner-loop", daemon=True
        )
        self._thread.start()

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def run(self, coro: Coroutine[Any, Any, _T]) -> _T:
        """Submete a coroutine ao loop de fundo e bloqueia até o resultado."""
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()
