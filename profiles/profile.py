# THIS FILE MUST BE NAMED profile.py for cloudlab to recognize it
import geni.portal as portal
import geni.rspec.pg as rspec

pc = portal.Context()

pc.defineParameter("nodeCount", "Number of backend nodes", portal.ParameterType.INTEGER, 4)
pc.defineParameter("nodeType", "Hardware Type for backend nodes", portal.ParameterType.NODETYPE, "c220g5") # NIC available for experimental use for this node type
pc.defineParameter("osImage", "Disk Image for the VMs", portal.ParameterType.IMAGE, "urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU20-64-STD")
pc.defineParameter("lbDocker", "Custom Docker Image for the Load Balancer", portal.ParameterType.STRING, "nginx:latest") # the first load balancer we want to benchmark
pc.defineParameter("bkDocker", "Custom Docker Image for the Backend Nodes", portal.ParameterType.STRING, "hashicorp/http-echo:latest") # Just a hello world image since we aren't testing the backend

params = pc.bindParameters()

request = pc.makeRequestRSpec()

lan = rspec.LAN()
lan.bandwidth = 10000000  # 10 Gbps

load_balancer = request.RawPC("loadBalancer")
load_balancer.hardware_type = params.nodeType
load_balancer.disk_image = params.osImage

load_balancer.addService(rspec.Execute(shell="sh", command="sudo apt-get update && sudo apt-get install -y docker.io"))
load_balancer.addService(rspec.Execute(shell="sh", command="sudo docker run -d --name loadBalancer {}".format(params.lbDocker)))

lb_iface = load_balancer.addInterface("if-lb")
lan.addInterface(lb_iface)

for i in range(params.nodeCount):
    node = request.RawPC("backend{}".format(i))
    node.hardware_type = params.nodeType
    node.disk_image = params.osImage
    node.addService(rspec.Execute(shell="sh", command="sudo apt-get update && sudo apt-get install -y docker.io"))
    node.addService(rspec.Execute(shell="sh", command="sudo docker run -d --name backend{} {}".format(i, params.bkDocker)))
    
    iface = node.addInterface("if-back{}".format(i))
    lan.addInterface(iface)
    
request.addResource(lan)
pc.printRequestRSpec(request)