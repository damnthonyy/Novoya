"""The admin overview use cases (#130) on fakes: how the search and the filters combine."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from novoya_api.planning.application.use_cases.list_admin_plans import ListAdminPlans
from novoya_api.quoting.application.use_cases.list_admin_quotes import ListAdminQuotes
from novoya_api.quoting.domain.quote import Quote, QuoteStatus
from novoya_api.shared.domain.value_objects import Locale

NOW = datetime(2026, 10, 22, 9, 0, tzinfo=UTC)


class FakePlans:
    def __init__(self) -> None:
        self.searches: list[tuple] = []

    async def search(self, statuses, wish_ids, *, limit, offset):
        self.searches.append((list(statuses), wish_ids))
        return []


class EmptyTrips:
    async def for_wish_ids(self, wish_ids):
        return {}


class FakeWishSearch:
    def __init__(self, found) -> None:
        self.found = found
        self.calls: list[tuple] = []

    async def matching(self, query, user_ids):
        self.calls.append((query, list(user_ids)))
        return self.found


class FakePeople:
    def __init__(self, user_ids=()) -> None:
        self.user_ids = list(user_ids)

    async def search_ids(self, query):
        return self.user_ids

    async def get_many(self, user_ids):
        return {}


def plans_use_case(found_wishes=()):
    plans, search = FakePlans(), FakeWishSearch(list(found_wishes))
    alice = uuid4()
    return ListAdminPlans(plans, EmptyTrips(), search, FakePeople([alice])), plans, search, alice


async def test_a_plan_search_passes_the_matching_clients_to_the_wish_search():
    use_case, plans, search, alice = plans_use_case([uuid4()])

    await use_case(query="  alice  ")

    assert search.calls == [("alice", [alice])]
    assert plans.searches[0][1] == search.found


async def test_a_plan_search_without_a_matching_wish_reads_no_plan():
    use_case, plans, _, _ = plans_use_case([])

    assert await use_case(query="nowhere") == []
    assert plans.searches == []


async def test_without_a_search_every_wish_is_read():
    use_case, plans, search, _ = plans_use_case()

    await use_case()

    assert search.calls == []
    assert plans.searches == [([], None)]


async def test_one_wish_outside_the_search_gives_nothing():
    use_case, plans, _, _ = plans_use_case([uuid4()])

    assert await use_case(query="alice", wish_id=uuid4()) == []
    assert plans.searches == []


class FakeQuotes:
    def __init__(self) -> None:
        self.searches: list[tuple] = []

    async def search(self, plan_ids, expired, now, *, limit, offset):
        self.searches.append((plan_ids, expired, now))
        return []


class FakePlanQuoting:
    def __init__(self, found) -> None:
        self.found = found
        self.calls: list[tuple] = []

    async def find_ids(self, statuses, query, user_ids):
        self.calls.append((list(statuses), query, list(user_ids)))
        return self.found

    async def facts(self, plan_ids):
        return {}


class FixedClock:
    def now(self):
        return NOW


def quotes_use_case(found=()):
    quotes, plans = FakeQuotes(), FakePlanQuoting(list(found))
    return ListAdminQuotes(quotes, plans, FakePeople(), FixedClock()), quotes, plans


async def test_sent_and_expired_quotes_wait_on_a_quoted_plan():
    plan_id = uuid4()
    use_case, quotes, plans = quotes_use_case([plan_id])

    await use_case(QuoteStatus.SENT)
    await use_case(QuoteStatus.EXPIRED)

    assert [call[0] for call in plans.calls] == [["quoted"], ["quoted"]]
    assert [(s[0], s[1]) for s in quotes.searches] == [([plan_id], False), ([plan_id], True)]


async def test_accepted_quotes_follow_the_plans_answer():
    use_case, quotes, plans = quotes_use_case([uuid4()])

    await use_case(QuoteStatus.ACCEPTED)

    assert plans.calls[0][0] == ["accepted"]
    assert quotes.searches[0][1] is None


async def test_without_a_filter_every_quote_is_read():
    use_case, quotes, plans = quotes_use_case()

    await use_case()

    assert plans.calls == []
    assert quotes.searches == [(None, None, NOW)]


async def test_no_matching_plan_reads_no_quote():
    use_case, quotes, _ = quotes_use_case([])

    assert await use_case(query="nowhere") == []
    assert quotes.searches == []


def a_quote(sent_at: datetime) -> Quote:
    return Quote.issue(uuid4(), uuid4(), uuid4(), Decimal("10.00"), Locale.EN, sent_at)


def test_a_quote_is_sent_until_it_expires_a_week_later():
    quote = a_quote(NOW)

    assert quote.status("quoted", NOW + timedelta(days=7)) is QuoteStatus.SENT
    assert quote.status("quoted", NOW + timedelta(days=7, seconds=1)) is QuoteStatus.EXPIRED


def test_the_clients_answer_wins_over_the_validity():
    quote = a_quote(NOW)

    assert quote.status("accepted", NOW + timedelta(days=30)) is QuoteStatus.ACCEPTED
    assert quote.status("rejected", NOW) is QuoteStatus.REJECTED
