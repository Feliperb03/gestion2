from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .reports import generarReporte
from pathlib import Path
from django.conf import settings
from django.utils import timezone
from .forms import ProductoForm
from .forms import ProveedorForm
from .models import Producto, Proveedor, Marca, Categoria, KardexEntry
from django.db.models import F, Sum
from django.http import JsonResponse
from django.http import HttpResponse
from django.template.loader import render_to_string
from io import BytesIO
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
        data = request.POST.copy()
        if 'cantidad' in data:
            data.pop('cantidad')
        form = ProductoForm(data)
        if form.is_valid():
            producto = form.save(commit=False)
            if not getattr(producto, 'cantidad', None):
                producto.cantidad = 0
            producto.save()
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
    numero_factura = request.POST.get('numero_factura', '')[:100]

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
        numero_factura=numero_factura,
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
            'numero_factura': entry.numero_factura,
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
def mostrarDashboard(request):
    # Query productos cuyo stock actual (cantidad) está por debajo del stock mínimo
    low_stock = Producto.objects.filter(cantidad__lt=F('stock_minimo')).order_by('cantidad')

    # Obtener los productos con menor cantidad salida (suma de 'cantidad' en entradas de tipo 'salida')
    least_qs = (
        KardexEntry.objects
        .filter(tipo=KardexEntry.TIPO_SALIDA)
        .values('producto__id', 'producto__nombre')
        .annotate(salidas=Sum('cantidad'))
        .order_by('salidas')[:3]
    )
    least_sold_products = [{'nombre': r['producto__nombre'], 'salidas': r.get('salidas') or 0} for r in least_qs]

    # Top 3 productos con más salidas
    most_qs = (
        KardexEntry.objects
        .filter(tipo=KardexEntry.TIPO_SALIDA)
        .values('producto__id', 'producto__nombre')
        .annotate(salidas=Sum('cantidad'))
        .order_by('-salidas')[:3]
    )
    most_sold_products = [{'nombre': r['producto__nombre'], 'salidas': r.get('salidas') or 0} for r in most_qs]

    # Top 3 productos con más entradas
    entered_qs = (
        KardexEntry.objects
        .filter(tipo=KardexEntry.TIPO_ENTRADA)
        .values('producto__id', 'producto__nombre')
        .annotate(entradas=Sum('cantidad'))
        .order_by('-entradas')[:3]
    )
    most_entered_products = [{'nombre': r['producto__nombre'], 'entradas': r.get('entradas') or 0} for r in entered_qs]

    # Productos con mayor stock (orden descendente por cantidad)
    stock_qs = Producto.objects.all().order_by('-cantidad')[:10]
    most_stock_products = [{'id': p.id, 'nombre': p.nombre, 'cantidad': p.cantidad, 'stock_minimo': p.stock_minimo} for p in stock_qs]

    return render(request, 'dashboard.html', {
        'low_stock_products': low_stock,
        'least_sold_products': least_sold_products,
        'most_sold_products': most_sold_products,
        'most_entered_products': most_entered_products,
        'most_stock_products': most_stock_products,
    })
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
    """
    Procesa el formulario de reportes y muestra la tabla de resultados
    en la misma página.
    """
    if request.method != 'POST':
        return redirect('reportes')

    tipo = request.POST.get('tipo')
    fecha_inicio = request.POST.get('fecha_inicio')
    fecha_fin = request.POST.get('fecha_fin')
    categoria_id = request.POST.get('categoria') or None

    # preparar contexto
    categorias = Categoria.objects.all().order_by('nombre')
    report_rows = []

    # parsear fechas
    from datetime import datetime
    start_date = None
    end_date = None
    try:
        if fecha_inicio:
            start_date = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        if fecha_fin:
            end_date = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
    except Exception:
        start_date = end_date = None

    # filtro por categoria: obtener nombre si existe
    categoria_nombre = None
    if categoria_id:
        try:
            cat = Categoria.objects.get(pk=int(categoria_id))
            categoria_nombre = cat.nombre
        except Exception:
            categoria_nombre = None

    # Helper para formatear precios a '9.990 CLP'
    def fmt_price(p):
        try:
            if p is None:
                return ''
            s = f"{int(p):,}"
            # usar punto como separador de miles
            return s.replace(',', '.') + ' CLP'
        except Exception:
            return p

    # Tipo 'stock' -> snapshot de productos
    if tipo == 'stock':
        qs = Producto.objects.all()
        if categoria_nombre:
            qs = qs.filter(categoria=categoria_nombre)
        qs = qs.order_by('-cantidad')
        for p in qs:
            report_rows.append({
                'categoria': getattr(p, 'categoria', '') or '',
                'producto': p.nombre,
                'quien': '',
                'precio_venta': getattr(p, 'precio', None),
                'precio_compra': getattr(p, 'precio_compra', None),
                'precio_venta_fmt': fmt_price(getattr(p, 'precio', None)),
                'precio_compra_fmt': fmt_price(getattr(p, 'precio_compra', None)),
                'cantidad': '',
                'stock': p.cantidad,
                'stock_minimo': p.stock_minimo,
                'fecha_hora': ''
            })

    # Tipo 'todo' -> listar entradas y salidas
    elif tipo == 'todo':
        entries = KardexEntry.objects.select_related('producto').filter(tipo__in=[KardexEntry.TIPO_ENTRADA, KardexEntry.TIPO_SALIDA])
        if categoria_nombre:
            entries = entries.filter(producto__categoria=categoria_nombre)
        if start_date:
            entries = entries.filter(fecha__date__gte=start_date)
        if end_date:
            entries = entries.filter(fecha__date__lte=end_date)
        entries = entries.order_by('fecha')
        for e in entries:
            prod = e.producto
            report_rows.append({
                'categoria': getattr(prod, 'categoria', '') or '',
                'producto': prod.nombre if prod else '',
                'quien': '',
                'precio_venta': getattr(prod, 'precio', None) if prod else None,
                'precio_compra': getattr(prod, 'precio_compra', None) if prod else None,
                'precio_venta_fmt': fmt_price(getattr(prod, 'precio', None) if prod else None),
                'precio_compra_fmt': fmt_price(getattr(prod, 'precio_compra', None) if prod else None),
                # cantidad unificada: siempre exponer la cantidad del movimiento
                'cantidad': e.cantidad,
                'stock': e.stock_after if getattr(e, 'stock_after', None) is not None else (prod.cantidad if prod else None),
                'stock_minimo': getattr(prod, 'stock_minimo', None) if prod else None,
                'fecha_hora': e.fecha.strftime('%Y-%m-%d %H:%M:%S'),
                'movimiento': 'Entrada' if e.tipo == KardexEntry.TIPO_ENTRADA else 'Salida'
            })

    # Tipo 'salidas' o 'entradas' -> filas del kardex
    elif tipo in ('salidas', 'entradas', KardexEntry.TIPO_SALIDA, KardexEntry.TIPO_ENTRADA):
        if tipo == 'salidas':
            filtro = KardexEntry.TIPO_SALIDA
        elif tipo == 'entradas':
            filtro = KardexEntry.TIPO_ENTRADA
        else:
            filtro = tipo
        entries = KardexEntry.objects.select_related('producto').filter(tipo=filtro)
        if categoria_nombre:
            # Producto.categoria puede ser texto; filtrar por igualdad
            entries = entries.filter(producto__categoria=categoria_nombre)
        if start_date:
            entries = entries.filter(fecha__date__gte=start_date)
        if end_date:
            entries = entries.filter(fecha__date__lte=end_date)

        entries = entries.order_by('fecha')
        for e in entries:
            prod = e.producto
            report_rows.append({
                'categoria': getattr(prod, 'categoria', '') or '',
                'producto': prod.nombre if prod else '',
                'quien': '',
                'precio_venta': getattr(prod, 'precio', None) if prod else None,
                'precio_compra': getattr(prod, 'precio_compra', None) if prod else None,
                'precio_venta_fmt': fmt_price(getattr(prod, 'precio', None) if prod else None),
                'precio_compra_fmt': fmt_price(getattr(prod, 'precio_compra', None) if prod else None),
                # cantidad unificada: siempre exponer la cantidad del movimiento
                'cantidad': e.cantidad,
                'stock': e.stock_after if getattr(e, 'stock_after', None) is not None else (prod.cantidad if prod else None),
                'stock_minimo': getattr(prod, 'stock_minimo', None) if prod else None,
                'fecha_hora': e.fecha.strftime('%Y-%m-%d %H:%M:%S'),
                'movimiento': 'Entrada' if e.tipo == KardexEntry.TIPO_ENTRADA else 'Salida'
            })

    else:
        messages.error(request, 'Tipo de reporte no válido')

    return render(request, 'reportes.html', {
        'categories': categorias,
        'report_rows': report_rows,
        'selected_tipo': tipo,
        'selected_categoria': int(categoria_id) if categoria_id else None,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    })


def generar_reporte_pdf(request):
    """
    Genera un PDF con los mismos resultados del reporte.
    Acepta GET o POST con los mismos parámetros: tipo, fecha_inicio, fecha_fin, categoria.
    Intenta usar WeasyPrint si está instalado; si no, intenta xhtml2pdf.
    """
    # aceptar tanto POST como GET
    data = request.POST if request.method == 'POST' else request.GET
    tipo = data.get('tipo')
    fecha_inicio = data.get('fecha_inicio')
    fecha_fin = data.get('fecha_fin')
    categoria_id = data.get('categoria') or None

    # Reuse the existing report-building logic by calling generar_reporte_view-like code
    # (duplicate minimal part for reliability)
    categorias = Categoria.objects.all().order_by('nombre')
    report_rows = []
    from datetime import datetime
    start_date = None
    end_date = None
    try:
        if fecha_inicio:
            start_date = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        if fecha_fin:
            end_date = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
    except Exception:
        start_date = end_date = None

    categoria_nombre = None
    if categoria_id:
        try:
            cat = Categoria.objects.get(pk=int(categoria_id))
            categoria_nombre = cat.nombre
        except Exception:
            categoria_nombre = None

    def fmt_price(p):
        try:
            if p is None:
                return ''
            s = f"{int(p):,}"
            return s.replace(',', '.') + ' CLP'
        except Exception:
            return p

    if tipo == 'stock':
        qs = Producto.objects.all()
        if categoria_nombre:
            qs = qs.filter(categoria=categoria_nombre)
        qs = qs.order_by('-cantidad')
        for p in qs:
            report_rows.append({
                'categoria': getattr(p, 'categoria', '') or '',
                'producto': p.nombre,
                'quien': '',
                'precio_venta_fmt': fmt_price(getattr(p, 'precio', None)),
                'precio_compra_fmt': fmt_price(getattr(p, 'precio_compra', None)),
                'cantidad': '',
                'stock': p.cantidad,
                'stock_minimo': p.stock_minimo,
                'fecha_hora': ''
            })
    elif tipo == 'todo':
        entries = KardexEntry.objects.select_related('producto').filter(tipo__in=[KardexEntry.TIPO_ENTRADA, KardexEntry.TIPO_SALIDA])
        if categoria_nombre:
            entries = entries.filter(producto__categoria=categoria_nombre)
        if start_date:
            entries = entries.filter(fecha__date__gte=start_date)
        if end_date:
            entries = entries.filter(fecha__date__lte=end_date)
        entries = entries.order_by('fecha')
        for e in entries:
            prod = e.producto
            report_rows.append({
                'categoria': getattr(prod, 'categoria', '') or '',
                'producto': prod.nombre if prod else '',
                'quien': '',
                'precio_venta_fmt': fmt_price(getattr(prod, 'precio', None) if prod else None),
                'precio_compra_fmt': fmt_price(getattr(prod, 'precio_compra', None) if prod else None),
                'cantidad': e.cantidad,
                'stock': e.stock_after if getattr(e, 'stock_after', None) is not None else (prod.cantidad if prod else None),
                'stock_minimo': getattr(prod, 'stock_minimo', None) if prod else None,
                'fecha_hora': e.fecha.strftime('%Y-%m-%d %H:%M:%S'),
                'movimiento': 'Entrada' if e.tipo == KardexEntry.TIPO_ENTRADA else 'Salida'
            })
    elif tipo in ('salidas', 'entradas', KardexEntry.TIPO_SALIDA, KardexEntry.TIPO_ENTRADA):
        if tipo == 'salidas':
            filtro = KardexEntry.TIPO_SALIDA
        elif tipo == 'entradas':
            filtro = KardexEntry.TIPO_ENTRADA
        else:
            filtro = tipo
        entries = KardexEntry.objects.select_related('producto').filter(tipo=filtro)
        if categoria_nombre:
            entries = entries.filter(producto__categoria=categoria_nombre)
        if start_date:
            entries = entries.filter(fecha__date__gte=start_date)
        if end_date:
            entries = entries.filter(fecha__date__lte=end_date)
        entries = entries.order_by('fecha')
        for e in entries:
            prod = e.producto
            report_rows.append({
                'categoria': getattr(prod, 'categoria', '') or '',
                'producto': prod.nombre if prod else '',
                'quien': '',
                'precio_venta_fmt': fmt_price(getattr(prod, 'precio', None) if prod else None),
                'precio_compra_fmt': fmt_price(getattr(prod, 'precio_compra', None) if prod else None),
                'cantidad': e.cantidad,
                'stock': e.stock_after if getattr(e, 'stock_after', None) is not None else (prod.cantidad if prod else None),
                'stock_minimo': getattr(prod, 'stock_minimo', None) if prod else None,
                'fecha_hora': e.fecha.strftime('%Y-%m-%d %H:%M:%S'),
                'movimiento': 'Entrada' if e.tipo == KardexEntry.TIPO_ENTRADA else 'Salida'
            })
    else:
        # tipo no válido -> retornar mensaje
        return HttpResponse('Tipo de reporte no válido', status=400)

    # Render HTML for PDF
    context = {
        'report_rows': report_rows,
        'selected_tipo': tipo,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }
    html = render_to_string('reportes_pdf.html', context)

    # Intentar generar PDF con WeasyPrint, fallback a xhtml2pdf
    try:
        from weasyprint import HTML
        pdf = HTML(string=html).write_pdf()
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="reporte.pdf"'
        return response
    except Exception:
        try:
            from xhtml2pdf import pisa
            buffer = BytesIO()
            pisa_status = pisa.CreatePDF(html, dest=buffer)
            if pisa_status.err:
                return HttpResponse('Error generando PDF', status=500)
            response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="reporte.pdf"'
            return response
        except Exception:
            return HttpResponse('No se pudo generar PDF. Instala WeasyPrint o xhtml2pdf.', status=500)

def mostrarReportes(request):
    # Mostrar la página de reportes con la lista de categorías para el formulario
    categorias = Categoria.objects.all().order_by('nombre')
    return render(request, 'reportes.html', {'categories': categorias})


def registrar_producto_view(request):
    """
    Crear un producto: ignorar cualquier 'cantidad' enviado en el formulario
    para que el stock solo pueda modificarse a través del kardex.
    """
    if request.method == 'POST':
        # Hacemos una copia mutable del POST y retiramos 'cantidad' si viene
        data = request.POST.copy()
        if 'cantidad' in data:
            data.pop('cantidad')

        form = ProductoForm(data)
        if form.is_valid():
            producto = form.save(commit=False)
            # Forzar que el stock inicial no se cambie desde aquí (dejar valor por defecto o 0)
            if not getattr(producto, 'cantidad', None):
                producto.cantidad = 0
            producto.save()
            messages.success(request, 'producto guardado con exito')
            return redirect('registrarProducto')
        else:
            messages.error(request, 'faltan datos por rellenar')
    else:
        form = ProductoForm()

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
        # No devolvemos 'cantidad' en el JSON para evitar que UIs auto-llenadas
        # permitan editar el stock desde formularios.
        data = {
            'id': producto.id,
            'nombre': producto.nombre,
            'descripcion': producto.descripcion,
            'codigo_barras': producto.codigo_barras,
            'codigo_interno': producto.codigo_interno,
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
        # Ignorar 'cantidad' en la actualización: crear copia y eliminar si viene
        data = request.POST.copy()
        if 'cantidad' in data:
            data.pop('cantidad')

        form = ProductoForm(data, instance=producto)
        if form.is_valid():
            prod = form.save(commit=False)
            # Asegurar que no se modifica el stock desde aquí
            prod.cantidad = producto.cantidad
            prod.save()
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