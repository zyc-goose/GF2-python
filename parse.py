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
        self.names = names
        self.devices = devices
        self.network = network
        self.monitors = monitors
        self.scanner = scanner

        self.symbol_type, self.symbol_id = None, None

        [self.NO_ERROR,
         self.BAD_CHARACTER,
         self.BAD_COMMENT,
         self.BAD_NUMBER,
         self.DEVICE_REDEFINED,
         self.DEVICE_TYPE_ABSENT,
         self.DEVICE_UNDEFINED,
         self.EMPTY_DEVICE_LIST,
         self.EMPTY_FILE,
         self.EMPTY_MONITOR_LIST,
         self.EMPTY_STATEMENT,
         self.EXPECT_DEVICE_TERMINAL_NAME,
         self.EXPECT_KEYWORD_IS_ARE,
         self.EXPECT_KEYWORD_TO,
         self.EXPECT_LEFT_PAREN,
         self.EXPECT_NO_QUALIFIER,
         self.EXPECT_PORT_NAME,
         self.EXPECT_PORT_NAME_DTYPE,
         self.EXPECT_QUALIFIER,
         self.EXPECT_RIGHT_PAREN,
         self.INPUT_CONNECTED,
         self.INPUT_TO_INPUT,
         self.INVALID_DEVICE_NAME,
         self.INVALID_DEVICE_TYPE,
         self.INVALID_FUNCTION_NAME,
         self.INVALID_PORT_NAME,
         self.INVALID_QUALIFIER,
         self.KEYWORD_AS_DEVICE_NAME,
         self.MONITOR_NOT_OUTPUT,
         self.MONITOR_PRESENT,
         self.OUTPUT_TO_OUTPUT] = names.unique_error_codes(31)

        self.errormsg = {
            self.NO_ERROR                      : "NO_ERROR",
            self.BAD_CHARACTER                 : "***Syntax Error: Invalid character",
            self.BAD_COMMENT                   : "***Syntax Error: Unterminated /* comment",
            self.BAD_NUMBER                    : "***Syntax Error: Number has too many leading zeros",
            self.DEVICE_REDEFINED              : "***Semantic Error: Device is already defined",
            self.DEVICE_TYPE_ABSENT            : "***Syntax Error: Expected device type",
            self.DEVICE_UNDEFINED              : "***Semantic Error: Device is not defined",
            self.EMPTY_DEVICE_LIST             : "***Syntax Error: Expected device names",
            self.EMPTY_FILE                    : "***Semantic Error: File is empty",
            self.EMPTY_MONITOR_LIST            : "***Syntax Error: Expected device terminal names",
            self.EMPTY_STATEMENT               : "***Syntax Error: Empty statement",
            self.EXPECT_DEVICE_TERMINAL_NAME   : "***Syntax Error: Expected device terminal names",
            self.EXPECT_KEYWORD_IS_ARE         : "***Syntax Error: Expected keyword 'is'/'are'",
            self.EXPECT_KEYWORD_TO             : "***Syntax Error: Expected keyword 'to'",
            self.EXPECT_LEFT_PAREN             : "***Syntax Error: Expected left parenthesis '('",
            self.EXPECT_NO_QUALIFIER           : "***Syntax Error: Expected no qualifier",
            self.EXPECT_PORT_NAME              : "***Syntax Error: Expected a port name after '.'",
            self.EXPECT_PORT_NAME_DTYPE        : "***Semantic Error: DTYPE device should have a port name",
            self.EXPECT_QUALIFIER              : "***Syntax Error: Expected qualifier for the device",
            self.EXPECT_RIGHT_PAREN            : "***Syntax Error: Expected right parenthesis ')'",
            self.INPUT_CONNECTED               : "***Semantic Error: Attempt to connect multiple outputs to an input",
            self.INPUT_TO_INPUT                : "***Semantic Error: Attempt to connect two inputs",
            self.INVALID_DEVICE_NAME           : "***Syntax Error: Invalid device name",
            self.INVALID_DEVICE_TYPE           : "***Syntax Error: Invalid device type",
            self.INVALID_FUNCTION_NAME         : "***Syntax Error: Invalid function, please specify 'DEVICE', 'CONNECT' or 'MONITOR'",
            self.INVALID_PORT_NAME             : "***Semantic Error: Invalid port name for the device",
            self.INVALID_QUALIFIER             : "***Semantic Error: Invalid qualifier for the given device type",
            self.KEYWORD_AS_DEVICE_NAME        : "***Syntax Error: Can't use keyword as device name",
            self.MONITOR_NOT_OUTPUT            : "***Semantic Error: Attempt to monitor an input",
            self.MONITOR_PRESENT               : "***Semantic Error: Monitor already exists for the given signal",
            self.OUTPUT_TO_OUTPUT              : "***Semantic Error: Attempt to connect two outputs"
        }

        self.error_code = self.NO_ERROR
        self.error_count = 0
        self.error_code_list = [] # store the error code history, for test
        self.last_error_pos_overwrite = False # for special cases
        self.last_error_pos = None

        self.device_with_qualifier = {
            'CLOCK'  : devices.CLOCK,
            'SWITCH' : devices.SWITCH,
            'AND'    : devices.AND,
            'NAND'   : devices.NAND,
            'OR'     : devices.OR,
            'NOR'    : devices.NOR
        }
        self.device_no_qualifier = {
            'DTYPE'  : devices.D_TYPE,
            'XOR'    : devices.XOR
        }

    def move_to_next_symbol(self):
        """Get next symbol from scanner."""
        cur_line, self.last_error_pos = self.scanner.complete_current_line()
        self.symbol_type, self.symbol_id = self.scanner.get_symbol()

    def parse_network(self):
        """Parse the circuit definition file."""
        # For now just return True, so that userint and gui can run in the
        # skeleton code. When complete, should return False when there are
        # errors in the circuit definition file.
        assert self.symbol_type is None and self.symbol_id is None, \
            "parse_network() should only be called once"
        self.move_to_next_symbol()  # initialise first symbol
        if self.is_EOF():
            self.error_code = self.EMPTY_FILE
            self.error_display()
            return False
        while not self.is_EOF():
            if not self.statement():
                # First check syntax error from scanner
                if self.symbol_type == self.scanner.SYNTAX_ERROR:
                    if self.is_target_name('Unrecogonized character'):
                        self.error_code = self.BAD_CHARACTER
                    elif self.is_target_name('Number starting with 0'):
                        self.error_code = self.BAD_NUMBER
                    else:
                        self.error_code = self.BAD_COMMENT
                self.error_display()
                self.error_code = self.NO_ERROR  # restore to normal state
                # move to next '(' to resume parsing
                while (not self.is_left_paren()) and (not self.is_EOF()):
                    self.move_to_next_symbol()
        if self.error_count > 0:
            print()
            if self.error_count == 1:
                print('Parser: 1 error generated.')
            else:
                print('Parser: %d errors generated.' % (self.error_count))
            return False
        return True

    def is_left_paren(self):
        """Check whether current symbol is '('."""
        return self.symbol_type == self.scanner.PUNCTUATION and \
            self.names.get_name_string(self.symbol_id) == '('

    def is_right_paren(self):
        """Check whether current symbol is ')'."""
        return self.symbol_type == self.scanner.PUNCTUATION and \
            self.names.get_name_string(self.symbol_id) == ')'

    def is_dot(self):
        """Check whether current symbol is ')'."""
        return self.symbol_type == self.scanner.PUNCTUATION and \
            self.names.get_name_string(self.symbol_id) == '.'

    def is_keyword(self):
        """Check whether current symbol is a keyword."""
        return self.symbol_type == self.scanner.KEYWORD

    def is_name(self):
        """Check whether current symbol is a name."""
        """i.e. any valid name excluding keywords"""
        return self.symbol_type == self.scanner.NAME

    def is_number(self):
        """Check whether current symbol is a number."""
        return self.symbol_type == self.scanner.NUMBER

    def is_EOF(self):
        """Check whether current symbol is EOF."""
        return self.symbol_type == self.scanner.EOF

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
        if self.is_number():
            return str(self.symbol_id)
        return self.names.get_name_string(self.symbol_id)

    def statement(self):
        """Parse a statement, which starts with '(' and ends with ')'."""
        if not self.is_left_paren():
            self.error_code = self.EXPECT_LEFT_PAREN
            return False
        self.move_to_next_symbol()
        # Check inside the statement
        if not (self.device() or self.connect() or self.monitor()):
            if self.error_code == self.NO_ERROR:
                if self.is_right_paren():
                    self.error_code = self.EMPTY_STATEMENT
                else:
                    self.error_code = self.INVALID_FUNCTION_NAME
            return False
        # Check the last parenthesis
        if not self.is_right_paren():
            self.error_code = self.EXPECT_RIGHT_PAREN
            return False
        self.move_to_next_symbol()
        return True

    def device(self):
        """Parse a device definition."""
        if not (self.is_keyword() and self.is_target_name('DEVICE')):
            return False  # not a device, pass on to connect
        self.move_to_next_symbol()
        # The first symbol must be a device name
        new_device_ids = set()
        device_id = self.get_first_device_id(new_device_ids)
        if device_id is None: # parse failed
            return False
        # Record all other device names
        while True:
            device_id = self.get_optional_device_id(new_device_ids)
            if device_id is None:
                if self.error_code == self.NO_ERROR:
                    break
                return False
            new_device_ids.add(device_id)
        # Expecting one keyword is/are
        if not self.check_keyword_is_are():
            return False
        self.move_to_next_symbol()
        # Expecting device type (and possibly a qualifier)
        device_kind, qualifier = self.get_device_type()
        if device_kind is None: # error occured
            return False
        for device_id in new_device_ids:
            error_code = self.devices.make_device(device_id, device_kind, qualifier)
            if error_code == self.devices.INVALID_QUALIFIER:
                self.error_code = self.INVALID_QUALIFIER
                return False
        return True

    def get_first_device_id(self, new_device_ids):
        """Parse the first device name by force.
        If successful, return device_id.
        If failed, generate error code and return None."""
        if not self.is_name():
            if self.is_keyword():
                if self.get_name_string() in ('is', 'are'):
                    self.error_code = self.EMPTY_DEVICE_LIST
                else:
                    self.error_code = self.KEYWORD_AS_DEVICE_NAME
            elif self.is_right_paren() or self.is_EOF():
                self.error_code = self.EMPTY_DEVICE_LIST
            else:
                self.error_code = self.INVALID_DEVICE_NAME
            return None
        # current symbol is name
        device_id = self.symbol_id
        if self.devices.get_device(device_id) is not None:
            self.error_code = self.DEVICE_REDEFINED
            return None
        new_device_ids.add(device_id)
        self.move_to_next_symbol()
        return device_id

    def get_optional_device_id(self, new_device_ids):
        """Parse a device name optionally.
        If successful, return device_id.
        If failed, return None and (may) generate error code."""
        if not self.is_name():
            return None # no error code since it's optional
        # current symbol is name
        device_id = self.symbol_id
        if self.devices.get_device(device_id) is not None \
           or device_id in new_device_ids:
            self.error_code = self.DEVICE_REDEFINED
            return None
        new_device_ids.add(device_id)
        self.move_to_next_symbol()
        return device_id

    def check_keyword_is_are(self):
        """Check whether current symbol is keyword 'is' or 'are'."""
        if not self.is_keyword():
            if self.is_left_paren() or self.is_right_paren():
                self.error_code = self.EXPECT_KEYWORD_IS_ARE
            else:
                self.error_code = self.INVALID_DEVICE_NAME
            return False
        if self.get_name_string() not in ('is', 'are'):
            if self.get_name_string() in self.device_with_qualifier:
                self.error_code = self.EXPECT_KEYWORD_IS_ARE
            elif self.get_name_string() in self.device_no_qualifier:
                self.error_code = self.EXPECT_KEYWORD_IS_ARE
            else:
                self.error_code = self.KEYWORD_AS_DEVICE_NAME
            return False
        return True

    def get_device_type(self):
        """Parse device type (and qualifier).
        Return (None, None) if failed."""
        if self.is_right_paren():
            self.error_code = self.DEVICE_TYPE_ABSENT
            return None, None
        elif not self.is_keyword():
            self.error_code = self.INVALID_DEVICE_TYPE
            return None, None
        # Classify device type
        device_type_str = self.get_name_string()
        if device_type_str in self.device_with_qualifier:
            # Check and update the qualifier
            self.move_to_next_symbol()
            if not self.is_number():
                self.error_code = self.EXPECT_QUALIFIER
                return None, None
            device_kind = self.device_with_qualifier[device_type_str]
            qualifier = self.symbol_id
            self.move_to_next_symbol()
            return device_kind, qualifier
        elif device_type_str in self.device_no_qualifier:
            # Check there is no qualifier
            self.move_to_next_symbol()
            if self.is_number():
                self.error_code = self.EXPECT_NO_QUALIFIER
                return None, None
            device_kind = self.device_no_qualifier[device_type_str]
            qualifier = None
            return device_kind, qualifier
        else:
            self.error_code = self.INVALID_DEVICE_TYPE
            return None, None

    def device_terminal(self, monitor_mode = False):
        """Parse a device terminal and return (devicd_id, port_id).
        Return (None, None) if error occurs."""
        if not self.is_name():
            return None, None  # no error code at this point
        device_id = self.symbol_id
        device = self.devices.get_device(device_id)
        if device is None:
            self.error_code = self.DEVICE_UNDEFINED
            return None, None
        self.move_to_next_symbol()
        if self.is_dot():
            self.move_to_next_symbol()
            if not self.is_name():
                self.error_code = self.EXPECT_PORT_NAME
                return None, None
            port_id = self.symbol_id
            if port_id not in device.inputs and port_id not in device.outputs:
                self.error_code = self.INVALID_PORT_NAME
                return None, None
            # monitor mode
            if monitor_mode:
                if port_id not in device.outputs:
                    self.error_code = self.MONITOR_NOT_OUTPUT
                    return None, None
                elif (device_id, port_id) in self.monitors.monitors_dictionary:
                    self.error_code = self.MONITOR_PRESENT
                    return None, None
            self.move_to_next_symbol()
        else:
            port_id = None
            if port_id not in device.outputs:
                self.error_code = self.EXPECT_PORT_NAME_DTYPE
                return None, None
            # monitor mode
            if monitor_mode and \
               (device_id, port_id) in self.monitors.monitors_dictionary:
                self.error_code = self.MONITOR_PRESENT
                self.last_error_pos_overwrite = True
                return None, None
        return device_id, port_id

    def connect(self):
        """Parse a connection."""
        if not (self.is_keyword() and self.is_target_name('CONNECT')):
            return False  # not a connect, pass on to monitor
        self.move_to_next_symbol()
        # Check first device port
        first_device_id, first_port_id = self.device_terminal()
        if first_device_id is None:  # error occurs
            if self.error_code == self.NO_ERROR:
                self.error_code = self.EXPECT_DEVICE_TERMINAL_NAME
            return False
        # Check keyword 'to'
        if not (self.is_keyword() and self.is_target_name('to')):
            self.error_code = self.EXPECT_KEYWORD_TO
            return False
        self.move_to_next_symbol()
        # Check second device port
        second_device_id, second_port_id = self.device_terminal()
        if second_device_id is None:  # error occurs
            if self.error_code == self.NO_ERROR:
                self.error_code = self.EXPECT_DEVICE_TERMINAL_NAME
            return False
        # Make connection now (use network module)
        error_code = self.network.make_connection(first_device_id, first_port_id,
                                                 second_device_id, second_port_id)
        if error_code != self.network.NO_ERROR:
            if error_code == self.network.INPUT_CONNECTED:
                self.error_code = self.INPUT_CONNECTED
            elif error_code == self.network.INPUT_TO_INPUT:
                self.error_code = self.INPUT_TO_INPUT
            elif error_code == self.network.OUTPUT_TO_OUTPUT:
                self.error_code = self.OUTPUT_TO_OUTPUT
            else:
                raise ValueError('zao yu feng')
            self.last_error_pos_overwrite = True
            return False
        return True

    def monitor(self):
        """Parse a series of monitors."""
        if not (self.is_keyword() and self.is_target_name('MONITOR')):
            return False  # not a monitor, pass back to statement
        self.move_to_next_symbol()
        # Check first device port
        device_id, port_id = self.device_terminal(monitor_mode = True)
        if device_id is None:  # error occurs
            if self.error_code == self.NO_ERROR:
                if self.is_right_paren():
                    self.error_code = self.EMPTY_MONITOR_LIST
                else:
                    self.error_code = self.INVALID_DEVICE_NAME
            return False
        error_code = self.monitors.make_monitor(device_id, port_id)
        if error_code != self.monitors.NO_ERROR:
            raise ValueError('zao yii feng tai tm shuai le')
        # Check all the other device ports
        while True:
            device_id, port_id = self.device_terminal(monitor_mode = True)
            if device_id is None:
                if self.error_code == self.NO_ERROR:
                    return True
                return False
            error_code = self.monitors.make_monitor(device_id, port_id)
            if error_code != self.monitors.NO_ERROR:
                raise ValueError('zao yii feng tai tm shuai le')

    def error_display(self, *args):
        """Display error messages on terminal."""
        self.error_count += 1  # increment error count
        self.error_code_list.append(self.error_code)
        current_line, error_position = self.scanner.complete_current_line()
        if self.last_error_pos_overwrite:
            error_position = self.last_error_pos
            self.last_error_pos_overwrite = False
        indent = ' '*2
        print('\n[ERROR #%d]' % (self.error_count))
        print('In File "'+self.scanner.input_file.name+'", line '\
            + str(self.scanner.line_number))
        print(indent + current_line)
        print(indent + ' '*(error_position-1) + '^')
        print(self.errormsg[self.error_code] + '')
        return True
