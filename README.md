# 🌌 Antigravity IDE Fixes & Patches

Uma coletânea de correções, patches de compatibilidade e utilitários de código aberto para a IDE **Antigravity** (o fork oficial do VS Code desenvolvido pelo Google).

Este repositório foi criado de forma totalmente pública e transparente para documentar, explicar e resolver problemas comuns enfrentados pela comunidade ao utilizar a IDE e suas extensões.

---

## 📦 Correções Disponíveis

Atualmente, o repositório conta com as seguintes correções prontas para uso:

| Correção / Pasta | Descrição | Tecnologia |
| :--- | :--- | :--- |
| 🔄 **[rebuild-conversations](./rebuild-conversations/)** | Restaura o histórico de conversas antigas ("Past Conversations" ou "Search all convos") que desaparecem misteriosamente devido a sobregravações no banco de dados SQLite (`state.vscdb`) da IDE. | Python / Windows Batch |
| 🔄 **[sync-conversations](./sync-conversations/)** | Sincroniza e normaliza o histórico do Antigravity 2.0 entre PCs (Pessoal e Notebook) usando placeholders neutros e Git. Contém utilitários para **recuperar páginas de bancos corrompidos** e **isolar conversas incompatíveis de versões mais recentes** da IDE. | Python / VBScript / Batch |
| 🐛 **[github-pr-extension-patch](./github-pr-extension-patch/)** | Corrige o crash e a falha na ativação da extensão oficial **GitHub Pull Requests & Issues** na IDE Antigravity, contornando a incompatibilidade do tipo `MarkdownString` e APIs de Chat propostas. | Node.js |

---

## 🔬 Descobertas Técnicas e Causa Raiz de Crashes Recentes

Durante a manutenção e sincronização do histórico do Antigravity, documentamos duas causas críticas de instabilidade e crashes automáticos da IDE (reloading/port restart):

### 1. Corrupção Física de Bancos de Dados (SQLite Malformed Pages)
*   **Problema:** Operações de sincronização com a IDE aberta ou interrupções abruptas podem corromper fisicamente as páginas do banco de dados SQLite de conversas individuais (causando o erro `disk image is malformed`).
*   **Impacto:** Qualquer tentativa da IDE de ler a conversa corrompida trava o servidor de linguagem ou exibe erros de leitura.
*   **Solução (`repair_sqlite_robust.py`):** Desenvolvemos um algoritmo que lê os registros de forma robusta e sequencial nas tabelas `trajectory_metadata_blob` e `steps`, extraindo o máximo possível de dados linha por linha e descartando as páginas corrompidas, gerando um banco de dados substituto 100% íntegro e legível.

### 2. Incompatibilidade de Tipos de Passos em Versões Anteriores (`StepHeader.Type()` panic)
*   **Problema:** Versões mais novas da IDE Antigravity (como v2.2.1) gravam novos tipos de passos (`step_type`) no banco de dados para gerenciar execuções avançadas do agente (como passos `31, 33, 38, 90, 91, 138`).
*   **Impacto:** Se esses bancos forem copiados para um computador rodando uma versão anterior do Language Server (como v2.0.6), o backend falha ao deserializar os metadados do passo no protobuf Go, retornando um ponteiro `nil` para o `Header`. Em seguida, ao tentar rodar filtros de histórico (como `shouldFilterRejectedHunks`), o backend chama `StepHeader.Type()` em um ponteiro nulo, gerando pânico em nível de sistema (`panic: runtime error: invalid memory address or nil pointer dereference`). Isso derruba o Language Server instantaneamente e força a IDE a reiniciar e recarregar a tela em outra porta.
*   **Solução (`move_all_unsupported_dbs.py` & `clean_backup_repo.py`):** Criamos ferramentas que varrem os bancos locais para detectar passos incompatíveis e movê-los para um diretório isolado (`unsupported_dbs`), regenerando em seguida o arquivo do índice global (`agyhub_summaries_proto.pb`) para manter a IDE perfeitamente estável com as demais conversas.

---

## 🛡️ Segurança e Transparência

Entendemos que executar scripts que alteram arquivos locais e configurações de banco de dados da sua IDE exige extrema confiança. Por isso, este repositório segue diretrizes estritas:

1.  **Código Aberto e Legível:** Todos os scripts de correção são escritos em scripts simples e puros de **Python** ou **JavaScript/Node.js**. Não há pacotes empacotados, binários fechados (`.exe`) ou dependências externas pesadas.
2.  **Explicação Granular:** Cada subpasta contém um arquivo `README.md` detalhado explicando exatamente **qual é a causa raiz do bug**, **por que ele acontece**, e **o que cada linha de código do script faz**.
3.  **Backups Automáticos:** O script de restauração de conversas cria automaticamente uma cópia de segurança antes de aplicar qualquer alteração no banco de dados SQLite local, permitindo desfazer o processo a qualquer momento.

---

## 🤝 Como Contribuir

Se você encontrou outro bug, extensão incompatível ou desenvolveu um patch útil para a IDE Antigravity:

1.  Faça um **Fork** deste repositório.
2.  Crie uma branch para a sua correção: `git checkout -b feature/minha-correcao`.
3.  Crie uma pasta com o nome da correção contendo:
    *   O script/código da correção.
    *   Um arquivo `README.md` explicando o problema, a causa raiz e como rodar a solução.
4.  Abra um **Pull Request** detalhando sua alteração!
