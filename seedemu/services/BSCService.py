#!/usr/bin/env python
# encoding: utf-8
# __author__ = 'Ruoff'

from __future__ import annotations
from seedemu.core import Node, Service, Server
from typing import Dict, List

BSCServerFileTemplates: Dict[str, str] = {}

# genesis: the start of the chain
BSCServerFileTemplates['genesis'] = '''{
     "config": {
       "chainId": 1000,
       "homesteadBlock": 0,
       "eip155Block": 0,
       "eip158Block": 0
                },
     "nonce": "0x0000000000000061",
     "timestamp": "0x0",
     "parentHash": "0x0000000000000000000000000000000000000000000000000000000000000000",
     "gasLimit": "0x8000000",
     "difficulty": "0x100",
     "mixhash": "0x0000000000000000000000000000000000000000000000000000000000000000",
     "coinbase": "0x3333333333333333333333333333333333333333",
     "alloc": {}
}'''

# bootstrapper: get enode urls from other eth nodes.
BSCServerFileTemplates['bootstrapper'] = '''\
#!/bin/bash

while read -r node; do {
    let count=0
    ok=true

    until curl -sHf http://$node/bsc-enode-url > /dev/null; do {
        echo "bsc: node $node not ready, waiting..."
        sleep 3
        let count++
        [ $count -gt 20 ] && {
            echo "bsc: node $node failed too many times, skipping."
            ok=false
            break
        }
    }; done

    ($ok) && {
        echo "`curl -s http://$node/bsc-enode-url`," >> /tmp/bsc-node-urls
    }
}; done < /tmp/bsc-nodes
'''

# bootstrapper: get enode urls from other eth nodes.
BSCServerFileTemplates['ipdiscover'] = '''\
#!/bin/bash
ifconfig | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1'
'''

BSCServerFileTemplates['addpeers'] = '''\
variable=$(cat /tmp/bsc-node-urls)
for i in ${variable//,/ }
do
    geth --exec "admin.addPeer(\\"$i\\")" attach ipc://.node/geth.ipc
done
'''

class SmartContract():

    __abi_file_name: str
    __bin_file_name: str

    def __init__(self, contract_file_bin, contract_file_abi):
        self.__abi_file_name = contract_file_abi
        self.__bin_file_name = contract_file_bin

    def __getContent(self, file_name):
        """!
        @brief get Content of the file_name.

        @param file_name from which we want to read data.
        
        @returns Contents of the file_name.
        """
        file = open(file_name, "r")
        data = file.read()
        file.close()
        return data.replace("\n","")
        

    def generateSmartContractCommand(self):
        """!
        @brief generates a shell command which deploys the smart Contract on the ethereum network.

        @param contract_file_bin binary file of the smart Contract.

        @param contract_file_abi abi file of the smart Contract.
        
        @returns shell command in the form of string.
        """
        abi = "abi = {}".format(self.__getContent(self.__abi_file_name))
        byte_code = "byteCode = \"0x{}\"".format(self.__getContent(self.__bin_file_name))
        unlock_account = "personal.unlockAccount(eth.accounts[0], \"{}\")".format("admin")
        contract_command = "testContract = eth.contract(abi).new({ from: eth.accounts[0], data: byteCode, gas: 1000000})"
        display_contract_Info = "testContract"
        finalCommand = "{},{},{},{},{}".format(abi, byte_code, unlock_account, contract_command, display_contract_Info)

        SmartContractCommand = "sleep 30 \n \
        while true \n\
        do \n\
        \t balanceCommand=\"geth --exec 'eth.getBalance(eth.accounts[0])' attach ipc://.node/geth.ipc\" \n\
        \t balance=$(eval \"$balanceCommand\") \n\
        \t minimumBalance=1000000 \n\
        \t if [ $balance -lt $minimumBalance ] \n\
        \t then \n \
        \t \t sleep 60 \n \
        \t else \n \
        \t \t break \n \
        \t fi \n \
        done \n \
        echo \"Balance ========> $balance\" \n\
        gethCommand=\'{}\'\n\
        finalCommand=\'geth --exec \"$gethCommand\" attach ipc://.node/geth.ipc\'\n\
        result=$(eval \"$finalCommand\")\n\
        touch transaction.txt\n\
        echo \"transaction hash $result\" \n\
        echo \"$result\" >> transaction.txt\n\
        ".format(finalCommand)
        return SmartContractCommand

class BSCServer(Server):
    """!
    @brief The Ethereum Server
    """

    __id: int
    __is_bootnode: bool
    __bootnode_http_port: int
    __smart_contract: SmartContract
    __start_Miner_node: bool
    __create_new_account: int
    __enable_external_connection: bool
    __unlockAccounts: bool
    __verbosity: str

    def __init__(self, id: int):
        """!
        @brief create new eth server.

        @param id serial number of this server.
        """
        self.__id = id
        self.__is_bootnode = False
        self.__bootnode_http_port = 8088
        self.__smart_contract = None
        self.__start_Miner_node = False
        self.__create_new_account = 0
        self.__enable_external_connection = False
        self.__unlockAccounts = False
        self.__verbosity = 3

    def __createNewAccountCommand(self, node: Node):
        if self.__create_new_account > 0:
            """!
            @brief generates a shell command which creates a new account in ethereum network.
    
            @param ethereum node on which we want to deploy the changes.
            
            """
            command = " sleep 20\n\
            geth --password /tmp/bsc-password account new \n\
            "

            for count in range(self.__create_new_account):
                node.appendStartCommand('(\n {})&'.format(command))

    def __unlockAccountsCommand(self, node: Node):
        if self.__unlockAccounts:
            """!
            @brief automatically unlocking the accounts in a node.
            Currently used to automatically be able to use our emulator using Remix.
            """

            base_command = "sleep 20\n\
            geth --exec 'personal.unlockAccount(eth.accounts[{}],\"admin\",0)' attach ipc://.node/geth.ipc\n\
            "
            
            full_command = ""
            for i in range(self.__create_new_account + 1):
                full_command += base_command.format(str(i))

            node.appendStartCommand('(\n {})&'.format(full_command))

    def __addMinerStartCommand(self, node: Node):
        if self.__start_Miner_node:
            """!
            @brief generates a shell command which start miner as soon as it the miner is booted up.
            
            @param ethereum node on which we want to deploy the changes.
            
            """   
            command = " sleep 20\n\
            geth --exec 'eth.defaultAccount = eth.accounts[0]' attach ipc://.node/geth.ipc \n\
            geth --exec 'miner.start(20)' attach ipc://.node/geth.ipc \n\
            "
            node.appendStartCommand('(\n {})&'.format(command))

    def setVerbosity(self, verbosity: int):
        self.__verbosity = verbosity

    def install(self, node: Node, eth: 'DeLTService', allBootnode: bool):
        """!
        @brief ETH server installation step.

        @param node node object
        @param eth reference to the eth service.
        @param allBootnode all-bootnode mode: all nodes are boot node.
        """
        ifaces = node.getInterfaces()
        assert len(ifaces) > 0, 'DeLTServer::install: node as{}/{} has not interfaces'.format(node.getAsn(), node.getName())
        addr = str(ifaces[0].getAddress())
        this_url = '{}:{}'.format(addr, self.getBootNodeHttpPort())

        # get other nodes IP for the bootstrapper.
        bootnodes = eth.getBootNodes()[:]
        if this_url in bootnodes: bootnodes.remove(this_url)


        node.appendFile('/tmp/bsc-genesis.json', BSCServerFileTemplates['genesis'])
        node.appendFile('/tmp/bsc-nodes', '\n'.join(bootnodes))
        node.appendFile('/tmp/bsc-bootstrapper', BSCServerFileTemplates['bootstrapper'])
        node.appendFile('/tmp/bsc-password', 'admin')
        node.appendFile('/tmp/bsc-ipdiscover', BSCServerFileTemplates['ipdiscover'])
        node.appendFile('/tmp/bsc-add-peers', BSCServerFileTemplates['addpeers'])

        node.addSoftware('software-properties-common')
        node.addSoftware('wget')
        node.addSoftware('unzip')
        node.addSoftware('net-tools')

        node.addSoftware('npm')
        node.addSoftware('git')

        # enable external connection
        self.enableExternalConnection()

        # set verbosity
        self.setVerbosity(3)

        # get BSC executable and mainnet
        node.addBuildCommand('wget https://github.com/binance-chain/bsc/releases/download/v1.1.5/geth_linux -O /usr/bin/geth -q --show-progress')

        # node.addBuildCommand('git clone https://github.com/trufflesuite/truffle.git')
        # node.changeWorkdir('/truffle')
        # node.addBuildCommand('/usr/bin/npm install -g truffle')
        # node.changeWorkdir('/')
        #
        # node.addBuildCommand('git clone https://github.com/trufflesuite/ganache-ui.git')
        # node.changeWorkdir('/ganache-ui')
        # node.addBuildCommand('/usr/bin/npm install')
        # node.changeWorkdir('/')


        # Change mode of gethBSC to executable
        node.addBuildCommand('chmod +x /usr/bin/geth')

        # tap the eth repo
        node.addBuildCommand('add-apt-repository ppa:ethereum/ethereum')
        # install bootnode
        node.addBuildCommand('apt-get update && apt-get install --yes bootnode')

        datadir_option = "--datadir /.node"

        # genesis
        node.appendStartCommand('[ ! -e "/.node/geth/nodekey" ] && geth {} init /tmp/bsc-genesis.json'.format(datadir_option))

        # create account via pre-defined password
        node.appendStartCommand('[ -z `ls -A /.node/keystore` ] && geth {} --password /tmp/bsc-password account new'.format(datadir_option))

        # find the ip address of the node
        node.appendStartCommand('chmod +x /tmp/bsc-ipdiscover')
        node.appendStartCommand('echo $(/tmp/bsc-ipdiscover) > /tmp/bsc-node-ip')

        if allBootnode or self.__is_bootnode:
            # generate enode url. other nodes will access this to bootstrap the network.
            node.appendStartCommand('echo "enode://$(bootnode --nodekey /.node/geth/nodekey -writeaddress)@{}:30303" > /tmp/bsc-enode-url'.format(addr))

            # host the eth-enode-url for other nodes.
            node.appendStartCommand('python3 -m http.server {} -d /tmp'.format(self.__bootnode_http_port), True)

        # load enode urls from other nodes
        node.appendStartCommand('chmod +x /tmp/bsc-bootstrapper')
        node.appendStartCommand('/tmp/bsc-bootstrapper')

        # node.addExposePort(8545, 8545)

        # launch Ethereum process.
        common_args = '{} --identity="NODE_{}" --networkid=1000 --verbosity={} --allow-insecure-unlock ' \
                      '--nat=extip:$(/tmp/bsc-ipdiscover) --http --http.port 8545 --http.addr localhost --mine'.format(datadir_option, self.__id, int(self.__verbosity))
        if self.externalConnectionEnabled():
            remix_args = "--http.corsdomain '*' --http.api web3,eth,debug,personal,net,admin"
            common_args = '{} {}'.format(common_args, remix_args)
        if len(bootnodes) > 0:
            node.appendStartCommand('nice -n 19 geth --bootnodes "$(cat /tmp/bsc-node-urls)" {}'.format(common_args), True)
        else:
            node.appendStartCommand('nice -n 19 geth {}'.format(common_args), True)

        # manually connect to peers using discovered addresses
        node.appendStartCommand('chmod +x /tmp/bsc-add-peers')
        node.appendStartCommand('/tmp/bsc-add-peers')

        self.__createNewAccountCommand(node)
        self.__unlockAccountsCommand(node)
        self.__addMinerStartCommand(node)

        if self.__smart_contract != None :
            smartContractCommand = self.__smart_contract.generateSmartContractCommand()
            node.appendStartCommand('(\n {})&'.format(smartContractCommand))

    def getId(self) -> int:
        """!
        @brief get ID of this node.

        @returns ID.
        """
        return self.__id

    def setBootNode(self, isBootNode: bool) -> BSCServer:
        """!
        @brief set bootnode status of this node.

        Note: if no nodes are configured as boot nodes, all nodes will be each
        other's boot nodes.

        @param isBootNode True to set this node as a bootnode, False otherwise.
        
        @returns self, for chaining API calls.
        """
        self.__is_bootnode = isBootNode

        return self

    def isBootNode(self) -> bool:
        """!
        @brief get bootnode status of this node.

        @returns True if this node is a boot node. False otherwise.
        """
        return self.__is_bootnode

    def setBootNodeHttpPort(self, port: int) -> BSCServer:
        """!
        @brief set the http server port number hosting the enode url file.

        @param port port

        @returns self, for chaining API calls.
        """

        self.__bootnode_http_port = port

        return self

    def getBootNodeHttpPort(self) -> int:
        """!
        @brief get the http server port number hosting the enode url file.

        @returns port
        """
        return self.__bootnode_http_port

    def enableExternalConnection(self) -> BSCServer:
        """!
        @brief setting a node as a remix node makes it possible for the remix IDE to connect to the node
        """
        self.__enable_external_connection = True

        return self

    def externalConnectionEnabled(self) -> bool:
        """!
        @brief returns wheter a node is a remix node or not
        """
        return self.__enable_external_connection

    def createNewAccount(self, number_of_accounts = 0) -> BSCServer:
        """!
        @brief Call this api to create a new account.

        @returns self, for chaining API calls.
        """
        self.__create_new_account = number_of_accounts or self.__create_new_account + 1
        
        return self

    def unlockAccounts(self) -> BSCServer:
        """!
        @brief This is mainly used to unlock the accounts in the remix node to make it directly possible for transactions to be 
        executed through Remix without the need to access the geth account in the docker container and unlocking manually
        """
        self.__unlockAccounts = True

        return self
        
    def startMiner(self) -> BSCServer:
        """!
        @brief Call this api to start Miner in the node.

        @returns self, for chaining API calls.
        """
        self.__start_Miner_node = True

        return self

    def deploySmartContract(self, smart_contract: SmartContract) -> BSCServer:
        """!
        @brief Call this api to deploy smartContract on the node.

        @returns self, for chaining API calls.
        """
        self.__smart_contract = smart_contract

        return self

class BSCService(Service):
    """!
    @brief The Ethereum network service.

    This service allows one to run a private Ethereum network in the emulator.
    """

    __serial: int
    __all_node_ips: List[str]
    __boot_node_addresses: List[str]

    __save_state: bool
    __save_path: str

    def __init__(self, saveState: bool = False, statePath: str = './bsc-node'):
        """!
        @brief create a new Ethereum service.

        @param saveState (optional) if true, the service will try to save state
        of the block chain by saving the datadir of every node. Default to
        false.
        @param statePath (optional) path to save containers' datadirs on the
        host. Default to "./eth-states". 
        """

        super().__init__()
        self.__serial = 0
        self.__all_node_ips = []
        self.__boot_node_addresses = []

        self.__save_state = saveState
        self.__save_path = statePath

    def getName(self):
        return 'BSCService'

    def getBootNodes(self) -> List[str]:
        """
        @brief get bootnode IPs.

        @returns list of IP addresses.
        """
        return self.__all_node_ips if len(self.__boot_node_addresses) == 0 else self.__boot_node_addresses

    def _doConfigure(self, node: Node, server: BSCServer):
        self._log('configuring as{}/{} as an eth node...'.format(node.getAsn(), node.getName()))

        ifaces = node.getInterfaces()
        assert len(ifaces) > 0, 'BSCService::_doConfigure(): node as{}/{} has not interfaces'.format()
        addr = '{}:{}'.format(str(ifaces[0].getAddress()), server.getBootNodeHttpPort())

        if server.isBootNode():
            self._log('adding as{}/{} as bootnode...'.format(node.getAsn(), node.getName()))
            self.__boot_node_addresses.append(addr)

        if self.__save_state:
            node.addSharedFolder('/root/.ethereum', '{}/{}'.format(self.__save_path, server.getId()))

    def _doInstall(self, node: Node, server: BSCServer):
        self._log('installing eth on as{}/{}...'.format(node.getAsn(), node.getName()))
        
        all_bootnodes = len(self.__boot_node_addresses) == 0

        if all_bootnodes:
            self._log('note: no bootnode configured. all nodes will be each other\'s boot node.')

        server.install(node, self, all_bootnodes)

    def _createServer(self) -> Server:
        self.__serial += 1
        return BSCServer(self.__serial)

    def print(self, indent: int) -> str:
        out = ' ' * indent
        out += 'BSCService:\n'

        indent += 4

        out += ' ' * indent
        out += 'Boot Nodes:\n'

        indent += 4

        for node in self.getBootNodes():
            out += ' ' * indent
            out += '{}\n'.format(node)

        return out

class GanacheServer(BSCServer):

    def __init__(self, id: int):
        super().__init__(id)
        self.__id = id
        self.__is_bootnode = False
        self.__bootnode_http_port = 8088
        self.__smart_contract = None
        self.__start_Miner_node = False
        self.__create_new_account = 0
        self.__enable_external_connection = False
        self.__unlockAccounts = False
        self.__verbosity = 3

    def __createNewAccountCommand(self, node: Node):
        if self.__create_new_account > 0:
            """!
            @brief generates a shell command which creates a new account in ethereum network.

            @param ethereum node on which we want to deploy the changes.

            """
            command = " sleep 20\n\
            geth --password /tmp/bsc-password account new \n\
            "

            for count in range(self.__create_new_account):
                node.appendStartCommand('(\n {})&'.format(command))

    def __unlockAccountsCommand(self, node: Node):
        if self.__unlockAccounts:
            """!
            @brief automatically unlocking the accounts in a node.
            Currently used to automatically be able to use our emulator using Remix.
            """

            base_command = "sleep 20\n\
            geth --exec 'personal.unlockAccount(eth.accounts[{}],\"admin\",0)' attach ipc://.node/geth.ipc\n\
            "

            full_command = ""
            for i in range(self.__create_new_account + 1):
                full_command += base_command.format(str(i))

            node.appendStartCommand('(\n {})&'.format(full_command))

    def __addMinerStartCommand(self, node: Node):
        if self.__start_Miner_node:
            """!
            @brief generates a shell command which start miner as soon as it the miner is booted up.

            @param ethereum node on which we want to deploy the changes.

            """
            command = " sleep 20\n\
            geth --exec 'eth.defaultAccount = eth.accounts[0]' attach ipc://.node/geth.ipc \n\
            geth --exec 'miner.start(20)' attach ipc://.node/geth.ipc \n\
            "
            node.appendStartCommand('(\n {})&'.format(command))

    def setVerbosity(self, verbosity: int):
        self.__verbosity = verbosity

    def install(self, node: Node, eth: 'DeLTService', allBootnode: bool):
        """!
        @brief ETH server installation step.

        @param node node object
        @param eth reference to the eth service.
        @param allBootnode all-bootnode mode: all nodes are boot node.
        """
        ifaces = node.getInterfaces()
        assert len(ifaces) > 0, 'DeLTServer::install: node as{}/{} has not interfaces'.format(node.getAsn(),
                                                                                              node.getName())
        addr = str(ifaces[0].getAddress())
        this_url = '{}:{}'.format(addr, self.getBootNodeHttpPort())

        # get other nodes IP for the bootstrapper.
        bootnodes = eth.getBootNodes()[:]
        if this_url in bootnodes: bootnodes.remove(this_url)

        node.appendFile('/tmp/bsc-genesis.json', BSCServerFileTemplates['genesis'])
        node.appendFile('/tmp/bsc-nodes', '\n'.join(bootnodes))
        node.appendFile('/tmp/bsc-bootstrapper', BSCServerFileTemplates['bootstrapper'])
        node.appendFile('/tmp/bsc-password', 'admin')
        node.appendFile('/tmp/bsc-ipdiscover', BSCServerFileTemplates['ipdiscover'])
        node.appendFile('/tmp/bsc-add-peers', BSCServerFileTemplates['addpeers'])

        node.addSoftware('software-properties-common')
        node.addSoftware('wget')
        node.addSoftware('unzip')
        node.addSoftware('net-tools')

        node.addSoftware('npm')
        node.addSoftware('git')

        # enable external connection
        self.enableExternalConnection()

        # set verbosity
        self.setVerbosity(3)

        # get BSC executable and mainnet
        node.addBuildCommand(
            'wget https://github.com/binance-chain/bsc/releases/download/v1.1.5/geth_linux -O /usr/bin/geth -q --show-progress')

        node.addBuildCommand('git clone https://github.com/poanetwork/blockscout')
        node.changeWorkdir('/blockscout')
        # node.addBuildCommand('/usr/bin/npm install -g truffle')
        # node.changeWorkdir('/')

        # node.addBuildCommand('git clone https://github.com/trufflesuite/ganache-ui.git')
        # node.changeWorkdir('/ganache-ui')
        node.addBuildCommand('/usr/bin/npm install -g ganache-cli')
        # node.changeWorkdir('/')

        # Change mode of gethBSC to executable
        node.addBuildCommand('chmod +x /usr/bin/geth')

        # tap the eth repo
        node.addBuildCommand('add-apt-repository ppa:ethereum/ethereum')
        # install bootnode
        node.addBuildCommand('apt-get update && apt-get install --yes bootnode')

        datadir_option = "--datadir /.node"

        # genesis
        node.appendStartCommand(
            '[ ! -e "/.node/geth/nodekey" ] && geth {} init /tmp/bsc-genesis.json'.format(datadir_option))

        # create account via pre-defined password
        node.appendStartCommand(
            '[ -z `ls -A /.node/keystore` ] && geth {} --password /tmp/bsc-password account new'.format(datadir_option))

        # find the ip address of the node
        node.appendStartCommand('chmod +x /tmp/bsc-ipdiscover')
        node.appendStartCommand('echo $(/tmp/bsc-ipdiscover) > /tmp/bsc-node-ip')

        if allBootnode or self.__is_bootnode:
            # generate enode url. other nodes will access this to bootstrap the network.
            node.appendStartCommand(
                'echo "enode://$(bootnode --nodekey /.node/geth/nodekey -writeaddress)@{}:30303" > /tmp/bsc-enode-url'.format(
                    addr))

            # host the eth-enode-url for other nodes.
            node.appendStartCommand('python3 -m http.server {} -d /tmp'.format(self.__bootnode_http_port), True)

        # load enode urls from other nodes
        node.appendStartCommand('chmod +x /tmp/bsc-bootstrapper')
        node.appendStartCommand('/tmp/bsc-bootstrapper')

        # node.addExposePort(8545, 8545)

        # launch Ethereum process.
        common_args = '{} --identity="NODE_{}" --networkid=1000 --verbosity={} --allow-insecure-unlock ' \
                      '--nat=extip:$(/tmp/bsc-ipdiscover) --http --http.port 8545 --http.addr localhost --mine'.format(
            datadir_option, self.__id, int(self.__verbosity))
        if self.externalConnectionEnabled():
            remix_args = "--http.corsdomain '*' --http.api web3,eth,debug,personal,net,admin"
            common_args = '{} {}'.format(common_args, remix_args)
        if len(bootnodes) > 0:
            node.appendStartCommand('nice -n 19 geth --bootnodes "$(cat /tmp/bsc-node-urls)" {}'.format(common_args),
                                    True)
        else:
            node.appendStartCommand('nice -n 19 geth {}'.format(common_args), True)

        # manually connect to peers using discovered addresses
        node.appendStartCommand('chmod +x /tmp/bsc-add-peers')
        node.appendStartCommand('/tmp/bsc-add-peers')

        self.__createNewAccountCommand(node)
        self.__unlockAccountsCommand(node)
        self.__addMinerStartCommand(node)

        if self.__smart_contract != None:
            smartContractCommand = self.__smart_contract.generateSmartContractCommand()
            node.appendStartCommand('(\n {})&'.format(smartContractCommand))

class GanacheService(Service):
    """!
    @brief The Ethereum network service.

    This service allows one to run a private Ethereum network in the emulator.
    """

    __serial: int
    __all_node_ips: List[str]
    __boot_node_addresses: List[str]

    __save_state: bool
    __save_path: str

    def __init__(self, saveState: bool = False, statePath: str = './bsc-node'):
        """!
        @brief create a new Ethereum service.

        @param saveState (optional) if true, the service will try to save state
        of the block chain by saving the datadir of every node. Default to
        false.
        @param statePath (optional) path to save containers' datadirs on the
        host. Default to "./eth-states".
        """

        super().__init__()
        self.__serial = 0
        self.__all_node_ips = []
        self.__boot_node_addresses = []

        self.__save_state = saveState
        self.__save_path = statePath

    def getName(self):
        return 'Ganache'

    def getBootNodes(self) -> List[str]:
        """
        @brief get bootnode IPs.

        @returns list of IP addresses.
        """
        return self.__all_node_ips if len(self.__boot_node_addresses) == 0 else self.__boot_node_addresses

    def _doConfigure(self, node: Node, server: BSCServer):
        self._log('configuring as{}/{} as an eth node...'.format(node.getAsn(), node.getName()))

        ifaces = node.getInterfaces()
        assert len(ifaces) > 0, 'GanacheService::_doConfigure(): node as{}/{} has not interfaces'.format()
        addr = '{}:{}'.format(str(ifaces[0].getAddress()), server.getBootNodeHttpPort())

        if server.isBootNode():
            self._log('adding as{}/{} as bootnode...'.format(node.getAsn(), node.getName()))
            self.__boot_node_addresses.append(addr)

        if self.__save_state:
            node.addSharedFolder('/root/.ethereum', '{}/{}'.format(self.__save_path, server.getId()))

    def _doInstall(self, node: Node, server: GanacheServer):
        self._log('installing eth on as{}/{}...'.format(node.getAsn(), node.getName()))

        all_bootnodes = len(self.__boot_node_addresses) == 0

        if all_bootnodes:
            self._log('note: no bootnode configured. all nodes will be each other\'s boot node.')

        server.install(node, self, all_bootnodes)

    def _createServer(self) -> Server:
        self.__serial += 1
        return GanacheServer(self.__serial)

    def print(self, indent: int) -> str:
        out = ' ' * indent
        out += 'BSCService:\n'

        indent += 4

        out += ' ' * indent
        out += 'Boot Nodes:\n'

        indent += 4

        for node in self.getBootNodes():
            out += ' ' * indent
            out += '{}\n'.format(node)

        return out
