from pprint import pprint
import src.general as gen
import googleapiclient


def get_project_regions(compute, project):
    """

    :param compute:
    :param project:
    :return:
    """
    request = compute.regions().list(project=project)
    regions = []
    while request is not None:
        response = request.execute()

        for region in response['items']:
            regions.append(region['name'])
        request = compute.regions().list_next(previous_request=request, previous_response=response)
    return regions


def get_project_addresses(compute, project, region):
    """

    :param compute:
    :param project:
    :param region:
    :return:
    """
    custom_filter = "addressType != INTERNAL"
    request = compute.addresses().list(project=project, region=region, filter=custom_filter)
    addresses = []
    while request is not None:
        response = request.execute()
        if 'items' in response.keys():
            for address in response['items']:
                addresses.append(address)
        request = compute.addresses().list_next(previous_request=request, previous_response=response)
    return addresses


def get_project_aggr_addresses(compute, project):
    """
    Get GCP VPC External IP addresses
    :param compute: object
    :param project: string
    :return: dictionary
    """
    request = compute.addresses().aggregatedList(project=project)
    addresses = []
    while request is not None:
        response = request.execute()
        for region in response['items']:
            if 'targets' in response['items'][region].keys():
                for address in response['items'][region]['targets']:
                    address_to_add = {'name': address['name'],
                                      'id': address['id'],
                                      'target': address['address'],
                                      'source': 'targets'}
                    if 'addressType' in address.keys():
                        if address['addressType'] == 'EXTERNAL':
                            addresses.append(address_to_add)
                        elif address['addressType'] == 'INTERNAL':
                            pass
                    elif address['status'] in ('IN_USE', 'RESERVED'):
                        addresses.append(address_to_add)

        request = compute.addresses().aggregatedList_next(previous_request=request,
                                                          previous_response=response)
    return addresses


def get_instance_aggr_public_ip(compute, project):
    """

    :param compute: object1
    :param project: string
    :return: dictionary
    """
    request = compute.instances().aggregatedList(project=project)
    instances = []
    while request is not None:
        response = request.execute()
        for region in response['items'].keys():
            if 'instances' in response['items'][region].keys():
                for instance in response['items'][region]['instances']:
                    address = {'name': instance['name'],
                               'id': instance['id'],
                               'source': 'instance'}
                    for interface in instance['networkInterfaces']:
                        if 'accessConfigs' in interface.keys():
                            for access in interface['accessConfigs']:
                                if 'natIP' in access.keys():
                                    address['target'] = access['natIP']
                                    instances.append(address)
        request = compute.instances().aggregatedList_next(previous_request=request,
                                                          previous_response=response)
    return instances


def get_sql_instance_public_ip(compute, project):
    """
    Get GCP Cloud SQL public IP addresses
    :param compute:
    :param project:
    :return: dictionary
    """
    request = compute.instances().list(project=project)
    instances = []
    while request is not None:
        response = request.execute()
        if 'items' in response.keys():
            for instance in response['items']:
                address = {'name': instance['name'],
                           'id': instance['connectionName'],
                           'source': 'sql',
                           'region': instance['region']}

                for ip_address in instance['ipAddresses']:
                    if 'ipAddress' in ip_address.keys():
                        address['target'] = ip_address['ipAddress']
                        instances.append(address)
        request = compute.instances().list_next(previous_request=request,
                                                previous_response=response)
    return instances


def get_organization_public_ip(compute, sql, projects_list):
    """
    Retrieve all GCP organization public IP address
    :param compute: gcp compute object
    :param sql: gcp sql cloud object
    :param projects_list: list
    :return: dictionary
    """
    project_ip_addresses = {}

    for project in projects_list:
        # noinspection PyUnresolvedReferences
        try:
            # print("{0},{1},{2}".format(project.name, project.project_id, project.status))
            total_project_addresses = []

            # Get list of reserved external IP addresses
            project_aggr_addresses = get_project_aggr_addresses(compute, project.project_id)

            # Get list of external ephemeral Compute instances addresses
            instance_aggr_addresses = get_instance_aggr_public_ip(compute, project.project_id)

            # Get list of external ephemeral SQL instances addresses
            sql_instance_aggr_addresses = get_sql_instance_public_ip(sql, project.project_id)

            # Aggregate results
            total_project_addresses.extend(project_aggr_addresses)
            total_project_addresses.extend(instance_aggr_addresses)
            total_project_addresses.extend(sql_instance_aggr_addresses)
            total_project_addresses = list({tgt['target']: tgt for tgt in total_project_addresses}.values())
            # Assign all external IP addresses to Project ID
            if total_project_addresses:
                project_ip_addresses[project.project_id] = {'name': project.name}
                project_ip_addresses[project.project_id]['targets'] = total_project_addresses

        except googleapiclient.errors.HttpError as error:
            pprint(error)

    gen.write_json_to_file('gcp_addresses.json', 'json', project_ip_addresses, True)

    return project_ip_addresses


