from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from django.db.models.deletion import ProtectedError
from .models import Conta, Receita, Despesa, Categoria
from .forms import ReceitaForm, DespesaForm, ContaForm, CategoriaForm


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

def editar_receita(request, receita_id):
    receita = get_object_or_404(Receita, id=receita_id)

    if request.method == 'POST':
        form = ReceitaForm(request.POST, instance=receita)

        if form.is_valid():
            form.save()
            return redirect('lista_receitas')
    else:
        form = ReceitaForm(instance=receita)

    contexto = {
        'form': form,
        'receita': receita,
    }

    return render(request, 'financeiro/form_receita.html', contexto)

def excluir_receita(request, receita_id):
    receita = get_object_or_404(Receita, id=receita_id)

    if request.method == 'POST':
        receita.delete()
        return redirect('lista_receitas')
    
    contexto = {
        'receita': receita,
    }

    return render(request, 'financeiro/confirmar_exclusao_receita.html', contexto)

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

def editar_despesa(request, despesa_id):
    despesa = get_object_or_404(Despesa, id=despesa_id)

    if request.method == 'POST':
        form = DespesaForm(request.POST, instance=despesa)

        if form.is_valid():
            form.save()
            return redirect('lista_despesas')
    else:
        form = DespesaForm(instance=despesa)

    contexto = {
        'form': form,
        'despesa': despesa,
    }

    return render(request, 'financeiro/form_despesa.html', contexto)

def excluir_despesa(request, despesa_id):
    despesa = get_object_or_404(Despesa, id=despesa_id)

    if request.method == 'POST':
        despesa.delete()
        return redirect('lista_despesas')

    contexto = {
        'despesa': despesa,
    }

    return render(request, 'financeiro/confirmar_exclusao_despesa.html', contexto)

def lista_contas(request):
    contas = Conta.objects.order_by('nome')
    contas_com_saldo = []

    for conta in contas:
        total_receitas = Receita.objects.filter(
            conta=conta,
            recebido=True
        ).aggregate(total=Sum('valor'))['total'] or 0

        total_despesas = Despesa.objects.filter(
            conta=conta,
            pago=True
        ).aggregate(total=Sum('valor'))['total'] or 0

        saldo_atual = conta.saldo_inicial + total_receitas - total_despesas

        contas_com_saldo.append({
            'conta': conta,
            'total_receitas': total_receitas,
            'total_despesas': total_despesas,
            'saldo_atual': saldo_atual,
        })

    contexto = {
        'contas_com_saldo': contas_com_saldo,
    }

    return render(request, 'financeiro/lista_contas.html', contexto)

def nova_conta(request):
    if request.method == 'POST':
        form = ContaForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('lista_contas')
    else:
        form = ContaForm()

    contexto = {
        'form': form,
    }

    return render(request, 'financeiro/form_conta.html', contexto)

def editar_conta(request, conta_id):
    conta = get_object_or_404(Conta, id=conta_id)

    if request.method == 'POST':
        form = ContaForm(request.POST, instance=conta)

        if form.is_valid():
            form.save()
            return redirect('lista_contas')
    else:
        form = ContaForm(instance=conta)

    contexto = {
        'form': form,
        'conta': conta,
    }

    return render(request, 'financeiro/form_conta.html', contexto)

def excluir_conta(request, conta_id):
    conta = get_object_or_404(Conta, id=conta_id)
    erro = None

    if request.method == 'POST':
        try:
            conta.delete()
            return redirect('lista_contas')
        except ProtectedError:
            erro = 'Esta conta possui receitas ou despesas vinculadas e nao pode ser excluida.'

    contexto = {
        'conta': conta,
        'erro': erro,
    }

    return render(request, 'financeiro/confirmar_exclusao_conta.html', contexto)

def lista_categorias(request):
    categorias = Categoria.objects.order_by('tipo', 'nome')

    contexto = {
        'categorias': categorias,
    }

    return render(request, 'financeiro/lista_categorias.html', contexto)

def nova_categoria(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('lista_categorias')
    else:
        form = CategoriaForm()

    contexto = {
        'form': form,
    }

    return render(request, 'financeiro/form_categoria.html', contexto)

def editar_categoria(request, categoria_id):
    categoria = get_object_or_404(Categoria, id=categoria_id)

    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=categoria)

        if form.is_valid():
            form.save()
            return redirect('lista_categorias')
    else:
        form = CategoriaForm(instance=categoria)

    contexto = {
        'form': form,
        'categoria': categoria,
    }

    return render(request, 'financeiro/form_categoria.html', contexto)

def excluir_categoria(request, categoria_id):
    categoria = get_object_or_404(Categoria, id=categoria_id)
    erro = None

    if request.method == 'POST':
        try:
            categoria.delete()
            return redirect('lista_categorias')
        except ProtectedError:
            erro = 'Esta categoria possui receitas ou despesas vinculadas e nao pode ser excluida.'

    contexto = {
        'categoria': categoria,
        'erro': erro,
    }

    return render(request, 'financeiro/confirmar_exclusao_categoria.html', contexto)
