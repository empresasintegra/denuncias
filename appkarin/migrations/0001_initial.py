# Generated by Django 5.2.1 on 2025-05-28 15:59

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Categoria',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=250)),
            ],
            options={
                'verbose_name': 'Categoria',
                'verbose_name_plural': 'Categorias',
            },
        ),
        migrations.CreateModel(
            name='Denuncia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descripcion', models.CharField(max_length=2000)),
                ('fecha', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Denuncia',
                'verbose_name_plural': 'Denuncias',
            },
        ),
        migrations.CreateModel(
            name='DenunciaEstado',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('estado', models.CharField(max_length=250)),
            ],
            options={
                'verbose_name': 'Estado de la denuncia',
                'verbose_name_plural': 'Estados de las denuncias',
            },
        ),
        migrations.CreateModel(
            name='RelacionEmpresa',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rol', models.CharField(max_length=500)),
            ],
        ),
        migrations.CreateModel(
            name='Tiempo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('intervalo', models.CharField(max_length=250)),
            ],
            options={
                'verbose_name': 'Tiempo',
                'verbose_name_plural': 'Tiempos',
            },
        ),
        migrations.CreateModel(
            name='Usuario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('anonimo', models.BooleanField(default=True)),
                ('nombre', models.CharField(max_length=250)),
                ('apellidos', models.CharField(max_length=250)),
                ('correo', models.EmailField(max_length=250)),
                ('celular', models.IntegerField()),
            ],
            options={
                'verbose_name': 'Usuario',
                'verbose_name_plural': 'Usuarios',
            },
        ),
        migrations.CreateModel(
            name='Archivo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.URLField(max_length=500)),
                ('denuncia', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='appkarin.denuncia')),
            ],
            options={
                'verbose_name': 'archivo',
                'verbose_name_plural': 'archivos',
            },
        ),
        migrations.CreateModel(
            name='EstadosDenuncia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateTimeField(auto_now_add=True)),
                ('denuncia', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='appkarin.denuncia')),
                ('estado', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='appkarin.denunciaestado')),
            ],
            options={
                'verbose_name': 'Estado de denuncia',
                'verbose_name_plural': 'Estados de denuncias',
            },
        ),
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('enunciado', models.CharField(max_length=500)),
                ('categoria', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='appkarin.categoria')),
            ],
            options={
                'verbose_name': 'Item',
                'verbose_name_plural': 'Items',
            },
        ),
        migrations.AddField(
            model_name='denuncia',
            name='item',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='appkarin.item'),
        ),
        migrations.AddField(
            model_name='denuncia',
            name='relacion_empresa',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='appkarin.relacionempresa'),
        ),
        migrations.AddField(
            model_name='denuncia',
            name='usuario',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='appkarin.usuario'),
        ),
        migrations.AlterUniqueTogether(
            name='denuncia',
            unique_together={('usuario_id', 'item_id', 'relacion_empresa_id')},
        ),
    ]
