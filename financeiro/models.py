from django.conf import settings
from django.db import models


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
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='despesas_financeiras')
    descricao = models.CharField('Descrição', max_length=150)
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    data = models.DateField()
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT)
    conta = models.ForeignKey(Conta, on_delete=models.PROTECT)
    pago = models.BooleanField(default=False)

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
