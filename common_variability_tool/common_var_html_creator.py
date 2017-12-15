from diff_two import format_sfnames
from bs4 import BeautifulSoup
from operator import itemgetter
import http
import urllib
import urllib.request as urllib2
import argparse
import os
import json


def html_creator_parser():
	parser = argparse.ArgumentParser("Parse a common variability file 'common_vars_file' into a simple "
									 "html report.")
	parser.add_argument('--common-vars-file', type=str, nargs=1,
						help='The common_vars_file that will be parsed into an html report.')
	parser.add_argument('--revision', type=str, nargs=1,
						help='The revision (changeset) which this analysis is based/run on.')
	parser.add_argument('--output', type=str, nargs=1,
						help='Where the output should be stored. By default, it is set to the current' +
						' working directory.')
	return parser


def get_file_info_commonvar(common_var_diff, rev=None, file=''):
	# Common_var_diff is a file called 'common_vars_file_'
	# that is made at the end of get_common_var_file. There
	# should be an entry for file in it

	# Get the information about file, sort the lines and display.
	file_info = common_var_diff['differences'][file]
	all_var_lines_counts = list(zip(file_info['differences_counts'], file_info['differences_lines']))
	print(all_var_lines_counts)
	sorted_var_lines = sorted(all_var_lines_counts, key=itemgetter(1))
	print(sorted_var_lines)
	if not sorted_var_lines:
		return """ """

	sorted_counts, sorted_lines = map(list,zip(*sorted_var_lines))

	total_compares = common_var_diff['meta-data']['total_number_processed']

	url = "https://hg.mozilla.org/try/complete-file/" + rev + "/" + file

	try:
		print(url)
		content = urllib2.urlopen(url).read()
		soup = BeautifulSoup(content, "html.parser")
		lines = (soup.findAll("pre", class_="sourcelines stripes"))

		# Get the lines
		lines_text = []
		for el in lines:
			for line in el.findAll(text=True):
				lines_text.append(str(line))

		# Reformat the lines.
		count = 0
		curr_line = ''
		formatted_lines = []
		for line in lines_text:
			if count == 0 and line == '\n':
				count = count + 1
				continue
			elif line == '\n':
				formatted_lines.append(curr_line)
				curr_line = ''
			else:
				curr_line += line
			count = count + 1
		if curr_line != '':
			formatted_lines.append(curr_line)

		styled_lines = ''
		for i in range(0, len(sorted_lines)):
			line = sorted_lines[i]
			line_count = sorted_counts[i]
			line_content = formatted_lines[int(line)-1]
			styled_lines += """
				<tr>
					<td> """ + str(line) + """ </td>
					<td> """ + str(line_content) + """ </td>
					<td> """ + str(line_count) + """ </td>
				</tr>
			"""
	except urllib.error.HTTPError:
		print("Couldn't find this file in hg.")
		styled_lines = """
			<tr>
				<td colspan="3"> Error: Couldn't find the file in hg. </td>
			</tr>
		"""

	# Return an html blob for this file.
	return """
	<div>
		<table border="1"> 
			<tr>
				<td colspan="2"> 
					<div> 
						<table>
							<tr> <td> """ + file + """ </td> </tr>
							<tr> <td> <a href=" """ + url + """ ">Hg Link</a> </td> </tr>
							<tr> <td> Variability-index: """ + str(max(sorted_counts)/total_compares) + """ </td> </tr>
							<tr> <td> Total Files Compared: """ + str(total_compares) + """ </td> </tr>
						</table>
					</div>
				</td>
				<td> Times Different </td>
			</tr>
		""" + styled_lines + """
		</table>
	</div>
	"""

# Accepts a simple JSON with source file keys
# and lines as the entries.
def get_file_info_simple(commons, rev=None, file=''):
	# Get the information about file, sort the lines and display.
	commons[file].sort()
	sorted_lines = commons[file]
	print(sorted_lines)
	if not sorted_lines:
		return """ """

	url = "https://hg.mozilla.org/try/complete-file/" + rev + "/" + file

	try:
		print(url)
		content = urllib2.urlopen(url).read()
		soup = BeautifulSoup(content, "html.parser")
		lines = (soup.findAll("pre", class_="sourcelines stripes"))

		# Get the lines
		lines_text = []
		for el in lines:
			for line in el.findAll(text=True):
				lines_text.append(str(line))

		# Reformat the lines.
		count = 0
		curr_line = ''
		formatted_lines = []
		for line in lines_text:
			if count == 0 and line == '\n':
				count = count + 1
				continue
			elif line == '\n':
				formatted_lines.append(curr_line)
				curr_line = ''
			else:
				curr_line += line
			count = count + 1
		if curr_line != '':
			formatted_lines.append(curr_line)

		styled_lines = ''
		for i in range(0, len(sorted_lines)):
			line = sorted_lines[i]
			line_content = formatted_lines[int(line)-1]
			styled_lines += """
				<tr>
					<td> """ + str(line) + """ </td>
					<td> """ + str(line_content) + """ </td>
				</tr>
			"""
	except urllib.error.HTTPError:
		print("Couldn't find this file in hg.")
		styled_lines = """
			<tr>
				<td colspan="3"> Error: Couldn't find the file in hg. </td>
			</tr>
		"""

	# Return an html blob for this file.
	return """
	<div>
		<table border="1"> 
			<tr>
				<td colspan="2"> 
					<div> 
						<table>
							<tr> <td> """ + file + """ </td> </tr>
							<tr> <td> <a href=" """ + url + """ ">Hg Link</a> </td> </tr>
						</table>
					</div>
				</td>
				<td> Times Different </td>
			</tr>
		""" + styled_lines + """
		</table>
	</div>
	"""


def get_html(common_vars, rev=None):
	file_infos = ''
	# Format names just incase
	if 'differences' in common_vars:
		common_vars['differences'] = format_sfnames(common_vars['differences'])
		for file in common_vars['differences']:
			file_infos += get_file_info_commonvar(common_vars, rev=rev, file=file)
	else:
		# We have a simple display to do
		for file in common_vars:
			file_infos += get_file_info_simple(common_vars, rev=rev, file=file)
	return """
	<!DOCTYPE html>
	<html>
		<head>
			<meta charset="UTF-8">
		</head>

		<body>
			<div>
				<h1> Variability Analysis </h1>
			</div> """ + \
			file_infos + """
		</body>
	</html>
	"""


def main():
	parser = html_creator_parser()
	args = parser.parse_args()

	rev = args.revision[0]
	common_vars_path = args.common_vars_file[0]
	output = args.output[0]

	if rev is None:
		raise Exception("Error, revision should be given.")
	if common_vars_path is None:
		raise Exception("Error, path to common_vars_file must be given.")
	if output is None:
		output = os.getcwd()

	data = None
	with open(common_vars_path) as jsonf:
		data = json.load(jsonf)

	html_file = get_html(data, rev=rev)

	output_file = os.path.join(output, 'variability_index.html')
	with open(output_file, 'w+') as html_out:
		html_out.write(html_file)
	print('Saved to: ' + output_file)


if __name__ == '__main__':
	main()