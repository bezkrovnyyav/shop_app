# Generated by Django 3.1.7 on 2021-04-17 16:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0033_auto_20210417_1931'),
    ]

    operations = [
        migrations.AlterField(
            model_name='basketitem',
            name='product',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='product.product', verbose_name='Товар'),
        ),
    ]