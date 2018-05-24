"""Test the parse module."""
import pytest

from names import Names
from scanner import Scanner
from parse import Parser
from devices import Devices
from network import Network
from monitors import Monitors

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
    print(new_parser.symbol_id)
    assert new_parser.statement()
