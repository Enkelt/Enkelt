# coding=utf-8

# Enkelt 3.0
# Copyright 2018, 2019 Edvard Busck-Nielsen, 2019 Morgan Willliams
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

# ############## #
# Enkelt Modules #
# ############## #


def enkelt_print(data):
	data = str(data)
	data = data.replace("True", "Sant").replace("False", "Falskt").replace("<class \'float\'>", "decimaltal").replace("<class \'str\'>", "sträng").replace("<class \'int\'>", "heltal").replace("<class \'list\'>", "lista").replace("<class \'dict\'>", "lexikon").replace("<class \'bool\'>", "boolesk").replace("<class \'NoneType\'>", "inget")
	print(data)

	
# ############ #
# Main Methods #
# ############ #

def check_for_updates(version_nr):
	import urllib.request
	import json
	
	global repo_location
	
	url = repo_location + '/master/VERSION.json'
	
	response = urllib.request.urlopen(url)
	
	data_store = json.loads(response.read())
	
	if data_store['version'] > float(version_nr):
		print('Uppdatering tillgänglig! Du har version ' + str(version_nr) + ' men du kan uppdatera till Enkelt version ' + str(data_store['version']))


def has_numbers(input_string):
	return any(char.isdigit() for char in input_string)


class ErrorClass:
	
	def __init__(self, error_msg):
		self.error = error_msg
		self.error_list = error_msg.split()
		self.errors = {
			'SyntaxError': 'Syntaxfel',
			'IndexError': 'Indexfel',
			'TypeError': 'Typfel',
			'ValueError': 'Värdefel',
			'NameError': 'Namnfel',
			'ZeroDivisionError': 'Nolldelningsfel',
			'AttributeError': 'Attributfel'
		}
	
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
			return translator.translate(self.error, dest = 'sv').text.replace('linje', 'rad').replace('final_transpiled.py, ', '')
		else:
			# Get line number
			for index, item in enumerate(self.error_list):
				if 'line' in item and has_numbers(self.error_list[index + 1]):
					line_index = index + 1
					return error_type + " (runt rad " + str(int(self.error_list[line_index][:-1]) - 3) + ')'
			return error_type


def _import(enkelt_module):
	global enkelt_script_path

	import_file = ''.join(enkelt_script_path.split('/')[:-1]) + '/' + enkelt_module + '.e'

	if os.path.isfile(import_file):
		get_import(import_file, True, enkelt_module)
	else:
		import_file = 'bib/' + enkelt_module + '.e'
		if os.path.isfile(import_file):
			get_import(import_file, True, enkelt_module)
		else:
			import urllib.request
	
			global web_import_location
	
			url = web_import_location + enkelt_module + '.e'

			try:
				response = urllib.request.urlopen(url)
				module_code = response.read().decode('utf-8')

				module_code = module_code.split('\n')

				get_import(module_code, False, enkelt_module)
			except Exception:
				print('Error kunde inte importera ' + enkelt_module)


def get_import(file_or_code, is_file, module_name):
	global imported_modules
	global source_code
	global final
	global user_functions

	imported_modules.append(module_name)

	if is_file:
		with open(file_or_code, 'r') as module_file:
			module_code = module_file.readlines()
			module_file.close()
	else:
		module_code = file_or_code

	while '' in module_code:
		module_code.pop(module_code.index(''))

	for line in module_code:
		
		if line != '\n':
			data = main(line)
			data = lex(data)

			for token_index, _ in enumerate(data):
				if data[token_index][0] == 'USER_FUNCTION':
					data[token_index][1] = module_name + '.' + data[token_index][1]

					user_functions[-1] = module_name + '.' + user_functions[-1]

			if is_developer_mode:
				print(data)

			parse(data, 0)
			final.append(''.join(source_code))
			final.append('\n')
			source_code = []


def parse(lexed, token_index):
	global source_code
	global indent_layers
	global is_if
	global is_math
	global is_for
	global look_for_loop_ending
	global needs_start_statuses
	global is_file_open
	
	global is_web_editor
	
	is_comment = False
	
	forbidden = ['in', 'str', 'int', 'list', 'num', 'matte_e', 'matte_pi']
	
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
		if token_val == 'skriv':
			if is_web_editor is False:
				source_code.append('Enkelt.enkelt_print(')
			else:
				source_code.append('print(')
		elif token_val == 'matte':
			is_math = True
		elif token_val == 'in':
			source_code.append('input(')
		elif token_val == 'om':
			source_code.append('if ')
			is_if = True
		elif token_val == 'anom':
			source_code.append('elif ')
			is_if = True
		elif token_val == 'Text':
			source_code.append('str(')
		elif token_val == 'Nummer':
			source_code.append('int(')
		elif token_val == 'Decimal':
			source_code.append('float(')
		elif token_val == 'Bool':
			source_code.append('bool(')
		elif token_val == 'längd':
			source_code.append('len(')
		elif token_val == 'töm':
			if os.name == 'nt':
				source_code.append('os.system("cls"')
			elif os.name == 'posix':
				source_code.append('print("\x1b[3J\x1b[H\x1b[2J"')
			else:
				source_code.append('os.system("clear"')
		elif token_val == 'till':
			source_code.append('append(')
		elif token_val == 'bort':
			source_code.append('pop(')
		elif token_val == 'ärnum':
			source_code.append('isdigit(')
		elif token_val == 'sortera':
			source_code.append('sorted(')
		elif token_val == 'slump':
			source_code.append('__import__("random").randint(')
		elif token_val == 'slumpval':
			source_code.append('__import__("random").choice(')
		elif token_val == 'blanda':
			source_code.append('__import__("random").shuffle(')
		elif token_val == 'området':
			source_code.append('range(')
		elif token_val == 'abs':
			source_code.append('abs(')
		elif token_val == 'lista':
			source_code.append('list(')
		elif token_val == 'runda':
			source_code.append('round(')
		elif token_val == 'versal':
			source_code.append('upper(')
		elif token_val == 'gemen':
			source_code.append('lower(')
		elif token_val == 'ersätt':
			source_code.append('replace(')
		elif token_val == 'infoga':
			source_code.append('insert(')
		elif token_val == 'index':
			source_code.append('index(')
		elif token_val == 'dela':
			source_code.append('split(')
		elif token_val == 'foga':
			source_code.append('join(')
		elif token_val == 'typ':
			source_code.append('type(')
		elif token_val == 'sin':
			source_code.append('__import__("math").sin(')
		elif token_val == 'cos':
			source_code.append('__import__("math").cos(')
		elif token_val == 'tan':
			source_code.append('__import__("math").tan(')
		elif token_val == 'potens':
			source_code.append('__import__("math").pow(')
		elif token_val == 'asin':
			source_code.append('__import__("math").asin(')
		elif token_val == 'acos':
			source_code.append('__import__("math").acos(')
		elif token_val == 'atan':
			source_code.append('__import__("math").atan(')
		elif token_val == 'tak':
			source_code.append('__import__("math").ceil(')
		elif token_val == 'golv':
			source_code.append('__import__("math").floor(')
		elif token_val == 'log':
			source_code.append('__import__("math").log(')
		elif token_val == 'kvadratrot':
			source_code.append('__import__("math").sqrt(')
		elif token_val == 'grader':
			source_code.append('__import__("math").degrees(')
		elif token_val == 'radianer':
			source_code.append('__import__("math").radians(')
		elif token_val == 'fakultet':
			source_code.append('__import__("math").factorial(')
		elif token_val == 'datum':
			source_code.append('__import__("datetime").date(')
		elif token_val == 'veckodag':
			source_code.append('weekday(')
		elif token_val == 'öppna':
			source_code.append('with open(')
			needs_start_statuses.append(True)
			is_file_open = True
		elif token_val == 'läs':
			source_code.append('read(')
		elif token_val == 'överför':
			source_code.append('write(')
		elif token_val == 'för':
			source_code.append('for ')
			is_for = True
			look_for_loop_ending = True
		elif token_val == 'medan':
			source_code.append('while ')
			look_for_loop_ending = True
		elif token_val == 'epok':
			source_code.append('__import__("time").time(')
		elif token_val == 'tid':
			source_code.append('__import__("time").ctime(')
		elif token_val == 'nu':
			source_code.append('__import__("datetime").datetime.now(')
		elif token_val == 'idag':
			source_code.append('__import__("datetime").date.today(')
		elif token_val == 'värden':
			source_code.append('values(')
		elif token_val == 'element':
			source_code.append('items(')
		elif token_val == 'numrera':
			source_code.append('enumerate(')
	elif token_type == 'VAR':
		if token_val not in forbidden:
			source_code.append(token_val)
		else:
			print('Error namnet ' + token_val + " är inte tillåtet som variabelnamn!")
	elif token_type == 'STRING':
		if is_file_open and len(token_val) <= 2:
			token_val = token_val.replace('l', 'r').replace('ö', 'w')
		source_code.append('"' + token_val + '"')
	elif token_type == 'PNUMBER' or token_type == 'NNUMBER':
		source_code.append(token_val)
	elif token_type == 'IMPORT':
		_import(token_val)
	elif token_type == 'OPERATOR':
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
		else:
			source_code.append(token_val)
	elif token_type == 'LIST_START':
		source_code.append('[')
	elif token_type == 'LIST_END':
		source_code.append(']')
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
	elif token_type == 'BOOL':
		if token_val == 'Sant':
			source_code.append('True')
		elif token_val == 'Falskt':
			source_code.append('False')
	elif token_type == 'KEYWORD':
		if token_val == 'inom':
			source_code.append(' in ')
		elif token_val == 'bryt':
			source_code.append('break')
		elif token_val == 'fortsätt':
			source_code.append('continue')
		elif token_val == 'returnera':
			source_code.append('return')
		elif token_val == 'inte':
			source_code.append('not ')
		elif token_val == 'passera':
			source_code.append('pass') 
		elif token_val == 'matte_e':
			source_code.append('__import__("math").e')
		elif token_val == 'matte_pi':
			source_code.append('__import__("math").pi')
		elif token_val == 'år':
			source_code.append('year')
		elif token_val == 'månad':
			source_code.append('month')
		elif token_val == 'dag':
			source_code.append('day')
		elif token_val == 'timme':
			source_code.append('hour')
		elif token_val == 'minut':
			source_code.append('minute')
		elif token_val == 'sekund':
			source_code.append('second')
		elif token_val == 'mikrosekund':
			source_code.append('microsecond')
		elif token_val == 'töm':
			if os.name == 'nt':
				source_code.append('os.system("cls")')
			elif os.name == 'posix':
				source_code.append('print("\x1b[3J\x1b[H\x1b[2J")')
			else:
				source_code.append('os.system("clear")')
		elif token_val == 'annars':
			source_code.append('else')
			needs_start_statuses.append(True)
		elif token_val == 'och':
			source_code.append(' and ')
		elif token_val == 'eller':
			source_code.append(' or ')
		elif token_val == 'som':
			source_code.append(' as ')
	elif token_type == 'USER_FUNCTION':
		token_val = token_val.replace('.', '_')
		source_code.append('def ' + token_val + '(')
		needs_start_statuses.append(True)
	elif token_type == 'USER_FUNCTION_CALL':
		token_val = token_val.replace('.', '_')
		source_code.append(token_val + '(')
	
	if len(lexed) - 1 >= token_index + 1 and is_comment is False:
		parse(lexed, token_index + 1)


def lex(line):
	if line[0] == '#':
		return ['COMMENT', line]

	global functions
	global user_functions
	global keywords
	global operators
	global imported_modules
	
	tmp_data = ''
	is_string = False
	is_var = False
	is_function = False
	is_import = False
	lexed_data = []
	last_action = ''
	might_be_negative_num = False
	data_index = -1
	for chr_index, char in enumerate(line):
		if is_import and char != ' ':
			tmp_data += char
		if is_import and chr_index == len(line)-1:
			lexed_data.append(['IMPORT', tmp_data])
			is_import = False
			tmp_data = ''
		if is_function and char not in operators and char != '(':
			tmp_data += char
		elif is_function and char == '(':
			lexed_data.append(['USER_FUNCTION', tmp_data])
			user_functions.append(tmp_data)
			tmp_data = ''
			is_function = False
		elif char == '{' and is_var is False:
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
								lexed_data.append(['FUNCTION', tmp_data])
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
					elif char in operators and tmp_data not in imported_modules:
						lexed_data.append(['OPERATOR', char])
					elif char in imported_modules and char != '.':
						lexed_data.append(['OPERATOR', char])
					elif char in imported_modules and char == '.':
						tmp_data += char
					else:
						if tmp_data == 'Sant' or tmp_data == 'Falskt':
							lexed_data.append(['BOOL', tmp_data])
							tmp_data = ''
						else:
							if char == '(' and tmp_data in functions:
								if tmp_data == 'matte':
									tmp_data = 'Nummer'
								lexed_data.append(['FUNCTION', tmp_data])
								tmp_data = ''
							elif char == '(' and tmp_data in user_functions:
								lexed_data.append(['USER_FUNCTION_CALL', tmp_data])
								tmp_data = ''
							elif char == '(' and tmp_data not in functions:
								lexed_data.append(['USER_FUNCTION_CALL', tmp_data])
								tmp_data = ''
							else:
								if is_import is False:
									tmp_data += char
								if tmp_data == 'Sant' or tmp_data == 'Falskt':
									lexed_data.append(['BOOL', tmp_data])
									tmp_data = ''
								else:
									if tmp_data in keywords:
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
									elif tmp_data == 'töm' and line[-3:] == 'töm':
										lexed_data.append(['KEYWORD', tmp_data])
										tmp_data = ''
									elif tmp_data == 'matte_e':
										lexed_data.append(['KEYWORD', tmp_data])
										tmp_data = ''
	
	return lexed_data


def main(statement):
	statement = statement.replace('\n', '').replace('\t', '').replace("'", '"')
	current_line = ''
	is_string = False
	is_import = False

	for char in statement:
		if char == ' ' and is_string:
			current_line += char
		elif char == ' ' and is_string is False and is_import is False:
			continue
		elif char == ' ' and is_string is False and is_import:
			current_line += char
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

	# Legacy removals
	if '.bort[' in current_line:
		current_line = current_line.replace('.bort[', '.bort(')
		
		tmp = ''
		is_index = False
		
		current_line = list(current_line)
		
		for index, text in enumerate(current_line):
			if '.bort(' in tmp and is_index is False:
				tmp = ''
				is_index = True
			elif is_index and text == ']':
				is_index = False
				current_line[index] = ')'
				current_line = ''.join(current_line)
				break
			else:
				tmp += text

	return current_line


def execute():
	global final
	global is_developer_mode
	global is_web_editor
	
	if is_web_editor is False:
		# Inserts necessary code to make importing a temporary python file work.
		code_to_append = "import enkelt as Enkelt\ndef __Enkelt__():\n\tprint('', end='')\n"
		final.insert(0, code_to_append)
	
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
	
	# Remove empty lines from final
	final = list(re.sub(r'\n\s*\n', '\n\n', ''.join(final)))

	code = ''.join(final)
	
	if is_developer_mode:
		print(code)
	
	if is_web_editor is False:
		# Writes the transpiled code to a file temporarily.
		with open('final_transpiled.py', 'w+')as transpiled_f:
			transpiled_f.writelines(code)
	
	# Executes the code transpiled to python and catches Exceptions
	try:
		if is_web_editor is False:
			import final_transpiled
			final_transpiled.__Enkelt__()
		else:
			exec(code)
	except Exception as e:
		if is_developer_mode:
			print(e)
		
		# Print out error(s) if any
		error = ErrorClass(str(e).replace('(<string>, ', '('))
		if error.get_error_message_data() != 'IGNORED':
			print(error.get_error_message_data())
	
	if is_web_editor is False:
		# Removes the temporary python code
		with open('final_transpiled.py', 'w+')as transpiled_f:
			transpiled_f.writelines('')


def run(line):
	global source_code
	global is_developer_mode
	global final
	global variables

	if line != '\n':
		data = main(line)
		data = lex(data)

		if is_developer_mode:
			print(data)

		parse(data, 0)
		final.append(''.join(source_code))
		final.append('\n')
		source_code = []


def execute_run_with_code(data):
	global variables
	
	for var in variables[::-1]:
		final.insert(0, var + '\n')
	
	for line_to_run in data:
		line_to_run = line_to_run.replace('£', ',')
		run(line_to_run)
	execute()
	

def run_with_code(data):
	global is_developer_mode
	global final
	global variables
	global tmp_variables
	
	if is_developer_mode is False and tmp_variables != []:
		# Variable setup
		variables = tmp_variables
		tmp_variables = []

	execute_run_with_code(data)


def console_line_runner(code):
	global variables
	global is_developer_mode
	global tmp_variables
	
	tmp_variables = variables
	
	is_developer_mode = False
	
	run_with_code([code])
	
	
def start_console(first):
	global version
	global is_developer_mode
	global variables
	global source_code
	
	if first:  # is first console run
		# Checks for updates:
		check_for_updates(version)
		# Print info
		print('Enkelt ' + str(version) + ' © 2018-2019 Edvard Busck-Nielsen' + ". GNU GPL v.3")
		print('Tryck Ctrl+C för att avsluta')
	
	code_line = input('Enkelt >> ')
	if code_line != '':
		test = main(code_line)
		test = lex(test)
		
		if code_line != 'töm' and code_line != 'töm()' and code_line != 'töm ()' and test[0][0] != 'VAR':
			console_line_runner(code_line)
			
		elif code_line == 'töm' or code_line == 'töm()' or code_line == 'töm ()':
			if not os.name == 'nt':
				os.system('clear')
			else:
				os.system('cls')
		else:
			parse(test, 0)
			variables.append(''.join(source_code))
			
	source_code = []
	start_console(False)


def web_editor_runner(event):
	global variables
	
	data = ''
	# These lines should be commented-out
	# data = document["inputCode"].value
	# data = data.split('\n')
	
	variables = []
	execute_run_with_code(data)


# ----- SETUP -----

# Global variable setup
is_list = False
is_if = False
is_math = False
is_for = False
look_for_loop_ending = False
needs_start_statuses = [False]
is_file_open = False

# --- SPECIAL --->
is_web_editor = False
# --- DO NOT CHANGE! --->

source_code = []
indent_layers = []
imported_modules = []

functions = [
	'skriv',
	'matte',
	'till',
	'bort',
	'töm',
	'om',
	'anom',
	'längd',
	'in',
	'Text',
	'Nummer',
	'Decimal',
	'Bool',
	'området',
	'sortera',
	'slumpval',
	'slump',
	'abs',
	'lista',
	'blanda',
	'runda',
	'versal',
	'gemen',
	'ärnum',
	'ersätt',
	'infoga',
	'index',
	'dela',
	'foga',
	'typ',
	'för',
	'medan',
	'epok',
	'tid',
	'nu',
	'sin',
	'cos',
	'tan',
	'asin',
	'acos',
	'atan',
	'potens',
	'tak',
	'golv',
	'fakultet',
	'kvadratrot',
	'log',
	'grader',
	'radianer',
	'datum',
	'idag',
	'veckodag',
	'värden',
	'element',
	'numrera',
	'öppna',
	'läs',
	'överför',
]
user_functions = []
keywords = [
	'annars',
	'inom',
	'bryt',
	'fortsätt',
	'returnera',
	'annars',
	'inte',
	'passera',
	'år',
	'månad',
	'dag',
	'timme',
	'minut',
	'sekund',
	'mikrosekund',
	'annars',
	'matte_e',
	'matte_pi',
	'och',
	'eller',
	'som',
]
operators = ['+', '-', '*', '/', '%', '<', '>', '=', '!', '.', ',', ')', ':', ';']

is_developer_mode = False
version = 3.0
repo_location = 'https://raw.githubusercontent.com/Enkelt/Enkelt/'
web_import_location = 'https://raw.githubusercontent.com/Enkelt/EnkeltBibliotek/master/bib/'

final = []
variables = []

tmp_variables = []
enkelt_script_path = ''


if is_web_editor is False:
	# Gets an env. variable to check if it's a test run.
	is_dev = os.getenv('ENKELT_DEV', False)
	
	# ----- START -----
	if not is_dev:
		try:
			if sys.version_info[0] < 3:
				raise Exception("Du måste använda Python version 3 eller högre")
			else:
				if len(sys.argv) >= 2:
					if '.e' in sys.argv[1]:
						enkelt_script_path = sys.argv[1]
					
					if len(sys.argv) >= 3:
						if sys.argv[2] == '--d':
							is_developer_mode = True
					
					with open(enkelt_script_path, 'r+')as f:
						tmp_code_to_run = f.readlines()
						
					while '' in tmp_code_to_run:
						tmp_code_to_run.pop(tmp_code_to_run.index(''))
					
					run_with_code(tmp_code_to_run)
					# Checks for updates:
					check_for_updates(version)
				else:
					variables = []
					final = []
					start_console(True)
		except Exception as e:
			print(e)
