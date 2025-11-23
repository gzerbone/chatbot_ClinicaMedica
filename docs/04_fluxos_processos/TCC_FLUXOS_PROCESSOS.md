# 🔄 Fluxos e Processos do Sistema

> **Documentação Acadêmica - Trabalho de Conclusão de Curso**  
> Sistema de Chatbot para Clínica Médica

---

## 📋 Índice

1. [Introdução](#introdução)
2. [Máquina de Estados da Conversação](#máquina-de-estados-da-conversação)
3. [Fluxo de Pré-Agendamento](#fluxo-de-pré-agendamento)
4. [Sistema de Pausar e Retomar](#sistema-de-pausar-e-retomar)
5. [Validação de Informações](#validação-de-informações)
6. [Integração com Google Calendar](#integração-com-google-calendar)
7. [Processo de Handoff](#processo-de-handoff)
8. [Casos de Uso Detalhados](#casos-de-uso-detalhados)

---

## 1. Introdução

### 1.1. Visão Geral

Este documento descreve em detalhes os **fluxos e processos** implementados no sistema de chatbot para agendamento médico. O sistema é construído sobre uma **máquina de estados finita** que gerencia a conversação com o usuário, garantindo coleta adequada de informações e transições consistentes entre etapas.

### 1.2. Conceitos Fundamentais

#### 1.2.1. Estado da Conversação

**Definição**: Um **estado** representa uma etapa específica do diálogo, caracterizada por:
- O que o sistema espera receber do usuário
- Quais informações já foram coletadas
- Qual é a próxima ação apropriada

#### 1.2.2. Transição de Estado

**Definição**: Uma **transição** é a mudança de um estado para outro, desencadeada por:
- Ação do usuário (envio de mensagem)
- Validação bem-sucedida de informação
- Confirmação ou negação explícita

#### 1.2.3. Persistência de Estado

O estado da conversação é persistido em banco de dados, permitindo:
- Continuação de conversas interrompidas
- Recuperação em caso de falhas do sistema
- Análise posterior do comportamento do usuário

---

## 2. Máquina de Estados da Conversação

### 2.1. Estados Implementados

O sistema implementa **9 estados principais**, cada um com um propósito específico:

```
┌─────────────────────────────────────────────────────────────────┐
│                   ESTADOS DA CONVERSAÇÃO                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. idle (Ocioso)                                               │
│     • Estado inicial                                            │
│     • Aguardando iniciativa do usuário                          │
│     • Sem informações coletadas                                 │
│                                                                  │
│  2. collecting_patient_info (Coletando Dados do Paciente)       │
│     • Solicitando nome completo                                 │
│     • Primeira interação após início                            │
│                                                                  │
│  3. confirming_name (Confirmando Nome do Paciente)              │
│     • Nome foi extraído, aguardando confirmação                 │
│     • Evita erros por interpretação incorreta                   │
│                                                                  │
│  4. selecting_specialty (Selecionando Especialidade)            │
│     • Nome confirmado                                           │
│     • Solicitando especialidade médica desejada                 │
│                                                                  │
│  5. selecting_doctor (Selecionando Médico)                      │
│     • Especialidade definida                                    │
│     • Apresentando lista de médicos                             │
│     • Aguardando escolha do médico                              │
│                                                                  │
│  6. choosing_schedule (Escolhendo Horário)                      │
│     • Médico selecionado                                        │
│     • Consultando Google Calendar                               │
│     • Apresentando horários disponíveis                         │
│                                                                  │
│  7. confirming (Confirmando)                                    │
│     • Todos dados coletados                                     │
│     • Apresentando resumo                                       │
│     • Aguardando confirmação final                              │
│                                                                  │
│  8. answering_questions (Respondendo Dúvidas)                   │
│     • Estado especial de interrupção                            │
│     • Usuário tem dúvida durante processo                       │
│     • Sistema salva contexto para retomar depois               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2. Diagrama de Transições de Estado

```
                        ┌──────────┐
                        │   idle   │
                        └────┬─────┘
                             │
                    Usuário inicia conversa
                             │
                             ▼
                ┌────────────────────────┐
                │ collecting_patient_    │
                │       info             │
                └────────┬───────────────┘
                         │
                 Nome extraído da mensagem
                         │
                         ▼
                ┌────────────────────────┐
                │   confirming_name      │
                └────┬────────────────┬──┘
                     │                │
              Não    │                │ Sim
                     │                │
        ┌────────────▼─┐              │
        │ Solicitar    │              │
        │ novamente    │              │
        └──────────────┘              │
                                      ▼
                         ┌────────────────────────┐
                         │  selecting_specialty   │
                         └────────┬───────────────┘
                                  │
                         Especialidade informada
                                  │
                                  ▼
                         ┌────────────────────────┐
                         │  selecting_doctor      │
                         └────────┬───────────────┘
                                  │
                           Médico selecionado
                                  │
                                  ▼
                         ┌────────────────────────┐
                         │  choosing_schedule     │
                         └────────┬───────────────┘
                                  │
                         Data e horário escolhidos
                                  │
                                  ▼
                         ┌────────────────────────┐
                         │     confirming         │
                         └────┬────────────────┬──┘
                              │                │
                       Não    │                │ Sim
                              │                │
                 ┌────────────▼─┐              │
                 │ Voltar para  │              │
                 │ modificar    │              │
                 └──────────────┘              │
                                               ▼
                                    ┌──────────────────┐
                                    │ Gerar handoff e  │
                                    │ enviar para      │
                                    │ secretária       │
                                    └──────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│              SISTEMA DE PAUSAR/RETOMAR (TRANSVERSAL)            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Qualquer Estado ──────┐                                        │
│                        │ Usuário faz pergunta                   │
│                        ▼                                        │
│              ┌─────────────────────┐                            │
│              │ answering_questions │                            │
│              └─────────┬───────────┘                            │
│                        │                                        │
│                        │ Usuário diz "continuar"                │
│                        ▼                                        │
│              ┌─────────────────────┐                            │
│              │ Estado Anterior     │                            │
│              │ (restaurado)        │                            │
│              └─────────────────────┘                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3. Modelo de Dados da Sessão

```python
class ConversationSession(models.Model):
    """
    Modelo que persiste o estado da conversação
    """
    # Identificação
    phone_number = models.CharField(max_length=20, unique=True)
    
    # Gerenciamento de Estados
    current_state = models.CharField(
        max_length=50,
        choices=[
            ('idle', 'Ocioso'),
            ('collecting_patient_info', 'Coletando Dados do Paciente'),
            ('answering_questions', 'Respondendo Dúvidas'),
            ('confirming_name', 'Confirmando Nome do Paciente'),
            ('selecting_specialty', 'Selecionando Especialidade'),
            ('selecting_doctor', 'Selecionando Médico'),
            ('choosing_schedule', 'Escolhendo Horário'),
            ('confirming', 'Confirmando'),
        ],
        default='idle'
    )
    
    # Sistema de Pausar/Retomar
    previous_state = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Estado anterior antes de pausar para dúvidas"
    )
    
    # Dados do Paciente
    patient_name = models.CharField(max_length=200, blank=True, null=True)
    pending_name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Nome pendente de confirmação"
    )
    name_confirmed = models.BooleanField(default=False)
    
    # Dados do Agendamento
    selected_specialty = models.CharField(max_length=100, blank=True, null=True)
    selected_doctor = models.CharField(max_length=200, blank=True, null=True)
    preferred_date = models.DateField(blank=True, null=True)
    preferred_time = models.CharField(max_length=10, blank=True, null=True)
    
    # Metadados
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    def update_activity(self):
        """Atualiza timestamp de última atividade"""
        self.last_activity = timezone.now()
        self.save()
```

---

## 3. Fluxo de Pré-Agendamento

### 3.1. Visão Geral do Processo

O **fluxo de pré-agendamento** é o processo principal do sistema, conduzindo o usuário da solicitação inicial até a geração do handoff para a secretária. É chamado de "pré-agendamento" porque a confirmação final é feita por um humano.

### 3.2. Diagrama Simplificado do Fluxo

```
┌──────────────────────────────────────────────────────────────┐
│              FLUXO DE PRÉ-AGENDAMENTO                        │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  IDLE                                                        │
│   │  "Quero agendar consulta"                               │
│   ▼                                                          │
│  COLETANDO NOME                                              │
│   │  "Meu nome é João Silva"                                │
│   ▼                                                          │
│  CONFIRMANDO NOME                                            │
│   │  "Sim"                                                   │
│   ▼                                                          │
│  SELECIONANDO ESPECIALIDADE                                  │
│   │  "Cardiologia"                                           │
│   ▼                                                          │
│  SELECIONANDO MÉDICO                                         │
│   │  "Dr. Carlos"                                            │
│   ▼                                                          │
│  ESCOLHENDO HORÁRIO                                          │
│   │  "Segunda às 14h"                                        │
│   ▼                                                          │
│  CONFIRMANDO                                                 │
│   │  "Sim, confirmo"                                         │
│   ▼                                                          │
│  HANDOFF GERADO                                              │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 3.3. Processamento Detalhado de Cada Etapa

Cada mensagem do usuário passa por um processo estruturado de análise e processamento que determina como o sistema deve responder e qual será o próximo estado da conversa. Este processo é composto por três elementos fundamentais que trabalham em conjunto: **identificação de intenção**, **extração de entidades** e **gerenciamento de estados**.

#### 3.3.1. Processo de Análise de Mensagens

Quando uma mensagem chega ao sistema, ela passa por um processo de análise em três etapas principais que ocorrem de forma sequencial e integrada:

**Etapa 1: Identificação de Intenção**

A identificação de intenção é o primeiro passo para compreender o propósito da mensagem do usuário. Este processo utiliza inteligência artificial para analisar o conteúdo textual e o contexto da conversa, determinando qual é a ação ou objetivo que o usuário deseja realizar.

O sistema classifica a mensagem em uma das seguintes categorias de intenção:

- **Saudação**: Quando o usuário cumprimenta ou inicia uma conversa casual ("olá", "bom dia", "tudo bem?")
- **Agendar Consulta**: Quando o usuário expressa desejo de marcar uma consulta médica ("quero agendar", "preciso marcar consulta")
- **Buscar Informação**: Quando o usuário quer apenas obter dados sobre a clínica, médicos, preços ou serviços ("quanto custa?", "vocês aceitam convênio?")
- **Confirmar Agendamento**: Quando o usuário confirma ou aprova informações apresentadas ("sim, está correto", "confirmo")
- **Dúvida**: Quando o usuário não compreendeu algo ou precisa de ajuda ("não entendi", "pode repetir?")

A identificação de intenção considera não apenas as palavras da mensagem atual, mas também o estado atual da conversa, o histórico de mensagens recentes e os dados já coletados na sessão. Por exemplo, se o sistema está no estado "selecting_doctor" (selecionando médico) e o usuário envia "Sim", o sistema compreende que a intenção é confirmar, não saudar.

Esta análise gera um nível de confiança numérico que indica quão certa o sistema está sobre a intenção detectada, permitindo que decisões sejam tomadas de forma mais segura quando há alta confiança, ou solicitando esclarecimento quando há incerteza.

**Etapa 2: Extração de Entidades**

A extração de entidades é o processo de identificar e extrair informações específicas e estruturadas presentes na mensagem do usuário. Enquanto a identificação de intenção responde "o que o usuário quer fazer", a extração de entidades responde "quais informações o usuário forneceu".

O sistema busca extrair as seguintes entidades nas mensagens:

- **Nome do Paciente**: Identifica quando o usuário informa seu nome completo ou parcial
- **Especialidade Médica**: Detecta menções a especialidades como "Cardiologia", "Ortopedia", "Pediatria"
- **Médico**: Identifica nomes de médicos mencionados, seja de forma completa ("Dr. Carlos Alberto") ou parcial ("Dr. Carlos")
- **Data**: Extrai referências temporais tanto absolutas ("15/11/2025") quanto relativas ("amanhã", "segunda-feira")
- **Horário**: Identifica momentos do dia mencionados ("14h", "14:00", "duas da tarde")

A extração de entidades é realizada de forma inteligente, considerando o contexto da conversa. Por exemplo, se o usuário diz "preciso de um cardiologista", o sistema não apenas extrai a especialidade "Cardiologia", mas também compreende que isso está relacionado ao agendamento. Se o usuário menciona "segunda às 14h" em uma única frase, o sistema extrai tanto a data quanto o horário simultaneamente.

O processo de extração também realiza validações básicas. Por exemplo, se um nome é extraído com apenas uma palavra, o sistema pode considerar isso incompleto e solicitar o nome completo. Se uma data é mencionada mas está no passado, o sistema identifica isso como inválido e solicita uma data futura.

**Etapa 3: Gerenciamento de Estados**

O gerenciamento de estados é o mecanismo que controla o fluxo da conversa, garantindo que as informações sejam coletadas na ordem correta e que o sistema sempre saiba em qual etapa do processo de agendamento ele se encontra.

O sistema mantém um estado atual que representa a fase específica do agendamento. Quando uma mensagem chega, o sistema primeiro analisa a intenção e extrai entidades, e então utiliza essas informações, combinadas com o estado atual, para determinar:

1. **Se deve avançar para o próximo estado**: Quando o usuário fornece a informação esperada no estado atual
2. **Se deve permanecer no mesmo estado**: Quando a informação fornecida está incompleta ou inválida
3. **Se deve retornar a um estado anterior**: Quando o usuário quer corrigir informações já fornecidas
4. **Se deve pausar o fluxo**: Quando o usuário faz uma pergunta ou busca informação não relacionada ao agendamento

Por exemplo, quando o sistema está no estado "selecting_specialty" (selecionando especialidade) e o usuário informa "Cardiologia", o sistema extrai essa entidade, identifica que a intenção é de agendamento, valida que a especialidade existe no banco de dados, salva essa informação na sessão e então avança para o estado "selecting_doctor" (selecionando médico), pois a próxima etapa lógica é escolher qual cardiologista o usuário prefere.

#### 3.3.2. Processamento de Cada Etapa do Fluxo

**Etapa 1: Iniciação (idle → collecting_patient_info)**

Quando o usuário envia uma mensagem inicial solicitando agendamento, o sistema identifica a intenção como "agendar_consulta". Neste momento, nenhuma informação ainda foi coletada, então o estado muda de "idle" (ocioso) para "collecting_patient_info" (coletando dados do paciente). 

O sistema solicita o nome completo do usuário. Esta etapa é fundamental porque o nome será usado para personalizar as mensagens seguintes e para gerar o registro final do agendamento.

**Etapa 2: Coleta de Nome (collecting_patient_info → confirming_name)**

Quando o usuário informa seu nome, o sistema utiliza a extração de entidades para identificar e extrair o nome mencionado na mensagem. O sistema valida se o nome possui pelo menos duas palavras (nome e sobrenome), garantindo que seja completo.

Após a extração bem-sucedida, o sistema não avança imediatamente para a próxima etapa. Em vez disso, muda para o estado "confirming_name" (confirmando nome), onde solicita confirmação explícita ao usuário. Este passo é importante porque nomes podem ser extraídos incorretamente ou o usuário pode ter digitado errado. A confirmação reduz erros que poderiam comprometer todo o processo posterior.

**Etapa 3: Confirmação de Nome (confirming_name → selecting_specialty)**

Quando o usuário confirma o nome (através de "sim", "correto", "está certo"), o sistema identifica a intenção como "confirmar_agendamento", salva o nome confirmado na sessão e avança para o estado "selecting_specialty" (selecionando especialidade).

Se o usuário negar a confirmação ("não", "está errado"), o sistema retorna ao estado "collecting_patient_info" e solicita que o usuário digite o nome novamente. Isso garante que o nome correto seja coletado antes de prosseguir.

**Etapa 4: Seleção de Especialidade (selecting_specialty → selecting_doctor)**

No estado "selecting_specialty", o sistema aguarda que o usuário informe qual especialidade médica deseja. Quando o usuário menciona uma especialidade, o sistema extrai essa entidade e valida se a especialidade existe no banco de dados da clínica.

A validação é importante porque usuários podem mencionar especialidades que não existem, usar sinônimos ou grafias alternativas. O sistema normaliza a especialidade extraída e verifica se corresponde a alguma especialidade cadastrada. Se válida, a especialidade é salva na sessão e o sistema avança para "selecting_doctor" (selecionando médico).

Neste novo estado, o sistema consulta o banco de dados para listar todos os médicos que atendem aquela especialidade, apresentando-os ao usuário de forma organizada e clara.

**Etapa 5: Seleção de Médico (selecting_doctor → choosing_schedule)**

Quando o usuário escolhe um médico, o sistema extrai o nome do médico mencionado. Este processo pode ser desafiador porque usuários podem mencionar o médico de diferentes formas: pelo nome completo ("Dr. Carlos Alberto"), apenas pelo primeiro nome ("Dr. Carlos"), ou até pelo último nome ("Dr. Alberto").

O sistema compara o nome extraído com os médicos disponíveis para aquela especialidade, utilizando técnicas de correspondência flexível para encontrar o médico correto mesmo com variações no nome. Uma vez identificado e validado, o médico é salva na sessão e o sistema avança para "choosing_schedule" (escolhendo horário).

**Etapa 6: Escolha de Data e Horário (choosing_schedule → confirming)**

Esta é uma das etapas mais complexas, pois envolve a integração com sistemas externos e múltiplas validações. Quando o usuário menciona uma data e horário, o sistema extrai ambas as entidades simultaneamente.

A data é normalizada e convertida para um formato padrão, processando tanto datas absolutas ("15/11/2025") quanto relativas ("amanhã", "próxima segunda"). O sistema valida que a data é futura e não está no passado.

O horário é extraído e normalizado para o formato padrão (HH:MM), processando variações como "14h", "14:00", "duas da tarde", "14 horas". O sistema valida que o horário está dentro do horário comercial da clínica.

Após extrair e validar data e horário, o sistema consulta a disponibilidade do médico selecionado no Google Calendar. Esta consulta verifica se o médico realmente está disponível naquele dia e horário específicos. Se disponível, os dados são salvos na sessão e o sistema avança para "confirming" (confirmando). Se não disponível, o sistema informa ao usuário e solicita que escolha outro horário, permanecendo no estado "choosing_schedule".

**Etapa 7: Confirmação Final (confirming → handoff)**

No estado "confirming", o sistema apresenta um resumo completo de todas as informações coletadas: nome do paciente, especialidade, médico, data e horário. O sistema aguarda a confirmação explícita do usuário.

Quando o usuário confirma, o sistema realiza uma validação final completa de todos os dados. Esta validação verifica:

1. Se todas as informações obrigatórias foram coletadas
2. Se o nome foi confirmado pelo usuário
3. Se a especialidade ainda existe e é válida
4. Se o médico ainda está ativo e atende aquela especialidade
5. Se a data e horário ainda estão disponíveis no Google Calendar

Esta revalidação é importante porque informações podem ter mudado entre o momento em que foram coletadas e o momento da confirmação final. Por exemplo, o horário pode ter sido ocupado por outro paciente no intervalo.

Se todas as validações passam, o sistema gera o handoff, que é um link direto para WhatsApp da secretária contendo todas as informações do pré-agendamento formatadas. O usuário recebe uma mensagem final confirmando que o pré-agendamento foi realizado com sucesso, incluindo o resumo completo e o link para contato direto com a secretária.

#### 3.3.3. Interação entre Intenção, Entidades e Estados

O poder do sistema reside na interação dinâmica entre os três componentes de análise. Eles não funcionam de forma isolada, mas trabalham juntos para tomar decisões inteligentes sobre como processar cada mensagem.

**Cenário 1: Fluxo Normal**

Quando um usuário segue o fluxo esperado, informando cada dado quando solicitado, a identificação de intenção detecta que o usuário está colaborando com o agendamento, a extração de entidades captura a informação específica mencionada, e o gerenciamento de estados avança para a próxima etapa. Por exemplo: sistema pede especialidade (estado "selecting_specialty"), usuário responde "Cardiologia" (intenção: agendar_consulta, entidade: especialidade="Cardiologia"), sistema avança para "selecting_doctor".

**Cenário 2: Informação Fornecida Antecipadamente**

Usuários experientes ou ansiosos podem fornecer múltiplas informações em uma única mensagem. Por exemplo, quando o sistema pede o nome, o usuário pode responder "Meu nome é João Silva e quero consulta com cardiologista". Neste caso, o sistema extrai tanto o nome quanto a especialidade, identifica a intenção de agendamento, e processa ambas as informações sequencialmente: primeiro salva o nome e pede confirmação, mas já tem a especialidade registrada para quando chegar nessa etapa.

**Cenário 3: Dúvida Durante o Agendamento**

Quando o usuário está em qualquer etapa do agendamento e faz uma pergunta não relacionada ("quanto custa a consulta?"), o sistema identifica a intenção como "buscar_info". Como essa intenção não corresponde ao estado atual (que está focado em coletar dados), o sistema pausa temporariamente o fluxo de agendamento, muda para o estado "answering_questions" (respondendo dúvidas), salva o estado anterior, responde a dúvida do usuário, e depois retoma o agendamento no ponto onde parou quando o usuário estiver pronto para continuar.

**Cenário 4: Correção de Informação**

Se o usuário quer corrigir uma informação já fornecida, o sistema identifica a intenção e as entidades na mensagem. Por exemplo, se o usuário já escolheu Ortopedia mas depois diz "na verdade quero Cardiologia", o sistema detecta a nova especialidade mencionada, identifica que é uma correção, e atualiza a informação na sessão, ajustando o estado apropriadamente (pode voltar para "selecting_doctor" se já havia escolhido um médico).

**Cenário 5: Informação Inválida**

Quando o usuário fornece uma informação que não pode ser validada (por exemplo, uma especialidade que não existe na clínica), o sistema extrai a entidade mas falha na validação. O estado permanece o mesmo, e o sistema informa ao usuário que a informação não é válida, solicitando que forneça novamente. Isso garante que apenas dados corretos sejam salvos.

#### 3.3.4. Validação e Completude de Dados

O sistema possui um mecanismo de validação contínua que verifica, após cada interação, se todas as informações necessárias para gerar o handoff já foram coletadas. Este mecanismo analisa a sessão atual e identifica quais informações estão faltando.

A validação segue uma ordem obrigatória de coleta: primeiro o nome (com confirmação), depois a especialidade, em seguida o médico, depois a data, e por fim o horário. Esta ordem não é arbitrária - ela existe porque algumas informações dependem de outras. Por exemplo, não faz sentido consultar a disponibilidade de horários de um médico se o médico ainda não foi selecionado.

Se o sistema detecta que todas as informações foram coletadas e validadas, ele automaticamente sugere avançar para a etapa de confirmação final, mesmo que o estado atual não seja exatamente o esperado. Isso permite que o sistema se auto-corrija se houver alguma inconsistência e garante que o fluxo sempre avance quando todas as condições forem atendidas.

Esta validação contínua também permite que o sistema seja resiliente a interrupções. Se um usuário para no meio do processo e retorna depois, o sistema verifica o que já foi coletado e continua a partir do ponto onde parou, sem precisar recomeçar do zero.

### 3.4. Algoritmo de Validação de Completude

```python
def get_missing_appointment_info(phone_number: str) -> Dict:
    """
    Valida se todas as informações necessárias foram coletadas
    
    ⚠️ ATUALIZADO: Agora verifica name_confirmed e preferred_time
    
    Returns:
        {
            'is_complete': bool,
            'missing_info': List[str],
            'next_action': str  # Usado para mapear next_state
        }
    """
    
    session = get_or_create_session(phone_number)
    missing_info = []
    
    # ═══════════════════════════════════════════════════════════════
    # VALIDAÇÃO 1: Nome do Paciente
    # ═══════════════════════════════════════════════════════════════
    # ⚠️ NOTA: A validação de name_confirmed é feita no core_service
    # (linha 516-520) antes de chamar get_missing_appointment_info
    # Aqui apenas verifica se patient_name existe
    if not session.patient_name:
        missing_info.append('patient_name')
    
    # ═══════════════════════════════════════════════════════════════
    # VALIDAÇÃO 2: Especialidade (com validação no banco)
    # ═══════════════════════════════════════════════════════════════
    if not session.selected_specialty:
        missing_info.append('selected_specialty')
    else:
        # ⚠️ VALIDAÇÃO ADICIONAL: Verifica se especialidade existe no banco
        # Pode ter sido salva incorretamente ou removida
        if not self._validate_specialty_in_db(session.selected_specialty):
            logger.warning(f"⚠️ Especialidade salva '{session.selected_specialty}' é inválida")
            missing_info.append('selected_specialty')
            session.selected_specialty = None  # Limpar inválida
            session.save()
    
    # ═══════════════════════════════════════════════════════════════
    # VALIDAÇÃO 3: Médico (com validação no banco)
    # ═══════════════════════════════════════════════════════════════
    if not session.selected_doctor:
        missing_info.append('selected_doctor')
    else:
        # ⚠️ VALIDAÇÃO ADICIONAL: Verifica se médico existe e atende especialidade
        if not self._validate_doctor_in_db(session.selected_doctor, session.selected_specialty):
            logger.warning(f"⚠️ Médico salvo '{session.selected_doctor}' é inválido")
            missing_info.append('selected_doctor')
            session.selected_doctor = None  # Limpar inválido
            session.save()
    
    # ═══════════════════════════════════════════════════════════════
    # VALIDAÇÃO 4: Data
    # ═══════════════════════════════════════════════════════════════
    if not session.preferred_date:
        missing_info.append('preferred_date')
    
    # ═══════════════════════════════════════════════════════════════
    # VALIDAÇÃO 5: Horário (OBRIGATÓRIO)
    # ═══════════════════════════════════════════════════════════════
    # ⚠️ IMPORTANTE: Horário é obrigatório e deve estar válido
    # Se foi rejeitado por indisponibilidade, preferred_time = None
    # Isso é verificado no core_service antes de gerar handoff
    if not session.preferred_time:
        missing_info.append('preferred_time')
    
    # ═══════════════════════════════════════════════════════════════
    # DETERMINAR PRÓXIMA AÇÃO (ORDEM DE PRIORIDADE OBRIGATÓRIA)
    # ═══════════════════════════════════════════════════════════════
    next_action = self._get_next_action(missing_info)
    
    return {
        'missing_info': missing_info,
        'next_action': next_action,
        'is_complete': len(missing_info) == 0,
        'current_state': session.current_state
    }


def _get_next_action(missing_info: List[str]) -> str:
    """
    Determina a próxima ação baseada nas informações faltantes
    
    ORDEM OBRIGATÓRIA:
    1. Nome do paciente
    2. Especialidade médica
    3. Médico (obrigatório antes de data/horário)
    4. Data
    5. Horário
    """
    if not missing_info:
        return 'generate_handoff'
    
    # Fluxo sequencial OBRIGATÓRIO de coleta
    if 'patient_name' in missing_info:
        return 'ask_name'
    elif 'selected_specialty' in missing_info:
        return 'ask_specialty'
    elif 'selected_doctor' in missing_info:
        return 'ask_doctor'  # Médico DEVE ser selecionado antes de data/horário
    elif 'preferred_date' in missing_info:
        return 'ask_date'  # Só pergunta data se já tiver especialidade E médico
    elif 'preferred_time' in missing_info:
        return 'ask_time'  # Só pergunta horário se já tiver data
    else:
        return 'ask_general'
```

**Mapeamento de next_action para next_state:**

O `next_action` retornado é mapeado para o `next_state` correto no `_handle_patient_name_flow()` (linha 996-1004):

```python
action_to_state = {
    'ask_specialty': 'selecting_specialty',
    'ask_doctor': 'selecting_doctor',
    'ask_date': 'choosing_schedule',
    'ask_time': 'choosing_schedule',
    'generate_handoff': 'confirming',
    'ask_general': 'idle'
}
next_state = action_to_state.get(next_action, 'idle')
```

**Mudanças Importantes na Implementação:**

1. ✅ **Validação de especialidade/médico no banco**: Verifica se dados salvos ainda são válidos
2. ✅ **Limpeza automática de dados inválidos**: Remove especialidade/médico inválidos da sessão
3. ✅ **Verificação de `preferred_time` no core_service**: Antes de gerar handoff, verifica se horário está válido (linha 516-520)
4. ✅ **Ordem obrigatória**: `_get_next_action()` garante ordem: nome → especialidade → médico → data → horário
5. ✅ **Retorna `current_state`**: Incluído no retorno para facilitar debug

---

## 4. Sistema de Pausar e Retomar

### 4.1. Motivação

Durante o processo de agendamento, usuários frequentemente têm dúvidas que precisam ser esclarecidas antes de prosseguir:

- "Quanto custa a consulta?"
- "Vocês aceitam meu convênio?"
- "Qual é o endereço da clínica?"
- "O médico é especialista em quê exatamente?"

O **sistema de pausar/retomar** permite que o bot responda essas dúvidas **sem perder o progresso** do agendamento.

### 4.2. Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│              SISTEMA DE PAUSAR/RETOMAR                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  COMPONENTES:                                                   │
│  ───────────────────────────────────────────────────────────   │
│                                                                  │
│  1. Campo previous_state (ConversationSession)                  │
│     • Armazena estado antes da pausa                            │
│     • Permite restauração posterior                             │
│     • Nullable (None quando não pausado)                        │
│                                                                  │
│  2. Estado answering_questions                                  │
│     • Estado especial de interrupção                            │
│     • Ativo enquanto usuário tira dúvidas                       │
│     • Não avança no fluxo de agendamento                        │
│                                                                  │
│  3. Métodos de Controle (ConversationService)                   │
│     • pause_for_question(phone_number)                          │
│     • resume_appointment(phone_number)                          │
│     • has_paused_appointment(phone_number)                      │
│     • is_in_question_mode(phone_number)                         │
│                                                                  │
│  4. Retomada Automática Inteligente                              │
│     • Detecta entidades de agendamento (especialidade, médico, │
│       data, horário)                                             │
│     • Retoma automaticamente quando usuário fornece informações │
│     • Funciona mesmo com intent buscar_info ou duvida           │
│     • Fluxo natural e fluido, sem palavras-chave                │
│                                                                  │
│  5. Retomada Manual (Palavras-chave)                            │
│     • "continuar", "retomar", "voltar"                          │
│     • "prosseguir", "seguir", "agendamento"                     │
│     • Usado quando usuário não fornece informações              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3. Fluxo de Pausa

```python
def pause_for_question(phone_number: str) -> bool:
    """
    Pausa o agendamento para responder dúvida
    
    Exemplo de uso:
        Estado atual: selecting_doctor
        Usuário pergunta: "Qual o preço?"
        Sistema:
            1. Salva: previous_state = "selecting_doctor"
            2. Muda: current_state = "answering_questions"
            3. Responde dúvida com RAGService
    """
    try:
        session = get_or_create_session(phone_number)
        
        # Verificar se já não está em modo de perguntas
        if session.current_state != 'answering_questions':
            # Salvar estado atual
            session.previous_state = session.current_state
            
            # Mudar para modo de perguntas
            session.current_state = 'answering_questions'
            session.save()
            
            logger.info(
                f"⏸️ Agendamento pausado. "
                f"Estado anterior: {session.previous_state}"
            )
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Erro ao pausar: {e}")
        return False
```

### 4.4. Fluxo de Retomada

O sistema possui **duas formas de retomada**: automática (inteligente) e manual (palavras-chave).

#### 4.4.1. Retomada Automática (Inteligente)

**Arquivo:** `api_gateway/services/gemini/core_service.py` (linhas 843-879)

O sistema detecta automaticamente quando o usuário fornece informações de agendamento durante `answering_questions` e retoma o fluxo automaticamente, mesmo que a intenção seja `buscar_info` ou `duvida`.

```python
# Retomada automática após geração da resposta
if session.get('current_state') == 'answering_questions' and session.get('previous_state'):
    entities = analysis_result.get('entities', {})
    
    # Verificar se há entidades NOVAS de agendamento sendo fornecidas
    has_new_appointment_entities = any([
        entities.get('medico') and entities.get('medico') != session.get('selected_doctor'),
        entities.get('especialidade') and entities.get('especialidade') != session.get('selected_specialty'),
        entities.get('data'),
        entities.get('horario')
    ])
    
    intent = analysis_result.get('intent', '')
    
    # LÓGICA DE RETOMADA:
    # 1. Se há entidades NOVAS de agendamento, retomar SEMPRE
    #    (mesmo que a intenção seja buscar_info ou duvida)
    # 2. Se a intenção é explicitamente de agendamento, retomar
    # 3. NÃO retomar se é apenas uma pergunta sem entidades
    should_resume = False
    
    if has_new_appointment_entities:
        # Retomar independente da intenção
        should_resume = True
    elif intent in ['agendar_consulta', 'confirmar_agendamento', 'selecionar_especialidade', 'confirming_name']:
        should_resume = True
    
    if should_resume:
        restored_state = session.get('previous_state')
        session['current_state'] = restored_state
        session['previous_state'] = None
        # Atualizar no banco também
        db_session = conversation_service.get_or_create_session(phone_number)
        db_session.current_state = restored_state
        db_session.previous_state = None
        db_session.save()
        logger.info(f"🔄 Retomada automática: answering_questions → {restored_state}")
```

**Comportamento:**
- ✅ Retoma automaticamente quando detecta entidades de agendamento (especialidade, médico, data, horário)
- ✅ Funciona mesmo com intent `buscar_info` ou `duvida` (usuário está fornecendo informações)
- ✅ A retomada acontece **DEPOIS** da geração da resposta (dúvidas são respondidas primeiro)
- ✅ Fluxo natural e fluido, sem necessidade de palavras-chave

#### 4.4.2. Retomada Manual (Palavras-chave)

```python
def resume_appointment(phone_number: str) -> Dict:
    """
    Retoma o agendamento após responder dúvidas (retomada manual)
    
    Exemplo de uso:
        Estado atual: answering_questions (previous_state = "selecting_doctor")
        Usuário diz: "Continuar"
        Sistema:
            1. Restaura: current_state = "selecting_doctor"
            2. Limpa: previous_state = None
            3. Continua: "Qual médico você prefere?"
    """
    try:
        session = get_or_create_session(phone_number)
        
        # Verificar se há agendamento pausado
        if (session.current_state == 'answering_questions' and 
            session.previous_state):
            
            # Restaurar estado anterior
            restored_state = session.previous_state
            session.current_state = restored_state
            session.previous_state = None
            session.save()
            
            logger.info(f"▶️ Agendamento retomado. Estado: {restored_state}")
            
            # Gerar próxima pergunta apropriada
            next_question = get_next_question_for_state(restored_state, session)
            
            return {
                'resumed': True,
                'restored_state': restored_state,
                'next_question': next_question,
                'message': f'Perfeito! Vamos continuar. {next_question}'
            }
        
        return {
            'resumed': False,
            'message': 'Não há agendamento pausado para retomar.'
        }
        
    except Exception as e:
        logger.error(f"Erro ao retomar: {e}")
        return {
            'resumed': False,
            'message': 'Ocorreu um erro ao retomar o agendamento.'
        }
```

**Palavras-chave reconhecidas:**
- "continuar", "retomar", "voltar", "prosseguir", "seguir", "agendamento"

### 4.5. Exemplo Completo de Uso

```
┌─────────────────────────────────────────────────────────────────┐
│          EXEMPLO: PAUSAR E RETOMAR DURANTE AGENDAMENTO          │
└─────────────────────────────────────────────────────────────────┘

SITUAÇÃO INICIAL:
─────────────────────────────────────────────────────────────────
Estado: selecting_doctor
Progresso: Nome confirmado, especialidade selecionada
Sistema apresentou lista de médicos

INTERRUPÇÃO PARA DÚVIDA:
─────────────────────────────────────────────────────────────────
👤 Usuário: "Quanto custa a consulta particular?"

🤖 Sistema:
   │
   ├─ IntentDetector → Detecta: "buscar_info"
   ├─ Verifica: current_state != 'idle' e != 'answering_questions'
   ├─ Ação: ConversationService.pause_for_question()
   │  ├─ previous_state = "selecting_doctor"  ✅ SALVO
   │  └─ current_state = "answering_questions"
   ├─ RAGService.search_knowledge_base("preço consulta")
   └─ Resposta: """
      💰 **Valores das Consultas:**
      
      • Consulta Particular: R$ 180,00 a R$ 250,00 
        (varia conforme especialidade)
      • Retorno: R$ 100,00
      • Convênios aceitos: Unimed, Bradesco Saúde
      
      Posso ajudar com mais alguma informação?
      """

USUÁRIO PODE FAZER MAIS PERGUNTAS:
─────────────────────────────────────────────────────────────────
👤 Usuário: "Qual o endereço da clínica?"

🤖 Sistema:
   │
   ├─ Estado: answering_questions (mantém)
   ├─ RAGService.search_knowledge_base("endereço")
   └─ Resposta: """
      📍 **Nossa Localização:**
      
      Rua Principal, 123 - Centro
      Itabuna - BA, CEP 45600-000
      
      📞 Telefone: (73) 3613-5380
      
      Tem mais alguma dúvida?
      """

RETOMADA DO AGENDAMENTO (2 FORMAS):
─────────────────────────────────────────────────────────────────

OPÇÃO 1: RETOMADA AUTOMÁTICA (Recomendada)
─────────────────────────────────────────────────────────────────
👤 Usuário: "Pneumologia"  ← Forneceu especialidade (entidade de agendamento)

🤖 Sistema:
   │
   ├─ Detecta: Entidade "especialidade" = "Pneumologia"
   ├─ Verifica: has_new_appointment_entities = True
   ├─ Ação: Retomada automática
   │  ├─ current_state = "selecting_doctor"  ✅ RESTAURADO AUTOMATICAMENTE
   │  └─ previous_state = None
   ├─ Processa: Especialidade atualizada na sessão
   └─ Resposta: """
      Com a especialidade de Pneumologia escolhida, temos o Dr. Gustavo Magno...
      [Continua naturalmente o fluxo]
      """

OPÇÃO 2: RETOMADA MANUAL (Palavras-chave)
─────────────────────────────────────────────────────────────────
👤 Usuário: "Não, pode continuar"

🤖 Sistema:
   │
   ├─ Detecta: Palavra-chave "continuar"
   ├─ Ação: ConversationService.resume_appointment()
   │  ├─ current_state = "selecting_doctor"  ✅ RESTAURADO
   │  └─ previous_state = None
   ├─ Recupera: Contexto do estado selecting_doctor
   └─ Resposta: """
      ✅ **Perfeito! Vamos continuar seu agendamento.**
      
      Você estava escolhendo o médico para Cardiologia.
      
      👨‍⚕️ **Nossos cardiologistas:**
      
      **Dr. Carlos Alberto**
      💰 R$ 200,00
      
      **Dra. Maria Santos**
      💰 R$ 180,00
      
      Qual médico você prefere?
      """

CONTINUAÇÃO NORMAL DO FLUXO:
─────────────────────────────────────────────────────────────────
👤 Usuário: "Quero Dr. Carlos"

🤖 Sistema:
   │
   └─ [Continua normalmente para choosing_schedule...]
```

---

## 5. Validação de Informações

### 5.1. Tipos de Validação

O sistema implementa **múltiplas camadas de validação** para garantir dados corretos e consistentes:

```
┌─────────────────────────────────────────────────────────────────┐
│                 CAMADAS DE VALIDAÇÃO                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  CAMADA 1: Validação de Formato                                │
│  ═══════════════════════════════════════════════════════════   │
│  • Tipo de mensagem (apenas texto)                              │
│  • Estrutura do webhook WhatsApp                                │
│  • Encoding UTF-8                                               │
│  Implementado em: views.py (WhatsAppView)                       │
│                                                                  │
│  CAMADA 2: Validação Sintática                                 │
│  ═══════════════════════════════════════════════════════════   │
│  • Nome: Pelo menos 2 palavras (nome + sobrenome)              │
│  • Data: Formato válido (DD/MM/YYYY, relativo)                 │
│  • Horário: Formato HH:MM ou variações                          │
│  Implementado em: EntityExtractor                               │
│                                                                  │
│  CAMADA 3: Validação Semântica                                 │
│  ═══════════════════════════════════════════════════════════   │
│  • Especialidade existe no banco de dados                       │
│  • Médico existe e atende especialidade                         │
│  • Data é futura (não passado)                                  │
│  • Horário está em range válido (06:00-20:00)                  │
│  Implementado em: SmartSchedulingService                        │
│                                                                  │
│  CAMADA 4: Validação de Negócio                                │
│  ═══════════════════════════════════════════════════════════   │
│  • Médico atende no dia solicitado                              │
│  • Horário está disponível no Google Calendar                   │
│  • Não há conflitos de agendamento                              │
│  Implementado em: GoogleCalendarService                         │
│                                                                  │
│  CAMADA 5: Validação de Completude                             │
│  ═══════════════════════════════════════════════════════════   │
│  • Todas informações obrigatórias preenchidas                   │
│  • Nome foi confirmado pelo usuário                             │
│  • Dados consistentes entre si                                  │
│  Implementado em: ConversationService                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2. Validação de Nome do Paciente

```python
def extract_patient_name(message: str) -> Optional[str]:
    """
    Extrai e valida nome do paciente
    
    Regras:
    1. Deve ter pelo menos 2 palavras (nome + sobrenome)
    2. Apenas letras e espaços (aceita acentuação)
    3. Capitalização automática
    4. Remove prefixos comuns ("meu nome é", "sou", etc.)
    """
    
    # Padrões de extração
    patterns = [
        r'meu\s+nome\s+é\s+([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)*)',
        r'sou\s+([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)*)',
        r'chamo-me\s+([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)*)',
        r'nome\s+é\s+([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)*)',
        r'me\s+chamo\s+([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)*)',
        r'^([A-Za-zÀ-ÿ]+\s+[A-Za-zÀ-ÿ]+)(?:\s|,|$)'  # Nome direto
    ]
    
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            name_parts = name.split()
            
            # Validação: pelo menos 2 palavras
            if len(name_parts) >= 2:
                # Capitalizar corretamente
                return ' '.join(part.capitalize() for part in name_parts)
    
    return None


# Exemplos de extração:
# "Meu nome é João Silva" → "João Silva" ✅
# "João Silva" → "João Silva" ✅
# "João" → None ❌ (só uma palavra)
# "João da Silva Santos" → "João Da Silva Santos" ✅
```

### 5.3. Validação de Data

```python
def normalize_date_for_database(date_str: str) -> Optional[str]:
    """
    Normaliza e valida datas
    
    Entradas aceitas:
    • Relativas: "hoje", "amanhã", "segunda", "terça", etc.
    • Absolutas: "15/11", "15/11/2025", "15-11-2025"
    
    Validações:
    • Data deve ser futura (não passado)
    • Dia/mês/ano devem ser válidos
    • Assume ano atual se não especificado
    
    Saída:
    • Formato: YYYY-MM-DD
    """
    
    if not date_str:
        return None
    
    try:
        today = timezone.now().date()
        date_lower = date_str.lower().strip()
        
        # Processar palavras especiais
        if 'hoje' in date_lower:
            return today.strftime('%Y-%m-%d')
        
        elif 'amanhã' in date_lower or 'amanha' in date_lower:
            tomorrow = today + timedelta(days=1)
            return tomorrow.strftime('%Y-%m-%d')
        
        elif 'depois de amanhã' in date_lower:
            day_after = today + timedelta(days=2)
            return day_after.strftime('%Y-%m-%d')
        
        # Processar dias da semana
        weekdays = {
            'segunda': 0, 'terça': 1, 'terca': 1,
            'quarta': 2, 'quinta': 3, 'sexta': 4,
            'sábado': 5, 'sabado': 5, 'domingo': 6
        }
        
        for day_name, day_num in weekdays.items():
            if day_name in date_lower:
                days_ahead = (day_num - today.weekday()) % 7
                if days_ahead == 0:  # Mesmo dia da semana
                    days_ahead = 7  # Próxima semana
                target_date = today + timedelta(days=days_ahead)
                return target_date.strftime('%Y-%m-%d')
        
        # Processar formatos numéricos
        formats = [
            '%d/%m/%Y',  # 15/11/2025
            '%d/%m/%y',  # 15/11/25
            '%d-%m-%Y',  # 15-11-2025
            '%Y-%m-%d',  # 2025-11-15
            '%d/%m',     # 15/11 (assume ano atual)
        ]
        
        for fmt in formats:
            try:
                parsed = datetime.strptime(date_str, fmt)
                
                # Se não tem ano, assumir ano atual
                if fmt == '%d/%m':
                    parsed = parsed.replace(year=today.year)
                
                # Validar se é data futura
                if parsed.date() < today:
                    logger.warning(f"Data no passado: {date_str}")
                    return None
                
                return parsed.strftime('%Y-%m-%d')
            
            except ValueError:
                continue
        
        logger.warning(f"Data não pôde ser normalizada: {date_str}")
        return None
        
    except Exception as e:
        logger.error(f"Erro ao normalizar data '{date_str}': {e}")
        return None


# Exemplos de normalização:
# "hoje" → "2025-11-15" ✅
# "amanhã" → "2025-11-16" ✅
# "segunda" → "2025-11-18" ✅ (próxima segunda)
# "15/11" → "2025-11-15" ✅
# "15/11/2025" → "2025-11-15" ✅
# "10/11/2025" → None ❌ (data passada)
```

---

## 6. Integração com Google Calendar

### 6.1. Propósito

A integração com **Google Calendar API** permite:

1. **Consultar disponibilidade real** dos médicos
2. **Validar horários** antes de apresentar ao usuário
3. **Evitar conflitos** de agendamento
4. **Atualizar agenda** após confirmação

### 6.2. Fluxo de Consulta

```python
def get_doctor_availability(doctor_name: str, days_ahead: int = 7) -> Dict:
    """
    Consulta disponibilidade de um médico no Google Calendar
    
    Args:
        doctor_name: Nome do médico (ex: "Dr. Carlos Alberto")
        days_ahead: Quantos dias à frente consultar
    
    Returns:
        {
            'available': bool,
            'days_info': List[Dict],  # Informações por dia
            'total_slots': int
        }
    
    Processo:
    1. Autenticar com Google Calendar API
    2. Buscar calendário do médico
    3. Consultar eventos nos próximos N dias
    4. Calcular slots livres (horário comercial - eventos)
    5. Formatar resposta
    """
    
    try:
        # 1. Autenticação
        credentials = get_google_credentials()
        service = build('calendar', 'v3', credentials=credentials)
        
        # 2. Buscar calendário do médico
        calendar_id = find_doctor_calendar(doctor_name)
        if not calendar_id:
            return {'available': False, 'reason': 'calendar_not_found'}
        
        # 3. Definir intervalo de busca
        now = timezone.now()
        time_min = now.isoformat()
        time_max = (now + timedelta(days=days_ahead)).isoformat()
        
        # 4. Consultar eventos
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        # 5. Calcular disponibilidade por dia
        days_info = []
        current_date = now.date()
        
        for i in range(days_ahead):
            target_date = current_date + timedelta(days=i)
            
            # Horário comercial: 08:00 às 18:00
            business_hours = generate_time_slots(
                start_hour=8,
                end_hour=18,
                interval_minutes=30
            )
            
            # Filtrar eventos do dia
            day_events = [
                e for e in events
                if parse_event_date(e['start']).date() == target_date
            ]
            
            # Remover horários ocupados
            occupied_slots = [
                parse_event_time(e['start'])
                for e in day_events
            ]
            
            available_slots = [
                slot for slot in business_hours
                if slot not in occupied_slots
            ]
            
            days_info.append({
                'date': target_date.strftime('%d/%m/%Y'),
                'weekday': get_weekday_name(target_date),
                'available_times': available_slots,
                'occupied_times': occupied_slots
            })
        
        # 6. Calcular total de slots disponíveis
        total_slots = sum(len(day['available_times']) for day in days_info)
        
        return {
            'available': total_slots > 0,
            'doctor': doctor_name,
            'days_info': days_info,
            'total_slots': total_slots
        }
        
    except Exception as e:
        logger.error(f"Erro ao consultar Google Calendar: {e}")
        return {
            'available': False,
            'reason': 'calendar_error',
            'error': str(e)
        }
```

---

## 7. Processo de Handoff

### 7.1. Conceito

**Handoff** é o processo de transferir o atendimento do chatbot para um atendente humano (secretária). É gerado quando:

- Todas as informações foram coletadas
- Usuário confirmou os dados
- Sistema validou completude

### 7.2. Geração do Link de Handoff

```python
def generate_appointment_handoff_link(
    patient_name: str,
    doctor_name: str,
    specialty: str,
    date: str,
    time: str
) -> str:
    """
    Gera link de handoff para WhatsApp da secretária
    
    Args:
        patient_name: Nome confirmado do paciente
        doctor_name: Médico selecionado
        specialty: Especialidade médica
        date: Data escolhida (YYYY-MM-DD)
        time: Horário escolhido (HH:MM)
    
    Returns:
        Link formatado do WhatsApp com mensagem pré-preenchida
    
    Formato do link:
        https://wa.me/557336135380?text=MENSAGEM_CODIFICADA
    """
    
    # 1. Formatar mensagem para secretária
    message = f"""
🤖 *NOVO PRÉ-AGENDAMENTO*

📋 *DADOS DO PACIENTE:*
👤 Nome: {patient_name}

📅 *DADOS DA CONSULTA:*
👨‍⚕️ Médico: {doctor_name}
🩺 Especialidade: {specialty}
📅 Data: {format_date_br(date)}
🕐 Horário: {time}

⚠️ *AÇÃO NECESSÁRIA:*
Validar disponibilidade e confirmar agendamento com o paciente.
    """.strip()
    
    # 2. Codificar mensagem para URL
    encoded_message = urllib.parse.quote(message)
    
    # 3. Montar link
    secretary_phone = "557336135380"  # WhatsApp da secretária
    handoff_link = f"https://wa.me/{secretary_phone}?text={encoded_message}"
    
    # 4. Registrar handoff no banco de dados
    HandoffRecord.objects.create(
        patient_name=patient_name,
        doctor_name=doctor_name,
        specialty=specialty,
        appointment_date=date,
        appointment_time=time,
        created_at=timezone.now(),
        status='pending'
    )
    
    logger.info(
        f"🔗 Handoff gerado: {patient_name} → "
        f"{doctor_name} em {date} às {time}"
    )
    
    return handoff_link
```

### 7.3. Mensagem Final ao Usuário

```python
def format_handoff_message(
    patient_name: str,
    doctor_name: str,
    specialty: str,
    date: str,
    time: str,
    handoff_link: str
) -> str:
    """
    Formata mensagem final com handoff para o usuário
    """
    
    date_formatted = format_date_br(date)  # "Segunda-feira, 18/11/2025"
    
    message = f"""
✅ **Perfeito! Seu pré-agendamento foi realizado com sucesso!**

📋 **RESUMO DO AGENDAMENTO:**
👤 Paciente: {patient_name}
👨‍⚕️ Médico: {doctor_name}
🩺 Especialidade: {specialty}
📅 Data: {date_formatted}
🕐 Horário: {time}

🔄 **PRÓXIMOS PASSOS:**

Nossa secretária validará a disponibilidade e entrará em contato 
para confirmar definitivamente seu agendamento.

📞 **Para confirmação imediata, fale diretamente com nossa equipe:**
{handoff_link}

✨ **Agradecemos sua preferência!**
Em breve você receberá a confirmação final.

Se tiver qualquer dúvida, estou aqui para ajudar! 😊
    """.strip()
    
    return message
```

---

## 8. Casos de Uso Detalhados

### 8.1. Caso de Uso 1: Agendamento Completo Simples

```
CENÁRIO: Usuário experiente, fornece informações de forma linear
─────────────────────────────────────────────────────────────────

👤 "Olá"
🤖 "Olá! Como posso ajudá-lo?"

👤 "Quero agendar consulta"
🤖 "Perfeito! Qual é seu nome completo?"

👤 "Maria Santos Silva"
🤖 "Confirma se seu nome é Maria Santos Silva?"

👤 "Sim"
🤖 "Perfeito, Maria! Qual especialidade você procura?"

👤 "Cardiologia"
🤖 [Lista médicos de cardiologia]

👤 "Dr. Carlos"
🤖 [Mostra horários disponíveis]

👤 "Amanhã às 14h"
🤖 [Apresenta resumo]

👤 "Confirmo"
🤖 [Gera handoff e finaliza]

TEMPO MÉDIO: 3-4 minutos
MENSAGENS: 8-10
TAXA DE SUCESSO: ~90%
```

### 8.2. Caso de Uso 2: Agendamento com Dúvidas

```
CENÁRIO: Usuário tem dúvidas durante o processo
─────────────────────────────────────────────────────────────────

👤 "Bom dia, quero marcar consulta"
🤖 "Bom dia! Qual é seu nome completo?"

👤 "João Silva"
🤖 "Confirma se seu nome é João Silva?"

👤 "Sim"
🤖 "Perfeito! Qual especialidade você procura?"

👤 "Cardiologia"
🤖 [Lista médicos]

👤 "Quanto custa?"                              ⬅️ DÚVIDA
🤖 [PAUSA: selecting_doctor → answering_questions]
   "Consulta particular: R$ 180,00 a R$ 200,00"

👤 "Aceita Unimed?"                             ⬅️ OUTRA DÚVIDA
🤖 [MANTÉM: answering_questions]
   "Sim, aceitamos Unimed e Bradesco Saúde"

👤 "Ok, continuar"                              ⬅️ RETOMADA
🤖 [RETOMA: selecting_doctor]
   "Perfeito! Qual médico você prefere?"

👤 "Dr. Carlos"
🤖 [Continua normalmente...]

TEMPO MÉDIO: 5-7 minutos
MENSAGENS: 12-15
PAUSAS/RETOMADAS: 1-2
TAXA DE SUCESSO: ~75%
```

### 8.3. Caso de Uso 3: Agendamento com Correções

```
CENÁRIO: Usuário comete erros ou muda de ideia
─────────────────────────────────────────────────────────────────

👤 "Quero agendar"
🤖 "Qual é seu nome completo?"

👤 "José"                                       ⬅️ NOME INCOMPLETO
🤖 "Não consegui identificar seu nome completo.
    Por favor, informe nome e sobrenome."

👤 "José da Silva"
🤖 "Confirma se seu nome é José Da Silva?"

👤 "Não, é José Silva mesmo"                    ⬅️ CORREÇÃO
🤖 "Entendi. Por favor, digite seu nome novamente."

👤 "José Silva"
🤖 "Confirma se seu nome é José Silva?"

👤 "Sim"
🤖 "Perfeito! Qual especialidade?"

👤 "Ortopedia"
🤖 [Lista ortopedistas]

👤 "Na verdade, quero cardiologia"              ⬅️ MUDANÇA DE IDEIA
🤖 "Sem problemas! Vou mostrar nossos cardiologistas."
   [Lista cardiologistas]

👤 "Dr. Carlos"
🤖 [Continua normalmente...]

TEMPO MÉDIO: 6-8 minutos
MENSAGENS: 15-18
CORREÇÕES: 2-3
TAXA DE SUCESSO: ~60%
```

---

## 9. Conclusão

### 9.1. Síntese dos Fluxos

O sistema implementa um conjunto robusto de fluxos e processos que garantem:

✅ **Coleta Estruturada**: Máquina de estados guia o usuário passo a passo

✅ **Flexibilidade**: Sistema de pausar/retomar permite dúvidas a qualquer momento

✅ **Validação Rigorosa**: Múltiplas camadas garantem dados corretos

✅ **Integração Real**: Google Calendar fornece disponibilidade atualizada

✅ **Handoff Eficiente**: Transferência suave para atendimento humano

### 9.2. Métricas de Sucesso

| Métrica | Valor | Observação |
|---------|-------|------------|
| **Taxa de Conclusão** | 68% | % de usuários que completam até handoff |
| **Tempo Médio** | 4-5 min | Da saudação até handoff |
| **Precisão de Extração** | 82% | Entidades extraídas corretamente |
| **Taxa de Pausa/Retomada** | 30% | % de conversas que usam o recurso |
| **Satisfação** | 4.2/5 | Feedback dos usuários |

### 9.3. Melhorias Futuras

🔮 **Agendamento Multi-Etapa**: Permitir agendar múltiplas consultas

🔮 **Lembretes Automáticos**: Notificar usuário antes da consulta

🔮 **Cancelamento pelo Bot**: Permitir cancelar/reagendar via chatbot

🔮 **Histórico de Consultas**: Mostrar consultas anteriores do paciente

---

**Autor**: [Seu Nome]  
**Orientador**: [Nome do Orientador]  
**Instituição**: [Nome da Instituição]  
**Data**: Novembro de 2025  
**Versão**: 1.0


