from scanner import Scanner
from names import Names
import sys

names = Names()
scanner = Scanner('full_adder.txt', names)



[symbol_type, symbol_id] = scanner.get_symbol()

while symbol_type != scanner.EOF:
    if symbol_type != scanner.NUMBER:
        content = names.get_name_string(symbol_id)
    else:
        content = symbol_id
    #print(symbol_type, symbol_id, content)

    #print(scanner.current_character,'\n',scanner.current_line)

    [current_line, error_position] = scanner.complete_current_line()
    print(current_line, '\n', '^'.rjust(error_position))
    
    
    [symbol_type, symbol_id] = scanner.get_symbol()

    


#print(symbol_type, symbol_id)
# for name in names.name_list:
#     print(name)

print(len(''))
