# Goal

To provide a site/app/service that can provide the following:

1. Documentation on the following:
 1. EC2 responses from openstack (and how to request them)
 1. Expected EC2 responses from EC2 (or via proxy via a mock server)
1. An implementation that can return mock EC2 results
 1. i.e. by implementing a simple server that holds a in-memory set of images/instances and 
    can accept/return valid responses and statuses as well as have the ability to create faults
    on demand (ie by a special URI paramter)
 1. A.k.a. a EC2 server (valid for a given EC2 api/wsdl/xsd version/date) without needing EC2...
1. A framework which can be used by QA to verify the compatability level in an automated fashion 
   by running a given set of profiles (ie a profile could be a request for an instance followed by
   a describe instance followed by a terminate instance) against the expected output for a given 
   profile (where the expected output is created using the mock EC2 server)
1. Improved openstack EC2 support by continuously increasing the previous compatability level