# Melhorias da P1

Revisão do MVP da P1 antes da etapa avançada (Aula 13).
Complete com os comentários da correção da P1 feita pelo professor.

| # | Problema na P1 | Situação |
|---|----------------|----------|
| 1 | Qualquer pessoa acessava e cadastrava livros: não havia login. | Corrigido: todas as telas usam `@login_required` e a API exige autenticação. |
| 2 | O CRUD estava incompleto: só listar e cadastrar, sem editar nem excluir. | Corrigido: telas de editar e excluir, sempre filtradas pela organização. |
| 3 | Os três templates repetiam todo o `<head>` (código duplicado). | Corrigido: `core/templates/base.html` e os templates usam `{% extends %}`. |
| 4 | `SECRET_KEY` e configuração do banco escritas direto no `settings.py`. | Corrigido: lidas do `.env`, que fica fora do Git (`.env.example` documenta). |
| 5 | `autor` é texto livre: o mesmo autor pode ser digitado de jeitos diferentes, e não dá para listar livros por autor. | Corrigido: model `Autor` da organização; o livro escolhe o autor numa lista que só mostra os da própria organização. |
| 6 | `ano` aceita qualquer número (negativo, 3000...). | Pendente: validação no model, que passa a valer no form, no Admin e na API. |
