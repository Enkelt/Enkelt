# coding=utf-8

# Enkelt 3.1
# Copyright 2018, 2019, 2020 Edvard Busck-Nielsen, 2019 Morgan Willliams.
# This file is part of Enkelt.
#
#     Enkelt is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     Foobar is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with Enkelt.  If not, see <https://www.gnu.org/licenses/>.

import sys
import re
import os


# ####### #
# CLASSES #
# ####### #


class ErrorClass:
    def __init__(self, error_msg):
        self.error = error_msg
        self.error_list = error_msg.split()
        self.errors = get_errors()

    def set_error(self, new_error_msg):
        self.error = new_error_msg

    def get_error_type(self):
        for part in self.errors:
            if 'Error' in part:
                return self.errors[part]
        return ''

    def get_error_message_data(self):
        if self.error == "module 'final_transpiled' has no attribute '__Enkelt__'":
            return 'IGNORED'

        from googletrans import Translator

        translator = Translator()

        error_type = self.get_error_type()

        if error_type == '':
            self.set_error(self.error.replace("Traceback (most recent call last):", ''))
            self.set_error(self.error.replace('File "tmp.py", ', ''))
            self.set_error(self.error.replace(", in <module>", ''))
            return translator.translate(self.error, dest='sv').text.replace('linje', 'rad').replace(
                'final_transpiled.py, ', '')
        else:
            # Get line number
            for index, item in enumerate(self.error_list):
                if 'line' in item and has_numbers(self.error_list[index + 1]):
                    line_index = index + 1
                    return error_type + " (vid rad " + str(int(self.error_list[line_index][:-1]) - 4) + ')'
            return error_type


# ############################################### #
# Modules Used When Executing The Transpiled Code #
# ############################################### #

def enkelt_print(data):
    print(translate_output_to_swedish(data))


# ############ #
# Main Methods #
# ############ #

def translate_output_to_swedish(data):
    data = str(data)
    return data.replace("True", "Sant").replace("False", "Falskt").replace("<class \'float\'>", "decimaltal").replace(
        "<class \'str\'>", "sträng").replace("<class \'int\'>", "heltal").replace("<class \'list\'>", "lista").replace(
        "<class \'dict\'>", "lexikon").replace("<class \'bool\'>", "boolesk").replace("<class \'NoneType\'>", "inget")


def check_for_updates(version_nr):
    import urllib.request
    import json

    global repo_location

    url = repo_location + '/master/VERSION.json'

    response = urllib.request.urlopen(url)

    data_store = json.loads(response.read())

    if data_store['version'] > float(version_nr):
        print('Uppdatering tillgänglig! Du har version ' + str(
            version_nr) + ' men du kan uppdatera till Enkelt version ' + str(data_store['version']))


def transpile_library_code(library_code, library_name):
    global final
    global source_code
    global is_extension

    for line in library_code:
        if line != '\n':
            data = fix_up_code_line(line)

            data = lex(data)

            for token_index, _ in enumerate(data):
                if data[token_index][0] == 'USER_FUNCTION':
                    data[token_index][1] = library_name + '.' + data[token_index][1]
                    user_functions[-1] = library_name + '.' + user_functions[-1]

            if is_extension:
                source_code.append(line)
            else:
                parse(data, 0)

            if is_developer_mode:
                print('--DEV: transpile_library_code, line')
                print(line)
                print('--DEV: transpile_library_code, lexed line')
                print(data)

            final.append(''.join(source_code))
            final.append('\n')
            source_code = []


def get_import(file_or_code, is_file, library_name):
    global imported_libraries
    global source_code
    global final
    global user_functions

    imported_libraries.append(library_name)

    library_code = file_or_code

    if is_file:
        with open(file_or_code) as library_file:
            library_code = library_file.readlines()

    while '' in library_code:
        library_code.pop(library_code.index(''))

    transpile_library_code(library_code, library_name)


def import_library_or_extension(library_name):
    import urllib.request
    from urllib.error import HTTPError

    global enkelt_script_path
    global web_import_location

    # Checks if the library/extension is user-made (i.e. local not remote).
    import_file = ''.join(enkelt_script_path.split('/')[:-1]) + '/' + library_name + '.e'
    extension_file = import_file[:-2]+'.epy'

    if os.path.isfile(import_file):
        get_import(import_file, True, library_name)

    elif os.path.isfile(extension_file):
        get_import(extension_file, True, library_name)

    else:
        # The library/extension is remote (i.e. needs to be fetched)
        url = web_import_location + library_name + '.e'

        try:
            response = urllib.request.urlopen(url)
            module_code = response.read().decode('utf-8')

            module_code = module_code.split('\n')

            get_import(module_code, False, library_name)

        except HTTPError:
            url = url[:-2] + '.epy'

            try:
                response = urllib.request.urlopen(url)
                module_code = response.read().decode('utf-8')

                module_code = module_code.split('\n')

                get_import(module_code, False, library_name)
            except HTTPError:
                print('Error! Kunde inte importera ' + library_name)


def translate_clear():
    if os.name == 'nt':
        return 'cls'
    return 'clear'


def has_numbers(input_string):
    return any(char.isdigit() for char in input_string)


def get_errors():
    return {
        'SyntaxError': 'Syntaxfel',
        'IndexError': 'Indexfel',
        'TypeError': 'Typfel',
        'ValueError': 'Värdefel',
        'NameError': 'Namnfel',
        'ZeroDivisionError': 'Nolldelningsfel',
        'AttributeError': 'Attributfel'
    }


def functions_and_keywords():
    return {
        'functions': {
            # Functions with no statuses in parse()
            'skriv': 'print',
            'in': 'input',
            'Text': 'str',
            'Nummer': 'int',
            'Decimal': 'float',
            'Bool': 'bool',
            'längd': 'len',
            'till': 'append',
            'bort': 'pop',
            'sortera': 'sorted',
            'slump': '__import__("random").randint',
            'slumpval': '__import__("random").choice',
            'blanda': '__import__("random").shuffle',
            'området': 'range',
            'abs': 'abs',
            'lista': 'list',
            'ärnum': 'isdigit',
            'runda': 'round',
            'versal': 'upper',
            'gemen': 'lower',
            'ersätt': 'replace',
            'infoga': 'insert',
            'index': 'index',
            'dela': 'split',
            'foga': 'join',
            'typ': 'type',
            'sin': '__import__("math").sin',
            'cos': '__import__("math").cos',
            'tan': '__import__("math").tan',
            'potens': '__import__("math").pow',
            'asin': '__import__("math").asin',
            'atan': '__import__("math").atan',
            'acos': '__import__("math").acos',
            'tak': '__import__("math").ceil',
            'golv': '__import__("math").floor',
            'log': '__import__("math").log',
            'kvadratrot': '__import__("math").sqrt',
            'grader': '__import__("math").degrees',
            'radianer': '__import__("math").radians',
            'fakultet': '__import__("math").factorial',
            'datum': '__import__("datetime").date',
            'veckodag': 'weekday',
            'läs': 'read',
            'överför': 'write',
            'epok': '__import__("time").time',
            'tid': '__import__("time").ctime',
            'nu': '__import__("datetime").datetime.now',
            'idag': '__import__("datetime").date.today',
            'värden': 'values',
            'element': 'elements',
            'numrera': 'enumerate',
            'töm': 'os.system("' + translate_clear() + '"',
            # Functions with statuses in parse()
            'om': 'if',
            'anom': 'elif',
            'öppna': 'with open',
            'för': 'for',
            'medan': 'while'
        },
        'keywords': {
            'Sant': 'True',
            'Falskt': 'False',
            'inom': ' in ',
            'bryt': 'break',
            'fortsätt': 'continue',
            'returnera': 'return ',
            'inte': 'not',
            'passera': 'pass',
            'matte_e': '__import__("math").e',
            'matte_pi': '__import__("math").pi',
            'år': 'year',
            'månad': 'month',
            'dag': 'day',
            'timme': 'hour',
            'minut': 'minute',
            'sekund': 'second',
            'mikrosekund': 'microsecond',
            'annars': 'else',
            'och': ' and ',
            'eller': ' or ',
            'som': ' as ',
            'klass': 'class ',
        },
    }


def operator_symbols():
    return ['+', '-', '*', '/', '%', '<', '>', '=', '!', '.', ',', ')', ':', ';']


def forbidden_variable_names():
    return ['in', 'str', 'int', 'list', 'num', 'matte_e', 'matte_pi', 'själv']


def translate_function(func):
    function_translations = functions_and_keywords()['functions']

    return function_translations[func] if func in function_translations.keys() else 'error'


def transpile_function(func):
    global source_code

    source_code.append(translate_function(func) + '(')


def translate_keyword(keyword):
    keyword_translations = functions_and_keywords()['keywords']

    return keyword_translations[keyword] if keyword in keyword_translations.keys() else 'error'


def transpile_keyword(keyword):
    global source_code

    source_code.append(translate_keyword(keyword))


# Parses the code tree and transpiles to python.
def parse(lexed, token_index):
    global source_code
    global indent_layers
    global is_if
    global is_math
    global is_for
    global look_for_loop_ending
    global needs_start_statuses
    global is_file_open
    global is_extension

    forbidden = forbidden_variable_names()

    global is_console_mode

    is_comment = False

    token_type = str(lexed[token_index][0])
    token_val = lexed[token_index][1]

    needs_start = False

    needs_start = needs_start_statuses[-1]

    if indent_layers and token_index == 0:
        for _ in indent_layers:
            source_code.append('\t')
    if token_type == 'COMMENT':
        source_code.append(token_val)
        is_comment = True
    elif token_type == 'FUNCTION':
        # Specific functions & function cases that ex. required updating of statuses.
        if token_val == 'skriv' and is_console_mode is False:
            source_code.append('Enkelt.enkelt_print(')
        elif token_val == 'matte':
            is_math = True
        elif token_val == 'om' or token_val == 'anom':
            source_code.append(translate_function(token_val) + ' ')
            is_if = True
        elif token_val == 'öppna':
            transpile_function(token_val)
            needs_start_statuses.append(True)
            is_file_open = True
        elif token_val == 'för' or token_val == 'medan':
            source_code.append(translate_function(token_val) + ' ')
            look_for_loop_ending = True
            if token_val == 'för':
                is_for = True
        # Every other function get's transpiled in the same way.
        else:
            transpile_function(token_val)
    elif token_type == 'VAR':
        if token_val not in forbidden:
            source_code.append(token_val)
        elif token_val == 'själv':
            source_code.append('self')
        else:
            print('Error namnet ' + token_val + " är inte tillåtet som variabelnamn!")
    elif token_type == 'STRING':
        if is_file_open and len(token_val) <= 2:
            token_val = token_val.replace('l', 'r').replace('ö', 'w')
        source_code.append('"' + token_val + '"')
    elif token_type == 'PNUMBER' or token_type == 'NNUMBER':
        source_code.append(token_val)
    elif token_type == 'IMPORT' or token_type == 'EXTENSION':
        if token_type == 'EXTENSION':
            is_extension = True
        import_library_or_extension(token_val)
    elif token_type == 'OPERATOR':
        # Special operator cases
        if is_if and token_val == ')':
            is_if = False
            needs_start_statuses.append(True)
        elif is_math and token_val == ')':
            is_math = False
        elif is_for and token_val == ';':
            is_for = False
        elif look_for_loop_ending and token_val == ')':
            look_for_loop_ending = False
            needs_start_statuses.append(True)
        # All other operators just gets appended to the source
        else:
            source_code.append(token_val)
    elif token_type == 'LIST_START' or token_type == 'LIST_END':
        source_code.append(token_val)
    elif token_type == 'START':
        if needs_start is False:
            source_code.append(token_val)
        elif len(lexed) - 1 == token_index:
            source_code.append(':')
        else:
            source_code.append(':' + '\n')
        if needs_start:
            indent_layers.append("x")
    elif token_type == 'END':
        if needs_start is False:
            source_code.append(token_val)
        else:
            needs_start_statuses.pop(-1)
            indent_layers.pop(-1)
            if len(lexed) - 1 != token_index:
                source_code.append('\n')
                for _ in indent_layers:
                    source_code.append('\t')
    elif token_type == 'KEYWORD' or token_type == 'BOOL':
        # Specific keywords & keyword cases that ex. required updating of statuses.
        if token_val == 'annars':
            source_code.append(translate_keyword(token_val))
            needs_start_statuses.append(True)
        # Every other keyword get's transpiled in the same way.
        else:
            transpile_keyword(token_val)
    elif token_type == 'USER_FUNCTION':
        # Needed when functions are imported functions
        token_val = token_val.replace('.', '__IMPORTED__')
        source_code.append('def ' + token_val + '(')
        needs_start_statuses.append(True)
    elif token_type == 'USER_FUNCTION_CALL':
        # Needed when functions are imported functions
        token_val = token_val.replace('.', '__IMPORTED__')
        source_code.append(token_val + '(')
    elif token_type == 'CLASS':
        source_code.append(' ' + token_val)
        needs_start_statuses.append(True)

    # Recursively calls parse() when there is more code to parse
    if len(lexed) - 1 >= token_index + 1 and is_comment is False:
        parse(lexed, token_index + 1)

    return source_code


def lex(line):
    if line[0] == '#':
        return ['COMMENT', line]

    global user_functions
    global imported_libraries

    operators = operator_symbols()

    tmp_data = ''
    is_string = False
    is_var = False
    is_function = False
    is_class = False
    is_import = False
    is_extension_mode = False
    lexed_data = []
    last_action = ''
    might_be_negative_num = False
    data_index = -1

    for chr_index, char in enumerate(line):
        if is_import and char != ' ':
            tmp_data += char
        if is_import and chr_index == len(line) - 1:
            lexed_data.append(['IMPORT' if is_extension_mode is False else 'EXTENSION', tmp_data])
            is_import = False
            is_extension_mode = False
            tmp_data = ''
        if is_function and char not in operators and char != '(':
            tmp_data += char
        elif is_function and char == '(':
            lexed_data.append(['USER_FUNCTION', tmp_data])
            user_functions.append(tmp_data)
            tmp_data = ''
            is_function = False
        elif char == '{' and is_var is False:
            if is_class:
                lexed_data.append(['CLASS', tmp_data])
                tmp_data = ''
                is_class = False
            lexed_data.append(['START', char])
        elif char == '}':
            lexed_data.append(['END', char])
        elif char == '#' and is_string is False:
            break
        elif char.isdigit() and is_string is False and is_var is False:
            if might_be_negative_num or last_action == 'NNUMBER':
                if last_action == 'NNUMBER':
                    lexed_data[data_index - 1] = ['NNUMBER', lexed_data[data_index - 1][1] + char]
                else:
                    lexed_data.append(['NNUMBER', '-' + char])
                    data_index += 1
                last_action = 'NNUMBER'
                might_be_negative_num = False
            else:
                if last_action == 'PNUMBER':
                    lexed_data[-1] = ['PNUMBER', lexed_data[-1][1] + char]
                else:
                    lexed_data.append(['PNUMBER', char])
                    data_index += 1

                last_action = 'PNUMBER'
        elif char == '-' and is_string is False:
            might_be_negative_num = True
        else:
            last_action = ''
            if char == '"' and is_string is False:
                is_string = True
                tmp_data = ''
            elif char == '"' and is_string:
                is_string = False
                lexed_data.append(['STRING', tmp_data])
                tmp_data = ''
            elif is_string:
                tmp_data += char
            else:
                if char == '[' and is_var is False:
                    lexed_data.append(['LIST_START', '['])
                elif char == ']' and is_var is False:
                    lexed_data.append(['LIST_END', ']'])
                else:
                    if char == '$':
                        is_var = True
                        tmp_data = ''
                    elif is_var:
                        if char != ' ' and char != '=' and char not in operators and char != '[' and char != ']' and char != '{' and char != '}':
                            tmp_data += char
                            if len(line) - 1 == chr_index:
                                is_var = False
                                lexed_data.append(['VAR', tmp_data])
                                tmp_data = ''
                        elif char == '=' or char in operators:
                            is_var = False
                            lexed_data.append(['VAR', tmp_data])
                            lexed_data.append(['OPERATOR', char])
                            tmp_data = ''
                        elif char == '[':
                            is_var = False
                            lexed_data.append(['VAR', tmp_data])
                            lexed_data.append(['LIST_START', '['])
                            tmp_data = ''
                        elif char == ']':
                            is_var = False
                            lexed_data.append(['VAR', tmp_data])
                            lexed_data.append(['LIST_END', '['])
                            tmp_data = ''
                        elif char == '{':
                            is_var = False
                            lexed_data.append(['VAR', tmp_data])
                            lexed_data.append(['START', char])
                            tmp_data = ''
                    elif char in operators and tmp_data not in imported_libraries:
                        lexed_data.append(['OPERATOR', char])
                    elif char in imported_libraries and char != '.':
                        lexed_data.append(['OPERATOR', char])
                    elif char in imported_libraries and char == '.':
                        tmp_data += char
                    else:
                        if tmp_data == 'Sant' or tmp_data == 'Falskt':
                            lexed_data.append(['BOOL', tmp_data])
                            tmp_data = ''
                        else:
                            if char == '(' and translate_function(tmp_data) != 'error':
                                if tmp_data == 'matte':
                                    tmp_data = 'Nummer'
                                lexed_data.append(['FUNCTION', tmp_data])
                                tmp_data = ''
                            elif char == '(' and tmp_data in user_functions or char == '(' and translate_function(
                                    tmp_data) == 'error':
                                lexed_data.append(['USER_FUNCTION_CALL', tmp_data])
                                tmp_data = ''
                            else:
                                if is_import is False:
                                    tmp_data += char
                                if tmp_data == 'Sant' or tmp_data == 'Falskt':
                                    lexed_data.append(['BOOL', tmp_data])
                                    tmp_data = ''
                                else:
                                    if translate_keyword(tmp_data) != 'error':
                                        lexed_data.append(['KEYWORD', tmp_data])
                                        tmp_data = ""
                                    elif tmp_data == 'def':
                                        is_function = True
                                        tmp_data = ''
                                    elif tmp_data == 'var':
                                        is_var = True
                                        tmp_data = ''
                                    elif tmp_data == 'importera':
                                        is_import = True
                                        tmp_data = ''
                                    elif tmp_data == 'utöka':
                                        is_extension_mode = True
                                        is_import = True
                                        tmp_data = ''
                                    elif tmp_data == 'matte_e' or tmp_data == 'töm' and line[-3:] == 'töm':
                                        lexed_data.append(['KEYWORD', tmp_data])
                                        tmp_data = ''
                                    elif tmp_data == 'klass':
                                        lexed_data.append(['KEYWORD', tmp_data])
                                        tmp_data = ''
                                        is_class = True

    return lexed_data


def fix_up_code_line(statement):
    global is_extension

    statement = statement.replace('\n', '').replace("'", '"').replace('\\"', '|-ENKELT_ESCAPED_QUOTE-|').replace('\\', '|-ENKELT_ESCAPED_BACKSLASH-|')
    if is_extension is False:
        statement = statement.replace('\t', '')

    current_line = ''
    is_string = False
    is_import = False

    for char in statement:
        if char == ' ' and is_string is False and is_import is False:
            continue
        elif char == '"' and is_string:
            is_string = False
            current_line += char
        elif char == '"' and is_string is False:
            is_string = True
            current_line += char
        else:
            current_line += char

        if current_line == 'importera':
            is_import = True

    return current_line


def fix_up_and_prepare_transpiled_code():
    global final

    # Removes unnecessary tabs
    for line_index, line in enumerate(final):
        tmp_line = list(line)
        chars_started = False
        for char_index, char in enumerate(tmp_line):
            if char != '\t' and char != '\n' and chars_started is False:
                chars_started = True
            elif chars_started and char == '\t' and char_index > 0:
                tmp_line[char_index] = ' '

        final[line_index] = ''.join(tmp_line)

    # Turn = = into == and ! = into != and + = into +=
    final = list(''.join(final).replace('= =', '==').replace('! =', '==').replace('+ =', '+='))

    # Fixes escaped (\) characters
    final = list(''.join(final).replace('|-ENKELT_ESCAPED_QUOTE-|', '\\"').replace('|-ENKELT_ESCAPED_BACKSLASH-|', '\\'))

    # Remove empty lines from final
    final = list(re.sub(r'\n\s*\n', '\n\n', ''.join(final)))

    code = ''.join(final)

    return code


def run_transpiled_code():
    global final
    global is_developer_mode
    global is_console_mode

    if is_console_mode is False:
        # Inserts necessary code to make importing a temporary python file work.
        code_to_append = "import enkelt as Enkelt\ndef __Enkelt__():\n\tprint('', end='')\n"
        final.insert(0, code_to_append)

    code = fix_up_and_prepare_transpiled_code()

    if is_developer_mode:
        print('--DEV: run_transpiled_code, final code')
        print(code)

    if is_console_mode is False:
        # Writes the transpiled code to a file temporarily.
        with open('final_transpiled.py', 'w+')as transpiled_f:
            transpiled_f.writelines(code)

    # Executes the code transpiled to python and catches Exceptions
    try:
        # The "main" way of executing the transpiled code
        if is_console_mode is False:
            # This line will show an error;
            # it's importing a temporary file that get's created (and deleted) by this script.
            import final_transpiled
            final_transpiled.__Enkelt__()
        # The "fallback"/console execution process.
        else:
            exec(code)
    except Exception as err:
        if is_developer_mode:
            print('--DEV: run_final_transpiled_code, error')
            print(err)

        # Print out error(s) if any
        error = ErrorClass(str(err).replace('(<string>, ', '('))
        if error.get_error_message_data() != 'IGNORED':
            print(error.get_error_message_data())

    if is_console_mode is False:
        # Removes the temporary python file.
        with open('final_transpiled.py', 'w+')as transpiled_f:
            transpiled_f.writelines('')
        os.remove(os.getcwd() + '/final_transpiled.py')


def transpile_line(line):
    global source_code
    global is_developer_mode
    global final

    if line != '\n':
        if is_developer_mode:
            print('--DEV: transpile_line, line')
            print(line)

        data = fix_up_code_line(line)
        data = lex(data)

        if is_developer_mode:
            print('--DEV: transpile_line, lexed line')
            print(data)

        parse(data, 0)

        # Appends the transpiled code to the final source code
        final.append(''.join(source_code))
        final.append('\n')
        source_code = []


def prepare_and_run_code_lines_to_be_run(code):
    global final
    global variables

    # Removes empty lines
    while '' in code:
        code.pop(code.index(''))

    # Inserts previously saved variables into the transpiled code (used in the console mode)
    if variables:
        for var in variables[::-1]:
            final.insert(0, var + '\n')

    # Runs the code line by line
    for line_to_run in code:
        transpile_line(line_to_run)

    run_transpiled_code()


def console_mode(first):
    global version
    global variables
    global source_code
    global final
    global is_console_mode

    is_console_mode = True

    if first:  # is first console run -> shows copyright & license info.
        check_for_updates(version)
        print('Enkelt v' + str(version) + ' © 2018-2019-2020 Edvard Busck-Nielsen' + ". GNU GPL v.3")
        print('Skriv "x" eller tryck Ctrl+C för att avsluta')

    code_line = input('Enkelt >>> ')

    if code_line != '' and code_line != 'x':
        tmp_lexed_code_line_to_test_if_var = fix_up_code_line(code_line)
        tmp_lexed_code_line_to_test_if_var = lex(tmp_lexed_code_line_to_test_if_var)

        # Makes sure that the line is a "normal" code line, i.e. not the clear command and not a variable declaration.
        if code_line.replace(' (', '(') != 'töm()' and tmp_lexed_code_line_to_test_if_var[0][0] != 'VAR':
            prepare_and_run_code_lines_to_be_run([code_line])

        # Clear command was issued
        elif code_line.replace(' (', '(') == 'töm()':
            os.system(translate_clear())

        # A variable was declared
        else:
            parse(tmp_lexed_code_line_to_test_if_var, 0)
            variables.append(''.join(source_code))

    if code_line == 'x':
        return

    # Calling the console, recursively
    source_code = []
    final = []
    console_mode(False)


# ----- SETUP -----

is_list = False
is_if = False
is_math = False
is_for = False
look_for_loop_ending = False
needs_start_statuses = [False]
is_file_open = False
is_extension = False

is_console_mode = False

source_code = []
indent_layers = []
imported_libraries = []
user_functions = []

# When user/dev tests
is_developer_mode = False
# Gets an env. variable to check if it's a circle-ci test run.
is_dev = os.getenv('ENKELT_DEV', False)

version = 3.1
repo_location = 'https://raw.githubusercontent.com/Enkelt/Enkelt/'
web_import_location = 'https://raw.githubusercontent.com/Enkelt/EnkeltWeb/master/bibliotek/bib/'

final = []
variables = []

enkelt_script_path = ''

# ----- START -----
if not is_dev:
    try:
        if sys.version_info[0] < 3:
            raise Exception("Du måste använda Python 3 eller högre")

        # Checks if code is being provided from an enkelt script or if it's a console/repl mode launch
        if len(sys.argv) >= 2:
            if '.e' in sys.argv[1]:
                enkelt_script_path = sys.argv[1]

            # Checks if enkelt is being run in developer mode (--d flag)
            if len(sys.argv) >= 3:
                if sys.argv[2] == '--d':
                    is_developer_mode = True

            with open(enkelt_script_path, 'r+')as f:
                tmp_code_to_run = f.readlines()

            prepare_and_run_code_lines_to_be_run(tmp_code_to_run)

            check_for_updates(version)
        else:
            # Starts console/repl mode
            variables = []
            final = []
            console_mode(True)
    except Exception as e:
        print(e)
