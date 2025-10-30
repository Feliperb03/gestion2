from django.contrib import admin
from .models import Producto, Proveedor, Empleado, Marca

# Registrar modelos existentes
admin.site.register(Producto)
admin.site.register(Proveedor)
admin.site.register(Empleado)


@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
	list_display = ('nombre', 'color')
	search_fields = ('nombre',)


from .models import Categoria


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'subcategoria')
    search_fields = ('nombre', 'subcategoria')