import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("acervo", "0002_livro_categoria_livro_tipo"),
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="livro",
            name="organizacao",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="core.organizacao",
            ),
        ),
    ]
