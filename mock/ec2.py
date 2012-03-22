import os
import time
import urllib2
import webob
import webob.dec

from mock import log as logging
from mock import wsgi


IP_FORMAT='10.0.0.%d'
INSTANCE_FORMAT = 'i_000%d'
LOG = logging.getLogger('mock.ec2')


class Ec2Mock(object):

    REQUEST_ID = 0
    IP_NUMBER = 1
    INSTANCE_NUMBER = 1

    INSTANCES = {}

    IMAGES = {
        'ami_1234567890': {
            'name': 'RHEL 6.2',
            'description': 'Linux_rhel6.2'
        }
    }

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

    def _fill_in_template(self, template, values):
        data = template

        # fill in the template values
        for k, v in values.iteritems():
            data = data.replace("%%%s%%" % k.upper(), v if v else '')

        return data

    def _run_instances(self, req):
        image_id = req.params.getall('ImageId')
        if not image_id or image_id[0] not in Ec2Mock.IMAGES:
            return self._error_response('NoImageID', 'No such image id')

        image_id = image_id[0]

        instance_id = INSTANCE_FORMAT % Ec2Mock.INSTANCE_NUMBER
        Ec2Mock.INSTANCE_NUMBER += 1

        Ec2Mock.INSTANCES[instance_id] = {}
        Ec2Mock.INSTANCES[instance_id]['code'] = '0'
        Ec2Mock.INSTANCES[instance_id]['ts'] = time.time()
        Ec2Mock.INSTANCES[instance_id]['ip'] = ''

        data = self._fill_in_template(Ec2Mock.RUN_INSTANCES_TEMPLATE,
                                      {
                                         'REQUEST_ID': str(Ec2Mock.REQUEST_ID),
                                         'INSTANCE_ID': instance_id,
                                         'IMAGE_ID': image_id
                                      })
        return data

    def _terminate_instances(self, req):
        id = req.params.getall('InstanceId.1')
        if not id or id[0] not in Ec2Mock.INSTANCES:
            return self._error_response('NoInstanceID', 'No instance id')

        id = id[0]

        data = self._fill_in_template(Ec2Mock.TERMINATE_INSTANCES_TEMPLATE,
                                      {
                                         'REQUEST_ID': str(Ec2Mock.REQUEST_ID),
                                         'INSTANCE_ID': id
                                      })
        del Ec2Mock.INSTANCES[id]
        return data

    def _describe_images(self, req):
        id = req.params.getall('ImageId.1')
        if not id or id[0] not in Ec2Mock.IMAGES:
            return self._error_response('NoImageID', 'No image id')

        id = id[0]

        data = self._fill_in_template(Ec2Mock.DESCRIBE_IMAGES_TEMPLATE,
                                      {
                                         'REQUEST_ID': str(Ec2Mock.REQUEST_ID),
                                         'IMAGE_ID': id,
                                         'NAME': Ec2Mock.IMAGES[id]['name'],
                                         'DESCRIPTION': Ec2Mock.IMAGES[id]['description']
                                      })
        return data


    def _describe_instances(self, req):
        id = req.params.getall('InstanceId.1')
        if not id or id[0] not in Ec2Mock.INSTANCES:
            return self._error_response('NoInstanceID', 'No instance id')

        id = id[0]

        code = Ec2Mock.INSTANCES[id]['code']
        ts = Ec2Mock.INSTANCES[id]['ts']
        ip = Ec2Mock.INSTANCES[id]['ip']
        now = time.time()
        
        if code == '0' and now > (ts + 20):
            Ec2Mock.INSTANCES[id]['code'] = code = '16'
            Ec2Mock.INSTANCES[id]['ip'] = ip = IP_FORMAT % Ec2Mock.IP_NUMBER
            Ec2Mock.IP_NUMBER = (Ec2Mock.IP_NUMBER + 1) % 256
        
        state = Ec2Mock.STATES[code]

        data = self._fill_in_template(Ec2Mock.DESCRIBE_INSTANCES_TEMPLATE,
                                      {
                                         'REQUEST_ID': str(Ec2Mock.REQUEST_ID),
                                         'INSTANCE_ID': id,
                                         'CODE': code,
                                         'STATE': state,
                                         'IP': ip
                                      })
        return data

    def _check_signature(self, req):
        return True

    def _error_response(self, code, message):
        data = self._fill_in_template(Ec2Mock.ERROR_TEMPLATE, {
                           'CODE': code,
                           'MESSAGE': message,
                           'REQUEST_ID': str(Ec2Mock.REQUEST_ID)
                        })
        Ec2Mock.REQUEST_ID += 1
        return data    

    def __call__(self, req):
        resp = webob.Response()
        resp.status = 200

        if not self._check_signature(req):
            resp.text = self._error_response('SignatureDoesNotMatch',
                                             'Signature problem')
            return resp

        action = req.params.getall('Action')
        LOG.debug('handling a %s request.' % action)

        if not action:
            resp.text = self._error_response('NoAction', 'No action!')
            return resp
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

        Ec2Mock.REQUEST_ID += 1
        resp.text = body
        return resp
