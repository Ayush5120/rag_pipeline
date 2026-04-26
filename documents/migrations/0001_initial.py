from django.db import migrations, models
import django.db.models.deletion
import pgvector.django


class Migration(migrations.Migration):

    initial = True
    dependencies = []

    operations = [
        pgvector.django.VectorExtension(),

        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=255)),
                ('file', models.FileField(upload_to='documents/')),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'Pending'),
                        ('processing', 'Processing'),
                        ('done', 'Done'),
                        ('failed', 'Failed'),
                    ],
                    default='pending',
                    max_length=20,
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),

        migrations.CreateModel(
            name='DocumentChunk',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('chunk_index', models.IntegerField()),
                ('content', models.TextField()),
                ('embedding', pgvector.django.VectorField(dimensions=384)),
                ('metadata', models.JSONField(default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('document', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='chunks',
                    to='documents.document',
                )),
            ],
            options={
                'ordering': ['chunk_index'],
            },
        ),

        migrations.CreateModel(
            name='QueryLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('query', models.TextField()),
                ('answer', models.TextField(blank=True)),
                ('retrieved_chunk_ids', models.JSONField(default=list)),
                ('latency_ms', models.IntegerField(default=0)),
                ('ragas_score', models.FloatField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),

        migrations.AddIndex(
            model_name='documentchunk',
            index=models.Index(fields=['document', 'chunk_index'], name='doc_chunk_idx'),
        ),

        migrations.RunSQL(
            sql="""
                CREATE INDEX IF NOT EXISTS documentchunk_embedding_ivfflat
                ON documents_documentchunk
                USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100);
            """,
            reverse_sql="DROP INDEX IF EXISTS documentchunk_embedding_ivfflat;",
        ),
    ]
