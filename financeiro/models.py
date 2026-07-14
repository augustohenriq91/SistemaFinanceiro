from django.conf import settings
from django.db import models
from decimal import Decimal


class Categoria(models.Model):
    TIPO_CHOICES = [
        ('receita', 'Receita'),
        ('despesa', 'Despesa'),
    ]

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='categorias_financeiras')
    nome = models.CharField('Nome', max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)

    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'

    def __str__(self):
        return self.nome


class Conta(models.Model):
    TIPO_CHOICES = [
        ('banco', 'Banco'),
        ('carteira', 'Carteira'),
        ('investimento', 'Investimento'),
    ]

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='contas_financeiras')
    nome = models.CharField('Nome', max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    saldo_inicial = models.DecimalField('Saldo inicial', max_digits=12, decimal_places=2, default=0)
    banco_principal = models.BooleanField('Banco principal', default=False)
    possui_cartao_credito = models.BooleanField('Possui cartão de crédito?', default=False)
    dias_antes_fechamento_fatura = models.PositiveIntegerField('Dias antes do vencimento da fatura', null=True, blank=True)
    dia_vencimento_fatura = models.PositiveIntegerField('Dia de vencimento da fatura', null=True, blank=True)

    class Meta:
        verbose_name = 'Conta'
        verbose_name_plural = 'Contas'

    def __str__(self):
        return self.nome


class Receita(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='receitas_financeiras')
    descricao = models.CharField('Descrição', max_length=150)
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    data = models.DateField()
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT)
    conta = models.ForeignKey(Conta, on_delete=models.PROTECT)
    recebido = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Receita'
        verbose_name_plural = 'Receitas'

    def __str__(self):
        return self.descricao


class Despesa(models.Model):
    TIPO_RECORRENCIA_CHOICES = [
        ('unica', 'Despesa única'),
        ('parcelada', 'Parcelada'),
        ('recorrente', 'Repetir sempre'),
    ]

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='despesas_financeiras')
    descricao = models.CharField('Descrição', max_length=150)
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    data = models.DateField()
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT)
    conta = models.ForeignKey(Conta, on_delete=models.PROTECT)
    pago = models.BooleanField(default=False)
    despesa_fixa = models.BooleanField('Despesa fixa?', default=False)
    tipo_recorrencia = models.CharField('Tipo de recorrência', max_length=20, choices=TIPO_RECORRENCIA_CHOICES, default='unica')
    quantidade_parcelas = models.PositiveIntegerField('Quantidade de parcelas', null=True, blank=True)
    parcela_atual = models.PositiveIntegerField('Parcela atual', null=True, blank=True)
    data_inicio_parcelamento = models.DateField('Data de início do parcelamento', null=True, blank=True)
    parcelas_ja_pagas = models.PositiveIntegerField('Parcelas já pagas', default=0, blank=True)
    grupo_recorrencia = models.CharField('Grupo da recorrência', max_length=36, blank=True, default='')

    class Meta:
        verbose_name = 'Despesa'
        verbose_name_plural = 'Despesas'

    def __str__(self):
        return self.descricao


class EmprestimoCartao(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='compras_cartao')
    pessoa = models.CharField('Pessoa', max_length=120)
    banco = models.CharField(max_length=100)
    cartao_utilizado = models.ForeignKey(
        Conta,
        verbose_name='Cartão utilizado',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='emprestimos_cartao_utilizado'
    )
    conta_recebimento = models.ForeignKey(
        Conta,
        verbose_name='Conta de recebimento',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='emprestimos_cartao_recebidos'
    )
    descricao = models.CharField('Descrição', max_length=150)
    valor_total = models.DecimalField('Valor total', max_digits=12, decimal_places=2)
    quantidade_parcelas = models.PositiveIntegerField('Quantidade de parcelas')
    data_compra = models.DateField('Data da compra')
    dia_vencimento_cartao = models.PositiveIntegerField('Dia de vencimento do cartão', default=10)
    observacao = models.TextField('Observação', blank=True)

    class Meta:
        verbose_name = 'Cartão de crédito'
        verbose_name_plural = 'Cartões de crédito'

    def __str__(self):
        return f'{self.pessoa} - {self.descricao}'


class ParcelaEmprestimo(models.Model):
    emprestimo = models.ForeignKey(
        EmprestimoCartao,
        verbose_name='Empréstimo',
        on_delete=models.CASCADE,
        related_name='parcelas'
    )
    numero = models.PositiveIntegerField('Número')
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    vencimento = models.DateField()
    pago = models.BooleanField(default=False)
    data_pagamento = models.DateField('Data de pagamento', null=True, blank=True)
    receita_gerada = models.ForeignKey(
        Receita,
        verbose_name='Receita gerada',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='parcelas_cartao'
    )

    class Meta:
        ordering = ['vencimento', 'numero']
        verbose_name = 'Parcela de cartão'
        verbose_name_plural = 'Parcelas de cartão'

    def __str__(self):
        return f'{self.emprestimo.pessoa} - parcela {self.numero}'


class AtivoInvestimento(models.Model):
    TIPO_CHOICES = [
        ('acao', 'Ação'),
        ('fii', 'FII'),
        ('etf', 'ETF'),
        ('bdr', 'BDR'),
        ('cripto', 'Cripto'),
        ('renda_fixa', 'Renda fixa'),
        ('outro', 'Outro'),
    ]

    MERCADO_CHOICES = [
        ('br', 'Brasil'),
        ('us', 'Estados Unidos'),
        ('cripto', 'Cripto'),
        ('manual', 'Manual'),
    ]

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ativos_investimento')
    conta = models.ForeignKey(Conta, on_delete=models.PROTECT, related_name='ativos_investimento')
    nome = models.CharField('Nome', max_length=120)
    ticker = models.CharField('Ticker', max_length=30)
    tipo = models.CharField('Tipo', max_length=20, choices=TIPO_CHOICES, default='acao')
    mercado = models.CharField('Mercado', max_length=20, choices=MERCADO_CHOICES, default='br')
    quantidade = models.DecimalField('Quantidade', max_digits=18, decimal_places=8, default=0)
    preco_medio = models.DecimalField('Preço médio', max_digits=14, decimal_places=4, default=0)
    cotacao_atual = models.DecimalField('Cotação atual', max_digits=14, decimal_places=4, null=True, blank=True)
    cotacao_atualizada_em = models.DateTimeField('Cotação atualizada em', null=True, blank=True)
    fonte_cotacao = models.CharField('Fonte da cotação', max_length=80, blank=True, default='')

    class Meta:
        ordering = ['nome']
        verbose_name = 'Ativo de investimento'
        verbose_name_plural = 'Ativos de investimento'

    def __str__(self):
        return f'{self.ticker} - {self.nome}'

    @property
    def ticker_cotacao(self):
        ticker = (self.ticker or '').strip().upper()
        if self.mercado == 'br' and ticker and '.' not in ticker:
            return f'{ticker}.SA'
        if self.mercado == 'cripto' and '-' not in ticker:
            return f'{ticker}-BRL'
        return ticker

    @property
    def valor_investido(self):
        return (self.quantidade or Decimal('0')) * (self.preco_medio or Decimal('0'))

    @property
    def valor_atual(self):
        if self.cotacao_atual is None:
            return None
        return (self.quantidade or Decimal('0')) * self.cotacao_atual

    @property
    def resultado(self):
        valor_atual = self.valor_atual
        if valor_atual is None:
            return None
        return valor_atual - self.valor_investido

    @property
    def rentabilidade_percentual(self):
        if not self.valor_investido or self.resultado is None:
            return None
        return (self.resultado / self.valor_investido) * Decimal('100')


class CotacaoAtivo(models.Model):
    ativo = models.ForeignKey(AtivoInvestimento, on_delete=models.CASCADE, related_name='historico_cotacoes')
    valor = models.DecimalField(max_digits=14, decimal_places=4)
    fonte = models.CharField(max_length=80, blank=True, default='')
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criada_em']
        verbose_name = 'Cotação de ativo'
        verbose_name_plural = 'Cotações de ativos'

    def __str__(self):
        return f'{self.ativo.ticker} - {self.valor}'
