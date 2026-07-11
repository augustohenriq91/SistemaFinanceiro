from django import forms
from .models import Receita, Despesa


class ReceitaForm(forms.ModelForm):
    class Meta:
        model = Receita
        fields = ['descricao', 'valor', 'data', 'categoria', 'conta', 'recebido']
        widgets = {
            'data': forms.DateInput(attrs={'type': 'date'}),
        }


class DespesaForm(forms.ModelForm):
    class Meta:
        model = Despesa
        fields = ['descricao', 'valor', 'data', 'categoria', 'conta', 'pago']
        widgets = {
            'data': forms.DateInput(attrs={'type': 'date'}),
        }