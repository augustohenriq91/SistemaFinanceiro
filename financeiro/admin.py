from django.contrib import admin
from .models import (
    Categoria,
    Conta,
    Receita,
    Despesa,
    EmprestimoCartao,
    ParcelaEmprestimo,
    AtivoInvestimento,
    CotacaoAtivo,
)


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo', 'usuario')
    list_filter = ('tipo', 'usuario')
    search_fields = ('nome', 'usuario__username', 'usuario__first_name', 'usuario__last_name')


@admin.register(Conta)
class ContaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo', 'saldo_inicial', 'banco_principal', 'possui_cartao_credito', 'dias_antes_fechamento_fatura', 'dia_vencimento_fatura', 'usuario')
    list_filter = ('tipo', 'banco_principal', 'possui_cartao_credito', 'usuario')
    search_fields = ('nome', 'usuario__username', 'usuario__first_name', 'usuario__last_name')


@admin.register(Receita)
class ReceitaAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'valor', 'data', 'categoria', 'conta', 'recebido', 'usuario')
    list_filter = ('recebido', 'categoria', 'conta', 'data', 'usuario')
    search_fields = ('descricao', 'usuario__username', 'usuario__first_name', 'usuario__last_name')


@admin.register(Despesa)
class DespesaAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'valor', 'data', 'categoria', 'conta', 'pago', 'despesa_fixa', 'tipo_recorrencia', 'parcela_atual', 'quantidade_parcelas', 'parcelas_ja_pagas', 'usuario')
    list_filter = ('pago', 'despesa_fixa', 'tipo_recorrencia', 'categoria', 'conta', 'data', 'usuario')
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


@admin.register(AtivoInvestimento)
class AtivoInvestimentoAdmin(admin.ModelAdmin):
    list_display = ('ticker', 'nome', 'tipo', 'mercado', 'conta', 'quantidade', 'preco_medio', 'cotacao_atual', 'cotacao_atualizada_em', 'usuario')
    list_filter = ('tipo', 'mercado', 'conta', 'usuario')
    search_fields = ('ticker', 'nome', 'conta__nome', 'usuario__username', 'usuario__first_name', 'usuario__last_name')


@admin.register(CotacaoAtivo)
class CotacaoAtivoAdmin(admin.ModelAdmin):
    list_display = ('ativo', 'valor', 'fonte', 'criada_em')
    list_filter = ('fonte', 'criada_em', 'ativo__usuario')
    search_fields = ('ativo__ticker', 'ativo__nome', 'ativo__usuario__username')
