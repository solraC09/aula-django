# Acervo - sistema de biblioteca

Sistema web em Django para gerenciar o acervo de uma biblioteca:
livros, autores, usuários e um dashboard com relatórios.

Projeto da disciplina Laboratório de Programação Full Stack
(Engenharia de Software - Universidade de Vassouras).


## O que o sistema faz

- Cadastro e login de usuários.
- Livros: listar, buscar, filtrar, cadastrar, editar e excluir.
- Autores: listar, cadastrar, editar e excluir.
- Dashboard com indicadores, gráficos e filtro por período.
- Exportação dos livros em CSV (abre no Excel).
- API REST em JSON para livros e para o dashboard.

Por baixo, o sistema é multi-organização: cada dado pertence a uma
biblioteca e ninguém enxerga dados de outra. Na prática ele funciona
com uma biblioteca só, e todo usuário novo entra nela.


## Quem pode fazer o quê

Cada usuário tem um papel, definido no Perfil:

- Operador (padrão de quem se cadastra):
  - vê todos os livros e autores;
  - cadastra livros e autores;
  - edita e exclui só os livros que ele mesmo cadastrou;
  - vê o dashboard sem a série por mês e sem exportar.
- Administrador:
  - pode tudo, inclusive editar e excluir qualquer livro;
  - exclui autores (só os que não têm livros);
  - vê o dashboard completo e exporta o CSV.

O superusuário sempre conta como administrador.


## Como rodar

1. Criar o ambiente virtual (só na primeira vez):

       python -m venv .venv

2. Ativar o ambiente virtual:

       source .venv/Scripts/activate      (Git Bash)
       .venv\Scripts\Activate.ps1         (PowerShell)

3. Instalar as dependências:

       python -m pip install -r requirements.txt

4. Criar o arquivo de configuração e preencher (veja a seção abaixo):

       cp .env.example .env

5. Criar as tabelas no banco:

       python manage.py migrate

6. Criar o administrador (usa ADMIN_USUARIO e ADMIN_SENHA do .env):

       python manage.py garantir_admin

7. Ligar o servidor:

       python manage.py runserver

8. Abrir no navegador:

       http://127.0.0.1:8000/


## Configuração (.env)

O .env guarda senhas, por isso não vai para o Git.
O .env.example mostra todas as variáveis:

- SECRET_KEY: chave interna do Django (sessões, cookies).
  Gere uma com:

      python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

- DEBUG: True em desenvolvimento, False em produção.
- DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT: dados do PostgreSQL.
  Sem DB_NAME, o projeto usa SQLite (arquivo db.sqlite3).
- ADMIN_USUARIO, ADMIN_SENHA, ADMIN_EMAIL: o administrador fixo.
- BIBLIOTECA_NOME: nome da biblioteca, usado se ainda não existir nenhuma.
- SQL_LOG: True para ver no terminal cada consulta SQL (com DEBUG=True).


## Administrador fixo

O comando abaixo cria o administrador do .env, ou restaura a senha e
o papel dele se alguém tiver mexido:

    python manage.py garantir_admin

Esse usuário não pode ser apagado pelo Admin do Django.


## Endereços

- /                      página inicial
- /livros/               lista de livros (20 por página)
- /livros/novo/          cadastrar livro
- /autores/              lista e cadastro de autores
- /dashboard/            dashboard
- /dashboard/exportar.csv   exportar livros em CSV (administrador)
- /contas/login/         entrar
- /contas/cadastro/      criar conta
- /admin/                painel do Django (administrador)


## API

Todas as rotas exigem login e mostram só dados da sua biblioteca.

- GET    /api/livros/          lista os livros
- POST   /api/livros/          cadastra um livro
- GET    /api/livros/ID/       mostra um livro
- PUT    /api/livros/ID/       edita (dono do livro ou administrador)
- PATCH  /api/livros/ID/       edita parte (dono ou administrador)
- DELETE /api/livros/ID/       exclui (dono ou administrador)
- GET    /api/dashboard/       métricas do dashboard

O dashboard aceita o período na URL:

    /api/dashboard/?inicio=2026-01-01&fim=2026-03-31

Logado no navegador, abra /api/livros/ para testar pela própria página
do Django REST Framework.


## Dashboard

Responde às perguntas que o dono da biblioteca faria toda semana:

- Quantos livros tenho, quantos estão disponíveis e quantos autores?
  (cartões com os totais)
- Quais autores têm mais livros? (ranking dos 5 primeiros)
- Quantos livros entraram por mês? (gráfico, só administrador)
- Como o acervo se divide por categoria? (gráfico)

O filtro de início e fim vale para todos os números ao mesmo tempo, e
também para o CSV. Datas inválidas são ignoradas, sem erro.

Os gráficos usam Chart.js, carregado da internet (cdn.jsdelivr.net).
Sem internet, a página abre normalmente, só sem os gráficos.


## Testes

    python manage.py test

Os testes cobrem, entre outras coisas:

- isolamento entre bibliotecas (telas, API e dashboard);
- permissões de operador, dono do livro e administrador;
- cadastro de usuário e administrador fixo;
- validações (ano, autor repetido, datas do filtro);
- números do dashboard e conteúdo do CSV;
- quantidade de consultas SQL, para garantir que não há N+1.


## Ver as consultas SQL

Para conferir o que o Django manda para o banco, coloque no .env:

    DEBUG=True
    SQL_LOG=True

e rode o runserver. Cada página aberta mostra as consultas no terminal.


## Pastas

- biblioteca/   configurações do projeto (settings, urls)
- core/         organizações, perfis, login, cadastro, admin fixo,
                páginas de erro e o layout base
- acervo/       livros, autores, dashboard, API e testes
  - dashboard.py   cálculo das métricas
  - static/        CSS e o JavaScript dos gráficos


## Roteiro de isolamento (Aula 14)

Crie uma segunda biblioteca no Admin com um usuário nela, entre como
um usuário da primeira e confira:

- [ ] A lista mostra só os livros da sua biblioteca.
- [ ] Abrir /livros/ID-DE-UM-LIVRO-DA-OUTRA/editar/ dá erro 404.
- [ ] Um livro cadastrado fica na sua biblioteca.
- [ ] Abrir /api/livros/ID-DE-UM-LIVRO-DA-OUTRA/ dá erro 404.
- [ ] No cadastro de livro, só aparecem autores da sua biblioteca.
- [ ] O dashboard só conta livros da sua biblioteca.
- [ ] Um operador não vê o botão Excluir nos livros de outras pessoas.
