import subprocess
import sys

file = sys.argv[1]

def log_contributors(file: str) -> list[str]:
    log = subprocess.run(["git", "log", "--follow", "--format=%ae", file], stdout=subprocess.PIPE)
    contributors = log.stdout.decode().splitlines()

    return contributors

print(log_contributors(file))


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

print(blame_contributors(file))
