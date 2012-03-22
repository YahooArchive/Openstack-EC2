import os
import sqlite3
import time
import urllib2

import webob
import webob.dec
import webob.exc

import xml.sax.saxutils as xmlutils

from mock import log as logging
from mock import wsgi
from mock import utils

INSTANCE_FORMAT = 'instance-%08x'
LOG = logging.getLogger('mock.ec2')


class Ec2Mock(object):

    STATES = {
        '0': 'pending',
        '16': 'running',
        '32': 'shutting-down',
        '48': 'terminated',
        '64': 'stopping',
        '80': 'stopped'
    }

    ERROR_TEMPLATE = u'''
<?xml version="1.0" encoding="UTF-8"?>
<Response>
   <Errors>
      <Error>
         <Code>%CODE%</Code>
         <Message>%MESSAGE%</Message>
      </Error>
   </Errors>
   <requestID>%REQUEST_ID%</requestID>
</Response>'''

    DESCRIBE_IMAGES_TEMPLATE = '''
<DescribeImagesResponse xmlns="http://ec2.amazonaws.com/doc/2011-12-15/">
   <requestId>%REQUEST_ID%</requestId> 
   <imagesSet>
      <item>
         <imageId>%IMAGE_ID%</imageId>
         <imageLocation/>
         <imageState>available</imageState>
         <imageOwnerId>206029621532</imageOwnerId>
         <isPublic>true</isPublic>
         <architecture>x86_64</architecture>
         <imageType>machine</imageType>
         <platform>linux</platform>
         <imageOwnerAlias>foo</imageOwnerAlias>
         <rootDeviceType>instance-store</rootDeviceType>
         <name>%NAME%</name>
         <description>%DESCRIPTION%</description>
         <blockDeviceMapping/>
         <virtualizationType>hvm</virtualizationType>
         <tagSet/>
         <hypervisor>kvm</hypervisor>
      </item>
   </imagesSet>
</DescribeImagesResponse>'''

    DESCRIBE_INSTANCES_TEMPLATE = '''
<DescribeInstancesResponse xmlns="http://ec2.amazonaws.com/doc/2011-12-15/"> 
   <requestId>%REQUEST_ID%</requestId> 
   <reservationSet>
      <item>
         <reservationId>r-bc7e30d7</reservationId>
         <ownerId>111122223333</ownerId>
         <groupSet>
            <item>
               <groupId>sg-2eac845a</groupId>
               <groupName>default</groupName>    
            </item>
         </groupSet>
         <instancesSet>
            <item>
               <instanceId>%INSTNACE_ID%</instanceId>
               <imageId>%IMAGE_ID%</imageId>
               <instanceState>
                  <code>%CODE%</code>
                  <name>%STATE%</name>
               </instanceState>
               <privateDnsName>domU-12-31-39-01-76-06.compute-1.internal</privateDnsName>
               <dnsName>ec2-72-44-52-124.compute-1.amazonaws.com</dnsName>
               <keyName>GSG_Keypair</keyName>
               <amiLaunchIndex>0</amiLaunchIndex>
               <productCodes/>
               <instanceType>m1.small</instanceType>
               <launchTime>2010-08-17T01:15:16.000Z</launchTime>
               <placement>
                  <availabilityZone>us-east-1b</availabilityZone>
               </placement>
               <kernelId>aki-94c527fd</kernelId>
               <ramdiskId>ari-96c527ff</ramdiskId>
               <monitoring>
                  <state>disabled</state>
               </monitoring>
               <privateIpAddress>10.255.121.240</privateIpAddress>
               <ipAddress>%IP%</ipAddress>
               <sourceDestCheck>true</sourceDestCheck>
               <groupSet>
                  <item>
                     <groupId>sg-2eac845a</groupId>
                     <groupName>default</groupName>    
                  </item>
               </groupSet>
               <architecture>i386</architecture>
               <rootDeviceType>ebs</rootDeviceType>
               <rootDeviceName>/dev/sda1</rootDeviceName>
               <blockDeviceMapping>
                  <item>
                     <deviceName>/dev/sda1</deviceName>
                     <ebs>
                        <volumeId>vol-a482c1cd</volumeId>
                        <status>attached</status>
                        <attachTime>2010-08-17T01:15:26.000Z</attachTime>
                        <deleteOnTermination>true</deleteOnTermination>
                     </ebs>
                  </item>
               </blockDeviceMapping>
               <virtualizationType>paravirtual</virtualizationType>
               <clientToken/>
               <tagSet/>
               <hypervisor>xen</hypervisor>
            </item>
         </instancesSet>
      </item>
   </reservationSet>
</DescribeInstancesResponse>
'''
    
    RUN_INSTANCES_TEMPLATE = '''
<RunInstancesResponse xmlns='http://ec2.amazonaws.com/doc/2011-11-15/'>
    <requestId>%REQUEST_ID%</requestId>
    <reservationId>r-157ad274</reservationId>
    <ownerId>111122223333</ownerId>
    <groupSet/>
    <instancesSet>
        <item>
            <instanceId>%INSTANCE_ID%</instanceId>
            <imageId>%IMAGE_ID%</imageId>
            <instanceState>
                <code>0</code>
                <name>pending</name>
            </instanceState>
            <privateDnsName/>
            <dnsName/>
            <reason/>
            <amiLaunchIndex>0</amiLaunchIndex>
            <productCodes/>
            <instanceType>m1.small</instanceType>
            <launchTime>2011-12-20T08:29:31.000Z</launchTime>
            <placement>
                <availabilityZone>us-east-1b</availabilityZone>
                <groupName/>
                <tenancy>default</tenancy>
            </placement>
            <kernelId>aki-805ea7e9</kernelId>
            <monitoring>
                <state>disabled</state>
            </monitoring>
            <subnetId>subnet-b2a249da</subnetId>
            <vpcId>vpc-1ea24976</vpcId>
            <privateIpAddress>10.0.0.142</privateIpAddress>
            <sourceDestCheck>true</sourceDestCheck>
            <groupSet>
                <item>
                    <groupId>sg-050c1369</groupId>
                    <groupName>default</groupName>
                </item>
            </groupSet>
            <stateReason>
                <code>pending</code>
                <message>pending</message>
            </stateReason>
            <architecture>i386</architecture>
            <rootDeviceType>ebs</rootDeviceType>
            <rootDeviceName>/dev/sda1</rootDeviceName>
            <blockDeviceMapping/>
            <virtualizationType>paravirtual</virtualizationType>
            <clientToken/>
            <hypervisor>xen</hypervisor>
            <networkInterfaceSet>
                <item>
                    <networkInterfaceId>eni-c6bb50ae</networkInterfaceId>
                    <subnetId>subnet-b2a249da</subnetId>
                    <vpcId>vpc-1ea24976</vpcId>
                    <description/>
                    <ownerId>111122223333</ownerId>
                    <status>in-use</status>
                    <privateIpAddress>10.0.0.142</privateIpAddress>
                    <sourceDestCheck>true</sourceDestCheck>
                    <groupSet>
                        <item>
                            <groupId>sg-050c1369</groupId>
                            <groupName>default</groupName>
                        </item>
                    </groupSet>
                    <attachment>
                        <attachmentId>eni-attach-0326646a</attachmentId>
                        <deviceIndex>0</deviceIndex>
                        <status>attaching</status>
                        <attachTime>2011-12-20T08:29:31.000Z</attachTime>
                        <deleteOnTermination>true</deleteOnTermination>
                    </attachment>
                </item>
            </networkInterfaceSet>
        </item>
    </instancesSet>
</RunInstancesResponse>
'''

    TERMINATE_INSTANCES_TEMPLATE = '''
<TerminateInstancesResponse xmlns="http://ec2.amazonaws.com/doc/2011-12-15/">
  <requestId>%REQUEST_ID%</requestId> 
  <instancesSet>
    <item>
      <instanceId>%INSTANCE_ID%</instanceId>
      <currentState>
        <code>32</code>
        <name>shutting-down</name>
      </currentState>
      <previousState>
        <code>16</code>
        <name>running</name>
      </previousState>
    </item>
  </instancesSet>
</TerminateInstancesResponse>
'''
    
    def __init__(self, config):
        self.cfg = config
        self.active_ip = [10, 0, 0, 1]
        self.rollover_ip = list(self.active_ip)
        self.instance_id = 0
        self.request_id = -1
        self.instances = dict()
        self.images = dict()
        self.images['ami_1234567890'] = {
            'name': 'RHEL 6.2',
            'description': 'Linux_rhel6.2'
        }

    def _fill_in_template(self, template, values):
        data = template

        # fill in the template values
        for k, v in values.iteritems():
            v = xmlutils.escape(v)
            data = data.replace("%%%s%%" % k.upper(), v)

        return data
    
    def _make_instance_id(self):
        instance_id = INSTANCE_FORMAT % (self.instance_id)
        self.instance_id += 1
        return instance_id

    def _run_instances(self, req):
        image_id = req.params.getall('ImageId')
        if not image_id or image_id[0] not in self.images:
            return self._error_response('NoImageID', 'No such image id')

        image_id = image_id[0]
        instance_id = self._make_instance_id()

        self.instances[instance_id] = {}
        self.instances[instance_id]['code'] = '0'
        self.instances[instance_id]['ts'] = time.time()
        self.instances[instance_id]['ip'] = ''

        return self._fill_in_template(Ec2Mock.RUN_INSTANCES_TEMPLATE,
                                      {
                                         'REQUEST_ID': str(self.request_id),
                                         'INSTANCE_ID': instance_id,
                                         'IMAGE_ID': image_id
                                      })

    def _terminate_instances(self, req):
        iid = req.params.getall('InstanceId.1')
        if not iid or iid[0] not in self.instances:
            return self._error_response('NoInstanceID', 'No instance id')

        iid = iid[0]
        data = self._fill_in_template(Ec2Mock.TERMINATE_INSTANCES_TEMPLATE,
                                      {
                                         'REQUEST_ID': str(self.request_id),
                                         'INSTANCE_ID': iid
                                      })
        del self.instances[iid]
        return data

    def _describe_images(self, req):
        ipam = req.params.getall('ImageId.1')
        if not ipam or ipam[0] not in self.images:
            return self._error_response('NoImageID', 'No image id')

        image_id = ipam[0]
        data = self._fill_in_template(Ec2Mock.DESCRIBE_IMAGES_TEMPLATE,
                                      {
                                         'REQUEST_ID': str(self.request_id),
                                         'IMAGE_ID': image_id,
                                         'NAME': self.images[image_id]['name'],
                                         'DESCRIPTION': self.images[image_id]['description']
                                      })
        return data

    def _make_ip(self):
        new_ip = list(self.active_ip)
        new_ip.reverse()
        for i, c in enumerate(new_ip):
            if i == 3:
                # Roll over
                new_ip = list(self.rollover_ip)
                new_ip.reverse()
                break
            new_ip[i] += 1
            if new_ip[i] <= 255:
                break
            else:
                new_ip[i] = new_ip[i] - 1
        new_ip.reverse()
        self.active_ip = list(new_ip)
        ip_strs = [str(c) for c in new_ip]
        return ".".join(ip_strs)

    def _describe_instances(self, req):
        iid = req.params.getall('InstanceId.1')
        if not iid or iid[0] not in self.instances:
            return self._error_response('NoInstanceID', 'No instance id')

        iid = iid[0]
        code = self.instances[iid]['code']
        ts = self.instances[iid]['ts']
        ip = self.instances[iid]['ip']
        now = time.time()
        
        if code == '0' and now > (ts + 20):
            self.instances[iid]['code'] = code = '16'
            ip = self._make_ip()
            self.instances[iid]['ip'] = ip

        return self._fill_in_template(Ec2Mock.DESCRIBE_INSTANCES_TEMPLATE,
                                      {
                                         'REQUEST_ID': str(self.request_id),
                                         'INSTANCE_ID': iid,
                                         'CODE': code,
                                         'STATE': Ec2Mock.STATES[code],
                                         'IP': ip
                                      })

    def _check_signature(self, req):
        return True

    def _error_response(self, code, message):
        data = self._fill_in_template(Ec2Mock.ERROR_TEMPLATE, {
                           'CODE': code,
                           'MESSAGE': message,
                           'REQUEST_ID': str(self.request_id)
                        })
        return data
        
    def _do_mock(self, req):
        action = req.params.getall('Action')
        LOG.debug('Handling a %r request.' % action)

        if not action or not action[0]:
            return self._error_response('NoAction', 'No action!')
        else: 
            action = action[0]

        body = ''
        if action == 'RunInstances':
            body = self._run_instances(req)
        elif action == 'TerminateInstances':
            body = self._terminate_instances(req)
        elif action == 'DescribeImages':
            body = self._describe_images(req)
        elif action == 'DescribeInstances':
            body = self._describe_instances(req)
        else:
            body = self._error_response('NoAction', 'No action!')

        return body

    def __call__(self, req):
        resp = webob.Response()
        self.request_id += 1
        body = self._do_mock(req)
        resp.unicode_body = body.strip()
        resp.content_type = 'text/xml'
        return resp
