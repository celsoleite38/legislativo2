Sistema Legislativo Municipal
Sistema web desenvolvido em Django para gerenciamento de processos legislativos, votação de projetos e cadastro de vereadores em câmaras municipais.

🏛️ Sobre o Projeto
Sistema completo para automação dos processos de uma câmara municipal, incluindo cadastro de vereadores, gestão de projetos legislativos e sistema de votação digital.

📋 Funcionalidades Principais
👤 Administração
Superusuário exclusivo para gestão do sistema

Cadastro de usuários da secretaria com confirmação por email

Configuração do limite máximo de vereadores via upload de ata

🗂️ Gestão de Vereadores
Cadastro completo com: nome, foto, partido, ata de posse

Limite máximo configurável de vereadores

Controle de ausências durante votações

📊 Sistema de Projetos
Tipos de projetos: PL, PLO, PLC, PEC

Fluxo de status:

🟡 EM PREPARAÇÃO - Painel da secretaria

🔵 EM PAUTA - Painel do presidente

🟢 ABERTO - Em votação

🔴 FECHADO - Votação encerrada

⚖️ Sistema de Votação
Painel do Presidente: Controle de abertura/encerramento

Painel do Vereador: Interface de votação (Sim/Não/Abstenção)

Tempo regulamentar configurável

Resultados automáticos com contagem de votos

🌐 Transparência
Painel público com acompanhamento em tempo real

Status individual de cada vereador

Histórico completo de votações

🚀 Tecnologias
Python 3.x

Django Framework

PostgreSQL (ou SQLite para desenvolvimento)

Sistema de autenticação customizado

Email com token de confirmação

Upload de arquivos (PDF, imagens)

📦 Instalação
