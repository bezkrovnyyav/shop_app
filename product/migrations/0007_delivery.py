# Generated by Django 3.1.7 on 2021-03-07 05:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0006_auto_20210227_0014'),
    ]

    operations = [
        migrations.CreateModel(
            name='Delivery',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='Delivery', max_length=350)),
                ('description', models.TextField(blank=True, null=True)),
            ],
        ),
    ]