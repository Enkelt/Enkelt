# coding=utf-8

# Enkelt 5.0
# Copyright 2018, 2019, 2020 Edvard Busck-Nielsen
# This file is part of Enkelt.
#
#     Enkelt is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     Enkelt is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with Enkelt.  If not, see <https://www.gnu.org/licenses/>.


from sys import argv, version_info
from os import getcwd, path, name, getenv, remove
import urllib.request


# ############ #
# Main Methods #
# ############ #

def check_for_updates(version):
	import json

	repo_location = 'https://raw.githubusercontent.com/Enkelt/Enkelt/'

	url = repo_location + '/master/VERSION.json'

	response = urllib.request.urlopen(url)

	data_store = json.loads(response.read())

	if data_store['version'] > float(version):
		print('Uppdatering tillgänglig! Du har version ' + str(
			version) + ' men du kan uppdatera till Enkelt version ' + str(data_store['version']))


# ############## #
# Helper Methods #
# ############## #

def translate_clear():
	if name == 'nt':
		return 'cls'
	return 'clear'


# ################### #
# Library & Importing #
# ################### #

# Transpiles the source code of the library being imported.
def transpile_library_code(library_code, library_name):
	global is_extension
	global additional_library_code

	source_code = library_code

	if not is_extension:
		source_code = lexer([line + '\n' for line in library_code.split('\n')])
		source_code = parser(source_code)
		source_code = source_code.split('\n')

	class_boilerplate_for_library = 'class ' + library_name + ':\n'
	for line in source_code:
		if line and line[-1] != '\n':
			class_boilerplate_for_library += '\n'

		class_boilerplate_for_library += '\t' + line

	additional_library_code = class_boilerplate_for_library

	is_extension = False


def maybe_load_from_file_then_transpile(file_or_code, is_file, library_name):
	library_code = file_or_code

	if is_file:
		with open(file_or_code) as library_file:
			library_code = library_file.readlines()

	while '' in library_code:
		library_code.pop(library_code.index(''))

	transpile_library_code(library_code, library_name)


# Fetches the source code of the remote library being imported.
def load_library_from_remote(url, library_name):
	response = urllib.request.urlopen(url)
	library_code = response.read().decode('utf-8')

	library_code = library_code.split('\n')

	maybe_load_from_file_then_transpile(library_code, False, library_name)


def import_library(library_name):
	from urllib.error import HTTPError

	global source_file_name
	global is_extension
	global additional_library_code
	global built_in_libraries

	if library_name in built_in_libraries:
		return

	web_import_location = 'https://raw.githubusercontent.com/Enkelt/EnkeltWeb/master/bibliotek/bib/'

	# Checks if the library is user-made (i.e. local not remote).
	import_file = ''.join(source_file_name.split('/')[:-1]) + '/' + library_name + '.e'

	if path.isfile(import_file):
		maybe_load_from_file_then_transpile(import_file, True, library_name)
	else:
		# The library might be a local extension (.epy file)
		import_file += 'py'
		if path.isfile(import_file):
			is_extension = True
			maybe_load_from_file_then_transpile(import_file, True, library_name)

		# The library might be remote (i.e. needs to be fetched)
		else:
			url = web_import_location + library_name + '.e'

			try:
				load_library_from_remote(url, library_name)
			except HTTPError:
				# The library might be a remote extension (.epy file)
				url += 'py'
				is_extension = True

				try:
					load_library_from_remote(url, library_name)
					return additional_library_code
				except HTTPError:
					print('Det inträffade ett fel! Kunde inte importera ' + library_name)


# ############## #
# Lexing & Lexer #
# ############## #

def lex_var_keyword(tokens, tmp):
	global variables
	global keywords
	global special_keywords

	collect = False
	collect_ends = []
	include_collect_end = False

	if tmp:
		if tmp in keywords:
			tokens.append(['KEYWORD', tmp])
		elif tmp in special_keywords.keys():
			tokens.append([special_keywords[tmp]['type'], tmp])
			collect = special_keywords[tmp]['collect']
			collect_ends = special_keywords[tmp]['collect_ends']
			include_collect_end = special_keywords[tmp]['include_collect_end']
		else:
			tokens.append(['VAR', tmp])

			if tmp not in variables:
				variables.append(tmp)
		tmp = ''
	return tokens, tmp, collect, collect_ends, include_collect_end


def add_part(parts, is_string, code):
	parts.append({
		'is_string': is_string,
		'code': code
	})

	is_string = True

	if code[-1] == '\n':
		is_string = False

	return parts, '', is_string


def fix_up_code_line(statement):
	statement = statement.replace("'", '"') \
		.replace('\\"', '|-ENKELT_ESCAPED_QUOTE-|') \
		.replace('\\', '|-ENKELT_ESCAPED_BACKSLASH-|')

	# Remove spaces between function names and '('.
	# Replaces four & two spaces with tab.
	parts = []
	is_string = False
	tmp = ''

	for char in statement:
		tmp += char

		if char == '"' and is_string:
			parts, tmp, is_string = add_part(parts, True, tmp)
			is_string = False
		elif char in ['"', '\n']:
			parts, tmp, is_string = add_part(parts, False, tmp)

	statement = ''
	for part in parts:
		if not part['is_string']:
			part['code'] = part['code'].replace('    ', '\t').replace('  ', '\t').replace(' (', '(')
		statement += part['code']

	return statement


def lexer(raw):
	tmp = ''
	is_collector = False
	collector_ends = []
	include_collector_end = False
	is_dict = []

	global keywords
	global operators
	global variables

	tokens = []

	for line in raw:
		line = fix_up_code_line(line)
		for char_index, char in enumerate(line):
			if char == '#':
				tokens.append(['FORMAT', '\n'])
				break

			if is_collector:
				if char not in collector_ends:
					tmp += char
				else:
					tokens[-1][1] = tmp

					if include_collector_end:
						tokens.append(['OP', char])

					is_collector = False
					include_collector_end = False
					tmp = ''

			elif char == '(':
				if tmp:
					if len(tmp) > 3 and tmp[:3] == 'def':
						tokens.append(['FUNC_DEF', tmp[3:]])
						tmp = ''
						continue

					tokens.append(['FUNC', tmp])
					tmp = ''
			elif char == '=':
				if tmp:
					tokens.append(['VAR', tmp])
					tokens.append(['ASSIGN', char])

					if tmp not in variables:
						variables.append(tmp)

					tmp = ''
				else:
					tokens.append(['OP', char])
			elif char in ['"', '\'']:
				is_collector = True
				collector_ends = ['"', '\'']
				include_collector_end = False
				tmp = ''
				tokens.append(['STR', ''])
			elif char == '{':
				is_dict.append(True)
				tokens.append(['OP', char])
			elif char == '}':
				tokens, tmp, is_collector, collector_ends, include_collector_end = lex_var_keyword(tokens, tmp)

				is_dict.pop(0)
				tokens.append(['OP', char])
			elif char.isdigit() and not tmp:
				if tokens and tokens[-1][0] == 'NUM':
					tokens[-1][1] += char
					continue
				tokens.append(['NUM', char])
			elif char == '&':
				is_collector = True
				collector_ends = ['\n']
				include_collector_end = True
				tmp = ''
				tokens.append(['DEC', ''])
			elif char in operators:
				if char == ':' and is_dict and tmp:
					tokens.append(['KEY', tmp])
					tmp = ''

				tokens, tmp, is_collector, collector_ends, include_collector_end = lex_var_keyword(tokens, tmp)

				tokens.append(['OP', char])
			elif char not in ['\n', '\t', ' ']:
				tmp += char
			elif char in ['\n', '\t']:
				tokens, tmp, is_collector, collector_ends, include_collector_end = lex_var_keyword(tokens, tmp)
				tokens.append(['FORMAT', char])
			else:
				tokens, tmp, is_collector, collector_ends, include_collector_end = lex_var_keyword(tokens, tmp)
	return tokens


# ####### #
# Parsing #
# ####### #

def transpile_var(var):
	vars = {
		'själv': 'self',
	}

	try:
		return vars[var]
	except KeyError:
		return var


def maybe_place_space_before(parsed, token_val):
	prefix = ' '

	if parsed and parsed[-1] in ['\n', '\t', '(', ' ', '.']:
		prefix = ''
	parsed += prefix + token_val + ' '

	return parsed


def translate_function(func):
	function_translations = functions_and_keywords()['functions']

	translation = function_translations[func] if func in function_translations.keys() else func
	if 'system("c' not in translation:
		translation += '('

	return translation


def translate_keyword(keyword):
	keyword_translations = functions_and_keywords()['keywords']

	return keyword_translations[keyword] if keyword in keyword_translations.keys() else 'error'


def parser(tokens):
	global built_in_vars

	is_skip = False
	add_parenthesis_at_en_of_line = False

	parsed = ''

	for token_index, token in enumerate(tokens):
		if is_skip:
			is_skip = False
			continue

		token_type = token[0]
		token_val = token[1]

		if token_type in ['FORMAT', 'ASSIGN', 'NUM']:
			if token_val == '\n' and add_parenthesis_at_en_of_line:
				parsed += ')'
				add_parenthesis_at_en_of_line = False
			parsed += token_val
		elif token_type == 'OP':
			if token_val in ['.', ')', ',', ':'] and parsed and parsed[-1] == ' ':
				parsed = parsed[:-1]

			parsed += token_val

			if token_val in [',', '=']:
				parsed += ' '
		elif token_type == 'STR':
			token_val = token_val.replace('|-ENKELT_ESCAPED_BACKSLASH-|', '\\').replace('|-ENKELT_ESCAPED_QUOTE-|','\\"')
			parsed += '"' + token_val + '"'
		elif token_type == 'IMPORT':
			import_library(token_val)
		elif token_type == 'KEYWORD':
			token_val = translate_keyword(token_val)
			parsed = maybe_place_space_before(parsed, token_val)
		elif token_type == 'VAR':
			if token_val not in built_in_vars and token_index > 0:
				parsed = maybe_place_space_before(parsed, token_val)
			else:
				parsed += transpile_var(token_val)
		elif token_type == 'FUNC':
			token_val = translate_function(token_val)
			parsed += token_val
		elif token_type == 'CLASS':
			parsed += '\nclass ' + token_val
		elif token_type == 'OBJ_NOTATION':
			parsed += '\n' + translate_keyword(token_val) + ':'
		elif token_type == 'FUNC_DEF':
			parsed += 'def ' + token_val + '('
		elif token_type == 'KEY':
			parsed += '\'' + token_val + '\''

		if len(parsed) > 3 and parsed[-1] == ' ' and parsed[-2] == '=' and parsed[-3] == ' ' and parsed[-4] == '=':
			parsed = parsed[:-4]
			parsed += ' == '

	return parsed


# ################################## #
# Transpiling, Building, & Executing #
# ################################## #

def translate_error(error_msg):
	error_msg = error_msg.args[0]

	translations = {
		'unmatched': 'Syntaxfel!',
		'division by zero': 'Nolldelningsfel!',
		'index': 'Indexfel!',
		'key': 'Nyckelfel!',
		'lookup': 'Sökfel!',
		'attribute': 'Attribut/Parameterfel!',
		'unexpected EOF': 'Oväntat programslut!',
		'result too large': 'Resultatet för stort!',
		'import': 'Importeringsfel!',
		'module': 'Modulfel',
		'syntax': 'Syntaxfel',
		'KeyboardInterrupt': 'Avbruten!',
		'memory': 'Minnefel!',
		'name': 'Namnfel!',
		'recursion': 'Rekursionsfel',
		'argument': 'Argumentfel!',
		'type': 'Typfel!',
		'referenced before': 'Referensfel!',
		'unicode': 'Unicode-fel!',
		'value': 'Värdefel!',
		'file': 'Filfel!',
		'timeout': 'Avbrottsfel!',
		'warning': 'Varning!',
		'indent': 'Indragsfel!',
		'\'break\' outside loop': 'Brytningsfel: Bryt utanför loop!',
		'invalid mode': 'Ogiltigt filläge!',
		'concaten': 'Sammanfogningsfel!',
	}

	sv_error_message = ''

	for key in translations:
		if key in error_msg:
			sv_error_message = translations[key]

	if not sv_error_message:
		sv_error_message = 'Fel! ENG: ' + error_msg

	return sv_error_message


def build(tokens):
	global additional_library_code
	global is_console
	global console_mode_variable_source_code

	console_mode_variable_source_code_to_ignore = []

	parsed = parser(tokens)

	if is_console and len(tokens) > 2 and tokens[1][0] == 'VAR':
		console_mode_variable_source_code_to_ignore.append(parsed)
		console_mode_variable_source_code.append(parsed)

	parsed = '\n' + ''.join(additional_library_code) + parsed

	boilerplate = "from os import system\nfrom collections import abc\n\n\ndef __enkelt__():\n\tprint('', end='')\n"

	boilerplate += '\n\tclass tid:\n'
	boilerplate += '\t\timport time\n'
	boilerplate += '\t\timport datetime\n\n'
	boilerplate += '\t\tepok = time.time\n'
	boilerplate += '\t\ttid = time.ctime\n'
	boilerplate += '\t\tdatum = datetime.date\n'
	boilerplate += '\t\tnu = datetime.datetime.now\n'
	boilerplate += '\t\tidag = datetime.date.today\n'

	boilerplate += '\n\tdef translate_output_to_swedish(data):\n'
	boilerplate += '\t\tif isinstance(data, abc.KeysView):\n'
	boilerplate += '\t\t\tdata = list(data)\n'
	boilerplate += '\t\treplace_dict = {\n'
	boilerplate += '\t\t\t"True": \'Sant\',\n'
	boilerplate += '\t\t\t"False": \'Falskt\',\n'
	boilerplate += '\t\t\t"None": \'Inget\',\n'
	boilerplate += '\t\t\t"<class \'float\'>": \'Decimaltal\',\n'
	boilerplate += '\t\t\t"<class \'str\'>": \'Sträng\',\n'
	boilerplate += '\t\t\t"<class \'int\'>": \'Heltal\',\n'
	boilerplate += '\t\t\t"<class \'list\'>": \'Lista\',\n'
	boilerplate += '\t\t\t"<class \'dict\'>": \'Lexikon\',\n'
	boilerplate += '\t\t\t"<class \'dict_keys\'>": \'Lexikonnycklar\',\n'
	boilerplate += '\t\t\t"<class \'bool\'>": \'Boolesk\',\n'
	boilerplate += '\t\t\t"<class \'IngetType\'>": \'Inget\',\n'
	boilerplate += '\t\t\t"<class \'Exception\'>": \'Feltyp\',\n'
	boilerplate += '\t\t\t"<class \'datetime.date\'>": \'Datum\',\n'
	boilerplate += '\t\t\t"<class \'datetime.datetime\'>": \'Datum & tid\',\n'
	boilerplate += '\t\t\t"<class \'range\'>": \'Område\'\n'
	boilerplate += '\t\t}\n'
	boilerplate += '\t\tdata = str(data)\n'
	boilerplate += '\t\tfor key in replace_dict:\n'
	boilerplate += '\t\t\tdata = data.replace(key, replace_dict[key])\n'
	boilerplate += '\t\treturn data\n'

	boilerplate += '\n\tdef enkelt_print(data):\n'
	boilerplate += '\t\tprint(translate_output_to_swedish(data))\n'

	boilerplate += '\n\tdef enkelt_input(prompt=\'\'):\n'
	boilerplate += '\t\ttmp = input(prompt)\n'
	boilerplate += '\t\ttry:\n'
	boilerplate += '\t\t\ttmp = int(tmp)\n'
	boilerplate += '\t\t\treturn tmp\n'
	boilerplate += '\t\texcept ValueError:\n'
	boilerplate += '\t\t\ttry:\n'
	boilerplate += '\t\t\t\ttmp = float(tmp)\n'
	boilerplate += '\t\t\t\treturn tmp\n'
	boilerplate += '\t\t\texcept ValueError:\n'
	boilerplate += '\t\t\t\treturn str(tmp)\n'

	boilerplate += '\n\tclass matte:\n'
	boilerplate += '\t\timport math\n'
	boilerplate += '\t\ttak = math.ceil\n'
	boilerplate += '\t\tgolv = math.floor\n'
	boilerplate += '\t\tfakultet = math.factorial\n'
	boilerplate += '\t\tsin = math.sin\n'
	boilerplate += '\t\tcos = math.cos\n'
	boilerplate += '\t\ttan = math.tan\n'
	boilerplate += '\t\tasin = math.asin\n'
	boilerplate += '\t\tacos = math.acos\n'
	boilerplate += '\t\tatan = math.atan\n'
	boilerplate += '\t\tpotens = math.pow\n'
	boilerplate += '\t\tkvadratrot = math.sqrt\n'
	boilerplate += '\t\tlog = math.log\n'
	boilerplate += '\t\tgrader = math.degrees\n'
	boilerplate += '\t\tradianer = math.radians\n'
	boilerplate += '\t\tabs = abs\n'

	boilerplate += '\n\t\t@staticmethod\n'
	boilerplate += '\t\tdef e():\n'
	boilerplate += '\t\t\tfrom math import e\n'
	boilerplate += '\t\t\treturn e\n'

	boilerplate += '\n\t\t@staticmethod\n'
	boilerplate += '\t\tdef pi():\n'
	boilerplate += '\t\t\tfrom math import pi\n'
	boilerplate += '\t\t\treturn pi'

	for variable_source_code in console_mode_variable_source_code:
		if variable_source_code not in console_mode_variable_source_code_to_ignore:
			variable_source_code = variable_source_code.replace('\n', '')
			boilerplate += '\t' + variable_source_code + '\n'

	fixed_code = boilerplate

	lines = parsed.split('\n')

	for line_index, line in enumerate(lines):
		line += '\n'

		if line:
			line = '\t' + line
		fixed_code += line

	if is_dev:
		print('--DEV: FINAL TRANSPILED CODE')
		print(fixed_code)

	if not is_console:
		with open('final_transpiled.py', 'w+', encoding='utf-8') as f:
			f.write('')
			f.write(fixed_code)

		# final_transpiled is a module generated by this script, line 454 will always show an error.
		import final_transpiled
		final_transpiled.__enkelt__()

		# Deletes the temporary script if development mode is not activated.
		if not is_dev:
			remove('final_transpiled.py')
	else:
		fixed_code += '__enkelt__()'
		exec(fixed_code)


def transpile(source_lines):
	source_lines.insert(0, '\n')
	source_lines[-1] += '\n'

	tokens_list = lexer(source_lines)

	if is_dev:
		print('--DEV: TOKENS LIST')
		for token in tokens_list:
			print(token)

	if tokens_list:
		build(tokens_list)
	else:
		print('Filen är tom!')

	check_for_updates(version_nr)


# ############### #
# Setup & Startup #
# ############### #

def startup(file_name):
	global version_nr
	global is_dev

	with open(file_name, encoding='utf-8') as f:
		source_lines = f.readlines()

	transpile(source_lines)


def start_console(first_run):
	global is_console
	global console_mode_variable_source_code

	is_console = True

	if first_run:
		print('Enkelt 5.0. GNU GPL v.3. © Edvard Busck-Nielsen. Enkelt.io')
	cmd = str(input('>>> '))

	if cmd == 'x':
		return

	transpile([cmd])

	start_console(False)


def functions_and_keywords():
	return {
		'functions': {
			'skriv': 'enkelt_print',
			'in': 'enkelt_input',
			'Sträng': 'str',
			'Heltal': 'int',
			'Decimal': 'float',
			'Lista': 'list',
			'Bool': 'bool',
			'längd': 'len',
			'till': 'append',
			'bort': 'pop',
			'sortera': 'sorted',
			'slump': '__import__("random").randint',
			'slumpval': '__import__("random").choice',
			'blanda': '__import__("random").shuffle',
			'området': 'range',
			'lista': 'list',
			'ärnum': 'isdigit',
			'runda': 'round',
			'versal': 'upper',
			'gemen': 'lower',
			'ärversal': 'isupper',
			'ärgemen': 'islower',
			'ersätt': 'replace',
			'infoga': 'insert',
			'index': 'index',
			'dela': 'split',
			'foga': 'join',
			'typ': 'type',
			'läs': 'read',
			'öppna': 'with open',
			'överför': 'write',
			'veckodag': 'weekday',
			'värden': 'values',
			'element': 'elements',
			'numrera': 'enumerate',
			'töm': 'system("' + translate_clear() + '"',
			'kasta': 'raise Exception',
			'nycklar': 'keys',
		},
		'keywords': {
			'för': 'for',
			'medan': 'while',
			'Sant': 'True',
			'Falskt': 'False',
			'Inget': 'None',
			'inom': 'in',
			'bryt': 'break',
			'fortsätt': 'continue',
			'returnera': 'return ',
			'passera': 'pass',
			'år': 'year',
			'månad': 'month',
			'dag': 'day',
			'timme': 'hour',
			'minut': 'minute',
			'sekund': 'second',
			'mikrosekund': 'microsecond',
			'global': 'global',
			'om': 'if',
			'annars': 'else',
			'anom': 'elif',
			'och': 'and',
			'eller': 'or',
			'som': 'as',
			'försök': 'try',
			'fånga': 'except Exception as',
			'slutligen': 'finally',
			'>': 'lambda',
		},
	}


# Globals
built_in_vars = ['själv']
variables = built_in_vars
console_mode_variable_source_code = []
keywords = functions_and_keywords()['keywords']

special_keywords = {
	'klass': {
		'type': 'CLASS',
		'collect': True,
		'collect_ends': [':'],
		'include_collect_end': True
	},
	'def': {
		'type': 'FUNC_DEF',
		'collect': True,
		'collect_ends': ['('],
		'include_collect_end': False
	},
	'försök': {
		'type': 'OBJ_NOTATION',
		'collect': True,
		'collect_ends': [':'],
		'include_collect_end': True
	},
	'fånga': {
		'type': 'OBJ_NOTATION',
		'collect': True,
		'collect_ends': [':'],
		'include_collect_end': False
	},
	'slutligen': {
		'type': 'OBJ_NOTATION',
		'collect': True,
		'collect_ends': [':'],
		'include_collect_end': False
	},
	'importera': {
		'type': 'IMPORT',
		'collect': True,
		'collect_ends': ['\n'],
		'include_collect_end': False
	}
}
operators = [':', ')', '!', '+', '-', '*', '/', '%', '.', ',', '[', ']', '&']
built_in_libraries = ['matte', 'tid']

source_file_name = ''
is_extension = False
additional_library_code = []
is_console = False

version_nr = 5.0

is_dev = False
is_running_tests = getenv('ENKELT_DEV_TEST_RUN', False)

# Start
if __name__ == '__main__' and not is_running_tests:
	try:
		if version_info[0] < 3:
			print("Du måste använda Python 3 eller högre")
			exit()

		if len(argv) > 1:
			if len(argv) > 2:
				flag = argv[2]
				if flag == '--d':
					is_dev = True

			source_file_name = argv[1]
			if path.isfile(getcwd() + '/' + source_file_name):
				startup(source_file_name)
			else:
				print('Filen kunde inte hittas!')
		else:
			start_console(True)
	except Exception as e:
		print(translate_error(e))
		if is_dev:
			print('--DEV: ERROR MESSAGE')
			print(e)
			import traceback
			traceback.print_exc()

		if is_console:
			start_console(False)
