from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('receitas/', views.lista_receitas, name='lista_receitas'),
    path('receitas/nova/', views.nova_receita, name='nova_receita'),
    path('despesas/', views.lista_despesas, name='lista_despesas'),
    path('despesas/nova/', views.nova_despesa, name='nova_despesa'),
    path('contas/', views.lista_contas, name='lista_contas'),
]