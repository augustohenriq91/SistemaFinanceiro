from datetime import date
from decimal import Decimal

from django.test import TestCase

from .forms import parse_data_brl, parse_valor_brl
from .models import Conta, EmprestimoCartao, ParcelaEmprestimo
from .views import data_vencimento_fatura, gerar_parcelas_emprestimo


class FormatacaoBrasileiraTests(TestCase):
    def test_parse_valor_brl_aceita_virgula_e_milhar(self):
        self.assertEqual(parse_valor_brl('R$ 1.234,56'), Decimal('1234.56'))
        self.assertEqual(parse_valor_brl('250,90'), Decimal('250.90'))
        self.assertEqual(parse_valor_brl('-3.133,77'), Decimal('-3133.77'))

    def test_parse_data_brl_aceita_data_completa_e_atalho(self):
        self.assertEqual(parse_data_brl('09/07/2026'), date(2026, 7, 9))
        self.assertEqual(parse_data_brl('2026-07-09'), date(2026, 7, 9))
        self.assertEqual(parse_data_brl('090726'), date(2026, 7, 9))


class CartaoEmprestadoTests(TestCase):
    def test_vencimento_respeita_fechamento_em_dias_antes_do_vencimento(self):
        self.assertEqual(
            data_vencimento_fatura(
                data_compra=date(2026, 7, 1),
                dias_antes_vencimento=5,
                dia_vencimento=7,
            ),
            date(2026, 7, 7),
        )
        self.assertEqual(
            data_vencimento_fatura(
                data_compra=date(2026, 7, 3),
                dias_antes_vencimento=5,
                dia_vencimento=7,
            ),
            date(2026, 8, 7),
        )

    def test_gera_parcelas_com_ajuste_de_centavos(self):
        cartao = Conta.objects.create(
            nome='Mercado Pago',
            tipo='banco',
            possui_cartao_credito=True,
            dias_antes_fechamento_fatura=5,
            dia_vencimento_fatura=7,
        )
        emprestimo = EmprestimoCartao.objects.create(
            pessoa='Cliente Teste',
            banco='Mercado Pago',
            cartao_utilizado=cartao,
            conta_recebimento=cartao,
            descricao='Compra teste',
            valor_total=Decimal('100.00'),
            quantidade_parcelas=3,
            data_compra=date(2026, 7, 1),
            dia_vencimento_cartao=7,
        )

        gerar_parcelas_emprestimo(emprestimo)

        parcelas = ParcelaEmprestimo.objects.filter(emprestimo=emprestimo).order_by('numero')
        self.assertEqual(parcelas.count(), 3)
        self.assertEqual(sum((parcela.valor for parcela in parcelas), Decimal('0.00')), Decimal('100.00'))
        self.assertEqual(parcelas[0].vencimento, date(2026, 7, 7))
