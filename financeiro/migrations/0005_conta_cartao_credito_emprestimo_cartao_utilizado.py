from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('financeiro', '0004_emprestimocartao_conta_recebimento_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='conta',
            name='possui_cartao_credito',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='conta',
            name='dia_fechamento_fatura',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='conta',
            name='dia_vencimento_fatura',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='emprestimocartao',
            name='cartao_utilizado',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='emprestimos_cartao_utilizado', to='financeiro.conta'),
        ),
    ]
