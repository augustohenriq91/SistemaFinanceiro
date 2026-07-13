from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def vincular_dados_existentes(apps, schema_editor):
    app_label, model_name = settings.AUTH_USER_MODEL.split('.')
    Usuario = apps.get_model(app_label, model_name)
    usuario = Usuario.objects.order_by('id').first()

    if not usuario:
        return

    for nome_modelo in ['Categoria', 'Conta', 'Receita', 'Despesa', 'EmprestimoCartao']:
        Modelo = apps.get_model('financeiro', nome_modelo)
        Modelo.objects.filter(usuario__isnull=True).update(usuario=usuario)


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('financeiro', '0007_verbose_names'),
    ]

    operations = [
        migrations.AddField(
            model_name='categoria',
            name='usuario',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='categorias_financeiras',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='conta',
            name='usuario',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='contas_financeiras',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='receita',
            name='usuario',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='receitas_financeiras',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='despesa',
            name='usuario',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='despesas_financeiras',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='emprestimocartao',
            name='usuario',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='compras_cartao',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(vincular_dados_existentes, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='categoria',
            name='usuario',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='categorias_financeiras',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name='conta',
            name='usuario',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='contas_financeiras',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name='receita',
            name='usuario',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='receitas_financeiras',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name='despesa',
            name='usuario',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='despesas_financeiras',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name='emprestimocartao',
            name='usuario',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='compras_cartao',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
