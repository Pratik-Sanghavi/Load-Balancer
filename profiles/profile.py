# THIS FILE MUST BE NAMED profile.py for cloudlab to recognize it
"""
Creates a profile with a client machine, load balancer and backend nodes
The profile also installs docker on all the "server" nodes and runs a custom docker image on the load balancer and backend nodes
Currently we auto start the Nginx and HAProxy load balancers
The backend nodes run a simple hello world docker image by Hashicorp

Instructions:
1. Go to https://www.cloudlab.us/
2. Click on "Create Slice"
3. Click on "Add a Profile"
4. Click on "Import Profile"
5. Copy the contents of this file and paste it in the text box
6. Click on "Create Profile"
7. Click on "Instantiate" to create a new experiment
8. Wait for the experiment to start

And you're done! You should now have a client machine, load balancer and backend nodes running in your experiment
"""

import geni.portal as portal
import geni.rspec.pg as rspec

pc = portal.Context()

pc.defineParameter("nodeCount", "Number of backend nodes", portal.ParameterType.INTEGER, 3)
pc.defineParameter("nodeType", "Hardware Type", portal.ParameterType.NODETYPE, "c220g1")
pc.defineParameter("osImage", "OS Image", portal.ParameterType.IMAGE,
                   "urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU24-64-STD")
pc.defineParameter("nginxDocker", "Nginx Docker Image", portal.ParameterType.STRING, "nginx:latest")
pc.defineParameter("haproxyDocker", "HAProxy Docker Image", portal.ParameterType.STRING,
                   "haproxytech/haproxy-alpine:latest")
pc.defineParameter("bkDocker", "Backend Docker Image", portal.ParameterType.STRING,
                   "hashicorp/http-echo:latest")

params = pc.bindParameters()
request = pc.makeRequestRSpec()

lan_frontend = rspec.LAN()
lan_frontend.bandwidth = 10000000  # 10 Gbps

lan_backend = rspec.LAN()
lan_backend.bandwidth = 10000000  # 10 Gbps

client = request.RawPC("client")
client.hardware_type = params.nodeType
client.disk_image = params.osImage
client_iface = client.addInterface("if-client")
lan_frontend.addInterface(client_iface)
client.addService(rspec.Execute(shell="sh", command="sudo apt-get update"))

# === Load Balancer ===
lb = request.RawPC("loadBalancer")
lb.hardware_type = params.nodeType
lb.disk_image = params.osImage

# Frontend interface to client
lb_iface_frontend = lb.addInterface("if-lb-frontend")
lan_frontend.addInterface(lb_iface_frontend)

# Backend interface to backend nodes
lb_iface_backend = lb.addInterface("if-lb-backend")
lan_backend.addInterface(lb_iface_backend)

lb.addService(rspec.Execute(shell="sh", command="sudo apt-get update && sudo apt-get install -y docker.io"))

# Nginx setup
lb.addService(rspec.Execute(shell="sh", command="mkdir -p /users/prsangh/logs/nginx /users/prsangh/nginx_config"))
lb.addService(rspec.Execute(shell="sh", command="wget -O /users/prsangh/nginx_config/nginx.conf "
                                                 "https://raw.githubusercontent.com/Pratik-Sanghavi/Load-Balancer/main/nginx_config/nginx.conf"))
lb.addService(rspec.Execute(shell="sh", command="sudo docker run -d --name nginx-lb "
                                                 "-p 80:80 "
                                                 "-v /users/prsangh/logs/nginx:/var/log/nginx "
                                                 "-v /users/prsangh/nginx_config/nginx.conf:/etc/nginx/nginx.conf:ro "
                                                 "{}".format(params.nginxDocker)))

# HAProxy setup
lb.addService(rspec.Execute(shell="sh", command="mkdir -p /users/prsangh/logs/haproxy /users/prsangh/haproxy_config"))
lb.addService(rspec.Execute(shell="sh", command="wget -O /users/prsangh/haproxy_config/haproxy.cfg "
                                                 "https://raw.githubusercontent.com/Pratik-Sanghavi/Load-Balancer/main/haproxy_config/haproxy.cfg"))
lb.addService(rspec.Execute(shell="sh", command="sudo docker run -d --name haproxy-lb "
                                                 "-p 81:80 -p 8404:8404 "
                                                 "-v /users/prsangh/logs/haproxy:/var/log/haproxy "
                                                 "-v /users/prsangh/haproxy_config/haproxy.cfg:/usr/local/etc/haproxy/haproxy.cfg:ro "
                                                 "{}".format(params.haproxyDocker)))

# === Backend Nodes ===
for i in range(params.nodeCount):
    node = request.RawPC("backend{}".format(i))
    node.hardware_type = params.nodeType
    node.disk_image = params.osImage
    iface = node.addInterface("if-back{}".format(i))
    lan_backend.addInterface(iface)

    node.addService(rspec.Execute(shell="sh", command="sudo apt-get update && sudo apt-get install -y docker.io"))
    echo_text = "Welcome from backend {}".format(i)
    node.addService(rspec.Execute(shell="sh", command="sudo docker run -d --name backend{} "
                                                       "-p 8080:5678 "
                                                       "{} -text='{}'"
                                  .format(i, params.bkDocker, echo_text)))

# Attach LANs
request.addResource(lan_frontend)
request.addResource(lan_backend)

pc.printRequestRSpec(request)
