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


def contributor_shares(authors: list[str]) -> dict:
    counter = Counter(authors)
    total = counter.total()

    shares = {}

    for author, count in counter.most_common():
        fraction = count / total
        shares[author] = fraction

    return shares


if __name__ == "__main__":
    file = sys.argv[1]

    from_log = log_contributors(file)
    log_shares = contributor_shares(from_log)

    from_blame = blame_contributors(file)
    blame_shares = contributor_shares(from_blame)

    print("log:", log_shares)
    print("blame:", blame_shares)
