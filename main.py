# -*- coding: utf-8 -*-
# __version__ = '0.1'
import argparse
import time
import os
import logging
import configparser
from datetime import datetime
import CloudFlare
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
import src.general as gen
import src.tenable as tnb
import src.gcp as gcp
import src.cf as cf
import src.aws as aws
import src.linode as lin
import src.others as others
from google.cloud import resource_manager
from linode_api4 import LinodeClient
from tenable_io.client import TenableIOClient


# General logging configuration
log_file_time = time.strftime("%Y-%m-%d-%H-%M", time.gmtime())
log_file_name = "logs/" + log_file_time + "-tenable-scan.log"
logfile = os.path.realpath(os.path.join(os.path.dirname(__file__), log_file_name))
print('All logs are stored in file - {0}'.format(logfile))

# create logger with 'spam_application'
logger = logging.getLogger('tenable-script')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler(logfile)
fh.setLevel(logging.DEBUG)

# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(fh)

logger.info('########################################  START ########################################')


def main():
    """

    Main func for automatic vulnerability scan by Tenable.io of Company GCP and Cloudflare resources
    :return: none
    """
    parser = argparse.ArgumentParser(description='Provide all arguments for successful Vulnerability scan')
    parser.add_argument("-all", dest="tg_all", action="store_true", help="Scan All supported infrastructures")
    parser.add_argument("-cloudflare", dest="tg_cloudflare", action="store_true", help="Scan GCP infrastructure")
    parser.add_argument("-gcp", dest="tg_gcp", action="store_true", help="Scan Cloudflare infrastructure")
    parser.add_argument("-aws", dest="tg_aws", action="store_true", help="Scan AWS infrastructures")
    parser.add_argument("-linode", dest="tg_linode", action="store_true", help="Scan Linode infrastructures")
    parser.add_argument("-others", dest="tg_others", action="store_true", help="Scan rest of SaaS: DO, Linode, etc")
    parser.add_argument("-schedule", dest="tg_schedule", action="store_true", help="Schedule scans by Tenable.io")
    parser.set_defaults(tg_all=False)
    parser.set_defaults(tg_cloudflare=False)
    parser.set_defaults(tg_gcp=False)
    parser.set_defaults(tg_aws=False)
    parser.set_defaults(tg_linode=False)
    parser.set_defaults(tg_others=False)
    parser.set_defaults(tg_schedule=False)
    args = parser.parse_args()
    # Create dirs
    gen.create_dirs()

    # Set configuration file location
    main_script_abs = os.path.dirname(os.path.abspath(__file__))
    settings_obj = configparser.ConfigParser()
    settings_obj.read(main_script_abs + '/conf/conf.cfg')

    # Initiate an instance of TenableIOClient.
    settings = settings_obj._sections.copy()
    tenable_client = TenableIOClient(access_key=settings['TENABLE.IO']['access_key'],
                                     secret_key=settings['TENABLE.IO']['secret_key'])
    logger.info('Successfully authenticated to Tenable.io')

    # Set scheduled scan time
    scan_time = datetime.now()

    # Set time delta if you need to launch scanning job right now
    if not args.tg_schedule:
        for section in settings.keys():
            if 'time_delta' in settings[section].keys():
                settings[section]['time_delta'] = 0

    # Launch scan jobs in Tenable.io against GCP resources
    if args.tg_gcp or args.tg_all:
        # Set GCP credentials environment
        logger.info('Parsing google credentials and set ENV variables')
        gcp_api_key_json = settings_obj.get('GCP', 'gcp-api-key-json')
        # Set Service account env variable and form path to json file
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = main_script_abs + gcp_api_key_json

        # Configure credentials for Google API authentication
        credentials = GoogleCredentials.get_application_default()
        compute = discovery.build('compute', 'v1', credentials=credentials)
        sql = discovery.build('sqladmin', 'v1beta4', credentials=credentials)
        logger.info('Successfully authenticated to GCP services')

        # Get list of all projects via GCP Resource manager
        resource_client = resource_manager.Client()
        projects_list = list(resource_client.list_projects())
        logger.info('Successfully extracted list GCP projects and public IP addresses')
        # Retrieve all GCP organization public IP address
        target_ip_addresses = gcp.get_organization_public_ip(compute, sql, projects_list)
        # # In case you need to read from local copy of saved projects
        # target_ip_addresses = gen.read_json_file('json/20181006T104414-gcp_addresses.json')
        logger.info('Trying to create scan jobs in Tenable.io for all GCP projects')

        # Launch scan against GCP resources
        scan_time = tnb.create_tenable_scan(scan_target='TENABLE_GCP_SCAN',
                                            client=tenable_client,
                                            target=target_ip_addresses,
                                            settings=settings,
                                            logger=logger,
                                            scan_time=scan_time)
        logger.info('Successfully created scan jobs in Tenable.io')

    if args.tg_cloudflare or args.tg_all:
        # Parse CF credentials environment
        logger.info('Parsing Cloudflare credentials')
        cf_email = settings_obj.get('CLOUDFLARE', 'cf_email')
        cf_api_key = settings_obj.get('CLOUDFLARE', 'cf_api_key')

        # Create Cloudflare connection object
        cf_client = CloudFlare.CloudFlare(email=cf_email, token=cf_api_key)
        # Create targets for scanning job
        target_hostnames = cf.get_cf_website_dns(cf_client=cf_client)

        # # Test purposes (comment please when test will be finished)
        # target_hostnames = gen.read_json_file('json/20181005T185623-cf_addresses.json')
        # scan_time += timedelta(hours=90)
        cf.create_firewall_access_rule(cf_client=cf_client, settings=settings, zones=target_hostnames)
        scan_time = tnb.create_tenable_scan(scan_target='TENABLE_CF_SCAN',
                                            client=tenable_client,
                                            target=target_hostnames,
                                            settings=settings,
                                            logger=logger,
                                            scan_time=scan_time)

    if args.tg_aws or args.tg_all:
        # Create Cloudflare connection object
        target_assets = aws.get_tenables_assets(client=tenable_client)
        scan_time = tnb.create_tenable_scan(scan_target='TENABLE_AWS_SCAN',
                                            client=tenable_client,
                                            target=target_assets,
                                            settings=settings,
                                            logger=logger,
                                            scan_time=scan_time)

    if args.tg_linode or args.tg_all:
        # Get Linode targets
        linode_client = LinodeClient(settings['LINODE']['lin_api_key'])
        linode_targets = lin.get_linode_targets(client=linode_client)
        scan_time = tnb.create_tenable_scan(scan_target='TENABLE_LINODE_SCAN',
                                            client=tenable_client,
                                            target=linode_targets,
                                            settings=settings,
                                            logger=logger,
                                            scan_time=scan_time)

    if args.tg_others or args.tg_all:
        # Launch scan of Other targets
        target_assets = others.prepare_other_targets(settings['TENABLE_OTHERS_SCAN'])
        scan_time = tnb.create_tenable_scan(scan_target='TENABLE_OTHERS_SCAN',
                                            client=tenable_client,
                                            target=target_assets,
                                            settings=settings,
                                            logger=logger,
                                            scan_time=scan_time)

    logger.info('Vulnerability scan will be finished at {0}'.format(scan_time.strftime('%Y%m%dT%H%M%S')))
    logger.info('########################################  END ########################################')


if __name__ == '__main__':
    main()
