from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('financeiro', '0003_emprestimocartao_dia_vencimento_cartao'),
    ]

    operations = [
        migrations.AddField(
            model_name='emprestimocartao',
            name='conta_recebimento',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='emprestimos_cartao_recebidos', to='financeiro.conta'),
        ),
        migrations.AddField(
            model_name='parcelaemprestimo',
            name='receita_gerada',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='parcelas_cartao', to='financeiro.receita'),
        ),
    ]
