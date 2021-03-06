# coding=UTF-8

import argparse, json
from jira import JIRA
from util import confman
from urllib.parse import urlparse
from util.mantis import Mantis


def get_jira_mantis_issues(jira, mantis, cfg):
    dt_str = cfg.get('Mantira', 'last_check')
    issues_mj = jira.search_issues('"Mantis ID" is not EMPTY AND updatedDate > "{}"'.format(dt_str), maxResults=None)

    for i in issues_mj:
        mantis_id = i.fields.customfield_10605
        if "http://192.168.132.59/mantis/view.php?" in mantis_id:
            mantis_id = mantis_id[mantis_id.find("?id=") + 4:]
        print("Jira: {} → Mantis: {}".format(i.key, mantis_id))


def watch_assigned_issues(jira, mantis, cfg):
    dt_str = cfg.get('Mantira', 'last_check')

    issues = jira.search_issues('assignee = currentUser() AND updatedDate > "{}"'.format(dt_str), maxResults=None)
    for i in issues:
        try:
            parent_issue = jira.issue(i.fields.parent.key)
            if not parent_issue.fields.watches.isWatching:
                print("Adding watch on {}".format(parent_issue.key))
                jira.add_watcher(parent_issue, jira.current_user())
        except(AttributeError):
            print("Error, maybe issue {} doesn't have a parent.".format(i.key))


def get_jira_incoherents(jira, mantis, cfg):
    dt_str = cfg.get('Mantira', 'last_check')

    print("Checking updates since {}".format(dt_str))

    issues = jira.search_issues('updatedDate > "{}"'.format(dt_str), maxResults=None)
    for i in issues:
        status = i.fields.status.name

        if status == 'Closed':
            for subissue in i.fields.subtasks:
                if subissue.fields.status.name != "Closed":
                    print("Issue {} is Closed but has at least a subtask not Closed ({})".format(
                        i.key, subissue.key))

        elif status in ('Testing', 'Developed'):
            for subissue in i.fields.subtasks:
                issuetype = subissue.fields.issuetype.name
                if issuetype in ('Dev Task'):
                    if subissue.fields.status.name != "Closed":
                        print("Issue {} is {} but has at least a Dev Task not Closed ({})".format(
                            i.key, status, subissue.key))

        elif status == 'In Progress':
            devstatuses = set()
            for subissue in i.fields.subtasks:
                issuetype = subissue.fields.issuetype.name
                if issuetype in ('Dev Task'):
                    devstatuses.add(subissue.fields.status.name)
            if len(devstatuses) == 1 and 'In Progress' not in devstatuses:
                print("Issue {} is In Progress but has all the Dev Task {}".format(
                    i.key, devstatuses))

        elif status == 'Open':
            for subissue in i.fields.subtasks:
                if subissue.fields.status.name != "Open":
                    print("Issue {} is Open but has at least a subtask not Open ({})".format(
                        i.key, subissue.key))

        else:
            pass


def get_jira_mantis_incoherents(jira, mantis, cfg):
    dt_str = cfg.get('Mantira', 'last_check')
    issues_mj = jira.search_issues('"Mantis ID" is not EMPTY AND updatedDate > "{}"'.format(dt_str), maxResults=None)

    for ji in issues_mj:
        mantis_id = ji.fields.customfield_10605
        if "http://192.168.132.59/mantis/view.php?" in mantis_id:
            mantis_id = mantis_id[mantis_id.find("?id=") + 4:]
        try:
            mi = mantis.mc_issue_get(issue_id=mantis_id)
        except:
            # print('Error getting issue "{}" on Mantis'.format(mantis_id))
            continue

        j_status = ji.fields.status.name
        m_status = mi.status.name

        if (j_status == 'Open' and m_status not in ('new', 'reopen')) or (
                j_status == 'In Progress' and m_status not in (
        'feedback', 'acknoweledged', 'confirmed', 'assigned')) or (
                j_status == 'Closed' and m_status not in ('resolved', 'closed', 'rejected')):
            print('Issue {} on Mantis is {} but the linked {} on Jira is {}'.format(
                mi.id, m_status, ji.key, j_status
            ))


def get_all_incoherents(jira, mantis, cfg):
    get_jira_incoherents(jira, mantis, cfg)
    get_jira_mantis_incoherents(jira, mantis, cfg)


if __name__ == '__main__':

    # first get the parameters of the script
    parser = argparse.ArgumentParser(description='Get the Jira issues linked to Mantis.')
    parser.add_argument('action', metavar='ACTION', type=str,
                        help='the action to be performed')
    parser.add_argument('--config', dest='config_file',
                        action='store', default='.mantira_config.json',
                        help='Set the config file to use '
                             '(default: .mantira_config.json)')
    parser.add_argument('--from_date', dest='from_date',
                        action='store', default='last_check',
                        help='From which date the analysis should take place, ISO format '
                             '(default = last check)')
    args = parser.parse_args()

    available_actions = {
        "get_jira_issues": get_jira_mantis_issues,
        "watch_assigned_issues": watch_assigned_issues,
        "incoherents": get_jira_incoherents,
        "allincoherents": get_all_incoherents
    }
    if args.action not in available_actions:
        print("Action {} not available.\nList of available actions: {}".format(args.action,
                                                                               list(available_actions.keys())))
        exit()

    # get configuration
    cfg = confman.Confman(cfgFile=args.config_file, autoask=True, autosave=True)

    # connect to Jira
    jira = JIRA(
        cfg.get('Jira', 'host', 'Insert the url of jira (i.e. http://jira.yourdomain.com): '),
        basic_auth=(
            cfg.get('Jira', 'username', 'Insert the username for Jira: '),
            cfg.get('Jira', 'password', 'Insert the username for Jira (it will be'
                                        ' saved in the config file: ' + cfg.cfgFile + '): ')))

    mantis = Mantis(
        cfg.get('Mantis', 'wsdl', 'Insert the wsdl of Mantis WS: '),
        cfg.get('Mantis', 'username', 'Insert username for Mantis: '),
        cfg.get('Mantis', 'password', 'Insert password for Mantis: (it will be'
                                      ' saved in the config file: ' + cfg.cfgFile + '): '))

    if (args.from_date == 'last_check'):
        dt_str = cfg.get('Mantira', 'last_check',
                         'Check never performed, insert a date from which filter the issues (YYYY-MM-DD): ')
    else:
        dt_str = args.from_date
    cfg.put('Mantira', 'last_check', dt_str)

    available_actions[args.action](jira=jira, mantis=mantis, cfg=cfg)

    from datetime import date, timedelta

    yesterday = date.today() - timedelta(1)
    cfg.put('Mantira', 'last_check', yesterday.strftime("%Y-%m-%d"))
