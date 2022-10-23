# Generated by Django 3.1.7 on 2021-03-14 20:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0018_auto_20210314_1844'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='promo',
            field=models.ForeignKey(blank=True, default='', null=True, on_delete=django.db.models.deletion.PROTECT, to='product.promocode'),
        ),
        migrations.AlterField(
            model_name='promocode',
            name='code',
            field=models.CharField(max_length=200, unique=True),
        ),
    ]
