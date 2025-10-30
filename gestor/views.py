from django.shortcuts import render, redirect
from django.contrib import messages
from .reports import generarReporte
from pathlib import Path
from django.conf import settings
from django.utils import timezone
from .forms import ProductoForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

##from models import Producto
##def listar_productos(request):
  ##  productos = Producto.objects.all()
    ##return render(request, 'gestor/listar_productos.html', {'productos': productos})

def mostrarLogin(request):
    return render(request, 'registro/login.html')
def mostrarIndex(request):
    return render(request, 'index.html')
def mostraMain(request):
    return render(request, 'main.html')
def mostrarRegistrarProducto(request):
    return render(request, 'registrarProducto.html')
def mostrarKardex(request):
    return render(request, 'kardex.html')
def mostrarEmpleados(request):
    return render(request, 'empleados.html')
def mostrarHistorial(request):
    return render(request, 'historial.html')
def mostrarReportes(request):
    return render(request, 'reportes.html')
def mostrarProveedores(request):
    return render(request, 'proveedores.html')
def generar_reporte_view(request):
    if request.method == 'POST':
        mensaje, url_publica = generarReporte()
        messages.success(request, f"{mensaje} → {url_publica}")
    return redirect('reportes')  # vuelve a la lista

def mostrarReportes(request):
    carpeta = Path(settings.MEDIA_ROOT) / "reportes"
    carpeta.mkdir(parents=True, exist_ok=True)

    archivos = []
    for p in sorted(carpeta.glob("*.xlsx"), key=lambda x: x.stat().st_mtime, reverse=True):
        archivos.append({
            "nombre": p.name,
            "url": f"{settings.MEDIA_URL}reportes/{p.name}",
            "fecha": timezone.datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.get_current_timezone())
        })
    return render(request, "reportes.html", {"archivos": archivos})
def registrar_producto_view(request):
    if request.method == "POST":
        form = ProductoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Producto registrado correctamente.")
            return redirect("registrarProducto")  # o a donde quieras volver
        else:
            messages.error(request, "Revisa los datos del formulario.")
    else:
        form = ProductoForm()

    return render(request, "registrarProducto.html", {"form": form})
def registrar_producto_view(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            # Guardamos el producto
            form.save()
            # Redirigimos a una página de éxito o listado de productos
            return redirect('listar_productos')  # Cambia esta URL por la que corresponda
    else:
        form = ProductoForm()  # Formulario vacío

    return render(request, 'registrarProducto.html', {'form': form})
@login_required
def mi_vista_secreta(request):
    # Si el usuario no está logueado, Django lo redirigirá 
    # automáticamente a la URL 'login' que definimos.
    return render(request, 'mi_template_secreto.html')