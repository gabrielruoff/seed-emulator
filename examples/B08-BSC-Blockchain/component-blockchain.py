#!/usr/bin/env python3
# encoding: utf-8
import seedemu
from seedemu import *

emu = Emulator()

# Create the Binance layer
# saveState=True: will set the blockchain folder using `volumes`, 
# so the blockchain data will be preserved when containers are deleted.
# Note: right now we need to manually create the folder for each node (see README.md). 
bsc = seedemu.services.BSCService(saveState = True)
ganache = seedemu.services.GanacheService(saveState = True)
# bsc.BSCServer.setVerbosity(4)

# Create Binance nodes (nodes in this layer are virtual)
b1 = bsc.install("bsc1")
b2 = bsc.install("bsc2")
b3 = bsc.install("bsc3")
b4 = bsc.install("bsc4")
b5 = bsc.install("bsc5")
b6 = bsc.install("bsc6")
g1 = ganache.install("gan1")

# Set bootnodes on e1 and e2. The other nodes can use these bootnodes to find peers.
# Start mining on e1 - e4
b1.setBootNode(True).setBootNodeHttpPort(8081).startMiner()
b2.setBootNode(True).startMiner()
b3.startMiner()
b4.startMiner()

# Create more accounts on e5 and e6
b5.startMiner().createNewAccount(3)
b6.createNewAccount().createNewAccount()

# Create a smart contract and deploy it from node e3 
# We need to put the compiled smart contracts inside the Contracts/ folder
#smart_contract = SmartContract("./Contracts/contract.bin", "./Contracts/contract.abi")
#b3.deploySmartContract(smart_contract)

# Customizing the display names (for visualization purpose)
emu.getVirtualNode('bsc1').setDisplayName('Binance-1')
emu.getVirtualNode('bsc2').setDisplayName('Binance-2')
emu.getVirtualNode('bsc3').setDisplayName('Binance-3')
emu.getVirtualNode('bsc4').setDisplayName('Binance-4')
emu.getVirtualNode('bsc5').setDisplayName('Binance-5')
emu.getVirtualNode('bsc6').setDisplayName('Binance-6')
emu.getVirtualNode('gan1').setDisplayName('Ganache-1')

# Add the layer and save the component to a file
emu.addLayer(bsc)
emu.addLayer(ganache)
emu.dump('component-blockchain.bin')
