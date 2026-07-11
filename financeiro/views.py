from django.shortcuts import render, redirect
from django.db.models import Sum
from .models import Conta, Receita, Despesa
from django.shortcuts import redirect
from .forms import ReceitaForm, DespesaForm


def dashboard(request):
    total_receitas = Receita.objects.filter(recebido=True).aggregate(
        total=Sum('valor')
    )['total'] or 0

    total_despesas = Despesa.objects.filter(pago=True).aggregate(
        total=Sum('valor')
    )['total'] or 0

    saldo = total_receitas - total_despesas

    contas = Conta.objects.all()
    ultimas_receitas = Receita.objects.order_by('-data')[:5]
    ultimas_despesas = Despesa.objects.order_by('-data')[:5]

    contexto = {
        'total_receitas': total_receitas,
        'total_despesas': total_despesas,
        'saldo': saldo,
        'contas': contas,
        'ultimas_receitas': ultimas_receitas,
        'ultimas_despesas': ultimas_despesas,
    }

    return render(request, 'financeiro/dashboard.html', contexto)


def lista_receitas(request):
    receitas = Receita.objects.order_by('-data')

    contexto = {
        'receitas': receitas,
    }

    return render(request, 'financeiro/lista_receitas.html', contexto)

def lista_despesas(request):
    despesas = Despesa.objects.order_by('-data')

    contexto = {
        'despesas': despesas,
    }

    return render(request, 'financeiro/lista_despesas.html', contexto)

def nova_receita(request):
    if request.method == 'POST':
        form = ReceitaForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('lista_receitas')
    else:
        form = ReceitaForm()

    contexto = {
        'form': form,
    }

    return render(request, 'financeiro/form_receita.html', contexto)

def nova_despesa(request):
    if request.method == 'POST':
        form = DespesaForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('lista_despesas')
    else:
        form = DespesaForm()

    contexto = {
        'form': form,
    }

    return render(request, 'financeiro/form_despesa.html', contexto)

def lista_contas(request):
    contas = Conta.objects.order_by('nome')

    contexto = {
        'contas': contas,
    }

    return render(request, 'financeiro/lista_contas.html', contexto)