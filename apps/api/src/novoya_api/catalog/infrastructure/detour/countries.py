"""The 86 country names of the DÉTOUR export (destinations.pays), in French, with the common
English name Novoya stores. A country missing here stops the import: add it, never guess it."""

COUNTRIES: dict[str, str] = {
    "Afrique du Sud": "South Africa",
    "Albanie": "Albania",
    "Argentine": "Argentina",
    "Arménie": "Armenia",
    "Australie": "Australia",
    "Autriche": "Austria",
    "Belgique": "Belgium",
    "Belize": "Belize",
    "Bolivie": "Bolivia",
    "Bosnie-Herzégovine": "Bosnia and Herzegovina",
    "Botswana": "Botswana",
    "Bulgarie": "Bulgaria",
    "Bénin": "Benin",
    "Cambodge": "Cambodia",
    "Canada": "Canada",
    "Chili": "Chile",
    "Chine": "China",
    "Chypre": "Cyprus",
    "Colombie": "Colombia",
    "Corée du Sud": "South Korea",
    "Costa Rica": "Costa Rica",
    "Croatie": "Croatia",
    "Cuba": "Cuba",
    "Côte d’Ivoire": "Ivory Coast",
    "Danemark": "Denmark",
    "Espagne": "Spain",
    "Estonie": "Estonia",
    "Fidji": "Fiji",
    "Finlande": "Finland",
    "France": "France",
    "Ghana": "Ghana",
    "Grèce": "Greece",
    "Guatemala": "Guatemala",
    "Géorgie": "Georgia",
    "Inde": "India",
    "Indonésie": "Indonesia",
    "Islande": "Iceland",
    "Italie": "Italy",
    "Japon": "Japan",
    "Kenya": "Kenya",
    "Laos": "Laos",
    "Lettonie": "Latvia",
    "Liban": "Lebanon",
    "Lituanie": "Lithuania",
    "Luxembourg": "Luxembourg",
    "Macédoine du Nord": "North Macedonia",
    "Madagascar": "Madagascar",
    "Malaisie": "Malaysia",
    "Malte": "Malta",
    "Maroc": "Morocco",
    "Maurice": "Mauritius",
    "Mexique": "Mexico",
    "Mongolie": "Mongolia",
    "Namibie": "Namibia",
    "Nicaragua": "Nicaragua",
    "Norvège": "Norway",
    "Nouvelle-Zélande": "New Zealand",
    "Népal": "Nepal",
    "Oman": "Oman",
    "Ouganda": "Uganda",
    "Ouzbékistan": "Uzbekistan",
    "Panama": "Panama",
    "Pays-Bas": "Netherlands",
    "Portugal": "Portugal",
    "Pérou": "Peru",
    "Roumanie": "Romania",
    "Royaume-Uni": "United Kingdom",
    "Rwanda": "Rwanda",
    "Samoa": "Samoa",
    "Serbie": "Serbia",
    "Slovénie": "Slovenia",
    "Sri Lanka": "Sri Lanka",
    "Suisse": "Switzerland",
    "Suède": "Sweden",
    "Sénégal": "Senegal",
    "Tanzanie": "Tanzania",
    "Taïwan": "Taiwan",
    "Thaïlande": "Thailand",
    "Togo": "Togo",
    "Tunisie": "Tunisia",
    "Vietnam": "Vietnam",
    "Zambie": "Zambia",
    "Égypte": "Egypt",
    "Équateur": "Ecuador",
    "États-Unis": "United States",
    "Éthiopie": "Ethiopia",
}


def country_key(name: str) -> str:
    """One spelling for lookups: spaces collapsed, case and apostrophe style ignored."""
    return " ".join(name.replace("’", "'").split()).casefold()


_ENGLISH = {country_key(french): english for french, english in COUNTRIES.items()}
_CANONICAL = {
    **{country_key(english): english for english in COUNTRIES.values()},
    **_ENGLISH,
}


def english_country(french: str) -> str | None:
    """The English name of a DÉTOUR country, or None when it is not in the map."""
    return _ENGLISH.get(country_key(french))


def canonical_country(name: str) -> str | None:
    """The English name of a country written in French or in English, or None."""
    return _CANONICAL.get(country_key(name))
