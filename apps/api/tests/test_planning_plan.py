"""The plan and its items are plain objects: tested without any port."""

from datetime import UTC, datetime
from uuid import UUID

import pytest

from novoya_api.planning.domain.errors import InvalidPlan, NoOfferFits
from novoya_api.planning.domain.plan import DraftItem, Plan, PlanStatus, keep_valid
from novoya_api.shared.domain.errors import InvalidInput

WISH_ID = UUID("00000000-0000-0000-0000-0000000000a1")
HOTEL = UUID("00000000-0000-0000-0000-0000000000b1")
WALK = UUID("00000000-0000-0000-0000-0000000000b2")
BOAT = UUID("00000000-0000-0000-0000-0000000000b3")
UNKNOWN = UUID("00000000-0000-0000-0000-0000000000ff")
NOW = datetime(2026, 10, 19, 9, 0, tzinfo=UTC)

DRAFTS = [
    DraftItem(WALK, 3, 1, "Morning walk"),
    DraftItem(HOTEL, 1, 7, None),
    DraftItem(BOAT, 3, 2, None),
]


def propose(drafts=DRAFTS, trip_days: int = 8) -> Plan:
    return Plan.propose(WISH_ID, True, "A week by the sea", drafts, trip_days, NOW)


# Errors


def test_plan_errors_are_422_input_errors_with_stable_codes():
    assert issubclass(InvalidPlan, InvalidInput)
    assert issubclass(NoOfferFits, InvalidInput)
    assert InvalidPlan.code == "invalid_plan"
    assert NoOfferFits.code == "no_offer_fits"


def test_plan_status_values_are_lowercase():
    assert [status.value for status in PlanStatus] == [
        "proposed",
        "requested",
        "negotiating",
        "quoted",
        "accepted",
        "rejected",
    ]


# Plan.propose


def test_propose_makes_a_proposed_plan_for_the_wish():
    plan = propose()

    assert plan.status is PlanStatus.PROPOSED
    assert plan.wish_id == WISH_ID
    assert plan.based_on_preferences is True
    assert plan.summary == "A week by the sea"
    assert plan.created_at == NOW
    assert plan.updated_at == NOW
    assert plan.assigned_agent_id is None


def test_propose_sorts_items_by_day_keeping_the_order_within_a_day():
    plan = propose()

    assert [(item.offer_id, item.day) for item in plan.items] == [
        (HOTEL, 1),
        (WALK, 3),
        (BOAT, 3),
    ]


def test_propose_copies_quantity_and_note():
    plan = propose()

    assert [(item.quantity, item.note) for item in plan.items] == [
        (7, None),
        (1, "Morning walk"),
        (2, None),
    ]


def test_proposed_items_have_no_negotiated_price_and_are_not_removed():
    plan = propose()

    assert all(item.negotiated_price is None for item in plan.items)
    assert all(item.removed is False for item in plan.items)


def test_propose_gives_new_ids_to_the_plan_and_each_item():
    first, second = propose(), propose()

    assert first.id != second.id
    assert len({item.id for item in first.items}) == len(DRAFTS)
    assert {item.id for item in first.items}.isdisjoint(item.id for item in second.items)


def test_propose_accepts_an_item_on_the_last_day():
    plan = propose([DraftItem(WALK, 8, 1, None)], trip_days=8)

    assert plan.items[0].day == 8


@pytest.mark.parametrize(
    "drafts",
    [
        [],
        [DraftItem(WALK, 0, 1, None)],
        [DraftItem(WALK, 9, 1, None)],
        [DraftItem(WALK, 2, 0, None)],
    ],
    ids=["no item", "day 0", "day after the trip", "quantity 0"],
)
def test_propose_with_invalid_items_raises_invalid_plan(drafts):
    with pytest.raises(InvalidPlan):
        propose(drafts, trip_days=8)


# keep_valid


def test_keep_valid_drops_an_offer_that_is_not_allowed():
    drafts = [DraftItem(HOTEL, 1, 7, None), DraftItem(UNKNOWN, 2, 1, None)]

    assert keep_valid(drafts, {HOTEL, WALK}, trip_days=8) == [DraftItem(HOTEL, 1, 7, None)]


@pytest.mark.parametrize("day", [0, -1, 9])
def test_keep_valid_drops_a_day_outside_the_trip(day):
    drafts = [DraftItem(WALK, day, 1, None), DraftItem(HOTEL, 1, 7, None)]

    assert keep_valid(drafts, {HOTEL, WALK}, trip_days=8) == [DraftItem(HOTEL, 1, 7, None)]


def test_keep_valid_drops_a_quantity_below_one():
    drafts = [DraftItem(WALK, 2, 0, None), DraftItem(HOTEL, 1, 7, None)]

    assert keep_valid(drafts, {HOTEL, WALK}, trip_days=8) == [DraftItem(HOTEL, 1, 7, None)]


def test_keep_valid_keeps_the_order_of_valid_items():
    drafts = [
        DraftItem(WALK, 3, 1, None),
        DraftItem(HOTEL, 1, 7, None),
        DraftItem(WALK, 8, 1, None),
    ]

    assert keep_valid(drafts, {HOTEL, WALK}, trip_days=8) == drafts
