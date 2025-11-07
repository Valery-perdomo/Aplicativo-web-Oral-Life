from django.contrib import admin
from .models import Paciente
from .models import LoginRecord
from .models import Cita
from .models import HistoriaClinica

admin.site.register(Paciente)
admin.site.register(LoginRecord)
admin.site.register(Cita)
admin.site.register(HistoriaClinica)




