import json
import time
import copy
import os


def load_artifacts(old_link, new_link):
	# Load the old and the new artifacts for proceseing.
	try:	
		old_lines = []
		f = open(old_link, 'r')
		old_lines = f.readlines()

		new_lines = []
		f = open(new_link, 'r')
		new_lines = f.readlines()
	except FileNotFoundError:
		return (None, None)

	return (old_lines, new_lines)


def load_artifact(file_path):
	try:
		lines = []
		with open(file_path, 'r') as f:
			lines = f.readlines()
		return lines
	except FileNotFoundError:
		return None


def load_json(file_path):
	with open(file_path) as jsonf:
		common_data = json.load(jsonf)
	return common_data


# Return a JSON of the file lines for
# easier comparison.
def get_file_json(file_name):
	current_sf = ''
	file_lines = load_artifact(file_name)
	new_hit_lines = {}
	for i in range(0, len(file_lines)):
		if file_lines[i].startswith('SF'):
			# Set the current source file to gather lines for
			current_sf = file_lines[i]
		if file_lines[i].startswith('DA'):
			# Get the line number
			line, line_count = file_lines[i].replace('DA:', '').split(',')
			if int(line_count) > 0:
				if current_sf not in new_hit_lines:
					new_hit_lines[current_sf] = []
				new_hit_lines[current_sf].append(int(line))

	return format_sfnames(new_hit_lines)


def check_testfiles(old_lines, new_lines):
	# Check if there are any differences in the test files.
	print('Checking test file differences...')

	# This will hold the differences at the end
	# of the run.
	# 'in_old': Files that are in the old file but not in the new one.
	# 'in_new': Files that are in the new file but not in the old one.
	differences = {
		'in_old': [],
		'in_new': []
	}

	# Get all the tests in the old file
	tests_old = []
	for i in range(0,len(old_lines)):
		if old_lines[i].startswith('TN'):
			tests_old.append(old_lines[i])

	# Check if they are in the new file
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

	# Check if the old file has any 
	# that aren't in the old file
	print('Checking old...')
	for i in tests_old:
		if i not in tests_new:
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
	# Checks for differences in source files
	print('Checking source file differences...')

	# This will hold the differences at the end
	# of the run.
	# 'in_old': Files that are in the old file but not in the new one.
	# 'in_new': Files that are in the new file but not in the old one.
	differences = {
		'in_old': [],
		'in_new': []
	}

	# Get the source files in the old file
	sfs_old = []
	multiples_old = False
	for i in range(0,len(old_lines)):
		if old_lines[i].startswith('SF'):
			if old_lines[i] in sfs_old:
				# If we found the source file twice, say so
				# and mark that we did in the data file.
				print('Multiple source file entries for:')
				print(old_lines[i])
				multiples_old = True
			sfs_old.append(old_lines[i])

	# Get the source files in the new file
	# and check it against the old file.
	print('Checking new...')
	sfs_new = []
	different = False
	multiples_new = False

	print(len(old_lines))
	print(len(new_lines))
	for i in range(0,len(new_lines)):
		if new_lines[i].startswith('SF'):
			if new_lines[i] in sfs_new:
				# If we found the source file twice, say so
				# and mark that we did in the data file.
				print('Multiple source file entries for:')
				print(new_lines[i])
				multiples_new = True
			# Save the source file
			sfs_new.append(new_lines[i])

			# Check if it's in the old source files,
			# if it's not print an error and store
			# it in a differences field.
			if new_lines[i] not in sfs_old:
				print('Big difference! Missing a source file in the old in comparison to new.')
				print('Source file: ')
				print(new_lines[i])
				different = True
				differences['in_new'].append(new_lines[i])

	# Check if there are any old source files
	# that are not in the new.
	print('Checking old...')
	for i in sfs_old:
		# Check if it's in the new source files,
		# if it's not print an error and store
		# it in a differences field.
		if i not in sfs_new:
				print('Big difference! Missing a source file in the new in comparison to old.')
				print('Source file: ')
				print(old_lines[i])
				different = True
				differences['in_old'].append(old_lines[i])

	print('Finished checking source file differences.')
	return {
		'all_sources_old': len(sfs_old),
		'all_sources_new': len(sfs_new),
		'different': different,
		'differences': differences,
		'different_multiples_old': multiples_old,
		'different_multiples_new': multiples_new,
		'new_sources': sfs_new, 
		'old_sources': sfs_old,
	}


# Returns the differences between the first
# and the second set given. Or those elements that are
# in the first but not the second one.
def diff(first, second):
		second = set(second)
		return [item for item in first if item not in second]


def check_lines(old_lines, new_lines, sfs):
	# Checks for differences in lines covered for the given source file

	# This will hold the differences at the end
	# of the run.
	# 'in_old': Files that are in the old file but not in the new one.
	# 'in_new': Files that are in the new file but not in the old one.
	differences = {}
	print('Checking lines...')

	# Holds the old and new lines that were hit for any source file that was found.
	old_hit_lines = {}
	new_hit_lines = {}

	# Holds the total number of lines that are in each source file for both old and new.
	total_new_count = {}
	total_old_count = {}

	# Initialize
	for i in range(0, len(sfs)):
		old_hit_lines[sfs[i]] = []
		new_hit_lines[sfs[i]] = []
		total_new_count[sfs[i]] = 0
		total_old_count[sfs[i]] = 0

	print('Getting old lines...')
	# Holds the current source file that we are looking at
	current_sf = ''
	for i in range(0, len(old_lines)):
		if old_lines[i].startswith('SF'):
			# Set the current source file to gather lines for
			current_sf = old_lines[i]
		if old_lines[i].startswith('DA'):
			# Get the line number
			line, line_count = old_lines[i].replace('DA:', '').split(',')
			# If we hit the line at least once, keep it
			if int(line_count) > 0:
				old_hit_lines[current_sf].append(int(line))
			# Increase total number of lines found in this file
			total_old_count[current_sf] += 1

	print('Getting new lines...')
	# Holds the current source file that we are looking at
	current_sf = ''
	for i in range(0, len(new_lines)):
		if new_lines[i].startswith('SF'):
			# Set the current source file to gather lines for
			current_sf = new_lines[i]
		if new_lines[i].startswith('DA'):
			# Get the line number
			line, line_count = new_lines[i].replace('DA:', '').split(',')
			if int(line_count) > 0:
				new_hit_lines[current_sf].append(int(line))
			# Increase total number of lines found in this file
			total_new_count[current_sf] += 1

	# Now that we have all the lines for old and new
	# we can compare them.
	print('Comparing lines...')

	# REMEMBER: Files that are not in the new file will
	# not be differenced here, they are added later.
	# Files that are in this file but not in the old one
	# will be kept but not compared.

	# For each new source file
	for sf in new_hit_lines:
		# If this source file is in the old, compare
		if sf in old_hit_lines:
			# If the number of lines in each of them is the same
			if len(new_hit_lines[sf]) == len(old_hit_lines[sf]):

				# Get the diff
				diff1 = diff(old_hit_lines[sf], new_hit_lines[sf])
				diff2 = diff(new_hit_lines[sf], old_hit_lines[sf])

				# If either of them are empty, there are differences
				if len(diff1) != 0 or len(diff2) != 0:
					print('Error, new and old lines for the source file:')
					print(sf)
					print('are not the same. Differences:')
					print('In old but not in new:')
					print(diff1)
					print('In new but not in old:')
					print(diff2)

					# Store the differences and the total line counts
					# for each source file
					differences[sf] = {
						'in_old': diff1,
						'in_new': diff2,
						'total_old': total_old_count[sf],
						'total_new': total_new_count[sf]
					}

			# Otherwise, there is definitely a difference
			else:
				# Get the differences
				diff1 = diff(old_hit_lines[sf], new_hit_lines[sf])
				diff2 = diff(new_hit_lines[sf], old_hit_lines[sf])

				print('Error, new and old lines for the source file:')
				print(sf)
				print('are not the same. Differences:')
				print('In old but not in new:')
				print(diff1)
				print('In new but not in old:')
				print(diff2)

				# Store the differences and the total line counts
				# for each source file
				differences[sf] = {
						'in_old': diff1,
						'in_new': diff2,
						'total_old': total_old_count[sf],
						'total_new': total_new_count[sf]
				}
		else:
			print('New file not in old...')
			# Store all the lines of the new file
			differences[sf] = {
						'in_old': [],
						'in_new': new_hit_lines[sf],
						'total_old': 0,
						'total_new': total_new_count[sf]
				}

	# Get the differences for the source files that are
	# in the old file but not the new one.
	for sf in old_hit_lines:
		if sf not in differences and sf not in new_hit_lines:
			# Store all the lines of the old file
			print('here now now ')
			differences[sf] = {
						'in_old': old_hit_lines[sf],
						'in_new': [],
						'total_old': total_old_count[sf],
						'total_new': 0
				}

	return differences


def format_sfnames(differences):
	# Removes the SF: and new line from the source file names
	new_differences = {}
	for sf in differences:
		new_sf = sf.replace('SF:', '', 1)
		new_sf = new_sf.replace('\n', '')
		new_differences[new_sf] = differences[sf]
	return new_differences


def save_single_json(data, name, output_dir=''):
	# Save a single json
	epoch_time = str(int(time.time()))
	with open(os.path.join(output_dir, name + '_' + epoch_time + '.json'), 'w+') as fp:
		json.dump(data, fp, sort_keys=True, indent=4)


def save_json(differences, tests_dict, sfs_dict, name='', output_dir=''):
	# Save the differences
	epoch_time = str(int(time.time()))
	with open(os.path.join(output_dir, name + '_data_line' + epoch_time + '.json'), 'w+') as fp:
		json.dump(differences, fp, sort_keys=True, indent=4)

	with open(os.path.join(output_dir, name + '_data_sources' + epoch_time + '.json'), 'w+') as fp:
		json.dump(sfs_dict, fp, sort_keys=True, indent=4)

	with open(os.path.join(output_dir, name + '_data_tests' + epoch_time + '.json'), 'w+') as fp:
		json.dump(tests_dict, fp, sort_keys=True, indent=4)


# Runs through everything
def get_diff(old_link, new_link, name='', output_dir='', save_the_data=True):
	print ('name: ' + name)
	# Load the artifacts
	(old_lines, new_lines) = load_artifacts(old_link, new_link)
	if old_lines is None and new_lines is None:
		return (None, None, None)

	# Check tests
	print ('name: ' + name)
	tests_dict = check_testfiles(old_lines, new_lines)
	# Check sources
	print ('name: ' + name)
	sfiles_dict = check_sourcefiles(old_lines, new_lines)
	# Check line differences
	print ('name: ' + name)
	differences = check_lines(old_lines, new_lines, sfiles_dict['new_sources'])

	# Reformat the source file names
	differences1 = format_sfnames(differences)
	print ('name: ' + name)
	# Save the differences
	if save_the_data:
		save_json(differences1, tests_dict, sfiles_dict, name=name, output_dir=output_dir)

	return (differences, sfiles_dict, tests_dict)
