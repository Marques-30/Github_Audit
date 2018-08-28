#!/usr/bin/env python

import click
import csv
from utils import request_get, BOTS, to_string
from terminaltables import AsciiTable

def get_user(login):
    """ Get user details, given their login """
    url = "https://api.github.com/users/{}".format(login)
    return request_get(url)


def get_teams():
    """ Get all of the teams listed under the docker org """
    url = "https://api.github.com/orgs/docker/teams"
    return request_get(url)


def get_org_owners():
    """ Get the users who are listed as owners for the Docker org """
    url = "https://api.github.com/orgs/docker/members?role=admin"
    results = request_get(url)
    owners = []
    for result in results:
        owners.append(result.get('login'))
    return owners


def get_members():
    count =1
    """Creates a CSV file and writes the list of users into it"""
    with open('Github.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(["Github Handle", "User name", "Email"])
        while count <= 500:
            try:
                """ Get the users who are listed as owners for the Docker org """
                url = "https://api.github.com/orgs/docker/members?role=all&page={}&per_page=1".format(count)
                result = request_get(url)
                grouping = []
                for res in result:
                    login = res.get('login')
                    if login not in BOTS:
                        user = get_user(login)
                        user_detail = {'login': login, 'name': user.get(u'name'), 'email': user.get('email')}
                        grouping.append(user_detail)
        
                for member in grouping:
                    print(" - {}, {}, {}".format(member.get('login'), member.get(u'name'), member.get('email')))
                    writer.writerow([member.get('login'), member.get(u'name'), member.get('email')])
            except UnicodeEncodeError:
                username = member.get(u'name').encode('utf_32')
                s = username.decode('utf_32')
                print(" - {}, " + s + ", {}").format(member.get(u'login'), member.get('email'))
                writer.writerow([member.get('login'), member.get(u'name').decode('utf_32'), member.get('email')])
            count += 1


def get_team_maintainers(team_id):
    """ Given a team_id, get the list of maintainers """
    url = "https://api.github.com/teams/{}/members?filter=maintainer".format(team_id)
    return request_get(url)


def get_org_repos(per_page=100, page=1):
    """ Get the repos for the docker org """
    url = "https://api.github.com/orgs/docker/repos?per_page={}&page={}".format(per_page, page)
    return request_get(url)


def get_repo_collabs(repo):
    """ Get collaborators for a repo"""
    url = "https://api.github.com/repos/docker/{}/collaborators?per_page=100".format(repo)
    return request_get(url)


def twofactorauth_check():
    """
    Make sure all user accounts have 2 factor auth enabled.
    """
    url = "https://api.github.com/orgs/docker/members?filter=2fa_disabled&per_page=200"
    result = request_get(url)
    naughty_list = []
    for res in result:
        login = res.get('login')
        if login not in BOTS:
            user = get_user(login)
            user_detail = {'login': login, 'name': user.get('name')}
            naughty_list.append(user_detail)

    print("The following people don't have 2FA turned on!")
    for baddy in naughty_list:
        print(" - {} -> {}".format(baddy.get('login'), baddy.get('name')))
    print("\n")


def team_maintainers_check():
    """ Make sure all teams have a maintainer """
    is_bad = False
    teams = get_teams()
    for team in teams:
        maintainers = get_team_maintainers(team.get('id'))
        main_list = []
        for main in maintainers:
            main_list.append(main.get('login'))
        if len(main_list) == 0:
            is_bad = True
            print("{} Doesn't have any team maintainers".format(team.get('name')))
    if not is_bad:
        print("All Teams have maintainers!\n")
    else:
        print("Fix the teams above, by adding a maintainer to them!\n")


def repo_check():
    """ Check which repos don't have an admin, and list them here. """
    owners = get_org_owners()
    # this should give us 400 repos, should be enough for a while.
    repos = get_org_repos()
    repos += get_org_repos(page=2)
    repos += get_org_repos(page=3)
    repos += get_org_repos(page=4)
    errors = []
    for repo in repos:
        has_admin = False
        try:
            # print repo.get('name')
            collabs = get_repo_collabs(repo.get('name'))
            # print collabs
            for collab in collabs:
                if collab.get('login') in owners:
                    # skip over the owners, they don't count for this.
                    # might create a false positive, if the only admins happen
                    # to be one of the owners.
                    continue
                if collab.get('permissions', {}).get('admin', False):
                    has_admin = True
                    break
            if not has_admin:
                errors.append(repo.get('name'))
        except Exception as exc:
            print(exc)
            errors.append(repo.get('name'))

    if not errors:
        print("No Repo errors, all repos look good.")
    else:
        print("The following repos don't have an admin, add one to fix.")
        print("  \n".join(errors))


@click.group()
@click.pass_context
def cli(ctx):
    pass


@cli.command()
def twofactorauth():
    """View members who do not have 2FA activated"""
    print("========= 2FA check ======= \n")
    # make sure everyone has 2 factor auth enabled
    twofactorauth_check()


@cli.command()
def audit():
    """View members without 2FA, team maintanier and repos without Admins"""
    print("========= Github Audit ======= \n")
    # make sure everyone has 2 factor auth enabled
    twofactorauth_check()
    # make sure all teams have a maintainer
    team_maintainers_check()
    # check all repos, make sure they have an admin
    repo_check()
    print("============================== \n")


@cli.command()
def owners():
    """View Owners of Docker Org"""
    owners = get_org_owners()
    print("Docker Github Owners\n----------------")
    for owner in owners:
        print(" - {}".format(owner))

@cli.command()
def members():
    """View all members Docker Github"""
    print("Docker Github members\n----------------------\n")
    #list of all memebers within docker Github
    get_members()


@cli.command()
@click.option('--reponame', prompt='reponame',
              help='Name of the repo to lookup')
def repo_collaborators(reponame):
    """View list of members and access level within certain repos"""
    try:
        table_data = [
            ['User', 'Admin', 'Push', "Pull"],
        ]
        collabs = get_repo_collabs(reponame)
        for collab in collabs:
            admin = collab.get('permissions', {}).get('admin', False)
            push = collab.get('permissions', {}).get('push', False)
            pull = collab.get('permissions', {}).get('pull', False)
            table_data.append([collab.get('login'),
                               to_string(admin),
                               to_string(push),
                               to_string(pull)])

        table = AsciiTable(table_data, reponame)
        print(table.table)
        print("\n")
    except Exception: #(u"{} not found".format(url))
        print("Repo does not exist with Docker Github")


if __name__ == '__main__':
    cli()
