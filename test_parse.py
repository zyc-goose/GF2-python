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

###### ERROR CODE TESTS ######
class ParserTestCase:
    """Receive an input file (as strings), run the parser and check the error code."""

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
        print("actual: [", end='')
        print(("\n" + " "*9).join(map(str, self.actual_output)), end=']\n')
        print("expect: [", end='')
        print(("\n" + " "*9).join(map(str, self.expected_output)), end=']\n')
        return False


def test_error_bad_character():
    """BAD_CHARACTER"""
    testcase = ParserTestCase()
    testcase.add_input_line('(DEVICE A B are XOR)')
    testcase.add_input_line('(DEVICE C D ?)')
    testcase.add_expected_error('BAD_CHARACTER', line_number=2, cursor_pos=13)
    testcase.execute()
    assert testcase.passed()

def test_error_bad_comment():
    """BAD_COMMENT"""
    testcase = ParserTestCase()
    testcase.add_input_line('/* foo bar pig dog')
    testcase.add_expected_error('BAD_COMMENT', line_number=1, cursor_pos=18)
    testcase.execute()
    assert testcase.passed()

def test_error_bad_number():
    """BAD_NUMBER"""
    testcase = ParserTestCase()
    testcase.add_input_line('(DEVICE A B are NAND 007)')
    testcase.add_expected_error('BAD_NUMBER', line_number=1, cursor_pos=24)
    testcase.execute()
    assert testcase.passed()

def test_error_device_redefined():
    """DEVICE_REDEFINED"""
    testcase = ParserTestCase()
    testcase.add_input_line('(DEVICE A B are NAND 2)')
    testcase.add_input_line('(DEVICE A ??!!@@##')
    testcase.add_expected_error('DEVICE_REDEFINED', line_number=2, cursor_pos=9)
    testcase.execute()
    assert testcase.passed()

def test_error_device_type_absent():
    """DEVICE_TYPE_ABSENT"""
    testcase = ParserTestCase()
    testcase.add_input_line('(DEVICE A1 A2 are  ')
    testcase.add_input_line('')
    testcase.add_input_line('   )')
    testcase.add_expected_error('DEVICE_TYPE_ABSENT', line_number=1, cursor_pos=17)
    testcase.execute()
    assert testcase.passed()

def test_error_device_undefined():
    """DEVICE_UNDEFINED"""
    testcase = ParserTestCase()
    testcase.add_input_line('(DEVICE A1 A2 are OR 3)')
    testcase.add_input_line('(MONITOR A3 )')
    testcase.add_expected_error('DEVICE_UNDEFINED', line_number=2, cursor_pos=11)
    testcase.execute()
    assert testcase.passed()

def test_error_empty_device_list():
    """EMPTY_DEVICE_LIST"""
    testcase = ParserTestCase()
    testcase.add_input_line('(DEVICE   are DTYPE)')
    testcase.add_input_line('(DEVICE  )')
    testcase.add_expected_error('EMPTY_DEVICE_LIST', line_number=1, cursor_pos=13)
    testcase.add_expected_error('EMPTY_DEVICE_LIST', line_number=2, cursor_pos=10)
    testcase.execute()
    assert testcase.passed()

def test_error_empty_file():
    """EMPTY_FILE"""
    testcase = ParserTestCase()
    testcase.add_input_line('// csbg csbg snb cnm wqnmlgb zao yu feng')
    testcase.add_input_line('/* Lorem Ipsum Cappucino Latte')
    testcase.add_input_line('bagels cereal chocolate pig elephant')
    testcase.add_input_line('zheye jidangwei */')
    testcase.add_expected_error('EMPTY_FILE', line_number=4, cursor_pos=18)
    testcase.execute()
    assert testcase.passed()

def test_error_empty_monitor_list():
    """EMPTY_MONITOR_LIST"""
    testcase = ParserTestCase()
    testcase.add_input_line('(DEVICE A is NAND 1)')
    testcase.add_input_line('(MONITOR          )')
    testcase.add_expected_error('EMPTY_MONITOR_LIST', line_number=2, cursor_pos=19)
    testcase.execute()
    assert testcase.passed()

def test_error_empty_statement():
    """EMPTY_STATEMENT"""
    testcase = ParserTestCase()
    testcase.add_input_line('(DEVICE dog cat bulldog are DTYPE)')
    testcase.add_input_line('()')
    testcase.add_expected_error('EMPTY_STATEMENT', line_number=2, cursor_pos=2)
    testcase.execute()
    assert testcase.passed()

def test_error_expect_device_terminal_name():
    """EXPECT_DEVICE_TERMINAL_NAME"""
    testcase = ParserTestCase()
    testcase.add_input_line('(CONNECT to B foo bar)')
    testcase.add_input_line('(CONNECT)')
    testcase.add_input_line('(DEVICE A is DTYPE)')
    testcase.add_input_line('(CONNECT A.DATA to )')
    testcase.add_expected_error('EXPECT_DEVICE_TERMINAL_NAME', line_number=1, cursor_pos=11)
    testcase.add_expected_error('EXPECT_DEVICE_TERMINAL_NAME', line_number=2, cursor_pos=9)
    testcase.add_expected_error('EXPECT_DEVICE_TERMINAL_NAME', line_number=4, cursor_pos=20)
    testcase.execute()
    assert testcase.passed()

def test_error_expect_keyword_is_are():
    """EXPECT_KEYWORD_IS_ARE"""
    testcase = ParserTestCase()
    testcase.add_input_line('(DEVICE A B C)')
    testcase.add_input_line('(DEVICE D E F CLOCK)')
    testcase.add_expected_error('EXPECT_KEYWORD_IS_ARE', line_number=1, cursor_pos=14)
    testcase.add_expected_error('EXPECT_KEYWORD_IS_ARE', line_number=2, cursor_pos=19)
    testcase.execute()
    assert testcase.passed()

def test_error_expect_keyword_to():
    """EXPECT_KEYWORD_TO"""
    testcase = ParserTestCase()
    testcase.add_input_line('(DEVICE A is XOR)')
    testcase.add_input_line('(CONNECT A)')
    testcase.add_input_line('(CONNECT A dog)')
    testcase.add_expected_error('EXPECT_KEYWORD_TO', line_number=2, cursor_pos=11)
    testcase.add_expected_error('EXPECT_KEYWORD_TO', line_number=3, cursor_pos=14)
    testcase.execute()
    assert testcase.passed()

def test_error_expect_left_paren():
    """EXPECT_LEFT_PAREN"""
    testcase = ParserTestCase()
    testcase.add_input_line('(DEVICE A is XOR)')
    testcase.add_input_line('  cat (DEVICE B is NOR 16)')
    testcase.add_expected_error('EXPECT_LEFT_PAREN', line_number=2, cursor_pos=5)
    testcase.execute()
    assert testcase.passed()

def test_error_expect_left_paren():
    """EXPECT_NO_QUALIFIER"""
    testcase = ParserTestCase()
    testcase.add_input_line('(DEVICE A is XOR 0)')
    testcase.add_input_line('(DEVICE B is DTYPE 3154)')
    testcase.add_expected_error('EXPECT_NO_QUALIFIER', line_number=1, cursor_pos=18)
    testcase.add_expected_error('EXPECT_NO_QUALIFIER', line_number=2, cursor_pos=23)
    testcase.execute()
    assert testcase.passed()

def test_error_expect_port_name():
    """EXPECT_PORT_NAME"""
    testcase = ParserTestCase()
    testcase.add_input_line('(DEVICE A B is NAND 2)')
    testcase.add_input_line('(CONNECT A. to )')
    testcase.add_input_line('(CONNECT A to B.)')
    testcase.add_expected_error('EXPECT_PORT_NAME', line_number=2, cursor_pos=11)
    testcase.add_expected_error('EXPECT_PORT_NAME', line_number=3, cursor_pos=16)
    testcase.execute()
    assert testcase.passed()


###### FUNCTION TESTS ######
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

def test_check_keyword_is_are_error(new_parser):
    assert not new_parser.check_keyword_is_are()
    assert new_parser.error_code == new_parser.EXPECT_KEYWORD_IS_ARE
    new_parser.move_to_next_symbol()

    assert not new_parser.check_keyword_is_are()
    assert new_parser.error_code == new_parser.INVALID_DEVICE_NAME
    new_parser.move_to_next_symbol()

    assert not new_parser.check_keyword_is_are()
    assert new_parser.error_code == new_parser.EXPECT_KEYWORD_IS_ARE
    new_parser.move_to_next_symbol()

    assert not new_parser.check_keyword_is_are()
    assert new_parser.error_code == new_parser.EXPECT_KEYWORD_IS_ARE
    new_parser.move_to_next_symbol()

    assert not new_parser.check_keyword_is_are()
    assert new_parser.error_code == new_parser.KEYWORD_AS_DEVICE_NAME
    new_parser.move_to_next_symbol()

def test_check_keyword_is_are(new_parser):
    assert new_parser.check_keyword_is_are()
    new_parser.move_to_next_symbol()

def test_get_device_type_error(new_parser):
    assert new_parser.get_device_type() == (None, None)
    assert new_parser.error_code == new_parser.DEVICE_TYPE_ABSENT
    new_parser.move_to_next_symbol()

    assert new_parser.get_device_type() == (None, None)
    assert new_parser.error_code == new_parser.INVALID_DEVICE_TYPE
    new_parser.move_to_next_symbol()

    assert new_parser.get_device_type() == (None, None)
    assert new_parser.error_code == new_parser.EXPECT_QUALIFIER

    assert new_parser.get_device_type() == (None, None)
    assert new_parser.error_code == new_parser.EXPECT_NO_QUALIFIER
    new_parser.move_to_next_symbol()

    assert new_parser.get_device_type() == (None, None)
    assert new_parser.error_code == new_parser.INVALID_DEVICE_TYPE
    new_parser.move_to_next_symbol()

def test_get_device_type(new_parser):
    assert new_parser.get_device_type() == (new_parser.devices.CLOCK, 10)
    assert new_parser.get_device_type() == (new_parser.devices.XOR, None)
    new_parser.move_to_next_symbol()

def test_device_terminal_error(new_parser):
    assert new_parser.device_terminal() == (None, None)
    new_parser.move_to_next_symbol()
    assert new_parser.device_terminal() == (None, None)
    assert new_parser.error_code == new_parser.DEVICE_UNDEFINED
    new_parser.move_to_next_symbol()
    assert new_parser.device_terminal() == (None, None)
    assert new_parser.error_code == new_parser.EXPECT_PORT_NAME
    new_parser.move_to_next_symbol()
    assert new_parser.device_terminal() == (None, None)
    assert new_parser.error_code == new_parser.INVALID_PORT_NAME
    new_parser.move_to_next_symbol()
    assert new_parser.device_terminal(monitor_mode=True) == (None, None)
    assert new_parser.error_code == new_parser.MONITOR_NOT_OUTPUT
    new_parser.move_to_next_symbol()
    new_parser.statement()
    new_parser.move_to_next_symbol()
    assert new_parser.device_terminal(monitor_mode=True) == (None, None)
    assert new_parser.error_code == new_parser.MONITOR_PRESENT
    new_parser.error_code = new_parser.NO_ERROR
    new_parser.statement()
    assert new_parser.device_terminal() == (None, None)
    assert new_parser.error_code == new_parser.EXPECT_PORT_NAME_DTYPE
    new_parser.statement()
    new_parser.move_to_next_symbol()
    assert new_parser.device_terminal(monitor_mode=True) == (None, None)
    assert new_parser.error_code == new_parser.MONITOR_PRESENT
    new_parser.error_code = new_parser.NO_ERROR

