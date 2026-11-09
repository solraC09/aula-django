import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("acervo", "0005_alter_livro_organizacao"),
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Autor",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("nome", models.CharField(max_length=120)),
                (
                    "organizacao",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="core.organizacao",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Autores",
                "ordering": ["nome"],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("organizacao", "nome"),
                        name="autor_unico_por_org",
                    )
                ],
            },
        ),
        migrations.AddField(
            model_name="livro",
            name="autor_novo",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="acervo.autor",
            ),
        ),
    ]
