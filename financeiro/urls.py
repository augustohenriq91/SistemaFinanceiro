from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('receitas/', views.lista_receitas, name='lista_receitas'),
    path('receitas/nova/', views.nova_receita, name='nova_receita'),
    path('receitas/<int:receita_id>/editar/', views.editar_receita, name='editar_receita'),
    path('receitas/<int:receita_id>/excluir/', views.excluir_receita, name='excluir_receita'),
    path('despesas/', views.lista_despesas, name='lista_despesas'),
    path('despesas/nova/', views.nova_despesa, name='nova_despesa'),
    path('despesas/<int:despesa_id>/editar/', views.editar_despesa, name='editar_despesa'),
    path('despesas/<int:despesa_id>/excluir/', views.excluir_despesa, name='excluir_despesa'),
    path('contas/', views.lista_contas, name='lista_contas'),
    path('contas/nova/', views.nova_conta, name='nova_conta'),
    path('contas/<int:conta_id>/editar/', views.editar_conta, name='editar_conta'),
    path('contas/<int:conta_id>/excluir/', views.excluir_conta, name='excluir_conta'),
    path('categorias/', views.lista_categorias, name='lista_categorias'),
    path('categorias/nova/', views.nova_categoria, name='nova_categoria'),
    path('categorias/<int:categoria_id>/editar/', views.editar_categoria, name='editar_categoria'),
    path('categorias/<int:categoria_id>/excluir/', views.excluir_categoria, name='excluir_categoria'),
]
