import os
import types
import requests

# disable warnings when using python less than 2.7.9
requests.packages.urllib3.disable_warnings()

# GITHUB_TOKEN for a user that has the access needed to run this script.
# ideally someone with owners rights.
TOKEN = os.environ.get('GITHUB_TOKEN')
if not TOKEN:
    raise Exception("GITHUB_TOKEN env variable is missing, please add it.")

# the list of bots that we currently have in the docker org.
BOTS = ['docker-codecov-bot',
        'docker-jenkins',
        'dockerjiraadmin',
        'GordonTheTurtle',
        'highland-tooling',
        'orca-eng',
        'dci-bot',
        'docker-autobuild',
        'docker-ci-scanner',
        'docker-metrics',
        'docker-tools-bot',
        'docker-tools-robot',
        'dtr-buildkite',
        'sf-release-bot',
        'psftwbot']


def request_get(url):
    """ nice wrapper around python requests that includes the token."""
    headers = {'Authorization': 'token {}'.format(TOKEN),
               'Content-Type': 'application/json'}
    r = requests.get(url, headers=headers)
    if r.status_code == requests.codes.not_found:
        raise Exception(u"{} not found".format(url))
    r.raise_for_status()
    return r.json()


def to_string(val):
    if val is None:
        return ''
    if isinstance(val, types.BooleanType):
        if val:
            return "X"
        return ""
    return str(val)
