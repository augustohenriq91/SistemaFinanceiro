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
    list_display = ('nome', 'tipo', 'usuario')
    list_filter = ('tipo', 'usuario')
    search_fields = ('nome', 'usuario__username', 'usuario__first_name', 'usuario__last_name')


@admin.register(Conta)
class ContaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo', 'saldo_inicial', 'possui_cartao_credito', 'dias_antes_fechamento_fatura', 'dia_vencimento_fatura', 'usuario')
    list_filter = ('tipo', 'possui_cartao_credito', 'usuario')
    search_fields = ('nome', 'usuario__username', 'usuario__first_name', 'usuario__last_name')


@admin.register(Receita)
class ReceitaAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'valor', 'data', 'categoria', 'conta', 'recebido', 'usuario')
    list_filter = ('recebido', 'categoria', 'conta', 'data', 'usuario')
    search_fields = ('descricao', 'usuario__username', 'usuario__first_name', 'usuario__last_name')


@admin.register(Despesa)
class DespesaAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'valor', 'data', 'categoria', 'conta', 'pago', 'usuario')
    list_filter = ('pago', 'categoria', 'conta', 'data', 'usuario')
    search_fields = ('descricao', 'usuario__username', 'usuario__first_name', 'usuario__last_name')


@admin.register(EmprestimoCartao)
class EmprestimoCartaoAdmin(admin.ModelAdmin):
    list_display = ('pessoa', 'cartao_utilizado', 'conta_recebimento', 'descricao', 'valor_total', 'quantidade_parcelas', 'data_compra', 'usuario')
    list_filter = ('cartao_utilizado', 'conta_recebimento', 'data_compra', 'usuario')
    search_fields = ('pessoa', 'descricao', 'banco', 'cartao_utilizado__nome', 'usuario__username', 'usuario__first_name', 'usuario__last_name')


@admin.register(ParcelaEmprestimo)
class ParcelaEmprestimoAdmin(admin.ModelAdmin):
    list_display = ('emprestimo', 'numero', 'valor', 'vencimento', 'pago', 'data_pagamento', 'receita_gerada')
    list_filter = ('pago', 'vencimento', 'emprestimo__usuario')
    search_fields = ('emprestimo__pessoa', 'emprestimo__descricao', 'emprestimo__banco', 'emprestimo__cartao_utilizado__nome', 'emprestimo__usuario__username')
