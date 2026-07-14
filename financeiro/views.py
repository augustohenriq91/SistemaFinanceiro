from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.db.models.deletion import ProtectedError
import json
from uuid import uuid4
from decimal import Decimal
from datetime import date, datetime, timedelta
from urllib.parse import urlencode
from .models import Conta, Receita, Despesa, Categoria, EmprestimoCartao, ParcelaEmprestimo
from .forms import ReceitaForm, DespesaForm, ContaForm, CategoriaForm, EmprestimoCartaoForm


MESES = [
    (1, 'Janeiro'),
    (2, 'Fevereiro'),
    (3, 'Março'),
    (4, 'Abril'),
    (5, 'Maio'),
    (6, 'Junho'),
    (7, 'Julho'),
    (8, 'Agosto'),
    (9, 'Setembro'),
    (10, 'Outubro'),
    (11, 'Novembro'),
    (12, 'Dezembro'),
]


def adicionar_meses(data, meses):
    mes = data.month - 1 + meses
    ano = data.year + mes // 12
    mes = mes % 12 + 1
    dias_por_mes = [31, 29 if ano % 4 == 0 and (ano % 100 != 0 or ano % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    dia = min(data.day, dias_por_mes[mes - 1])
    return data.replace(year=ano, month=mes, day=dia)


def fim_do_mes(data_base):
    return adicionar_meses(data_base.replace(day=1), 1) - timedelta(days=1)


def salvar_despesa_com_recorrencia(despesa):
    if not despesa.despesa_fixa or despesa.tipo_recorrencia == 'unica':
        despesa.despesa_fixa = False
        despesa.tipo_recorrencia = 'unica'
        despesa.quantidade_parcelas = None
        despesa.parcela_atual = None
        despesa.data_inicio_parcelamento = None
        despesa.parcelas_ja_pagas = 0
        despesa.grupo_recorrencia = ''
        despesa.save()
        return

    grupo = despesa.grupo_recorrencia or str(uuid4())
    descricao_base = despesa.descricao
    despesa.grupo_recorrencia = grupo

    if despesa.tipo_recorrencia == 'parcelada':
        quantidade = despesa.quantidade_parcelas or 1
        data_inicio = despesa.data_inicio_parcelamento or despesa.data
        parcelas_pagas = min(despesa.parcelas_ja_pagas or 0, quantidade)
        despesa.data = data_inicio
        despesa.parcela_atual = 1
        despesa.descricao = f'{descricao_base} (1/{quantidade})'
        despesa.pago = parcelas_pagas >= 1
        despesa.save()

        for numero in range(2, quantidade + 1):
            Despesa.objects.create(
                usuario=despesa.usuario,
                descricao=f'{descricao_base} ({numero}/{quantidade})',
                valor=despesa.valor,
                data=adicionar_meses(data_inicio, numero - 1),
                categoria=despesa.categoria,
                conta=despesa.conta,
                pago=numero <= parcelas_pagas,
                despesa_fixa=True,
                tipo_recorrencia='parcelada',
                quantidade_parcelas=quantidade,
                parcela_atual=numero,
                data_inicio_parcelamento=data_inicio,
                parcelas_ja_pagas=parcelas_pagas,
                grupo_recorrencia=grupo,
            )
        return

    despesa.tipo_recorrencia = 'recorrente'
    despesa.quantidade_parcelas = None
    despesa.parcela_atual = None
    despesa.data_inicio_parcelamento = None
    despesa.parcelas_ja_pagas = 0
    despesa.save()


def garantir_despesas_recorrentes(usuario, ate_data):
    grupos = (
        Despesa.objects
        .filter(
            usuario=usuario,
            despesa_fixa=True,
            tipo_recorrencia='recorrente',
        )
        .exclude(grupo_recorrencia='')
        .values_list('grupo_recorrencia', flat=True)
        .distinct()
    )

    for grupo in grupos:
        modelo = (
            Despesa.objects
            .filter(usuario=usuario, grupo_recorrencia=grupo, tipo_recorrencia='recorrente')
            .order_by('data', 'id')
            .first()
        )

        if not modelo or modelo.data > ate_data:
            continue

        meses = 1
        data_lancamento = adicionar_meses(modelo.data, meses)

        while data_lancamento <= ate_data and meses <= 240:
            ja_existe = Despesa.objects.filter(
                usuario=usuario,
                grupo_recorrencia=grupo,
                data__year=data_lancamento.year,
                data__month=data_lancamento.month,
            ).exists()

            if not ja_existe:
                Despesa.objects.create(
                    usuario=usuario,
                    descricao=modelo.descricao,
                    valor=modelo.valor,
                    data=data_lancamento,
                    categoria=modelo.categoria,
                    conta=modelo.conta,
                    pago=False,
                    despesa_fixa=True,
                    tipo_recorrencia='recorrente',
                    quantidade_parcelas=None,
                    parcela_atual=None,
                    grupo_recorrencia=grupo,
                )

            meses += 1
            data_lancamento = adicionar_meses(modelo.data, meses)


def data_com_dia_seguro(data_base, dia):
    dia_seguro = max(1, min(dia, 31))
    dias_por_mes = [31, 29 if data_base.year % 4 == 0 and (data_base.year % 100 != 0 or data_base.year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return data_base.replace(day=min(dia_seguro, dias_por_mes[data_base.month - 1]))


def interpretar_data_filtro(valor):
    if not valor:
        return None

    texto = str(valor).strip()

    for formato in ('%d/%m/%Y', '%Y-%m-%d'):
        try:
            return datetime.strptime(texto, formato).date()
        except ValueError:
            pass

    digitos = ''.join(ch for ch in texto if ch.isdigit())
    ano_atual = date.today().year

    if len(digitos) == 4:
        texto = f'{digitos[:2]}/{digitos[2:]}/{ano_atual}'
    elif len(digitos) == 6:
        ano = int(digitos[4:])
        ano += 2000 if ano < 70 else 1900
        texto = f'{digitos[:2]}/{digitos[2:4]}/{ano}'
    elif len(digitos) == 8:
        texto = f'{digitos[:2]}/{digitos[2:4]}/{digitos[4:]}'
    else:
        return None

    try:
        return datetime.strptime(texto, '%d/%m/%Y').date()
    except ValueError:
        return None


def data_vencimento_fatura(data_compra, dias_antes_vencimento, dia_vencimento):
    vencimento = data_com_dia_seguro(data_compra, dia_vencimento)

    if data_compra > vencimento:
        vencimento = data_com_dia_seguro(adicionar_meses(data_compra, 1), dia_vencimento)

    fechamento = vencimento - timedelta(days=dias_antes_vencimento)

    if data_compra > fechamento:
        vencimento = data_com_dia_seguro(adicionar_meses(vencimento, 1), dia_vencimento)

    return vencimento


def periodo_request(request):
    hoje = date.today()

    try:
        mes = int(request.GET.get('mes', hoje.month))
    except (TypeError, ValueError):
        mes = hoje.month

    try:
        ano = int(request.GET.get('ano', hoje.year))
    except (TypeError, ValueError):
        ano = hoje.year

    mes = max(1, min(mes, 12))
    ano = max(2000, min(ano, 2100))
    return ano, mes


def anos_disponiveis(usuario):
    anos = set()
    for model in (Receita, Despesa):
        for valor in model.objects.filter(usuario=usuario).dates('data', 'year'):
            anos.add(valor.year)
    for valor in EmprestimoCartao.objects.filter(usuario=usuario).dates('data_compra', 'year'):
        anos.add(valor.year)
    anos.add(date.today().year)
    return sorted(anos, reverse=True)


def gerar_parcelas_emprestimo(emprestimo):
    emprestimo.parcelas.all().delete()
    cartao = emprestimo.cartao_utilizado
    dias_antes_vencimento = cartao.dias_antes_fechamento_fatura if cartao else 1
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
                    dias_antes_vencimento,
                    dia_vencimento
                ),
                numero - 1
            ),
        )


def dashboard(request):
    usuario = request.user
    ano_selecionado, mes_selecionado = periodo_request(request)
    data_periodo = date(ano_selecionado, mes_selecionado, 1)
    garantir_despesas_recorrentes(usuario, fim_do_mes(data_periodo))

    receitas_periodo = Receita.objects.filter(usuario=usuario, data__year=ano_selecionado, data__month=mes_selecionado)
    despesas_periodo = Despesa.objects.filter(usuario=usuario, data__year=ano_selecionado, data__month=mes_selecionado)

    total_receitas = receitas_periodo.filter(recebido=True).aggregate(
        total=Sum('valor')
    )['total'] or 0

    total_receitas_pendentes = receitas_periodo.filter(recebido=False).aggregate(
        total=Sum('valor')
    )['total'] or 0

    total_despesas = despesas_periodo.filter(pago=True).aggregate(
        total=Sum('valor')
    )['total'] or 0

    total_despesas_pendentes = despesas_periodo.filter(pago=False).aggregate(
        total=Sum('valor')
    )['total'] or 0

    total_despesas_pendentes = Despesa.objects.filter(usuario=usuario, pago=False).aggregate(
        total=Sum('valor')
    )['total'] or 0

    saldo = total_receitas - total_despesas

    contas = Conta.objects.filter(usuario=usuario).order_by('nome')
    saldo_total_contas = 0
    contas_com_saldo = []

    for conta in contas:
        receitas_conta = Receita.objects.filter(
            usuario=usuario,
            conta=conta,
            recebido=True
        ).aggregate(total=Sum('valor'))['total'] or 0

        despesas_conta = Despesa.objects.filter(
            usuario=usuario,
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

    ultimas_receitas = receitas_periodo.order_by('-data')[:5]
    ultimas_despesas = despesas_periodo.order_by('-data')[:5]
    receitas_pendentes = receitas_periodo.filter(recebido=False).order_by('data')[:5]
    despesas_pendentes = despesas_periodo.filter(pago=False).order_by('data')[:5]
    hoje = date.today()
    despesas_vencidas = despesas_periodo.filter(pago=False, data__lt=hoje)
    total_despesas_vencidas = despesas_vencidas.aggregate(total=Sum('valor'))['total'] or 0
    quantidade_despesas_vencidas = despesas_vencidas.count()
    quantidade_receitas_pendentes = receitas_periodo.filter(recebido=False).count()
    proxima_despesa_pendente = despesas_periodo.filter(pago=False).order_by('data').first()
    parcelas_cartao_mes_base = ParcelaEmprestimo.objects.select_related(
        'emprestimo',
        'emprestimo__cartao_utilizado',
        'emprestimo__conta_recebimento',
    ).filter(
        emprestimo__usuario=usuario,
        vencimento__year=ano_selecionado,
        vencimento__month=mes_selecionado,
    ).order_by('vencimento', 'emprestimo__pessoa', 'numero')

    parcelas_cartao_mes = parcelas_cartao_mes_base.filter(pago=False)
    parcelas_cartao_mes_pagas = parcelas_cartao_mes_base.filter(pago=True)
    proximo_vencimento_cartao = parcelas_cartao_mes.first()
    total_cartao_mes_pendente = parcelas_cartao_mes.aggregate(total=Sum('valor'))['total'] or 0
    total_cartao_mes_pago = parcelas_cartao_mes_pagas.aggregate(total=Sum('valor'))['total'] or 0
    total_faturas_cartao = parcelas_cartao_mes_base.aggregate(total=Sum('valor'))['total'] or 0
    quantidade_parcelas_cartao_pendentes = parcelas_cartao_mes.count()
    pessoas_cartao_aberto = parcelas_cartao_mes.values('emprestimo__pessoa').annotate(
        total_aberto=Sum('valor'),
        parcelas_abertas=Count('id'),
    ).order_by('-total_aberto', 'emprestimo__pessoa')[:6]
    total_pessoas_cartao_aberto = parcelas_cartao_mes.values('emprestimo__pessoa').distinct().count()
    # Variação do saldo em relação ao mês anterior (net: receitas recebidas - despesas pagas)
    mes_atual_year = ano_selecionado
    mes_atual_month = mes_selecionado
    mes_anterior = adicionar_meses(data_periodo, -1)

    receitas_mes_atual = Receita.objects.filter(usuario=usuario, recebido=True, data__year=mes_atual_year, data__month=mes_atual_month).aggregate(total=Sum('valor'))['total'] or 0
    despesas_mes_atual = Despesa.objects.filter(usuario=usuario, pago=True, data__year=mes_atual_year, data__month=mes_atual_month).aggregate(total=Sum('valor'))['total'] or 0
    net_mes_atual = receitas_mes_atual - despesas_mes_atual

    receitas_mes_anterior = Receita.objects.filter(usuario=usuario, recebido=True, data__year=mes_anterior.year, data__month=mes_anterior.month).aggregate(total=Sum('valor'))['total'] or 0
    despesas_mes_anterior = Despesa.objects.filter(usuario=usuario, pago=True, data__year=mes_anterior.year, data__month=mes_anterior.month).aggregate(total=Sum('valor'))['total'] or 0
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
        'total_despesas_vencidas': total_despesas_vencidas,
        'quantidade_despesas_vencidas': quantidade_despesas_vencidas,
        'quantidade_receitas_pendentes': quantidade_receitas_pendentes,
        'proxima_despesa_pendente': proxima_despesa_pendente,
        'parcelas_cartao_mes': parcelas_cartao_mes,
        'parcelas_cartao_mes_pagas': parcelas_cartao_mes_pagas,
        'total_cartao_mes_pendente': total_cartao_mes_pendente,
        'total_cartao_mes_pago': total_cartao_mes_pago,
        'total_faturas_cartao': total_faturas_cartao,
        'quantidade_parcelas_cartao_pendentes': quantidade_parcelas_cartao_pendentes,
        'proximo_vencimento_cartao': proximo_vencimento_cartao,
        'pessoas_cartao_aberto': pessoas_cartao_aberto,
        'total_pessoas_cartao_aberto': total_pessoas_cartao_aberto,
        'meses': MESES,
        'anos': anos_disponiveis(usuario),
        'mes_selecionado': mes_selecionado,
        'ano_selecionado': ano_selecionado,
        'saldo_variacao_percent': saldo_variacao_percent,
        'saldo_variacao_change': saldo_variacao_change,
        'saldo_variacao_class': ('positive' if (saldo_variacao_percent is not None and saldo_variacao_percent > 0) or (saldo_variacao_percent is None and saldo_variacao_change > 0) else ('negative' if (saldo_variacao_percent is not None and saldo_variacao_percent < 0) or (saldo_variacao_percent is None and saldo_variacao_change < 0) else 'neutral')),
    }

    return render(request, 'financeiro/dashboard.html', contexto)


def relatorios(request):
    usuario = request.user
    try:
        ano = int(request.GET.get('ano', date.today().year))
    except (TypeError, ValueError):
        ano = date.today().year

    ano = max(2000, min(ano, 2100))
    garantir_despesas_recorrentes(usuario, date(ano, 12, 31))
    linhas_mensais = []

    for numero_mes, nome_mes in MESES:
        receitas_mes = Receita.objects.filter(
            usuario=usuario,
            recebido=True,
            data__year=ano,
            data__month=numero_mes,
        ).aggregate(total=Sum('valor'))['total'] or 0
        despesas_mes = Despesa.objects.filter(
            usuario=usuario,
            pago=True,
            data__year=ano,
            data__month=numero_mes,
        ).aggregate(total=Sum('valor'))['total'] or 0

        linhas_mensais.append({
            'mes': nome_mes,
            'receitas': receitas_mes,
            'despesas': despesas_mes,
            'saldo': receitas_mes - despesas_mes,
        })

    receitas_por_categoria = []
    for categoria in Categoria.objects.filter(usuario=usuario, tipo='receita').order_by('nome'):
        total = Receita.objects.filter(
            usuario=usuario,
            categoria=categoria,
            recebido=True,
            data__year=ano,
        ).aggregate(total=Sum('valor'))['total'] or 0
        if total:
            receitas_por_categoria.append({'categoria': categoria.nome, 'total': total})

    despesas_por_categoria = []
    for categoria in Categoria.objects.filter(usuario=usuario, tipo='despesa').order_by('nome'):
        total = Despesa.objects.filter(
            usuario=usuario,
            categoria=categoria,
            pago=True,
            data__year=ano,
        ).aggregate(total=Sum('valor'))['total'] or 0
        if total:
            despesas_por_categoria.append({'categoria': categoria.nome, 'total': total})

    total_receitas = sum(item['receitas'] for item in linhas_mensais)
    total_despesas = sum(item['despesas'] for item in linhas_mensais)

    contexto = {
        'ano': ano,
        'anos': anos_disponiveis(usuario),
        'linhas_mensais': linhas_mensais,
        'receitas_por_categoria': receitas_por_categoria,
        'despesas_por_categoria': despesas_por_categoria,
        'total_receitas': total_receitas,
        'total_despesas': total_despesas,
        'saldo_anual': total_receitas - total_despesas,
    }

    return render(request, 'financeiro/relatorios.html', contexto)


def baixar_backup(request):
    usuario = request.user
    dados = {
        'usuario': {
            'username': usuario.username,
            'nome': usuario.get_full_name(),
            'email': usuario.email,
        },
        'categorias': list(
            Categoria.objects.filter(usuario=usuario).values('id', 'nome', 'tipo')
        ),
        'contas': list(
            Conta.objects.filter(usuario=usuario).values(
                'id',
                'nome',
                'tipo',
                'saldo_inicial',
                'banco_principal',
                'possui_cartao_credito',
                'dias_antes_fechamento_fatura',
                'dia_vencimento_fatura',
            )
        ),
        'receitas': list(
            Receita.objects.filter(usuario=usuario).values(
                'id',
                'descricao',
                'valor',
                'data',
                'categoria_id',
                'conta_id',
                'recebido',
            )
        ),
        'despesas': list(
            Despesa.objects.filter(usuario=usuario).values(
                'id',
                'descricao',
                'valor',
                'data',
                'categoria_id',
                'conta_id',
                'pago',
            )
        ),
        'compras_cartao': list(
            EmprestimoCartao.objects.filter(usuario=usuario).values(
                'id',
                'pessoa',
                'banco',
                'cartao_utilizado_id',
                'conta_recebimento_id',
                'descricao',
                'valor_total',
                'quantidade_parcelas',
                'data_compra',
                'dia_vencimento_cartao',
                'observacao',
            )
        ),
        'parcelas_cartao': list(
            ParcelaEmprestimo.objects.filter(emprestimo__usuario=usuario).values(
                'id',
                'emprestimo_id',
                'numero',
                'valor',
                'vencimento',
                'pago',
                'data_pagamento',
                'receita_gerada_id',
            )
        ),
    }

    conteudo = json.dumps(dados, ensure_ascii=False, indent=2, default=str)
    filename = f'backup_financeiro_{usuario.username}_{datetime.now():%Y%m%d_%H%M%S}.json'
    response = HttpResponse(conteudo, content_type='application/json; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def lista_receitas(request):
    usuario = request.user
    receitas = Receita.objects.filter(usuario=usuario).order_by('-data')
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
        dt = interpretar_data_filtro(data)
        if dt:
            receitas = receitas.filter(data=dt)

    resumo_receitas = receitas.aggregate(
        total_filtrado=Sum('valor'),
        total_recebido=Sum('valor', filter=Q(recebido=True)),
        total_pendente=Sum('valor', filter=Q(recebido=False)),
        quantidade=Count('id'),
    )

    categorias = Categoria.objects.filter(usuario=usuario, tipo='receita').order_by('nome')
    contas = Conta.objects.filter(usuario=usuario).order_by('nome')
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
        'total_receitas_filtrado': resumo_receitas['total_filtrado'] or 0,
        'total_receitas_recebidas': resumo_receitas['total_recebido'] or 0,
        'total_receitas_pendentes': resumo_receitas['total_pendente'] or 0,
        'quantidade_receitas_filtradas': resumo_receitas['quantidade'] or 0,
    }

    return render(request, 'financeiro/lista_receitas.html', contexto)

def lista_despesas(request):
    usuario = request.user
    q = request.GET.get('q', '').strip()
    categoria_id = request.GET.get('categoria', '')
    conta_id = request.GET.get('conta', '')
    status = request.GET.get('status', '')
    data = request.GET.get('data', '')
    data_filtrada = interpretar_data_filtro(data) if data else None

    garantir_despesas_recorrentes(usuario, data_filtrada or date.today())

    despesas = Despesa.objects.filter(usuario=usuario).order_by('-data')

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
        if data_filtrada:
            despesas = despesas.filter(data=data_filtrada)

    resumo_despesas = despesas.aggregate(
        total_filtrado=Sum('valor'),
        total_pago=Sum('valor', filter=Q(pago=True)),
        total_pendente=Sum('valor', filter=Q(pago=False)),
        quantidade=Count('id'),
    )

    categorias = Categoria.objects.filter(usuario=usuario, tipo='despesa').order_by('nome')
    contas = Conta.objects.filter(usuario=usuario).order_by('nome')
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
        'total_despesas_filtrado': resumo_despesas['total_filtrado'] or 0,
        'total_despesas_pagas': resumo_despesas['total_pago'] or 0,
        'total_despesas_pendentes': resumo_despesas['total_pendente'] or 0,
        'quantidade_despesas_filtradas': resumo_despesas['quantidade'] or 0,
    }

    return render(request, 'financeiro/lista_despesas.html', contexto)

def nova_receita(request):
    if request.method == 'POST':
        form = ReceitaForm(request.POST, user=request.user)

        if form.is_valid():
            receita = form.save(commit=False)
            receita.usuario = request.user
            receita.save()
            return redirect('lista_receitas')
    else:
        form = ReceitaForm(user=request.user)

    contexto = {
        'form': form,
    }

    return render(request, 'financeiro/form_receita.html', contexto)

def editar_receita(request, receita_id):
    receita = get_object_or_404(Receita, id=receita_id, usuario=request.user)

    if request.method == 'POST':
        form = ReceitaForm(request.POST, instance=receita, user=request.user)

        if form.is_valid():
            form.save()
            return redirect('lista_receitas')
    else:
        form = ReceitaForm(instance=receita, user=request.user)

    contexto = {
        'form': form,
        'receita': receita,
    }

    return render(request, 'financeiro/form_receita.html', contexto)

def excluir_receita(request, receita_id):
    receita = get_object_or_404(Receita, id=receita_id, usuario=request.user)

    if request.method == 'POST':
        receita.delete()
        return redirect('lista_receitas')
    
    contexto = {
        'receita': receita,
    }

    return render(request, 'financeiro/confirmar_exclusao_receita.html', contexto)

def alternar_recebimento_receita(request, receita_id):
    receita = get_object_or_404(Receita, id=receita_id, usuario=request.user)

    if request.method == 'POST':
        receita.recebido = not receita.recebido
        receita.save(update_fields=['recebido'])

    proxima_pagina = request.POST.get('next') or 'lista_receitas'
    if not proxima_pagina.startswith('/'):
        proxima_pagina = 'lista_receitas'
    return redirect(proxima_pagina)

def nova_despesa(request):
    if request.method == 'POST':
        form = DespesaForm(request.POST, user=request.user)

        if form.is_valid():
            despesa = form.save(commit=False)
            despesa.usuario = request.user
            salvar_despesa_com_recorrencia(despesa)
            return redirect('lista_despesas')
    else:
        form = DespesaForm(user=request.user)

    contexto = {
        'form': form,
    }

    return render(request, 'financeiro/form_despesa.html', contexto)

def editar_despesa(request, despesa_id):
    despesa = get_object_or_404(Despesa, id=despesa_id, usuario=request.user)

    if request.method == 'POST':
        form = DespesaForm(request.POST, instance=despesa, user=request.user)

        if form.is_valid():
            form.save()
            return redirect('lista_despesas')
    else:
        form = DespesaForm(instance=despesa, user=request.user)

    contexto = {
        'form': form,
        'despesa': despesa,
    }

    return render(request, 'financeiro/form_despesa.html', contexto)

def excluir_despesa(request, despesa_id):
    despesa = get_object_or_404(Despesa, id=despesa_id, usuario=request.user)

    if request.method == 'POST':
        despesa.delete()
        return redirect('lista_despesas')

    contexto = {
        'despesa': despesa,
    }

    return render(request, 'financeiro/confirmar_exclusao_despesa.html', contexto)

def alternar_pagamento_despesa(request, despesa_id):
    despesa = get_object_or_404(Despesa, id=despesa_id, usuario=request.user)

    if request.method == 'POST':
        despesa.pago = not despesa.pago
        despesa.save(update_fields=['pago'])

    proxima_pagina = request.POST.get('next') or 'lista_despesas'
    if not proxima_pagina.startswith('/'):
        proxima_pagina = 'lista_despesas'
    return redirect(proxima_pagina)

def lista_contas(request):
    usuario = request.user
    contas = Conta.objects.filter(usuario=usuario).order_by('nome')
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

    contas_filtradas = contas
    contas_ids = list(contas_filtradas.values_list('id', flat=True))
    total_saldo_inicial = contas_filtradas.aggregate(total=Sum('saldo_inicial'))['total'] or 0
    total_receitas_filtradas = Receita.objects.filter(
        usuario=usuario,
        conta_id__in=contas_ids,
        recebido=True,
    ).aggregate(total=Sum('valor'))['total'] or 0
    total_despesas_filtradas = Despesa.objects.filter(
        usuario=usuario,
        conta_id__in=contas_ids,
        pago=True,
    ).aggregate(total=Sum('valor'))['total'] or 0
    saldo_contas_filtradas = total_saldo_inicial + total_receitas_filtradas - total_despesas_filtradas
    resumo_contas = contas_filtradas.aggregate(
        quantidade=Count('id'),
        principais=Count('id', filter=Q(banco_principal=True)),
        com_cartao=Count('id', filter=Q(possui_cartao_credito=True)),
        sem_cartao=Count('id', filter=Q(possui_cartao_credito=False)),
    )

    paginator = Paginator(contas, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    querystring = urlencode({k: v for k, v in request.GET.items() if v and k != 'page'})

    contas_com_saldo = []

    for conta in page_obj:
        total_receitas = Receita.objects.filter(
            usuario=usuario,
            conta=conta,
            recebido=True
        ).aggregate(total=Sum('valor'))['total'] or 0

        total_despesas = Despesa.objects.filter(
            usuario=usuario,
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
        'total_contas_filtradas': resumo_contas['quantidade'] or 0,
        'total_contas_principais': resumo_contas['principais'] or 0,
        'total_contas_com_cartao': resumo_contas['com_cartao'] or 0,
        'total_contas_sem_cartao': resumo_contas['sem_cartao'] or 0,
        'saldo_contas_filtradas': saldo_contas_filtradas,
    }

    return render(request, 'financeiro/lista_contas.html', contexto)


def manter_apenas_um_banco_principal(usuario, conta):
    if conta.banco_principal:
        Conta.objects.filter(
            usuario=usuario,
            banco_principal=True,
        ).exclude(id=conta.id).update(banco_principal=False)


def nova_conta(request):
    if request.method == 'POST':
        form = ContaForm(request.POST)

        if form.is_valid():
            conta = form.save(commit=False)
            conta.usuario = request.user
            conta.save()
            manter_apenas_um_banco_principal(request.user, conta)
            return redirect('lista_contas')
    else:
        form = ContaForm()

    contexto = {
        'form': form,
    }

    return render(request, 'financeiro/form_conta.html', contexto)

def editar_conta(request, conta_id):
    conta = get_object_or_404(Conta, id=conta_id, usuario=request.user)

    if request.method == 'POST':
        form = ContaForm(request.POST, instance=conta)

        if form.is_valid():
            conta = form.save()
            manter_apenas_um_banco_principal(request.user, conta)
            return redirect('lista_contas')
    else:
        form = ContaForm(instance=conta)

    contexto = {
        'form': form,
        'conta': conta,
    }

    return render(request, 'financeiro/form_conta.html', contexto)

def excluir_conta(request, conta_id):
    conta = get_object_or_404(Conta, id=conta_id, usuario=request.user)
    erro = None

    if request.method == 'POST':
        try:
            conta.delete()
            return redirect('lista_contas')
        except ProtectedError:
            erro = 'Esta conta possui receitas ou despesas vinculadas e não pode ser excluída.'

    contexto = {
        'conta': conta,
        'erro': erro,
    }

    return render(request, 'financeiro/confirmar_exclusao_conta.html', contexto)

def lista_categorias(request):
    categorias = Categoria.objects.filter(usuario=request.user).order_by('tipo', 'nome')
    q = request.GET.get('q', '').strip()
    tipo = request.GET.get('tipo', '')

    if q:
        categorias = categorias.filter(nome__icontains=q)
    if tipo:
        categorias = categorias.filter(tipo=tipo)

    resumo_categorias = categorias.aggregate(
        quantidade=Count('id'),
        receitas=Count('id', filter=Q(tipo='receita')),
        despesas=Count('id', filter=Q(tipo='despesa')),
    )
    total_tipos_categorias = int(bool(resumo_categorias['receitas'])) + int(bool(resumo_categorias['despesas']))

    contexto = {
        'categorias_receitas': categorias.filter(tipo='receita'),
        'categorias_despesas': categorias.filter(tipo='despesa'),
        'filtro_q': q,
        'filtro_tipo': tipo,
        'total_categorias_filtradas': resumo_categorias['quantidade'] or 0,
        'total_categorias_receitas': resumo_categorias['receitas'] or 0,
        'total_categorias_despesas': resumo_categorias['despesas'] or 0,
        'total_tipos_categorias': total_tipos_categorias,
    }

    return render(request, 'financeiro/lista_categorias.html', contexto)

def nova_categoria(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)

        if form.is_valid():
            categoria = form.save(commit=False)
            categoria.usuario = request.user
            categoria.save()
            return redirect('lista_categorias')
    else:
        form = CategoriaForm()

    contexto = {
        'form': form,
    }

    return render(request, 'financeiro/form_categoria.html', contexto)

def editar_categoria(request, categoria_id):
    categoria = get_object_or_404(Categoria, id=categoria_id, usuario=request.user)

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
    categoria = get_object_or_404(Categoria, id=categoria_id, usuario=request.user)
    erro = None

    if request.method == 'POST':
        try:
            categoria.delete()
            return redirect('lista_categorias')
        except ProtectedError:
            erro = 'Esta categoria possui receitas ou despesas vinculadas e não pode ser excluída.'

    contexto = {
        'categoria': categoria,
        'erro': erro,
    }

    return render(request, 'financeiro/confirmar_exclusao_categoria.html', contexto)

def lista_emprestimos_cartao(request):
    usuario = request.user
    emprestimos = EmprestimoCartao.objects.filter(usuario=usuario).select_related('cartao_utilizado', 'conta_recebimento').order_by('-data_compra')
    q = request.GET.get('q', '').strip()
    cartao_id = request.GET.get('cartao', '')
    status = request.GET.get('status', '')

    if q:
        emprestimos = emprestimos.filter(pessoa__icontains=q)
    if cartao_id:
        emprestimos = emprestimos.filter(cartao_utilizado_id=cartao_id)

    querystring = urlencode({k: v for k, v in request.GET.items() if v and k != 'page'})

    emprestimos = emprestimos.annotate(
        total_parcelas_count=Count('parcelas'),
        parcelas_pendentes_count=Count('parcelas', filter=Q(parcelas__pago=False)),
    )
    emprestimos_filtrados_ids = emprestimos.values_list('id', flat=True)
    emprestimos_abertos = emprestimos.filter(parcelas_pendentes_count__gt=0)
    emprestimos_quitados = emprestimos.filter(
        total_parcelas_count__gt=0,
        parcelas_pendentes_count=0,
    )

    if status == 'pago':
        emprestimos_abertos = EmprestimoCartao.objects.none()
    elif status == 'pendente':
        emprestimos_quitados = EmprestimoCartao.objects.none()

    parcelas = ParcelaEmprestimo.objects.select_related(
        'emprestimo',
        'emprestimo__cartao_utilizado',
        'emprestimo__conta_recebimento',
    ).filter(
        emprestimo__usuario=usuario,
        emprestimo_id__in=emprestimos_filtrados_ids,
    ).order_by('vencimento', 'emprestimo__pessoa', 'numero')

    parcelas_pendentes = parcelas.filter(pago=False)
    parcelas_pagas = parcelas.filter(pago=True).order_by('-vencimento', 'emprestimo__pessoa', 'numero')

    if status == 'pago':
        parcelas_pendentes = ParcelaEmprestimo.objects.none()
    elif status == 'pendente':
        parcelas_pagas = ParcelaEmprestimo.objects.none()

    total_emprestado = emprestimos.aggregate(total=Sum('valor_total'))['total'] or 0
    total_pago = ParcelaEmprestimo.objects.filter(
        emprestimo__usuario=usuario,
        emprestimo_id__in=emprestimos_filtrados_ids,
        pago=True,
    ).aggregate(total=Sum('valor'))['total'] or 0
    total_pendente = ParcelaEmprestimo.objects.filter(
        emprestimo__usuario=usuario,
        emprestimo_id__in=emprestimos_filtrados_ids,
        pago=False,
    ).aggregate(total=Sum('valor'))['total'] or 0
    total_emprestimos_filtrados = emprestimos.count()
    total_emprestimos_abertos = emprestimos_abertos.count()
    total_emprestimos_quitados = emprestimos_quitados.count()
    cartoes = Conta.objects.filter(usuario=usuario, possui_cartao_credito=True).order_by('nome')

    contexto = {
        'emprestimos': emprestimos_abertos,
        'emprestimos_quitados': emprestimos_quitados,
        'parcelas_pendentes': parcelas_pendentes,
        'parcelas_pagas': parcelas_pagas,
        'total_emprestado': total_emprestado,
        'total_pago': total_pago,
        'total_pendente': total_pendente,
        'total_emprestimos_filtrados': total_emprestimos_filtrados,
        'total_emprestimos_abertos': total_emprestimos_abertos,
        'total_emprestimos_quitados': total_emprestimos_quitados,
        'cartoes': cartoes,
        'querystring': querystring,
        'current_url': request.get_full_path(),
        'filtro_q': q,
        'filtro_cartao': cartao_id,
        'filtro_status': status,
    }

    return render(request, 'financeiro/lista_emprestimos_cartao.html', contexto)

def novo_emprestimo_cartao(request):
    if request.method == 'POST':
        form = EmprestimoCartaoForm(request.POST, user=request.user)

        if form.is_valid():
            emprestimo = form.save(commit=False)
            emprestimo.usuario = request.user
            emprestimo.banco = emprestimo.cartao_utilizado.nome
            emprestimo.dia_vencimento_cartao = emprestimo.cartao_utilizado.dia_vencimento_fatura
            emprestimo.save()
            gerar_parcelas_emprestimo(emprestimo)
            return redirect('lista_emprestimos_cartao')
    else:
        form = EmprestimoCartaoForm(user=request.user)

    contexto = {
        'form': form,
    }

    return render(request, 'financeiro/form_emprestimo_cartao.html', contexto)

def editar_emprestimo_cartao(request, emprestimo_id):
    emprestimo = get_object_or_404(EmprestimoCartao, id=emprestimo_id, usuario=request.user)
    campos_que_recalculam_parcelas = {
        'cartao_utilizado',
        'valor_total',
        'quantidade_parcelas',
        'data_compra',
    }

    if request.method == 'POST':
        form = EmprestimoCartaoForm(request.POST, instance=emprestimo, user=request.user)

        if form.is_valid():
            tem_parcela_paga = emprestimo.parcelas.filter(pago=True).exists()
            deve_recalcular = bool(campos_que_recalculam_parcelas.intersection(form.changed_data))

            if tem_parcela_paga and deve_recalcular:
                messages.error(
                    request,
                    'Este gasto já possui parcelas pagas. Para proteger o histórico, não altere cartão, valor, data ou quantidade de parcelas.'
                )
                contexto = {
                    'form': form,
                    'emprestimo': emprestimo,
                }
                return render(request, 'financeiro/form_emprestimo_cartao.html', contexto)

            emprestimo = form.save(commit=False)
            emprestimo.usuario = request.user
            emprestimo.banco = emprestimo.cartao_utilizado.nome
            emprestimo.dia_vencimento_cartao = emprestimo.cartao_utilizado.dia_vencimento_fatura
            emprestimo.save()

            if deve_recalcular:
                gerar_parcelas_emprestimo(emprestimo)

            return redirect('lista_emprestimos_cartao')
    else:
        form = EmprestimoCartaoForm(instance=emprestimo, user=request.user)

    contexto = {
        'form': form,
        'emprestimo': emprestimo,
    }

    return render(request, 'financeiro/form_emprestimo_cartao.html', contexto)

def excluir_emprestimo_cartao(request, emprestimo_id):
    emprestimo = get_object_or_404(EmprestimoCartao, id=emprestimo_id, usuario=request.user)

    if request.method == 'POST':
        emprestimo.delete()
        return redirect('lista_emprestimos_cartao')

    contexto = {
        'emprestimo': emprestimo,
    }

    return render(request, 'financeiro/confirmar_exclusao_emprestimo_cartao.html', contexto)

def alternar_pagamento_parcela(request, parcela_id):
    parcela = get_object_or_404(ParcelaEmprestimo, id=parcela_id, emprestimo__usuario=request.user)
    proxima_pagina = request.POST.get('next') or 'lista_emprestimos_cartao'
    if not proxima_pagina.startswith('/') or proxima_pagina.startswith('//'):
        proxima_pagina = 'lista_emprestimos_cartao'

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
                return redirect(proxima_pagina)

            categoria, _ = Categoria.objects.get_or_create(
                usuario=request.user,
                nome='Pagamento cartão emprestado',
                tipo='receita'
            )

            receita = Receita.objects.create(
                usuario=request.user,
                descricao=f'Pagamento cartão - {parcela.emprestimo.pessoa} ({parcela.numero}/{parcela.emprestimo.quantidade_parcelas})',
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

    return redirect(proxima_pagina)
