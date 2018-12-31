# Tenable general functions and queries
import src.general as gen


def get_linode_targets(**kwargs):
    """
    Get Tenable.io assets
    :param kwargs:
    :return: string or boolean
    """
    client = kwargs['client']
    my_linodes = client.linode.instances()
    targets = {'linode-parser': {'name': 'linode-parser', 'targets': []},
               'linode-dmarket': {'name': 'linode-dmarket', 'targets': []}}

    for linode in my_linodes:
        target = {}
        target['name'] = linode.label
        target['target'] = linode.ipv4[0]
        if linode.label.endswith('_dm'):
            targets['linode-dmarket']['targets'].append(target)
        else:
            targets['linode-parser']['targets'].append(target)

    gen.write_json_to_file('linode_addresses.json', 'json', targets, True)
    return targets
