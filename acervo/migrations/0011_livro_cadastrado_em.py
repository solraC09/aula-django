import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("acervo", "0010_alter_livro_ano"),
    ]

    operations = [
        migrations.AddField(
            model_name="livro",
            name="cadastrado_em",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddIndex(
            model_name="livro",
            index=models.Index(
                fields=["cadastrado_em"], name="acervo_livr_cadastr_27eca0_idx"
            ),
        ),
    ]
