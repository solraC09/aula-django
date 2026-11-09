import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("acervo", "0007_dados_autor"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="livro",
            name="autor",
        ),
        migrations.RenameField(
            model_name="livro",
            old_name="autor_novo",
            new_name="autor",
        ),
        migrations.AlterField(
            model_name="livro",
            name="autor",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to="acervo.autor",
            ),
        ),
    ]
