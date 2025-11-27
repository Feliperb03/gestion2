# gestor/forms.py
from django import forms
from .models import Producto, Proveedor, Marca


class ProveedorModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        # Mostrar el RUT en el select
        return obj.rut_pro


class ProductoForm(forms.ModelForm):
    # Campos requeridos según petición del usuario
    nombre = forms.CharField(required=True)
    codigo_barras = forms.CharField(required=True)
    codigo_interno = forms.CharField(required=True)
    # 'cantidad' (stock) must not be editable via the product form; stock is
    # managed exclusively through the kardex. We do not include 'cantidad'
    # as an input field here so POSTs can't change it.
    stock_minimo = forms.IntegerField(required=True, min_value=0)
    # Precios en CLP: pedimos enteros (sin decimales). Usuario puede escribir '9.990' o '9990'
    precio = forms.IntegerField(required=True, min_value=0)
    precio_compra = forms.IntegerField(required=True, min_value=0)
    proveedor = ProveedorModelChoiceField(queryset=Proveedor.objects.all(), required=True)
    marca = forms.ModelChoiceField(queryset=Marca.objects.all(), required=False)

    def __init__(self, *args, **kwargs):
        # Normalizar entradas comunes (p.ej. decimales con coma) antes de bind
        data = kwargs.get('data')
        if data:
            data = data.copy()
            for fld in ('precio', 'precio_compra'):
                v = data.get(fld)
                if isinstance(v, str) and v:
                    # Usuarios pueden escribir '9.990' o '9,990' o '9990'.
                    # Normalizar quitando puntos y comas que actúan como separador de miles.
                    cleaned = v.replace('.', '').replace(',', '').replace(' ', '')
                    data[fld] = cleaned
            kwargs['data'] = data
        super().__init__(*args, **kwargs)

    class Meta:
        model = Producto
        fields = [
            "nombre", "descripcion", "codigo_barras", "codigo_interno",
            "stock_minimo", "precio", "precio_compra",
            "categoria", "marca", "proveedor", "fecha_entrada"
        ]
        widgets = {
            "fecha_entrada": forms.DateInput(attrs={"type": "date"}),
        }

from .models import Proveedor


class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = [
            'rut_pro', 'nombre_pro', 'telefono_pro', 'domicilio_fiscal_pro', 'correo_pro', 'direccion_pro'
        ]
        widgets = {
            'rut_pro': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00000000-0'}),
            'nombre_pro': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre o Razón Social'}),
            'telefono_pro': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+56 9 1111 1111'}),
            'domicilio_fiscal_pro': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Domicilio Fiscal'}),
            'correo_pro': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@empresa.cl'}),
            'direccion_pro': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dirección (Calle, Número, Ciudad)'}),
        }
