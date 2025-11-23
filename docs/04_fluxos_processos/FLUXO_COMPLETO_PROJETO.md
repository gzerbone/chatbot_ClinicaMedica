# 📋 Fluxo Completo do Projeto - Chatbot Clínica Médica

## 🎯 Visão Geral

Este documento descreve **detalhadamente e visualmente** o fluxo completo do sistema de chatbot para clínica médica, desde a recepção de mensagens do WhatsApp até a geração de handoffs para a secretária.

---

## 📑 Índice

- [Arquitetura do Sistema](#arquitetura-do-sistema)
- [Fluxo de Dados Completo](#fluxo-de-dados-completo)
- [Detalhamento por Componente](#detalhamento-por-componente)
- [Fluxo de Agendamento Visual](#fluxo-de-agendamento-visual)
- [Persistência e Sincronização](#persistência-e-sincronização)
- [Monitoramento e Logs](#monitoramento-e-logs)
- [Diagramas de Sequência](#diagramas-de-sequência)
- [Configuração e Deploy](#configuração-e-deploy)

---

## 🏗️ Arquitetura do Sistema

### Visão Macro da Arquitetura

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         SISTEMA CHATBOT CLÍNICA                           │
└──────────────────────────────────────────────────────────────────────────┘

                           ┌─────────────────┐
                           │   📱 PACIENTE   │
                           │    WhatsApp     │
                           └────────┬────────┘
                                    │
                                    │ Mensagem
                                    ▼
                    ┌───────────────────────────────┐
                    │  🌐 WhatsApp Business API     │
                    │  - Recebe mensagens           │
                    │  - Envia respostas            │
                    └───────────┬───────────────────┘
                                │
                                │ Webhook POST
                                ▼
┌───────────────────────────────────────────────────────────────────────┐
│                         🖥️ DJANGO SERVER                               │
├───────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  📨 API GATEWAY (app)                                           │ │
│  ├─────────────────────────────────────────────────────────────────┤ │
│  │                                                                   │ │
│  │  ┌──────────────────┐         ┌──────────────────┐             │ │
│  │  │  views.py        │────────►│ process_message  │             │ │
│  │  │  - webhook       │         │ - orchestrator   │             │ │
│  │  └──────────────────┘         └────────┬─────────┘             │ │
│  │                                         │                        │ │
│  │                                         ▼                        │ │
│  │              ┌─────────────────────────────────────────┐        │ │
│  │              │    🤖 GEMINI CHATBOT SERVICE            │        │ │
│  │              │    (MODULARIZADO - 5 MÓDULOS)           │        │ │
│  │              ├─────────────────────────────────────────┤        │ │
│  │              │  Core Service (Orquestrador):           │        │ │
│  │              │  1. SessionManager → Obtém sessão       │        │ │
│  │              │  2. IntentDetector → Analisa intenção   │        │ │
│  │              │  3. EntityExtractor → Extrai entidades  │        │ │
│  │              │  4. RAG Service → Consulta dados        │        │ │
│  │              │  5. ResponseGenerator → Gera resposta   │        │ │
│  │              │  6. Valida agendamento                  │        │ │
│  │              │  7. Gera handoff (se completo)          │        │ │
│  │              │  8. SessionManager → Atualiza sessão    │        │ │
│  │              └───┬─────────────────────────┬───────────┘        │ │
│  │                  │                         │                    │ │
│  └──────────────────┼─────────────────────────┼────────────────────┘ │
│                     │                         │                      │
│  ┌──────────────────▼─────────────────────────▼──────────────────┐  │
│  │              SERVIÇOS DE APOIO                                 │  │
│  ├────────────────────────────────────────────────────────────────┤  │
│  │                                                                  │  │
│  │  📊 ConversationService    🔍 SmartSchedulingService           │  │
│  │  - Gerencia sessões         - Consulta horários                │  │
│  │  - Histórico de msgs        - Google Calendar                  │  │
│  │  - Extração de nomes        - Valida médicos                   │  │
│  │                                                                  │  │
│  │  📚 RAGService              🔗 HandoffService                   │  │
│  │  - Dados da clínica         - Gera links WhatsApp              │  │
│  │  - Médicos, exames          - Mensagens formatadas             │  │
│  │  - Especialidades           - Transferência secretária         │  │
│  │                                                                  │  │
│  │  📈 TokenMonitor            📅 GoogleCalendarService            │  │
│  │  - Monitora tokens          - Disponibilidade real             │  │
│  │  - Modo econômico           - Horários livres                  │  │
│  │  - Alertas de uso           - Validação de datas               │  │
│  │                                                                  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

           ┌──────────────────────────┬──────────────────────────┐
           │                          │                          │
           ▼                          ▼                          ▼
    ┌─────────────┐          ┌─────────────┐          ┌─────────────┐
    │ 💾 DATABASE │          │ 💨 CACHE    │          │ 🔮 GEMINI AI│
    │   SQLite3   │          │ Django Mem  │          │  Google API │
    ├─────────────┤          ├─────────────┤          ├─────────────┤
    │ - Sessions  │          │ - Sessions  │          │ - Análise   │
    │ - Messages  │          │ - Clinic    │          │ - Resposta  │
    │ - Clinic    │          │   Data      │          │ - Entidades │
    │   Data      │          │ - Tokens    │          │             │
    └─────────────┘          └─────────────┘          └─────────────┘

                    ┌────────────────────────────┐
                    │  📅 GOOGLE CALENDAR API    │
                    │  - Disponibilidade médicos │
                    │  - Horários livres         │
                    └────────────────────────────┘
```

---

## 🔄 Fluxo de Dados Completo

### Fluxo Simplificado: Da Mensagem à Resposta

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FLUXO SIMPLIFICADO DO SISTEMA                    │
└─────────────────────────────────────────────────────────────────────┘

📱 MENSAGEM DO USUÁRIO
   │
   │ "Olá, quero agendar uma consulta"
   │
   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ ETAPA 1: RECEPÇÃO E PREPARAÇÃO                                     │
├─────────────────────────────────────────────────────────────────────┤
│ • Recebe mensagem via WhatsApp Webhook                              │
│ • Extrai número do telefone e texto da mensagem                     │
│ • Busca ou cria sessão de conversa no banco de dados               │
│ • Carrega histórico de mensagens anteriores (últimas 10)           │
│ • Carrega dados da clínica (médicos, especialidades, etc.)        │
└─────────────────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ ETAPA 2: ANÁLISE INTELIGENTE DA MENSAGEM                           │
├─────────────────────────────────────────────────────────────────────┤
│ • Identifica a intenção do usuário (agendar, perguntar, etc.)      │
│ • Extrai informações relevantes (nome, especialidade, médico, data, horário)       │
│ • Determina qual deve ser o próximo passo da conversa              │
└─────────────────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ ETAPA 3: PROCESSAMENTO ESPECIALIZADO                                │
├─────────────────────────────────────────────────────────────────────┤
│ • Verifica se precisa confirmar nome do paciente                    │
│ • Detecta se usuário quer tirar dúvidas (pausa agendamento)        │
│ • Valida horários fornecidos contra Google Calendar                 │
│ • Verifica se todas informações estão completas para confirmar     │
└─────────────────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ ETAPA 4: ATUALIZAÇÃO E PERSISTÊNCIA                                │
├─────────────────────────────────────────────────────────────────────┤
│ • Atualiza informações coletadas na sessão                         │
│ • Corrige estado da conversa automaticamente                       │
│ • Salva mensagens no histórico do banco de dados                    │
│ • Sincroniza dados entre cache e banco                               │
└─────────────────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ ETAPA 5: GERAÇÃO DA RESPOSTA                                       │
├─────────────────────────────────────────────────────────────────────┤
│ • Gera resposta contextualizada baseada na análise                  │
│ • Inclui informações relevantes (horários, médicos, etc.)          │
│ • Formata mensagem de forma amigável e profissional                 │
└─────────────────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ ETAPA 6: ENVIO E FINALIZAÇÃO                                       │
├─────────────────────────────────────────────────────────────────────┤
│ • Envia resposta via WhatsApp Business API                          │
│ • Registra conclusão do processamento                               │
└─────────────────────────────────────────────────────────────────────┘
   │
   ▼
📱 RESPOSTA PARA O USUÁRIO
   "Olá! Qual é o seu nome completo?"
```

---

### Explicação Detalhada de Cada Etapa

#### ETAPA 1: RECEPÇÃO E PREPARAÇÃO

Quando uma mensagem chega ao sistema, o primeiro passo é preparar o ambiente para processá-la adequadamente. O sistema precisa recuperar o contexto da conversa e os dados necessários para entender e responder corretamente.

**Recuperação da Sessão de Conversa**

O sistema identifica o usuário pelo número de telefone e busca sua sessão de conversa no banco de dados. Se é a primeira vez que o usuário interage, uma nova sessão é criada com estado inicial "ocioso". A sessão armazena todas as informações coletadas durante o processo de agendamento, como nome do paciente, especialidade escolhida, médico selecionado, data e horário preferidos, além do estado atual da conversa.

O sistema também mantém uma cópia da sessão em memória (cache) para acesso rápido, sincronizando periodicamente com o banco de dados para garantir persistência. Isso permite que mesmo se o sistema reiniciar, a conversa possa ser retomada de onde parou.

**Carregamento do Histórico de Conversa**

Para entender o contexto da mensagem atual, o sistema recupera as últimas 10 mensagens trocadas com o usuário. Isso permite que o sistema compreenda referências a mensagens anteriores, como quando o usuário diz "esse médico" ou "naquela data". O histórico inclui tanto as mensagens do usuário quanto as respostas do sistema, permitindo uma compreensão completa do diálogo.

**Carregamento dos Dados da Clínica**

O sistema carrega informações atualizadas sobre a clínica, incluindo lista de médicos disponíveis, suas especialidades, horários de funcionamento, valores de consultas, convênios aceitos e outras informações relevantes. Esses dados são armazenados em cache para evitar consultas repetidas ao banco de dados, melhorando a performance do sistema. Os dados são atualizados automaticamente quando há mudanças no cadastro da clínica.

---

#### ETAPA 2: ANÁLISE INTELIGENTE DA MENSAGEM

Esta etapa utiliza inteligência artificial para compreender profundamente o que o usuário está comunicando, tanto em termos de intenção quanto de informações específicas.

**Identificação da Intenção**

O sistema analisa a mensagem do usuário para determinar qual é sua intenção principal. As intenções possíveis incluem: agendar uma consulta, buscar informações sobre a clínica, confirmar dados fornecidos, tirar dúvidas, ou simplesmente cumprimentar. Esta análise considera não apenas as palavras usadas, mas também o contexto da conversa atual e o histórico de mensagens anteriores.

Por exemplo, se o usuário está no meio de um agendamento e pergunta "Quanto custa?", o sistema entende que a intenção é buscar informação, mas mantém o contexto de que está no processo de agendamento. Se o usuário diz "Sim, está correto" após ver um resumo, o sistema identifica a intenção como confirmação.

**Extração de Informações Relevantes**

Paralelamente à identificação da intenção, o sistema extrai informações específicas mencionadas na mensagem. Isso inclui o nome do paciente (quando fornecido), a especialidade médica desejada, o nome do médico escolhido, datas e horários mencionados. A extração é feita de forma inteligente, reconhecendo diferentes formas de expressar a mesma informação.

Por exemplo, o sistema reconhece que "segunda-feira", "segunda", "próxima segunda" e "18/11" podem se referir à mesma data. Da mesma forma, "14h", "14:00", "duas da tarde" e "14 horas" são todas reconhecidas como o mesmo horário. O sistema também é capaz de lidar com referências relativas, como "amanhã", "depois de amanhã" ou "próxima semana".

**Determinação do Próximo Passo**

Com base na intenção identificada, nas informações extraídas e no estado atual da conversa, o sistema determina qual deve ser o próximo passo. Se o usuário está iniciando um agendamento, o próximo passo é coletar o nome. Se já tem o nome mas falta a especialidade, o próximo passo é perguntar sobre a especialidade desejada. O sistema sempre segue uma ordem lógica: primeiro o nome, depois a especialidade, em seguida o médico, e por fim a data e horário.

---

#### ETAPA 3: PROCESSAMENTO ESPECIALIZADO

Esta etapa contém lógicas específicas para situações particulares que podem ocorrer durante a conversa, garantindo que o sistema responda adequadamente a cada cenário.

**Confirmação do Nome do Paciente**

Quando o sistema detecta que o usuário está fornecendo ou confirmando seu nome, um processo especial é acionado. Se o nome foi mencionado pela primeira vez, ele é extraído da mensagem e armazenado temporariamente, aguardando confirmação. O sistema então pergunta ao usuário se o nome está correto, evitando erros de interpretação.

Se o usuário confirma o nome (dizendo "sim", "correto", "isso", etc.), o nome é definitivamente salvo e marcado como confirmado. O sistema então verifica quais informações ainda faltam para o agendamento e direciona automaticamente para a próxima etapa necessária. Se o usuário rejeita o nome, o sistema solicita que ele digite novamente.

Este processo de confirmação é feito de forma otimizada, gerando respostas diretamente sem precisar consultar a inteligência artificial novamente, economizando recursos e garantindo respostas mais rápidas.

**Sistema de Pausar e Retomar**

Durante o processo de agendamento, o usuário pode ter dúvidas que precisam ser esclarecidas antes de continuar. O sistema detecta quando o usuário está fazendo uma pergunta (como "Quanto custa?" ou "Vocês aceitam meu convênio?") e pausa temporariamente o fluxo de agendamento.

Quando isso acontece, o sistema salva o estado atual do agendamento (por exemplo, "escolhendo médico") e muda para um estado especial de "respondendo dúvidas". O sistema então responde a dúvida do usuário utilizando sua base de conhecimento sobre a clínica.

Após responder, o sistema pode retomar automaticamente o agendamento de duas formas: se o usuário fornece informações de agendamento (como mencionar uma especialidade ou médico), o sistema detecta isso e retoma automaticamente. Alternativamente, se o usuário diz palavras como "continuar" ou "retomar", o sistema restaura o estado anterior e continua de onde parou.

**Validação de Horários em Tempo Real**

Quando o usuário fornece uma data e horário desejados, o sistema imediatamente consulta o calendário do médico no Google Calendar para verificar se aquele horário específico está realmente disponível. Esta validação acontece assim que a informação é fornecida, não esperando até a confirmação final.

Se o horário solicitado não está disponível, o sistema informa isso ao usuário e sugere automaticamente horários alternativos disponíveis no mesmo dia ou em outros dias próximos. Isso evita que o usuário confirme um agendamento para um horário que não está livre, melhorando a experiência e evitando retrabalho.

A validação também acontece novamente no momento da confirmação final, pois o horário pode ter sido ocupado entre o momento em que foi sugerido e o momento da confirmação. Isso garante que apenas horários realmente disponíveis sejam confirmados.

**Verificação de Completude**

Antes de gerar o link de confirmação para a secretária, o sistema verifica se todas as informações necessárias foram coletadas: nome do paciente confirmado, especialidade escolhida, médico selecionado, data e horário válidos. Se alguma informação estiver faltando, o sistema identifica qual é a primeira informação faltante na ordem de prioridade e solicita essa informação ao usuário, retornando ao estado apropriado da conversa.

---

#### ETAPA 4: ATUALIZAÇÃO E PERSISTÊNCIA

Após processar a mensagem e extrair as informações, o sistema atualiza a sessão de conversa e garante que todos os dados sejam persistidos corretamente.

**Atualização da Sessão**

As informações extraídas da mensagem são salvas na sessão do usuário. Se o usuário mencionou uma especialidade, ela é validada contra o banco de dados para garantir que existe e está ativa, e então é salva. O mesmo acontece com o médico mencionado: o sistema verifica se o médico existe, se atende a especialidade escolhida, e então salva a informação.

O sistema também atualiza o estado da conversa para refletir o progresso. Por exemplo, quando o nome é confirmado e a especialidade é escolhida, o estado muda para "selecionando médico". Esta atualização de estado é feita automaticamente pelo sistema, garantindo que sempre reflita corretamente em que etapa do processo o usuário se encontra.

**Correção Automática de Estado**

O sistema possui uma lógica inteligente que corrige automaticamente o estado da conversa baseado nas informações já coletadas. Por exemplo, se o usuário forneceu o médico antes da especialidade (fora da ordem normal), o sistema salva ambas as informações e ajusta o estado para refletir que agora precisa apenas da data e horário, mesmo que o estado anterior indicasse que estava coletando especialidade.

Esta correção garante que o sistema sempre saiba exatamente o que falta coletar, independentemente da ordem em que o usuário fornece as informações, tornando o processo mais flexível e natural.

**Persistência no Banco de Dados**

Todas as informações são salvas no banco de dados para garantir persistência. A sessão é atualizada com as novas informações, e as mensagens trocadas (tanto do usuário quanto do sistema) são registradas no histórico. Isso permite que o sistema possa recuperar o contexto completo da conversa a qualquer momento, mesmo após reinicializações.

O sistema também mantém uma cópia em cache (memória) para acesso rápido, sincronizando periodicamente com o banco de dados. Esta estratégia de dupla persistência garante tanto performance quanto confiabilidade.

---

#### ETAPA 5: GERAÇÃO DA RESPOSTA

Com todas as informações processadas e a sessão atualizada, o sistema gera uma resposta apropriada para o usuário.

**Geração Contextualizada**

A resposta é gerada considerando múltiplos fatores: a intenção identificada, o estado atual da conversa, as informações já coletadas, o que ainda falta coletar, e o contexto do histórico de mensagens. O sistema utiliza inteligência artificial para criar respostas naturais e conversacionais, adaptando o tom e o conteúdo conforme a situação.

Por exemplo, se o usuário está no início do processo, a resposta será uma saudação e uma solicitação do nome. Se já tem várias informações coletadas, a resposta será mais direta e focada no que falta. Se o usuário está confirmando dados, a resposta será um resumo claro e uma solicitação de confirmação.

**Inclusão de Informações Relevantes**

Quando apropriado, a resposta inclui informações úteis para o usuário. Se está escolhendo especialidade, a resposta lista as especialidades disponíveis. Se está escolhendo médico, lista os médicos da especialidade escolhida com suas informações. Se está escolhendo horário, mostra os horários disponíveis consultados do Google Calendar.

O sistema também inclui informações contextuais, como valores de consultas quando relevante, ou lembretes sobre o que já foi escolhido para ajudar o usuário a manter o contexto da conversa.

**Formatação e Apresentação**

A resposta é formatada de forma clara e amigável, utilizando emojis moderadamente para tornar a comunicação mais próxima e fácil de ler. O sistema evita repetir informações já fornecidas e mantém um tom profissional mas acessível.

Em situações especiais, como quando um horário não está disponível, a resposta é formatada de forma clara para informar o problema e apresentar alternativas de forma organizada e fácil de entender.

---

#### ETAPA 6: ENVIO E FINALIZAÇÃO

A resposta gerada é enviada ao usuário e o processamento é finalizado.

**Envio via WhatsApp**

A resposta é enviada através da API do WhatsApp Business, que se encarrega de entregar a mensagem ao usuário no aplicativo WhatsApp. O sistema aguarda confirmação de que a mensagem foi enviada com sucesso.

**Registro e Logging**

O sistema registra todas as etapas do processamento em logs detalhados, incluindo a intenção identificada, as entidades extraídas, o estado da conversa, e a resposta gerada. Isso permite monitoramento, análise e depuração quando necessário.

O tempo total de processamento também é registrado, permitindo identificar gargalos e otimizar a performance do sistema. Em caso de erros, informações detalhadas são registradas para análise posterior.

**Finalização**

Após o envio bem-sucedido, o processamento é finalizado e o sistema aguarda a próxima mensagem do usuário. A sessão permanece ativa e todas as informações coletadas estão disponíveis para a próxima interação, permitindo que a conversa continue de forma natural e contextualizada.

---

### Sequência Detalhada: Da Mensagem à Resposta

```
┌─────────────────────────────────────────────────────────────────────┐
│ ETAPA 1: RECEPÇÃO DA MENSAGEM                                       │
└─────────────────────────────────────────────────────────────────────┘

📱 Paciente (WhatsApp)
   │
   │ Envia: "Olá, gostaria de agendar uma consulta"
   │
   ▼
🌐 WhatsApp Business API
   │
   │ POST https://seu-dominio.com/webhook/
   │ {
   │   "from": "5573988221003",
   │   "text": "Olá, gostaria de agendar uma consulta",
   │   "timestamp": "2024-10-09T14:30:00Z"
   │ }
   │
   ▼
📨 Django: api_gateway/views.py
   │
   │ def whatsapp_webhook(request):
   │     ├─ Valida verificação (GET)
   │     ├─ Processa mensagem (POST)
   │     └─ Chama process_message()
   │
   ▼


┌─────────────────────────────────────────────────────────────────────┐
│ ETAPA 2: PROCESSAMENTO INICIAL                                      │
└─────────────────────────────────────────────────────────────────────┘

📨 views.process_message(phone, message)
   │
   │ 1. Extrai dados do webhook
   │    ├─ phone_number: "5573988221003"
   │    ├─ message_text: "Olá, gostaria de agendar..."
   │    └─ timestamp: "2024-10-09T14:30:00Z"
   │
   │ 2. Chama GeminiChatbotService
   │
   ▼
🤖 gemini_chatbot_service.process_message()
   │
   │ Log: 🔍 Processando mensagem de 5573988221003
   │
   ▼


┌─────────────────────────────────────────────────────────────────────┐
│ ETAPA 3: ORQUESTRAÇÃO (GeminiChatbotService)                        │
└─────────────────────────────────────────────────────────────────────┘

🤖 GeminiChatbotService.process_message()
   │
   ├─ PASSO 1: Obter/Criar Sessão
   │  │
   │  ├─ session = session_manager.get_or_create_session(phone_number)
   │  │  │
   │  │  ├─ Busca em cache: gemini_session_5573988221003
   │  │  │
   │  │  ├─ Se não existe:
   │  │  │  └─ Busca no banco ou cria nova sessão:
   │  │  │     {
   │  │  │       'phone_number': '5573988221003',
   │  │  │       'current_state': 'idle',
   │  │  │       'patient_name': None,
   │  │  │       'selected_doctor': None,
   │  │  │       'preferred_date': None,
   │  │  │       'preferred_time': None
   │  │  │     }
   │  │  │
   │  │  └─ Salva em cache (15 min)
   │  │
   │  └─ Log: 📊 Estado atual da sessão: idle
   │
   ├─ PASSO 2: Verificar Agendamento Pausado (Sistema de Dúvidas)
   │  │
   │  ├─ if conversation_service.has_paused_appointment(phone_number):
   │  │  │
   │  │  ├─ Detecta palavras-chave: ['continuar', 'retomar', 'voltar']
   │  │  │
   │  │  ├─ Se detectado:
   │  │  │  └─ conversation_service.resume_appointment()
   │  │  │     ├─ Restaura estado anterior
   │  │  │     └─ Retorna resposta de retomada
   │  │  │
   │  │  └─ Log: ▶️ Sessão retomada
   │  │
   │  └─ (Neste caso: não há agendamento pausado)
   │
   ├─ PASSO 3: Obter Histórico e Dados da Clínica
   │  │
   │  ├─ conversation_history = session_manager.get_conversation_history()
   │  │  └─ Retorna últimas 10 mensagens do banco
   │  │
   │  ├─ clinic_data = _get_clinic_data_optimized()
   │  │  │
   │  │  ├─ Verifica cache: gemini_clinic_data
   │  │  │
   │  │  ├─ Se cache vazio:
   │  │  │  └─ RAGService obtém dados do banco
   │  │  │     └─ Salva em cache (15-60 min dinâmico)
   │  │  │
   │  │  └─ Se cache existe: retorna do cache
   │  │
   │  └─ Log: 📋 Dados da clínica obtidos (cache: sim/não)
   │
   ├─ PASSO 4: Detectar Intenção (IntentDetector)
   │  │
   │  ├─ intent_result = intent_detector.analyze_message(
   │  │      message, session, conversation_history, clinic_data
   │  │    )
   │  │  │
   │  │  ├─ Construir prompt de análise com Gemini AI
   │  │  │
   │  │  ├─ Enviar para Gemini API
   │  │  │
   │  │  └─ Retorna:
   │  │     {
   │  │       "intent": "agendar_consulta",
   │  │       "next_state": "collecting_patient_info",
   │  │       "confidence": 0.95,
   │  │       "reasoning": "..."
   │  │     }
   │  │
   │  └─ Log: 🔍 Intent detectado: agendar_consulta, Confiança: 0.95
   │
   ├─ PASSO 5: Extrair Entidades (EntityExtractor)
   │  │
   │  ├─ entities_result = entity_extractor.extract_entities(
   │  │      message, session, conversation_history, clinic_data
   │  │    )
   │  │  │
   │  │  ├─ Usa Gemini AI para extrair entidades
   │  │  │  - nome_paciente, medico, especialidade, data, horario
   │  │  │
   │  │  └─ Retorna: {'nome_paciente': None, 'medico': None, ...}
   │  │
   │  └─ Log: 📦 Entidades extraídas: {}
   │
   ├─ PASSO 6: Combinar Resultados
   │  │
   │  ├─ analysis_result = {
   │  │      'intent': intent_result['intent'],
   │  │      'next_state': intent_result['next_state'],
   │  │      'confidence': intent_result['confidence'],
   │  │      'entities': entities_result,
   │  │      'reasoning': intent_result.get('reasoning', ''),
   │  │      'raw_message': message
   │  │    }
   │  │
   │  └─ (Preparado para próximos passos)
   │
   ├─ PASSO 6.1: Fluxo Dedicado de Confirmação do Nome ⚠️ NOVO
   │  │
   │  ├─ manual_name_response = _handle_patient_name_flow(
   │  │      phone_number, session, message, analysis_result
   │  │    )
   │  │  │
   │  │  ├─ Verifica se nome já está confirmado
   │  │  │  └─ Se sim: retorna None (continua fluxo)
   │  │  │
   │  │  ├─ Se há pending_name:
   │  │  │  └─ Valida confirmação/rejeição do usuário
   │  │  │     ├─ Se confirmado: salva nome e avança estado
   │  │  │     └─ Se rejeitado: solicita nome novamente
   │  │  │
   │  │  ├─ Se não há nome e mensagem indica nome:
   │  │  │  └─ Extrai nome das entidades
   │  │  │     ├─ Salva em pending_name
   │  │  │     └─ Solicita confirmação
   │  │  │
   │  │  └─ Se retorna resposta: interrompe fluxo aqui
   │  │
   │  └─ (Neste caso: retorna None, continua fluxo)
   │
   ├─ PASSO 7: Detectar Dúvidas Durante Agendamento ⚠️ NOVO
   │  │
   │  ├─ if intent in ['buscar_info', 'duvida']:
   │  │  │
   │  │  ├─ Verifica se está em estado pausável:
   │  │  │  ['collecting_patient_info', 'selecting_specialty', 
   │  │  │   'selecting_doctor', 'choosing_schedule', 'confirming_name']
   │  │  │
   │  │  ├─ Se sim:
   │  │  │  └─ conversation_service.pause_for_question()
   │  │  │     ├─ Salva estado anterior
   │  │  │     ├─ Muda para 'answering_questions'
   │  │  │     └─ Permite responder dúvidas
   │  │  │
   │  │  └─ Log: ⏸️ Agendamento pausado para responder dúvida
   │  │
   │  └─ (Neste caso: não é dúvida)
   │
   ├─ PASSO 7.5: Verificar Disponibilidade (se aplicável) ⚠️ NOVO
   │  │
   │  ├─ Se usuário pergunta sobre horários disponíveis:
   │  │  └─ smart_scheduling_service.get_doctor_availability()
   │  │     ├─ Consulta Google Calendar
   │  │     └─ Retorna horários livres
   │  │
   │  └─ (Neste caso: não aplicável)
   │
   ├─ PASSO 8: Atualizar Sessão ANTES de Gerar Resposta ⚠️ ATUALIZADO
   │  │
   │  ├─ session_manager.update_session(
   │  │      phone_number, session, analysis_result, {'response': ''}
   │  │    )
   │  │  │
   │  │  ├─ Salva entidades extraídas na sessão
   │  │  ├─ Valida médico/especialidade no banco
   │  │  ├─ Corrige estado automaticamente se necessário
   │  │  └─ Sincroniza com banco de dados
   │  │
   │  └─ Log: ✅ Sessão atualizada
   │
   ├─ PASSO 8.1: Validar Data Inválida ⚠️ NOVO
   │  │
   │  ├─ if session.get('invalid_date_provided'):
   │  │  │
   │  │  └─ Retorna resposta solicitando data em formato numérico
   │  │
   │  └─ (Neste caso: não aplicável)
   │
   ├─ PASSO 8.5: Validar Horário Fornecido ⚠️ NOVO
   │  │
   │  ├─ Se usuário forneceu data E horário:
   │  │  └─ smart_scheduling_service.is_time_slot_available()
   │  │     ├─ Verifica disponibilidade no Google Calendar
   │  │     ├─ Se indisponível: sugere alternativas
   │  │     └─ Se disponível: continua fluxo
   │  │
   │  └─ (Neste caso: não aplicável)
   │
   ├─ PASSO 9: Verificar Confirmação e Gerar Handoff ⚠️ ATUALIZADO
   │  │
   │  ├─ if intent == 'confirmar_agendamento':
   │  │  │
   │  │  ├─ Verifica informações faltantes
   │  │  │
   │  │  ├─ Valida disponibilidade do horário específico
   │  │  │
   │  │  ├─ Se completo E horário disponível:
   │  │  │  └─ _handle_appointment_confirmation()
   │  │  │     ├─ Gera link de handoff
   │  │  │     ├─ Cria mensagem formatada
   │  │  │     └─ Muda estado para 'confirming'
   │  │  │
   │  │  └─ Se já confirmado anteriormente:
   │  │     └─ Retorna resumo sem gerar novo handoff
   │  │
   │  └─ (Neste caso: não é confirmação)
   │
   ├─ PASSO 9.5: Obter Missing Info (se necessário) ⚠️ NOVO
   │  │
   │  ├─ if current_state == 'collecting_patient_info':
   │  │  │
   │  │  └─ missing_info = conversation_service.get_missing_appointment_info()
   │  │     └─ Adiciona ao analysis_result para ResponseGenerator
   │  │
   │  └─ (Neste caso: aplicável)
   │
   ├─ PASSO 10: Gerar Resposta (ResponseGenerator)
   │  │
   │  ├─ if not response_result.get('response'):
   │  │  │
   │  │  ├─ response_result = response_generator.generate_response(
   │  │  │      message, analysis_result, session, 
   │  │  │      conversation_history, clinic_data
   │  │  │    )
   │  │  │  │
   │  │  │  ├─ Construir prompt contextualizado
   │  │  │  ├─ Enviar para Gemini AI
   │  │  │  └─ Retorna resposta formatada
   │  │  │
   │  │  ├─ Verificação final: interceptar se Gemini perguntou
   │  │  │    data/horário sem especialidade/médico ⚠️ NOVO
   │  │  │
   │  │  └─ Atualizar sessão com resposta final
   │  │
   │  └─ Log: 💬 Resposta gerada
   │
   ├─ PASSO 10.5: Retomada Automática (se aplicável) ⚠️ NOVO
   │  │
   │  ├─ if current_state == 'answering_questions':
   │  │  │
   │  │  ├─ Verifica se usuário forneceu entidades de agendamento
   │  │  │
   │  │  ├─ Se sim:
   │  │  │  └─ Restaura estado anterior automaticamente
   │  │  │     └─ Log: 🔄 Retomada automática do agendamento
   │  │
   │  └─ (Neste caso: não aplicável)
   │
   ├─ PASSO 11: Salvar Mensagens no Banco
   │  │
   │  ├─ session_manager.save_messages(
   │  │      phone_number, message, response, analysis_result
   │  │    )
   │  │  │
   │  │  ├─ Salva mensagem do usuário
   │  │  └─ Salva resposta do bot
   │  │
   │  └─ Log: 💾 Mensagens salvas
   │
   └─ PASSO 12: Retornar Resultado
      │
      └─ return {
           'response': "Olá! 😊 Fico feliz em ajudar...",
           'intent': 'agendar_consulta',
           'confidence': 0.95
         }


┌─────────────────────────────────────────────────────────────────────┐
│ ETAPA 4: ENVIO DA RESPOSTA                                          │
└─────────────────────────────────────────────────────────────────────┘

📨 views.process_message()
   │
   ├─ Recebe resultado do GeminiChatbotService
   │
   ├─ whatsapp_service.send_message(
   │    phone_number="5573988221003",
   │    message="Olá! 😊 Fico feliz em ajudar..."
   │  )
   │  │
   │  ├─ POST https://graph.facebook.com/v17.0/.../messages
   │  │  {
   │  │    "messaging_product": "whatsapp",
   │  │    "to": "5573988221003",
   │  │    "text": {
   │  │      "body": "Olá! 😊 Fico feliz em ajudar..."
   │  │    }
   │  │  }
   │  │
   │  └─ Log: ✅ Mensagem enviada para WhatsApp
   │
   ├─ return JsonResponse({'success': True})
   │
   └─ Log: 🎯 Processamento completo - 2.3s
```

---

## 🎬 Fluxo de Agendamento Visual (Exemplo Completo)

### Conversa Passo a Passo com Estados e Banco de Dados

```
┌─────────────────────────────────────────────────────────────────────┐
│ MENSAGEM 1: SAUDAÇÃO E SOLICITAÇÃO                                  │
└─────────────────────────────────────────────────────────────────────┘

👤 PACIENTE: "Olá, gostaria de agendar uma consulta"

┌──────────────────────────────────────┐
│ PROCESSAMENTO                         │
├──────────────────────────────────────┤
│ IntentDetector:                      │
│ ├─ Intent: agendar_consulta         │
│ ├─ Confidence: 0.95                 │
│ └─ Next State: collecting_patient_info│
│                                      │
│ EntityExtractor:                     │
│ └─ Entidades: {}                    │
│                                      │
│ _handle_patient_name_flow():        │
│ └─ Retorna: None (não há nome ainda)│
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ BANCO DE DADOS                        │
├──────────────────────────────────────┤
│ ConversationSession #1:              │
│ ├─ phone: 5573988221003              │
│ ├─ current_state: collecting_patient_info│
│ ├─ patient_name: null                │
│ ├─ name_confirmed: false             │
│ ├─ pending_name: null                │
│ ├─ selected_doctor: null             │
│ ├─ selected_specialty: null          │
│ ├─ preferred_date: null              │
│ └─ preferred_time: null             │
│                                      │
│ ConversationMessage #1:              │
│ ├─ type: user                        │
│ ├─ content: "Olá, gostaria..."       │
│ ├─ intent: agendar_consulta          │
│ └─ entities: {}                      │
│                                      │
│ ConversationMessage #2:              │
│ ├─ type: bot                         │
│ └─ content: "Olá! 😊 Fico feliz..."  │
└──────────────────────────────────────┘

🤖 BOT: "Olá! 😊 Fico feliz em ajudar com seu agendamento.
        Para começar, qual é o seu nome completo?"

═══════════════════════════════════════════════════════════════════════


┌─────────────────────────────────────────────────────────────────────┐
│ MENSAGEM 2: FORNECIMENTO DO NOME                                    │
└─────────────────────────────────────────────────────────────────────┘

👤 PACIENTE: "Meu nome é João Silva Santos"

┌──────────────────────────────────────┐
│ PROCESSAMENTO                         │
├──────────────────────────────────────┤
│ IntentDetector:                      │
│ └─ Intent: agendar_consulta          │
│                                      │
│ EntityExtractor:                     │
│ ├─ Usa Gemini AI para extrair        │
│ └─ Entidades: {                      │
│      nome_paciente: "João Silva Santos"│
│    }                                 │
│                                      │
│ _handle_patient_name_flow():        │
│ ├─ Detecta: expecting_name = True   │
│ ├─ Extrai nome das entidades         │
│ ├─ Salva em: pending_name            │
│ ├─ Sincroniza com banco              │
│ └─ Retorna resposta de confirmação   │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ FLUXO DE NOME (Interceptado)         │
├──────────────────────────────────────┤
│ ⚠️ IMPORTANTE: Fluxo interceptado     │
│    antes de gerar resposta com Gemini│
│                                      │
│ 1. Nome extraído: "João Silva Santos"│
│ 2. Salvo em: session['pending_name'] │
│ 3. Estado: confirming_name           │
│ 4. Resposta gerada manualmente       │
│    (economiza tokens)                │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ BANCO DE DADOS (Atualizado)          │
├──────────────────────────────────────┤
│ ConversationSession #1:              │
│ ├─ current_state: confirming_name    │
│ ├─ pending_name: "João Silva Santos" │← Aguardando confirmação
│ ├─ patient_name: null                │
│ ├─ name_confirmed: false             │
│ └─ ...                               │
│                                      │
│ ConversationMessage #3:              │
│ ├─ type: user                        │
│ ├─ content: "Meu nome é João..."     │
│ ├─ entities: {                       │
│ │    nome_paciente: "João Silva..."  │
│ │  }                                 │
└──────────────────────────────────────┘

🤖 BOT: "Entendi. Confirma se seu nome completo é João Silva Santos? 
        Se estiver correto, responda com 'sim'. Caso contrário, 
        digite novamente seu nome completo."

═══════════════════════════════════════════════════════════════════════


┌─────────────────────────────────────────────────────────────────────┐
│ MENSAGEM 3: CONFIRMAÇÃO DO NOME                                     │
└─────────────────────────────────────────────────────────────────────┘

👤 PACIENTE: "Sim"

┌──────────────────────────────────────┐
│ PROCESSAMENTO                         │
├──────────────────────────────────────┤
│ IntentDetector:                      │
│ └─ Intent: confirmar_agendamento    │
│                                      │
│ EntityExtractor:                     │
│ └─ Entidades: {}                    │
│                                      │
│ _handle_patient_name_flow():        │
│ ├─ Detecta: pending_name existe     │
│ ├─ Chama: confirm_patient_name()    │
│ ├─ Status: 'confirmed'              │
│ ├─ Salva: patient_name              │
│ ├─ Limpa: pending_name              │
│ ├─ Define: name_confirmed = True    │
│ ├─ Determina próximo estado         │
│ └─ Retorna resposta com follow-up   │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ LÓGICA DE CONFIRMAÇÃO                │
├──────────────────────────────────────┤
│ conversation_service.confirm_patient_ │
│   name():                            │
│                                      │
│ 1. Verifica pending_name existe      │
│ 2. Detecta palavras: ["sim", "s",    │
│    "yes", "confirmo", "correto"]     │
│ 3. Salva: patient_name = pending_name│
│ 4. Limpa: pending_name = None        │
│ 5. Define: name_confirmed = True     │
│ 6. Retorna: status = 'confirmed'     │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ DETERMINAÇÃO DO PRÓXIMO ESTADO       │
├──────────────────────────────────────┤
│ get_missing_appointment_info():     │
│ └─ next_action: 'ask_specialty'     │
│                                      │
│ Mapeamento:                          │
│ ask_specialty → selecting_specialty │
│                                      │
│ _build_follow_up_after_name():      │
│ └─ "Para continuarmos, qual         │
│     especialidade você deseja..."    │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ BANCO DE DADOS (Atualizado)          │
├──────────────────────────────────────┤
│ ConversationSession #1:              │
│ ├─ current_state: selecting_specialty│
│ ├─ patient_name: "João Silva Santos" │← CONFIRMADO!
│ ├─ pending_name: null                │← Limpo
│ ├─ name_confirmed: true              │← Flag ativada
│ └─ ...                               │
└──────────────────────────────────────┘

🤖 BOT: "Perfeito, João Silva Santos! Para continuarmos, qual 
        especialidade você deseja consultar?"

═══════════════════════════════════════════════════════════════════════


┌─────────────────────────────────────────────────────────────────────┐
│ MENSAGEM 4: SELEÇÃO DE ESPECIALIDADE                                │
└─────────────────────────────────────────────────────────────────────┘

👤 PACIENTE: "Pneumologia"

┌──────────────────────────────────────┐
│ PROCESSAMENTO                         │
├──────────────────────────────────────┤
│ IntentDetector:                      │
│ └─ Intent: agendar_consulta          │
│                                      │
│ EntityExtractor:                     │
│ ├─ Extrai: especialidade = "Pneumologia"│
│ ├─ Valida no banco de dados          │
│ └─ Entidades: {                      │
│      especialidade: "Pneumologia"    │
│    }                                 │
│                                      │
│ SessionManager.update_session():     │
│ ├─ Valida especialidade no banco     │
│ ├─ Salva: selected_specialty         │
│ ├─ Corrige estado automaticamente    │
│ └─ Sincroniza com banco              │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ VALIDAÇÃO DE ESPECIALIDADE           │
├──────────────────────────────────────┤
│ EntityExtractor._validate_specialty():│
│                                      │
│ 1. Query: Especialidade.objects.    │
│    filter(nome__icontains="pneumo") │
│                                      │
│ 2. Resultado: ✓ Encontrada          │
│    {                                 │
│      id: 2,                          │
│      nome: "Pneumologia",            │
│      ativa: true                     │
│    }                                 │
│                                      │
│ 3. Busca médicos da especialidade    │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ CORREÇÃO AUTOMÁTICA DE ESTADO        │
├──────────────────────────────────────┤
│ SessionManager (linha 357):          │
│                                      │
│ Se tem especialidade mas não médico: │
│ └─ Estado: selecting_doctor           │
│                                      │
│ ✅ Estado corrigido automaticamente   │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ BANCO DE DADOS (Atualizado)          │
├──────────────────────────────────────┤
│ ConversationSession #1:              │
│ ├─ current_state: selecting_doctor   │
│ ├─ patient_name: "João Silva Santos" │
│ ├─ selected_specialty: "Pneumologia" │← ATUALIZADO!
│ ├─ name_confirmed: true              │
│ └─ ...                               │
└──────────────────────────────────────┘

🤖 BOT: "Perfeito! 🫁 Pneumologia
        
        Agora, com qual médico você gostaria de agendar?
        
        Médicos de Pneumologia:
        👨‍⚕️ Dr. Gustavo - Medicina do Sono, Pneumologia
        💰 Consulta particular: R$ 150,00
        
        Qual médico você prefere?"

═══════════════════════════════════════════════════════════════════════


┌─────────────────────────────────────────────────────────────────────┐
│ MENSAGEM 5: SELEÇÃO DO MÉDICO                                       │
└─────────────────────────────────────────────────────────────────────┘

👤 PACIENTE: "Dr. Gustavo"

┌──────────────────────────────────────┐
│ PROCESSAMENTO                         │
├──────────────────────────────────────┤
│ IntentDetector:                      │
│ └─ Intent: agendar_consulta          │
│                                      │
│ EntityExtractor:                     │
│ ├─ Extrai: medico = "Dr. Gustavo"    │
│ ├─ Valida no banco de dados          │
│ └─ Entidades: {                      │
│      medico: "Dr. Gustavo"           │
│    }                                 │
│                                      │
│ SessionManager.update_session():     │
│ ├─ Valida médico no banco            │
│ ├─ Salva: selected_doctor            │
│ ├─ Corrige estado automaticamente   │
│ └─ Sincroniza com banco              │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ VALIDAÇÃO DE MÉDICO                  │
├──────────────────────────────────────┤
│ SessionManager._validate_doctor():   │
│                                      │
│ 1. Query: Medico.objects.filter(     │
│    nome__icontains="gustavo")       │
│                                      │
│ 2. Verifica especialidade compatível │
│                                      │
│ 3. Resultado: ✓ Médico encontrado    │
│    {                                 │
│      id: 1,                          │
│      nome: "Dr. Gustavo",            │
│      especialidades: ["Medicina do   │
│        Sono", "Pneumologia"]         │
│    }                                 │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ CONSULTA GOOGLE CALENDAR              │
├──────────────────────────────────────┤
│ SmartSchedulingService:              │
│ └─ get_doctor_availability():       │
│    ├─ Consulta Google Calendar API  │
│    ├─ Filtra eventos do médico       │
│    └─ Calcula horários livres        │
│                                      │
│ Resultado:                           │
│ {                                    │
│   "days": [                          │
│     {                                │
│       "date": "14/10/2024",          │
│       "weekday": "Segunda-feira",    │
│       "available_times": [           │
│         "08:00", "09:00", "10:00",   │
│         "14:00", "15:00", "16:00"    │
│       ]                              │
│     }                                │
│   ]                                  │
│ }                                    │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ CORREÇÃO AUTOMÁTICA DE ESTADO        │
├──────────────────────────────────────┤
│ SessionManager (linha 367):          │
│                                      │
│ Se tem médico E especialidade:      │
│ └─ Estado: choosing_schedule          │
│                                      │
│ ✅ Estado avançado automaticamente   │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ BANCO DE DADOS (Atualizado)          │
├──────────────────────────────────────┤
│ ConversationSession #1:              │
│ ├─ current_state: choosing_schedule   │
│ ├─ patient_name: "João Silva Santos" │
│ ├─ selected_specialty: "Pneumologia" │
│ ├─ selected_doctor: "Dr. Gustavo"    │← ATUALIZADO!
│ └─ ...                               │
└──────────────────────────────────────┘

🤖 BOT: "Excelente escolha! 👨‍⚕️
        
        Dr. Gustavo
        🩺 Medicina do Sono, Pneumologia
        💰 Consulta particular: R$ 150,00
        
        📅 Horários disponíveis:
        
        Segunda-feira (14/10/2024):
        ✅ 08:00, 09:00, 10:00, 14:00, 15:00, 16:00
        
        Quarta-feira (16/10/2024):
        ✅ 08:00, 09:00, 14:00
        
        Qual data e horário seria melhor para você?"

═══════════════════════════════════════════════════════════════════════


┌─────────────────────────────────────────────────────────────────────┐
│ MENSAGEM 6: FORNECIMENTO DE DATA E HORÁRIO                          │
└─────────────────────────────────────────────────────────────────────┘

👤 PACIENTE: "14 de outubro às 14 horas"

┌──────────────────────────────────────┐
│ PROCESSAMENTO                         │
├──────────────────────────────────────┤
│ IntentDetector:                      │
│ └─ Intent: agendar_consulta          │
│                                      │
│ EntityExtractor:                     │
│ ├─ Extrai: data = "2024-10-14"      │
│ ├─ Extrai: horario = "14:00"         │
│ └─ Entidades: {                      │
│      data: "2024-10-14",             │
│      horario: "14:00"                │
│    }                                 │
│                                      │
│ ⚠️ VALIDAÇÃO IMEDIATA DE HORÁRIO     │
│ (linha 380-492):                     │
│ ├─ Verifica disponibilidade          │
│ ├─ Se indisponível: sugere alternativas│
│ └─ Se disponível: salva na sessão   │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ VALIDAÇÃO DE HORÁRIO (Antecipada)    │
├──────────────────────────────────────┤
│ SmartSchedulingService:              │
│ └─ is_time_slot_available():        │
│    ├─ Consulta Google Calendar        │
│    ├─ Verifica se horário está livre │
│    └─ Retorna:                       │
│       {                              │
│         available: true,             │
│         date_formatted: "14/10/2024",│
│         time_formatted: "14:00"      │
│       }                              │
│                                      │
│ ✅ Horário disponível!               │
│ Salva na sessão                       │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ BANCO DE DADOS (Atualizado)          │
├──────────────────────────────────────┤
│ ConversationSession #1:              │
│ ├─ current_state: choosing_schedule   │
│ ├─ patient_name: "João Silva Santos" │
│ ├─ selected_specialty: "Pneumologia" │
│ ├─ selected_doctor: "Dr. Gustavo"    │
│ ├─ preferred_date: 2024-10-14        │← ATUALIZADO!
│ ├─ preferred_time: 14:00:00          │← ATUALIZADO!
│ └─ ...                               │
└──────────────────────────────────────┘

🤖 BOT: "Perfeito! Agendamento para Segunda-feira, 14/10/2024 às 14:00 
        com o Dr. Gustavo.
        
        Deseja confirmar este agendamento? (Sim/Não)"

═══════════════════════════════════════════════════════════════════════


┌─────────────────────────────────────────────────────────────────────┐
│ MENSAGEM 7: CONFIRMAÇÃO FINAL E HANDOFF                             │
└─────────────────────────────────────────────────────────────────────┘

👤 PACIENTE: "Sim, está correto"

┌──────────────────────────────────────┐
│ PROCESSAMENTO                         │
├──────────────────────────────────────┤
│ IntentDetector:                      │
│ └─ Intent: confirmar_agendamento     │← GATILHO!
│                                      │
│ EntityExtractor:                     │
│ └─ Entidades: {}                    │
│                                      │
│ ⚠️ VERIFICAÇÕES ANTES DO HANDOFF:    │
│ ├─ 1. Verifica informações faltantes│
│ ├─ 2. Valida horário novamente      │
│ ├─ 3. Verifica se já foi confirmado │
│ └─ 4. Gera handoff (se primeira vez)│
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ VALIDAÇÃO DE INFORMAÇÕES              │
├──────────────────────────────────────┤
│ conversation_service.get_missing_    │
│   appointment_info():                │
│                                      │
│ Verificando campos obrigatórios:     │
│ ✓ patient_name: "João Silva Santos" │
│ ✓ selected_doctor: "Dr. Gustavo"     │
│ ✓ selected_specialty: "Pneumologia"  │
│ ✓ preferred_date: 2024-10-14        │
│ ✓ preferred_time: 14:00:00          │
│                                      │
│ Resultado:                           │
│ {                                    │
│   is_complete: true,                 │
│   missing_info: []                   │
│ }                                    │
│                                      │
│ ✅ TODAS INFORMAÇÕES PRESENTES!      │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ VALIDAÇÃO FINAL DE HORÁRIO           │
├──────────────────────────────────────┤
│ SmartSchedulingService:              │
│ └─ is_time_slot_available():        │
│    ├─ Verifica disponibilidade      │
│    └─ Resultado: available = true   │
│                                      │
│ ✅ Horário ainda disponível!         │
│ Prosseguir com handoff...            │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ VERIFICAÇÃO DE CONFIRMAÇÃO DUPLICADA │
├──────────────────────────────────────┤
│ Se current_state == 'confirming':    │
│ └─ ⚠️ Já foi confirmado anteriormente│
│    └─ Retorna resumo sem gerar      │
│       novo handoff                   │
│                                      │
│ Se current_state != 'confirming':    │
│ └─ ✅ Primeira confirmação           │
│    └─ Gera handoff                   │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ GERAÇÃO DE HANDOFF                   │
├──────────────────────────────────────┤
│ handoff_service.generate_appointment_│
│   handoff_link():                    │
│                                      │
│ 1. Coletar informações:              │
│    ├─ patient: "João Silva Santos"   │
│    ├─ doctor: "Dr. Gustavo"          │
│    ├─ specialty: "Pneumologia"       │
│    ├─ date: "14/10/2024"             │
│    └─ time: "14:00"                  │
│                                      │
│ 2. Criar mensagem formatada:         │
│    base_message = """                │
│    Olá, gostaria de confirmar meu    │
│    pré-agendamento:                  │
│                                      │
│    👤 Paciente: João Silva Santos    │
│    👨‍⚕️ Médico: Dr. Gustavo          │
│    📅 Data: 14/10/2024               │
│    🕐 Horário: 14:00                 │
│    """                               │
│                                      │
│ 3. URL encode e gerar link:          │
│    link = "https://wa.me/            │
│      5573988221003?text=..."         │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ BANCO DE DADOS (Final)               │
├──────────────────────────────────────┤
│ ConversationSession #1:              │
│ ├─ current_state: confirming         │← Mudado após handoff
│ ├─ patient_name: "João Silva Santos" │
│ ├─ name_confirmed: true              │
│ ├─ selected_doctor: "Dr. Gustavo"    │
│ ├─ selected_specialty: "Pneumologia" │
│ ├─ preferred_date: 2024-10-14        │
│ ├─ preferred_time: 14:00:00          │
│ ├─ handoff_link: "https://wa.me/..." │
│ ├─ created_at: 2024-10-09 14:30      │
│ ├─ updated_at: 2024-10-09 14:45      │
│ └─ last_activity: 2024-10-09 14:45   │
│                                      │
│ Total Mensagens: 14                  │
│ (7 do usuário + 7 do bot)            │
└──────────────────────────────────────┘

🤖 BOT: "✅ Perfeito! Vamos confirmar seu pré-agendamento:

        📋 RESUMO:
        👤 Paciente: João Silva Santos
        👨‍⚕️ Médico: Dr. Gustavo
        🩺 Especialidade: Pneumologia
        📅 Data: Segunda-feira, 14/10/2024
        🕐 Horário: 14:00
        
        🔄 Para CONFIRMAR definitivamente:
        👩‍💼 Nossa secretária validará a disponibilidade e 
        confirmará seu agendamento.
        
        📞 Clique no link abaixo para falar diretamente com 
        nossa equipe:
        https://wa.me/5573988221003?text=Ol%C3%A1%2C%20gostaria..."

═══════════════════════════════════════════════════════════════════════


┌─────────────────────────────────────────────────────────────────────┐
│ RESULTADO FINAL: PACIENTE CLICA NO LINK                             │
└─────────────────────────────────────────────────────────────────────┘

📱 Paciente clica no link de handoff

   ↓

🌐 WhatsApp abre conversa com secretária

   ↓

👩‍💼 Secretária recebe mensagem pré-formatada:

"Olá, gostaria de confirmar meu pré-agendamento:

👤 Paciente: João Silva Santos
👨‍⚕️ Médico: Dr. Gustavo
🩺 Especialidade: Pneumologia
📅 Data: 14/10/2024
🕐 Horário: 14:00"

   ↓

✅ Secretária valida disponibilidade no sistema

   ↓

✅ Secretária confirma agendamento com paciente

   ↓

📅 Agendamento inserido no Google Calendar

═══════════════════════════════════════════════════════════════════════

NOTAS IMPORTANTES SOBRE O FLUXO ATUALIZADO:
═══════════════════════════════════════════════════════════════════════

1. ⚠️ FLUXO DE NOME INTERCEPTADO:
   - _handle_patient_name_flow() intercepta antes do ResponseGenerator
   - Economiza tokens do Gemini
   - Garante confirmação do nome antes de continuar

2. ✅ CORREÇÃO AUTOMÁTICA DE ESTADO:
   - SessionManager corrige estado automaticamente
   - Baseado nas informações coletadas
   - Garante ordem correta: nome → especialidade → médico → data/horário

3. 🔍 VALIDAÇÃO ANTECIPADA DE HORÁRIO:
   - Valida horário assim que fornecido (não espera confirmação)
   - Se indisponível: sugere alternativas imediatamente
   - Evita confirmar horário que não está disponível

4. 🛡️ VALIDAÇÃO DUPLA NA CONFIRMAÇÃO:
   - Valida horário novamente antes de gerar handoff
   - Verifica se já foi confirmado anteriormente
   - Evita gerar handoff duplicado

5. 📊 PERSISTÊNCIA COMPLETA:
   - Todas as informações salvas no banco
   - Sincronização cache + banco
   - Histórico completo de mensagens

═══════════════════════════════════════════════════════════════════════
```

---

## 📊 Persistência e Sincronização

### Diagrama de Sincronização Cache + Banco de Dados

```
┌──────────────────────────────────────────────────────────────────────┐
│ ESTRATÉGIA DE PERSISTÊNCIA DUAL                                      │
└──────────────────────────────────────────────────────────────────────┘

┌─────────────────────────┐         ┌─────────────────────────┐
│   💨 CACHE (Django)     │◄───────►│   💾 BANCO DE DADOS     │
│   django.core.cache     │  Sync   │   SQLite3               │
├─────────────────────────┤         ├─────────────────────────┤
│                         │         │                         │
│ Chave: gemini_session_  │         │ ConversationSession:    │
│        5573988221003    │         │ ├─ id: 1                │
│                         │         │ ├─ phone: 5573988221003 │
│ Valor: {                │         │ ├─ patient_name: "João" │
│   phone: "557398...",   │         │ ├─ selected_doctor: ... │
│   current_state: "...", │         │ ├─ preferred_date: ...  │
│   patient_name: "...",  │         │ ├─ preferred_time: ...  │
│   ...                   │         │ └─ ...                  │
│ }                       │         │                         │
│                         │         │ ConversationMessage:    │
│ Timeout: 15-60 min      │         │ ├─ id: 1-12             │
│ (Baseado em uso tokens) │         │ ├─ session_id: 1        │
│                         │         │ ├─ message_type: ...    │
│ Chave: gemini_clinic_   │         │ ├─ content: ...         │
│        data             │         │ └─ ...                  │
│                         │         │                         │
│ Valor: {                │         │ Persistente             │
│   clinica_info: {...},  │         │ Histórico completo      │
│   medicos: [...],       │         │ Auditoria               │
│   ...                   │         │                         │
│ }                       │         │                         │
│                         │         │                         │
│ Timeout: 15-60 min      │         │                         │
│ (Baseado em uso tokens) │         │                         │
│                         │         │                         │
│ Chave: gemini_tokens_   │         │                         │
│        2024-10-09       │         │                         │
│                         │         │                         │
│ Valor: 125678           │         │                         │
│ (Total tokens usado)    │         │                         │
│                         │         │                         │
│ Timeout: 24h            │         │                         │
└─────────────────────────┘         └─────────────────────────┘

       ⬆️                                    ⬆️
       │                                     │
       │                                     │
┌──────┴──────────┐              ┌──────────┴──────┐
│  LEITURA RÁPIDA │              │ PERSISTÊNCIA     │
│  - Sessions     │              │ - Histórico      │
│  - Clinic Data  │              │ - Auditoria      │
│  - Tokens       │              │ - Backup         │
└─────────────────┘              └──────────────────┘


FLUXO DE ATUALIZAÇÃO:
═══════════════════════════════════════════════════════════════════════

1️⃣ Nova Mensagem Chega
   ↓
2️⃣ Buscar Sessão:
   ├─ Primeiro: Tenta cache ← RÁPIDO (ms)
   └─ Se não existe: Busca banco → Cache ← LENTO (50ms)
   ↓
3️⃣ Processar com Gemini
   ↓
4️⃣ Atualizar Sessão:
   ├─ Atualiza cache ← INSTANTÂNEO
   └─ Sincroniza banco ← ASSÍNCRONO
   ↓
5️⃣ Salvar Mensagens:
   └─ Grava banco diretamente ← PERSISTENTE

BENEFÍCIOS:
═══════════════════════════════════════════════════════════════════════
✅ Performance: Cache primeiro (< 1ms)
✅ Persistência: Banco sempre sincronizado
✅ Recuperação: Se cache limpo, reconstrói do banco
✅ Escalabilidade: Cache compartilhado (Redis futuro)
✅ Auditoria: Histórico completo no banco
```

---

## 📈 Monitoramento e Logs

### Sistema de Logs Estruturados

```
┌──────────────────────────────────────────────────────────────────────┐
│ EXEMPLO DE LOGS EM PRODUÇÃO (Processamento de 1 Mensagem)           │
└──────────────────────────────────────────────────────────────────────┘

[2024-10-09 14:30:15] INFO 📱 Webhook recebido de 5573988221003
[2024-10-09 14:30:15] DEBUG 🔍 Mensagem: "Olá, gostaria de agendar uma consulta"
[2024-10-09 14:30:15] INFO 🤖 Iniciando processamento com GeminiChatbotService

[2024-10-09 14:30:15] INFO ✅ Sessão obtida - Estado: idle, Nome: None
[2024-10-09 14:30:15] DEBUG 📋 Dados da clínica obtidos (cache: não)
[2024-10-09 14:30:15] DEBUG 📜 Histórico obtido: 0 mensagens

[2024-10-09 14:30:16] INFO 🔍 Análise de intenção iniciada
[2024-10-09 14:30:16] INFO 📊 TOKENS - ANÁLISE: Input=1,245, Output=156, Total=1,401
[2024-10-09 14:30:16] INFO 📊 SESSÃO 5573988221003: Total=1,401, Acumulado=1,401
[2024-10-09 14:30:16] INFO 📊 DIA: Total=125,678, Limite=1,500,000, Uso=8.4%
[2024-10-09 14:30:16] INFO 🔍 Intenção detectada: agendar_consulta (0.95)

[2024-10-09 14:30:17] INFO 💬 Geração de resposta iniciada
[2024-10-09 14:30:18] INFO 📊 TOKENS - RESPOSTA: Input=2,134, Output=287, Total=2,421
[2024-10-09 14:30:18] INFO 📊 SESSÃO 5573988221003: Total=2,421, Acumulado=3,822
[2024-10-09 14:30:18] INFO 📊 DIA: Total=128,099, Limite=1,500,000, Uso=8.5%

[2024-10-09 14:30:18] INFO ✅ Sessão atualizada - Estado: collecting_patient_info
[2024-10-09 14:30:18] INFO 💾 Sessão sincronizada com banco - ID: 1
[2024-10-09 14:30:18] INFO 💾 Mensagem usuário salva - ID: 1
[2024-10-09 14:30:18] INFO 💾 Mensagem bot salva - ID: 2

[2024-10-09 14:30:19] INFO ✅ Mensagem enviada para WhatsApp
[2024-10-09 14:30:19] INFO 🎯 Processamento completo em 3.2s

═══════════════════════════════════════════════════════════════════════

LOGS DE MONITORAMENTO DE TOKENS:
═══════════════════════════════════════════════════════════════════════

[2024-10-09 08:00:00] INFO 📊 Tokens hoje: 0 / 1,500,000 (0.0%)
[2024-10-09 12:30:45] INFO 📊 Tokens hoje: 654,321 / 1,500,000 (43.6%)
[2024-10-09 18:45:12] WARNING ⚠️ AVISO: Uso de tokens em 82.3% do limite diário
[2024-10-09 21:30:00] ERROR ⚠️ ALERTA: Uso de tokens em 91.5% do limite diário
[2024-10-09 23:15:30] CRITICAL 🚨 CRÍTICO: Uso de tokens em 96.1%!
[2024-10-09 23:15:30] WARNING 🔄 Ativando modo econômico
[2024-10-09 23:15:30] INFO ✅ Modo econômico ativado - tokens preservados

═══════════════════════════════════════════════════════════════════════

LOGS DE ERRO (Exemplos):
═══════════════════════════════════════════════════════════════════════

[2024-10-09 14:30:20] ERROR ❌ Gemini API error: Rate limit exceeded
[2024-10-09 14:30:20] INFO 🔄 Tentando novamente em 5s... (tentativa 1/3)

[2024-10-09 14:30:25] ERROR ❌ Erro ao consultar Google Calendar: 503
[2024-10-09 14:30:25] WARNING ⚠️ Retornando horários do cache

[2024-10-09 14:30:30] ERROR ❌ Banco de dados não acessível
[2024-10-09 14:30:30] INFO 💾 Sessão mantida apenas em cache

═══════════════════════════════════════════════════════════════════════
```

---

## 🔧 Configuração e Deploy

### Arquivo .env (Template)

```bash
# ═══════════════════════════════════════════════════════════════════
# IMPORTANTE: Este arquivo contém informações sensíveis
# - NÃO commitar no git
# - Usar valores diferentes em dev/produção
# - Rotacionar chaves periodicamente
# ═══════════════════════════════════════════════════════════════════

# ───────────────────────────────────────────────────────────────────
# GEMINI AI (Google)
# ───────────────────────────────────────────────────────────────────
GEMINI_API_KEY=AIzaSy...  # Obter em https://makersuite.google.com/app/apikey
GEMINI_MODEL=gemini-2.0-flash
GEMINI_ENABLED=True
GEMINI_TOKEN_MONITORING=True
GEMINI_DAILY_TOKEN_LIMIT=1500000

# ───────────────────────────────────────────────────────────────────
# WHATSAPP BUSINESS API (Meta)
# ───────────────────────────────────────────────────────────────────
WHATSAPP_ACCESS_TOKEN=EAAJZBp...  # Token de acesso do app
WHATSAPP_PHONE_NUMBER_ID=123456789  # ID do número de telefone
WHATSAPP_VERIFY_TOKEN=meu_token_secreto_123  # Token personalizado
WHATSAPP_API_URL=https://graph.facebook.com/v17.0

# ───────────────────────────────────────────────────────────────────
# GOOGLE CALENDAR API
# ───────────────────────────────────────────────────────────────────
GOOGLE_CALENDAR_ENABLED=True
GOOGLE_SERVICE_ACCOUNT_FILE=service-account-key.json
CLINIC_CALENDAR_ID=primary

# ───────────────────────────────────────────────────────────────────
# CLÍNICA (Dados de Negócio)
# ───────────────────────────────────────────────────────────────────
CLINIC_NAME=Clínica PneumoSono
CLINIC_DOMAIN=https://clinica.exemplo.com
CLINIC_WHATSAPP_NUMBER=5573988221003  # Número da secretária

# ───────────────────────────────────────────────────────────────────
# DJANGO (Configurações Gerais)
# ───────────────────────────────────────────────────────────────────
DEBUG=False  # NUNCA True em produção!
SECRET_KEY=django-insecure-...  # Gerar com: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
ALLOWED_HOSTS=localhost,127.0.0.1,seu-dominio.com

# ───────────────────────────────────────────────────────────────────
# BANCO DE DADOS
# ───────────────────────────────────────────────────────────────────
DATABASE_URL=sqlite:///db.sqlite3  # Prod: postgresql://user:pass@host:port/db

# ───────────────────────────────────────────────────────────────────
# CACHE (Opcional - usar Redis em produção)
# ───────────────────────────────────────────────────────────────────
REDIS_URL=redis://localhost:6379/0  # Se usar Redis
```

### Processo de Deploy Completo

```
┌──────────────────────────────────────────────────────────────────────┐
│ DEPLOY PASSO A PASSO                                                 │
└──────────────────────────────────────────────────────────────────────┘

ETAPA 1: PREPARAÇÃO DO AMBIENTE
═══════════════════════════════════════════════════════════════════════

$ git clone https://github.com/seu-usuario/chatbot_ClinicaMedica.git
$ cd chatbot_ClinicaMedica

$ python -m venv venv
$ source venv/bin/activate  # Linux/Mac
$ venv\Scripts\activate     # Windows

$ pip install -r requirements.txt

Dependências instaladas:
✓ Django==5.0
✓ djangorestframework==3.14.0
✓ google-generativeai==0.3.0
✓ google-auth==2.25.0
✓ google-api-python-client==2.110.0
✓ requests==2.31.0


ETAPA 2: CONFIGURAÇÃO DE VARIÁVEIS
═══════════════════════════════════════════════════════════════════════

$ cp .env.example .env
$ nano .env  # ou seu editor favorito

Configurar:
✓ GEMINI_API_KEY (obrigatório)
✓ WHATSAPP_ACCESS_TOKEN (obrigatório)
✓ WHATSAPP_PHONE_NUMBER_ID (obrigatório)
✓ WHATSAPP_VERIFY_TOKEN (criar personalizado)
✓ GOOGLE_SERVICE_ACCOUNT_FILE (se usar Calendar)
✓ SECRET_KEY (gerar novo)


ETAPA 3: SETUP DO BANCO DE DADOS
═══════════════════════════════════════════════════════════════════════

$ python manage.py migrate

Operações:
  ✓ Applying contenttypes.0001_initial... OK
  ✓ Applying auth.0001_initial... OK
  ✓ Applying admin.0001_initial... OK
  ✓ Applying rag_agent.0001_initial... OK
  ✓ Applying rag_agent.0002_clinicainfo_whatsapp... OK
  ✓ Applying rag_agent.0003_medico_crm... OK
  ✓ Applying api_gateway.0001_initial... OK
  ✓ Applying api_gateway.0002_alter_session_state... OK
  ✓ Applying api_gateway.0003_session_name_confirmed... OK

$ python manage.py createsuperuser

Username: admin
Email: admin@clinica.com
Password: ******
Superuser created successfully.

$ python scripts/criar_dados_pneumosono.py

Dados criados:
✓ Clínica PneumoSono
✓ 2 Médicos (Dr. Gustavo, Dr. Gleyton Porto)
✓ 4 Especialidades
✓ 3 Convênios
✓ 2 Exames


ETAPA 4: CONFIGURAÇÃO DO GOOGLE CALENDAR (Opcional)
═══════════════════════════════════════════════════════════════════════

$ python scripts/setup_calendar_dev.py

Configurando Google Calendar:
✓ Service account autenticada
✓ Calendar API ativada
✓ Permissões configuradas
✓ Teste de conexão: OK


ETAPA 5: TESTES DE INTEGRAÇÃO
═══════════════════════════════════════════════════════════════════════

$ python manage.py runserver

Development server running at: http://127.0.0.1:8000/

Testando endpoints:
✓ GET /test-gemini-connection/
  Response: {"status": "success", "model": "gemini-2.0-flash"}

✓ POST /test-chatbot-service/
  Request: {"phone_number": "5511999999999", "message": "Olá"}
  Response: {"response": "Olá! Como posso ajudar?", "intent": "saudacao"}

✓ GET /admin/
  Admin interface: OK


ETAPA 6: CONFIGURAÇÃO DO WEBHOOK (WhatsApp)
═══════════════════════════════════════════════════════════════════════

Meta Developer Console:
1. Acessar: https://developers.facebook.com/apps
2. Configurar Webhook:
   URL: https://seu-dominio.com/webhook/
   Verify Token: [seu WHATSAPP_VERIFY_TOKEN]
3. Subscrever eventos:
   ✓ messages
   ✓ message_status

Teste:
$ curl -X POST https://seu-dominio.com/webhook/ \
  -H "Content-Type: application/json" \
  -d '{"entry":[{"changes":[{"value":{"messages":[{"from":"5511999999999","text":{"body":"Teste"}}]}}]}]}'

Response: {"status": "ok"}


ETAPA 7: DEPLOY EM PRODUÇÃO
═══════════════════════════════════════════════════════════════════════

Opção A: Heroku
───────────────
$ heroku create chatbot-clinica
$ git push heroku main
$ heroku config:set GEMINI_API_KEY=...
$ heroku config:set WHATSAPP_ACCESS_TOKEN=...
$ heroku run python manage.py migrate
$ heroku run python scripts/criar_dados_pneumosono.py

Opção B: Railway
────────────────
$ railway login
$ railway init
$ railway up
# Configurar variáveis no dashboard

Opção C: VPS (Ubuntu)
──────────────────────
$ sudo apt update
$ sudo apt install python3-pip python3-venv nginx
$ # ... configurar gunicorn, nginx, etc


ETAPA 8: MONITORAMENTO PÓS-DEPLOY
═══════════════════════════════════════════════════════════════════════

Verificar logs:
$ tail -f logs/django.log
$ tail -f logs/gemini.log

Monitorar tokens:
$ curl https://seu-dominio.com/token-usage-stats/

Testar webhook:
$ curl https://seu-dominio.com/webhook/?hub.mode=subscribe&hub.verify_token=...

═══════════════════════════════════════════════════════════════════════
✅ DEPLOY COMPLETO!
═══════════════════════════════════════════════════════════════════════
```

---

## 🎯 Métricas e Performance

### Dashboard de Métricas

```
┌──────────────────────────────────────────────────────────────────────┐
│ DASHBOARD DE PERFORMANCE                                             │
└──────────────────────────────────────────────────────────────────────┘

TEMPO DE RESPOSTA (Médias em ms)
═══════════════════════════════════════════════════════════════════════
┌────────────────────────────────┬──────────┬──────────┬──────────────┐
│ Operação                       │ Mínimo   │ Médio    │ Máximo       │
├────────────────────────────────┼──────────┼──────────┼──────────────┤
│ Recepção Webhook               │   5 ms   │  12 ms   │   45 ms      │
│ Busca Sessão (cache hit)       │   1 ms   │   3 ms   │   10 ms      │
│ Busca Sessão (cache miss)      │  30 ms   │  50 ms   │  120 ms      │
│ Análise Intenção (Gemini)      │ 200 ms   │ 450 ms   │  800 ms      │
│ Geração Resposta (Gemini)      │ 350 ms   │ 750 ms   │ 1500 ms      │
│ Consulta Google Calendar        │ 400 ms   │ 950 ms   │ 2200 ms      │
│ Salvar Banco de Dados           │  10 ms   │  25 ms   │   80 ms      │
│ Envio WhatsApp API              │  80 ms   │ 150 ms   │  300 ms      │
├────────────────────────────────┼──────────┼──────────┼──────────────┤
│ TOTAL (por mensagem)            │ 1.2s     │ 2.4s     │ 5.0s         │
└────────────────────────────────┴──────────┴──────────┴──────────────┘


USO DE TOKENS (Últimas 24h)
═══════════════════════════════════════════════════════════════════════
Tokens Usados:     654,321  ███████████████░░░░░░  43.6%
Limite Diário:   1,500,000
Tokens Restantes:  845,679

Por Operação:
├─ Análises (300 tokens/msg):     195,000  ██████░░░░░░░░░░░░  29.8%
├─ Respostas (600 tokens/msg):    390,000  ████████████░░░░░░  59.6%
└─ Cache hits (economizados):      69,321  ███░░░░░░░░░░░░░░░  10.6%

Modo Econômico: ❌ Desativado (uso < 80%)


SESSÕES E MENSAGENS
═══════════════════════════════════════════════════════════════════════
┌────────────────────────────────┬──────────────────────────────────┐
│ Sessões Ativas (últimas 24h)   │ 127                              │
│ Mensagens Processadas           │ 1,543                            │
│ Agendamentos Iniciados          │ 89                               │
│ Agendamentos Completos (Handoff)│ 52                               │
│ Taxa de Conversão               │ 58.4%                            │
└────────────────────────────────┴──────────────────────────────────┘


INTENÇÕES MAIS COMUNS
═══════════════════════════════════════════════════════════════════════
┌────────────────────────┬──────────┬───────────────────────────────┐
│ Intenção               │ Qtd      │ Gráfico                       │
├────────────────────────┼──────────┼───────────────────────────────┤
│ agendar_consulta       │  412     │ ████████████████████░░  53.3% │
│ buscar_info            │  215     │ ███████████░░░░░░░░░░  27.8% │
│ buscar_medico          │   98     │ █████░░░░░░░░░░░░░░░░  12.7% │
│ buscar_horarios        │   47     │ ██░░░░░░░░░░░░░░░░░░░   6.1% │
└────────────────────────┴──────────┴───────────────────────────────┘


SAÚDE DO SISTEMA
═══════════════════════════════════════════════════════════════════════
┌────────────────────────┬──────────┬───────────────────────────────┐
│ Métrica                │ Status   │ Valor                         │
├────────────────────────┼──────────┼───────────────────────────────┤
│ Uptime                 │ ✅ OK    │ 99.97% (última semana)        │
│ Erros (última hora)    │ ✅ OK    │ 2 (0.13%)                     │
│ Latência Média         │ ✅ OK    │ 2.4s (< 3s)                   │
│ Uso CPU                │ ✅ OK    │ 34% (< 70%)                   │
│ Uso Memória            │ ⚠️ WARN  │ 78% (< 90%)                   │
│ Conexões BD            │ ✅ OK    │ 12/100                        │
│ Cache Hit Rate         │ ✅ OK    │ 87%                           │
└────────────────────────┴──────────┴───────────────────────────────┘
```

---

**📅 Última Atualização:** Outubro 2025 
**📝 Versão:** 2.0 (Completa e Visual)  
**👨‍💻 Desenvolvido com:** Django + Gemini AI + Google Calendar + WhatsApp Business API
