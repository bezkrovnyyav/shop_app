# Generated by Django 3.1.7 on 2021-04-17 16:31

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('product', '0032_auto_20210416_1641'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='cost_of_delivery_on_curr',
            field=models.FloatField(default=0, verbose_name='Стоимость доставки в валюте'),
        ),
        migrations.CreateModel(
            name='BasketItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('qty', models.IntegerField(default=1, verbose_name='Количество')),
                ('price', models.FloatField(verbose_name='Стоимость за ед.')),
                ('title', models.CharField(max_length=200, verbose_name='Название товара')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='product.product', verbose_name='Товар')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
        ),
    ]