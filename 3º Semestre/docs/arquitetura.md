# Arquitetura e escopo do laboratório

A **InvestPrime Capital** é uma organização fictícia do setor financeiro, usada como cenário de treinamento. A infraestrutura foi estruturada na **AWS**, com serviços distribuídos em servidores Linux:

- **ERP/CRM:** Dolibarr em Debian, representando rotinas administrativas e financeiras.
- **Correio corporativo:** iRedMail em Ubuntu Server, representando comunicações e processos dependentes de e-mail.
- **Rede e identidade:** instâncias EC2, segmentação lógica, regras de acesso e permissões de usuários e serviços.

## Fluxo lógico simplificado

```text
Usuários simulados
      |
      +--> Serviço de e-mail corporativo (iRedMail)
      |
      +--> Sistema administrativo e financeiro (Dolibarr)
                   |
              Infraestrutura AWS
          (rede, instâncias e acessos)
```

## Pontos de atenção

O projeto evidenciou a importância de separar funções, aplicar o menor privilégio, controlar acessos administrativos, proteger identidades e manter registros suficientes para auditoria. Em sistemas financeiros, e-mail e ERP fazem parte do mesmo fluxo de negócio: a falha de um pode afetar a confiança nas operações do outro.

**Sanitização:** foram omitidos nomes de contas, endereços IP, identificadores de instância, domínios, regras específicas de firewall, credenciais, chaves e capturas de tela.
