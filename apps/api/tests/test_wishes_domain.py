"""The wish, its destination and its panel are plain objects: tested without any port."""

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from novoya_api.shared.domain.errors import DomainError, InvalidTransition
from novoya_api.wishes.domain.errors import InvalidWish
from novoya_api.wishes.domain.panel import Panel, PanelSection, Tag
from novoya_api.wishes.domain.wish import Destination, Wish, WishStatus, find_covered

USER_ID = UUID("00000000-0000-0000-0000-000000000001")
CREATED = datetime(2026, 10, 18, 9, 0, tzinfo=UTC)
LATER = datetime(2026, 10, 18, 9, 5, tzinfo=UTC)

LISBON = Destination("Portugal", "Lisbon")
PORTO = Destination("Portugal", "Porto")
MARRAKECH = Destination("Morocco", "Marrakech")
COVERED = [LISBON, PORTO, MARRAKECH]

PANEL = Panel(sections=(PanelSection("style", "Style", True, (Tag("beach", "Beach"),)),))


def new_wish() -> Wish:
    return Wish.create(USER_ID, "A week in the sun", CREATED)


# Destination and coverage


def test_destination_city_defaults_to_none():
    assert Destination("Portugal").city is None


def test_destination_is_immutable():
    with pytest.raises(FrozenInstanceError):
        LISBON.city = "Porto"  # type: ignore[misc]


def test_find_covered_returns_the_covered_city():
    assert find_covered(Destination("Portugal", "Porto"), COVERED) == PORTO


def test_find_covered_ignores_case_and_whitespace():
    assert find_covered(Destination("  portugal ", "LISBON"), COVERED) == LISBON


def test_find_covered_without_city_returns_the_first_covered_entry_of_the_country():
    assert find_covered(Destination("Portugal"), COVERED) == LISBON


def test_find_covered_returns_none_for_an_uncovered_city_in_a_covered_country():
    assert find_covered(Destination("Portugal", "Faro"), COVERED) is None


def test_find_covered_returns_none_for_an_uncovered_country():
    assert find_covered(Destination("Spain", "Lisbon"), COVERED) is None


def test_find_covered_returns_none_when_nothing_is_covered():
    assert find_covered(LISBON, []) is None


def test_find_covered_matches_a_city_in_a_country_wide_entry():
    morocco = Destination("Morocco")

    assert find_covered(Destination("Morocco", "Fes"), [morocco]) == morocco


# Wish creation


def test_create_starts_a_draft_without_destination_or_panel():
    wish = Wish.create(USER_ID, "A week in Lisbon", CREATED)

    assert isinstance(wish.id, UUID)
    assert wish.user_id == USER_ID
    assert wish.text == "A week in Lisbon"
    assert wish.status is WishStatus.DRAFT
    assert wish.destination is None
    assert wish.panel is None
    assert wish.created_at == CREATED
    assert wish.updated_at == CREATED


def test_create_strips_the_text():
    wish = Wish.create(USER_ID, "  A week in Lisbon \n", CREATED)

    assert wish.text == "A week in Lisbon"


def test_create_gives_each_wish_its_own_id():
    assert new_wish().id != new_wish().id


@pytest.mark.parametrize("text", ["", "   ", "\n\t"])
def test_create_with_blank_text_raises_invalid_wish(text):
    with pytest.raises(InvalidWish):
        Wish.create(USER_ID, text, CREATED)


def test_invalid_wish_is_a_domain_error():
    assert issubclass(InvalidWish, DomainError)


def test_wish_status_values():
    assert [status.value for status in WishStatus] == [
        "draft",
        "not_covered",
        "panel_shown",
        "answered",
        "planned",
    ]


# Wish transitions


def test_mark_not_covered_sets_status_destination_and_updated_at():
    wish = new_wish()
    madrid = Destination("Spain", "Madrid")

    wish.mark_not_covered(madrid, LATER)

    assert wish.status is WishStatus.NOT_COVERED
    assert wish.destination == madrid
    assert wish.panel is None
    assert wish.updated_at == LATER
    assert wish.created_at == CREATED


def test_show_panel_sets_status_destination_panel_and_updated_at():
    wish = new_wish()

    wish.show_panel(LISBON, PANEL, LATER)

    assert wish.status is WishStatus.PANEL_SHOWN
    assert wish.destination == LISBON
    assert wish.panel == PANEL
    assert wish.updated_at == LATER
    assert wish.created_at == CREATED


def test_show_panel_after_not_covered_raises_invalid_transition():
    wish = new_wish()
    wish.mark_not_covered(Destination("Spain"), LATER)

    with pytest.raises(InvalidTransition):
        wish.show_panel(LISBON, PANEL, LATER)


def test_mark_not_covered_after_panel_shown_raises_invalid_transition():
    wish = new_wish()
    wish.show_panel(LISBON, PANEL, LATER)

    with pytest.raises(InvalidTransition):
        wish.mark_not_covered(Destination("Spain"), LATER)


def test_show_panel_twice_raises_invalid_transition():
    wish = new_wish()
    wish.show_panel(LISBON, PANEL, LATER)

    with pytest.raises(InvalidTransition):
        wish.show_panel(LISBON, PANEL, LATER)


def test_mark_not_covered_twice_raises_invalid_transition():
    wish = new_wish()
    wish.mark_not_covered(Destination("Spain"), LATER)

    with pytest.raises(InvalidTransition):
        wish.mark_not_covered(Destination("Spain"), LATER)


@pytest.mark.parametrize("status", [WishStatus.ANSWERED, WishStatus.PLANNED])
def test_transitions_from_a_later_status_raise_invalid_transition(status):
    wish = Wish(
        id=uuid4(),
        user_id=USER_ID,
        text="A week in Lisbon",
        status=status,
        destination=LISBON,
        panel=PANEL,
        created_at=CREATED,
        updated_at=CREATED,
    )

    with pytest.raises(InvalidTransition):
        wish.show_panel(LISBON, PANEL, LATER)
    with pytest.raises(InvalidTransition):
        wish.mark_not_covered(LISBON, LATER)


# Panel


def test_from_tags_groups_tags_by_section_in_order_of_first_appearance():
    panel = Panel.from_tags(["style:beach", "food:seafood", "style:city", "food:street_food"])

    assert [section.id for section in panel.sections] == ["style", "food"]
    assert [tag.id for tag in panel.sections[0].tags] == ["beach", "city"]
    assert [tag.id for tag in panel.sections[1].tags] == ["seafood", "street_food"]


def test_from_tags_puts_a_tag_without_section_in_preferences():
    panel = Panel.from_tags(["quiet"])

    assert panel.sections == (
        PanelSection("preferences", "Preferences", True, (Tag("quiet", "Quiet"),)),
    )


def test_from_tags_removes_duplicates():
    panel = Panel.from_tags(["style:beach", "style:beach", "style:city"])

    assert [tag.id for tag in panel.sections[0].tags] == ["beach", "city"]


def test_from_tags_trims_and_lowercases_ids():
    panel = Panel.from_tags(["  STYLE:Beach  ", "style:beach"])

    assert panel.sections == (PanelSection("style", "Style", True, (Tag("beach", "Beach"),)),)


@pytest.mark.parametrize("empty", ["", "   "])
def test_from_tags_ignores_empty_strings(empty):
    panel = Panel.from_tags([empty, "style:beach"])

    assert panel.sections == (PanelSection("style", "Style", True, (Tag("beach", "Beach"),)),)


def test_from_tags_builds_titles_and_labels_from_ids():
    panel = Panel.from_tags(["night_life:live-music", "food:sea_food"])

    assert panel.sections[0].title == "Night life"
    assert panel.sections[0].tags[0].label == "Live music"
    assert panel.sections[1].tags[0].label == "Sea food"


def test_from_tags_makes_every_section_multi_and_no_tag_preselected():
    panel = Panel.from_tags(["style:beach", "quiet", "food:seafood"])

    assert all(section.multi for section in panel.sections)
    assert not any(tag.preselected for section in panel.sections for tag in section.tags)


def test_from_tags_asks_budget_persons_and_dates():
    panel = Panel.from_tags(["style:beach"])

    assert panel.ask_budget is True
    assert panel.ask_persons is True
    assert panel.ask_dates is True


def test_from_tags_without_tags_has_no_sections():
    assert Panel.from_tags([]).sections == ()


def test_to_dict_returns_the_architecture_shape():
    panel = Panel.from_tags(["style:beach", "style:city", "quiet"])

    assert panel.to_dict() == {
        "sections": [
            {
                "id": "style",
                "title": "Style",
                "multi": True,
                "tags": [
                    {"id": "beach", "label": "Beach", "preselected": False},
                    {"id": "city", "label": "City", "preselected": False},
                ],
            },
            {
                "id": "preferences",
                "title": "Preferences",
                "multi": True,
                "tags": [{"id": "quiet", "label": "Quiet", "preselected": False}],
            },
        ],
        "ask_budget": True,
        "ask_persons": True,
        "ask_dates": True,
    }


def test_to_dict_keeps_preselected_and_ask_flags():
    panel = Panel(
        sections=(PanelSection("style", "Style", False, (Tag("beach", "Beach", True),)),),
        ask_budget=False,
        ask_persons=True,
        ask_dates=False,
    )

    assert panel.to_dict() == {
        "sections": [
            {
                "id": "style",
                "title": "Style",
                "multi": False,
                "tags": [{"id": "beach", "label": "Beach", "preselected": True}],
            }
        ],
        "ask_budget": False,
        "ask_persons": True,
        "ask_dates": False,
    }
