# Patch para Extensão GitHub Pull Requests (Antigravity IDE)

Este patch corrige a incompatibilidade que impede a extensão oficial do **GitHub Pull Requests & Issues** (`github.vscode-pull-request-github`, versão `0.126.0-universal`) de ser ativada ou carregar os Pull Requests no **Antigravity IDE** (o fork da Google baseado no VS Code).

---

## 🔍 O Problema (Causa Raiz)

Quando instalada no Antigravity IDE, a extensão oficial do GitHub falha silenciosamente na aba lateral ou reporta erros de ativação. Ao debugar o log do desenvolvedor da IDE, identificamos duas causas distintas:

### 1. Incompatibilidade de APIs Propostas de Chat (`package.json`)
A extensão do GitHub tenta injetar botões e menus integrados com o GitHub Copilot Chat nas seções `chat/chatSessions` e `chat/input/editing/sessionToolbar`. Como essas APIs de Chat propostas não são permitidas ou suportadas de forma aberta pela arquitetura de segurança do Antigravity IDE, o carregamento de todo o manifesto da extensão é **rejeitado**, impedindo sua inicialização.

### 2. Erro de Renderização de Rótulos em Markdown (`extension.js`)
No código compilado e empacotado da extensão (`dist/extension.js`), a extensão tenta instanciar rótulos de itens de árvore usando MarkdownString:
```javascript
M={label:new r.MarkdownString(this._getLabel(),!0)}
b={label:new r.MarkdownString(`$(check) ${l}`,!0)}
```
No motor do Antigravity, as labels de itens da barra lateral de árvore esperam estritamente strings puras em vez de objetos Markdown completos estruturados dessa forma. A tentativa de renderizar esse objeto causa uma quebra de tipo no interpretador da IDE, impedindo a exibição das seções de Pull Requests.

---

## 🛠️ A Solução

Desenvolvemos um script em Node.js (`patch_extension.js`) que limpa automaticamente as duas inconsistências em todas as instâncias instaladas da extensão (nas pastas de dados locais `.antigravity` e `.antigravity-ide`).

O script realiza as seguintes alterações automatizadas:
1.  Remove as chaves problemáticas `chat/chatSessions` e `chat/input/editing/sessionToolbar` da seção de contribuições de menus no `package.json` da extensão.
2.  Patcheia o bundle `dist/extension.js` convertendo as instâncias de `MarkdownString` em strings limpas tradicionais (`this._getLabel()` e `` `$(check) ${l}` ``).

---

## 🚀 Como Executar

1.  Abra o terminal de sua preferência.
2.  Navegue até esta pasta e execute o script de diagnóstico para verificar o estado atual:
    ```bash
    node check_extension.js
    ```
3.  Execute o script de patch para aplicar as correções:
    ```bash
    node patch_extension.js
    ```
4.  Após a execução bem-sucedida, abra a IDE Antigravity, abra a Paleta de Comandos (`Ctrl + Shift + P`) e execute o comando **`Developer: Reload Window`** (Recarregar Janela) ou reinicie o aplicativo.

Pronto! A aba lateral do GitHub passará a carregar seus Pull Requests normalmente.
