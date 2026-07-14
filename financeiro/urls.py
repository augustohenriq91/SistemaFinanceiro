from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views

urlpatterns = [
    path('', login_required(views.dashboard), name='dashboard'),
    path('relatorios/', login_required(views.relatorios), name='relatorios'),
    path('backup/', login_required(views.baixar_backup), name='baixar_backup'),
    path('receitas/', login_required(views.lista_receitas), name='lista_receitas'),
    path('receitas/nova/', login_required(views.nova_receita), name='nova_receita'),
    path('receitas/<int:receita_id>/editar/', login_required(views.editar_receita), name='editar_receita'),
    path('receitas/<int:receita_id>/excluir/', login_required(views.excluir_receita), name='excluir_receita'),
    path('receitas/<int:receita_id>/recebimento/', login_required(views.alternar_recebimento_receita), name='alternar_recebimento_receita'),
    path('despesas/', login_required(views.lista_despesas), name='lista_despesas'),
    path('despesas/nova/', login_required(views.nova_despesa), name='nova_despesa'),
    path('despesas/<int:despesa_id>/editar/', login_required(views.editar_despesa), name='editar_despesa'),
    path('despesas/<int:despesa_id>/excluir/', login_required(views.excluir_despesa), name='excluir_despesa'),
    path('despesas/<int:despesa_id>/pagamento/', login_required(views.alternar_pagamento_despesa), name='alternar_pagamento_despesa'),
    path('contas/', login_required(views.lista_contas), name='lista_contas'),
    path('contas/nova/', login_required(views.nova_conta), name='nova_conta'),
    path('contas/<int:conta_id>/editar/', login_required(views.editar_conta), name='editar_conta'),
    path('contas/<int:conta_id>/excluir/', login_required(views.excluir_conta), name='excluir_conta'),
    path('categorias/', login_required(views.lista_categorias), name='lista_categorias'),
    path('categorias/nova/', login_required(views.nova_categoria), name='nova_categoria'),
    path('categorias/<int:categoria_id>/editar/', login_required(views.editar_categoria), name='editar_categoria'),
    path('categorias/<int:categoria_id>/excluir/', login_required(views.excluir_categoria), name='excluir_categoria'),
    path('cartao-emprestado/', login_required(views.lista_emprestimos_cartao), name='lista_emprestimos_cartao'),
    path('cartao-emprestado/novo/', login_required(views.novo_emprestimo_cartao), name='novo_emprestimo_cartao'),
    path('cartao-emprestado/<int:emprestimo_id>/editar/', login_required(views.editar_emprestimo_cartao), name='editar_emprestimo_cartao'),
    path('cartao-emprestado/<int:emprestimo_id>/excluir/', login_required(views.excluir_emprestimo_cartao), name='excluir_emprestimo_cartao'),
    path('cartao-emprestado/parcela/<int:parcela_id>/pagar/', login_required(views.alternar_pagamento_parcela), name='alternar_pagamento_parcela'),
]
