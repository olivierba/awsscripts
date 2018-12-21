from __future__ import print_function

import boto3
import json
import pytz
import logging
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

present = datetime.now(pytz.utc)  # UTC aware time
iam = boto3.resource('iam')
client = boto3.client("iam")

KEY = 'LastUsedDate'

def lambda_handler(event, context):
    logger.info("Event: " + str(event))
    logger.info("Starting inactive account review")
    for user in iam.users.all():
        profile = user.LoginProfile()
        # block executed for user with console access
        try:
            profile.load()  # Will crash if no console access, couldn't find a more elegant way to test
            lastUsed = user.password_last_used
            if lastUsed is not None:
                timedelta = present - lastUsed
                if timedelta.days < 90:
                    logger.info("OK USER %s password used less than  90 ago OK", user.name)
                else:
                    logger.warning("KO USER: %s , console access deactivated due to inactivity for more than 90 days", user.user_name)
                    profile.delete()
            else: 
                # checking for creation datetime
                createDate = profile.create_date
                timedelta = present - createDate
                if timedelta.days < 90:
                    logger.info("OK USER created less than 90 ago, User: %s date: %s", user.user_name,  createDate)
                else:
                    logger.warning("KO USER created more than 90 ago, User: %s date: %s Console access is Active but NEVER USED, console access deactivated", user.user_name,  createDate)
                    profile.delete()
        except:
            logger.info("User %s No console access skipping test", user.user_name)


        # checking access keys
        Metadata = client.list_access_keys(UserName=user.user_name)
        if Metadata['AccessKeyMetadata']:
            for key in user.access_keys.all():
                AccessId = key.access_key_id
                Status = key.status
                LastUsed = client.get_access_key_last_used(AccessKeyId=AccessId)
                if Status == "Active":
                    if KEY in LastUsed['AccessKeyLastUsed']:
                        # check if used less than 90 days ago
                        lastKeyUsed = LastUsed['AccessKeyLastUsed'][KEY]
                        timedelta = present - lastKeyUsed
                        if timedelta.days > 90:
                            logger.warning("KO KEY, more than 90 days since last activity, key deaactivated! User: %s Key: %s, AK Last Used: %s", user.user_name, AccessId, LastUsed['AccessKeyLastUsed'][KEY])
                            key.deactivate()
                        else:
                            logger.info("OK KEY User: %s Key: %s AK Last Used: %s", user.user_name, AccessId, LastUsed['AccessKeyLastUsed'][KEY])
                    else:
                        keyCreateDate = key.create_date
                        timedelta = present - keyCreateDate
                    if timedelta.days < 90:
                        logger.info("OK KEY created less than 90 ago, User: %s Key: %s, Key is Active but NEVER USED", user.user_name,  AccessId)
                    else:
                        logger.warning("KO KEY created more than 90 ago, key de-activated! User: %s Key: %s, Key is Active but NEVER USED", user.user_name,  AccessId)
                        key.deactivate()
                else:
                    logger.info("NA KEY User: %s  Key: %s Keys is Inactive", user.user_name,  AccessId)
    logger.info("Account review completed")


