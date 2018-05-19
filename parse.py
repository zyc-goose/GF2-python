"""Parse the definition file and build the logic network.

Used in the Logic Simulator project to analyse the syntactic and semantic
correctness of the symbols received from the scanner and then builds the
logic network.

Classes
-------
Parser - parses the definition file and builds the logic network.
"""


class Parser:

    """Parse the definition file and build the logic network.

    The parser deals with error handling. It analyses the syntactic and
    semantic correctness of the symbols it receives from the scanner, and
    then builds the logic network. If there are errors in the definition file,
    the parser detects this and tries to recover from it, giving helpful
    error messages.

    Parameters
    ----------
    names: instance of the names.Names() class.
    devices: instance of the devices.Devices() class.
    network: instance of the network.Network() class.
    monitors: instance of the monitors.Monitors() class.
    scanner: instance of the scanner.Scanner() class.

    Public methods
    --------------
    parse_network(self): Parses the circuit definition file.
    """

    def __init__(self, names, devices, network, monitors, scanner):
        """Initialise constants."""
        self.symbol_type = self.symbol_id = None
        self.move_to_next_symbol()
        self.error_code = self.NO_ERROR
        self.error_count = 0
        self.existing_device_ids = set()
        self.device_type_to_id = {
            'CLOCK'  : devices.CLOCK,
            'SWITCH' : devices.SWITCH,
            'AND'    : devices.AND,
            'NAND'   : devices.NAND,
            'OR'     : devices.OR,
            'NOR'    : devices.NOR,
            'DTYPE'  : devices.DTYPE,
            'XOR'    : devices.XOR
        }
        [] = names.unique_error_codes(13)

    def move_to_next_symbol(self):
        """Get next symbol from scanner."""
        self.symbol_type, self.symbol_id = scanner.get_symbol()

    def parse_network(self):
        """Parse the circuit definition file."""
        # For now just return True, so that userint and gui can run in the
        # skeleton code. When complete, should return False when there are
        # errors in the circuit definition file.
        return True
        ##################################################
        if self.is_EOF():
            self.error_code = self.EMPTY_FILE
            return False
        while not self.is_EOF():
            if not self.statement():
                self.error_display()
                self.error_code = self.NO_ERROR # restore to normal state
                while (not self.is_left_paren()) and (not self.is_EOF()):
                    self.move_to_next_symbol() # move to next '(' to resume parsing
        if self.error_count > 0:
            return False
        return True

    def is_left_paren(self):
        """Check whether current symbol is '('."""
        return self.symbol_type == scanner.PUNCTUATION and \
               names.get_name_string(self.symbol_id) == '('

    def is_right_paren(self):
        """Check whether current symbol is ')'."""
        return self.symbol_type == scanner.PUNCTUATION and \
               names.get_name_string(self.symbol_id) == ')'

    def is_dot(self):
        """Check whether current symbol is ')'."""
        return self.symbol_type == scanner.PUNCTUATION and \
               names.get_name_string(self.symbol_id) == '.'

    def is_keyword(self):
        """Check whether current symbol is a keyword."""
        return self.symbol_type == scanner.KEYWORD

    def is_identifier(self):
        """Check whether current symbol is an identifier."""
        return self.symbol_type == scanner.IDENTIFIER

    def is_number(self):
        """Check whether current symbol is a number."""
        return self.symbol_type == scanner.NUMBER

    def is_EOF(self):
        """Check whether current symbol is EOF."""
        return self.symbol_type == scanner.EOF

    def is_target_name(self, target_name):
        """Check if the name string corresponding to self.symbol_id
        is the same as target_name."""
        if not isinstance(target_name, str):
            raise TypeError('target_name should be a str')
        return self.get_name_string() == target_name

    def get_name_string(self):
        """Get the name string of self.symbol_id."""
        if not isinstance(self.symbol_id, int):
            raise TypeError('self.symbol_id should be an int')
        return self.names.get_name_string(self.symbol_id)

    def statement(self):
        """Parse a statement, which starts with '(' and ends with ')'."""
        if not self.is_left_paren():
            self.error_code = self.EXPECT_LEFT_PAREN
            return False
        self.move_to_next_symbol()
        if not (self.device() or self.connect() or self.monitor()):
            if self.error_code == self.NO_ERROR:
                self.error_code = self.UNKNOWN_FUNCTION_NAME
            return False
        self.move_to_next_symbol()
        if not self.is_right_paren():
            self.error_code = self.EXPECT_RIGHT_PAREN
            return False
        self.move_to_next_symbol()
        return True

    def device(self):
        """Parse a device definition."""
        if not (self.is_keyword() and self.is_target_name('DEVICE')):
            return False # no error code
        self.move_to_next_symbol()
        if not self.is_identifier():
            if self.is_keyword():
                if self.get_name_string() in ('is', 'are'):
                    self.error_code = self.EMPTY_DEVICE_LIST
                else:
                    self.error_code = self.KEYWORD_AS_DEVICE_NAME
            elif self.is_right_paren():
                self.error_code = self.EMPTY_DEVICE_LIST
            else:
                self.error_code = self.INVALID_DEVICE_NAME
            return False
        if self.symbol_id in self.existing_device_ids:
            self.error_code = self.DEVICE_REDEFINED
            return False
        self.existing_device_ids.add(self.symbol_id)
        new_device_ids = [self.symbol_id]
        self.move_to_next_symbol()
        while self.is_identifier():
            if self.symbol_id in self.existing_device_ids:
                self.error_code = self.DEVICE_REDEFINED
                return False
            self.existing_device_ids.add(self.symbol_id)
            new_device_ids.append(self.symbol_id)
            self.move_to_next_symbol()
        if not (self.is_keyword() and (self.get_name_string() in ('is', 'are'))):
            self.error_code = self.EXPECT_KEYWORD_IS_ARE
            return False
        self.move_to_next_symbol()
        if self.is_right_paren():
            self.error_code = self.DEVICE_TYPE_ABSENT
            return False
        elif not self.is_identifier():
            self.error_code = self.EXPECT_DEVICE_TYPE
            return False
        device_type = self.get_name_string()
        qualifier = None
        if device_type in ('CLOCK','SWITCH','AND','NAND','OR','NOR'):
            self.move_to_next_symbol()
            if not self.is_number():
                self.error_code = self.EXPECT_QUALIFIER
                return False
            qualifier = self.symbol_id
            self.move_to_next_symbol()
            return True
        elif device_type in ('DTYPE','XOR'):
            self.move_to_next_symbol()
            if self.is_number():
                self.error_code = self.EXPECT_NO_QUALIFIER
                return False
            return True
        else:
            self.error_code = self.UNKNOWN_DEVICE_TYPE
            return False

    def device_terminal(self):
        """Parse a device terminal and return (devicd_id, port_id).
        Return (None, None) if error occurs."""
        if not self.is_identifier():
            return None, None # no error code at this point
        device_id = self.symbol_id
        if device_id not in self.existing_device_ids:
            self.error_code = self.DEVICE_UNDEFINED
            return None, None
        self.move_to_next_symbol()
        if self.is_dot():
            self.move_to_next_symbol()
            if not self.is_identifier():
                self.error_code = self.EXPECT_PORT_NAME
                return None, None
            port_id = self.symbol_id
            self.move_to_next_symbol()
        else:
            port_id = None
        return device_id, port_id


    def connect(self):
        """Parse a connection."""
        if not (self.is_keyword() and self.is_target_name('CONNECT')):
            return False # no error code
        self.move_to_next_symbol()
        first_device_id, first_port_id = self.device_terminal()
        if first_device_id is None: # error occurs
            if self.error_code == self.NO_ERROR:
                self.error_code = self.EXPECT_DEVICE_TERMINAL_NAME
            return False
        if not (self.is_keyword() and self.is_target_name('to')):
            self.error_code = self.EXPECT_KEYWORD_TO
            return False
        self.move_to_next_symbol()
        second_device_id, second_port_id = self.device_terminal()
        if second_device_id is None: # error occurs
            if self.error_code == self.NO_ERROR:
                self.error_code = self.EXPECT_DEVICE_TERMINAL_NAME
            return False
        return True

    def monitor(self):
        """Parse a series of monitors."""
        if not (self.is_keyword() and self.is_target_name('MONITOR')):
            return False # no error code
        self.move_to_next_symbol()
        device_id, port_id = self.device_terminal()
        if device_id is None: # error occurs
            if self.error_code == self.NO_ERROR:
                if self.is_right_paren():
                    self.error_code = self.EMPTY_MONITOR_LIST
                else:
                    self.error_code = self.EXPECT_DEVICE_NAME
            return False
        while True:
            device_id, port_id = self.device_terminal()
            if device_id is None:
                if self.error_code == self.NO_ERROR:
                    return True
                return False

    def error_display(self):
        """Display error messages on terminal."""
        return True
