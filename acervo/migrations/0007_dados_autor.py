from django.db import migrations


def texto_para_autor(apps, schema_editor):
    Autor = apps.get_model("acervo", "Autor")
    Livro = apps.get_model("acervo", "Livro")

    for livro in Livro.objects.filter(autor_novo__isnull=True):
        autor, _ = Autor.objects.get_or_create(
            organizacao_id=livro.organizacao_id,
            nome=livro.autor.strip(),
        )
        livro.autor_novo = autor
        livro.save(update_fields=["autor_novo"])


class Migration(migrations.Migration):

    dependencies = [
        ("acervo", "0006_autor"),
    ]

    operations = [
        migrations.RunPython(texto_para_autor, migrations.RunPython.noop),
    ]
