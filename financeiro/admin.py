from django.contrib import admin
from .models import (
    Categoria,
    Conta,
    Receita,
    Despesa,
    EmprestimoCartao,
    ParcelaEmprestimo,
)


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo')
    list_filter = ('tipo',)
    search_fields = ('nome',)


@admin.register(Conta)
class ContaAdmin(admin.ModelAdmin):
<<<<<<< HEAD
    list_display = ('nome', 'tipo', 'saldo_inicial', 'possui_cartao_credito', 'dias_antes_fechamento_fatura', 'dia_vencimento_fatura')
=======
    list_display = ('nome', 'tipo', 'saldo_inicial', 'possui_cartao_credito', 'dia_fechamento_fatura', 'dia_vencimento_fatura')
>>>>>>> fd0bd6b736464bfe364d04a0b39eca147ad3875e
    list_filter = ('tipo', 'possui_cartao_credito')
    search_fields = ('nome',)


@admin.register(Receita)
class ReceitaAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'valor', 'data', 'categoria', 'conta', 'recebido')
    list_filter = ('recebido', 'categoria', 'conta', 'data')
    search_fields = ('descricao',)


@admin.register(Despesa)
class DespesaAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'valor', 'data', 'categoria', 'conta', 'pago')
    list_filter = ('pago', 'categoria', 'conta', 'data')
    search_fields = ('descricao',)


@admin.register(EmprestimoCartao)
class EmprestimoCartaoAdmin(admin.ModelAdmin):
    list_display = ('pessoa', 'cartao_utilizado', 'conta_recebimento', 'descricao', 'valor_total', 'quantidade_parcelas', 'data_compra')
    list_filter = ('cartao_utilizado', 'conta_recebimento', 'data_compra')
    search_fields = ('pessoa', 'descricao', 'banco', 'cartao_utilizado__nome')


@admin.register(ParcelaEmprestimo)
class ParcelaEmprestimoAdmin(admin.ModelAdmin):
    list_display = ('emprestimo', 'numero', 'valor', 'vencimento', 'pago', 'data_pagamento', 'receita_gerada')
    list_filter = ('pago', 'vencimento')
    search_fields = ('emprestimo__pessoa', 'emprestimo__descricao', 'emprestimo__banco', 'emprestimo__cartao_utilizado__nome')
