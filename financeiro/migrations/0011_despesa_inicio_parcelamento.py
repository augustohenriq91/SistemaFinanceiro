from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('financeiro', '0010_despesa_recorrencia'),
    ]

    operations = [
        migrations.AddField(
            model_name='despesa',
            name='data_inicio_parcelamento',
            field=models.DateField(blank=True, null=True, verbose_name='Data de início do parcelamento'),
        ),
        migrations.AddField(
            model_name='despesa',
            name='parcelas_ja_pagas',
            field=models.PositiveIntegerField(blank=True, default=0, verbose_name='Parcelas já pagas'),
        ),
    ]
