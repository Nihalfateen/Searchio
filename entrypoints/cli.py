import argparse

from sapien.core.limit_memory import start_memory_monitor
from sapien.core.logging import setup_logging

setup_logging()
start_memory_monitor(show_memory_updates=True)


def main():
    # TODO continue here
    parser = argparse.ArgumentParser(description="Sapien Indexer CLI")
    parser.add_argument("file_path", type=str, help="Path to the file to index")

    _ = parser.parse_args()


if __name__ == "__main__":
    main()
