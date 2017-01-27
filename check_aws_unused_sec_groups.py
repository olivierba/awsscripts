#!/usr/bin/env python
#
# This script check AWS Security group usage to determine which one are used
# You need to configure aws cli (python) with your id and secret
# You need to install boto3 aws python sdk
#
#

import boto3

ec2 = boto3.resource('ec2')
securityGroups = ec2.security_groups
instances = ec2.instances.all()
for sg in securityGroups.all():
    present = False
    # print 'testing group ' + sg.group_name + ' id:'+sg.id
    for instance in instances:
        # print 'testing instance ' + instance.id
        all_sg_ids = [sgi['GroupId'] for sgi in instance.security_groups]
        # print all_sg_ids
        if sg.id in all_sg_ids:
            present = True
            print 'Group '+sg.group_name+' used by Instance(s) ' + instance.id 
    # print 'all instance tested for this group'
    if present is False:
        print 'Group '+sg.group_name+' unused'



