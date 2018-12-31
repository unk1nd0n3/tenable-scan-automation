# Tenable general functions and queries
import re
import src.general as gen


def get_tenables_assets(**kwargs):
    """
    Get Tenable.io assets
    :param kwargs:
    :return: string or boolean
    """
    client = kwargs['client']
    assets = client.assets_api.list()
    targets = []
    re_ip_obj = re.compile("^(?!10\.|192\.168\.).*$")
    for asset in assets.assets:
        if asset.aws_ec2_name:
            match_ip_addr = list(filter(re_ip_obj.match, asset.ipv4))
            target = {'name': asset.aws_ec2_name[0],
                      'id': asset.id,
                      'source': "AWS",
                      'target': match_ip_addr[0]}
            targets.append(target)
    aws_targets = {"aws": {"name": "dev-prod", "targets": targets}}
    gen.write_json_to_file('aws_addresses.json', 'json', aws_targets, True)
    return aws_targets
