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


def test_error_example():
    """Example test"""
    testcase = ParserTestCase()
    testcase.add_input_line('(DEVICE D1 D2 are)')
    testcase.add_expected_error(error_name='DEVICE_TYPE_ABSENT', line_number=1, cursor_pos=18)
    testcase.execute()
    assert testcase.passed()

def test_error_bad_character():
    """BAD_CHARACTER"""
    testcase = ParserTestCase()
    testcase.add_input_line('(DEVICE A B are XOR)')
    testcase.add_input_line('(DEVICE C D ?)')
    testcase.add_expected_error(error_name='BAD_CHARACTER', line_number=2, cursor_pos=13)
    testcase.execute()
    assert testcase.passed()


# Function-wise Tests
@pytest.fixture(scope="session")
def new_parser():
    path = 'test_def.txt'
    names = Names()
    scanner = Scanner(path, names)
    devices = Devices(names)
    network = Network(names, devices)
    monitors = Monitors(names, devices, network)
    new_parser = Parser(names, devices, network, monitors, scanner)
    return new_parser

@pytest.fixture
def move_to_next_symbol(new_parser):
    new_parser.move_to_next_symbol()
    return new_parser

def test_is_left_paren(move_to_next_symbol):
    assert move_to_next_symbol.is_left_paren()

def test_is_right_paren(move_to_next_symbol):
    assert move_to_next_symbol.is_right_paren()

def test_is_dot(move_to_next_symbol):
    assert move_to_next_symbol.is_dot()

def test_is_keyword(move_to_next_symbol):
    assert move_to_next_symbol.is_keyword()

def test_is_name(move_to_next_symbol):
    assert move_to_next_symbol.is_name()

def test_is_number(move_to_next_symbol):
    assert move_to_next_symbol.is_number()

def test_is_target_name(move_to_next_symbol):
    assert move_to_next_symbol.is_target_name('target')

def test_get_name_string(move_to_next_symbol):
    assert move_to_next_symbol.get_name_string() == 'wtf'

def test_statement_error(move_to_next_symbol):
    move_to_next_symbol.statement()
    error_code_1 = move_to_next_symbol.error_code
    move_to_next_symbol.error_code = move_to_next_symbol.NO_ERROR
    move_to_next_symbol.move_to_next_symbol()

    move_to_next_symbol.statement()
    error_code_2 = move_to_next_symbol.error_code
    move_to_next_symbol.error_code = move_to_next_symbol.NO_ERROR
    move_to_next_symbol.move_to_next_symbol()

    move_to_next_symbol.statement()
    error_code_3 = move_to_next_symbol.error_code
    move_to_next_symbol.error_code = move_to_next_symbol.NO_ERROR
    move_to_next_symbol.move_to_next_symbol()

    move_to_next_symbol.statement()
    error_code_4 = move_to_next_symbol.error_code
    move_to_next_symbol.error_code = move_to_next_symbol.NO_ERROR
    assert error_code_1 == move_to_next_symbol.EXPECT_LEFT_PAREN
    assert error_code_2 == move_to_next_symbol.EMPTY_STATEMENT
    assert error_code_3 == move_to_next_symbol.INVALID_FUNCTION_NAME
    assert error_code_4 == move_to_next_symbol.EXPECT_RIGHT_PAREN

def test_statement(new_parser):
    assert new_parser.statement()

def test_device_error(new_parser):
    assert not new_parser.device()
    error_code_1 = new_parser.error_code
    assert error_code_1 == new_parser.NO_ERROR
    new_parser.move_to_next_symbol()

    assert not new_parser.device()
    new_parser.error_code = new_parser.NO_ERROR
    new_parser.move_to_next_symbol()

    assert not new_parser.device()
    new_parser.error_code = new_parser.NO_ERROR
    new_parser.move_to_next_symbol()

    assert not new_parser.device()
    new_parser.error_code = new_parser.NO_ERROR
    new_parser.move_to_next_symbol()

    assert not new_parser.device()
    new_parser.error_code = new_parser.NO_ERROR
    new_parser.move_to_next_symbol()

    assert not new_parser.device()
    error_code_2 = new_parser.error_code
    assert error_code_2 == new_parser.INVALID_QUALIFIER
    new_parser.error_code = new_parser.NO_ERROR

def test_device(move_to_next_symbol):
    assert move_to_next_symbol.device()

def test_get_first_device_id_error(new_parser):
    assert new_parser.get_first_device_id(set()) is None
    assert new_parser.error_code == new_parser.EMPTY_DEVICE_LIST
    new_parser.move_to_next_symbol()

    assert new_parser.get_first_device_id(set()) is None
    assert new_parser.error_code == new_parser.KEYWORD_AS_DEVICE_NAME
    new_parser.move_to_next_symbol()

    assert new_parser.get_first_device_id(set()) is None
    assert new_parser.error_code == new_parser.EMPTY_DEVICE_LIST
    new_parser.move_to_next_symbol()

    assert new_parser.get_first_device_id(set()) is None
    assert new_parser.error_code == new_parser.INVALID_DEVICE_NAME
    new_parser.move_to_next_symbol()

    new_parser.get_first_device_id(set())
    assert new_parser.error_code == new_parser.DEVICE_REDEFINED
    new_parser.move_to_next_symbol()

def test_get_first_device_id(new_parser):
    assert new_parser.get_first_device_id(set()) is not None

def test_get_optional_device_id_error(new_parser):
    assert new_parser.get_optional_device_id(set()) is None
    assert new_parser.error_code == new_parser.DEVICE_REDEFINED
    new_parser.move_to_next_symbol()

def test_get_optional_device_id(new_parser):
    assert new_parser.get_optional_device_id(set()) is not None

def test_
