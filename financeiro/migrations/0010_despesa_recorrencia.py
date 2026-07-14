from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('financeiro', '0009_conta_banco_principal'),
    ]

    operations = [
        migrations.AddField(
            model_name='despesa',
            name='despesa_fixa',
            field=models.BooleanField(default=False, verbose_name='Despesa fixa?'),
        ),
        migrations.AddField(
            model_name='despesa',
            name='tipo_recorrencia',
            field=models.CharField(
                choices=[
                    ('unica', 'Despesa única'),
                    ('parcelada', 'Parcelada'),
                    ('recorrente', 'Repetir sempre'),
                ],
                default='unica',
                max_length=20,
                verbose_name='Tipo de recorrência',
            ),
        ),
        migrations.AddField(
            model_name='despesa',
            name='quantidade_parcelas',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='Quantidade de parcelas'),
        ),
        migrations.AddField(
            model_name='despesa',
            name='parcela_atual',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='Parcela atual'),
        ),
        migrations.AddField(
            model_name='despesa',
            name='grupo_recorrencia',
            field=models.CharField(blank=True, default='', max_length=36, verbose_name='Grupo da recorrência'),
        ),
    ]
