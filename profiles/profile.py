# THIS FILE MUST BE NAMED profile.py for cloudlab to recognize it
import geni.portal as portal
import geni.rspec.pg as rspec

pc = portal.Context()

pc.defineParameter("nodeCount", "Number of backend nodes", portal.ParameterType.INTEGER, 4)
pc.defineParameter("nodeType", "Hardware Type for backend nodes", portal.ParameterType.NODETYPE, "c220g1") # NIC available for experimental use for this node type
pc.defineParameter("osImage", "Disk Image for the VMs", portal.ParameterType.IMAGE, "urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU20-64-STD")
pc.defineParameter("nginxDocker", "Custom Docker Image for the Nginx Load Balancer", portal.ParameterType.STRING, "nginx:latest") # the first load balancer we want to benchmark
pc.defineParameter("haproxyDocker", "Custom Docker Image for the Load Balancer", portal.ParameterType.STRING, "haproxytech/haproxy-alpine:latest")
pc.defineParameter("bkDocker", "Custom Docker Image for the Backend Nodes", portal.ParameterType.STRING, "hashicorp/http-echo:latest") # Just a hello world image since we aren't testing the backend

params = pc.bindParameters()

request = pc.makeRequestRSpec()

lan = rspec.LAN()
lan.bandwidth = 10000000  # 10 Gbps

load_balancer = request.RawPC("loadBalancer")
load_balancer.hardware_type = params.nodeType
load_balancer.disk_image = params.osImage

load_balancer.addService(rspec.Execute(shell="sh", command="sudo apt-get update && sudo apt-get install -y docker.io"))

# Nginx Load Balancer
load_balancer.addService(rspec.Execute(shell="sh", command="wget -O /users/prsangh/nginx_config/nginx.conf https://raw.githubusercontent.com/Pratik-Sanghavi/Load-Balancer/main/nginx_config/nginx.conf"))
load_balancer.addService(rspec.Execute(shell="sh", command="sudo docker run -d --name nginx-lb -p 80:80 -v /users/prsangh/logs/nginx:/var/log/nginx -v /users/prsangh/nginx_config/nginx.conf:/etc/nginx/nginx.conf {}".format(params.nginxDocker)))

# HAProxy Load Balancer
load_balancer.addService(rspec.Execute(shell="sh", command="wget -O /users/prsangh/haproxy_config/haproxy.cfg https://raw.githubusercontent.com/Pratik-Sanghavi/Load-Balancer/main/nginx_config/haproxy.cfg"))
load_balancer.addService(rspec.Execute(shell="sh", command="sudo docker run -d --name haproxy-lb -p 81:80 -p 8404:8404 -v /users/prsangh/logs/haproxy:/usr/local/etc/haproxy -v /users/prsangh/haproxy_config/haproxy.cfg:/usr/local/etc/haproxy/haproxy.cfg:ro {}".format(params.haproxyDocker)))

lb_iface = load_balancer.addInterface("if-lb")
lan.addInterface(lb_iface)

for i in range(params.nodeCount):
    text = "Welcome from backend {}".format(i)
    node = request.RawPC("backend{}".format(i))
    node.hardware_type = params.nodeType
    node.disk_image = params.osImage
    node.addService(rspec.Execute(shell="sh", command="sudo apt-get update && sudo apt-get install -y docker.io"))
    node.addService(rspec.Execute(shell="sh", command="sudo docker run -d --name backend{} -p 8080:5678 {} -text={}".format(i, params.bkDocker, text)))
    
    iface = node.addInterface("if-back{}".format(i))
    lan.addInterface(iface)
    
request.addResource(lan)
pc.printRequestRSpec(request)