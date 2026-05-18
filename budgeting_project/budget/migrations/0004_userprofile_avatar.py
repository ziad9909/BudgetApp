from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('budget', '0003_userprofile_subscription_service_key'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/'),
        ),
    ]
