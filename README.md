### What is this repository for? ###

This script is designated for сreation of scheduled _OR_ launch scanning jobs in Tenable.io against next targets:
* Google Cloud Platform. Script retrieves public IP addresses from: Compute, SQL Cloud and VPC Reserved addresses
* Cloudflare. Script retrieves DNS type A records and schedule mostly WEB scan by standard Tenable.io engine
* Amazon Web Services. Script retrieves AWS assets from Tenable.io and schedule scan by Tenable.io engine
* Linode. Script retrieves servers (linodes) and schedule scan of all publicly faced resources by Tenable.io engine
* Custom. Script retrived targets from configuration file.

### Prerequisites ###

* GCP service account MUST have Role - Viewer or for safety you can create custom one.
* GCP service account MUST be added to whole organization.
* Create and add separate account to every Cloudflare account.
* Create separate account in Tenable.io for scheduling scans.
* Create separate or general Tenable.io scanning policy.
* Create and sync Tenable.io AWS connectors to all Company AWS accounts.
* Create folders in Tenable.io under :
  * GCP
  * Cloudflare
  * AWS
  * Linode
  * Others
* Email to send notifications about Tenable.io vulnerability scan

### How do I get set up a script? ###

* Clone repository
* Goto sec-network-automate-scan
* Install virtual env:
    ```bash
    pip install virtualenv
    virtualenv venv
    source venv/bin/activate
    ```
* Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
* Copy and rename configuration template file from temple:
    ```bash
    cp conf/conf.cfg.template --> conf/conf.cfg
    ```
* Add config options to Configuration file
* Run script (see section: Usage)
Schedule script via cron (see folder: additional)

### Usage ###
* Use script with below arguments:
    ```bash
    Usage:
      main.py [OPTIONS]
    
    OPTIONS:
       -all           Scan all SaaS public infrastructures
       -gcp           Scan GCP infrastructure
       -aws           Scan AWS infrastructure
       -linode        Scan Linode infrastructure
       -cloudflare    Scan Cloudflare infrastructure
       -other         Scan custom targets
       -schedule      Schedule scanning jobs
    ```

### Coming Features ###
* N/A
