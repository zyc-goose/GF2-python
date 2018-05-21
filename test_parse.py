from names import Names
from scanner import Scanner
from parse import Parser
from devices import Devices
from network import Network
from monitors import Monitors

path = 'full_adder.txt'
names = Names()
scanner = Scanner(path, names)
devices = Devices(names)
network = Network(names, devices)
monitors = Monitors(names, devices, network)
parser = Parser(names, devices, network, monitors, scanner)

parser.parse_network()
