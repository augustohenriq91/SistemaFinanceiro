from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('financeiro', '0002_emprestimocartao_parcelaemprestimo'),
    ]

    operations = [
        migrations.AddField(
            model_name='emprestimocartao',
            name='dia_vencimento_cartao',
            field=models.PositiveIntegerField(default=10),
        ),
    ]
