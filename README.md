# To-Do
- [x] Configuração de ambiente
- [x] Criar conta no **ZeroTier**
- [ ] Efetuar ping remoto entre hosts
- [ ] Criar script em Python para fazer troca de mensagens P2P
- [ ] Definição do esqueleto do código para blockchain e ferramentas
- [ ] Implementações
- [ ] Testes locais
- [ ] Testes em grupo
- [ ] Validação dos resultados

# Utilidades
- [Painel Web](https://my.zerotier.com/network/9bee8941b5431cb5)
- **Network ID**: 9bee8941b5431cb5

# Usando Docker
- Em um diretório com o arquivo `docker-compose.yml`, execute `docker compose up -d`
- Verifique informações úteis utilizando `docker-compsoe -f`
- Execute `docker exec zerotier zerotier-cli listnetwork`
    - Isto irá executar o `zerotier-cli` dentro do container e executar o command `listnetworks`
- Se funcionar, irá retornar algo como *200 listnetworks 9bee8941b5431cb5 myNetworkName b6:d1:6d:9e:73:89 **OK PRIVATE** zt3jn4uxia 10.x.x.x*
    - **9bee8941b5431cb5**: conectado à rede 9bee8941b5431cb5 (com o nome *myNetwork*)
    - **b6:d1:6d:9e:73:89**: MAC virtual
    - **OK**: Autorizado e conectado
    - **zt3jn4uxia**: Interface 
    - **10.x.x.x**: IP atribuído

