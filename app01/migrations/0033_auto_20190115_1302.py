# Generated by Django 2.1.4 on 2019-01-15 13:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app01', '0032_auto_20190115_0615'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tbl_stat',
            name='callRate',
            field=models.FloatField(default=0, verbose_name='当前任务cps'),
        ),
    ]