# Generated by Django 2.2.16 on 2022-05-16 11:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0014_remove_post_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='image',
            field=models.ImageField(blank=True, upload_to='posts/', verbose_name='Изображение в посте'),
        ),
    ]
