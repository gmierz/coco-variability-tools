from html.parser import HTMLParser
import argparse
import json
import time
import copy


parser = argparse.ArgumentParser(description='Diff two runs and compare differences while ' +
											 'taking common variability into account.')
parser.add_argument('--path-to-old', '-po', type=str, nargs=1,
					help='The path that points to a GRCOV file from an `older` run that was either ' +
						 'a part of the variability analyisis, or a different one altogether.')
parser.add_argument('--path-to-new', '-pn', type=str, nargs=1,
					help='The path to the newer GRCOV file that will be compared with to determine ' +
					'differences that are unique and not due to inherent variability.')
parser.add_argument('--variability-json', '-vj', type=str, nargs=1,
					help='The path to the json that contains the variability data for this test suite' +
					' and chunk.')

def load_artifacts(old_link, new_link):
	old_lines = []
	f = open(old_link, 'r')
	old_lines = f.readlines()

	new_lines = []
	f = open(new_link, 'r')
	new_lines = f.readlines()

	return (old_lines, new_lines)

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
		'all_sources_old': len(sfs_old),
		'all_sources_new': len(sfs_new),
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
	total_new_count = {}
	total_old_count = {}
	for i in range(0, len(sfs)):
		old_hit_lines[sfs[i]] = []
		new_hit_lines[sfs[i]] = []
		total_new_count[sfs[i]] = 0
		total_old_count[sfs[i]] = 0

	print('Getting old lines...')
	current_sf = ''
	for i in range(0, len(old_lines)):
		if old_lines[i].startswith('SF'):
			current_sf = old_lines[i]
		if old_lines[i].startswith('DA'):
			line, line_count = old_lines[i].replace('DA:', '').split(',')
			# If we hit the line at least once
			if int(line_count) > 0:
				old_hit_lines[current_sf].append(int(line))
			# Increase total number of lines found in this file
			total_old_count[current_sf] += 1

	print('Getting new lines...')
	current_sf = ''
	for i in range(0, len(new_lines)):
		if new_lines[i].startswith('SF'):
			current_sf = new_lines[i]
		if new_lines[i].startswith('DA'):
			line, line_count = new_lines[i].replace('DA:', '').split(',')
			if int(line_count) > 0:
				new_hit_lines[current_sf].append(int(line))
			# Increase total number of lines found in this file
			total_new_count[current_sf] += 1

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
					'in_new': diff2,
					'total_old': total_old_count[sf],
					'total_new': total_new_count[sf]
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
					'in_new': diff2,
					'total_old': total_old_count[sf],
					'total_new': total_new_count[sf]
			}

	return differences

def format_sfnames(differences):
	new_differences = {}
	for sf in differences:
		new_sf = sf.replace('SF:', '', 1)
		new_sf = new_sf.replace('\n', '')
		new_differences[new_sf] = differences[sf]
	return new_differences

def save_single_json(data, name):
	epoch_time = str(int(time.time()))
	with open(name + '_' + epoch_time + '.json', 'w+') as fp:
		json.dump(data, fp, sort_keys=True, indent=4)

def save_json(differences, tests_dict, sfs_dict):
	epoch_time = str(int(time.time()))
	with open('data_line' + epoch_time + '.json', 'w+') as fp:
		json.dump(differences, fp, sort_keys=True, indent=4)

	with open('data_sources' + epoch_time + '.json', 'w+') as fp:
		json.dump(sfs_dict, fp, sort_keys=True, indent=4)

	with open('data_tests' + epoch_time + '.json', 'w+') as fp:
		json.dump(tests_dict, fp, sort_keys=True, indent=4)

def filter_commons(differences, common_var_file):
	# Load common vars file
	with open(common_var_file) as jsonf:
		common_data = json.load(jsonf)

	# Now we have all the differences, filter
	# out the lines in the files which have common variability.
	# If they are now empty, leave a trace so we can tell.

	# Go through the differences, and for each sf, get the
	# lines which are commonly variable for it. Then,
	# remove these commonly variable lines from the differences.

	# For each source file
	new_differences = {}
	for sf in differences:
		sf_dict = differences[sf]
		new_differences[sf] = {}
		new_sf = {}
		new_line_data_list = []
		condition = 'not_variability'
		# Get it in the commmonly different
		if sf in common_data:
			tmp_sf = copy.deepcopy(sf_dict)
			condition = 'possible_variability'
			# Holds common data about this file
			sf_commons = common_data[sf]

			# For each entry in old and new, aggregate them
			# while looking for commonly variable, and 
			# not commonly variable. `new_line_data_list`
			# will always have unique entries.
			for i in sf_dict['in_old']:
				if 'differences_lines' in sf_commons: # Bug in commons file
					if i in sf_commons['differences_lines']:
						# Commonly variable line, set new data to tell this.
						new_line_data = (i, 'variable')
						sf_commons['differences_lines'].remove(i)
					else:
						new_line_data = (i, 'not_variable')
					new_line_data_list.append(new_line_data)

			for i in sf_dict['in_new']:
				if 'differences_lines' in sf_commons: # Bug in commons file
					if i in sf_commons['differences_lines']:
						# Commonly variable line, set new data to tell this.
						new_line_data = (i, 'variable')
						sf_commons['differences_lines'].remove(i)
					else:
						new_line_data = (i, 'not_variable')
					new_line_data_list.append(new_line_data)

			# Now, we have a list of lines that were different between the two
			# and they are annotated with information on whether or not the
			# lines that are commonly variable. Save these to process them
			# again later.

		# Or leave it as a new difference
		else:
			for i in sf_dict['in_old']:
				new_line_data = (i, 'not_variable')
				new_line_data_list.append(new_line_data)

			for i in sf_dict['in_new']:
				new_line_data = (i, 'not_variable')
				new_line_data_list.append(new_line_data)

		# Set the new differences.
		new_sf['condition'] = condition
		new_sf['differences'] = new_line_data_list
		#print(new_sf)
		new_differences[sf] = new_sf
	return new_differences

def intersection(a, b):
	return list(set(a).intersection(b))

def split_var_and_nonvar(differences, old_differences):
	# Run this on the differences obtained from filter_commons.
	# Each line in each of the differences is annotated as a tuple.
	# Let's split this data into four groups:
	#	1. Source files with variability
	#	2. Source files with no variability.
	#	3. Source files with lines from variability.
	#	4. Source files with lines from non-variability.
	#
	# old_differences has the 'in_old' and 'in_new' so that
	# we can distinguish between the two.

	sf_variable = []			# 1. List
	sf_nonvariable = []			# 2. List
	sf_both = []				# X. List for files which have variability and non-variability
	sf_lines_variable = {}		# 3. Dict
	sf_lines_nonvariable = {}	# 4. Dict

	# For each source file
	for sf in differences:
		sf_lines_nonvariable[sf] = {}
		sf_lines_variable[sf] = {}

		# Check if it has variability
		if differences[sf]['condition'] == 'possible_variability':
			# There is a chance that this file has no variability.
			variable_coverage = True
			variable_and_non = True

			# Store the different lines in two buckets.
			sf_line_diffs_variable = []
			sf_line_diffs_nonvariable = []

			# Go through the differences and separate based on flag.
			# This gives us per-sf information.
			for (line, variability_flag) in differences[sf]['differences']:
				if variability_flag == 'variable':
					# Found a variable line.
					sf_line_diffs_variable.append(line)
				else:
					# Found a nonvariable line
					sf_line_diffs_nonvariable.append(line)
			# If we did not find any common variability.
			if len(sf_line_diffs_variable) == 0:
				variable_coverage = False
				variable_and_non = False
			elif len(sf_line_diffs_nonvariable) == 0:
				variable_coverage = True
				variable_and_non = False
			# Else we have variable and non-variable coverage mixed.

			# Add all these fields to both regardless of variability.
			# Gives all the lines that are non variable and in the old differences.
			sf_lines_nonvariable[sf]['in_old'] = intersection(sf_line_diffs_nonvariable, old_differences[sf]['in_old'])
			# Gives all the lines that are non variable and in the new differences.
			sf_lines_nonvariable[sf]['in_new'] = intersection(sf_line_diffs_nonvariable, old_differences[sf]['in_new'])

			# Gives all the lines that are variable and in the old differences.
			sf_lines_variable[sf]['in_old'] = intersection(sf_line_diffs_variable, old_differences[sf]['in_old'])
			# Gives all the lines that are variable and in the new differences.
			sf_lines_variable[sf]['in_new'] = intersection(sf_line_diffs_variable, old_differences[sf]['in_new'])

			# Add the source file to one of the two datasets
			# depending on whether it has variability or not.
			if variable_and_non:
				sf_both.append(sf)
			elif variable_coverage:
				sf_variable.append(sf)
			else:
				sf_nonvariable.append(sf)

		# Otherwise, this file has no common variability, set the fields to as
		# what they were originally.
		else:
			sf_nonvariable.append(sf)

			# Reset the old and new line fields.
			sf_lines_nonvariable[sf]['in_old'] = old_differences[sf]['in_old']
			sf_lines_nonvariable[sf]['in_new'] = old_differences[sf]['in_new']

	# Save each dataset individually.
	print('Saving data...')
	save_single_json({'variable_sources': sf_variable}, 'variable_sources')
	save_single_json({'notcommonlyvariable_sources': sf_nonvariable}, 'notcommonly_variable_sources')
	save_single_json({'mixed_common_and_notcommon': sf_both}, 'mixed_common_and_notcommon_sources')
	save_single_json(sf_lines_variable, 'all_variable_sources_and_lines')
	save_single_json(sf_lines_nonvariable, 'all_notcommonlyvariable_sources_and_lines')


	# Store all the data in a dict to be returned
	data_dict = {
		'sf_variable': sf_variable,
		'sf_nonvariable': sf_nonvariable,
		'sf_both': sf_both,
		'sf_lines_nonvariable': sf_lines_nonvariable,
		'sf_lines_variable': sf_lines_variable
	}
	return data_dict


def get_diff(old_link, new_link, common_var_file):
	(old_lines, new_lines) = load_artifacts(old_link, new_link)
	tests_dict = check_testfiles(old_lines, new_lines)
	sfiles_dict = check_sourcefiles(old_lines, new_lines)
	differences = check_lines(old_lines, new_lines, sfiles_dict['new_sources'])
	differences1 = format_sfnames(differences)
	save_json(differences1, tests_dict, sfiles_dict)
	differences = filter_commons(differences1, common_var_file)
	diffs = split_var_and_nonvar(differences, differences1)
	save_single_json(diffs, 'test_diffs')
	return differences

if __name__ == '__main__':
	args = parser.parse_args()

	old_link = 'C:\\Users\\Gregory\\Documents\\mozwork\\grcov_data\\bc2_50times\\test_removal\\grcov_lcov_output_stdout0.info'
	new_link = 'C:\\Users\\Gregory\\Documents\\mozwork\\grcov_data\\bc2_50times\\test_removal\\grcov_lcov_output_stdout_m_oneTest.info'
	common_var_file = 'C:\\Users\\Gregory\\Documents\\mozwork\\grcov_data\\common_var_data.json'

	if args.variability_json is not None:
		# Set the values to what the user wants.
		print('Setting user specific files...')
		common_var_file = args.variability_json[0]
		old_link = args.path_to_old[0]
		new_link = args.path_to_new[0]

	diffs = get_diff(old_link, new_link, common_var_file)
