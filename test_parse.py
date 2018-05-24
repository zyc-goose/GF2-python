"""Test the parse module."""
import pytest

from names import Names
from scanner import Scanner
from parse import Parser
from devices import Devices
from network import Network
from monitors import Monitors

import os
from collections import namedtuple


class ParserTestCase:
    """Receive an input file (as strings), run the parser and check the output."""

    def __init__(self):
        self.testfile_name = 'testfile.txt'
        self.testfile = ''
        self.input_lines = []
        self.expected_output = []
        self.actual_output = []
        self.parser = None
        self.ErrorTuple = namedtuple('ErrorTuple', 'error, linum, pos')

    def add_input_line(self, line):
        """Add a line to the testfile."""
        if not isinstance(line, str):
            raise TypeError("the line to be added should be a str")
        self.input_lines.append(line)

    def add_expected_error(self, error_name, line_number, cursor_pos):
        """Add an expected error tuple to the output list."""
        error_tuple = self.ErrorTuple(error_name, line_number, cursor_pos)
        self.expected_output.append(error_tuple)

    def make_testfile(self):
        """Write the input lines into the testfile."""
        self.testfile = '\n'.join(self.input_lines)
        with open(self.testfile_name, 'w') as fout:
            fout.write(self.testfile)
        self.input_lines = []

    def make_parser(self):
        """Initialise a parser for the testcase."""
        if self.parser is not None:
            return None
        names = Names()
        scanner = Scanner(self.testfile_name, names)
        devices = Devices(names)
        network = Network(names, devices)
        monitors = Monitors(names, devices, network)
        self.parser = Parser(names, devices, network, monitors, scanner, test_mode=True)

    def execute(self):
        """Run parser to produce the output."""
        self.make_testfile()
        self.make_parser()
        self.parser.parse_network()
        self.actual_output = self.parser.error_tuple_list
        os.remove(self.testfile_name)

    def passed(self):
        """Check whether the testcase passes."""
        if self.actual_output == self.expected_output:
            return True
        print("\nInput file:")
        print(self.testfile + '\n')
        print("actual:", self.actual_output)
        print("expect:", self.expected_output)
        return False


def test_example():
    """Example test"""
    testcase = ParserTestCase()
    testcase.add_input_line('(DEVICE D1 D2 are)')
    testcase.add_expected_error(error_name='DEVICE_TYPE_ABSENT', line_number=1, cursor_pos=18)
    testcase.execute()
    assert testcase.passed()

def test_bad_character():
    testcase = ParserTestCase()
    testcase.add_input_line('(DEVICE A B are XOR)')
    testcase.add_input_line('(DEVICE C D ?)')
    testcase.add_expected_error(error_name='BAD_CHARACTER', line_number=2, cursor_pos=13)
    testcase.execute()
    assert testcase.passed()
