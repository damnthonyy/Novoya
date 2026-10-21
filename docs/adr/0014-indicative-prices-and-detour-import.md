# 0014. Indicative partner prices, and the DÉTOUR catalog import

- **Status:** Accepted
- **Date:** 2026-10-21
- **Issue / PR:** #83, #119

## Context

The client, DÉTOUR, sent its catalog as a sqlite export: destinations, partners, offers with
a unit price, opening months and terms, travellers' reviews behind consents, trip options
(`preferences`), and also circuits, advisors and test scenarios. Partners do publish a unit
price per person, but the price of a trip is still negotiated (ADR 0006). The reviews are
personal data: ADR 0003 asks for a GDPR review before Novoya reads outside data. Country
names in the export are in French; Novoya stores English names.

## Decision

We import partners, offers, publishable reviews and extras with
`python -m novoya_api.catalog.infrastructure.detour --source detour.sqlite`, and nothing else.

- **Indicative prices on the offer page only.** An offer keeps its unit price (`price_eur`,
  `price_unit` per person per night, trip or activity) and shows it as indicative on
  `GET /offers/{id}`. The plan, the agent's prices and the quote are unchanged: the agent
  still negotiates each item, and the total comes from those negotiated prices.
- **Reviews only from `avis_diffusables`.** That view holds the reviews whose author agreed
  to publication, already pseudonymised ("First name I." or "Voyageur anonyme"). The tables
  `avis`, `avis_publics` and `consentements` are never read. Each import replaces the
  reviews: a review whose consent was withdrawn is deleted on the next import. This is the
  GDPR review ADR 0003 asks for.
- **Not imported:** circuits, advisors, scenarios, raw reviews and consents.
- **Countries in English** (`detour/countries.py`). Any country written in French or in English
  is found through the CLDR names that Babel ships, so a country the client adds later needs no
  code change. The 86 names of the first export keep their English spelling ("Ivory Coast").
  A name that is not a country stops the import. Cities are kept as given.
- Partners have no phone in the export: `contact_phone` is optional. Imported partners are
  marked `source = 'detour'`, and the development seed refuses to run after an import.
- Extras (`included`, `supplement`, `on_quote`) can be added when the client asks for a
  quote. A supplement is counted once, at its amount then; the agent prices `on_quote`
  extras and can adjust a supplement.

## Consequences

- ADR 0006 is partly replaced: offers may carry a price, but only as an indication.
- A partner, offer or extra that leaves the export is made inactive, not deleted (plans may
  point to it). The export owns `active` of imported offers and extras.
- The import is idempotent (ids are uuid5 of the DÉTOUR ids), runs in one transaction, opens
  the file read-only, prints counts only, and its errors name DÉTOUR ids, never a name or
  an email. The export itself is never committed (`*.sqlite`, `livraison/` in `.gitignore`).
- The privacy page (#45) must list published reviews (ARCHITECTURE §9).
- Tests: `tests/test_catalog_detour_mapping.py`, `tests/test_catalog_detour_sql.py`, on a
  made-up export (`tests/detour_fixture.py`).
