from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base

class Mandi(Base):
    __tablename__ = "mandis"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    state: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    district: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lng: Mapped[float] = mapped_column(Float, nullable=False)
    geocode_source: Mapped[str] = mapped_column(String(50), nullable=False)
    geocode_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    prices: Mapped[List["Price"]] = relationship(
        "Price",
        back_populates="mandi",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_mandis_state_district", "state", "district"),
    )

class Price(Base):
    __tablename__ = "prices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mandi_id: Mapped[int] = mapped_column(
        ForeignKey("mandis.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    commodity: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    variety: Mapped[str] = mapped_column(String(100), nullable=False, default="Default")
    grade: Mapped[str] = mapped_column(String(50), nullable=False, default="FAQ")
    arrival_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    min_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    modal_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    max_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="data.gov.in")
    is_seeded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    mandi: Mapped["Mandi"] = relationship("Mandi", back_populates="prices")

    __table_args__ = (
        UniqueConstraint(
            "mandi_id",
            "commodity",
            "variety",
            "grade",
            "arrival_date",
            name="uq_mandi_commodity_variety_grade_date",
        ),
        Index("ix_prices_mandi_commodity_date", "mandi_id", "commodity", "arrival_date"),
        Index("ix_prices_commodity_date", "commodity", "arrival_date"),
    )

class GeocodeCache(Base):
    __tablename__ = "geocode_cache"

    key: Mapped[str] = mapped_column(String(255), primary_key=True)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lng: Mapped[float] = mapped_column(Float, nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

class DistanceCache(Base):
    __tablename__ = "distance_cache"

    origin_key: Mapped[str] = mapped_column(String(255), primary_key=True)
    mandi_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    road_km: Mapped[float] = mapped_column(Float, nullable=False)
    duration_min: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_distance_cache_origin", "origin_key"),
    )
