import argparse, json
from jira import JIRA
from util import confman
from urllib.parse import urlparse

def getJiraMantisIssues(jira,cfg):
    issues_mj = jira.search_issues('"Mantis ID" is not EMPTY')

    for i in issues_mj:
        mantis_id = i.fields.customfield_10605
        if "http://192.168.132.59/mantis/view.php?" in mantis_id:
            mantis_id = mantis_id[mantis_id.find("?id=")+4:]
        print("Jira: {} → Mantis: {}".format(i.key, mantis_id))


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
        "get_jira_issues": getJiraMantisIssues
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

    available_actions[args.action](jira,args)


