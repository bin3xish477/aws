#!/bin/bash
### Install zaproxy
#curl -Ls https://github.com/zaproxy/zaproxy/releases/download/v2.10.0/ZAP_2.10.0_Linux.tar.gz > /tmp/ZAP_2.10.0_Linux.tar.gz
curl -Ls https://workshops.devax.academy/security-for-developers/module2/files/ZAP_2.10.0_Linux.tar.gz > /tmp/ZAP_2.10.0_Linux.tar.gz
cd /tmp
tar -xzvf ZAP_2.10.0_Linux.tar.gz
sudo mv /tmp/ZAP_2.10.0/ /opt/zaproxy

### Install Java
sudo yum update
sudo amazon-linux-extras enable corretto8 -y
sudo yum install java-1.8.0-amazon-corretto -y

### Inject into systemd
sudo cat > /lib/systemd/system/zaproxy.service << EOL
[Unit]
Description=OWASP Zap Headless
After=multi-user.target

[Service]
Type=idle
ExecStart=/opt/zaproxy/zap.sh -daemon -host 0.0.0.0 -port 8080 -config api.addrs.addr.name=.* -config api.addrs.addr.regex=true -config api.key=$API_KEY -config proxy.behindnat=true
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOL
sudo systemctl daemon-reload
sudo systemctl enable zaproxy.service
sudo systemctl start zaproxy.service
