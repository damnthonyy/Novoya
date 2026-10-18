import asyncio

from novoya_api.catalog.infrastructure.seed.run import seed_catalog


def main() -> None:
    asyncio.run(seed_catalog())


if __name__ == "__main__":
    main()
