#!/usr/bin/env python3
# encoding: utf-8

from seedemu.core import Emulator, Binding, Filter
from seedemu.mergers import DEFAULT_MERGERS
from seedemu.compiler import Docker
from os import mkdir, chdir, getcwd, path


emuA = Emulator()
emuB = Emulator()

# Load the pre-built components and merge them
emuA.load('../B00-mini-internet/base-component.bin')
emuB.load('./component-blockchain.bin')
emu = emuA.merge(emuB, DEFAULT_MERGERS)

# Binding virtual nodes to physical nodes
emu.addBinding(Binding('bsc1', filter = Filter(asn = 151)))
emu.addBinding(Binding('bsc2', filter = Filter(asn = 152)))
emu.addBinding(Binding('bsc3', filter = Filter(asn = 163)))
emu.addBinding(Binding('bsc4', filter = Filter(asn = 164)))
emu.addBinding(Binding('bsc5', filter = Filter(asn = 150)))
emu.addBinding(Binding('bsc6', filter = Filter(asn = 170)))

output = './output'

def createDirectoryAtBase(base:str, directory:str, override:bool = False):
    cur = getcwd()
    if path.exists(base):
        chdir(base)
        if override:
            rmtree(directory)
        mkdir(directory)
    chdir(cur)


saveState = True
def updateBscStates():
    if saveState:
        createDirectoryAtBase(output, "bsc-node/")
        for i in range(1, 7):
            createDirectoryAtBase(output, "bsc-node/" + str(i))

# Render and compile
emu.render()

# If output directory exists and override is set to false, we call exit(1)
# updateOutputdirectory will not be called
emu.compile(Docker(), output, override=True)
updateBscStates()
