from artifact_downloader import artifact_downloader
from common_var_retriever import get_common_var_file
from common_var_html_creator import get_html

import argparse
import os


def common_var_creator_parser():
	parser = argparse.ArgumentParser("This program goes through the directories created by artifact_downloader " +
									 "and creates a common var file for each one.")
	parser.add_argument('--task-group-id', type=str, nargs=1,
						help='The group of tasks that should be parsed to find and download all the necessary ' +
						'data to be used in this analysis. ')
	parser.add_argument('--test-suites-list', type=str, nargs='+',
						help='The list of tests to look at. e.g. mochitest-browser-chrome-e10s-2.' +
						' If it`s empty we assume that it means nothing, if `all` is given all suites' +
						' will be processed.')
	parser.add_argument('--output-all', type=str, nargs=1,
						help='This is the directory where all the download, extracted, and suffixed ' +
						'data will reside. Furthermore, this is where the common vars will be.')
	parser.add_argument('--exclude', type=int, nargs='*',
						help='List of datasets that will be excluded. Starting from 0 to' +
						' number of grcov files found.')
	parser.add_argument('--html-out', action='store_true',
						help='Outputs an html view of the variability.')
	return parser


def common_var_creator(task_group_id, test_suites_list=[], output_dir=os.getcwd(), exclude=[], save_the_data=True, html_out=True):
	# Download artifacts
	task_dir, head_rev = artifact_downloader(task_group_id, output_dir=output_dir, test_suites=test_suites_list)
	#task_dir = """C:\\Users\\Gregory\\Documents\\mozwork\\devtools_analysis\\MLq5-3ejTSu7RyAi1zx6ug\\5"""
	# In the task dir, there will be one
	# directory per test suite chunk.
	dirnames = [dirname for dirname in os.listdir(task_dir) if os.path.isdir(os.path.join(task_dir, dirname))]

	# For each test suite chunk
	for test_suite_chunk_name in dirnames:
		path_to_chunk = os.path.join(task_dir, test_suite_chunk_name)

		# Within the 'grcov_data' directory, we can find all the grcov files
		# at the top level.
		grcov_data_dir = os.path.join(path_to_chunk, 'grcov_data')
		common_var_procd = get_common_var_file(grcov_data_dir, exclude, output_dir=grcov_data_dir, save_the_data=save_the_data)

		if html_out:
			hfile = get_html(common_var_procd, head_rev)

			output_file = os.path.join(output_dir, 'variability_index.html')
			with open(output_file, 'w+') as f:
				f.write(hfile)


def main():
	parser = common_var_creator_parser()
	args = parser.parse_args()

	task_group_id = None
	test_suites_list = []
	output_all = os.getcwd()

	if not args.task_group_id:
		raise Exception("A task group ID must be given.")
	else:
		task_group_id = args.task_group_id[0]

	if args.test_suites_list:
		test_suites_list = args.test_suites_list

	if args.output_all:
		output_all = args.output_all[0]

	print(task_group_id)
	common_var_creator(task_group_id, test_suites_list=test_suites_list, \
					   output_dir=output_all, save_the_data=True, \
					   html_out=args.html_out)


if __name__ == '__main__':
	main()
