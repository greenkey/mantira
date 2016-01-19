import argparse, json
from jira import JIRA
from util import confman
from urllib.parse import urlparse
from util.mantis import Mantis

def getJiraMantisIssues(jira,mantis,cfg):
    issues_mj = jira.search_issues('"Mantis ID" is not EMPTY')

    for i in issues_mj:
        mantis_id = i.fields.customfield_10605
        if "http://192.168.132.59/mantis/view.php?" in mantis_id:
            mantis_id = mantis_id[mantis_id.find("?id=")+4:]
        print("Jira: {} → Mantis: {}".format(i.key, mantis_id))

def watchAssignedIssues(jira,mantis,cfg):
    issues = jira.search_issues('assignee = currentUser()')
    for i in issues:
        try:
            parent_issue = jira.issue(i.fields.parent.key)
            if not parent_issue.fields.watches.isWatching:
                print("Adding watch on {}".format( parent_issue.key ))
                jira.add_watcher(parent_issue,jira.current_user())
        except(AttributeError):
            print("Error, maybe issue {} doesn't have a parent.".format( i.key ))

def getJiraIncoherents(jira,mantis,cfg):
    from datetime import date, timedelta

    dt_str = cfg.get('Jira','last_check','Check never performed, insert a date from which filter the issues (YYYY-MM-DD): ')
    yesterday = date.today() - timedelta(1)
    cfg.put('Jira', 'last_check', yesterday.strftime("%Y-%m-%d"))

    print("Checking updates since {}".format(dt_str))

    issues = jira.search_issues('status changed AFTER "{}"'.format(dt_str))
    for i in issues:
        status = i.fields.status.name

        if status == 'Closed':
            for subissue in i.fields.subtasks:
                if subissue.fields.status.name != "Closed":
                    print("Issue {} is Closed but has at least a subtask not Closed ({})".format(
                        i.key, subissue.key))

        elif status in ('Testing','Developed'):
            for subissue in i.fields.subtasks:
                issuetype = subissue.fields.issuetype.name
                if issuetype in ('Dev Task'):
                    if subissue.fields.status.name != "Closed":
                        print("Issue {} is Testing but has at least a Dev Task not Closed ({})".format(
                            i.key, subissue.key))

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

def getJiraMantisIncoherents(jira,mantis,cfg):
    issues_mj = jira.search_issues('"Mantis ID" is not EMPTY')

    for ji in issues_mj:
        mantis_id = ji.fields.customfield_10605
        if "http://192.168.132.59/mantis/view.php?" in mantis_id:
            mantis_id = mantis_id[mantis_id.find("?id=")+4:]
        try:
            mi = mantis.mc_issue_get(issue_id=mantis_id)
        except:
            #print('Error getting issue "{}" on Mantis'.format(mantis_id))
            continue
        
        j_status = ji.fields.status.name
        m_status = mi.status.name

        if (j_status == 'Open' and m_status not in ('new', 'reopen')) or (j_status == 'In Progress' and m_status not in ('feedback', 'acknoweledged', 'confirmed', 'assigned')) or (j_status == 'Closed' and m_status not in ('resolved', 'closed', 'rejected')):
            print('Issue {} on Mantis is {} but the linked {} on Jira is {}'.format(
                mi.id, m_status, ji.key, j_status
                ))


def getAllIncoherents(jira,mantis,cfg):
    getJiraIncoherents(jira,mantis,cfg)
    getJiraMantisIncoherents(jira,mantis,cfg)

if __name__ == '__main__':

    # first get the parameters of the script
    parser = argparse.ArgumentParser(description='Get the Jira issues linked to Mantis.')
    parser.add_argument('action', metavar='ACTION', type=str,
                       help='the action to be performed')
    parser.add_argument('--config', dest='config_file',
                       action='store', default='.mantira_config.json',
                       help='Set the config file to use '
                            '(default: .mantira_config.json)')
    args = parser.parse_args()

    available_actions = {
        "get_jira_issues": getJiraMantisIssues,
        "watch_assigned_issues": watchAssignedIssues,
        "incoherents": getJiraIncoherents,
        "allincoherents": getAllIncoherents
    }
    if args.action not in available_actions:
        print("Action {} not available.\nList of available actions: {}".format(args.action,list(available_actions.keys())))
        exit()

    # get configuration
    cfg = confman.Confman(cfgFile=args.config_file, autoask=True, autosave=True)

    # connect to Jira
    jira = JIRA(
        cfg.get('Jira','host','Insert the url of jira (i.e. http://jira.yourdomain.com): '),
        basic_auth=(
            cfg.get('Jira','username','Insert the username for Jira: '),
            cfg.get('Jira','password','Insert the username for Jira (it will be'
                                         ' saved in the config file: '+cfg.cfgFile+'): ')))

    mantis = Mantis(
            cfg.get('Mantis','wsdl','Insert the wsdl of Mantis WS: '),
            cfg.get('Mantis','username','Insert username for Mantis: '),
            cfg.get('Mantis','password','Insert password for Mantis: (it will be'
                                         ' saved in the config file: '+cfg.cfgFile+'): '))

    available_actions[args.action](jira=jira,mantis=mantis,cfg=cfg)


