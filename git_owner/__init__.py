#!/usr/bin/env python3

import argparse
from collections import Counter
import logging
import re
import subprocess
import sys
from threading import Thread
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
        '-p',
        '--placeholder',
        metavar="OWNER",
        help='If Git fails to analyze the given file, show this placeholder as owner.')
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


def log_contributors(file: str, names: bool, output: dict) -> None:
    if names:
        user_format = r"%an"
    else:
        user_format = r"%ae"

    try:
        log = subprocess.run(["git", "log", "--follow", f"--format={user_format}", file],
            capture_output=True,
            check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"The git log command failed:\n{e.stderr.decode()}")
        return

    contributors = log.stdout.decode().splitlines()

    output["log"] = contributors


def blame_contributors(file: str, names: bool, output: dict) -> None:
    blame_contributors = []

    try:
        blame = subprocess.run(["git", "blame", "--line-porcelain", file],
        capture_output=True,
        check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"The git blame command failed:\n{e.stderr.decode()}")
        return

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

    output["blame"] = blame_contributors


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


# The mutable object to store thread results
Buffer = dict[str, list[str]]


def estimate_file(file: str, args: argparse.Namespace) -> SortedShares:
    # Prepare a mutable output object for the later threads.
    buffer: Buffer = {}

    if args.only_log:
        log_contributors(file, args.names, buffer)

        try:
            log_shares = contributor_shares(buffer["log"])
        except KeyError:
            sys.exit(1)

        logging.debug(f"Contributors:\n{log_shares}")
        sorted_shares = sort_shares(log_shares)

    elif args.only_blame:
        blame_contributors(file, args.names, buffer)

        try:
            blame_shares = contributor_shares(buffer["blame"])
        except KeyError:
            sys.exit(1)

        logging.debug(f"Contributors:\n{blame_shares}")
        sorted_shares = sort_shares(blame_shares)

    else:
        # The threads store return values in the mutable object.
        t1 = Thread(target=log_contributors, args=[file, args.names, buffer])
        t2 = Thread(target=blame_contributors, args=[file, args.names, buffer])
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        # The threads have finished now.

        # If either of the buffers is empty, the git command failed. Exit.
        try:
            log = buffer["log"]
            blame = buffer["blame"]
        except KeyError:
            sys.exit(1)

        log_shares = contributor_shares(log)
        blame_shares = contributor_shares(blame)

        logging.debug(f"Contributors in log:\n{log_shares}")
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
