from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('financeiro', '0005_conta_cartao_credito_emprestimo_cartao_utilizado'),
    ]

    operations = [
        migrations.RenameField(
            model_name='conta',
            old_name='dia_fechamento_fatura',
            new_name='dias_antes_fechamento_fatura',
        ),
    ]
