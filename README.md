# Sistema Financeiro Pessoal

Sistema web em Django para controle financeiro pessoal.

## Funcionalidades atuais

- Dashboard com resumo financeiro
- Layout moderno com menu lateral e estilo unificado
- Receitas: listar, criar, editar e excluir
- Despesas: listar, criar, editar e excluir
- Contas: listar, criar, editar e excluir
- Categorias: listar, criar, editar e excluir
- Cartão de Crédito: cadastrar pessoa, banco, valor usado e parcelas
- Controle mensal de parcelas do Cartão de Crédito
- Dia de vencimento do cartao em cada emprestimo
- Dashboard mostra quem ainda nao pagou parcelas com vencimento no mes atual
- Calculo de saldo por conta
- Confirmacao antes de excluir registros
- Painel administrativo do Django como apoio

## Como executar

No terminal, dentro da pasta `SistemaFinanceiro`, execute:

```powershell
.\venv\Scripts\Activate.ps1
python manage.py check
python manage.py runserver
```

Depois acesse:

```text
http://127.0.0.1:8000/
```

## Principais telas

```text
/                  Dashboard
/receitas/         Lista de receitas
/receitas/nova/    Nova receita
/despesas/         Lista de despesas
/despesas/nova/    Nova despesa
/contas/           Lista de contas
/contas/nova/      Nova conta
/categorias/       Lista de categorias
/categorias/nova/  Nova categoria
/cartao-emprestado/       Controle de cartao emprestado
/cartao-emprestado/novo/  Novo emprestimo no cartao
/admin/            Painel administrativo
```

## Observacao sobre exclusao

Contas e categorias que ja estejam vinculadas a receitas ou despesas nao podem ser excluidas diretamente. Isso protege o historico financeiro do sistema.
