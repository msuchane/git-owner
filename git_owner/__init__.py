import sys

from git import Repo

file = sys.argv[1]

repo = Repo(".")

blame = repo.blame(repo.head, file)

print(blame)
