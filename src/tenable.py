# Tenable general functions and queries
from datetime import timedelta
from tenable_io.api.models import ScanSettings
from tenable_io.api.scans import ScanCreateRequest


def get_tenable_folder_id(**kwargs):
    """
    Get Tenable.io scanning folder id
    :param kwargs:
    :return: string or boolean
    """
    client = kwargs['client']
    folders = client.folders_api.list().folders
    for folder in folders:
        if folder.name == kwargs['folder_name']:
            return folder.id
    else:
        return False


def get_tenable_policy_uuid(**kwargs):
    """
    Get Tenable.io scanning policy id
    :param kwargs:
    :return: string or boolean
    """
    client = kwargs['client']
    policies = client.policies_api.list().policies
    for policy in policies:
        if policy.name == kwargs['policy_name']:
            return policy
    else:
        return False


def get_composed_scan_jobs(**kwargs):
    """
    Compose targets for each scan job due to license limits
    :param kwargs: (see call function details)
    :return: dictionary, datetime object
    """
    license_count = int(kwargs['license_count'])
    projects = kwargs['projects']
    settings = kwargs['scan_settings']
    # Set scheduled scan time
    scan_time = kwargs['scan_time']
    # Schedule scan start time
    time_delta = int(settings['time_delta'])
    projects_before_split = list(projects.keys())

    # Find all projects with targets count greater than license count
    for project in projects_before_split:
        # targets_list = [address['target'] for address in projects[project]['addresses']]
        targets_list_len = len(projects[project]['targets'])
        if targets_list_len > license_count:
            chunk = 1
            for idx in range(0, targets_list_len, license_count):
                new_project = "{0}-part{1}".format(project, str(chunk))
                projects[new_project] = projects[project].copy()
                projects[new_project]['name'] = new_project
                projects[new_project]['targets'] = projects[project]['targets'][idx:idx + license_count]
                chunk += 1
            projects.pop(project)

    projects_sorted = sorted(projects.items(), key=lambda x: len(x[1]['targets']))
    project_names_to_check = [project[0] for project in projects_sorted]
    project_names_left = list(projects.keys())

    while project_names_left:
        count = license_count
        scan_start_time_str = scan_time.strftime('%Y%m%dT%H%M%S')
        for project in project_names_to_check:
            targets_list = [address['target'] for address in projects[project]['targets']]
            targets_list_len = len(targets_list)
            if project in project_names_left:
                if targets_list_len <= count:
                    projects[project]['starttime'] = scan_start_time_str
                    project_names_left.remove(project)
                    count -= targets_list_len

        scan_time += timedelta(hours=time_delta)
        project_names_to_check = project_names_left
    return projects, scan_time


def create_tenable_scan(**kwargs):
    """
    Schedule scan job in Tenable.io account
    :param kwargs: list of arguments (see call function details)
    :return: datetime object
    """
    # Assign arguments
    settings = kwargs['settings'][kwargs['scan_target']]
    client = kwargs['client']
    logger = kwargs['logger']
    scan_time = kwargs['scan_time']
    # Scan name time part
    settings['policy'] = get_tenable_policy_uuid(client=client,
                                                 policy_name=settings['policy_name'])
    settings['folder_id'] = get_tenable_folder_id(client=client,
                                                  folder_name=settings['folder_name'])
    # Set correct ACLs
    acls = [{'display_name': settings['acl_name'],
             'name': settings['acl_name'],
             'id': settings['acl_id'],
             'permissions': settings['acl_permissions'],
             'type': 'group'}]

    targets, scan_time = get_composed_scan_jobs(projects=kwargs['target'],
                                                license_count=kwargs['settings']['TENABLE.IO']['license_count'],
                                                scan_settings=settings,
                                                scan_time=scan_time)

    # Create and launch scans in Tenable
    for target in targets:
        project = targets[target]

        # Set scan name
        scan_name = "{0}-{1}-{2}".format(targets[target]['starttime'],
                                         settings['name'],
                                         project['name'])
        # Set scan targets
        targets_list = [address['target'] for address in project['targets']]
        targets_str = ",".join(targets_list)
        settings['text_targets'] = targets_str
        # Create scan object
        scan_settings = ScanSettings(name=scan_name,
                                     emails=settings['emails'] if 'emails' in settings.keys() else False,
                                     enabled=settings['enabled'],
                                     starttime=targets[target]['starttime'],
                                     rrules=settings['rrules'],
                                     timezone=settings['timezone'],
                                     folder_id=settings['folder_id'],
                                     policy_id=settings['policy'].id,
                                     scanner_id=settings['scanner_id'],
                                     text_targets=targets_str,
                                     acls=acls)

        scan_request = ScanCreateRequest(uuid=settings['policy'].template_uuid,
                                         settings=scan_settings)

        client.scans_api.create(scan_request)
        logger.info("Successfully created scan {0}".format(scan_name))
    return scan_time
