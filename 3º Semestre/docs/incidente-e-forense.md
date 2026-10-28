# Simulação de incidente e investigação forense

## Cenário

O exercício simulou uma cadeia de comprometimento iniciada por **phishing**, seguida de uso indevido de credenciais, exploração de fragilidades de aplicação e abuso de permissões, com risco de **Business Email Compromise (BEC)** e fraude financeira. Todas as ações pertenciam ao laboratório acadêmico autorizado.

## Principais atividades estudadas

- **Engenharia social e identidade:** como mensagens fraudulentas podem levar ao comprometimento de contas.
- **Aplicações e permissões:** como falhas técnicas e de autorização podem ampliar o alcance de um incidente.
- **Movimentação entre componentes:** avaliação de riscos quando diferentes serviços e identidades compartilham confiança excessiva.
- **Fraude de processo:** impacto do comprometimento do e-mail sobre solicitações e aprovações financeiras.
- **Detecção e investigação:** correlação temporal de eventos de autenticação, aplicação e infraestrutura.

## Metodologia forense

1. Delimitar escopo e preservar evidências disponíveis.
2. Registrar origem, integridade e cadeia de custódia dos artefatos.
3. Analisar registros de autenticação, serviços web e eventos da infraestrutura.
4. Construir uma linha do tempo para relacionar ações e impactos.
5. Produzir um relatório pós-incidente com causas prováveis, limitações e recomendações.

O material original do projeto incluiu relatórios de ambiente, pós-incidente e evidências técnicas. **Logs originais, hashes vinculados a arquivos internos, dados de usuários e detalhes de exploração não foram publicados aqui.**

## Lições

A investigação não deve se limitar a encontrar uma vulnerabilidade: é necessário compreender a sequência dos eventos, o impacto no negócio, as falhas de controle e as evidências que sustentam as conclusões.
