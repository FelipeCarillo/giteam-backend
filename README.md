# GiTeam

Uma plataforma inteligente que automatiza análises de Pull Requests e Issues do GitHub usando IA.

## 📋 Visão Geral

O GiTeam é uma solução completa que permite configurar agentes de IA para revisar automaticamente Pull Requests e
analisar Issues em repositórios GitHub. O sistema oferece análises detalhadas, sugestões de melhoria e feedback
construtivo, ajudando equipes a manter a qualidade do código e acelerar o processo de desenvolvimento.

## 🚀 Funcionalidades Principais

- **Análise Automatizada de PRs**: Revisão inteligente de código com feedback detalhado
- **Resolução de Issues**: Análise e sugestões para problemas reportados
- **Múltiplos Provedores de IA**: Suporte para OpenAI e Anthropic
- **Configuração Flexível**: Agentes personalizáveis com diferentes níveis de detalhamento
- **Controle de Custos**: Monitoramento e limites de gastos com APIs de IA
- **Integração Nativa**: Webhooks automáticos com GitHub

## 🏗️ Arquitetura

### Backend (FastAPI)

- **API REST** com autenticação GitHub OAuth
- **Sistema de Agentes** configuráveis por repositório
- **Processamento Assíncrono** via AWS SQS/Lambda
- **Banco de Dados** PostgreSQL para persistência
- **Controle de Custos** com histórico detalhado

### Infraestrutura (AWS CDK)

- **API Gateway** para recebimento de webhooks
- **Lambda Functions** para processamento
- **SQS Queue** para processamento assíncrono
- **Infraestrutura como Código** com Python CDK

## 🛠️ Tecnologias

- **Backend**: Python, FastAPI, SQLAlchemy, Pydantic
- **IA**: OpenAI GPT, Anthropic Claude
- **Cloud**: AWS (Lambda, SQS, API Gateway)
- **Database**: PostgreSQL
- **Infrastructure**: AWS CDK
- **Authentication**: GitHub OAuth

## 🎯 Como Funciona

1. **Configuração**: Usuário conecta repositórios GitHub e configura agentes
2. **Webhooks**: GitHub envia eventos de PR/Issue para a API
3. **Processamento**: Agentes de IA analisam o conteúdo automaticamente
4. **Feedback**: Comentários são postados diretamente no GitHub
5. **Monitoramento**: Custos e operações são rastreados em tempo real

## 🔧 Configuração Local

### Pré-requisitos

- Python 3.12+
- PostgreSQL
- Conta AWS (para deploy)
- Tokens das APIs de IA (OpenAI/Anthropic)

## 🌐 Frontend

**Link do Frontend**: https://github.com/FelipeCarillo/giteam-frontend

## 📊 Estrutura do Projeto

```
├── src/                    # Código da aplicação FastAPI
│   ├── agent/             # Lógica dos agentes de IA
│   ├── routes/            # Endpoints da API
│   ├── models/            # Modelos SQLAlchemy
│   ├── entities/          # Entidades Pydantic
│   ├── infra/             # Integrações (GitHub, Database)
│   └── webhooks/          # Handlers para webhooks
├── iac/                   # Infraestrutura AWS CDK
└── README.md
```

## 🤝 Contribuição

Contribuições são bem-vindas! Por favor, abra uma issue para discutir mudanças importantes antes de enviar um PR.

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para detalhes.

---

**Desenvolvido com ❤️ para automatizar e melhorar o processo de desenvolvimento**