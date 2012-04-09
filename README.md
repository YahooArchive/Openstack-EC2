# Goal

To provide a site/app/service that can provide the following:

1. Documentation on the following:
 1. EC2 responses from openstack (and how to request them)
 1. Expected EC2 responses from EC2 (or via proxy via a mock server)
1. An implementation that can return mock EC2 results
 1. I.e. by implementing a simple server that holds a in-memory set of images/instances and 
    can accept/return valid responses and statuses as well as have the ability to create faults
    on demand (ie by a special URI paramter)
 1. Aka a EC2 server (valid for a given EC2 api/wsdl/xsd version) without needing EC2