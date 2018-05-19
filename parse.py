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
        self.move_to_next_symbol()
        self.error_code = self.NO_ERROR


    def move_to_next_symbol(self):
        """Get next symbol from scanner."""
        self.symbol_type, self.symbol_id = scanner.get_symbol()

    def parse_network(self):
        """Parse the circuit definition file."""
        # For now just return True, so that userint and gui can run in the
        # skeleton code. When complete, should return False when there are
        # errors in the circuit definition file.
        while not self.is_EOF():
            if not self.statement():
                self.error_display()
                self.error_code = self.NO_ERROR # restore to normal state
                while (not self.is_left_paren()) and (not self.is_EOF()):
                    self.move_to_next_symbol()
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

    def statement(self):
        """Parse a statement, which starts with '(' and ends with ')'."""
        if self.is_left_paren():
            self.move_to_next_symbol()
            if self.device() or self.connect() or self.monitor():
                self.move_to_next_symbol()
                if self.is_right_paren():
                    self.move_to_next_symbol()
                    return True
                else:
                    self.error_code = self.EXPECT_RIGHT_PAREN
                    return False
            else:
                if self.error_code == self.NO_ERROR:
                    self.error_code = self.UNKNOWN_FUNCTION_NAME
                return False
        else:
            self.error_code = self.EXPECT_LEFT_PAREN
            return False

    def device(self):
        """Parse a device definition."""
        


    def error_display(self):
        """Display error messages on terminal."""
        return True
