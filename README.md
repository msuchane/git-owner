# git-owner

Estimate who the approximate owner of a file is in a Git repository. Take into account the Git blame and Git log information.

## Installation

The tool is currently packaged for Fedora, CentOS Stream, and RHEL.

1. Enable the RPM repository:

    ```
    # dnf copr enable mareksu/git-owner 
    ```

2. Install the package:

    ```
    # dnf install git-owner 
    ```

## Usage

* Estimate the ownership of a file in a Git repository:

    ```
    git-repository]$ git-owner file
    ```

* See available options:

    ```
    git-repository]$ git-owner --help
    ```
