FROM cfee3a34e9c68ac1d16035a81a926786
ARG DEBIAN_FRONTEND=noninteractive
RUN echo 'exec zsh' > /root/.bashrc
RUN apt-get update && apt-get install -y -qq --no-install-recommends curl dnsutils ipcalc iproute2 iputils-ping jq mtr-tiny nano netcat tcpdump termshark vim-nox zsh npm
RUN apt-get update && apt-get install -y -qq --no-install-recommends net-tools software-properties-common unzip wget git
RUN curl -L https://grml.org/zsh/zshrc > /root/.zshrc
RUN wget https://github.com/binance-chain/bsc/releases/download/v1.1.5/geth_linux -O /usr/bin/geth -q --show-progress
RUN chmod +x /usr/bin/geth
RUN add-apt-repository ppa:ethereum/ethereum
RUN apt-get update && apt-get install --yes bootnode
COPY start.sh /start.sh
COPY d18858afc6bb66ec3a19d872077acfd2 /seedemu_sniffer
COPY 17ac2d812a99a91e7f747e1defb72a29 /seedemu_worker
RUN chmod +x /start.sh
RUN chmod +x /seedemu_sniffer
RUN chmod +x /seedemu_worker
COPY e01e36443f9f72c6204189260d0bd276 /ifinfo.txt
COPY d3d51fdf7f4bad30dc5db560a01ce629 /interface_setup
COPY 7a1d330a625621309e76e39685bbbb19 /tmp/bsc-genesis.json
COPY 3fec51576b6d5c584dc7b017dd478976 /tmp/bsc-nodes
COPY 25605a505277487a6b4193209de5c77f /tmp/bsc-bootstrapper
COPY 4248d1aafd3af3a2e484e0289d6b1a9e /tmp/bsc-password
COPY 556e39edf49bc04a7d11179131097045 /tmp/bsc-ipdiscover
COPY 49bf2bad80a1512e5c096535cf9ceb9b /tmp/bsc-add-peers

WORKDIR /usr/src/app
RUN git clone https://github.com/etherparty/explorer
CMD ["/start.sh"]
WORKDIR /usr/src/app/explorer
#CMD ["npm", "init"]
#ENTRYPOINT ["/usr/bin/npm", "start"]
