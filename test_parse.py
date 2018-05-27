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
"""This section of test intends to check whether the parser is able to generate
the correct error messages when given a poorly defined input file. The class
ParserTestCase acts as a virtual machine to handle the input and output and
check whethe the output is as desired."""
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

@pytest.fixture
def testcase():
    """An empty TestCase instance."""
    return ParserTestCase()


def test_error_bad_character(testcase):
    """BAD_CHARACTER"""
    testcase.add_input_line('(DEVICE A B are XOR)')
    testcase.add_input_line('(DEVICE C D ?)')
    testcase.add_expected_error('BAD_CHARACTER', line_number=2, cursor_pos=13)
    testcase.execute()
    assert testcase.passed()

def test_error_bad_comment(testcase):
    """BAD_COMMENT"""
    testcase.add_input_line('/* foo bar pig dog')
    testcase.add_expected_error('BAD_COMMENT', line_number=1, cursor_pos=18)
    testcase.execute()
    assert testcase.passed()

def test_error_bad_number(testcase):
    """BAD_NUMBER"""
    testcase.add_input_line('(DEVICE A B are NAND 007)')
    testcase.add_expected_error('BAD_NUMBER', line_number=1, cursor_pos=24)
    testcase.execute()
    assert testcase.passed()

def test_error_device_redefined(testcase):
    """DEVICE_REDEFINED"""
    testcase.add_input_line('(DEVICE A B are NAND 2)')
    testcase.add_input_line('(DEVICE A ??!!@@##')
    testcase.add_expected_error('DEVICE_REDEFINED', line_number=2, cursor_pos=9)
    testcase.execute()
    assert testcase.passed()

def test_error_device_type_absent(testcase):
    """DEVICE_TYPE_ABSENT"""
    testcase.add_input_line('(DEVICE A1 A2 are  ')
    testcase.add_input_line('')
    testcase.add_input_line('   )')
    testcase.add_expected_error('DEVICE_TYPE_ABSENT', line_number=1, cursor_pos=17)
    testcase.execute()
    assert testcase.passed()

def test_error_device_undefined(testcase):
    """DEVICE_UNDEFINED"""
    testcase.add_input_line('(DEVICE A1 A2 are OR 3)')
    testcase.add_input_line('(MONITOR A3 )')
    testcase.add_expected_error('DEVICE_UNDEFINED', line_number=2, cursor_pos=11)
    testcase.execute()
    assert testcase.passed()

def test_error_empty_device_list(testcase):
    """EMPTY_DEVICE_LIST"""
    testcase.add_input_line('(DEVICE   are DTYPE)')
    testcase.add_input_line('(DEVICE  )')
    testcase.add_expected_error('EMPTY_DEVICE_LIST', line_number=1, cursor_pos=13)
    testcase.add_expected_error('EMPTY_DEVICE_LIST', line_number=2, cursor_pos=10)
    testcase.execute()
    assert testcase.passed()

def test_error_empty_file(testcase):
    """EMPTY_FILE"""
    testcase.add_input_line('// csbg csbg snb cnm wqnmlgb zao yu feng')
    testcase.add_input_line('/* Lorem Ipsum Cappucino Latte')
    testcase.add_input_line('bagels cereal chocolate pig elephant')
    testcase.add_input_line('zheye jidangwei */')
    testcase.add_expected_error('EMPTY_FILE', line_number=4, cursor_pos=18)
    testcase.execute()
    assert testcase.passed()

def test_error_empty_monitor_list(testcase):
    """EMPTY_MONITOR_LIST"""
    testcase.add_input_line('(DEVICE A is NAND 1)')
    testcase.add_input_line('(MONITOR          )')
    testcase.add_expected_error('EMPTY_MONITOR_LIST', line_number=2, cursor_pos=19)
    testcase.execute()
    assert testcase.passed()

def test_error_empty_statement(testcase):
    """EMPTY_STATEMENT"""
    testcase.add_input_line('(DEVICE dog cat bulldog are DTYPE)')
    testcase.add_input_line('()')
    testcase.add_expected_error('EMPTY_STATEMENT', line_number=2, cursor_pos=2)
    testcase.execute()
    assert testcase.passed()

def test_error_expect_device_terminal_name(testcase):
    """EXPECT_DEVICE_TERMINAL_NAME"""
    testcase.add_input_line('(CONNECT to B foo bar)')
    testcase.add_input_line('(CONNECT)')
    testcase.add_input_line('(DEVICE A is DTYPE)')
    testcase.add_input_line('(CONNECT A.DATA to )')
    testcase.add_expected_error('EXPECT_DEVICE_TERMINAL_NAME', line_number=1, cursor_pos=11)
    testcase.add_expected_error('EXPECT_DEVICE_TERMINAL_NAME', line_number=2, cursor_pos=9)
    testcase.add_expected_error('EXPECT_DEVICE_TERMINAL_NAME', line_number=4, cursor_pos=20)
    testcase.execute()
    assert testcase.passed()

def test_error_expect_keyword_is_are(testcase):
    """EXPECT_KEYWORD_IS_ARE"""
    testcase.add_input_line('(DEVICE A B C)')
    testcase.add_input_line('(DEVICE D E F CLOCK)')
    testcase.add_expected_error('EXPECT_KEYWORD_IS_ARE', line_number=1, cursor_pos=14)
    testcase.add_expected_error('EXPECT_KEYWORD_IS_ARE', line_number=2, cursor_pos=19)
    testcase.execute()
    assert testcase.passed()

def test_error_expect_keyword_to(testcase):
    """EXPECT_KEYWORD_TO"""
    testcase.add_input_line('(DEVICE A is XOR)')
    testcase.add_input_line('(CONNECT A)')
    testcase.add_input_line('(CONNECT A dog)')
    testcase.add_expected_error('EXPECT_KEYWORD_TO', line_number=2, cursor_pos=11)
    testcase.add_expected_error('EXPECT_KEYWORD_TO', line_number=3, cursor_pos=14)
    testcase.execute()
    assert testcase.passed()

def test_error_expect_left_paren(testcase):
    """EXPECT_LEFT_PAREN"""
    testcase.add_input_line('(DEVICE A is XOR)')
    testcase.add_input_line('  cat (DEVICE B is NOR 16)')
    testcase.add_expected_error('EXPECT_LEFT_PAREN', line_number=2, cursor_pos=5)
    testcase.execute()
    assert testcase.passed()

def test_error_expect_left_paren(testcase):
    """EXPECT_NO_QUALIFIER"""
    testcase.add_input_line('(DEVICE A is XOR 0)')
    testcase.add_input_line('(DEVICE B is DTYPE 3154)')
    testcase.add_expected_error('EXPECT_NO_QUALIFIER', line_number=1, cursor_pos=18)
    testcase.add_expected_error('EXPECT_NO_QUALIFIER', line_number=2, cursor_pos=23)
    testcase.execute()
    assert testcase.passed()

def test_error_expect_port_name(testcase):
    """EXPECT_PORT_NAME"""
    testcase.add_input_line('(DEVICE A B is NAND 2)')
    testcase.add_input_line('(CONNECT A. to )')
    testcase.add_input_line('(CONNECT A to B.)')
    testcase.add_expected_error('EXPECT_PORT_NAME', line_number=2, cursor_pos=11)
    testcase.add_expected_error('EXPECT_PORT_NAME', line_number=3, cursor_pos=16)
    testcase.execute()
    assert testcase.passed()

def test_error_expect_port_name_dtype(testcase):
    """EXPECT_PORT_NAME_DTYPE"""
    testcase.add_input_line('(DEVICE A B is DTYPE)')
    testcase.add_input_line('(CONNECT A to )')
    testcase.add_input_line('(CONNECT A.QBAR to B)')
    testcase.add_expected_error('EXPECT_PORT_NAME_DTYPE', line_number=2, cursor_pos=10)
    testcase.add_expected_error('EXPECT_PORT_NAME_DTYPE', line_number=3, cursor_pos=20)
    testcase.execute()
    assert testcase.passed()

def test_error_expect_qualifier(testcase):
    """EXPECT_QUALIFIER"""
    testcase.add_input_line('(DEVICE A B is NAND 3 )')
    testcase.add_input_line('(DEVICE C D is NAND   )')
    testcase.add_expected_error('EXPECT_QUALIFIER', line_number=2, cursor_pos=19)
    testcase.execute()
    assert testcase.passed()

def test_error_expect_right_paren(testcase):
    """EXPECT_RIGHT_PAREN"""
    testcase.add_input_line('(DEVICE foo bar is NAND 14')
    testcase.add_input_line('  /* some useless comment')
    testcase.add_input_line(' anothe sb sb sb sb csbg */')
    testcase.add_input_line('(CONNECT foo.I1 to bar)')
    testcase.add_expected_error('EXPECT_RIGHT_PAREN', line_number=1, cursor_pos=27)
    testcase.execute()
    assert testcase.passed()

def test_error_input_connected(testcase):
    """INPUT_CONNECTED"""
    testcase.add_input_line('(DEVICE A B C are AND 2)')
    testcase.add_input_line('  /* some useless comment')
    testcase.add_input_line(' anothe sb sb sb sb csbg */')
    testcase.add_input_line('')
    testcase.add_input_line('(CONNECT A to C.I1)')
    testcase.add_input_line('(CONNECT B to C.I1)')
    testcase.add_expected_error('INPUT_CONNECTED', line_number=6, cursor_pos=18)
    testcase.execute()
    assert testcase.passed()

def test_error_input_connected(testcase):
    """INPUT_TO_INPUT"""
    testcase.add_input_line('(DEVICE A B are AND 2)')
    testcase.add_input_line('(CONNECT A.I2 to B.I1)')
    testcase.add_expected_error('INPUT_TO_INPUT', line_number=2, cursor_pos=21)
    testcase.execute()
    assert testcase.passed()

def test_error_invalid_device_name(testcase):
    """INVALID_DEVICE_NAME"""
    testcase.add_input_line('(DEVICE A B C1234 1234)')
    testcase.add_input_line('(DEVICE DDD .)')
    testcase.add_expected_error('INVALID_DEVICE_NAME', line_number=1, cursor_pos=22)
    testcase.add_expected_error('INVALID_DEVICE_NAME', line_number=2, cursor_pos=13)
    testcase.execute()
    assert testcase.passed()

def test_error_invalid_device_type(testcase):
    """INVALID_DEVICE_TYPE"""
    testcase.add_input_line('(DEVICE A11 A22 A33 are BTYPE)')
    testcase.add_input_line('(DEVICE B1 B2 B3 are csbg)')
    testcase.add_input_line('(DEVICE C1 C2 C3 are .)')
    testcase.add_input_line('(DEVICE D1 D2 D3 are MONITOR)')
    testcase.add_expected_error('INVALID_DEVICE_TYPE', line_number=1, cursor_pos=29)
    testcase.add_expected_error('INVALID_DEVICE_TYPE', line_number=2, cursor_pos=25)
    testcase.add_expected_error('INVALID_DEVICE_TYPE', line_number=3, cursor_pos=22)
    testcase.add_expected_error('INVALID_DEVICE_TYPE', line_number=4, cursor_pos=28)
    testcase.execute()
    assert testcase.passed()

def test_error_invalid_function_name(testcase):
    """INVALID_FUNCTION_NAME"""
    testcase.add_input_line('(DEVICES )')
    testcase.add_input_line('(CONNECTION C1 C2 C3 are .)')
    testcase.add_input_line('(MONICA D1 )')
    testcase.add_expected_error('INVALID_FUNCTION_NAME', line_number=1, cursor_pos=8)
    testcase.add_expected_error('INVALID_FUNCTION_NAME', line_number=2, cursor_pos=11)
    testcase.add_expected_error('INVALID_FUNCTION_NAME', line_number=3, cursor_pos=7)
    testcase.execute()
    assert testcase.passed()

def test_error_invalid_port_name(testcase):
    """INVALID_PORT_NAME"""
    testcase.add_input_line('(DEVICE A is NAND 4)')
    testcase.add_input_line('(DEVICE B is DTYPE)')
    testcase.add_input_line('(CONNECT A.I5 to sb)')
    testcase.add_input_line('(MONITOR B.QQQ)')
    testcase.add_expected_error('INVALID_PORT_NAME', line_number=3, cursor_pos=13)
    testcase.add_expected_error('INVALID_PORT_NAME', line_number=4, cursor_pos=14)
    testcase.execute()
    assert testcase.passed()

def test_error_invalid_qualifier(testcase):
    """INVALID_QUALIFIER"""
    testcase.add_input_line('(DEVICE A is NAND 0)')
    testcase.add_input_line('(DEVICE B is NOR 17)')
    testcase.add_input_line('(DEVICE C is SWITCH 2)')
    testcase.add_expected_error('INVALID_QUALIFIER', line_number=1, cursor_pos=19)
    testcase.add_expected_error('INVALID_QUALIFIER', line_number=2, cursor_pos=19)
    testcase.add_expected_error('INVALID_QUALIFIER', line_number=3, cursor_pos=21)
    testcase.execute()
    assert testcase.passed()

def test_error_keyword_as_device_name(testcase):
    """KEYWORD_AS_DEVICE_NAME"""
    testcase.add_input_line('(DEVICE DEVICE)')
    testcase.add_input_line('(DEVICE csbg CONNECT)')
    testcase.add_input_line('(DEVICE A B to)')
    testcase.add_expected_error('KEYWORD_AS_DEVICE_NAME', line_number=1, cursor_pos=14)
    testcase.add_expected_error('KEYWORD_AS_DEVICE_NAME', line_number=2, cursor_pos=20)
    testcase.add_expected_error('KEYWORD_AS_DEVICE_NAME', line_number=3, cursor_pos=14)
    testcase.execute()
    assert testcase.passed()

def test_error_monitor_not_output(testcase):
    """MONITOR_NOT_OUTPUT"""
    testcase.add_input_line('(DEVICE csbg is DTYPE)')
    testcase.add_input_line('(DEVICE zyf is NAND 2)')
    testcase.add_input_line('(MONITOR csbg.CLK)')
    testcase.add_input_line('(MONITOR zyf.I1)')
    testcase.add_expected_error('MONITOR_NOT_OUTPUT', line_number=3, cursor_pos=17)
    testcase.add_expected_error('MONITOR_NOT_OUTPUT', line_number=4, cursor_pos=15)
    testcase.execute()
    assert testcase.passed()

def test_error_monitor_present(testcase):
    """MONITOR_PRESENT"""
    testcase.add_input_line('(DEVICE A B C are OR 4)')
    testcase.add_input_line('(MONITOR A B C)')
    testcase.add_input_line('(MONITOR C)')
    testcase.add_input_line('(MONITOR A)')
    testcase.add_expected_error('MONITOR_PRESENT', line_number=3, cursor_pos=10)
    testcase.add_expected_error('MONITOR_PRESENT', line_number=4, cursor_pos=10)
    testcase.execute()
    assert testcase.passed()

def test_error_output_to_output(testcase):
    """OUTPUT_TO_OUTPUT"""
    testcase.add_input_line('(DEVICE A B C are XOR)')
    testcase.add_input_line('(DEVICE D is DTYPE)')
    testcase.add_input_line('(CONNECT A to B)')
    testcase.add_input_line('(CONNECT D.Q to D.QBAR)')
    testcase.add_expected_error('OUTPUT_TO_OUTPUT', line_number=3, cursor_pos=15)
    testcase.add_expected_error('OUTPUT_TO_OUTPUT', line_number=4, cursor_pos=22)
    testcase.execute()
    assert testcase.passed()


###### FUNCTION TESTS ######
''' The following tests are intended to test each function in parser.py,
and assert all the possible returns of the functions. It omits testing 
error display as this has been thoroughly tested above'''
@pytest.fixture(scope="session")
def new_parser():
    # Build a fixture and all the following tests uses it
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

# Series of tests for the individual assertion functions
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
    # Missing left parenthesis
    move_to_next_symbol.statement()
    error_code_1 = move_to_next_symbol.error_code
    move_to_next_symbol.error_code = move_to_next_symbol.NO_ERROR
    move_to_next_symbol.move_to_next_symbol()

    # Empty statement
    move_to_next_symbol.statement()
    error_code_2 = move_to_next_symbol.error_code
    move_to_next_symbol.error_code = move_to_next_symbol.NO_ERROR
    move_to_next_symbol.move_to_next_symbol()

    # First keyword is invalid
    move_to_next_symbol.statement()
    error_code_3 = move_to_next_symbol.error_code
    move_to_next_symbol.error_code = move_to_next_symbol.NO_ERROR
    move_to_next_symbol.move_to_next_symbol()

    # Missing right parenthesis
    move_to_next_symbol.statement()
    error_code_4 = move_to_next_symbol.error_code
    move_to_next_symbol.error_code = move_to_next_symbol.NO_ERROR
    assert error_code_1 == move_to_next_symbol.EXPECT_LEFT_PAREN
    assert error_code_2 == move_to_next_symbol.EMPTY_STATEMENT
    assert error_code_3 == move_to_next_symbol.INVALID_FUNCTION_NAME
    assert error_code_4 == move_to_next_symbol.EXPECT_RIGHT_PAREN

def test_statement(new_parser):
    # function statement all pass
    assert new_parser.statement()

def test_device_error(new_parser):
    # keyword not DEVICE
    assert not new_parser.device()
    error_code_1 = new_parser.error_code
    assert error_code_1 == new_parser.NO_ERROR
    new_parser.move_to_next_symbol()

    # No device name given
    assert not new_parser.device()
    new_parser.error_code = new_parser.NO_ERROR
    new_parser.move_to_next_symbol()

    # Invalid character
    assert not new_parser.device()
    new_parser.error_code = new_parser.NO_ERROR
    new_parser.move_to_next_symbol()

    # missing first device name
    assert not new_parser.device()
    new_parser.error_code = new_parser.NO_ERROR
    new_parser.move_to_next_symbol()

    # Missing device type
    assert not new_parser.device()
    new_parser.error_code = new_parser.NO_ERROR
    new_parser.move_to_next_symbol()

    # Invalid Qualifier
    assert not new_parser.device()
    error_code_2 = new_parser.error_code
    assert error_code_2 == new_parser.INVALID_QUALIFIER
    new_parser.error_code = new_parser.NO_ERROR

def test_device(move_to_next_symbol):
    # Function device all pass
    assert move_to_next_symbol.device()

def test_get_first_device_id_error(new_parser):
    # No device is given
    assert new_parser.get_first_device_id(set()) is None
    assert new_parser.error_code == new_parser.EMPTY_DEVICE_LIST
    new_parser.move_to_next_symbol()

    # Keyword as device name
    assert new_parser.get_first_device_id(set()) is None
    assert new_parser.error_code == new_parser.KEYWORD_AS_DEVICE_NAME
    new_parser.move_to_next_symbol()

    # Empty list
    assert new_parser.get_first_device_id(set()) is None
    assert new_parser.error_code == new_parser.EMPTY_DEVICE_LIST
    new_parser.move_to_next_symbol()

    # Device name is invalid
    assert new_parser.get_first_device_id(set()) is None
    assert new_parser.error_code == new_parser.INVALID_DEVICE_NAME
    new_parser.move_to_next_symbol()

    # Repeated definition of devices, made use of previously defined device
    new_parser.get_first_device_id(set())
    assert new_parser.error_code == new_parser.DEVICE_REDEFINED
    new_parser.move_to_next_symbol()

def test_get_first_device_id(new_parser):
    # get_first_device_id all pass
    assert new_parser.get_first_device_id(set()) is not None

def test_get_optional_device_id_error(new_parser):
    # Repeated definition of devices, made use of previously defined device
    assert new_parser.get_optional_device_id(set()) is None
    assert new_parser.error_code == new_parser.DEVICE_REDEFINED
    new_parser.move_to_next_symbol()

def test_get_optional_device_id(new_parser):
    # get_optional_device_id all pass
    assert new_parser.get_optional_device_id(set()) is 37

def test_check_keyword_is_are_error(new_parser):
    # missing keyword is/are
    assert not new_parser.check_keyword_is_are()
    assert new_parser.error_code == new_parser.EXPECT_KEYWORD_IS_ARE
    new_parser.move_to_next_symbol()

    # Invalid name, unknown character
    assert not new_parser.check_keyword_is_are()
    assert new_parser.error_code == new_parser.INVALID_DEVICE_NAME
    new_parser.move_to_next_symbol()

    # Got device with qualifier instead
    assert not new_parser.check_keyword_is_are()
    assert new_parser.error_code == new_parser.EXPECT_KEYWORD_IS_ARE
    new_parser.move_to_next_symbol()

    # Got device without qualifier instead
    assert not new_parser.check_keyword_is_are()
    assert new_parser.error_code == new_parser.EXPECT_KEYWORD_IS_ARE
    new_parser.move_to_next_symbol()

    # Got keyword but not is/are instead
    assert not new_parser.check_keyword_is_are()
    assert new_parser.error_code == new_parser.KEYWORD_AS_DEVICE_NAME
    new_parser.move_to_next_symbol()

def test_check_keyword_is_are(new_parser):
    # check_keyword_is_are all pass
    assert new_parser.check_keyword_is_are()
    new_parser.move_to_next_symbol()

def test_get_device_type_error(new_parser):
    # Got right parenthesis
    assert new_parser.get_device_type() == (None, None)
    assert new_parser.error_code == new_parser.DEVICE_TYPE_ABSENT
    new_parser.move_to_next_symbol()

    # not a keyword
    assert new_parser.get_device_type() == (None, None)
    assert new_parser.error_code == new_parser.INVALID_DEVICE_TYPE
    new_parser.move_to_next_symbol()

    # Qualifier missing
    assert new_parser.get_device_type() == (None, None)
    assert new_parser.error_code == new_parser.EXPECT_QUALIFIER

    # Should have no qualifier
    assert new_parser.get_device_type() == (None, None)
    assert new_parser.error_code == new_parser.EXPECT_NO_QUALIFIER
    new_parser.move_to_next_symbol()

    # is a keyword but not a device type
    assert new_parser.get_device_type() == (None, None)
    assert new_parser.error_code == new_parser.INVALID_DEVICE_TYPE
    new_parser.move_to_next_symbol()

def test_get_device_type(new_parser):
    # Device with qualidier test pass
    assert new_parser.get_device_type() == (new_parser.devices.CLOCK, 10)
    # Device without qualidier test pass
    assert new_parser.get_device_type() == (new_parser.devices.XOR, None)
    new_parser.move_to_next_symbol()

def test_device_terminal_error(new_parser):
    # Not a valid name
    assert new_parser.device_terminal() == (None, None)
    new_parser.move_to_next_symbol()

    # Undefined device
    assert new_parser.device_terminal() == (None, None)
    assert new_parser.error_code == new_parser.DEVICE_UNDEFINED
    new_parser.move_to_next_symbol()

    # No port name given but followed by 'to'
    assert new_parser.device_terminal() == (None, None)
    assert new_parser.error_code == new_parser.EXPECT_PORT_NAME
    new_parser.move_to_next_symbol()

    # Port name exceed the range
    assert new_parser.device_terminal() == (None, None)
    assert new_parser.error_code == new_parser.INVALID_PORT_NAME
    new_parser.move_to_next_symbol()

    # In monitor mode, not monitoring output
    assert new_parser.device_terminal(monitor_mode=True) == (None, None)
    assert new_parser.error_code == new_parser.MONITOR_NOT_OUTPUT
    new_parser.error_code = new_parser.NO_ERROR
    new_parser.move_to_next_symbol()

    # already being monitored
    new_parser.statement()
    assert new_parser.device_terminal(monitor_mode=True) == (None, None)
    assert new_parser.error_code == new_parser.MONITOR_PRESENT
    new_parser.error_code = new_parser.NO_ERROR

    # Monitor mode, DTYPE to be monitored, missing port name
    new_parser.statement()
    assert new_parser.device_terminal() == (None, None)
    assert new_parser.error_code == new_parser.EXPECT_PORT_NAME_DTYPE
    new_parser.error_code = new_parser.NO_ERROR

    # already being monitored, for DTYPE branch
    new_parser.statement()
    assert new_parser.device_terminal(monitor_mode=True) == (None, None)
    assert new_parser.error_code == new_parser.MONITOR_PRESENT
    new_parser.error_code = new_parser.NO_ERROR

def test_device_terminal(new_parser):
    # device_terminal all pass
    new_parser.move_to_next_symbol()
    new_parser.statement()
    assert new_parser.device_terminal() == (42, 31)

def test_connect(new_parser):
    # connect all pass
    assert new_parser.connect()

def test_connect_error(new_parser):
    # Incorrect keyword
    assert not new_parser.connect()
    new_parser.move_to_next_symbol()

    # missing first device
    new_parser.error_code = new_parser.NO_ERROR
    assert not new_parser.connect()
    assert new_parser.error_code == new_parser.EXPECT_DEVICE_TERMINAL_NAME

    # missing keyword to
    new_parser.error_code = new_parser.NO_ERROR
    assert not new_parser.connect()
    assert new_parser.error_code == new_parser.EXPECT_KEYWORD_TO

    # missing second device
    new_parser.error_code = new_parser.NO_ERROR
    new_parser.move_to_next_symbol()
    assert not new_parser.connect()
    assert new_parser.error_code == new_parser.EXPECT_DEVICE_TERMINAL_NAME

    # Input already connected
    new_parser.error_code = new_parser.NO_ERROR
    assert not new_parser.connect()
    assert new_parser.error_code == new_parser.INPUT_CONNECTED

    # Input connected to input
    new_parser.error_code = new_parser.NO_ERROR
    assert not new_parser.connect()
    assert new_parser.error_code == new_parser.INPUT_TO_INPUT

    # Output connected to output
    new_parser.error_code = new_parser.NO_ERROR
    assert not new_parser.connect()
    assert new_parser.error_code == new_parser.OUTPUT_TO_OUTPUT

def test_monitor_error(new_parser):
    # Keyword not MONITOR
    new_parser.error_code = new_parser.NO_ERROR
    assert not new_parser.monitor()
    new_parser.move_to_next_symbol()

    # No monitor given
    new_parser.error_code = new_parser.NO_ERROR
    assert not new_parser.monitor()
    assert new_parser.error_code == new_parser.EMPTY_MONITOR_LIST

    # Device name invalid, undefined device is tested in device terminal test
    new_parser.error_code = new_parser.NO_ERROR
    new_parser.move_to_next_symbol()
    assert not new_parser.monitor()
    assert new_parser.error_code == new_parser.INVALID_DEVICE_NAME

    # Check other device branch
    new_parser.error_code = new_parser.NO_ERROR
    assert not new_parser.monitor()

def test_monitor(new_parser):
    # Function monitor all pass
    new_parser.error_code = new_parser.NO_ERROR
    assert not new_parser.monitor()
