"""
URL configuration for gestion_360 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from gestor import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.mostrarLogin),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='registration/logout.html'), name='logout'),

    # 2. Vistas para cambio de contraseña (desde el panel de admin o estando logueado)
    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='registration/password_change_form.html'), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='registration/password_change_done.html'), name='password_change_done'),
    path('main/', views.mostraMain, name="main"),
    path('registrarProducto/', views.mostrarRegistrarProducto, name="registrarProducto"),
    path("registrarProducto/nuevo/", views.registrar_producto_view, name="registrarProducto"),
    path('Kardex/', views.mostrarKardex, name="kardex"),
    path('empleados/', views.mostrarEmpleados, name="empleados"),
    path('historial/', views.mostrarHistorial, name="historial"),
    path('reportes/', views.mostrarReportes, name="reportes"),
    path('proveedores/', views.mostrarProveedores, name="proveedores"),
    path('reportes/generar/', views.generar_reporte_view, name='generar_reporte'),
    path('password_reset/', 
         auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html',
                                               email_template_name='registration/password_reset_email.html',
                                               subject_template_name='registration/password_reset_subject.txt'), 
         name='password_reset'),
    
    path('password_reset/done/', 
         auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), 
         name='password_reset_done'),
    
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), 
         name='password_reset_confirm'),
    
    path('reset/done/', 
         auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), 
         name='password_reset_complete'),
    
    

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

