from names import Names
import pytest


@pytest.fixture
def new_names():
    '''returns an instance of class Names'''
    new_names = Names()
    return new_names

def test_unique_error_code(new_names):
    assert new_names.unique_error_code(3) == [0,1,2]
    assert new_names.unique_error_code(2) == [3,4]
    assert new_names.error_code_count == 5


def test_lookup(new_names):
    assert new_names.lookup('DEVICE') == 0
    assert new_names.lookup('CONNECT') == 1
    assert new_names.lookup('MONITOR') == 2
    assert new_names.lookup('CLOCK') == 3
    assert new_names.lookup('DEVICE') == 0
    assert new_names.lookup('CONNECT') == 1
    assert new_names.lookup('SWITCH') == 4
    assert new_names.lookup(['CLOCK','AND','SWITCH','NAND']) == [3,5,4,6]
    assert new_names.lookup('G2') == 7

def test_query(new_names):
    assert new_names.query('DEVICE') == 0
    assert new_names.query('device') == None
    assert new_names.query('AND') == 5
    assert new_names.query('G1') == None

def test_get_name_string(new_names):
    assert new_names.get_name_string(0) == 'DEVICE'
    assert new_names.get_name_string(3) == 'CLOCK'
    assert new_names.get_name_string(12) == None
    assert new_names.get_name_string(7) == 'G2'
