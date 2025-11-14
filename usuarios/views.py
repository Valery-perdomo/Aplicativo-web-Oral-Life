from datetime import datetime, timedelta
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Group
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from .models import Paciente, Cita, HistoriaClinica, Mensaje

#roles
def is_superuser(user):
    return user.is_authenticated and user.is_superuser


def is_odontologo(user):
    return user.is_authenticated and user.groups.filter(name='odontologo').exists()


def group_required(group_name):
    """Decorador simple para restringir vistas por grupo"""
    def check(u):
        return u.is_authenticated and u.groups.filter(name=group_name).exists()
    return user_passes_test(check)

# login y registro
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.groups.filter(name='odontologo').exists():
                return redirect('odontologo_home')
            elif user.groups.filter(name='auxiliar').exists():
                return redirect('auxiliar_home')
            else:
                return redirect('home')
        else:
            messages.error(request, "Usuario o contraseña incorrectos.")
    return render(request, 'usuarios/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


class CustomPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = 'password_reset_confirm.html'
    success_url = reverse_lazy('login')


def register_view(request):
    if request.method == 'POST':
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 != password2:
            messages.error(request, 'Las contraseñas no coinciden.')
            return redirect('registro')

        if User.objects.filter(username=email).exists():
            messages.error(request, 'Este correo ya está registrado.')
            return redirect('registro')

        user = User.objects.create_user(
            username=email,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password1
        )
        Paciente.objects.create(user=user, nombre=f"{first_name} {last_name}", edad=0, email=email)
        messages.success(request, 'Registro exitoso. Ahora puedes iniciar sesión.')
        return redirect('login')

    return render(request, 'usuarios/registro.html')

#paciente
@login_required
def home_view(request):
    return render(request, 'usuarios/home_pacientes.html')

@login_required
def ver_historia_paciente(request):
    try:
        paciente = Paciente.objects.get(user=request.user)
    except Paciente.DoesNotExist:
        messages.error(request, "No tienes perfil de paciente.")
        return redirect('home')

    historias = HistoriaClinica.objects.filter(paciente=paciente).order_by('-fecha')
    return render(request, 'usuarios/historia_clinica.html', {'historias': historias})

@login_required
def agendar_cita(request):
    # Obtener fecha y hora actual
    ahora = datetime.now()
    fecha_actual = ahora.date()
    hora_actual = ahora.strftime('%H:%M')

    try:
        paciente = Paciente.objects.get(user=request.user)
    except Paciente.DoesNotExist:
        messages.error(request, "Debes crear un perfil de paciente primero.")
        return redirect('home')

    if request.method == 'POST':
        fecha = request.POST.get('fecha')
        hora = request.POST.get('hora')
        procedimiento = request.POST.get('procedimiento')

        if not procedimiento:
            messages.error(request, "Debes seleccionar un procedimiento antes de agendar.")
            return redirect('agendar_cita')

        try:
            fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
            hora_obj = datetime.strptime(hora, '%H:%M').time()
        except ValueError:
            messages.error(request, "Formato de fecha u hora inválido.")
            return redirect('agendar_cita')

        hora_inicio_mañana = datetime.strptime("08:00", "%H:%M").time()
        hora_fin_mañana = datetime.strptime("12:00", "%H:%M").time()
        hora_inicio_tarde = datetime.strptime("14:00", "%H:%M").time()
        hora_fin_tarde = datetime.strptime("18:00", "%H:%M").time()

        if not ((hora_inicio_mañana <= hora_obj < hora_fin_mañana) or (hora_inicio_tarde <= hora_obj < hora_fin_tarde)):
            messages.error(request, "El horario seleccionado está fuera del horario laboral (8:00–12:00 / 14:00–18:00).")
            return redirect('agendar_cita')

        cita_nueva = Cita(paciente=paciente, fecha=fecha_obj, hora=hora_obj, procedimiento=procedimiento)
        hora_inicio_dt = datetime.combine(fecha_obj, hora_obj)
        hora_fin_dt = datetime.combine(fecha_obj, cita_nueva.hora_fin())

        citas_en_dia = Cita.objects.filter(fecha=fecha_obj).exclude(estado='cancelada')
        for cita in citas_en_dia:
            cita_inicio_dt = datetime.combine(cita.fecha, cita.hora)
            cita_fin_dt = datetime.combine(cita.fecha, cita.hora_fin())

            if hora_inicio_dt < cita_fin_dt and hora_fin_dt > cita_inicio_dt:
                messages.error(
                    request,
                    f"No puedes agendar esta cita porque ya hay una cita desde las "
                    f"{cita_inicio_dt.strftime('%H:%M')} hasta las {cita_fin_dt.strftime('%H:%M')}."
                )
                return redirect('agendar_cita')

        cita_nueva.save()
        messages.success(
            request,
            f"✅ Cita de {cita_nueva.get_procedimiento_display()} agendada para "
            f"{fecha_obj.strftime('%d/%m/%Y')} a las {hora_obj.strftime('%H:%M')} "
            f"(duración aproximada: {int(cita_nueva.duracion().total_seconds() / 60)} min)."
        )
        return redirect('agendar_cita')

    citas = Cita.objects.filter(paciente=paciente).order_by('-fecha', '-hora')
    proxima_cita = citas.filter(estado__in=['pendiente', 'confirmada']).order_by('fecha', 'hora').first()

    return render(request, 'usuarios/agendar_cita.html', {
        'nombre_paciente': paciente.nombre,
        'proxima_cita': proxima_cita,
        'citas': citas,
        'today': fecha_actual,
        'hora_actual': hora_actual
    })


@login_required
def actualizar_estado_cita_paciente(request, cita_id, nuevo_estado):
    cita = get_object_or_404(Cita, id=cita_id, paciente__user=request.user)
    cita.estado = nuevo_estado
    cita.save()
    return redirect('agendar_cita')

#auxiliar
@group_required('auxiliar')
def auxiliar_home(request):
    resumen = {
        'total_pacientes': Paciente.objects.count(),
        'citas_pendientes': Cita.objects.filter(estado='pendiente').count(),
        'citas_confirmadas': Cita.objects.filter(estado='confirmada').count(),
    }
    return render(request, 'usuarios/auxiliar_home.html', {'resumen': resumen})

@group_required('auxiliar')
def auxiliar_citas(request):
    """
    Muestra solo las citas confirmadas para el auxiliar.
    """
    citas = (
        Cita.objects
        .select_related('paciente', 'paciente__user')
        .filter(estado='confirmada')  
        .order_by('-fecha', '-hora')
    )
    return render(request, 'usuarios/auxiliar_citas.html', {'citas': citas})

@login_required
def cancelar_cita(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id)
    if (
        request.user.groups.filter(name='auxiliar').exists()
        or request.user.groups.filter(name='odontologo').exists()
        or (hasattr(cita.paciente, 'user') and cita.paciente.user == request.user)
    ):
        nombre_paciente = cita.paciente.nombre
        cita.delete()
        messages.success(request, f"La cita de {nombre_paciente} fue eliminada correctamente.")
        if request.user.groups.filter(name='auxiliar').exists():
            return redirect('auxiliar_citas')
        elif request.user.groups.filter(name='odontologo').exists():
            return redirect('odo_citas')
        else:
            return redirect('agendar_cita')
    messages.error(request, "No tienes permiso para eliminar esta cita.")
    return redirect('home')

@group_required('auxiliar')
def crear_historia_clinica(request):
    pacientes = Paciente.objects.all().order_by('nombre')

    if request.method == "POST":
        paciente_id = request.POST.get("paciente")
        paciente = get_object_or_404(Paciente, id=paciente_id)

        if HistoriaClinica.objects.filter(paciente=paciente, fecha__date=datetime.today().date()).exists():
            messages.error(request, f"Ya existe una historia clínica registrada hoy para {paciente.nombre}.")
            return redirect('crear_historia_clinica')

        historia = HistoriaClinica.objects.create(
            paciente=paciente,
            auxiliar=request.user,
            nombre=request.POST.get("nombre"),
            fecha_nacimiento=request.POST.get("fecha_nacimiento") or None,
            edad=request.POST.get("edad") or None,
            sexo=request.POST.get("sexo"),
            tipo_id=request.POST.get("tipo_id"),
            numero_id=request.POST.get("numero_id"),
            estado_civil=request.POST.get("estado_civil"),
            direccion=request.POST.get("direccion"),
            telefono=request.POST.get("telefono"),
            ocupacion=request.POST.get("ocupacion"),
            nivel_educativo=request.POST.get("nivel_educativo"),
            nivel_socioeconomico=request.POST.get("nivel_socioeconomico"),
            contacto_emergencia=request.POST.get("contacto_emergencia"),
            telefono_emergencia=request.POST.get("telefono_emergencia"),
            motivo_consulta=request.POST.get("motivo"),
            historia_enfermedad=request.POST.get("historia_enfermedad"),
            antecedentes_familiares=", ".join([
                op for op in [
                    "Afecciones cardíacas" if request.POST.get("af_card") else "",
                    "Diabetes Mellitus" if request.POST.get("af_diab") else "",
                    "Hipertensión" if request.POST.get("af_hiper") else "",
                    "Epilepsia" if request.POST.get("af_epile") else "",
                    "Cáncer" if request.POST.get("af_cancer") else "",
                    request.POST.get("af_otro", "")
                ] if op
            ]),
            antecedentes_personales=request.POST.get("antecedentes_personales"),
            antecedentes_tox=", ".join([
                op for op in [
                    "Fuma" if request.POST.get("tox_fuma") else "",
                    "Alcohol" if request.POST.get("tox_alcohol") else "",
                    "Drogas" if request.POST.get("tox_drogas") else "",
                    "Alergia a anestesia" if request.POST.get("tox_alergico_anestesia") else "",
                    "Toma medicación" if request.POST.get("tox_medicamento") else "",
                ] if op
            ]),
            examen_fisico=request.POST.get("examen_fisico"),
            odontograma_detalle=request.POST.get("odontograma_detalle"),
            analisis_periodontal=request.POST.get("analisis_periodontal"),
            higiene=request.POST.get("higiene"),
            diagnostico=request.POST.get("diagnosticos"),
            pronostico=request.POST.get("pronostico"),
            plan_tratamiento="\n".join([
                f"{request.POST.get(f'diente_{i}')}, {request.POST.get(f'codigo_{i}')}, {request.POST.get(f'procedimiento_{i}')}, {request.POST.get(f'costo_{i}')}"
                for i in range(1, 6)
                if request.POST.get(f'diente_{i}')
            ]),
            firma_paciente=request.POST.get("firma_paciente"),
            firma_odontologo=request.POST.get("firma_odontologo"),
            fecha_firma=request.POST.get("fecha_firma") or None,
        )

        messages.success(request, f"Historia clínica registrada correctamente para {paciente.nombre}.")
        return redirect('auxiliar_citas')

    return render(request, 'usuarios/auxiliar_historial.html', {'pacientes': pacientes})

@group_required('auxiliar')
def editar_historia_clinica(request, historia_id):
    historia = get_object_or_404(HistoriaClinica, id=historia_id)

    if request.method == "POST":
        for campo in [
            "nombre", "fecha_nacimiento", "edad", "sexo", "tipo_id", "numero_id",
            "estado_civil", "direccion", "telefono", "ocupacion", "nivel_educativo",
            "nivel_socioeconomico", "contacto_emergencia", "telefono_emergencia",
            "motivo", "historia_enfermedad", "antecedentes_familiares", "antecedentes_personales",
            "antecedentes_tox", "examen_fisico", "odontograma_detalle", "analisis_periodontal",
            "higiene", "diagnostico", "pronostico", "plan_tratamiento", "firma_paciente",
            "firma_odontologo", "fecha_firma"
        ]:
            if campo in request.POST:
                setattr(historia, campo if campo != "motivo" else "motivo_consulta", request.POST[campo])

        historia.save()
        messages.success(request, "Historia clínica actualizada correctamente.")
        return redirect('lista_historias_clinicas')

    return render(request, 'usuarios/auxiliar_historial_edit.html', {'historia': historia})

@group_required('auxiliar')
def lista_historias_clinicas(request):
    historias = HistoriaClinica.objects.select_related('paciente', 'auxiliar').order_by('-fecha')
    return render(request, 'usuarios/lista_auxiliar_historial.html', {'historias': historias})

@group_required('auxiliar')
def detalle_historia_auxiliar(request, historia_id):
    """
    Muestra todos los datos registrados de una historia clínica (solo lectura).
    """
    historia = get_object_or_404(HistoriaClinica, id=historia_id)
    return render(request, 'usuarios/detalle_historia_auxiliar.html', {'historia': historia})

#odontologo
@group_required('odontologo')
def odontologo_home(request):
    resumen = {
        'total_pacientes': Paciente.objects.count(),
        'citas_hoy': Cita.objects.filter(fecha=datetime.today().date()).count(),
        'citas_pendientes': Cita.objects.filter(fecha__gte=datetime.today().date()).count(),
    }
    return render(request, 'usuarios/odontologo_home.html', {'resumen': resumen})

@group_required('odontologo')
def odo_citas(request):
    """
    Muestra solo las citas confirmadas visibles para el odontólogo.
    """
    citas = (
        Cita.objects
        .select_related('paciente', 'paciente__user')
        .filter(estado='confirmada')  
        .order_by('-fecha', '-hora')
    )
    return render(request, 'usuarios/odo_citas.html', {'citas': citas})

@group_required('odontologo')
def ver_historia_odontologo(request):
    historias = HistoriaClinica.objects.select_related('paciente', 'auxiliar').order_by('-fecha')
    return render(request, 'usuarios/odo_historial.html', {'historias': historias})

@group_required('odontologo')
def detalle_historia_odontologo(request, historia_id):
    historia = get_object_or_404(HistoriaClinica, id=historia_id)
    return render(request, 'usuarios/odo_historia_detalle.html', {'historia': historia})

#MENSAJES
@login_required
def chat_view(request):
    Mensaje.limpiar_antiguos()
    auxiliar = User.objects.filter(groups__name='auxiliar').first()
    if not auxiliar:
        messages.error(request, "No hay auxiliares disponibles para chatear.")
        return redirect('home')

    mensajes = Mensaje.objects.filter(
        Q(remitente=request.user, destinatario=auxiliar) |
        Q(remitente=auxiliar, destinatario=request.user)
    ).order_by('fecha_envio')

    if request.method == "POST":
        contenido = request.POST.get('mensaje')
        if contenido:
            Mensaje.objects.create(
                remitente=request.user,
                destinatario=auxiliar,
                contenido=contenido
            )
            return redirect('chat')

    return render(request, 'usuarios/chat_pacientes.html', {'mensajes': mensajes, 'auxiliar': auxiliar})

@login_required
def lista_chats(request):
    Mensaje.limpiar_antiguos()
    if request.user.groups.filter(name='auxiliar').exists():
        conversaciones = Mensaje.objects.filter(
            Q(remitente=request.user) | Q(destinatario=request.user)
        ).values_list('remitente', 'destinatario')
        ids = set()
        for remitente, destinatario in conversaciones:
            if remitente != request.user.id:
                ids.add(remitente)
            if destinatario != request.user.id:
                ids.add(destinatario)
        pacientes = User.objects.filter(id__in=ids).exclude(groups__name='auxiliar')
        return render(request, 'usuarios/lista_chats_auxiliar.html', {'pacientes': pacientes})
    return redirect('home')

@group_required('auxiliar')
def chat_auxiliar(request, username):
    Mensaje.limpiar_antiguos()
    paciente = get_object_or_404(User, username=username)
    mensajes = Mensaje.objects.filter(
        Q(remitente=request.user, destinatario=paciente) |
        Q(remitente=paciente, destinatario=request.user)
    ).order_by('fecha_envio')

    if request.method == "POST":
        contenido = request.POST.get('mensaje')
        if contenido:
            Mensaje.objects.create(
                remitente=request.user,
                destinatario=paciente,
                contenido=contenido
            )
            return redirect('chat_auxiliar', username=username)

    return render(request, 'usuarios/chat_auxiliar.html', {'mensajes': mensajes, 'paciente': paciente})
