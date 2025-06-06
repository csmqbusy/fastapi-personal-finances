import uuid

from sqlalchemy import UUID
from sqlalchemy.orm import Mapped, mapped_column


class IdUuidPkMixin(object):
    id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        primary_key=True,
        default=uuid.uuid4,
    )
