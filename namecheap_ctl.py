#!/usr/bin/env python3

# based on: https://github.com/trwnh/namecheap

import os, time
from _namecheap_client import Records
from argparse import ArgumentParser
from dotenv import load_dotenv


parser = ArgumentParser()
parser.add_argument("-e", "--env", type=str,
                    help="Name of the environment. Defines which env-file to read. If not specified `.env` file is "
                         "used. E.g. if --env=PROD, `.PROD.env` config file will be use.")
args = parser.parse_args()


CERTBOT_DOMAIN = os.getenv('CERTBOT_DOMAIN')
NEW_CHALLENGE = os.getenv('CERTBOT_VALIDATION')

load_dotenv(f'.{args.env}.env')


def set_new_challenge():
    records = Records(CERTBOT_DOMAIN)
    records.fetch_records()
    records.set_challenge(NEW_CHALLENGE)
    records.post_records()
    records.fetch_records()
    time.sleep(60)


if __name__ == "__main__":
    set_new_challenge()
