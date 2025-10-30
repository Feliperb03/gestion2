# gestor/forms.py
from django import forms
from .models import Producto

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ["nombre", "descripcion", "cantidad", "precio", "categoria", "fecha_entrada"]
        widgets = {
            "fecha_entrada": forms.DateInput(attrs={"type": "date"}),
        }
