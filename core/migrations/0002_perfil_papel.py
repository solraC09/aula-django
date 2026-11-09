from django.db import migrations, models


def superusuarios_viram_admin(apps, schema_editor):
    Perfil = apps.get_model("core", "Perfil")
    Perfil.objects.filter(usuario__is_superuser=True).update(papel="admin")


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="perfil",
            name="papel",
            field=models.CharField(
                choices=[("admin", "Administrador"), ("operador", "Operador")],
                default="operador",
                max_length=20,
            ),
        ),
        migrations.RunPython(superusuarios_viram_admin, migrations.RunPython.noop),
    ]
