"""Map variable names and string names to unique integers.

Used in the Logic Simulator project. Most of the modules in the project
use this module either directly or indirectly.

Classes
-------
Names - maps variable names and string names to unique integers.
"""


class Names:

    """Map variable names and string names to unique integers.

    This class deals with storing grammatical keywords and user-defined words,
    and their corresponding name IDs, which are internal indexing integers. It
    provides functions for looking up either the name ID or the name string.
    It also keeps track of the number of error codes defined by other classes,
    and allocates new, unique error codes on demand.

    Parameters
    ----------
    No parameters.

    Public methods
    -------------
    unique_error_codes(self, num_error_codes): Returns a list of unique integer
                                               error codes.

    query(self, name_string): Returns the corresponding name ID for the
                        name string. Returns None if the string is not present.

    lookup(self, name_string_list): Returns a list of name IDs for each
                        name string. Adds a name if not already present.

    get_name_string(self, name_id): Returns the corresponding name string for
                        the name ID. Returns None if the ID is not present.
    """

    '''preset keywords, these should not be modified'''

    def __init__(self):
        """Initialise names list."""
        self.error_code_count = 0  # how many error codes have been declared
        self.name_list = []


    def unique_error_codes(self, num_error_codes):
        """Return a list of unique integer error codes."""
        if not isinstance(num_error_codes, int):
            raise TypeError("Expected num_error_codes to be an integer.")
        if num_error_codes <= 0:
            raise ValueError("num_error_codes should be larger than 0")
        self.error_code_count += num_error_codes
        return range(self.error_code_count - num_error_codes,
                     self.error_code_count)

    def query(self, name_string):
        """Return the corresponding name ID for name_string.

        If the name string is not present in the names list, return None.
        """
        if name_string in self.name_list:
            return self.name_list.index(name_string)
        else:
            return None

    def lookup(self, name_string_list):
        """Return a list of name IDs for each name string in name_string_list.

        If the name string is not present in the names list, add it.
        """
        if isinstance(name_string_list, list):
            name_id_list = []
            for name_string in name_string_list:
                if name_string  not in self.name_list:
                    self.name_list.append(name_string)
                name_id_list.append(self.query(name_string))
            return name_id_list
        elif name_string_list  not in self.name_list:
            self.name_list.append(name_string_list)
        return self.query(name_string_list)

    def get_name_string(self, name_id):
        """Return the corresponding name string for name_id.

        If the name_id is not an index in the names list, return None.
        """
        if not isinstance(name_id, int):
            raise TypeError('name_id should be an int')
        if 0 <= name_id < len(self.name_list):
            return self.name_list[name_id]
        else:
            return None
            
    def common_prefix_length(self, string1, string2):
        """Return the length of the longest common prefix for the two input strings."""
        min_len = min(len(string1), len(string2))
        for i in range(min_len):
            if string1[i] != string2[i]:
                return i
        return min_len
        
    def get_recommend_raw(self, target_string):
        """Return all the strings in this namespace which have non-zero common
           prefix length with the target string (may contain keywords)."""
        return [x for x in self.name_list if self.common_prefix_length(x, target_string) > 0]

