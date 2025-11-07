from django.urls import path
from django.shortcuts import redirect
from . import views
from .views import CustomPasswordResetConfirmView

urlpatterns = [

    #login y registro
    path('', lambda request: redirect('login')),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('registro/', views.register_view, name='registro'),

    #panel del paciente
    path('home_pacientes/', views.home_view, name='home'),
    path('agendar_cita/', views.agendar_cita, name='agendar_cita'),
    path('cita/<int:cita_id>/<str:nuevo_estado>/', views.actualizar_estado_cita_paciente, name='actualizar_estado_cita_paciente'),
    path('paciente/historia/', views.ver_historia_paciente, name='historia_clinica'),
    path('chat/', views.chat_view, name='chat'),

    #panel del odontologo
    path('odontologo/', views.odontologo_home, name='odontologo_home'),
    path('odontologo/citas/', views.odo_citas, name='odo_citas'),
    path('odontologo/historias/', views.ver_historia_odontologo, name='ver_historia_odontologo'),
    path('odontologo/historia/<int:historia_id>/', views.detalle_historia_odontologo, name='detalle_historia_odontologo'),
    path('citas/cancelar/<int:cita_id>/', views.cancelar_cita, name='cancelar_cita'),

    #panel del auxiliar
    path('auxiliar/', views.auxiliar_home, name='auxiliar_home'),
    path('auxiliar/citas/', views.auxiliar_citas, name='auxiliar_citas'),
    path('auxiliar/historia/', views.crear_historia_clinica, name='crear_historia_clinica'),
    path('auxiliar/historias/', views.lista_historias_clinicas, name='lista_historias_clinicas'),
    path('auxiliar/historias/editar/<int:historia_id>/', views.editar_historia_clinica, name='editar_historia_clinica'),
    path('auxiliar/historia/<int:historia_id>/', views.detalle_historia_auxiliar, name='detalle_historia_auxiliar'),
    path('mensajes/', views.lista_chats, name='lista_chats'),
    path('mensajes/<str:username>/', views.chat_auxiliar, name='chat_auxiliar'),
]
