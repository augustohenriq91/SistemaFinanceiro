from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('financeiro', '0008_dados_por_usuario'),
    ]

    operations = [
        migrations.AddField(
            model_name='conta',
            name='banco_principal',
            field=models.BooleanField(default=False, verbose_name='Banco principal'),
        ),
    ]
