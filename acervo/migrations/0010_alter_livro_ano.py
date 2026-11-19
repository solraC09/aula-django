import acervo.models
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("acervo", "0009_livro_cadastrado_por"),
    ]

    operations = [
        migrations.AlterField(
            model_name="livro",
            name="ano",
            field=models.IntegerField(
                validators=[
                    django.core.validators.MinValueValidator(1000),
                    acervo.models.validar_ano_nao_futuro,
                ]
            ),
        ),
    ]
