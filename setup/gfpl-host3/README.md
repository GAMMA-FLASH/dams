configurare il packet forwarding sul mainpc

entra sul mainpc in ssh:
Funzione per abilitare il forwarding temporaneo

```
ssh gamma@mainpc_ip
sudo sysctl -w net.ipv4.ip_forward=1
```

per disabilitare il forwarding , mettere `0`

lancia lo script per mappare le porte del dams a delle porte sul mainpc. apri il firewall per un ip specifico dove gireranno i client

```
ssh gamma@mainpc_ip
sudo ./iptables_forward.sh add 192.168.1.10 192.168.1.20 1234 5678 enps1
```
