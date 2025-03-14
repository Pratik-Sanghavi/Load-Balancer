# Load Balancer

This repository is created for managing different load balancing profiles on cloud lab. Currently we support:

* `nginx`
* `haproxy`

The default configuration has 4 backend instances behind the load balancer instance. Although we provide the configuration files as well, these won't be preloaded on the load balancer docker. Rather copy them to the path expected by the load balancer docker and reload the load balancer to use the new profile. We still need to figure out a suitable way to auto-deploy with the correct configuration from the very beginning.