from django.db import migrations, models
import django.db.models.deletion
from django.utils.text import slugify


def forwards(apps, schema_editor):
    School = apps.get_model("accounts", "School")
    State = apps.get_model("accounts", "State")
    Town = apps.get_model("accounts", "Town")
    for school in School.objects.all():
        state, _ = State.objects.get_or_create(
            name=school.state or "FCT", defaults={"slug": slugify(school.state or "FCT")}
        )
        town, _ = Town.objects.get_or_create(
            name=school.city,
            state=state,
            defaults={"latitude": school.latitude, "longitude": school.longitude},
        )
        school.town = town
        school.save(update_fields=["town"])


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_school_institution_type_alter_school_country"),
    ]

    operations = [
        migrations.CreateModel(
            name="State",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=60, unique=True)),
                ("slug", models.SlugField(max_length=60, unique=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Town",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("latitude", models.DecimalField(decimal_places=6, max_digits=9)),
                ("longitude", models.DecimalField(decimal_places=6, max_digits=9)),
                ("state", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="towns", to="accounts.state")),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.AddConstraint(
            model_name="town",
            constraint=models.UniqueConstraint(fields=("name", "state"), name="unique_town_per_state"),
        ),
        migrations.AddField(
            model_name="school",
            name="town",
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name="schools", to="accounts.town"),
        ),
        migrations.RunPython(forwards, migrations.RunPython.noop),
        migrations.RemoveField(model_name="school", name="city"),
        migrations.RemoveField(model_name="school", name="state"),
        migrations.RemoveField(model_name="school", name="country"),
        migrations.RemoveField(model_name="school", name="latitude"),
        migrations.RemoveField(model_name="school", name="longitude"),
        migrations.AlterField(
            model_name="school",
            name="town",
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="schools", to="accounts.town"),
        ),
    ]
