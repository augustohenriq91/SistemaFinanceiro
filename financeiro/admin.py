from django.contrib import admin
from .models import Categoria, Conta, Receita, Despesa


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo')
    list_filter = ('tipo',)
    search_fields = ('nome',)


@admin.register(Conta)
class ContaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo', 'saldo_inicial')
    list_filter = ('tipo',)
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