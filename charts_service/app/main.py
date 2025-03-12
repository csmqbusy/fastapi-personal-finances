import asyncio

from aio_pika import connect_robust
from aio_pika.patterns import RPC

from app.core.config import settings
from charts_service.app.services import (
    create_simple_chart,
    create_simple_annual_chart,
    create_annual_chart_with_categories,
    create_simple_monthly_chart,
    create_monthly_chart_with_categories,
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
    await rpc.register(
        "create_annual_chart_with_categories",
        create_annual_chart_with_categories,
        auto_delete=True,
    )
    await rpc.register(
        "create_simple_monthly_chart",
        create_simple_monthly_chart,
        auto_delete=True,
    )
    await rpc.register(
        "create_monthly_chart_with_categories",
        create_monthly_chart_with_categories,
        auto_delete=True,
    )

    try:
        await asyncio.Future()
    finally:
        await connection.close()


if __name__ == "__main__":
    asyncio.run(main())
