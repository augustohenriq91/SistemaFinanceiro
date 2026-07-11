from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum
from django.db.models.deletion import ProtectedError
from decimal import Decimal
from datetime import date
from .models import Conta, Receita, Despesa, Categoria, EmprestimoCartao, ParcelaEmprestimo
from .forms import ReceitaForm, DespesaForm, ContaForm, CategoriaForm, EmprestimoCartaoForm


def adicionar_meses(data, meses):
    mes = data.month - 1 + meses
    ano = data.year + mes // 12
    mes = mes % 12 + 1
    dias_por_mes = [31, 29 if ano % 4 == 0 and (ano % 100 != 0 or ano % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    dia = min(data.day, dias_por_mes[mes - 1])
    return data.replace(year=ano, month=mes, day=dia)


def data_com_dia_seguro(data_base, dia):
    dia_seguro = max(1, min(dia, 31))
    dias_por_mes = [31, 29 if data_base.year % 4 == 0 and (data_base.year % 100 != 0 or data_base.year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return data_base.replace(day=min(dia_seguro, dias_por_mes[data_base.month - 1]))


def data_vencimento_fatura(data_compra, dia_fechamento, dia_vencimento):
    mes_fatura = data_compra

    if data_compra.day > dia_fechamento:
        mes_fatura = adicionar_meses(data_compra, 1)

    mes_vencimento = mes_fatura
    if dia_vencimento <= dia_fechamento:
        mes_vencimento = adicionar_meses(mes_fatura, 1)

    return data_com_dia_seguro(mes_vencimento, dia_vencimento)


def gerar_parcelas_emprestimo(emprestimo):
    emprestimo.parcelas.all().delete()
    cartao = emprestimo.cartao_utilizado
    dia_fechamento = cartao.dia_fechamento_fatura if cartao else 1
    dia_vencimento = cartao.dia_vencimento_fatura if cartao else emprestimo.dia_vencimento_cartao
    quantidade = emprestimo.quantidade_parcelas
    valor_base = (emprestimo.valor_total / Decimal(quantidade)).quantize(Decimal('0.01'))
    total_parcial = valor_base * quantidade
    ajuste = emprestimo.valor_total - total_parcial

    for numero in range(1, quantidade + 1):
        valor = valor_base
        if numero == quantidade:
            valor += ajuste

        ParcelaEmprestimo.objects.create(
            emprestimo=emprestimo,
            numero=numero,
            valor=valor,
            vencimento=adicionar_meses(
                data_vencimento_fatura(
                    emprestimo.data_compra,
                    dia_fechamento,
                    dia_vencimento
                ),
                numero - 1
            ),
        )


def dashboard(request):
    total_receitas = Receita.objects.filter(recebido=True).aggregate(
        total=Sum('valor')
    )['total'] or 0

    total_receitas_pendentes = Receita.objects.filter(recebido=False).aggregate(
        total=Sum('valor')
    )['total'] or 0

    total_despesas = Despesa.objects.filter(pago=True).aggregate(
        total=Sum('valor')
    )['total'] or 0

    total_despesas_pendentes = Despesa.objects.filter(pago=False).aggregate(
        total=Sum('valor')
    )['total'] or 0

    saldo = total_receitas - total_despesas

    contas = Conta.objects.all()
    saldo_total_contas = 0

    for conta in contas:
        receitas_conta = Receita.objects.filter(
            conta=conta,
            recebido=True
        ).aggregate(total=Sum('valor'))['total'] or 0

        despesas_conta = Despesa.objects.filter(
            conta=conta,
            pago=True
        ).aggregate(total=Sum('valor'))['total'] or 0

        saldo_total_contas += conta.saldo_inicial + receitas_conta - despesas_conta

    ultimas_receitas = Receita.objects.order_by('-data')[:5]
    ultimas_despesas = Despesa.objects.order_by('-data')[:5]
    receitas_pendentes = Receita.objects.filter(recebido=False).order_by('data')[:5]
    despesas_pendentes = Despesa.objects.filter(pago=False).order_by('data')[:5]
    hoje = date.today()
    parcelas_cartao_mes = ParcelaEmprestimo.objects.select_related(
        'emprestimo',
        'emprestimo__cartao_utilizado',
        'emprestimo__conta_recebimento',
    ).filter(
        pago=False,
        vencimento__year=hoje.year,
        vencimento__month=hoje.month,
    ).order_by('vencimento', 'emprestimo__pessoa', 'numero')
    total_cartao_mes_pendente = parcelas_cartao_mes.aggregate(total=Sum('valor'))['total'] or 0

    contexto = {
        'total_receitas': total_receitas,
        'total_receitas_pendentes': total_receitas_pendentes,
        'total_despesas': total_despesas,
        'total_despesas_pendentes': total_despesas_pendentes,
        'saldo': saldo,
        'saldo_total_contas': saldo_total_contas,
        'contas': contas,
        'ultimas_receitas': ultimas_receitas,
        'ultimas_despesas': ultimas_despesas,
        'receitas_pendentes': receitas_pendentes,
        'despesas_pendentes': despesas_pendentes,
        'parcelas_cartao_mes': parcelas_cartao_mes,
        'total_cartao_mes_pendente': total_cartao_mes_pendente,
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

def lista_emprestimos_cartao(request):
    emprestimos = EmprestimoCartao.objects.select_related('cartao_utilizado', 'conta_recebimento').order_by('-data_compra')
    parcelas = ParcelaEmprestimo.objects.select_related('emprestimo', 'emprestimo__cartao_utilizado', 'emprestimo__conta_recebimento').order_by('vencimento', 'emprestimo__pessoa', 'numero')
    total_emprestado = emprestimos.aggregate(total=Sum('valor_total'))['total'] or 0
    total_pago = ParcelaEmprestimo.objects.filter(pago=True).aggregate(total=Sum('valor'))['total'] or 0
    total_pendente = ParcelaEmprestimo.objects.filter(pago=False).aggregate(total=Sum('valor'))['total'] or 0

    contexto = {
        'emprestimos': emprestimos,
        'parcelas': parcelas,
        'total_emprestado': total_emprestado,
        'total_pago': total_pago,
        'total_pendente': total_pendente,
    }

    return render(request, 'financeiro/lista_emprestimos_cartao.html', contexto)

def novo_emprestimo_cartao(request):
    if request.method == 'POST':
        form = EmprestimoCartaoForm(request.POST)

        if form.is_valid():
            emprestimo = form.save(commit=False)
            emprestimo.banco = emprestimo.cartao_utilizado.nome
            emprestimo.dia_vencimento_cartao = emprestimo.cartao_utilizado.dia_vencimento_fatura
            emprestimo.save()
            gerar_parcelas_emprestimo(emprestimo)
            return redirect('lista_emprestimos_cartao')
    else:
        form = EmprestimoCartaoForm()

    contexto = {
        'form': form,
    }

    return render(request, 'financeiro/form_emprestimo_cartao.html', contexto)

def editar_emprestimo_cartao(request, emprestimo_id):
    emprestimo = get_object_or_404(EmprestimoCartao, id=emprestimo_id)

    if request.method == 'POST':
        form = EmprestimoCartaoForm(request.POST, instance=emprestimo)

        if form.is_valid():
            emprestimo = form.save(commit=False)
            emprestimo.banco = emprestimo.cartao_utilizado.nome
            emprestimo.dia_vencimento_cartao = emprestimo.cartao_utilizado.dia_vencimento_fatura
            emprestimo.save()
            gerar_parcelas_emprestimo(emprestimo)
            return redirect('lista_emprestimos_cartao')
    else:
        form = EmprestimoCartaoForm(instance=emprestimo)

    contexto = {
        'form': form,
        'emprestimo': emprestimo,
    }

    return render(request, 'financeiro/form_emprestimo_cartao.html', contexto)

def excluir_emprestimo_cartao(request, emprestimo_id):
    emprestimo = get_object_or_404(EmprestimoCartao, id=emprestimo_id)

    if request.method == 'POST':
        emprestimo.delete()
        return redirect('lista_emprestimos_cartao')

    contexto = {
        'emprestimo': emprestimo,
    }

    return render(request, 'financeiro/confirmar_exclusao_emprestimo_cartao.html', contexto)

def alternar_pagamento_parcela(request, parcela_id):
    parcela = get_object_or_404(ParcelaEmprestimo, id=parcela_id)

    if request.method == 'POST':
        if parcela.pago:
            if parcela.receita_gerada:
                parcela.receita_gerada.delete()
            parcela.pago = False
            parcela.data_pagamento = None
            parcela.receita_gerada = None
        else:
            if not parcela.emprestimo.conta_recebimento:
                messages.error(
                    request,
                    'Defina uma conta de recebimento antes de marcar esta parcela como paga.'
                )
                return redirect('lista_emprestimos_cartao')

            categoria, _ = Categoria.objects.get_or_create(
                nome='Pagamento cartao emprestado',
                tipo='receita'
            )

            receita = Receita.objects.create(
                descricao=f'Pagamento cartao - {parcela.emprestimo.pessoa} ({parcela.numero}/{parcela.emprestimo.quantidade_parcelas})',
                valor=parcela.valor,
                data=date.today(),
                categoria=categoria,
                conta=parcela.emprestimo.conta_recebimento,
                recebido=True,
            )

            parcela.pago = True
            parcela.data_pagamento = date.today()
            parcela.receita_gerada = receita

        parcela.save()

    return redirect('lista_emprestimos_cartao')
