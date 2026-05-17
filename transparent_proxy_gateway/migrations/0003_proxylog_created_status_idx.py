# Generated manually for cross-database stats index

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "transparent_proxy_gateway",
            "0002_rename_gateway_pro_created_5e1c8a_idx_transparent_created_8cd6c2_idx",
        ),
    ]

    operations = [
        migrations.AddIndex(
            model_name="proxylog",
            index=models.Index(
                fields=["created_at", "status_code"],
                name="proxylog_created_status_idx",
            ),
        ),
    ]
