# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-04-09 16:23
from __future__ import unicode_literals

import contour.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contour', '0006_auto_20180409_1710'),
    ]

    operations = [
        migrations.CreateModel(
            name='PlottedFigure',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(default=None, null=True, upload_to=contour.models.media_directory_path)),
                ('probabilistic_model', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contour.ProbabilisticModel')),
            ],
        ),
    ]
