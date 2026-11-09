from django.db import migrations


def org_padrao(apps, schema_editor):
    Organizacao = apps.get_model("core", "Organizacao")
    Livro = apps.get_model("acervo", "Livro")

    if not Livro.objects.filter(organizacao__isnull=True).exists():
        return

    org, _ = Organizacao.objects.get_or_create(nome="Organização padrão")
    Livro.objects.filter(organizacao__isnull=True).update(organizacao=org)


class Migration(migrations.Migration):

    dependencies = [
        ("acervo", "0003_livro_organizacao"),
    ]

    operations = [
        migrations.RunPython(org_padrao, migrations.RunPython.noop),
    ]
