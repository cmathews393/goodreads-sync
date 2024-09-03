from concurrent.futures import ThreadPoolExecutor, as_completed
from time import perf_counter

from goodreads_sync.functions import Audiobookshelf, GoodreadsRSS


def main() -> None:
    goodreads = GoodreadsRSS()

    # Parse the feed and get collection title and new books

    collection_title, books = goodreads.parse_feed()
    abs_instance = Audiobookshelf()
    abs_instance.get_abs_libraries()
    for libid in abs_instance.lib_ids:
        start = perf_counter()
        collection_id = abs_instance.create_audiobookshelf_collection(
            collection_title,
            libid,
        )
        wanted_books = []
        with ThreadPoolExecutor() as executor:
            future_to_book = {
                executor.submit(
                    abs_instance.get_abs_book_id,
                    book["title"],
                    libid,
                ): book
                for book in books
            }

            for future in as_completed(future_to_book):
                abs_id = future.result()
                if abs_id:
                    wanted_books.append(abs_id)

        if wanted_books:
            abs_instance.add_books_to_audiobookshelf_collection(
                collection_id,
                wanted_books,
            )

            stop = perf_counter()
        print("Elapsed time:", stop, start)
        print("Elapsed time during the whole program in seconds:", stop - start)
    print(abs_instance.missing_books)
    print("Operation completed.")


if __name__ == "__main__":
    # Sample usage
    main()
