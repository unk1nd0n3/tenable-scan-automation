from pprint import pprint
import src.general as gen


def get_cf_website_dns(**kwargs):
    """

    :param kwargs:
    :return:
    """
    cf_client = kwargs['cf_client']
    cf_zones = cf_client.zones.get()
    hostnames = {}
    for zone in cf_zones:
        # params = {'name': zone['name'], 'per_page': 200}
        addresses = cf_client.zones.dns_records.get(zone['id'])
        hostnames[zone['name']] = {'id': zone['id'], 'name': zone['name']}
        hostnames[zone['name']]['targets'] = []
        for hostname in addresses:
            if hostname['type'] == 'A':
                new_hostname = hostname.copy()
                new_hostname['target'] = hostname['name']
                hostnames[zone['name']]['targets'].append(new_hostname)
        # print(addresses)
    gen.write_json_to_file('cf_addresses.json', 'json', hostnames, True)
    return hostnames


def create_firewall_access_rule(**kwargs):
    """
    Create whitelist in Cloudflare account for Tenable.io ip range
    :return:
    """
    cf_client = kwargs['cf_client']
    tenable_settings = kwargs['settings']['TENABLE.IO']
    tenable_ranges = tenable_settings['scanner_ranges'].split(',')
    zones = kwargs['zones']

    for zone in zones:
        zone_id = zones[zone]['id']
        try:
            for ip_range in tenable_ranges:
                params = {"mode": "whitelist",
                          "configuration": {"target": "ip_range", "value": ip_range},
                          "notes": "Security: whitelist vulnerability scanner"}
                cf_client.zones.firewall.access_rules.rules.post(zone_id, data=params)
        except Exception as error:
            pprint(error)
        # rules = cf_client.zones.firewall.access_rules.rules.get(zone_id)
        # print(rules)
    return True


