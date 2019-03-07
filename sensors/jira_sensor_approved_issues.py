# See ./requirements.txt for requirements.
import os

from jira.client import JIRA

from st2reactor.sensor.base import PollingSensor


class JIRASensorApprovedIssues(PollingSensor):
    '''
    Sensor will monitor for any new projects created in JIRA and
    emit trigger instance when one is created.
    '''

    def __init__(self, sensor_service, config=None, poll_interval=5):
        super(JIRASensorApprovedIssues, self).__init__(sensor_service=sensor_service,
                                                       config=config,
                                                       poll_interval=poll_interval)

        self._jira_url = None
        # The Consumer Key created while setting up the "Incoming Authentication" in
        # JIRA for the Application Link.
        self._consumer_key = u''
        self._rsa_key = None
        self._jira_client = None
        self._access_token = u''
        self._access_secret = u''
        self._projects_available = None
        self._poll_interval = 30
        self._project = None
        self._issues_in_project = None
        self._jql_query = None
        self._trigger_name = 'jira_sensor_new_approved_issues'
        self._trigger_pack = 'jira'
        self._trigger_ref = '.'.join([self._trigger_pack, self._trigger_name])

    def _read_cert(self, file_path):
        with open(file_path) as f:
            return f.read()

    def setup(self):
        self._jira_url = self._config['url']
        auth_method = self._config['auth_method']

        if auth_method == 'oauth':
            rsa_cert_file = self._config['rsa_cert_file']
            if not os.path.exists(rsa_cert_file):
                raise Exception(
                    'Cert file for JIRA OAuth not found at %s.' % rsa_cert_file)
            self._rsa_key = self._read_cert(rsa_cert_file)
            self._poll_interval = self._config.get(
                'poll_interval', self._poll_interval)
            oauth_creds = {
                'access_token': self._config['oauth_token'],
                'access_token_secret': self._config['oauth_secret'],
                'consumer_key': self._config['consumer_key'],
                'key_cert': self._rsa_key
            }

            self._jira_client = JIRA(options={'server': self._jira_url},
                                     oauth=oauth_creds)
        elif auth_method == 'basic':
            basic_creds = (self._config['username'], self._config['password'])
            self._jira_client = JIRA(options={'server': self._jira_url},
                                     basic_auth=basic_creds)

        else:
            msg = ('You must set auth_method to either "oauth"',
                   'or "basic" your jira.yaml config file.')
            raise Exception(msg)

        if self._projects_available is None:
            self._projects_available = set()
            for proj in self._jira_client.projects():
                self._projects_available.add(proj.key)
        self._project = self._config.get('project', None)
        if not self._project or self._project not in self._projects_available:
            raise Exception('Invalid project (%s) to track.' % self._project)

        self._jql_query = self._config.get('jql', None)
        if self._jql_query is None:
            self._jql_query = 'project=%s' % self._project

        all_issues = self._jira_client.search_issues(
            self._jql_query, maxResults=None)
        self._issues_in_project = {issue.key: issue for issue in all_issues}

    def poll(self):
        self._detect_new_issues()

    def cleanup(self):
        pass

    def add_trigger(self, trigger):
        pass

    def update_trigger(self, trigger):
        pass

    def remove_trigger(self, trigger):
        pass

    def _detect_new_issues(self):
        new_issues = self._jira_client.search_issues(
            self._jql_query, maxResults=50, startAt=0)

        for issue in new_issues:
            if issue.key not in self._issues_in_project:
                self._dispatch_issues_trigger(issue)
                self._issues_in_project[issue.key] = issue

    def _dispatch_issues_trigger(self, issue):
        trigger = self._trigger_ref
        payload = {}
        payload['project'] = self._project
        payload['id'] = issue.id
        payload['expand'] = issue.raw.get('expand', '')
        payload['issue_key'] = issue.key
        payload['issue_url'] = issue.self
        payload['issue_browse_url'] = self._jira_url + '/browse/' + issue.key
        payload['fields'] = issue.raw.get('fields', {})
        self._sensor_service.dispatch(trigger, payload)
