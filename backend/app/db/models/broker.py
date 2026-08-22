"""Encrypted broker credentials and tokens. Ciphertext only; never returned to React."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, UniqueConstraint, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.db.models.enums import BrokerCode, BrokerConnectionStatus, sql_in_list
from app.db.models.mixins import TimestampMixin


class BrokerAccount(TimestampMixin, Base):
    __tablename__ = "broker_accounts"
    __table_args__ = (
        UniqueConstraint("user_id", "broker", "client_id", name="uq_broker_accounts_user_broker_client"),
        CheckConstraint(f"broker IN {sql_in_list(BrokerCode)}", name="broker"),
        CheckConstraint(
            f"status IN {sql_in_list(BrokerConnectionStatus)}",
            name="status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    broker: Mapped[str] = mapped_column(String(32), nullable=False)
    client_id: Mapped[str] = mapped_column(String(128), nullable=False)
    encrypted_api_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    encrypted_api_secret: Mapped[str | None] = mapped_column(Text, nullable=True)
    encrypted_totp: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default=text(f"'{BrokerConnectionStatus.DISCONNECTED.value}'"),
    )

    tokens: Mapped[list[BrokerToken]] = relationship(back_populates="broker_account")


class BrokerToken(TimestampMixin, Base):
    __tablename__ = "broker_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    broker_account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("broker_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    encrypted_access_token: Mapped[str] = mapped_column(Text, nullable=False)
    token_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    broker_account: Mapped[BrokerAccount] = relationship(back_populates="tokens")
