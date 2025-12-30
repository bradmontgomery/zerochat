#! /usr/bin/env python
"""
A non-blocking stdin reader.
Inspired by: http://goo.gl/Ts9fJ

"""
from __future__ import annotations

from select import select
from sys import stdin, stdout
from typing import TextIO


class NonblockingStdinReader:
    def __init__(self, *, timeout: float = 0.1) -> None:
        self.stdin: TextIO = stdin
        self.timeout: float = timeout  # seconds
        self.input_value: str = ""

    def print_input(self) -> None:
        """Print the input value (if it exists) to stdout & reset it to an
        empty string."""
        if self.input_value:
            stdout.write(f"{self.input_value}\n")
            self.input_value = ""

    def get_input(self) -> str:
        """Return the input value (if it exists) & reset it to an empty
        string."""
        s = self.input_value
        if s:
            self.input_value = ""
        return s

    def _read_file_list(self, file_list: list[TextIO]) -> None:
        if file_list:
            for f in file_list:
                line = f.readline()
                if line:
                    self.input_value += line
                else:  # No more content
                    file_list.remove(f)

    def read(self) -> None:
        read_list = select([self.stdin], [], [], self.timeout)[0]
        self._read_file_list(read_list)


if __name__ == "__main__":

    # Sample program to illustrate this reader; It prints random string data,
    # while letting you enter text on stdin.

    import random
    from string import ascii_letters

    r = NonblockingStdinReader()
    while True:
        # periodically print junk
        if random.randint(0, 10) == 0:
            junk = "".join([random.choice(ascii_letters) for x in range(20)])
            stdout.write(junk + "\n")
        r.read()
        r.print_input()
        stdout.flush()  # flush so this'll go ahead and write output
