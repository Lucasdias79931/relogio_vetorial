Tarefa:
Implementar quatro processos com Pyro: P1, P2, P3, P4.

Cada processo deve:

Executar eventos locais com intervalos arbitrários de até 5 segundos (≤ 5s).

Enviar mensagens para outros processos em alguns desses eventos.

Receber mensagens e atualizar o relógio vetorial.

Registrar cada evento em um log local, com:

Identificador do evento (ex.: P1-E3),

Tipo de evento (local, envio, recebimento),

Valor do relógio vetorial após o evento.

A execução deve durar entre 1 a 2 minutos, de forma contínua, para que vários eventos ocorram naturalmente.


