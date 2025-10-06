# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api_gateway', '0005_delete_appointmentrequest'),
    ]

    operations = [
        migrations.AlterField(
            model_name='conversationsession',
            name='current_state',
            field=models.CharField(
                choices=[
                    ('idle', 'Ocioso'),
                    ('collecting_patient_info', 'Coletando Dados do Paciente'),
                    ('collecting_info', 'Coletando Informações'),
                    ('confirming_name', 'Confirmando Nome do Paciente'),
                    ('selecting_doctor', 'Selecionando Médico'),
                    ('choosing_schedule', 'Escolhendo Horário'),
                    ('confirming', 'Confirmando')
                ],
                default='idle',
                max_length=50
            ),
        ),
    ]
