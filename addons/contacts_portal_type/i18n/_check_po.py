#!/usr/bin/env python3
path = "tr.po"
with open(path, encoding="utf-8") as f:
    for i, line in enumerate(f, 1):
        s = line.rstrip("\n")
        if not s.strip():
            continue
        if s.startswith("#"):
            continue
        if s.startswith("msgid "):
            continue
        if s.startswith("msgstr "):
            continue
        if s.startswith('"'):
            continue
        print("Unexpected line", i, repr(s[:120]))
