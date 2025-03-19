#!/bin/bash

# Add a virtual IP (VIP) for IPVS (use any internal port, e.g., 82)
IPVS_VIP="10.10.1.1"
IPVS_PORT="82"
BACKEND_PORT="8080"

echo "Adding $VIRTUAL_IP to service ..."
ipvsadm -A -t $IPVS_VIP -s wlc

# Add the real servers (RIPs) to the virtual service
ipvsadm -a -t ${IPVS_VIP} -r 10.10.1.2:8080 -m
ipvsadm -a -t ${IPVS_VIP} -r 10.10.1.3:8080 -m
ipvsadm -a -t ${IPVS_VIP} -r 10.10.1.4:8080 -m
ipvsadm -a -t ${IPVS_VIP} -r 10.10.1.5:8080 -m

# Keep the container running
tail -f /dev/null