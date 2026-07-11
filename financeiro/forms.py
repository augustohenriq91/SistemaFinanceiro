from django import forms
from .models import Receita, Despesa, Conta, Categoria, EmprestimoCartao


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

class ContaForm(forms.ModelForm):
    class Meta:
        model = Conta
        fields = [
            'nome',
            'tipo',
            'saldo_inicial',
            'possui_cartao_credito',
            'dia_fechamento_fatura',
            'dia_vencimento_fatura',
        ]
        labels = {
            'nome': 'Nome',
            'tipo': 'Tipo',
            'saldo_inicial': 'Saldo inicial',
            'possui_cartao_credito': 'Possui cartao de credito?',
            'dia_fechamento_fatura': 'Dia que fecha a fatura',
            'dia_vencimento_fatura': 'Dia que vence a fatura',
        }

    def clean(self):
        cleaned_data = super().clean()
        possui_cartao = cleaned_data.get('possui_cartao_credito')
        dia_fechamento = cleaned_data.get('dia_fechamento_fatura')
        dia_vencimento = cleaned_data.get('dia_vencimento_fatura')

        if possui_cartao:
            if not dia_fechamento:
                self.add_error('dia_fechamento_fatura', 'Informe o dia de fechamento da fatura.')
            if not dia_vencimento:
                self.add_error('dia_vencimento_fatura', 'Informe o dia de vencimento da fatura.')

            for campo, valor in [
                ('dia_fechamento_fatura', dia_fechamento),
                ('dia_vencimento_fatura', dia_vencimento),
            ]:
                if valor and (valor < 1 or valor > 31):
                    self.add_error(campo, 'Informe um dia entre 1 e 31.')
        else:
            cleaned_data['dia_fechamento_fatura'] = None
            cleaned_data['dia_vencimento_fatura'] = None

        return cleaned_data

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nome', 'tipo']


class EmprestimoCartaoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cartao_utilizado'].queryset = Conta.objects.filter(
            possui_cartao_credito=True
        ).order_by('nome')
        self.fields['cartao_utilizado'].required = True
        self.fields['conta_recebimento'].required = True

    class Meta:
        model = EmprestimoCartao
        fields = [
            'pessoa',
            'cartao_utilizado',
            'conta_recebimento',
            'descricao',
            'valor_total',
            'quantidade_parcelas',
            'data_compra',
            'observacao',
        ]
        widgets = {
            'data_compra': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'pessoa': 'Pessoa',
            'cartao_utilizado': 'Cartao utilizado',
            'conta_recebimento': 'Conta recebimento',
            'descricao': 'Descricao',
            'valor_total': 'Valor total',
            'quantidade_parcelas': 'Quantidade de parcelas',
            'data_compra': 'Data da compra',
            'observacao': 'Observacao',
        }

    def clean_quantidade_parcelas(self):
        quantidade = self.cleaned_data['quantidade_parcelas']
        if quantidade < 1:
            raise forms.ValidationError('Informe pelo menos 1 parcela.')
        return quantidade
