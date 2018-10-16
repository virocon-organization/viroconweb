# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2018-03-06 16:14
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import contour.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AdditionalContourOption',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('option_key', models.CharField(default=None, max_length=240, null=True)),
                ('option_value', models.CharField(default=None, max_length=240, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ContourPath',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='DistributionModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='peak period', max_length=50)),
                ('symbol', models.CharField(default='Tp', max_length=5)),
                ('distribution', models.CharField(choices=[
                    ('Normal', 'Normal Distribution'),
                    ('Weibull', 'Weibull'),
                    ('Lognormal_SigmaMu', 'Log-Normal'),
                    ('KernelDensity', 'Kernel Density')],
                    max_length=15)),
            ],
        ),
        migrations.CreateModel(
            name='EEDCScalar',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('x', models.DecimalField(decimal_places=5, max_digits=10, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='EnvironmentalContour',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fitting_method', models.CharField(default=None, max_length=240)),
                ('contour_method', models.CharField(default=None, max_length=240)),
                ('return_period', models.DecimalField(decimal_places=5, max_digits=10)),
                ('state_duration', models.DecimalField(decimal_places=5, max_digits=10)),
                ('path_of_statics', models.CharField(default=None, max_length=240, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ExtremeEnvDesignCondition',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('contour_path', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contour.ContourPath')),
            ],
        ),
        migrations.CreateModel(
            name='MeasureFileModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(default='MeasureFile', max_length=50)),
                ('upload_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('measure_file', models.FileField(upload_to='', validators=[contour.validators.validate_csv_upload])),
                ('path_of_statics', models.CharField(default=None, max_length=240, null=True)),
                ('primary_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='primary', to=settings.AUTH_USER_MODEL)),
                ('secondary_user', models.ManyToManyField(max_length=50, related_name='secondary', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ParameterModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('function', models.CharField(choices=[(None, 'None'), ('power3', 'power function'), ('exp3', 'exponential')], max_length=6)),
                ('x0', models.DecimalField(decimal_places=5, default=0.0, max_digits=10, null=True)),
                ('x1', models.DecimalField(decimal_places=5, default=0.0, max_digits=10, null=True)),
                ('x2', models.DecimalField(decimal_places=5, default=0.0, max_digits=10, null=True)),
                ('dependency', models.CharField(default='!', max_length=10)),
                ('name', models.CharField(default='empty', max_length=10)),
                ('distribution', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contour.DistributionModel')),
            ],
        ),
        migrations.CreateModel(
            name='ProbabilisticModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('upload_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('collection_name', models.CharField(default='VariablesCollection', max_length=50)),
                ('path_of_statics', models.CharField(default=None, max_length=240, null=True)),
                ('measure_file_model', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='contour.MeasureFileModel')),
                ('primary_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='variables_primary', to=settings.AUTH_USER_MODEL)),
                ('secondary_user', models.ManyToManyField(related_name='variables_secondary', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='environmentalcontour',
            name='probabilistic_model',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contour.ProbabilisticModel'),
        ),
        migrations.AddField(
            model_name='eedcscalar',
            name='EEDC',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contour.ExtremeEnvDesignCondition'),
        ),
        migrations.AddField(
            model_name='distributionmodel',
            name='probabilistic_model',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contour.ProbabilisticModel'),
        ),
        migrations.AddField(
            model_name='contourpath',
            name='environmental_contour',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contour.EnvironmentalContour'),
        ),
        migrations.AddField(
            model_name='additionalcontouroption',
            name='environmental_contour',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contour.EnvironmentalContour'),
        ),
    ]
