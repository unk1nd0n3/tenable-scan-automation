# Tenable general functions and queries
import src.general as gen


def prepare_other_targets(settings):
    """
    Get Tenable.io assets
    :param settings: dictionary
    :return: string or boolean
    """
    other_targets = {"others": {}}
    for target in settings.keys():
        if target.startswith('target_'):
            targets = []
            target_name = target.split('_')[1]
            addresses = settings[target].split(',')
            for address in addresses:
                target_new = {'name': target_name,
                              'id': target_name + '-' + address,
                              'source': "config",
                              'target': address}
                targets.append(target_new)
            other_targets["others"] = {"name": target_name, "targets": targets}
    gen.write_json_to_file('other_addresses.json', 'json', other_targets, True)
    return other_targets

