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
    get_symbol(self): Translates the next sequence of characters and
                      returns the symbol type and ID.
    """


    def __init__(self, path, names):    '''name is an instance of Names'''
        """Open specified file and initialise reserved words and IDs."""
        try:
            self.input_file = open(path)
        except  FileNotFoundError:
            print("can't find file under this name")

        self.names = names

        symbol_type_list = [
        self.KEYWORD,
        self.NAME,
        self.NUMBER,
        self.PUNCTUATION,
        self.SYNTAX_ERROR
        self.EOF]

        keywords_list = [
        'DEVICE',
        'CONNECT',
        'MONITOR',
        'CLOCK',
        'SWITCH',
        'AND',
        'NAND',
        'OR',
        'NOR',
        'DTYPE',
        'XOR',
        'is',
        'are',
        'to',
        '(',
        ')',
        '.']
        wtf = names.lookup(keywords_list)   '''check later'''

        error_list = [
        'Unrecogonized character',
        'Number starting with 0'
        'Unterminated comment']           '''any more errors?'''
        wwtf = names.lookup(error_list)

        self.current_character = ""

    def skip_spaces(self):
        '''move to the next non-whitespace character'''
        self.current_character = self.advance()
        while self.current_character.isspace():
            self.current_character = self.advance()

    def advance(self):
        return self.input_file.read(1)

    def get_name(self):
        name = ''
        while self.current_character.isalnum() and self.current_character != "":
            number = number + self.current_character
            self.current_character = self.advance()
        return name

    def get_number(self):   '''handle cases of '00001' '''
        number = self.current_character
        while self.current_character.isdigit() and self.current_character != "":
            number = number + self.current_character
            self.current_character = self.advance()

        if number[0] == '0' and len(number) != 1:
            return -1
        else:
            return int(number)

    def skip_comment(self):
        self.current_character = self.advance()
        if self.current_character == '/':
            while (self.current_character != '/n') or (self.current_character != ''):
                self.current_character = self.advance()
            self.get_symbol(self.names)
        elif self.current_character == '*':
            self.current_character = self.advance()
            next_character = self.advance()
            while  (self.current_character != '*') or (next_character != '/') or (next_character == ''):
                self.current_character = next_character
                next_character = self.advance()
            if next_character == '':
                symbol_type = self.SYNTAX_ERROR
                symbol_id = self.names.query('Unterminated comment')
            else self.get_symbol(self.names)
        else:
            symbol_type = self.SYNTAX_ERROR
            symbol_id = self.names.query('Unrecogonized character')

    def get_symbol(self):
        """Return the symbol type and ID of the next sequence of characters.

        If the current character is not recognised, both symbol type and ID
        are assigned None. Note: this function is called again (recursively)
        if it encounters a comment or end of line.
        """

        self.skip_spaces() # current character now not whitespace
        if self.current_character.isalpha():
            name_string = self.get_name()
            if name_string in self.keywords_list:
                symbol_type = self.KEYWORD
                symbol_id = Names.query(name_string)
            else:
                symbol_type = self.NAME
                symbol_id = self.names.lookup(name_string)
        elif self.current_character.isdigit(): # a number cannot start with 0
            symbol_type = self.NUMBER
            symbol_id = self.get_number()
            if symbol_id == -1:
                symbol_type = self.SYNTAX_ERROR
                symbol_id = self.names.query('Number starting with 0')
        elif (self.current_character == '(') or (self.current_character == ')') or (self.current_character == '.')
            symbol_type = self.PUNCTUATION
            symbol_id = Names.query(self.current_character)
        elif self.current_character == ''
            symbol_type = self.EOF
            symbol_id = 3154
        elif self.current_character == '/':
            self.skip_comment()
        else: # not a valid character
            symbol_type = self.SYNTAX_ERROR
            symbol_id = self.names.query('Unrecogonized character')

        return [symbol_type, symbol_id]
