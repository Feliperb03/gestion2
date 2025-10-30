from django.db import models

class Producto(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    cantidad = models.PositiveIntegerField(default=0)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    categoria = models.CharField(max_length=100)
    fecha_entrada = models.DateField()

    def __str__(self):
        return str(self.nombre)+" - "+str(self.descripcion)+" - "+str(self.cantidad)+" - "+str(self.precio)+" - "+str(self.categoria)+" - "+str(self.fecha_entrada)
class Proveedor(models.Model):
    nombre_pro = models.CharField(max_length=30)
    rut_pro = models.CharField(max_length=10)
    telefono_pro = models.IntegerField(max_length=11)
    direccion_pro = models.CharField(max_length=40)
    def __str__(self):
        return str(self.nombre_pro)+" - "+str(self.rut_pro)+" - "+str(self.telefono_pro)+" - "+str(self.direccion_pro)
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

