from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('financeiro', '0006_rename_dia_fechamento_para_dias_antes'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='categoria',
            options={'verbose_name': 'Categoria', 'verbose_name_plural': 'Categorias'},
        ),
        migrations.AlterModelOptions(
            name='conta',
            options={'verbose_name': 'Conta', 'verbose_name_plural': 'Contas'},
        ),
        migrations.AlterModelOptions(
            name='despesa',
            options={'verbose_name': 'Despesa', 'verbose_name_plural': 'Despesas'},
        ),
        migrations.AlterModelOptions(
            name='emprestimocartao',
            options={'verbose_name': 'Cartão de crédito', 'verbose_name_plural': 'Cartões de crédito'},
        ),
        migrations.AlterModelOptions(
            name='parcelaemprestimo',
            options={'ordering': ['vencimento', 'numero'], 'verbose_name': 'Parcela de cartão', 'verbose_name_plural': 'Parcelas de cartão'},
        ),
        migrations.AlterModelOptions(
            name='receita',
            options={'verbose_name': 'Receita', 'verbose_name_plural': 'Receitas'},
        ),
        migrations.AlterField(
            model_name='categoria',
            name='nome',
            field=models.CharField(max_length=100, verbose_name='Nome'),
        ),
        migrations.AlterField(
            model_name='conta',
            name='dia_vencimento_fatura',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='Dia de vencimento da fatura'),
        ),
        migrations.AlterField(
            model_name='conta',
            name='dias_antes_fechamento_fatura',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='Dias antes do vencimento da fatura'),
        ),
        migrations.AlterField(
            model_name='conta',
            name='nome',
            field=models.CharField(max_length=100, verbose_name='Nome'),
        ),
        migrations.AlterField(
            model_name='conta',
            name='possui_cartao_credito',
            field=models.BooleanField(default=False, verbose_name='Possui cartão de crédito?'),
        ),
        migrations.AlterField(
            model_name='conta',
            name='saldo_inicial',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Saldo inicial'),
        ),
        migrations.AlterField(
            model_name='despesa',
            name='descricao',
            field=models.CharField(max_length=150, verbose_name='Descrição'),
        ),
        migrations.AlterField(
            model_name='emprestimocartao',
            name='cartao_utilizado',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='emprestimos_cartao_utilizado', to='financeiro.conta', verbose_name='Cartão utilizado'),
        ),
        migrations.AlterField(
            model_name='emprestimocartao',
            name='conta_recebimento',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='emprestimos_cartao_recebidos', to='financeiro.conta', verbose_name='Conta de recebimento'),
        ),
        migrations.AlterField(
            model_name='emprestimocartao',
            name='data_compra',
            field=models.DateField(verbose_name='Data da compra'),
        ),
        migrations.AlterField(
            model_name='emprestimocartao',
            name='descricao',
            field=models.CharField(max_length=150, verbose_name='Descrição'),
        ),
        migrations.AlterField(
            model_name='emprestimocartao',
            name='dia_vencimento_cartao',
            field=models.PositiveIntegerField(default=10, verbose_name='Dia de vencimento do cartão'),
        ),
        migrations.AlterField(
            model_name='emprestimocartao',
            name='observacao',
            field=models.TextField(blank=True, verbose_name='Observação'),
        ),
        migrations.AlterField(
            model_name='emprestimocartao',
            name='pessoa',
            field=models.CharField(max_length=120, verbose_name='Pessoa'),
        ),
        migrations.AlterField(
            model_name='emprestimocartao',
            name='quantidade_parcelas',
            field=models.PositiveIntegerField(verbose_name='Quantidade de parcelas'),
        ),
        migrations.AlterField(
            model_name='emprestimocartao',
            name='valor_total',
            field=models.DecimalField(decimal_places=2, max_digits=12, verbose_name='Valor total'),
        ),
        migrations.AlterField(
            model_name='parcelaemprestimo',
            name='data_pagamento',
            field=models.DateField(blank=True, null=True, verbose_name='Data de pagamento'),
        ),
        migrations.AlterField(
            model_name='parcelaemprestimo',
            name='emprestimo',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='parcelas', to='financeiro.emprestimocartao', verbose_name='Empréstimo'),
        ),
        migrations.AlterField(
            model_name='parcelaemprestimo',
            name='numero',
            field=models.PositiveIntegerField(verbose_name='Número'),
        ),
        migrations.AlterField(
            model_name='parcelaemprestimo',
            name='receita_gerada',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='parcelas_cartao', to='financeiro.receita', verbose_name='Receita gerada'),
        ),
        migrations.AlterField(
            model_name='receita',
            name='descricao',
            field=models.CharField(max_length=150, verbose_name='Descrição'),
        ),
    ]
