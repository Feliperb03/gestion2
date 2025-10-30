from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .reports import generarReporte
from pathlib import Path
from django.conf import settings
from django.utils import timezone
from .forms import ProductoForm
from .forms import ProveedorForm
from .models import Producto, Proveedor, Marca, Categoria, KardexEntry
from django.http import JsonResponse
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
    # Manejar GET y POST del formulario de producto, y pasar marcas/categorias/proveedores
    marcas = Marca.objects.all().order_by('nombre')
    categorias = Categoria.objects.all().order_by('nombre')
    proveedores = Proveedor.objects.all().order_by('nombre_pro')
    productos = Producto.objects.all().order_by('-id')
    # calcular el siguiente código interno (mostrar al usuario como read-only)
    from django.db.models import Max
    last_id = Producto.objects.aggregate(Max('id')).get('id__max') or 0
    next_codigo_interno = str(last_id + 1).zfill(6)

    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto añadido con éxito.')
            return redirect('registrarProducto')
        else:
            messages.error(request, 'Por favor revisa los datos del formulario.')
    else:
        form = ProductoForm(initial={'codigo_interno': next_codigo_interno})

    return render(request, 'registrarProducto.html', {
        'marcas': marcas,
        'categorias': categorias,
        'proveedores': proveedores,
        'productos': productos,
        'form': form,
        'next_codigo_interno': next_codigo_interno,
    })
def mostrarKardex(request):
    # Pasamos las últimas entradas del kardex para render inicial
    entradas = KardexEntry.objects.select_related('producto').all().order_by('-fecha')[:50]
    return render(request, 'kardex.html', {'entradas': entradas})


def kardex_buscar(request):
    """Buscar productos por nombre o código (AJAX GET). Devuelve lista JSON con id, nombre y stock."""
    q = request.GET.get('q', '').strip()
    if q:
        productos = Producto.objects.filter(nombre__icontains=q)[:50]
    else:
        productos = Producto.objects.all().order_by('-id')[:50]

    results = []
    for p in productos:
        results.append({
            'id': p.id,
            'nombre': p.nombre,
            'codigo_interno': p.codigo_interno,
            'cantidad': p.cantidad,
            'stock_minimo': p.stock_minimo,
        })
    return JsonResponse({'results': results})


def kardex_registrar(request):
    """Registrar una entrada o salida en el kardex (AJAX POST).

    Parámetros POST esperados: producto_id, tipo (entrada|salida), cantidad, motivo
    Devuelve JSON con el movimiento creado y stock actualizado.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    producto_id = request.POST.get('producto_id') or request.POST.get('producto')
    tipo = request.POST.get('tipo')
    try:
        cantidad = int(request.POST.get('cantidad') or 0)
    except ValueError:
        return JsonResponse({'error': 'Cantidad inválida'}, status=400)
    motivo = request.POST.get('motivo', '')[:200]

    if not producto_id or tipo not in (KardexEntry.TIPO_ENTRADA, KardexEntry.TIPO_SALIDA):
        return JsonResponse({'error': 'Parámetros incompletos'}, status=400)

    producto = get_object_or_404(Producto, pk=producto_id)

    # Validación: no permitir salidas mayores al stock actual
    if tipo == KardexEntry.TIPO_SALIDA and cantidad > producto.cantidad:
        return JsonResponse({'error': 'Cantidad mayor al stock actual'}, status=400)

    # Actualizar stock
    if tipo == KardexEntry.TIPO_ENTRADA:
        producto.cantidad = producto.cantidad + cantidad
    else:
        producto.cantidad = max(0, producto.cantidad - cantidad)
    producto.save()

    # Crear kardex entry
    entry = KardexEntry.objects.create(
        producto=producto,
        tipo=tipo,
        cantidad=cantidad,
        motivo=motivo,
        stock_after=producto.cantidad,
    )

    data = {
        'ok': True,
        'entry': {
            'id': entry.id,
            'producto_id': producto.id,
            'producto_nombre': producto.nombre,
            'tipo': entry.tipo,
            'cantidad': entry.cantidad,
            'motivo': entry.motivo,
            'fecha': entry.fecha.strftime('%Y-%m-%d %H:%M:%S'),
            'stock_after': entry.stock_after,
            'stock_minimo': producto.stock_minimo,
        }
    }
    return JsonResponse(data)
def mostrarEmpleados(request):
    return render(request, 'empleados.html')
def mostrarHistorial(request):
    return render(request, 'historial.html')
def mostrarReportes(request):
    return render(request, 'reportes.html')
def mostrarProveedores(request):
    """Lista proveedores y permite crear uno nuevo mediante el modal.

    GET: muestra la lista y el formulario vacío.
    POST: procesa creación de un nuevo proveedor y redirige para limpiar el formulario.
    """
    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            form.save()
            # después de guardar, redirigimos para evitar resubmit
            return redirect('proveedores')
    else:
        form = ProveedorForm()

    proveedores = Proveedor.objects.all().order_by('nombre_pro')
    return render(request, 'proveedores.html', {'proveedores': proveedores, 'form': form})


def proveedor_editar(request, pk):
    """Editar un proveedor existente."""
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method == 'POST':
        form = ProveedorForm(request.POST, instance=proveedor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Proveedor actualizado correctamente.')
            return redirect('proveedores')
    else:
        form = ProveedorForm(instance=proveedor)

    return render(request, 'editar_proveedor.html', {'form': form, 'proveedor': proveedor})


def proveedor_eliminar(request, pk):
    """Confirmar y eliminar un proveedor."""
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method == 'POST':
        proveedor.delete()
        messages.success(request, 'Proveedor eliminado correctamente.')
        return redirect('proveedores')
    return render(request, 'confirmar_eliminar_proveedor.html', {'proveedor': proveedor})
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
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            form.save()
            # mensaje según petición del usuario (texto exacto)
            messages.success(request, 'producto guardado con exito')
            return redirect('registrarProducto')
        else:
            # mensaje de error cuando faltan datos
            messages.error(request, 'faltan datos por rellenar')
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


def marca_nuevo(request):
    """Crear una Marca desde AJAX. Espera POST con 'marca_nombre' y 'marca_color'. Devuelve JSON."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    nombre = request.POST.get('marca_nombre') or request.POST.get('name')
    color = request.POST.get('marca_color') or request.POST.get('color') or '#000000'
    if not nombre:
        return JsonResponse({'error': 'Nombre requerido'}, status=400)

    nombre = nombre.strip()
    marca, created = Marca.objects.get_or_create(nombre=nombre, defaults={'color': color})
    if not created:
        marca.color = color
        marca.save()

    return JsonResponse({'id': marca.id, 'nombre': marca.nombre, 'color': marca.color}, status=201)


def categoria_nuevo(request):
    """Crear una Categoria desde AJAX. Espera POST con 'categoria_nombre' y 'categoria_subcategoria'. Devuelve JSON."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    nombre = request.POST.get('categoria_nombre') or request.POST.get('name')
    sub = request.POST.get('categoria_subcategoria') or request.POST.get('subcategoria') or ''
    if not nombre:
        return JsonResponse({'error': 'Nombre requerido'}, status=400)

    nombre = nombre.strip()
    categoria, created = Categoria.objects.get_or_create(nombre=nombre, defaults={'subcategoria': sub})
    if not created:
        categoria.subcategoria = sub
        categoria.save()

    return JsonResponse({'id': categoria.id, 'nombre': categoria.nombre, 'subcategoria': categoria.subcategoria}, status=201)


def producto_editar(request, pk):
    """Soporta GET (devuelve JSON con datos) y POST (actualiza el producto).
    GET: devuelve JSON con los campos del producto.
    POST: recibe datos del formulario, valida con ProductoForm y guarda.
    """
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'GET':
        data = {
            'id': producto.id,
            'nombre': producto.nombre,
            'descripcion': producto.descripcion,
            'codigo_barras': producto.codigo_barras,
            'codigo_interno': producto.codigo_interno,
            'cantidad': producto.cantidad,
            'stock_minimo': producto.stock_minimo,
            'precio': producto.precio,
            'precio_compra': producto.precio_compra,
            'categoria': producto.categoria,
            'marca': producto.marca.id if producto.marca else None,
            'proveedor': producto.proveedor.id if producto.proveedor else None,
            'fecha_entrada': producto.fecha_entrada.isoformat() if producto.fecha_entrada else None,
        }
        return JsonResponse(data)

    # POST -> actualizar
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            return JsonResponse({'ok': True}, status=200)
        else:
            # devolver errores de formulario
            return JsonResponse({'ok': False, 'errors': form.errors}, status=400)
    return JsonResponse({'error': 'Método no permitido'}, status=405)


def producto_eliminar(request, pk):
    """Eliminar un producto vía AJAX (POST). Devuelve JSON."""
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        producto.delete()
        return JsonResponse({'ok': True})
    return JsonResponse({'error': 'Método no permitido'}, status=405)
@login_required
def mi_vista_secreta(request):
    # Si el usuario no está logueado, Django lo redirigirá 
    # automáticamente a la URL 'login' que definimos.
    return render(request, 'mi_template_secreto.html')