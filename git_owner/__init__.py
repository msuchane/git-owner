from collections import Counter
import subprocess
import sys


def log_contributors(file: str) -> list[str]:
    log = subprocess.run(["git", "log", "--follow", "--format=%ae", file], stdout=subprocess.PIPE)
    contributors = log.stdout.decode().splitlines()

    return contributors


def blame_contributors(file: str) -> list[str]:
    blame_contributors = []

    blame = subprocess.run(["git", "blame", "--line-porcelain", file], stdout=subprocess.PIPE)
    blame_text = blame.stdout.decode().splitlines()

    for index, line in enumerate(blame_text):
        if index % 13 == 2:
            assert line.startswith("author-mail")
            author = line[13:-1]
            blame_contributors.append(author)

    return blame_contributors


def contributor_shares(authors: list[str]) -> dict[str, float]:
    counter = Counter(authors)
    total = counter.total()

    shares = {}

    for author, count in counter.most_common():
        fraction = count / total
        shares[author] = fraction

    return shares


def combine_shares(log: dict[str, float], blame: dict[str, float]) -> dict[str, float]:
    combined_shares = {}

    for author, fraction in log.items():
        combined_shares[author] = fraction / 2

    for author, fraction in blame.items():
        existing_value = combined_shares.get(author, 0)
        combined = existing_value + (fraction / 2)
        combined_shares[author] = combined

    return combined_shares


if __name__ == "__main__":
    file = sys.argv[1]

    from_log = log_contributors(file)
    log_shares = contributor_shares(from_log)

    from_blame = blame_contributors(file)
    blame_shares = contributor_shares(from_blame)

    print("log:", log_shares)
    print("blame:", blame_shares)

    combined_shares = combine_shares(log_shares, blame_shares)

    shares_items = list(combined_shares.items())
    sorted_shares = sorted(shares_items, key=lambda item: item[1], reverse=True)

    for (index, (author, fraction)) in enumerate(sorted_shares):
        rank = index + 1
        percentage = fraction * 100
        print("#{:>2}  {}  ({:.1%})".format(rank, author, fraction))
