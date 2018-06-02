"""Parse the definition file and build the logic network.

Used in the Logic Simulator project to analyse the syntactic and semantic
correctness of the symbols received from the scanner and then builds the
logic network.

Classes
-------
Parser - parses the definition file and builds the logic network.
"""

from collections import namedtuple # For self.ErrorTuple

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

    Optional Parameters
    -------------------
    test_mode (=False): if True, parser will operate in test mode and no
                        error messages will be displayed in terminal.

    Public methods
    --------------
    move_to_next_symbol(self): Get next symbol from scanner.

    parse_network(self): Parses the circuit definition file.

    is_target_name(self, target_name): Check if the name string corresponding
                                       to self.symbol_id is the same as the
                                       target_name.

    get_name_string(self): Get the name string of self.symbol_id.

    get_terminal_name(self, device_id, port_id): Return the terminal name from
                                                 (device_id, port_id).

    statement(self): Parse a statement, which starts with '(' and ends with ')'.

    device(self): Parse a device definition.

    add_device_location(self): Add current (linum, pos) to the dict of device
                               locations.

    get_first_device_id(self, new_device_ids): Parse the first device name
                                               by force.

    get_optional_device_id(self, new_device_ids): Parse a device name
                                                  optionally.

    check_keyword_is_are(self): Check whether current symbol is keyword 'is' or
                                'are'.

    get_device_type(self): Parse device type (and qualifier).

    get_device_type_string(self, device): Get string representation of the
                                          device's type.

    device_terminal(self, monitor_mode = False): Parse a device terminal and
                                                 return (devicd_id, port_id).

    connect(self): Parse a connection.

    monitor(self): Parse a series of monitors.

    error_display(self, *args): Display error messages on terminal.

    error_additional_info(self): Add additional information to the error
                                 display.
    """

    def __init__(self, names, devices, network, monitors, scanner, test_mode=False):
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
         self.INPUT_UNCONNECTED,
         self.INVALID_DEVICE_NAME,
         self.INVALID_DEVICE_TYPE,
         self.INVALID_FUNCTION_NAME,
         self.INVALID_PORT_NAME,
         self.INVALID_QUALIFIER,
         self.KEYWORD_AS_DEVICE_NAME,
         self.MONITOR_NOT_OUTPUT,
         self.MONITOR_PRESENT,
         self.OUTPUT_TO_OUTPUT] = names.unique_error_codes(32)

        # FOR TEST
        self.error_names = {
            self.NO_ERROR                      : "NO_ERROR",
            self.BAD_CHARACTER                 : "BAD_CHARACTER",
            self.BAD_COMMENT                   : "BAD_COMMENT",
            self.BAD_NUMBER                    : "BAD_NUMBER",
            self.DEVICE_REDEFINED              : "DEVICE_REDEFINED",
            self.DEVICE_TYPE_ABSENT            : "DEVICE_TYPE_ABSENT",
            self.DEVICE_UNDEFINED              : "DEVICE_UNDEFINED",
            self.EMPTY_DEVICE_LIST             : "EMPTY_DEVICE_LIST",
            self.EMPTY_FILE                    : "EMPTY_FILE",
            self.EMPTY_MONITOR_LIST            : "EMPTY_MONITOR_LIST",
            self.EMPTY_STATEMENT               : "EMPTY_STATEMENT",
            self.EXPECT_DEVICE_TERMINAL_NAME   : "EXPECT_DEVICE_TERMINAL_NAME",
            self.EXPECT_KEYWORD_IS_ARE         : "EXPECT_KEYWORD_IS_ARE",
            self.EXPECT_KEYWORD_TO             : "EXPECT_KEYWORD_TO",
            self.EXPECT_LEFT_PAREN             : "EXPECT_LEFT_PAREN",
            self.EXPECT_NO_QUALIFIER           : "EXPECT_NO_QUALIFIER",
            self.EXPECT_PORT_NAME              : "EXPECT_PORT_NAME",
            self.EXPECT_PORT_NAME_DTYPE        : "EXPECT_PORT_NAME_DTYPE",
            self.EXPECT_QUALIFIER              : "EXPECT_QUALIFIER",
            self.EXPECT_RIGHT_PAREN            : "EXPECT_RIGHT_PAREN",
            self.INPUT_CONNECTED               : "INPUT_CONNECTED",
            self.INPUT_TO_INPUT                : "INPUT_TO_INPUT",
            self.INPUT_UNCONNECTED             : "INPUT_UNCONNECTED",
            self.INVALID_DEVICE_NAME           : "INVALID_DEVICE_NAME",
            self.INVALID_DEVICE_TYPE           : "INVALID_DEVICE_TYPE",
            self.INVALID_FUNCTION_NAME         : "INVALID_FUNCTION_NAME",
            self.INVALID_PORT_NAME             : "INVALID_PORT_NAME",
            self.INVALID_QUALIFIER             : "INVALID_QUALIFIER",
            self.KEYWORD_AS_DEVICE_NAME        : "KEYWORD_AS_DEVICE_NAME",
            self.MONITOR_NOT_OUTPUT            : "MONITOR_NOT_OUTPUT",
            self.MONITOR_PRESENT               : "MONITOR_PRESENT",
            self.OUTPUT_TO_OUTPUT              : "OUTPUT_TO_OUTPUT"
        }

        self.errormsg = {
            self.NO_ERROR                      : "NO_ERROR",
            self.BAD_CHARACTER                 : _("***Syntax Error: Invalid character"),
            self.BAD_COMMENT                   : _("***Syntax Error: Unterminated /* comment"),
            self.BAD_NUMBER                    : _("***Syntax Error: Number has too many leading zeros"),
            self.DEVICE_REDEFINED              : _("***Semantic Error: Device '{symbol_name}' is already defined"),
            self.DEVICE_TYPE_ABSENT            : _("***Syntax Error: Expected device type after 'is'/'are'"),
            self.DEVICE_UNDEFINED              : _("***Semantic Error: Device '{symbol_name}' is not defined"),
            self.EMPTY_DEVICE_LIST             : _("***Syntax Error: Device list is empty"),
            self.EMPTY_FILE                    : _("***Semantic Error: File is empty"),
            self.EMPTY_MONITOR_LIST            : _("***Syntax Error: Monitor list is empty"),
            self.EMPTY_STATEMENT               : _("***Syntax Error: Statement is empty"),
            self.EXPECT_DEVICE_TERMINAL_NAME   : _("***Syntax Error: Expected a device terminal name (device_name + port_name)"),
            self.EXPECT_KEYWORD_IS_ARE         : _("***Syntax Error: Expected keyword 'is'/'are'"),
            self.EXPECT_KEYWORD_TO             : _("***Syntax Error: Expected keyword 'to'"),
            self.EXPECT_LEFT_PAREN             : _("***Syntax Error: Expected left parenthesis '('"),
            self.EXPECT_NO_QUALIFIER           : _("***Syntax Error: Expected no qualifier for the device type '{device_type}'"),
            self.EXPECT_PORT_NAME              : _("***Syntax Error: Expected a valid port name after '.'"),
            self.EXPECT_PORT_NAME_DTYPE        : _("***Semantic Error: DTYPE device should have a port name"),
            self.EXPECT_QUALIFIER              : _("***Syntax Error: Expected a qualifier for the device type '{device_type}'"),
            self.EXPECT_RIGHT_PAREN            : _("***Syntax Error: Expected right parenthesis ')'"),
            self.INPUT_CONNECTED               : _("***Semantic Error: Input '{input_name}' is already connected to output '{output_name}'"),
            self.INPUT_TO_INPUT                : _("***Semantic Error: Attempt to connect two inputs"),
            self.INPUT_UNCONNECTED             : _("***Semantic Error: Some input ports are not connected to any outputs"),
            self.INVALID_DEVICE_NAME           : _("***Syntax Error: Invalid device name '{symbol_name}'"),
            self.INVALID_DEVICE_TYPE           : _("***Syntax Error: Invalid device type '{device_type}'"),
            self.INVALID_FUNCTION_NAME         : _("***Syntax Error: Invalid function '{symbol_name}', please specify 'DEVICE', 'CONNECT' or 'MONITOR'"),
            self.INVALID_PORT_NAME             : _("***Semantic Error: Invalid port name '{port_name}' for the device '{device_name}' ({device_type_full})"),
            self.INVALID_QUALIFIER             : _("***Semantic Error: Invalid qualifier for the device type '{device_type}'"),
            self.KEYWORD_AS_DEVICE_NAME        : _("***Syntax Error: Can't use keyword '{symbol_name}' as device name"),
            self.MONITOR_NOT_OUTPUT            : _("***Semantic Error: Attempt to monitor an input"),
            self.MONITOR_PRESENT               : _("***Semantic Error: Monitor already exists for the signal '{terminal_name}'"),
            self.OUTPUT_TO_OUTPUT              : _("***Semantic Error: Attempt to connect two outputs")
        }
        self.errormsg_format_dict = {} # used for str.format(**dict)

        self.error_code = self.NO_ERROR
        self.error_count = 0

        # For errormsg display
        self.Location = namedtuple('Location', 'linum, pos')
        self.device_locations = {} # id -> location
        self.connect_locations = {}
        self.monitor_locations = {}

        # For error cursor position correction
        self.last_error_pos_overwrite = False
        self.last_error_pos = None
        self.last_error_linum = None

        # For testing purpose
        self.test_mode = test_mode
        self.ErrorTuple = namedtuple('ErrorTuple', 'error, linum, pos')
        self.error_tuple_list = []

        self.device_with_qualifier = {
            'CLOCK'  : devices.CLOCK,
            'SWITCH' : devices.SWITCH,
            'AND'    : devices.AND,
            'NAND'   : devices.NAND,
            'OR'     : devices.OR,
            'NOR'    : devices.NOR,
            'RC'     : devices.RC
        }
        self.device_no_qualifier = {
            'DTYPE'  : devices.D_TYPE,
            'XOR'    : devices.XOR,
            'NOT'    : devices.NOT
        }

    def move_to_next_symbol(self):
        """Get next symbol from scanner."""
        self.last_error_pos = len(self.scanner.current_line)
        self.last_error_linum = self.scanner.line_number
        self.symbol_type, self.symbol_id = self.scanner.get_symbol()
        self.errormsg_format_dict['symbol_name'] = self.get_name_string()

    def parse_network(self):
        """Parse the circuit definition file."""
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
                    self.last_error_pos_overwrite = False # cannot use previous pos
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
        if self.error_count == 0: # only check network when no other errors
            unconnected_inputs = self.network.find_unconnected_inputs()
            if len(unconnected_inputs) > 0:
                print('The following inputs are not connected to any outputs:')
                for i, (device_id, input_id) in enumerate(unconnected_inputs):
                    terminal_name = self.get_terminal_name(device_id, input_id)
                    print('  [%d] %s' % (i + 1, terminal_name))
                print('Please check your circuit connection before running the parser again.')
                self.error_count = 1
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

    def get_terminal_name(self, device_id, port_id):
        """Return the terminal name from (device_id, port_id)."""
        device_name = self.names.get_name_string(device_id)
        assert device_name is not None, "device_id not exist"
        if port_id is None:
            return device_name
        port_name = self.names.get_name_string(port_id)
        return device_name + '.' + port_name

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
            self.last_error_pos_overwrite = True
            self.last_error_pos += 1
            return False
        self.move_to_next_symbol()
        return True

    def device(self):
        """Parse a device definition."""
        if self.error_code != self.NO_ERROR: # make sure no error has occured
            return False
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
                self.last_error_pos_overwrite = True
                return False
        return True

    def add_device_location(self):
        """Add current (linum, pos) to the dict of device locations."""
        self.device_locations[self.symbol_id] = \
        self.Location(self.scanner.line_number, len(self.scanner.current_line))

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
        self.add_device_location()
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
        self.add_device_location()
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

        device_type_str = self.get_name_string()
        self.errormsg_format_dict['device_type'] = device_type_str

        if self.is_right_paren():
            self.error_code = self.DEVICE_TYPE_ABSENT
            self.last_error_pos_overwrite = True
            return None, None
        elif not self.is_keyword():
            self.error_code = self.INVALID_DEVICE_TYPE
            return None, None
        # Classify device type
        if device_type_str in self.device_with_qualifier:
            # Check and update the qualifier
            self.move_to_next_symbol()
            if not self.is_number():
                self.error_code = self.EXPECT_QUALIFIER
                self.last_error_pos_overwrite = True
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
            line, linum = self.scanner.complete_current_line()
            return None, None

    def get_device_type_string(self, device):
        """Get string representation of the device's type."""
        if device is None:
            return None
        device_kind = device.device_kind
        device_type_str = self.names.get_name_string(device_kind)
        if device_kind in self.devices.gate_types and device_kind != self.devices.XOR:
            device_type_str += ' ' + str(len(device.inputs))
        elif device_kind == self.devices.CLOCK:
            device_type_str += ' ' + str(device.clock_half_period)
        return device_type_str

    def device_terminal(self, monitor_mode = False):
        """Parse a device terminal and return (devicd_id, port_id).
        Return (None, None) if error occurs."""
        if not self.is_name():
            return None, None  # no error code at this point
        device_id = self.device_id = self.symbol_id
        device = self.devices.get_device(device_id)
        self.errormsg_format_dict['device_name'] = self.get_name_string()
        self.errormsg_format_dict['device_type_full'] = self.get_device_type_string(device)
        if device is None:
            self.error_code = self.DEVICE_UNDEFINED
            return None, None
        self.move_to_next_symbol()
        if self.is_dot():
            self.move_to_next_symbol()
            if self.is_target_name('to') or self.is_right_paren():
                self.error_code = self.EXPECT_PORT_NAME
                self.last_error_pos_overwrite = True
                return None, None
            port_id = self.port_id = self.symbol_id
            self.errormsg_format_dict['port_name'] = self.get_name_string()
            if port_id not in device.inputs and port_id not in device.outputs:
                self.error_code = self.INVALID_PORT_NAME
                return None, None
            # monitor mode
            if monitor_mode:
                if port_id not in device.outputs:
                    self.error_code = self.MONITOR_NOT_OUTPUT
                    return None, None
                elif (device_id, port_id) in self.monitors.monitors_dictionary:
                    self.errormsg_format_dict['terminal_name'] = \
                        self.get_terminal_name(device_id, port_id)
                    self.error_code = self.MONITOR_PRESENT
                    return None, None
                else:
                    self.monitor_locations[(device_id, port_id)] = \
                    self.Location(self.scanner.line_number, len(self.scanner.current_line))
            self.move_to_next_symbol()
        else:
            port_id = self.port_id = None
            if port_id not in device.outputs:
                self.error_code = self.EXPECT_PORT_NAME_DTYPE
                self.last_error_pos_overwrite = True
                return None, None
            # monitor mode
            if monitor_mode:
                if (device_id, port_id) in self.monitors.monitors_dictionary:
                    self.errormsg_format_dict['terminal_name'] = \
                        self.get_terminal_name(device_id, port_id)
                    self.error_code = self.MONITOR_PRESENT
                    self.last_error_pos_overwrite = True
                    return None, None
                else:
                    self.monitor_locations[(device_id, port_id)] = \
                    self.Location(self.last_error_linum, self.last_error_pos)
        return device_id, port_id

    def connect(self):
        """Parse a connection."""
        if self.error_code != self.NO_ERROR: # make sure no error has occured
            return False
        if not (self.is_keyword() and self.is_target_name('CONNECT')):
            return False  # not a connect, pass on to monitor
        self.move_to_next_symbol()
        # Check first device port
        first_device_id, first_port_id = self.device_terminal()
        if first_device_id is None:  # error occurs
            if self.error_code == self.NO_ERROR:
                self.error_code = self.EXPECT_DEVICE_TERMINAL_NAME
            return False
        first_location = self.Location(self.last_error_linum, self.last_error_pos)
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
        second_location = self.Location(self.last_error_linum, self.last_error_pos)
        # Make connection now (use network module)
        error_code = self.network.make_connection(first_device_id, first_port_id,
                                                 second_device_id, second_port_id)
        if error_code != self.network.NO_ERROR:
            if error_code == self.network.INPUT_CONNECTED:
                self.error_code = self.INPUT_CONNECTED
                # for errormsg display
                first_device = self.devices.get_device(first_device_id)
                if first_port_id in first_device.inputs:
                    input_device_id = first_device_id
                    input_port_id = first_port_id
                    input_location = first_location
                else:
                    input_device_id = second_device_id
                    input_port_id = second_port_id
                    input_location = second_location
                self.errormsg_format_dict['input_name'] = \
                    self.get_terminal_name(input_device_id, input_port_id)
                output_device_id, output_port_id = \
                    self.network.get_connected_output(input_device_id, input_port_id)
                self.errormsg_format_dict['output_name'] = \
                    self.get_terminal_name(output_device_id, output_port_id)
                self.device_id, self.port_id = input_device_id, input_port_id
                self.last_error_linum, self.last_error_pos = input_location
            elif error_code == self.network.INPUT_TO_INPUT:
                self.error_code = self.INPUT_TO_INPUT
            elif error_code == self.network.OUTPUT_TO_OUTPUT:
                self.error_code = self.OUTPUT_TO_OUTPUT
            else:
                raise ValueError('zao yu feng')
            self.last_error_pos_overwrite = True
            return False
        self.connect_locations[(first_device_id, first_port_id)] = first_location
        self.connect_locations[(second_device_id, second_port_id)] = second_location
        return True

    def monitor(self):
        """Parse a series of monitors."""
        if self.error_code != self.NO_ERROR: # make sure no error has occured
            return False
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
        current_line, error_position = self.scanner.complete_current_line()
        line_number = self.scanner.line_number
        if self.last_error_pos_overwrite:
            error_position = self.last_error_pos
            line_number = self.last_error_linum
            self.last_error_pos_overwrite = False
        ###TEST BEGIN###
        if self.test_mode:
            error_tuple = self.ErrorTuple(self.error_names[self.error_code], line_number, error_position)
            self.error_tuple_list.append(error_tuple)
            return True
        ###TEST END###
        indent = ' '*2
        print(_('\n[ERROR #%d]') % (self.error_count))
        print(_('In File "')+self.scanner.input_file.name+_('", line ')\
            + str(line_number))
        print(indent + current_line)
        print(indent + ' '*(error_position-1) + '^')
        print(self.errormsg[self.error_code].format(**self.errormsg_format_dict))
        self.error_additional_info()
        return True

    def error_additional_info(self):
        """Add additional information to the error display."""
        indent = ' '*2
        if self.error_code in (self.DEVICE_REDEFINED, self.MONITOR_PRESENT):
            if self.error_code == self.DEVICE_REDEFINED:
                location = self.device_locations[self.symbol_id]
            else:
                location = self.monitor_locations[(self.device_id, self.port_id)]
            print('-----------------------------------------')
            print(_('Previous definition here, in line'), location.linum)
            if location.linum < self.scanner.line_number:
                line = self.scanner.previous_lines[location.linum]
            else:
                line, pos = self.scanner.complete_current_line()
            print(indent + line)
            print(indent + ' '*(location.pos-1) + '^')
        elif self.error_code == self.INPUT_CONNECTED:
            location = self.connect_locations[(self.device_id, self.port_id)]
            print('-----------------------------------------')
            print(_('Previous connection here, in line'), location.linum)
            if location.linum < self.scanner.line_number:
                line = self.scanner.previous_lines[location.linum]
            else:
                line, pos = self.scanner.complete_current_line()
            print(indent + line)
            print(indent + ' '*(location.pos-1) + '^')
