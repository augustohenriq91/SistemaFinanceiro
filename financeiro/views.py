from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum
from django.db.models.deletion import ProtectedError
from decimal import Decimal
from datetime import date, datetime
from urllib.parse import urlencode
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


def data_vencimento_fatura(data_compra, dias_antes_vencimento, dia_vencimento):
    dia_fechamento = max(1, dia_vencimento - dias_antes_vencimento)
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
    contas_com_saldo = []

    for conta in contas:
        receitas_conta = Receita.objects.filter(
            conta=conta,
            recebido=True
        ).aggregate(total=Sum('valor'))['total'] or 0

        despesas_conta = Despesa.objects.filter(
            conta=conta,
            pago=True
        ).aggregate(total=Sum('valor'))['total'] or 0

        saldo_atual_conta = conta.saldo_inicial + receitas_conta - despesas_conta
        saldo_total_contas += saldo_atual_conta

        contas_com_saldo.append({
            'conta': conta,
            'total_receitas': receitas_conta,
            'total_despesas': despesas_conta,
            'saldo_atual': saldo_atual_conta,
        })

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
    total_faturas_cartao = total_cartao_mes_pendente
    # Variação do saldo em relação ao mês anterior (net: receitas recebidas - despesas pagas)
    mes_atual_year = hoje.year
    mes_atual_month = hoje.month
    mes_anterior = adicionar_meses(hoje, -1)

    receitas_mes_atual = Receita.objects.filter(recebido=True, data__year=mes_atual_year, data__month=mes_atual_month).aggregate(total=Sum('valor'))['total'] or 0
    despesas_mes_atual = Despesa.objects.filter(pago=True, data__year=mes_atual_year, data__month=mes_atual_month).aggregate(total=Sum('valor'))['total'] or 0
    net_mes_atual = receitas_mes_atual - despesas_mes_atual

    receitas_mes_anterior = Receita.objects.filter(recebido=True, data__year=mes_anterior.year, data__month=mes_anterior.month).aggregate(total=Sum('valor'))['total'] or 0
    despesas_mes_anterior = Despesa.objects.filter(pago=True, data__year=mes_anterior.year, data__month=mes_anterior.month).aggregate(total=Sum('valor'))['total'] or 0
    net_mes_anterior = receitas_mes_anterior - despesas_mes_anterior

    saldo_variacao_percent = None
    saldo_variacao_change = net_mes_atual - net_mes_anterior
    try:
        if net_mes_anterior != 0:
            saldo_variacao_percent = float((net_mes_atual - net_mes_anterior) / (abs(net_mes_anterior)) * 100.0)
    except Exception:
        saldo_variacao_percent = None

    if saldo_variacao_percent is not None:
        saldo_variacao_percent = round(saldo_variacao_percent, 1)

    contexto = {
        'total_receitas': total_receitas,
        'total_receitas_pendentes': total_receitas_pendentes,
        'total_despesas': total_despesas,
        'total_despesas_pendentes': total_despesas_pendentes,
        'saldo': saldo,
        'saldo_total_contas': saldo_total_contas,
        'contas': contas,
        'contas_com_saldo': contas_com_saldo,
        'ultimas_receitas': ultimas_receitas,
        'ultimas_despesas': ultimas_despesas,
        'receitas_pendentes': receitas_pendentes,
        'despesas_pendentes': despesas_pendentes,
        'parcelas_cartao_mes': parcelas_cartao_mes,
        'total_cartao_mes_pendente': total_cartao_mes_pendente,
        'total_faturas_cartao': total_faturas_cartao,
        'saldo_variacao_percent': saldo_variacao_percent,
        'saldo_variacao_change': saldo_variacao_change,
        'saldo_variacao_class': ('positive' if (saldo_variacao_percent is not None and saldo_variacao_percent > 0) or (saldo_variacao_percent is None and saldo_variacao_change > 0) else ('negative' if (saldo_variacao_percent is not None and saldo_variacao_percent < 0) or (saldo_variacao_percent is None and saldo_variacao_change < 0) else 'neutral')),
    }

    return render(request, 'financeiro/dashboard.html', contexto)


def lista_receitas(request):
    receitas = Receita.objects.order_by('-data')
    q = request.GET.get('q', '').strip()
    categoria_id = request.GET.get('categoria', '')
    conta_id = request.GET.get('conta', '')
    status = request.GET.get('status', '')
    data = request.GET.get('data', '')

    if q:
        receitas = receitas.filter(descricao__icontains=q)
    if categoria_id:
        receitas = receitas.filter(categoria_id=categoria_id)
    if conta_id:
        receitas = receitas.filter(conta_id=conta_id)
    if status == 'recebido':
        receitas = receitas.filter(recebido=True)
    elif status == 'pendente':
        receitas = receitas.filter(recebido=False)
    if data:
        dt = None
        try:
            dt = datetime.strptime(data, '%d/%m/%Y').date()
        except Exception:
            try:
                # also accept ISO format if present
                dt = datetime.strptime(data, '%Y-%m-%d').date()
            except Exception:
                dt = None
        if dt:
            receitas = receitas.filter(data=dt)

    categorias = Categoria.objects.filter(tipo='receita').order_by('nome')
    contas = Conta.objects.order_by('nome')
    paginator = Paginator(receitas, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    querystring = urlencode({k: v for k, v in request.GET.items() if v and k != 'page'})

    contexto = {
        'receitas': page_obj,
        'categorias': categorias,
        'contas': contas,
        'page_obj': page_obj,
        'querystring': querystring,
        'filtro_q': q,
        'filtro_categoria': categoria_id,
        'filtro_conta': conta_id,
        'filtro_status': status,
        'filtro_data': data,
    }

    return render(request, 'financeiro/lista_receitas.html', contexto)

def lista_despesas(request):
    despesas = Despesa.objects.order_by('-data')
    q = request.GET.get('q', '').strip()
    categoria_id = request.GET.get('categoria', '')
    conta_id = request.GET.get('conta', '')
    status = request.GET.get('status', '')
    data = request.GET.get('data', '')

    if q:
        despesas = despesas.filter(descricao__icontains=q)
    if categoria_id:
        despesas = despesas.filter(categoria_id=categoria_id)
    if conta_id:
        despesas = despesas.filter(conta_id=conta_id)
    if status == 'pago':
        despesas = despesas.filter(pago=True)
    elif status == 'pendente':
        despesas = despesas.filter(pago=False)
    if data:
        dt = None
        try:
            dt = datetime.strptime(data, '%d/%m/%Y').date()
        except Exception:
            try:
                dt = datetime.strptime(data, '%Y-%m-%d').date()
            except Exception:
                dt = None
        if dt:
            despesas = despesas.filter(data=dt)

    categorias = Categoria.objects.filter(tipo='despesa').order_by('nome')
    contas = Conta.objects.order_by('nome')
    paginator = Paginator(despesas, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    querystring = urlencode({k: v for k, v in request.GET.items() if v and k != 'page'})

    contexto = {
        'despesas': page_obj,
        'categorias': categorias,
        'contas': contas,
        'page_obj': page_obj,
        'querystring': querystring,
        'filtro_q': q,
        'filtro_categoria': categoria_id,
        'filtro_conta': conta_id,
        'filtro_status': status,
        'filtro_data': data,
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
    q = request.GET.get('q', '').strip()
    tipo = request.GET.get('tipo', '')
    cartao = request.GET.get('cartao', '')

    if q:
        contas = contas.filter(nome__icontains=q)
    if tipo:
        contas = contas.filter(tipo=tipo)
    if cartao == 'sim':
        contas = contas.filter(possui_cartao_credito=True)
    elif cartao == 'nao':
        contas = contas.filter(possui_cartao_credito=False)

    paginator = Paginator(contas, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    querystring = urlencode({k: v for k, v in request.GET.items() if v and k != 'page'})

    contas_com_saldo = []

    for conta in page_obj:
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
        'tipos_conta': Conta.TIPO_CHOICES,
        'page_obj': page_obj,
        'querystring': querystring,
        'filtro_q': q,
        'filtro_tipo': tipo,
        'filtro_cartao': cartao,
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
    q = request.GET.get('q', '').strip()
    tipo = request.GET.get('tipo', '')

    if q:
        categorias = categorias.filter(nome__icontains=q)
    if tipo:
        categorias = categorias.filter(tipo=tipo)

    paginator = Paginator(categorias, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    querystring = urlencode({k: v for k, v in request.GET.items() if v and k != 'page'})

    contexto = {
        'categorias': page_obj,
        'page_obj': page_obj,
        'querystring': querystring,
        'filtro_q': q,
        'filtro_tipo': tipo,
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
    q = request.GET.get('q', '').strip()
    cartao_id = request.GET.get('cartao', '')
    status = request.GET.get('status', '')

    if q:
        emprestimos = emprestimos.filter(pessoa__icontains=q)
    if cartao_id:
        emprestimos = emprestimos.filter(cartao_utilizado_id=cartao_id)

    parcelas = ParcelaEmprestimo.objects.select_related('emprestimo', 'emprestimo__cartao_utilizado', 'emprestimo__conta_recebimento').order_by('vencimento', 'emprestimo__pessoa', 'numero')
    if status == 'pago':
        parcelas = parcelas.filter(pago=True)
    elif status == 'pendente':
        parcelas = parcelas.filter(pago=False)

    paginator = Paginator(parcelas, 10)
    parcelas_page = paginator.get_page(request.GET.get('page'))
    querystring = urlencode({k: v for k, v in request.GET.items() if v and k != 'page'})

    total_emprestado = emprestimos.aggregate(total=Sum('valor_total'))['total'] or 0
    total_pago = ParcelaEmprestimo.objects.filter(pago=True).aggregate(total=Sum('valor'))['total'] or 0
    total_pendente = ParcelaEmprestimo.objects.filter(pago=False).aggregate(total=Sum('valor'))['total'] or 0
    cartoes = Conta.objects.filter(possui_cartao_credito=True).order_by('nome')

    contexto = {
        'emprestimos': emprestimos,
        'parcelas': parcelas_page,
        'total_emprestado': total_emprestado,
        'total_pago': total_pago,
        'total_pendente': total_pendente,
        'cartoes': cartoes,
        'page_obj': parcelas_page,
        'querystring': querystring,
        'filtro_q': q,
        'filtro_cartao': cartao_id,
        'filtro_status': status,
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
