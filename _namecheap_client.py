#!/usr/bin/env python3


import os, requests
from bs4 import BeautifulSoup as bs
from telegram import TelegramBot


def parse_response(result):
    soup = bs(result, 'xml')
    is_successful = soup.ApiResponse["Status"] == "OK"
    if not is_successful:
        raise Exception("Api response NOK: \n" + result)
    return soup


class ApiClient:

    def __init__(self, certbot_domain):
        if os.getenv('IS_SANDBOX'):
            self.api_url = "https://api.sandbox.namecheap.com/xml.response"
        else:
            self.api_url = "https://api.namecheap.com/xml.response"

        [_, sld, tld] = certbot_domain.split('.')
        self.params = {'ApiUser': os.getenv('API_USERNAME'), 'ApiKey': os.getenv('API_KEY'),
                       'UserName': os.getenv('NC_USERNAME'), 'ClientIp': os.getenv('CLIENT_IP'),
                       'SLD': sld, 'TLD': tld}

        self.telegram = TelegramBot(os.getenv('TELEGRAM_BOT_TOKEN'), os.getenv('TELEGRAM_CHAT_ID'))

    def fetch_hosts(self):
        params = self.params.copy()
        params['Command'] = 'namecheap.domains.dns.getHosts'
        result = requests.get(self.api_url, params=params).text
        self.telegram.send_code(result)
        return parse_response(result)

    def post_records(self, payload):
        params = self.params.copy()
        params['Command'] = 'namecheap.domains.dns.setHosts'
        params.update(payload)

        result = requests.post(self.api_url, params=params).text
        soup = parse_response(result)
        success = soup.DomainDNSSetHostsResult["IsSuccess"] == "true"
        if not success:
            raise Exception("Api response NOK: \n" + result)


class Records:
    def __init__(self, certbot_domain):
        self.api = ApiClient(certbot_domain)
        self.records = None

    def fetch_records(self):
        # Fetches list of dns records from namecheap
        soup = self.api.fetch_hosts()
        self.records = soup.find_all('host')

    def remove_challenge(self):
        for record in self.records.copy():
            if record['Name'] == '_acme-challenge':
                self.records.remove(record)

    def set_challenge(self, challenge):
        self.remove_challenge()
        challenge_soup = bs(f'<Host Name="_acme-challenge" Type="TXT" Address="{challenge}" TTL="60"', 'xml')
        self.records.append(challenge_soup.Host)

    def post_records(self):
        # Sends new configuration to namecheap API
        # NB! can be dangerous: currently only cares about name, type, address, ttl, mxpref.

        payload = {}
        # payload['EmailType'] = 'MX'  # For manual MX setup. Lookup documentation if your config is different.

        n = 1
        for record in self.records:
            payload.update({
                f'HostName{n}': record['Name'],
                f'RecordType{n}': record['Type'],
                f'Address{n}': record['Address']
            })
            if 'TTL' in record.attrs:
                payload.update({f'TTL{n}': record['TTL']})
            if 'MXPref' in record.attrs:
                payload.update({f'MXPref{n}': record['MXPref']})

            n += 1

        self.api.post_records(payload)
