#!/usr/bin/env python3
# WebFaction Dynamic DNS Updater

import os
import sys
import time
import argparse
import configparser
import ipaddress
import urllib.parse
import urllib.request
import xmlrpc.client

VERSION = '0.1.0'


class WFAPI:
    endpoint = 'https://api.webfaction.com/'

    # API session expires 60 mins after the last API call
    session_ttl = 3540

    def __init__(self, username, password):
        self.session_id = None
        self.last_call_time = 0
        self.server = xmlrpc.client.ServerProxy(WFAPI.endpoint)

        self.username = username
        self.password = password

        self.login(username, password)

    def has_valid_session(self):
        return (self.session_id is not None and
                self.last_call_time+WFAPI.session_ttl >= int(time.time()))

    def _call(self, method_name, *args, **kwargs):
        # Login again on session expiry
        if not self.has_valid_session() and method_name != 'login':
            if not self.login(self.username, self.password):
                raise SystemError('API auto-login failed')

        self.last_call_time = int(time.time())

        return getattr(self.server, method_name)(*args, **kwargs)

    def login(self, username, password, machine='', version=1):
        if version not in (1, 2):
            raise ValueError("Invalid parameter 'version': {}".format(version))

        result = self._call('login', username, password, machine, version)

        if len(result) and len(result[0]):
            self.session_id = result[0]
            return True

        return False

    def list_dns_overrides(self):
        return self._call('list_dns_overrides', self.session_id)

    def create_dns_override(self, domain='', a_ip='', cname='', mx_name='',
                            mx_priority='', spf_record='', aaaa_ip='',
                            srv_record=''):
        return self._call('create_dns_override', self.session_id, domain,
                          a_ip, cname, mx_name, mx_priority, spf_record,
                          aaaa_ip, srv_record)

    def delete_dns_override(self, domain='', a_ip='', cname='', mx_name='',
                            mx_priority='', spf_record='', aaaa_ip='',
                            srv_record=''):
        return self._call('delete_dns_override', self.session_id, domain,
                          a_ip, cname, mx_name, mx_priority, spf_record,
                          aaaa_ip, srv_record)

    def find_dns_override(self, domain):
        for o in self.list_dns_overrides():
            if o['domain'] == domain:
                return o

        return None


def parse_args():
    parser = argparse.ArgumentParser(
        description='WebFaction Dynamic DNS Updater'
    )
    parser.add_argument('-c', '--config',
                        help='specify a config file (default: config.ini)',
                        type=str,
                        default='config.ini'
                        )

    return parser.parse_args()


def main():
    args = parse_args()

    print('WebFaction Dynamic DNS Updater v{}'.format(VERSION))

    # Config file checks/parsing
    if not os.path.exists(args.config):
        print('Configuration file not found: {}'.format(args.config))
        sys.exit(1)

    config = configparser.ConfigParser()
    try:
        if len(config.read(args.config)) == 0:
            raise configparser.Error()
    except configparser.Error:
        print('Failed parsing configuration file: {}'.format(args.config))
        sys.exit(1)

    # Check IP discovery config value
    ip_discovery = urllib.parse.urlparse(config.get('wfdyndns', 'ip_discovery'))

    if ip_discovery.scheme.lower() not in ('http', 'https') or ip_discovery.netloc == '':
        print('Invalid ip_discover URL provided')
        sys.exit(1)

    # Check wait_mins config value
    wait_mins = config.getint('wfdyndns', 'wait_mins', fallback=10)
    if wait_mins < 1:
        print('Error, wait_mins must be a positive integer value, exiting')
        sys.exit()

    wait_secs = wait_mins*60

    # Check API config values
    api_username = config.get('wfdyndns', 'api_username')
    if not len(api_username):
        print('api_username not defined')
        sys.exit(1)

    api_password = config.get('wfdyndns', 'api_password')
    if not len(api_password):
        print('api_password not defined')
        sys.exit(1)

    # Check dns_record config value
    dns_record = config.get('wfdyndns', 'dns_record')
    if not len(dns_record):
        print('dns_record not defined')
        sys.exit(1)

    # (Re-)initialise the API
    api_init = True

    # Process loop
    while True:
        try:
            # Initialise API object
            if api_init:
                api_init = False
                api = WFAPI(api_username, api_password)

            # Get external IP address
            try:
                ip_str = urllib.request.urlopen(config['wfdyndns']['ip_discovery'], timeout=10) \
                                                .read().decode('ascii').strip()
            except urllib.request.URLError:
                print('Failed getting external IP address, waiting...')
                api_init = True
                sys.stdout.flush()
                time.sleep(wait_secs)
                continue

            try:
                ip = ipaddress.ip_address(ip_str)
            except ValueError:
                print('Failed parsing IP address: {}, waiting...'.format(ip_str))
                sys.stdout.flush()
                time.sleep(wait_secs)
                continue

            print('External IP address: {}'.format(ip))

            # Checking A or AAAA record based on our IP address
            ip_field = 'a_ip'
            if isinstance(ip, ipaddress.IPv6Address):
                ip_field = 'aaaa_ip'

            # Try and find an existing DNS record
            dns_override = api.find_dns_override(config.get('wfdyndns', 'dns_record'))

            # Record requires creating/updating
            if dns_override is None or \
               (dns_override is not None and str(ip) != dns_override[ip_field]):
                print('Updating DNS record...')

                # Wipe any existing DNS record entries
                api.delete_dns_override(domain=dns_record)

                if isinstance(ip, ipaddress.IPv4Address):
                    api.create_dns_override(domain=dns_record, a_ip=str(ip), aaaa_ip='')
                else:
                    api.create_dns_override(domain=dns_record, a_ip='', aaaa_ip=str(ip))
            else:
                print('No update required')

            print('Waiting for {} minute(s)...'.format(wait_mins))
            sys.stdout.flush()
            time.sleep(wait_secs)
        except OSError:
            api_init = True
            print('Possible network failure detected, waiting...')
            sys.stdout.flush()
            time.sleep(wait_secs)
            continue
        except KeyboardInterrupt:
            sys.exit()

if __name__ == '__main__':
    main()
