#!/usr/bin/env python
#
# This script check AWS IAM for account and key inactive for 90 days
# Actual deactivation commented out for now
#
# You need to configure aws cli (python) with your id and secret
# You need to install boto3 aws python sdk
# dependencies pip install awscli boto3 pytz
# 
#

import boto3
import pytz
from datetime import datetime

present = datetime.now(pytz.utc)  # UTC aware time
iam = boto3.resource('iam')
client = boto3.client("iam")

KEY = 'LastUsedDate'

for user in iam.users.all():
    profile = user.LoginProfile()
    # block executed for user with console access
    try:
        profile.load()  # Will crash if no console access, couldn't find a more elegant way to test
        lastUsed = user.password_last_used
        if lastUsed is not None:
            timedelta = present - lastUsed
            if timedelta.days < 90:
                print "OK USER ", user.name, 'password used less than  90 ago OK'
            else:
                print "KO USER: ", user.user_name, "console access deactivated due to inactivity for more than 90 days"
                profile.delete()
        else:
            # checking for creation datetime
            createDate = profile.create_date
            timedelta = present - createDate
            if timedelta.days < 90:
                print "OK USER created less than 90 ago, User: ", user.user_name, "date: ",  createDate
            else:
                print "KO USER created more than 90 ago, User: ", user.user_name, "date: ",  createDate, "Console access is Active but NEVER USED, console access deactivated"
                profile.delete()
    except:
        print "User ", user.user_name, "No console access skipping test"

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
                        print "KO KEY, more than 90 days since last activity, key deaactivated! User: ", user.user_name,  "Key: ", AccessId, "AK Last Used: ", LastUsed['AccessKeyLastUsed'][KEY]
                        key.deactivate()
                    else:
                        print "OK KEY User: ", user.user_name,  "Key: ", AccessId, "AK Last Used: ", LastUsed['AccessKeyLastUsed'][KEY]
                else:
                    keyCreateDate = key.create_date
                    timedelta = present - keyCreateDate
                    if timedelta.days < 90:
                        print "OK KEY created less than 90 ago, User: ", user.user_name, "Key: ",  AccessId, "Key is Active but NEVER USED"
                    else:
                        print "KO KEY created more than 90 ago, key deaactivated! User: ", user.user_name, "Key: ",  AccessId, "Key is Active but NEVER USED"
                        key.deactivate()
            else:
                    print "NA KEY User: ", user.user_name, "Key: ",  AccessId, "Keys is InActive"


