"""The plan and its items are plain objects: tested without any port."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from novoya_api.planning.domain.errors import InvalidPlan, NoOfferFits, PlanNotFound
from novoya_api.planning.domain.plan import DraftItem, Plan, PlanStatus, keep_valid
from novoya_api.shared.domain.errors import InvalidInput, InvalidTransition, PermissionDenied

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


# request_quote


def test_request_quote_moves_a_proposed_plan_to_requested():
    plan = propose()
    later = datetime(2026, 10, 19, 10, 0, tzinfo=UTC)

    plan.request_quote(later)

    assert plan.status is PlanStatus.REQUESTED
    assert plan.updated_at == later
    assert all(item.negotiated_price is None for item in plan.items)


@pytest.mark.parametrize("status", [s for s in PlanStatus if s is not PlanStatus.PROPOSED])
def test_request_quote_from_any_other_status_raises_invalid_transition(status):
    plan = propose()
    plan.status = status

    with pytest.raises(InvalidTransition):
        plan.request_quote(NOW)

    assert plan.status is status


# take


def test_take_moves_a_requested_plan_to_negotiating():
    plan = propose()
    plan.request_quote(NOW)
    agent = uuid4()
    later = datetime(2026, 10, 19, 10, 0, tzinfo=UTC)

    plan.take(agent, later)

    assert plan.status is PlanStatus.NEGOTIATING
    assert plan.assigned_agent_id == agent
    assert plan.updated_at == later


@pytest.mark.parametrize("status", [s for s in PlanStatus if s is not PlanStatus.REQUESTED])
def test_take_from_any_other_status_raises_invalid_transition(status):
    plan = propose()
    plan.status = status
    if status is PlanStatus.PROPOSED:
        plan.assigned_agent_id = None

    with pytest.raises(InvalidTransition):
        plan.take(uuid4(), NOW)

    assert plan.status is status


# set_item_price / remove_item


def negotiating_plan() -> tuple[Plan, UUID]:
    plan = propose()
    plan.request_quote(NOW)
    agent = uuid4()
    plan.take(agent, NOW)
    return plan, agent


def test_set_item_price_stores_the_negotiated_price():
    plan, agent = negotiating_plan()
    item = plan.items[0]
    later = datetime(2026, 10, 19, 11, 0, tzinfo=UTC)

    plan.set_item_price(item.id, agent, Decimal("120.00"), later)

    assert plan.items[0].negotiated_price == Decimal("120.00")
    assert plan.priced_total() == Decimal("120.00")
    assert plan.updated_at == later


def test_set_item_price_by_another_agent_is_forbidden():
    plan, _agent = negotiating_plan()
    with pytest.raises(PermissionDenied):
        plan.set_item_price(plan.items[0].id, uuid4(), Decimal("10.00"), NOW)


def test_set_item_price_when_not_negotiating_raises_invalid_transition():
    plan = propose()
    with pytest.raises(InvalidTransition):
        plan.set_item_price(plan.items[0].id, uuid4(), Decimal("10.00"), NOW)


def test_set_item_price_must_be_more_than_zero():
    plan, agent = negotiating_plan()
    with pytest.raises(InvalidPlan):
        plan.set_item_price(plan.items[0].id, agent, Decimal("0"), NOW)


def test_set_item_price_of_an_unknown_item_is_not_found():
    plan, agent = negotiating_plan()
    with pytest.raises(PlanNotFound):
        plan.set_item_price(uuid4(), agent, Decimal("10.00"), NOW)


def test_remove_item_hides_it_from_the_total():
    plan, agent = negotiating_plan()
    first, second = plan.items[0], plan.items[1]
    plan.set_item_price(first.id, agent, Decimal("50.00"), NOW)

    plan.remove_item(first.id, agent, NOW)

    assert plan.items[0].removed is True
    assert plan.items[0].negotiated_price is None
    assert plan.priced_total() == Decimal("0")
    assert second.id in {item.id for item in plan.items if not item.removed}


def test_remove_item_cannot_drop_the_last_kept_item():
    plan, agent = negotiating_plan()
    for item in plan.items[1:]:
        plan.remove_item(item.id, agent, NOW)

    with pytest.raises(InvalidPlan):
        plan.remove_item(plan.items[0].id, agent, NOW)


def test_restore_item_puts_a_removed_item_back():
    plan, agent = negotiating_plan()
    item = plan.items[0]
    plan.set_item_price(item.id, agent, Decimal("50.00"), NOW)
    plan.remove_item(item.id, agent, NOW)
    later = datetime(2026, 10, 19, 11, 0, tzinfo=UTC)

    plan.restore_item(item.id, agent, later)
    plan.set_item_price(item.id, agent, Decimal("40.00"), later)

    assert plan.items[0].removed is False
    assert plan.items[0].negotiated_price == Decimal("40.00")
    assert plan.updated_at == later


def test_set_item_price_of_a_removed_item_is_invalid():
    plan, agent = negotiating_plan()
    plan.remove_item(plan.items[0].id, agent, NOW)

    with pytest.raises(InvalidPlan):
        plan.set_item_price(plan.items[0].id, agent, Decimal("10.00"), NOW)


def test_priced_total_ignores_unpriced_and_removed_items():
    plan, agent = negotiating_plan()
    plan.set_item_price(plan.items[0].id, agent, Decimal("80.00"), NOW)
    plan.set_item_price(plan.items[1].id, agent, Decimal("20.00"), NOW)
    plan.remove_item(plan.items[1].id, agent, NOW)

    assert plan.priced_total() == Decimal("80.00")


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
