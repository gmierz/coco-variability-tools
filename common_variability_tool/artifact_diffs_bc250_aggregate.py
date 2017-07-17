import os
import time
import csv
import json
import sys
import argparse

output_dir = os.getcwd()
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

# Get all the old artifacts, and process them into a data structure.
# Check for differences in source files used first, then check for
# differences at a finer granularity.

def check_testfiles(old_lines, new_lines):
	print('Checking test file differences...')
	differences = {
		'in_old': [],
		'in_new': []
	}

	tests_old = []
	for i in range(0,len(old_lines)):
		if old_lines[i].startswith('TN'):
			tests_old.append(old_lines[i])

	print('Checking new...')
	tests_new = []
	different = False
	print(len(old_lines))
	print(len(new_lines))
	for i in range(0,len(new_lines)):
		if new_lines[i].startswith('TN'):
			tests_new.append(new_lines[i])
			if new_lines[i] not in tests_old:
				print('Big difference! Missing a test file in the old in comparison to new.')
				print('Test file: ')
				print(new_lines[i])
				different = True
				differences['in_new'].append(new_lines[i])

	print('Checking old...')
	for i in range(0, len(old_lines)):
		if old_lines[i].startswith('TN') and (old_lines[i] not in tests_new):
				print('Big difference! Missing a test file in the new in comparison to old.')
				print('Test file: ')
				print(old_lines[i])
				different = True
				differences['in_old'].append(old_lines[i])

	print('Finished checking test file differences.')
	return {
		'different': different,
		'differences': differences,
		'old_tests': tests_old,
		'new_tests': tests_new
	}

def check_sourcefiles(old_lines, new_lines):
	print('Checking source file differences...')
	differences = {
		'in_old': [],
		'in_new': []
	}

	sfs_old = []
	multiples_old = False
	for i in range(0,len(old_lines)):
		if old_lines[i].startswith('SF'):
			if old_lines[i] in sfs_old:
				print('Multiple source file entries for:')
				print(old_lines[i])
				multiples_old = True
			sfs_old.append(old_lines[i])

	print('Checking new...')
	sfs_new = []
	different = False
	multiples_new = False
	print(len(old_lines))
	print(len(new_lines))
	for i in range(0,len(new_lines)):
		if new_lines[i].startswith('SF'):
			if new_lines[i] in sfs_new:
				print('Multiple source file entries for:')
				print(new_lines[i])
				multiples_new = True
			sfs_new.append(new_lines[i])
			if new_lines[i] not in sfs_old:
				print('Big difference! Missing a source file in the old in comparison to new.')
				print('Source file: ')
				print(new_lines[i])
				different = True
				differences['in_new'].append(new_lines[i])

	print('Checking old...')
	for i in range(0, len(old_lines)):
		if old_lines[i].startswith('SF') and (old_lines[i] not in sfs_new):
				print('Big difference! Missing a source file in the new in comparison to old.')
				print('Source file: ')
				print(old_lines[i])
				different = True
				differences['in_old'].append(old_lines[i])

	print('Finished checking source file differences.')
	return {
		'different': different,
		'differences': differences,
		'different_multiples_old': multiples_old,
		'different_multiples_new': multiples_new,
		'new_sources': sfs_new, 
		'old_sources': sfs_old,
	}

def diff(first, second):
		second = set(second)
		return [item for item in first if item not in second]

def check_lines(old_lines, new_lines, sfs):
	differences = {}
	print('Checking lines...')
	old_hit_lines = {}
	new_hit_lines = {}
	for i in range(0, len(sfs)):
		old_hit_lines[sfs[i]] = []
		new_hit_lines[sfs[i]] = []

	print('Getting old lines...')
	current_sf = ''
	for i in range(0, len(old_lines)):
		if old_lines[i].startswith('SF'):
			current_sf = old_lines[i]
		if old_lines[i].startswith('DA'):
			line, line_count = old_lines[i].replace('DA:', '').split(',')
			if int(line_count) > 0:
				old_hit_lines[current_sf].append(int(line))

	print('Getting new lines...')
	current_sf = ''
	for i in range(0, len(new_lines)):
		if new_lines[i].startswith('SF'):
			current_sf = new_lines[i]
		if new_lines[i].startswith('DA'):
			line, line_count = new_lines[i].replace('DA:', '').split(',')
			if int(line_count) > 0:
				new_hit_lines[current_sf].append(int(line))

	print('Comparing lines...')
	for sf in new_hit_lines:
		if len(new_hit_lines[sf]) == len(old_hit_lines[sf]):
			diff1 = diff(old_hit_lines, new_hit_lines)
			diff2 = diff(new_hit_lines, old_hit_lines)
			if len(diff1) != 0 or len(diff2) != 0:
				print('Error, new and old lines for the source file:')
				print(sf)
				print('are not the same. Differences:')
				print('In old but not in new:')
				print(diff1)
				print('In new but not in old:')
				print(diff2)

				differences[sf] = {
					'in_old': diff1,
					'in_new': diff2
				}
		else:
			diff1 = diff(old_hit_lines[sf], new_hit_lines[sf])
			diff2 = diff(new_hit_lines[sf], old_hit_lines[sf])
			print('Error, new and old lines for the source file:')
			print(sf)
			print('are not the same. Differences:')
			print('In old but not in new:')
			print(diff1)
			print('In new but not in old:')
			print(diff2)

			differences[sf] = {
					'in_old': diff1,
					'in_new': diff2
			}

	return differences


def load_artifacts(old_link, new_link):
	old_lines = []
	f = open(old_link, 'r')
	old_lines = f.readlines()

	new_lines = []
	f = open(new_link, 'r')
	new_lines = f.readlines()

	return (old_lines, new_lines)

def save_data(tests, sfiles, differences):
	epoch_time = str(int(time.time()))
	name_sf = 'saved_differences_sources' + epoch_time + '.csv'
	name_old = 'saved_differences_in_old_not_new' + epoch_time + '.csv'
	name_new = 'saved_differences_in_new_not_old' + epoch_time + '.csv'
	with open(name_new, 'w+') as olddiff:
		writer_old = csv.writer(olddiff, delimiter=",")

		with open(name_old, 'w+') as newdiff:
			writer_new = csv.writer(newdiff, delimiter=",")

			with open(name_sf, 'w+') as sourcefile:
				writer_sf = csv.writer(sourcefile, delimiter=",")
				for i in differences:
					writer_sf.writerow([i])
					writer_new.writerow(differences[i]['in_new'])
					writer_old.writerow(differences[i]['in_old'])

def format_sfnames(differences):
	new_differences = {}
	for sf in differences:
		new_sf = sf.replace('SF:', '', 1)
		new_sf = new_sf.replace('\n', '')
		new_differences[new_sf] = differences[sf]
	return new_differences

def save_json(differences, tests_dict, sfs_dict, name=''):
	epoch_time = str(int(time.time()))
	with open(os.path.join(output_dir, 'data_line_' + name + '_' + epoch_time + '.json'), 'w+') as fp:
		json.dump(differences, fp, sort_keys=True, indent=4)

	with open(os.path.join(output_dir, 'data_sources_' + name + '_' + epoch_time + '.json'), 'w+') as fp:
		json.dump(sfs_dict, fp, sort_keys=True, indent=4)

	with open(os.path.join(output_dir, 'data_tests_' + name + '_' + epoch_time + '.json'), 'w+') as fp:
		json.dump(tests_dict, fp, sort_keys=True, indent=4)


def get_diff(old_link, new_link, name=''):
	(old_lines, new_lines) = load_artifacts(old_link, new_link)
	tests_dict = check_testfiles(old_lines, new_lines)
	sfiles_dict = check_sourcefiles(old_lines, new_lines)
	differences = check_lines(old_lines, new_lines, sfiles_dict['new_sources'])
	differences = format_sfnames(differences)
	save_json(differences, tests_dict, sfiles_dict, name)
	return (differences, sfiles_dict, tests_dict)

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
def merge_commons_diffs(diff_new, diff_old, name=''):
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
			not_variable[entry] = diff_old[entry]
	diff_old = new_diff_old

	# Now go through the new one and remove all entries that are not in the old.
	new_diff_new = {}
	now_variable = {}
	for entry in diff_new:
		if entry in diff_old:
			new_diff_new[entry] = diff_new[entry]
		else:
			now_variable[entry] = diff_new[entry]
	diff_new = new_diff_new

	# Now both of the diffs have the same source files, compare their lines and keep the
	# lines which appear in both
	diff_ret = {}
	for entry in diff_old:
		new_entry = diff_new[entry]
		old_entry = diff_old[entry]
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
			'differences_lines': lines,
			'differences_counts': counts
		}

	for entry in not_variable:
		diff_ret[entry] = not_variable[entry]
	for entry in now_variable:
		diff_ret[entry] = now_variable[entry]

	epoch_time = str(int(time.time()))
	with open(os.path.join(output_dir, 'file_' + name + '_' + epoch_time + '.json'), 'w+') as fp:
		json.dump(diff_ret, fp, sort_keys=True, indent=4)
	return diff_ret


if __name__ == '__main__':
	# Start with a directory containing all the GRCOV data from multiple runs of the same test suite
	# and same chunk.

	# When running, first differences found is never in 'file_'. It is in the 'data_line' and 'data_source' files.
	starter_dir = os.getcwd()
	number = 50
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
		print('Output directory not given, data will be saved in the current working directory.')

	dirs = os.listdir(starter_dir)
	all_differences = {}
	differences = {}
	for i in range(0, number):
		if i in exclude:
			curr_path = os.path.join(starter_dir, 'grcov_lcov_output_stdout' + str(i) + '.info')
			diff_path = os.path.join(starter_dir, 'grcov_lcov_output_stdout' + str(i+1) + '.info')
			name = str(i) + 'vs' + str(i+1)
			all_differences[name] = {}
			all_differences[name]['differences'], all_differences[name]['sfiles_dict'], all_differences[name]['tests_dict'] = \
				get_diff(curr_path, diff_path, name)
			differences = merge_commons_diffs(all_differences[name]['differences'], differences, name)