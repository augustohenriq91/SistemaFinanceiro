from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('financeiro', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmprestimoCartao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pessoa', models.CharField(max_length=120)),
                ('banco', models.CharField(max_length=100)),
                ('descricao', models.CharField(max_length=150)),
                ('valor_total', models.DecimalField(decimal_places=2, max_digits=12)),
                ('quantidade_parcelas', models.PositiveIntegerField()),
                ('data_compra', models.DateField()),
                ('observacao', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='ParcelaEmprestimo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero', models.PositiveIntegerField()),
                ('valor', models.DecimalField(decimal_places=2, max_digits=12)),
                ('vencimento', models.DateField()),
                ('pago', models.BooleanField(default=False)),
                ('data_pagamento', models.DateField(blank=True, null=True)),
                ('emprestimo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='parcelas', to='financeiro.emprestimocartao')),
            ],
            options={
                'ordering': ['vencimento', 'numero'],
            },
        ),
    ]
