from django.db import models

class Producto(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    codigo_barras = models.CharField(max_length=100, blank=True)
    codigo_interno = models.CharField(max_length=100, blank=True)
    cantidad = models.PositiveIntegerField(default=0)  # stock
    stock_minimo = models.PositiveIntegerField(default=0)
    # Guardamos precios en pesos chilenos (CLP) como enteros (sin centavos)
    precio = models.PositiveIntegerField(null=False, default=0)  # precio de venta en CLP (ej: 9990)
    precio_compra = models.PositiveIntegerField(null=True, blank=True)  # precio de compra en CLP
    categoria = models.CharField(max_length=100, blank=True)
    fecha_entrada = models.DateField(null=True, blank=True)
    proveedor = models.ForeignKey('Proveedor', null=True, blank=True, on_delete=models.SET_NULL)
    marca = models.ForeignKey('Marca', null=True, blank=True, on_delete=models.SET_NULL)

    def save(self, *args, **kwargs):
        """
        Si codigo_interno no está presente, se genera automáticamente usando el id
        autoincremental del registro (rellenado con ceros a la izquierda).
        Implementación en dos pasos: salvo para obtener el id, luego si hace falta
        actualizo codigo_interno basado en ese id.
        """
        if not self.codigo_interno:
            # Guarda primero para asegurarnos de tener un id
            super().save(*args, **kwargs)
            # Usa el id como código interno (padded)
            self.codigo_interno = str(self.id).zfill(6)
            # Evita recursión infinita pasando update_fields
            super().save(update_fields=['codigo_interno'])
            return
        return super().save(*args, **kwargs)

    def __str__(self):
        return str(self.nombre)+" - "+str(self.descripcion)+" - "+str(self.cantidad)+" - "+str(self.precio)+" - "+str(self.categoria)+" - "+str(self.fecha_entrada)
class Proveedor(models.Model):
    nombre_pro = models.CharField(max_length=100)
    rut_pro = models.CharField(max_length=20, unique=True)
    telefono_pro = models.CharField(max_length=20, blank=True)
    direccion_pro = models.CharField(max_length=200, blank=True)
    domicilio_fiscal_pro = models.CharField(max_length=200, blank=True)
    correo_pro = models.EmailField(max_length=254, blank=True)

    def __str__(self):
        return f"{self.nombre_pro} - {self.rut_pro}"
class Empleado(models.Model):
    nombre_emp = models.CharField(max_length=30)
    correo = models.EmailField(max_length=25)
    tipo_doc = models.Choices
    nroDoc = models.CharField(max_length=10)
    telefono = models.IntegerField(max_length=11)
    direccion = models.CharField(max_length=40)
    def __str__(self):
        return str(self.nombre_emp)+" - "+str(self.correo)+" - "+str(self.tipo_doc)+" - "+str(self.nroDoc)+" - "+str(self.telefono)+" - "+str(self.direccion)
    
  # si no usas Django: from datetime import datetime
# from string import ascii_uppercase  # ya no lo necesitamos


class Marca(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    color = models.CharField(max_length=7, default="#000000")  # hex formato #rrggbb

    def __str__(self):
        return self.nombre


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    subcategoria = models.CharField(max_length=100, blank=True)

    def __str__(self):
        if self.subcategoria:
            return f"{self.nombre} / {self.subcategoria}"
        return self.nombre


class KardexEntry(models.Model):
    """Registro de movimientos de inventario (kardex).

    Almacena entradas y salidas por producto, cantidad, motivo y stock resultante.
    """
    TIPO_ENTRADA = 'entrada'
    TIPO_SALIDA = 'salida'
    TIPO_CHOICES = [
        (TIPO_ENTRADA, 'Entrada'),
        (TIPO_SALIDA, 'Salida'),
    ]

    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='kardex_entries')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    cantidad = models.PositiveIntegerField()
    motivo = models.CharField(max_length=200, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    stock_after = models.IntegerField()

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.fecha} {self.get_tipo_display()} {self.cantidad} - {self.producto.nombre} (stock: {self.stock_after})"

