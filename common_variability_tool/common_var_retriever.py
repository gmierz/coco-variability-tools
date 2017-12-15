from diff_two import get_diff, save_single_json, format_sfnames, load_artifact, get_file_json
import os
import time
import csv
import json
import sys
import argparse


def artifact_aggregate_diffs_parser():
	parser = argparse.ArgumentParser(description='Diff a set of runs of the same test suite and chunk ' +
												 'and aggregate all common variability.')
	parser.add_argument('--dir', '-d', type=str, nargs=1,
						help='This field is for setting the directory to where we can find' +
						' all of the data files. It should contain all the grcov data, suffixed' +
						' by a number from 0 to the number of files specified by --number, or -n.' +
						' ex: grcov_lcov_output_stdout0.info, grcov_lcov_output_stdout1.info, ...')
	parser.add_argument('--number', '-n', type=int, nargs=1,
						help='This field is for setting the total number of data files that should' +
						' be processed.')
	parser.add_argument('--exclude', type=int, nargs='*',
						help='List of datasets that will be excluded. Starting from 0 to' +
						' number of files specified by --number.')
	parser.add_argument('--output', type=str, nargs=1,
						help='Where the output should be stored. By default, it is set to the current' +
						' working directory.')
	return parser


def merge_lines(lines1, lines2, old_counts=[]):
	# Old counts is used for lines1 if it is given.
	new_lines = []
	counts = []
	new_lines1 = lines1
	old_count_flag = 0 if len(old_counts) == 0 else 1

	# Get all the lines in lines1, or in both:
	for line in lines1:
		new_lines.append(line)
		count = 1 - old_count_flag
		if line in lines2:
			lines2.remove(line)
			# 1 signifies that a line was in both
			count = 2 - old_count_flag
		counts.append(count)

	# Add old counts to the list if they exist
	if len(old_counts) != 0:
		counts = [counts[i]+old_counts[i] for i in range(0, len(counts))]

	# Get all the lines that were only in lines2:
	if len(lines2) != 0:
		for line in lines2:
			new_lines.append(line)
			counts.append(1)

	return (new_lines, counts)

file_counter = 0
def merge_commons_diffs(diff_new, diff_old, name='', output_dir='', save_the_data=True):
	# diff_old should be the previously processed file, it has additional fields
	if len(diff_old) == 0:
		return diff_new

	# First, check if the same source files are in both.
	# If not, remove those which aren't in both from the overall result.
	# Start by going through the previously processed dict.
	not_variable = {}
	new_diff_old = {}
	for entry in diff_old:
		if entry in diff_new:
			new_diff_old[entry] = diff_old[entry]
		else:
			# Those entries which are not in the new differences
			# are not variable in this merge.
			not_variable[entry] = diff_old[entry]
			if 'appearance_list' not in not_variable[entry]:
				not_variable[entry]['appearance_list'] = [name]
			else:
				not_variable[entry]['appearance_list'].append(name)
	diff_old = new_diff_old

	# Now go through the new one and remove all entries that are not in the old.
	new_diff_new = {}
	now_variable = {}
	for entry in diff_new:
		if entry in diff_old:
			new_diff_new[entry] = diff_new[entry]
		else:
			# These entries are differences which
			# are new and have only just now popped
			# up.
			now_variable[entry] = diff_new[entry]
			if 'appearance_list' not in now_variable[entry]:
				now_variable[entry]['appearance_list'] = [name]
			else:
				now_variable[entry]['appearance_list'].append(name)
	diff_new = new_diff_new

	def union(a, b, c=[]):
		return list(set().union(a, b, c))

	# Now both of the diffs have the same source files, compare their lines and keep the
	# lines which appear in both
	diff_ret = {}
	for entry in diff_old:
		new_entry = diff_new[entry]
		old_entry = diff_old[entry]

		# Get previous appearances if they exist
		new_appearance = new_entry['appearance_list'] if 'appearance_list' in new_entry else []
		old_appearance = old_entry['appearance_list'] if 'appearance_list' in old_entry else []

		# Merge the differences, keeping all lines. and a count for occurrence.
		lines = []
		counts = []

		# Merge new and old lines together.
		# Counts will always be 1 here as the differences are completely unique.
		# In other words, we don't need to care about them and they will be taken
		# care of in the next call to merge_lines. This will happen either in the 
		# next iteration or if we find 'differences_lines' in old_entry.
		(lines, counts) = merge_lines(new_entry['in_new'], new_entry['in_old'])

		# If we already have difference lines in diff_old, merge those with the old
		# and add the counts together.
		if 'differences_lines' in old_entry:
			(merged, new_counts) = merge_lines(old_entry['differences_lines'], lines, old_entry['differences_counts'])
			lines = merged
			counts = new_counts

		diff_ret[entry] = {
			'appearance_list': union(new_appearance, old_appearance, [name]),
			'differences_lines': lines,
			'differences_counts': counts
		}

	# Add all the entries which are either no longer variable
	# or just became variable.
	for entry in not_variable:
		if 'differences_lines' in not_variable[entry]:
			diff_ret[entry] = not_variable[entry]
		else:
			line_unions = union(not_variable[entry]['in_new'], not_variable[entry]['in_old'])
			diff_ret[entry] = {
				'appearance_list': not_variable[entry]['appearance_list'],
				'differences_lines': line_unions,
				'differences_counts': [1 for x in line_unions]
			}
	for entry in now_variable:
		if 'differences_lines' in now_variable[entry]:
			diff_ret[entry] = now_variable[entry]
		else:
			line_unions = union(now_variable[entry]['in_new'], now_variable[entry]['in_old'])
			diff_ret[entry] = {
				'appearance_list': now_variable[entry]['appearance_list'],
				'differences_lines': line_unions,
				'differences_counts': [1 for x in line_unions]
			}

	if save_the_data:
		epoch_time = str(int(time.time()))
		with open(os.path.join(output_dir, 'file_' + name + '_' + epoch_time + '.json'), 'w+') as fp:
			json.dump(diff_ret, fp, sort_keys=True, indent=4)
	return diff_ret

def get_common_var_file(starter_dir, exclude, output_dir='', number=0, save_the_data=False):
	print('save the data: ' + str(save_the_data))
	if number == 0:
		files = [f for f in os.listdir(starter_dir) if os.path.isfile(os.path.join(starter_dir, f))]
		for file in files:
			if 'grcov_lcov_output_stdout' in file:
				number += 1
		if number < 3:
			print('Error, couldn`t find any/enough data files in the directory (needs at least 2): ' + starter_dir)
			return None

	all_differences = {}
	differences = {}
	for i in range(0, number-1):
		if i not in exclude:
			curr_path = os.path.join(starter_dir, 'grcov_lcov_output_stdout' + str(i) + '.info')
			diff_path = os.path.join(starter_dir, 'grcov_lcov_output_stdout' + str(i+1) + '.info')
			name = str(i) + 'vs' + str(i+1)
			all_differences[name] = {}
			# Get the difference
			all_differences[name]['differences'], all_differences[name]['sfiles_dict'], all_differences[name]['tests_dict'] = \
				get_diff(curr_path, diff_path, name=name, output_dir=output_dir, save_the_data=save_the_data)
			if all_differences[name]['sfiles_dict'] is None:
				# Bad dataset, go to the next one
				continue
			# Merge the differences into common variability
			print(name)
			differences = merge_commons_diffs(all_differences[name]['differences'], differences, name=name, output_dir=output_dir, \
				save_the_data=save_the_data)

	meta_data = {
		'total_number_processed': number,
		'data_dir': starter_dir
	}

	new_differences = format_sfnames(differences)

	meta_differences = {
		'differences': new_differences,
		'meta-data': meta_data
	}
	if save_the_data:
		save_single_json(meta_differences, 'common_vars_file_', output_dir=output_dir)

	return meta_differences


def get_common_file(starter_dir, exclude, output_dir='', number=0, save_the_data=False):
	print('save the data: ' + str(save_the_data))
	if number == 0:
		files = [f for f in os.listdir(starter_dir) if os.path.isfile(os.path.join(starter_dir, f))]
		for file in files:
			if 'grcov_lcov_output_stdout' in file:
				number += 1
		if number < 3:
			print('Error, couldn`t find any/enough data files in the directory (needs at least 2): ' + starter_dir)
			return None

	common_lines = {}
	first = True
	for i in range(0, number-1):
		if i not in exclude:
			curr_path = os.path.join(starter_dir, 'grcov_lcov_output_stdout' + str(i) + '.info')
			if not os.path.exists(curr_path):
				continue

			file_json = get_file_json(curr_path)

			if first:
				common_lines = file_json
				continue

			for sf in file_json:
				if sf not in common_lines:
					common_lines[sf] = file_json[sf]
				else:
					file_lines = file_json[sf]
					for line_num in file_lines:
						if line_num not in common_lines[sf]:
							common_lines[sf].append(line_num)

	for sf in common_lines:
		common_lines[sf].sort()

	return format_sfnames(common_lines)
			

def main():
	# Start with a directory containing all the GRCOV data from multiple runs of the same test suite
	# and same chunk.

	# When running, first differences found is never in 'file_'. It is in the 'data_line' and 'data_source' files.
	starter_dir = os.getcwd()
	number = 0
	for dp, dirs, files, in os.walk(starter_dir):
		for file in files:
			if 'grcov_lcov_output_stdout' in file:
				number += 1
	if number == 0:
		print('Error, couldn`t find any data files, directory: ' + starter_dir)
	exclude = [16]
	print(starter_dir)

	args = parser.parse_args()
	if args.dir is not None and args.number is not None:
		starter_dir = args.dir[0]
		number = args.number[0]
		exclude = args.exclude if args.exclude is not None else []
		print('Printing args')
		print(starter_dir)
		print(number)
		print(exclude)
	else:
		print('Proper arguments not given, will continue based on defaults.')

	if args.output is not None:
		output_dir = args.output[0]
		print(output_dir)
	else:
		output_dir = os.getcwd()
		print('Output directory not given, data will be saved in the current working directory.')


if __name__ == '__main__':
	main()