from novoya_api.wishes.domain.wish import Destination, find_covered

# Until the partner catalog exists (#17): a few destinations so POST /wishes works end to end.
# Same names and tag format ("section:tag") as the seed planned in #17.
_TAGS = {
    Destination("Portugal", "Lisbon"): [
        "style:beach",
        "style:culture",
        "rhythm:calm",
        "food:seafood",
        "accommodation:hotel",
    ],
    Destination("Portugal", "Porto"): [
        "style:culture",
        "style:city",
        "food:wine",
        "accommodation:guesthouse",
    ],
    Destination("Morocco", "Marrakech"): [
        "style:culture",
        "style:desert",
        "rhythm:active",
        "food:street_food",
        "accommodation:riad",
    ],
}


class StaticCatalog:
    """Catalog with fixed data. Replaced by an adapter over catalog.public when #17 lands."""

    async def covered_destinations(self) -> list[Destination]:
        return list(_TAGS)

    async def tags_at(self, destination: Destination) -> list[str]:
        if destination.city is None:
            return [
                tag
                for place, tags in _TAGS.items()
                if find_covered(destination, [place])
                for tag in tags
            ]
        match = find_covered(destination, list(_TAGS))
        return list(_TAGS[match]) if match else []
