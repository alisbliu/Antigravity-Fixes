# Sincronização Automatizada de Conversas (Antigravity 2.0)

Este utilitário resolve o problema de divergência e falta de sincronismo do histórico de conversas do **Antigravity 2.0** (a ferramenta de desenvolvimento agêntica baseada no Google Gemini) ao utilizá-la em múltiplos computadores (ex: PC Pessoal e Notebook da Empresa).

---

## 🔍 O Problema (A Causa Raiz)

O Antigravity 2.0 gerencia as conversas localmente no sistema usando arquivos de banco de dados SQLite (`.db`) e arquivos serializados Protobuf (`.pb`) dentro da pasta de dados da aplicação (`%USERPROFILE%\.gemini\antigravity\conversations\`). 

Cada conversa possui metadados internos gravados na tabela `trajectory_metadata_blob` que a vinculam de forma rígida a:
1. **URI do Workspace:** O caminho local da pasta aberta na IDE (ex: `file:///C:/Users/Eduardo/Documents/obsidian-personal-vault` ou `file:///E:/Cofre%20Eduardo%20%28Obsidian%29`).
2. **ID do Projeto (Project ID):** O UUID interno gerado pela IDE para aquele workspace (ex: `d90b1c26-...` ou `e1d2e2cc-...`).
3. **ID do Workspace (Workspace ID):** O identificador único de cache da IDE.

Por conta disso, **copiar os arquivos brutos diretamente de um computador para o outro não funciona**. O Antigravity do computador de destino simplesmente ignora as conversas importadas porque os caminhos de arquivos e IDs de projetos gravados no banco de dados da conversa não existem localmente.

---

## 🛠️ A Solução (Normalização por Placeholders)

Desenvolvemos um fluxo de sincronização bidirecional, transparente e agnóstico de máquina. O utilitário realiza a tradução dinâmica dos metadados das conversas usando placeholders intermediários salvos em um repositório Git de backup (ex: [antigravity-backup](https://github.com/alisbliu/antigravity-backup)).

### Como funciona:

1. **Ao Exportar (`--push`):** 
   O script lê os bancos de dados locais das conversas, decodifica a estrutura Protobuf de metadados, e substitui todas as informações específicas do computador por placeholders neutros:
   * `file:///E:/Cofre...` ➔ `{{WORKSPACE_URI}}`
   * `e1d2e2cc-...` ➔ `{{PROJECT_ID}}`
   * `fe29abba-...` ➔ `{{WORKSPACE_ID}}`
   Em seguida, copia esses arquivos normalizados para a pasta do repositório de backup.

2. **Ao Importar (`--pull`):**
   O script detecta automaticamente as configurações locais do projeto ativo (URI do workspace local e ID do projeto local) lendo os arquivos de configuração do Antigravity (`~/.gemini/config/projects/`). Ao copiar as conversas do repositório de backup para a pasta local da IDE, ele substitui os placeholders pelos valores reais da máquina atual.

---

## 📂 Estrutura dos Arquivos do Fix

* **`sync_antigravity.py`**: O script core em Python que realiza a decodificação/codificação genérica dos blobs Protobuf e atualiza as referências locais e placeholders.
* **`sync_auto.bat`**: Script Batch do Windows que coordena o fluxo git e as execuções de pull/push do Python de forma integrada.
* **`sync_silent.vbs`**: Script VBScript para executar o `.bat` em segundo plano de forma 100% silenciosa (invisível, sem abrir a janela preta do CMD).

---

## ⚙️ Como Instalar e Configurar (Passo a Passo)

### 1. Clonar o Repositório de Backup das Conversas
Em ambos os computadores, clone o seu repositório de backup (ex: `antigravity-backup`) na raiz da sua pasta de usuário (ou em outro local de sua preferência):
```bash
git clone https://github.com/seu-usuario/antigravity-backup.git "C:\Users\SeuUsuario\antigravity-backup"
```

### 2. Configurar o Agendamento Silencioso no Windows (Task Scheduler)
Para fazer o histórico de conversas sincronizar sozinho a cada 30 minutos sem nenhuma janela atrapalhando sua tela:

1. Abra o **Agendador de Tarefas (Task Scheduler)** do Windows.
2. No painel de ações da direita, clique em **Criar Tarefa Básica...**.
3. **Nome:** `Antigravity Conversations Sync`
4. **Disparador:** Selecione **Ao fazer logon** (ou Diariamente).
5. **Ação:** Selecione **Iniciar um programa**.
6. **Configurações:**
   * **Programa/script:** `wscript.exe`
   * **Adicione argumentos (opcional):** `"C:\Users\SeuUsuario\Antigravity-Fixes\sync-conversations\sync_silent.vbs"` *(Nota: Ajuste para o caminho real da pasta onde você colocou o VBScript)*
   * **Iniciar em (opcional):** `C:\Users\SeuUsuario\Antigravity-Fixes\sync-conversations\` *(Nota: Isso é crucial para o VBScript encontrar o arquivo .bat no mesmo diretório)*
7. Salve e conclua.
8. Abra as propriedades da tarefa criada para ajustar os disparadores:
   * Vá em **Disparadores** ➔ Selecione o disparador de logon ➔ Clique em **Editar...**.
   * Marque a opção **Repetir a tarefa a cada:** `30 minutos` (ou 1 hora) por tempo indeterminado.
   * Clique em **OK** para salvar.

Pronto! A partir de agora, ambas as máquinas sincronizarão o histórico de conversas automaticamente no plano de fundo.
