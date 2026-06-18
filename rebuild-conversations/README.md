# Recuperador de Histórico de Conversas (Antigravity IDE)

Este utilitário resolve o problema clássico em que a IDE **Antigravity** (a bifurcação do VS Code criada pelo Google) para de exibir ou "perde" o histórico de conversas passadas na barra lateral ("Past Conversations" ou "Search all convos").

---

## 🔍 O Problema (A Causa Raiz)

Descobrimos o comportamento interno de como o Antigravity IDE gerencia o histórico de conversas:

1.  **Chave Protobuf no Banco de Dados:** O dropdown de conversas recentes na barra lateral é populado a partir de um objeto codificado em Protobuf e serializado como Base64 na chave `antigravityUnifiedStateSync.trajectorySummaries` dentro do banco SQLite de configurações globais da IDE (`state.vscdb`).
2.  **Dessincronização de Workspace:** Se você abrir uma conversa e o workspace dela não estiver mapeado corretamente ou se as datas/identificadores do histórico corromperem por falhas de sincronização na nuvem, a IDE remove as conversas da lista visual, embora os arquivos físicos de log continuem existindo no disco (na pasta `%USERPROFILE%\.gemini\antigravity-ide\brain`).
3.  **Sobregravação do Cache em Memória (O Grande Obstáculo):** 
    > [!WARNING]
    > A IDE mantém as configurações em cache ativo na memória RAM enquanto está sendo executada. Se tentarmos atualizar o banco SQLite `state.vscdb` com a IDE aberta, ela simplesmente **ignora** as alterações físicas no disco e, no momento em que você fecha a IDE ou recarrega a janela (Reload Window), ela grava o cache antigo da memória de volta para o disco, apagando qualquer correção externa.

---

## 🛠️ A Solução

A solução consiste em ler os arquivos físicos de log diretamente das pastas de dados (`.gemini/antigravity-ide/brain`), inferir o workspace correspondente a partir das referências de arquivos em Markdown de cada conversa e reconstruir a chave Protobuf de indexação no banco SQLite. 

Tudo isso **deve ser executado obrigatoriamente com a IDE totalmente fechada**.

### Conteúdo desta Pasta:

1.  **`rebuild_conversations.py`**: O script core em Python. Ele localiza as pastas do Antigravity, lê todos os UUIDs de conversas, reconstrói o protobuf serializado com timestamps válidos e atualiza o `state.vscdb`.
2.  **`non_interactive_rebuild.py`**: Um wrapper em Python que executa o script acima alimentando-o com as entradas padrão, automatizando o mapeamento de workspace das conversas baseando-se nos artefatos locais.
3.  **`recuperar_conversas.bat`**: Um script em lote (`.bat`) do Windows para execução rápida em 1 clique.

---

## 🚀 Como Executar (Instruções de Uso)

1.  **FECHE O ANTIGRAVITY IDE COMPLETAMENTE.** 
    *   *Dica:* Feche pelo botão `X` da janela e certifique-se no Gerenciador de Tarefas do Windows que nenhum processo chamado `Antigravity` ou `VS Code` da IDE permaneceu rodando.
2.  Dê dois cliques no arquivo **`recuperar_conversas.bat`**.
3.  O console do Windows se abrirá. Pressione qualquer tecla para confirmar que fechou a IDE e iniciar a execução.
4.  O script rodará em menos de 3 segundos e atualizará o banco de dados.
5.  Abra o **Antigravity IDE** novamente. Suas conversas antigas estarão ordenadas por data e visíveis no menu.
