from django.db import models

class Categoria(models.Model):
    TIPO_CHOICES = [
        ('receita', 'Receita'),
        ('despesa', 'Despesa'),
    ]

    nome = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)

    def __str__(self):
        return self.nome


class Conta(models.Model):
    TIPO_CHOICES = [
        ('banco', 'Banco'),
        ('carteira', 'Carteira'),
        ('investimento', 'Investimento'),
    ]

    nome = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    saldo_inicial = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    possui_cartao_credito = models.BooleanField(default=False)
    dia_fechamento_fatura = models.PositiveIntegerField(null=True, blank=True)
    dia_vencimento_fatura = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return self.nome


class Receita(models.Model):
    descricao = models.CharField(max_length=150)
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    data = models.DateField()
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT)
    conta = models.ForeignKey(Conta, on_delete=models.PROTECT)
    recebido = models.BooleanField(default=False)

    def __str__(self):
        return self.descricao


class Despesa(models.Model):
    descricao = models.CharField(max_length=150)
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    data = models.DateField()
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT)
    conta = models.ForeignKey(Conta, on_delete=models.PROTECT)
    pago = models.BooleanField(default=False)

    def __str__(self):
        return self.descricao


class EmprestimoCartao(models.Model):
    pessoa = models.CharField(max_length=120)
    banco = models.CharField(max_length=100)
    cartao_utilizado = models.ForeignKey(
        Conta,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='emprestimos_cartao_utilizado'
    )
    conta_recebimento = models.ForeignKey(
        Conta,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='emprestimos_cartao_recebidos'
    )
    descricao = models.CharField(max_length=150)
    valor_total = models.DecimalField(max_digits=12, decimal_places=2)
    quantidade_parcelas = models.PositiveIntegerField()
    data_compra = models.DateField()
    dia_vencimento_cartao = models.PositiveIntegerField(default=10)
    observacao = models.TextField(blank=True)

    def __str__(self):
        return f'{self.pessoa} - {self.descricao}'


class ParcelaEmprestimo(models.Model):
    emprestimo = models.ForeignKey(
        EmprestimoCartao,
        on_delete=models.CASCADE,
        related_name='parcelas'
    )
    numero = models.PositiveIntegerField()
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    vencimento = models.DateField()
    pago = models.BooleanField(default=False)
    data_pagamento = models.DateField(null=True, blank=True)
    receita_gerada = models.ForeignKey(
        Receita,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='parcelas_cartao'
    )

    class Meta:
        ordering = ['vencimento', 'numero']

    def __str__(self):
        return f'{self.emprestimo.pessoa} - parcela {self.numero}'
