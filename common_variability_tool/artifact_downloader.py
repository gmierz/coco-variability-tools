import argparse
try:
	from urllib.parse import urlencode
	from urllib.request import urlopen, urlretrieve
except ImportError:
	from urllib import urlencode, urlretrieve
	from urllib2 import urlopen

# Use this program to dowwnload, extract, and distribute GRCOV
# files that are to be used for the variability analysis.

# FIGURE OUT A BETTER WAY TO DO THIS
# It requires a list of treeherder links. One for each grcov
# artifact that needs to be downloaded, extracted, and suffixed.

parser = argparse.ArgumentParser("This tool can download the GRCOV data from a list of " +
								 "treeherder links. It then extracts the data, suffixes it with " +
								 "a number and then stores it in an output directory.")
parser.add_argument('--treeherder-links', type=str, nargs='*',
					help='The treeherder links that have the grcov data. ex: ' +
					' https://queue.taskcluster.net/v1/task/NIENrMRzSieYYRUeReeb2Q/runs/0/artifacts/public/test_info//code-coverage-grcov.zip')
parser.add_argument('--output', type=str, nargs=1,
					help='This is the directory where all the download, extracted, and suffixed ' +
					'data will reside.')


# Marco's functions, very useful.
def get_json(url, params=None):
    if params is not None:
        url += '?' + urlencode(params)

    r = urlopen(url).read().decode('utf-8')

	return json.loads(r)


def get_task(branch, revision):
    task = get_json('https://index.taskcluster.net/v1/task/gecko.v2.%s.revision.%s.firefox.linux64-ccov-opt' % (branch, revision))
    return task['taskId']


def get_task_details(task_id):
    task_details = get_json('https://queue.taskcluster.net/v1/task/' + task_id)
    return task_details


def get_task_artifacts(task_id):
    artifacts = get_json('https://queue.taskcluster.net/v1/task/' + task_id + '/artifacts')
    return artifacts['artifacts']


def get_tasks_in_group(group_id):
    reply = get_json('https://queue.taskcluster.net/v1/task-group/' + group_id + '/list', {
        'limit': '200',
    })
    tasks = reply['tasks']
    while 'continuationToken' in reply:
        reply = get_json('https://queue.taskcluster.net/v1/task-group/' + group_id + '/list', {
            'limit': '200',
            'continuationToken': reply['continuationToken'],
        })
        tasks += reply['tasks']
    return tasks


def download_artifact(task_id, artifact):
    fname = os.path.join('ccov-artifacts', task_id + '_' + os.path.basename(artifact['name']))
    urlretrieve('https://queue.taskcluster.net/v1/task/' + task_id + '/artifacts/public/test_info//' + artifact['name'], fname)


def suite_name_from_task_name(name):
    name = name[len('test-linux64-ccov/opt-'):]
    parts = [p for p in name.split('-') if p != 'e10s' and not p.isdigit()]
return '-'.join(parts)

def download_artifact(link):
	urlretrieve('https://queue.taskcluster.net/v1/task/' + task_id + '/artifacts/' + artifact['name'], fname)

if __name__ == '__main__':
	