from goodreads_sync.config import Config
from goodreads_sync.functions import GoodreadsRSS


def main():
    goodreads = GoodreadsRSS()

    print(goodreads.parse_feed(Config.goodreads_rss))


if __name__ == "__main__":
    main()
