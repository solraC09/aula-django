import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("acervo", "0004_dados_org"),
    ]

    operations = [
        migrations.AlterField(
            model_name="livro",
            name="organizacao",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to="core.organizacao",
            ),
        ),
    ]
