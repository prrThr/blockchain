# To-Do
- [x] Configuração de ambiente
- [x] Criar conta no **ZeroTier**
- [x] Efetuar ping remoto entre hosts
- [x] Criar script em Python para fazer troca de mensagens P2P
- [ ] Definição do esqueleto do código para blockchain e ferramentas
- [ ] Implementações
- [ ] Testes locais
- [ ] Testes em grupo
- [ ] Validação dos resultados

# Utilidades
- [Painel Web](https://my.zerotier.com/network/9bee8941b5431cb5)
- **Network ID**: 9bee8941b5431cb5
- [DockerHub](https://hub.docker.com/r/zerotier/zerotier)
- [Dockerfile](https://github.com/zerotier/ZeroTierOne/blob/dev/ext/installfiles/linux/zerotier-containerized/Dockerfile)

# Usando Docker

### Verificando se funcionou
- Abra o terminal no diretório desde projeto
- Execute `docker compose up -d` para subir um container de acordo com o `docker-compose.yml`
- Verifique informações úteis utilizando `docker-compose -f`
- Execute `docker exec zerotier zerotier-cli listnetwork`
    - Isto irá executar o `zerotier-cli` dentro do container e executar o command `listnetworks`
- Se funcionar, irá retornar algo como *200 listnetworks 9bee8941b5431cb5 myNetworkName b6:d1:6d:9e:73:89 OK PRIVATE zt3jn4uxia 10.x.x.x*

#### Explicação do retorno a cima
- **9bee8941b5431cb5**: conectado à rede 9bee8941b5431cb5 (com o nome *myNetwork*)
- **b6:d1:6d:9e:73:89**: MAC virtual
- **OK**: Autorizado e conectado
- **zt3jn4uxia**: Interface 
- **10.x.x.x**: IP atribuído

### Rodando o chat P2P
- Execute `docker exec -it zerotier python3 home/p2p_chat.py`

