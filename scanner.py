"""Read the circuit definition file and translate the characters into symbols.

Used in the Logic Simulator project to read the characters in the definition
file and translate them into symbols that are usable by the parser.

Classes
-------
Scanner - reads definition file and translates characters into symbols.
"""


class Scanner:

    """Read circuit definition file and translate the characters into symbols.

    Once supplied with the path to a valid definition file, the scanner
    translates the sequence of characters in the definition file into
    symbol types and symbol IDs that the parser can use. It also skips over
    comments and irrelevant formatting characters, such as spaces and line
    breaks.

    Parameters
    ----------
    path: path to the circuit definition file.
    names: instance of the names.Names() class.

    Public methods
    -------------
    advance(self): Read the next character and set self.current_character
                   to the new value, also updates current_line

    skip_spaces(self): Move to the next non-whitespace character

    get_name(self): Read the next name symbol, returns the name string

    get_number(self): Read the next number symbol, returns the number,
                      also handles invalid numbers starting with 0

    skip_comment(self): Skip comment until the next meaningful character

    complete_current_line(self): Return the completed line and a
                                 position indicating where error occurs

    get_symbol(self): Translates the next sequence of characters and
                      returns the symbol type and ID.
    """

    def __init__(self, path, names):
        """Open specified file and initialise reserved words and IDs."""
        try:
            self.input_file = open(path)
        except FileNotFoundError:
            print("can't find file under this name")

        self.names = names

        symbol_type_list = [self.KEYWORD, self.NAME, self.NUMBER,
                            self.PUNCTUATION, self.SYNTAX_ERROR,
                            self.EOF] = range(6)

        '''initialise preserved keywords and error messages'''
        self.keywords_list = [
            'DEVICE',
            'CONNECT',
            'MONITOR',
            'CLOCK',
            'SWITCH',
            'RC',
            'AND',
            'NAND',
            'OR',
            'NOR',
            'DTYPE',
            'XOR',
            'NOT',
            'is',
            'are',
            'to',
            '(',
            ')',
            '.']
        dummy = names.lookup(self.keywords_list)

        self.error_list = [
            'Unrecogonized character',
            'Number starting with 0',
            'Unterminated comment']
        dummy = names.lookup(self.error_list)

        self.previous_lines = []        # for errormsg display
        self.line_number = 0            # also for errormsg display
        self.current_line = ''
        self.current_character = ''
        self.advance()

    def advance(self):
        if self.current_character not in ('\n', ''):
            self.current_line += self.current_character
        else:
            self.previous_lines.append(self.current_line)
            self.current_line = ''
            self.line_number += 1

        self.current_character = self.input_file.read(1)

    def skip_spaces(self):
        '''move to the next non-whitespace character'''
        while self.current_character.isspace():
            self.advance()

    def complete_current_line(self):
        # record cursor position
        current_cursor_position = self.input_file.tell()
        current_line = self.current_line
        error_position = len(current_line)
        current_character = self.current_character
        # complete reading current_line
        while current_character not in('\n', ''):
            current_line += current_character
            current_character = self.input_file.read(1)
        # move back to scan location
        self.input_file.seek(current_cursor_position)
        return [current_line, error_position]

    def get_name(self):
        name = ''
        while (self.current_character.isalnum() and
               self.current_character != ''):
            name = name + self.current_character
            self.advance()
        return name

    def get_number(self):
        number = ''
        while (self.current_character.isdigit() and
               self.current_character != ''):
            number = number + self.current_character
            self.advance()

        if number[0] == '0' and len(number) != 1:
            return -1
        else:
            return int(number)

    def skip_comment(self):
        '''comment symbol defined as '//' or '/*' and '*/',
           case 3: only '/' obtained, return unrecogonized character
           case 2: '/*' read in but no '*/', return unterminated comment
           case 1: correct comment skipped
        '''
        self.advance()
        if self.current_character not in ('/', '*'):
            return 3
        elif self.current_character == '/':
            while self.current_character not in ('\n', ''):
                self.advance()
            return 1
        elif self.current_character == '*':
            previous_character = self.current_character
            self.advance()
            while not (previous_character == '*' and
                       self.current_character == '/'):
                previous_character = self.current_character
                self.advance()
                if self.current_character == '':
                    return 2
            self.advance()
            return 1

    def get_symbol(self):
        """Return the symbol type and ID of the next sequence of characters.

        Note: this function is called again (recursively) if it encounters
        a comment or end of line.
        """

        self.skip_spaces()  # current character now not whitespace
        if self.current_character.isalpha():
            name_string = self.get_name()
            if name_string in self.keywords_list:
                symbol_type = self.KEYWORD
                symbol_id = self.names.query(name_string)
            else:
                symbol_type = self.NAME
                symbol_id = self.names.lookup(name_string)
        elif self.current_character.isdigit():  # a number cannot start with 0
            symbol_type = self.NUMBER
            symbol_id = self.get_number()
            if symbol_id == -1:
                symbol_type = self.SYNTAX_ERROR
                symbol_id = self.names.query('Number starting with 0')
        elif self.current_character in ('(', ')', '.'):
            symbol_type = self.PUNCTUATION
            symbol_id = self.names.query(self.current_character)
            self.advance()
        elif self.current_character == '':
            symbol_type = self.EOF
            symbol_id = 1  # only symbol_type is checked in parser
        elif self.current_character == '/':
            skip_successful = self.skip_comment()
            if skip_successful == 1:
                [symbol_type, symbol_id] = self.get_symbol()
            elif skip_successful == 2:
                symbol_type = self.SYNTAX_ERROR
                symbol_id = self.names.query('Unterminated comment')
            elif skip_successful == 3:
                symbol_type = self.SYNTAX_ERROR
                symbol_id = self.names.query('Unrecogonized character')
        else:  # not a valid character
            symbol_type = self.SYNTAX_ERROR
            symbol_id = self.names.query('Unrecogonized character')
            self.advance()

        return [symbol_type, symbol_id]
