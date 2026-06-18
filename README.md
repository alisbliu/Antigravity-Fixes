# 🌌 Antigravity IDE Fixes & Patches

Uma coletânea de correções, patches de compatibilidade e utilitários de código aberto para a IDE **Antigravity** (o fork oficial do VS Code desenvolvido pelo Google).

Este repositório foi criado de forma totalmente pública e transparente para documentar, explicar e resolver problemas comuns enfrentados pela comunidade ao utilizar a IDE e suas extensões.

---

## 📦 Correções Disponíveis

Atualmente, o repositório conta com as seguintes correções prontas para uso:

| Correção / Pasta | Descrição | Tecnologia |
| :--- | :--- | :--- |
| 🔄 **[rebuild-conversations](./rebuild-conversations/)** | Restaura o histórico de conversas antigas ("Past Conversations" ou "Search all convos") que desaparecem misteriosamente devido a sobregravações no banco de dados SQLite (`state.vscdb`) da IDE. | Python / Windows Batch |
| 🐛 **[github-pr-extension-patch](./github-pr-extension-patch/)** | Corrige o crash e a falha na ativação da extensão oficial **GitHub Pull Requests & Issues** na IDE Antigravity, contornando a incompatibilidade do tipo `MarkdownString` e APIs de Chat propostas. | Node.js |

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
