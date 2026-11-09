# Acervo - mini-SaaS de bibliotecas

Várias bibliotecas usam o mesmo sistema,
mas cada uma só vê os próprios livros.


## Como rodar

1. Criar o ambiente virtual (só na primeira vez):

       python -m venv .venv

2. Ativar o ambiente virtual:

       .venv\Scripts\Activate.ps1

3. Instalar as dependências:

       pip install -r requirements.txt

4. Atualizar o banco de dados:

       python manage.py migrate

5. Criar um usuário administrador:

       python manage.py createsuperuser

6. Ligar o servidor:

       python manage.py runserver

7. Abrir no navegador:

       http://127.0.0.1:8000/


## Primeiro uso (no Admin)

Entre em http://127.0.0.1:8000/admin/ e:

1. Crie duas organizações: "Biblioteca A" e "Biblioteca B".
2. Crie dois usuários: "ana" e "bruno".
3. Crie um Perfil ligando "ana" à Biblioteca A.
4. Crie um Perfil ligando "bruno" à Biblioteca B.
5. Crie um Perfil para o seu administrador também.

Atenção: usuário sem Perfil não consegue usar o sistema.

Cada Perfil tem um papel:

- Administrador: pode tudo, inclusive excluir livros.
- Operador: cadastra e edita, mas não exclui.

Antes de cadastrar livros, cadastre os autores em /autores/.


## Testes automáticos

    python manage.py test

No final deve aparecer "OK".


## Roteiro de isolamento (Aula 14)

Entre como "ana" e confira:

- [ ] A lista mostra só os livros da Biblioteca A.
- [ ] Abrir /livros/ID-DE-UM-LIVRO-DA-B/editar/ dá erro 404.
- [ ] Um livro cadastrado fica na Biblioteca A.
- [ ] Abrir /api/livros/ID-DE-UM-LIVRO-DA-B/ dá erro 404.
- [ ] No cadastro de livro, só aparecem autores da Biblioteca A.
- [ ] Um operador não vê o botão "Excluir".


## Usar PostgreSQL (opcional)

Sem configurar nada, o projeto usa SQLite.
Para trocar para PostgreSQL:

1. Crie um banco vazio chamado "biblioteca" no pgAdmin.
2. Copie o arquivo de exemplo:

       copy .env.example .env

3. Abra o .env e coloque a sua senha em DB_PASSWORD.
4. Rode de novo os passos 4, 5 e 6 de "Como rodar".


## Endereços

- /              página inicial
- /livros/       lista de livros
- /autores/      lista e cadastro de autores
- /admin/        painel do administrador
- /api/livros/   API em JSON


## Pastas

- core/          organizações, perfis e login
- acervo/        livros e autores (telas, API e testes)
- biblioteca/    configurações do projeto
