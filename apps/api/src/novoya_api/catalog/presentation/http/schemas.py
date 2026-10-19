from datetime import date
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from novoya_api.catalog.domain import Offer, Partner

KindName = Literal["hotel", "guide", "transport", "activity", "agency"]
PlaceName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=64)]
ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]
LongText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Phone = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=32)]
EmailText = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True, min_length=3, max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    ),
]


class PartnerResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    name: str
    kind: KindName
    country: str
    city: str
    contact_email: str
    contact_phone: str
    active: bool

    @classmethod
    def of(cls, partner: Partner) -> "PartnerResponse":
        return cls(
            id=partner.id,
            name=partner.name,
            kind=partner.kind.value,
            country=partner.country,
            city=partner.city,
            contact_email=partner.contact_email,
            contact_phone=partner.contact_phone,
            active=partner.active,
        )


class CreatePartnerRequest(BaseModel):
    name: ShortText
    kind: KindName
    country: PlaceName
    city: PlaceName
    contact_email: EmailText
    contact_phone: Phone
    active: bool = True


class UpdatePartnerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: ShortText | None = None
    kind: KindName | None = None
    country: PlaceName | None = None
    city: PlaceName | None = None
    contact_email: EmailText | None = None
    contact_phone: Phone | None = None
    active: bool | None = None


class OfferResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    partner_id: UUID
    kind: KindName
    title: str
    description: str
    country: str
    city: str
    min_persons: int
    max_persons: int
    available_from: date
    available_to: date
    tags: list[str]
    featured: bool
    active: bool

    @classmethod
    def of(cls, offer: Offer) -> "OfferResponse":
        return cls(
            id=offer.id,
            partner_id=offer.partner_id,
            kind=offer.kind.value,
            title=offer.title,
            description=offer.description,
            country=offer.country,
            city=offer.city,
            min_persons=offer.min_persons,
            max_persons=offer.max_persons,
            available_from=offer.available_from,
            available_to=offer.available_to,
            tags=list(offer.tags),
            featured=offer.featured,
            active=offer.active,
        )


class CreateOfferRequest(BaseModel):
    partner_id: UUID
    kind: KindName
    title: ShortText
    description: LongText
    country: PlaceName
    city: PlaceName
    min_persons: Annotated[int, Field(ge=1)]
    max_persons: Annotated[int, Field(ge=1)]
    available_from: date
    available_to: date
    tags: list[str] = Field(default_factory=list, max_length=50)
    featured: bool = False
    active: bool = True


class UpdateOfferRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: KindName | None = None
    title: ShortText | None = None
    description: LongText | None = None
    country: PlaceName | None = None
    city: PlaceName | None = None
    min_persons: Annotated[int, Field(ge=1)] | None = None
    max_persons: Annotated[int, Field(ge=1)] | None = None
    available_from: date | None = None
    available_to: date | None = None
    tags: Annotated[list[str], Field(max_length=50)] | None = None
    featured: bool | None = None
    active: bool | None = None


class DestinationResponse(BaseModel):
    """A place Novoya can plan a trip, from listed partner offers."""

    model_config = ConfigDict(frozen=True)

    country: str
    city: str
