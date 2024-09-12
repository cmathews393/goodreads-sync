import os
import re

# Define a list of common stop words to exclude from matching

STOP_WORDS = {
    "the",
    "and",
    "of",
    "a",
    "an",
    "in",
    "on",
    "for",
    "with",
    "to",
    "from",
    "by",
    "at",
    "as",
    "is",
    "it",
    "this",
    "that",
    "be",
    "are",
    "was",
    "were",
    "but",
    "or",
    "if",
    "then",
    "else",
    "when",
    "where",
    "which",
    "how",
    "what",
    "why",
    "who",
    "whom",
}

# Add all single letters, a-z, to the STOP_WORDS set
STOP_WORDS.update({chr(i) for i in range(ord("a"), ord("z") + 1)})


def get_epub_files(directory):
    """Recursively gather all .epub files from a directory."""
    epub_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".epub"):
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, directory)
                epub_files.append(relative_path)
    return epub_files


def clean_filename(filename):
    """Cleans the filename by replacing slashes with spaces, removing the extension, punctuation, stop words, and converting to lowercase."""
    filename = os.path.splitext(filename)[0]  # Remove file extension
    filename = filename.replace("/", " ")  # Replace slashes with spaces
    words = (
        re.sub(r"[^\w\s]", "", filename).lower().split()
    )  # Remove punctuation, lower case, split into words
    # Exclude stop words
    return [word for word in words if word not in STOP_WORDS]


def have_common_words(epub1, epub2, threshold=4):
    """Check if two filenames have a certain number of common words."""
    words1 = set(clean_filename(epub1))
    words2 = set(clean_filename(epub2))
    common_words = words1.intersection(words2)
    return len(common_words) >= threshold, common_words


def find_and_display_matches(ebooks_dir, ebookimport_dir):
    """Find .epub files in both directories and display matches and potential deletions."""
    # Get all .epub files from both directories
    ebooks_epubs = get_epub_files(ebooks_dir)
    ebookimport_epubs = get_epub_files(ebookimport_dir)
    ebookimport_epubs_set = set(ebookimport_epubs)  # For faster lookup
    dry_run = None
    duplicates = set()  # To store unique duplicates from ebookimport_dir

    # Iterate over the list of files and check for duplicates with common words
    for epub in ebooks_epubs:
        for import_epub in ebookimport_epubs_set:
            match, common_words = have_common_words(epub, import_epub)
            if match:
                duplicates.add(import_epub)  # Add to set to ensure uniqueness
                # Display the matching files and the common words
                print(
                    f"Match found: {os.path.join(ebooks_dir, epub)} <-> {os.path.join(ebookimport_dir, import_epub)}",
                )
                print(f"Common words: {common_words}")
                if dry_run:
                    print(f"Would delete: {os.path.join(ebookimport_dir, import_epub)}")

    n = len(duplicates)
    print(f"\nTotal unique duplicates found: {n}")

    if not dry_run:
        # If not in dry run mode, delete the duplicates
        for dup in duplicates:
            dup_path = os.path.join(ebookimport_dir, dup)
            try:
                os.remove(dup_path)
                print(f"Deleted: {dup_path}")
            except Exception as e:
                print(f"Error deleting {dup_path}: {e}")


if __name__ == "__main__":
    # Directories to compare
    ebooks_dir = "/audiobookshelf/ebooks"
    ebookimport_dir = "/audiobookshelf/ebookimport"

    # Set dry_run=False to perform actual deletion, dry_run=True to only show matches
    find_and_display_matches(ebooks_dir, ebookimport_dir, dry_run=True)
