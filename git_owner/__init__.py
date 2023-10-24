#!/usr/bin/env python3

import argparse
from collections import Counter
import logging
import re
import subprocess
from typing import Optional


def cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog='git-owner',
        description='Estimate who the approximate owner of a file is in a Git repository.')

    parser.add_argument(
        'files',
        nargs='+',
        help='One or more files in the current Git repository.')
    parser.add_argument(
        '-m',
        '--most-likely',
        action='store_true',
        help='Show only the most likely owner without additional statistics.')
    parser.add_argument(
        '-n',
        '--names',
        action='store_true',
        help='Identify users by name rather than by email.')
    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help='Show debugging messages.')

    ex_group = parser.add_mutually_exclusive_group()

    ex_group.add_argument(
        '-l',
        '--only-log',
        action='store_true',
        help='Estimate only from Git log.')
    ex_group.add_argument(
        '-b',
        '--only-blame',
        action='store_true',
        help='Estimate only from Git blame.')

    args = parser.parse_args()

    return args


def log_contributors(file: str, names: bool) -> list[str]:
    if names:
        user_format = r"%an"
    else:
        user_format = r"%ae"

    log = subprocess.run(["git", "log", "--follow", f"--format={user_format}", file], stdout=subprocess.PIPE)
    contributors = log.stdout.decode().splitlines()

    return contributors


def blame_contributors(file: str, names: bool) -> list[str]:
    blame_contributors = []

    blame = subprocess.run(["git", "blame", "--line-porcelain", file], stdout=subprocess.PIPE)
    blame_text = blame.stdout.decode().splitlines()

    if names:
        author_regex = re.compile("^author (.+)$")
    else:
        author_regex = re.compile("^author-mail <(.+)>$")

    for index, line in enumerate(blame_text):
        re_match = re.search(author_regex, line)

        if re_match is not None:
            captured = re_match.group(1)
            blame_contributors.append(captured)

    return blame_contributors


Shares = dict[str, float]


def contributor_shares(authors: list[str]) -> Shares:
    counter = Counter(authors)
    total = counter.total()

    shares = {}

    for author, count in counter.most_common():
        fraction = count / total
        shares[author] = fraction

    return shares


def combine_shares(log: Shares, blame: Shares) -> Shares:
    combined_shares = {}

    for author, fraction in log.items():
        combined_shares[author] = fraction / 2

    for author, fraction in blame.items():
        existing_value = combined_shares.get(author, 0)
        combined = existing_value + (fraction / 2)
        combined_shares[author] = combined

    return combined_shares


SortedShares = list[tuple[str, float]]


def sort_shares(shares: Shares) -> SortedShares:
    shares_items = list(shares.items())
    sorted_shares = sorted(shares_items, key=lambda item: item[1], reverse=True)

    return sorted_shares


def likely_owner(shares: SortedShares) -> str:
    most_contributions = shares[0]
    author = most_contributions[0]

    return author


def estimate_file(file: str, args: argparse.Namespace) -> SortedShares:
    if args.only_log:
        from_log = log_contributors(file, args.names)
        log_shares = contributor_shares(from_log)
        logging.debug(f"Contributors:\n{log_shares}")
        sorted_shares = sort_shares(log_shares)
    elif args.only_blame:
        from_blame = blame_contributors(file, args.names)
        blame_shares = contributor_shares(from_blame)
        logging.debug(f"Contributors:\n{blame_shares}")
        sorted_shares = sort_shares(blame_shares)
    else:
        from_log = log_contributors(file, args.names)
        log_shares = contributor_shares(from_log)
        logging.debug(f"Contributors in log:\n{log_shares}")

        from_blame = blame_contributors(file, args.names)
        blame_shares = contributor_shares(from_blame)
        logging.debug(f"Contributors in blame:\n{blame_shares}")

        combined_shares = combine_shares(log_shares, blame_shares)
        sorted_shares = sort_shares(combined_shares)

    return sorted_shares


def report_shares(shares: SortedShares, header: Optional[str]) -> None:
    if header:
        print(f"-- {header} --")
    for (index, (author, fraction)) in enumerate(shares):
        rank = index + 1
        print("#{:>2}  {}  ({:.1%})".format(rank, author, fraction))


def print_report(shares: SortedShares, file: str, args: argparse.Namespace) -> None:
    if args.most_likely:
        print(likely_owner(shares))
    else:
        if len(args.files) > 1:
            header = file
        else:
            header = None
        report_shares(shares, header)


if __name__ == "__main__":
    args = cli()

    # Configure the level of logging output
    if args.verbose:
        log_level=logging.DEBUG
    else:
        log_level=logging.WARNING
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')

    for file in args.files:
        shares = estimate_file(file, args)
        print_report(shares, file, args)
