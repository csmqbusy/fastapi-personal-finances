import asyncio

from aio_pika import connect_robust
from aio_pika.patterns import RPC

from app.core.config import settings
from charts_service.app.services import (
    create_simple_chart,
    create_simple_annual_chart,
)


async def main() -> None:
    connection = await connect_robust(
        settings.broker.url,
    )

    channel = await connection.channel()

    rpc = await RPC.create(channel)

    # first param is also the queue name
    await rpc.register(
        "create_simple_chart",
        create_simple_chart,
        auto_delete=True,
    )
    await rpc.register(
        "create_simple_annual_chart",
        create_simple_annual_chart,
        auto_delete=True,
    )

    try:
        await asyncio.Future()
    finally:
        await connection.close()


if __name__ == "__main__":
    asyncio.run(main())
