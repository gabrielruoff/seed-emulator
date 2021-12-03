#!/bin/bash
chmod +x /interface_setup
/interface_setup
ip rou del default 2> /dev/null
chmod +x /tmp/bsc-ipdiscover
[ ! -e "/.node/geth/nodekey" ] && geth --datadir /.node init /tmp/bsc-genesis.json
[ -z `ls -A /.node/keystore` ] && geth --datadir /.node --password /tmp/bsc-password account new
echo $(/tmp/bsc-ipdiscover) > /tmp/bsc-node-ip
chmod +x /tmp/bsc-bootstrapper
/tmp/bsc-bootstrapper
nice -n 19 geth --bootnodes "$(cat /tmp/bsc-node-urls)" --datadir /.node --identity="explorer" --networkid=1000 --verbosity=9 --allow-insecure-unlock --nat=extip:$(/tmp/bsc-ipdiscover) --http --http.port 8545 --http.addr localhost --http.corsdomain '*' --http.api web3,eth,debug,personal,net,admin &
chmod +x /tmp/bsc-add-peers
/tmp/bsc-add-peers
(
  sleep 20
            geth --password /tmp/bsc-password account new 
            )&
(
  sleep 20
            geth --password /tmp/bsc-password account new 
            )&
(
  sleep 20
            geth --password /tmp/bsc-password account new 
            )&
(
  sleep 20
            geth --exec 'eth.defaultAccount = eth.accounts[0]' attach ipc://.node/geth.ipc 
            geth --exec 'miner.start(20)' attach ipc://.node/geth.ipc 
            )&

echo "ready! run 'docker exec -it $HOSTNAME /bin/zsh' to attach to this node" >&2
for f in /proc/sys/net/ipv4/conf/*/rp_filter; do echo 0 > "$f"; done
tail -f /dev/null
