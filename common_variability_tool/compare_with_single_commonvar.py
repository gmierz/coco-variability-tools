from diff_two import *
from artifact_downloader import download_artifact, unzip_grcov, get_task_artifacts
from common_var_html_creator import get_html
import argparse
import os
import json
import shutil
import time

def compare_with_single_parser():
	parser = argparse.ArgumentParser(description='Get difference between failure run and good runs.')
	parser.add_argument('--variability-json', '-vj', type=str, nargs=1,
						help='The path to the json that contains the variability data for this test suite' +
						' and chunk.')
	parser.add_argument('--output', type=str, nargs=1,
						help='Where the output should be stored. By default, it is set to the current' +
						' working directory.')
	parser.add_argument('--task-group-id', type=str, nargs=1,
						help='The group of tasks that should be parsed to find and download all the necessary ' +
						'data to be used in this analysis. ')
	parser.add_argument('--failed-task-id', type=str, nargs=1,
						help='The task that is a failure.')
	parser.add_argument('--get-html', action='store_true',
						help='The task that is a failure.')
	parser.add_argument('--revision', type=str, nargs=1,
						help='The revision (changeset) which this analysis is based/run on.')
	return parser


def compare_failure_to_commons(failure_file, common_vars_name):
	print('Comparing')
	print(common_vars_name)
	with open(common_vars_name) as jsonf:
		common_vars = json.load(jsonf)
	if 'differences' in common_vars:
		differences = common_vars['differences']
	else:
		differences = common_vars
	failure_json = get_file_json(failure_file)
	intermittent_lines = {}
	for sf in failure_json:
		if sf in differences:
			if 'differences_lines' in differences[sf]:
				var_lines = differences[sf]['differences_lines']
			else:
				var_lines = differences[sf]
			fail_lines = failure_json[sf]
			lines = []
			for line_num in fail_lines:
				if line_num not in var_lines:
					lines.append(line_num)
			if len(lines) != 0:
				intermittent_lines[sf] = lines
		else:
			intermittent_lines[sf] = failure_json[sf]

	return intermittent_lines


def main():
	print('Comparing failure to variabilitly.')

	parser = compare_with_single_parser()
	args = parser.parse_args()

	output = os.getcwd()
	if args.output is not None:
		output = args.output[0]

	tmp_dir = os.path.join(output, 'tmp_data')
	if os.path.exists(tmp_dir):
		shutil.rmtree(tmp_dir)
	os.mkdir(tmp_dir)

	artifacts = get_task_artifacts(args.failed_task_id[0])
	for artifact in artifacts:
		if 'grcov' in artifact['name']:
			filen = download_artifact(args.failed_task_id[0], artifact, tmp_dir)
			print(filen)
			unzip_grcov(filen, tmp_dir, count=0)

	name = 'grcov_lcov_output_stdout0.info'
	diffs = compare_failure_to_commons(os.path.join(tmp_dir, name), args.variability_json[0])
	save_single_json(diffs, 'intermittent_uniques', output_dir=output)
	if args.get_html:
		html_file = get_html(diffs, rev=args.revision[0])

		output_file = os.path.join(output, args.failed_task_id[0] + '_intermittent_uniques_' + str(int(time.time())) + '.html')
		with open(output_file, 'w+') as html_out:
			html_out.write(html_file)


if __name__ == "__main__":
	main()