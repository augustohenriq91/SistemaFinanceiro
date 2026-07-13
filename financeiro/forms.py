from django import forms
from decimal import Decimal, InvalidOperation
from datetime import date, datetime
from .models import Receita, Despesa, Conta, Categoria, EmprestimoCartao


def parse_valor_brl(value):
    if value in (None, ''):
        return value

    if isinstance(value, Decimal):
        return value

    texto = str(value).strip()
    texto = texto.replace('R$', '').replace(' ', '')
    texto = ''.join(ch for ch in texto if ch.isdigit() or ch in ',.-')

    if not texto:
        return value

    negativo = texto.startswith('-')
    texto = texto.replace('-', '')

    if ',' in texto:
        texto = texto.replace('.', '').replace(',', '.')
    elif '.' in texto:
        ultimo_ponto = texto.rfind('.')
        casas_decimais = len(texto) - ultimo_ponto - 1
        if 0 < casas_decimais <= 2:
            texto = texto[:ultimo_ponto].replace('.', '') + '.' + texto[ultimo_ponto + 1:]
        else:
            texto = texto.replace('.', '')

    if negativo:
        texto = '-' + texto

    try:
        return Decimal(texto)
    except InvalidOperation:
        return value


class BRLDecimalField(forms.DecimalField):
    def to_python(self, value):
        return super().to_python(parse_valor_brl(value))


def parse_data_brl(value):
    if value in (None, ''):
        return value

    if isinstance(value, date):
        return value

    texto = str(value).strip()

    for formato in ('%d/%m/%Y', '%Y-%m-%d'):
        try:
            return datetime.strptime(texto, formato).date()
        except ValueError:
            pass

    digitos = ''.join(ch for ch in texto if ch.isdigit())
    ano_atual = date.today().year

    if len(digitos) == 4:
        texto = f'{digitos[:2]}/{digitos[2:]}/{ano_atual}'
    elif len(digitos) == 6:
        ano = int(digitos[4:])
        ano += 2000 if ano < 70 else 1900
        texto = f'{digitos[:2]}/{digitos[2:4]}/{ano}'
    elif len(digitos) == 8:
        texto = f'{digitos[:2]}/{digitos[2:4]}/{digitos[4:]}'
    else:
        return value

    try:
        return datetime.strptime(texto, '%d/%m/%Y').date()
    except ValueError:
        return value


class BRLDateField(forms.DateField):
    def to_python(self, value):
        return super().to_python(parse_data_brl(value))


class ReceitaForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields['categoria'].queryset = Categoria.objects.filter(
                usuario=user,
                tipo='receita',
            ).order_by('nome')
            self.fields['conta'].queryset = Conta.objects.filter(usuario=user).order_by('nome')

    class Meta:
        model = Receita
        fields = ['descricao', 'valor', 'data', 'categoria', 'conta']
        widgets = {
            'data': forms.TextInput(attrs={'class': 'date-mask', 'placeholder': 'DD/MM/YYYY'}),
            'valor': forms.TextInput(attrs={
                'inputmode': 'decimal',
                'placeholder': '0,00',
                'class': 'currency',
                'autocomplete': 'off',
            }),
        }
        help_texts = {
            'valor': 'Digite o valor usando vírgula para centavos. Exemplo: 1500,75.',
            'data': 'Digite DD/MM/AAAA. Atalhos aceitos: 0907 vira 09/07 do ano atual.',
        }
        labels = {
            'descricao': 'Descrição',
        }
        field_classes = {
            'valor': BRLDecimalField,
            'data': BRLDateField,
        }

    def clean_valor(self):
        return parse_valor_brl(self.cleaned_data.get('valor'))


class DespesaForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields['categoria'].queryset = Categoria.objects.filter(
                usuario=user,
                tipo='despesa',
            ).order_by('nome')
            self.fields['conta'].queryset = Conta.objects.filter(usuario=user).order_by('nome')

    class Meta:
        model = Despesa
        fields = ['descricao', 'valor', 'data', 'categoria', 'conta', 'pago']
        widgets = {
            'data': forms.TextInput(attrs={'class': 'date-mask', 'placeholder': 'DD/MM/YYYY'}),
            'valor': forms.TextInput(attrs={
                'inputmode': 'decimal',
                'placeholder': '0,00',
                'class': 'currency',
                'autocomplete': 'off',
            }),
        }
        help_texts = {
            'valor': 'Digite o valor usando vírgula para centavos. Exemplo: 250,90.',
            'data': 'Digite DD/MM/AAAA. Atalhos aceitos: 0907 vira 09/07 do ano atual.',
        }
        labels = {
            'descricao': 'Descrição',
        }
        field_classes = {
            'valor': BRLDecimalField,
            'data': BRLDateField,
        }

    def clean_valor(self):
        return parse_valor_brl(self.cleaned_data.get('valor'))

class ContaForm(forms.ModelForm):
    class Meta:
        model = Conta
        fields = [
            'nome',
            'tipo',
            'saldo_inicial',
            'possui_cartao_credito',
            'dias_antes_fechamento_fatura',
            'dia_vencimento_fatura',
        ]
        widgets = {
            'saldo_inicial': forms.TextInput(attrs={
                'inputmode': 'decimal',
                'placeholder': '0,00',
                'class': 'currency',
                'autocomplete': 'off',
            }),
            'dias_antes_fechamento_fatura': forms.NumberInput(attrs={
                'min': '1',
                'max': '31',
                'placeholder': '5',
            }),
            'dia_vencimento_fatura': forms.NumberInput(attrs={
                'min': '1',
                'max': '31',
                'placeholder': '7',
            }),
        }
        labels = {
            'nome': 'Nome',
            'tipo': 'Tipo',
            'saldo_inicial': 'Saldo inicial',
            'possui_cartao_credito': 'Possui cartão de crédito?',
            'dias_antes_fechamento_fatura': 'Dias antes do vencimento da fatura',
            'dia_vencimento_fatura': 'Dia que vence a fatura',
        }
        help_texts = {
            'saldo_inicial': 'Informe o saldo inicial desta conta. Exemplo: 1200,00.',
        }
        field_classes = {
            'saldo_inicial': BRLDecimalField,
        }

    def clean_saldo_inicial(self):
        return parse_valor_brl(self.cleaned_data.get('saldo_inicial'))

    def clean(self):
        cleaned_data = super().clean()
        possui_cartao = cleaned_data.get('possui_cartao_credito')
        dias_antes_vencimento = cleaned_data.get('dias_antes_fechamento_fatura')
        dia_vencimento = cleaned_data.get('dia_vencimento_fatura')

        if possui_cartao:
            if not dias_antes_vencimento:
                self.add_error('dias_antes_fechamento_fatura', 'Informe quantos dias antes do vencimento a fatura fecha.')
            if not dia_vencimento:
                self.add_error('dia_vencimento_fatura', 'Informe o dia de vencimento da fatura.')

            for campo, valor in [
                ('dias_antes_fechamento_fatura', dias_antes_vencimento),
                ('dia_vencimento_fatura', dia_vencimento),
            ]:
                if valor and (valor < 1 or valor > 31):
                    self.add_error(campo, 'Informe um valor entre 1 e 31.')
        else:
            cleaned_data['dias_antes_fechamento_fatura'] = None
            cleaned_data['dia_vencimento_fatura'] = None

        return cleaned_data

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nome', 'tipo']
        labels = {
            'nome': 'Nome',
            'tipo': 'Tipo',
        }


class EmprestimoCartaoForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        cartoes = Conta.objects.filter(possui_cartao_credito=True)
        contas = Conta.objects.all()

        if user is not None:
            cartoes = cartoes.filter(usuario=user)
            contas = contas.filter(usuario=user)

        self.fields['cartao_utilizado'].queryset = cartoes.order_by('nome')
        self.fields['conta_recebimento'].queryset = contas.order_by('nome')
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
            'data_compra': forms.TextInput(attrs={'class': 'date-mask', 'placeholder': 'DD/MM/YYYY'}),
            'valor_total': forms.TextInput(attrs={
                'inputmode': 'decimal',
                'placeholder': '0,00',
                'class': 'currency',
                'autocomplete': 'off',
            }),
            'quantidade_parcelas': forms.NumberInput(attrs={
                'min': '1',
                'placeholder': '1',
            }),
        }
        labels = {
            'pessoa': 'Pessoa',
            'cartao_utilizado': 'Cartão utilizado',
            'conta_recebimento': 'Conta de recebimento',
            'descricao': 'Descrição',
            'valor_total': 'Valor total',
            'quantidade_parcelas': 'Quantidade de parcelas',
            'data_compra': 'Data da compra',
            'observacao': 'Observação',
        }
        help_texts = {
            'valor_total': 'Digite o valor total da compra no cartão. Exemplo: 1200,50.',
            'data_compra': 'Digite DD/MM/AAAA. Atalhos aceitos: 0907 vira 09/07 do ano atual.',
        }
        field_classes = {
            'valor_total': BRLDecimalField,
            'data_compra': BRLDateField,
        }

    def clean_valor_total(self):
        return parse_valor_brl(self.cleaned_data.get('valor_total'))

    def clean_quantidade_parcelas(self):
        quantidade = self.cleaned_data['quantidade_parcelas']
        if quantidade < 1:
            raise forms.ValidationError('Informe pelo menos 1 parcela.')
        return quantidade
