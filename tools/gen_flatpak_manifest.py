#!/usr/bin/env python3

import argparse
import os
import re
import subprocess

TEMPLATE = "flatpak/io.github.wivrn.wivrn.yml.in"


class CMakeFile:
    def __init__(self, filename: str):
        self.entries = {}
        with open(filename) as f:
            data = f.read()
        for match in re.findall("FetchContent_Declare\\(([^)]*)\\)", data):
            words = [word for word
                     in match.replace("\n", " ").split(" ")
                     if word]
            self.entries[words[0]] = words[1:]

    def get(self, target: str, key: str) -> str:
        entry = self.entries[target]
        index = entry.index(key)
        return entry[index + 1]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--git")
    parser.add_argument("--gitlocal", action="store_true")
    parser.add_argument("--dir", action="store_true")

    args = parser.parse_args()
    if not (args.git or args.dir):
        args.gitlocal = True

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    cmake = CMakeFile(os.path.join(root, "CMakeLists.txt"))
    with open(os.path.join(root, TEMPLATE)) as f:
        template = f.read()

    monado_commit = cmake.get("monado", "GIT_TAG")
    boostpfr_url = cmake.get("boostpfr", "URL")
    boostpfr_sha256 = cmake.get("boostpfr", "URL_HASH").split("=")[-1]

    try:
        git_commit = subprocess.check_output(
                ["git", "describe", "--exact-match", "--tags"],
                cwd=root,
                stderr=subprocess.DEVNULL
                ).decode().strip()
    except subprocess.CalledProcessError:
        git_commit = subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=root
                ).decode().strip()
    git_desc = subprocess.check_output(
                ["git", "describe", "--tags", "--always"],
                cwd=root
                ).decode().strip()

    if args.git or args.gitlocal:
        template = template.replace("WIVRN_SRC1", "type: git")
        if args.git:
            template = template.replace("WIVRN_SRC2", f"url: {args.git}")
        else:
            template = template.replace("WIVRN_SRC2", f"url: {root}")
        template = template.replace("WIVRN_SRC3", f"tag: {git_commit}")
    else:
        template = template.replace("WIVRN_SRC1", "type: dir")
        template = template.replace("WIVRN_SRC2", f"path: {root}")
        template = template.replace("WIVRN_SRC3", "")

    template = template.replace("WIVRN_GIT_DESC", git_desc)
    template = template.replace("WIVRN_GIT_COMMIT", git_commit)

    template = template.replace("BOOSTPFR_URL", boostpfr_url)
    template = template.replace("BOOSTPFR_SHA256", boostpfr_sha256)
    template = template.replace("MONADO_COMMIT", monado_commit)

    print(template)
