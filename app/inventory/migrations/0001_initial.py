# Generated by Django 4.1.4 on 2022-12-14 16:54

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Label',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100)),
                ('value', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('is_primary', models.BooleanField(default=False)),
                ('priority', models.IntegerField()),
            ],
            options={
                'ordering': ('priority', '-created_at'),
            },
        ),
        migrations.CreateModel(
            name='ProductInventory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255)),
                ('cost_price', models.DecimalField(decimal_places=2, max_digits=12)),
                ('selling_price', models.DecimalField(decimal_places=2, max_digits=12)),
                ('default_quantity', models.IntegerField(default=0, verbose_name='quantity')),
                ('current_quantity', models.IntegerField(default=0, verbose_name='available_quantity')),
                ('minimum_stock_quantity', models.IntegerField(blank=True, default=0, null=True, verbose_name='minimum_stock_quantity')),
                ('category', models.CharField(max_length=255)),
                ('low_quantity', models.BooleanField(default=False)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='product_owner', to=settings.AUTH_USER_MODEL)),
                ('labels', models.ManyToManyField(to='inventory.label')),
            ],
            options={
                'verbose_name_plural': 'ProductInventories',
                'ordering': ('-created_at',),
                'unique_together': {('name', 'created_by')},
            },
        ),
    ]
