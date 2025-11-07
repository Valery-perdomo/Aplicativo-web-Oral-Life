from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, datetime

#modelo paciente
class Paciente(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    nombre = models.CharField(max_length=100)
    edad = models.IntegerField()
    email = models.EmailField()

    def __str__(self):
        return self.nombre

#modelo historia clinica
class HistoriaClinica(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='historias')
    odontologo = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='historias_atendidas'
    )
    auxiliar = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='historias_registradas'
    )

    fecha = models.DateTimeField(auto_now_add=True)

    nombre = models.CharField(max_length=150, null=True, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    edad = models.IntegerField(null=True, blank=True)
    sexo = models.CharField(max_length=20, null=True, blank=True)
    tipo_id = models.CharField(max_length=30, null=True, blank=True)
    numero_id = models.CharField(max_length=30, null=True, blank=True)
    estado_civil = models.CharField(max_length=30, null=True, blank=True)
    direccion = models.CharField(max_length=150, null=True, blank=True)
    telefono = models.CharField(max_length=30, null=True, blank=True)
    ocupacion = models.CharField(max_length=100, null=True, blank=True)
    nivel_educativo = models.CharField(max_length=100, null=True, blank=True)
    nivel_socioeconomico = models.CharField(max_length=100, null=True, blank=True)
    contacto_emergencia = models.CharField(max_length=100, null=True, blank=True)
    telefono_emergencia = models.CharField(max_length=30, null=True, blank=True)

    motivo_consulta = models.TextField()

    historia_enfermedad = models.TextField(null=True, blank=True)

    antecedentes_familiares = models.TextField(null=True, blank=True)
    antecedentes_personales = models.TextField(null=True, blank=True)
    antecedentes_tox = models.TextField(null=True, blank=True)

    examen_fisico = models.TextField(null=True, blank=True)

    odontograma_detalle = models.TextField(null=True, blank=True)

    analisis_periodontal = models.TextField(null=True, blank=True)

    higiene = models.CharField(max_length=50, null=True, blank=True)

    diagnostico = models.TextField(blank=True, null=True)

    pronostico = models.CharField(max_length=50, null=True, blank=True)

    plan_tratamiento = models.TextField(null=True, blank=True)

    firma_paciente = models.CharField(max_length=150, null=True, blank=True)
    firma_odontologo = models.CharField(max_length=150, null=True, blank=True)
    fecha_firma = models.DateField(null=True, blank=True)

    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Historia de {self.paciente.nombre} - {self.fecha.strftime('%d/%m/%Y')}"


# modelo login
class LoginRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    login_time = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.login_time}"


#modelo cita
ESTADOS_CITA = [
    ('pendiente', 'Pendiente'),
    ('confirmada', 'Confirmada'),
    ('cancelada', 'Cancelada'),
]

from datetime import datetime, timedelta
from django.db import models

class Cita(models.Model):
    PROCEDIMIENTOS = [
        ('valoracion', 'Valoración (10 min)'),
        ('exodoncia_simple', 'Exodoncia Simple (40 min)'),
        ('exodoncia_quirurgica', 'Exodoncia Quirúrgica (1h 30min)'),
        ('montaje_ortodoncia', 'Montaje Ortodoncia (1h)'),
        ('control_ortodoncia', 'Control Ortodoncia (30 min)'),
        ('calza', 'Calza (30 min)'),
        ('higiene', 'Higiene (20 min)'),
        ('rehabilitacion', 'Rehabilitación (40 min)'),
        ('implantes', 'Implantes (1h)'),
        ('aclaramiento', 'Aclaramiento (1h)'),
    ]

    ESTADOS_CITA = [
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
    ]

    paciente = models.ForeignKey("Paciente", on_delete=models.CASCADE)
    fecha = models.DateField()
    hora = models.TimeField()
    procedimiento = models.CharField(max_length=50, choices=PROCEDIMIENTOS, default='valoracion')
    estado = models.CharField(max_length=20, choices=ESTADOS_CITA, default='pendiente')

    def duracion(self):
        duraciones = {
            'valoracion': timedelta(minutes=10),
            'exodoncia_simple': timedelta(minutes=40),
            'exodoncia_quirurgica': timedelta(hours=1, minutes=30),
            'montaje_ortodoncia': timedelta(hours=1),
            'control_ortodoncia': timedelta(minutes=30),
            'calza': timedelta(minutes=30),
            'higiene': timedelta(minutes=20),
            'rehabilitacion': timedelta(minutes=40),
            'implantes': timedelta(hours=1),
            'aclaramiento': timedelta(hours=1),
        }
        return duraciones.get(self.procedimiento, timedelta(minutes=10))

    def hora_fin(self):
        hora_inicio = datetime.combine(self.fecha, self.hora)
        return (hora_inicio + self.duracion()).time()

    def __str__(self):
        return f"{self.paciente.nombre} - {self.get_procedimiento_display()} ({self.fecha} {self.hora})"

#modelo mensaje
class Mensaje(models.Model):
    remitente = models.ForeignKey(
        User, related_name='mensajes_enviados', on_delete=models.CASCADE
    )
    destinatario = models.ForeignKey(
        User, related_name='mensajes_recibidos', on_delete=models.CASCADE
    )
    contenido = models.TextField()
    fecha_envio = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.remitente.username} → {self.destinatario.username}: {self.contenido[:30]}"

    @classmethod
    def limpiar_antiguos(cls):
        """Borra automáticamente los mensajes con más de 7 días."""
        limite = timezone.now() - timedelta(days=7)
        cls.objects.filter(fecha_envio__lt=limite).delete()
