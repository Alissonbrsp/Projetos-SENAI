# 3º Semestre — Projeto Integrador de Segurança Cibernética

## InvestPrime Capital | Simulação de incidente BEC

Projeto acadêmico em equipe que reproduziu, em **ambiente controlado**, um incidente de **Business Email Compromise (BEC)** em uma empresa financeira fictícia. O trabalho percorreu o ciclo de construção da infraestrutura, simulação de ataque, investigação forense, contenção, hardening e planejamento de continuidade.

> **Aviso:** esta pasta apresenta uma versão pública e sanitizada do aprendizado. Não contém credenciais, chaves privadas, endereços de servidores, dados pessoais, logs brutos, provas de conceito executáveis nem configurações que exponham o laboratório.

### Objetivos
- Construir um ambiente corporativo simulado em nuvem.
- Compreender como phishing, comprometimento de contas e falhas de controle podem resultar em fraude.
- Investigar rastros de um incidente com preservação de evidências.
- Propor e documentar controles preventivos, detectivos e corretivos.
- Relacionar decisões técnicas à continuidade operacional e à proteção de informações.

### Tecnologias e conceitos
**AWS (EC2 e controles de acesso), Linux (Debian e Ubuntu Server), Dolibarr ERP/CRM, iRedMail, redes e firewall, análise de logs, investigação forense, hardening, MFA, gestão de privilégios, LGPD, BCP e DRP.**

### Etapas do trabalho
1. **Ambiente:** implantação de serviços de ERP e e-mail em infraestrutura AWS segregada.
2. **Simulação de incidente:** cenário de engenharia social e comprometimento de identidade, com abuso de permissões e tentativa de fraude no fluxo financeiro.
3. **Forense e resposta:** construção de linha do tempo, análise de evidências e avaliação das causas e impactos.
4. **Mitigação:** fortalecimento de autenticação, revisão de privilégios, correção de configurações e melhoria da visibilidade dos eventos.
5. **Continuidade:** planejamento de recuperação e ações para reduzir recorrência.

### Materiais públicos
- [Arquitetura e escopo](docs/arquitetura.md)
- [Incidente e investigação](docs/incidente-e-forense.md)
- [Hardening, governança e aprendizados](docs/mitigacoes-e-aprendizados.md)

### Limites
Este repositório documenta um **exercício acadêmico**, não um ataque a uma empresa real. A presença de artefatos ou documentação de uma técnica não significa que uma configuração esteja ativa ou que um controle tenha sido validado em produção. Detalhes operacionais sensíveis permanecem fora do repositório público.
