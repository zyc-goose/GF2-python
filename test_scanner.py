from scanner import Scanner
from names import Names
import pytest


@pytest.fixture
def new_names():
    '''returns an instance of class Names'''
    new_names = Names()
    return new_names

@pytest.fixture
def new_scanner ():
    '''returns an instance of class Scanner'''
    new_names = Names()
    new_scanner = Scanner('ripple_counter.txt', new_names)
    return new_scanner

@pytest.fixture
def new_scanner_names ():
    '''returns an instance of class Scanner'''
    new_names = Names()
    new_scanner = Scanner('test_names.txt', new_names)
    return new_scanner_names

@pytest.fixture
def new_scanner_numbers ():
    '''returns an instance of class Scanner'''
    new_names = Names()
    new_scanner = Scanner('test_numbers.txt', new_names)
    return new_scanner_numbers

def test_get_symbol(new_names, new_scanner):
    i = 0
    desired_output = [[3, 14], [0, 0], [1, 20], [0, 11], [0, 9], [3, 15],
    [3, 14], [0, 0], [1, 21], [1, 22], [1, 23], [0, 12], [0, 4], [2, 0],
    [3, 15], [3, 14], [0, 0], [1, 24], [0, 11], [0, 3], [2, 1], [3, 15],
    [3, 14], [0, 1], [1, 21], [0, 13], [1, 20], [3, 16], [1, 25], [3, 15],
    [3, 14], [0, 1], [1, 22], [0, 13], [1, 20], [3, 16], [1, 26], [3, 15],
    [3, 14], [0, 1], [1, 23], [0,13], [1, 20], [3, 16], [1, 27], [3, 15],
    [3, 14], [0, 1], [1, 24], [0, 13], [1, 20], [3, 16], [1, 28], [3, 15],
    [3, 14], [0, 2], [1, 24], [3, 15]]
    [symbol_type, symbol_id] = new_scanner.get_symbol()
    while symbol_type != new_scanner.EOF:
        assert [symbol_type, symbol_id] == desired_output[i]
        i += 1
        [symbol_type, symbol_id] = new_scanner.get_symbol()

    assert new_scanner.get_symbol() == [5, 3154]

def test_complete_current_line(new_names,new_scanner):
    #new_scanner.input_file.seek(0)
    i = 0
    desired_output = [
    ['(DEVICE Q is DTYPE)', 1],
    ['(DEVICE Q is DTYPE)', 7],
    ['(DEVICE Q is DTYPE)', 9],
    ['(DEVICE Q is DTYPE)', 12],
    ['(DEVICE Q is DTYPE)', 18],
    ['(DEVICE Q is DTYPE)', 19],
    ['(DEVICE set clr data are SWITCH 0)', 1],
    ['(DEVICE set clr data are SWITCH 0)', 7],
    ['(DEVICE set clr data are SWITCH 0)', 11],
    ['(DEVICE set clr data are SWITCH 0)', 15],
    ['(DEVICE set clr data are SWITCH 0)', 20],
    ['(DEVICE set clr data are SWITCH 0)', 24],
    ['(DEVICE set clr data are SWITCH 0)', 31],
    ['(DEVICE set clr data are SWITCH 0)', 33],
    ['(DEVICE set clr data are SWITCH 0)', 34],
    ['(DEVICE clk is CLOCK 1)', 1],
    ['(DEVICE clk is CLOCK 1)', 7],
    ['(DEVICE clk is CLOCK 1)', 11],
    ['(DEVICE clk is CLOCK 1)', 14],
    ['(DEVICE clk is CLOCK 1)', 20],
    ['(DEVICE clk is CLOCK 1)', 22],
    ['(DEVICE clk is CLOCK 1)', 23],
    ['(CONNECT set to Q.SET)', 1],
    ['(CONNECT set to Q.SET)', 8],
    ['(CONNECT set to Q.SET)', 12],
    ['(CONNECT set to Q.SET)', 15],
    ['(CONNECT set to Q.SET)', 17],
    ['(CONNECT set to Q.SET)', 18],
    ['(CONNECT set to Q.SET)', 21],
    ['(CONNECT set to Q.SET)', 22],
    ['(CONNECT clr to Q.CLEAR)', 1],
    ['(CONNECT clr to Q.CLEAR)', 8],
    ['(CONNECT clr to Q.CLEAR)', 12],
    ['(CONNECT clr to Q.CLEAR)', 15],
    ['(CONNECT clr to Q.CLEAR)', 17],
    ['(CONNECT clr to Q.CLEAR)', 18],
    ['(CONNECT clr to Q.CLEAR)', 23],
    ['(CONNECT clr to Q.CLEAR)', 24],
    ['(CONNECT data to Q.DATA)', 1],
    ['(CONNECT data to Q.DATA)', 8],
    ['(CONNECT data to Q.DATA)', 13],
    ['(CONNECT data to Q.DATA)', 16],
    ['(CONNECT data to Q.DATA)', 18],
    ['(CONNECT data to Q.DATA)', 19],
    ['(CONNECT data to Q.DATA)', 23],
    ['(CONNECT data to Q.DATA)', 24],
    ['(CONNECT clk to Q.CLK)', 1],
    ['(CONNECT clk to Q.CLK)', 8],
    ['(CONNECT clk to Q.CLK)', 12],
    ['(CONNECT clk to Q.CLK)', 15],
    ['(CONNECT clk to Q.CLK)', 17],
    ['(CONNECT clk to Q.CLK)', 18],
    ['(CONNECT clk to Q.CLK)', 21],
    ['(CONNECT clk to Q.CLK)', 22],
    ['(MONITOR clk)', 1],
    ['(MONITOR clk)', 8],
    ['(MONITOR clk)', 12],
    ['(MONITOR clk)', 13]]
    [symbol_type, symbol_id] = new_scanner.get_symbol()
    while symbol_type != new_scanner.EOF:
        assert new_scanner.complete_current_line() == desired_output[i]
        i += 1
        [symbol_type, symbol_id] = new_scanner.get_symbol()
