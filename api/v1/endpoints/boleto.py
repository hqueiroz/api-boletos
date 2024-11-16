#from typing import List 
from fastapi import APIRouter
from fastapi import status
from fastapi import Depends
from models.boleto_model import BoletoModel

#Imports boleto
import requests
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.colors import Color
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
from datetime import datetime, timedelta
import psycopg2
from sshtunnel import SSHTunnelForwarder
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from core.database import connect_to_postgresql,create_ssh_tunnel


# Bypass warning SQLModel select
from sqlmodel.sql.expression import Select, SelectOfScalar
SelectOfScalar.inherit_cache = True #type:ignore
Select.inherit_cache = True #type:ignore
# Fim Bypass

router = APIRouter()

# GET BOLETO
@router.post('/', status_code=status.HTTP_201_CREATED, response_model = BoletoModel)

def gerar_boleto_pdf(boleto: BoletoModel):

    # PARAMETROS FATURA
    schema_db = boleto.schema_db
    id_fatura = boleto.id_fatura

    # CONECTA BANCO
    tunnel, local_port = create_ssh_tunnel()
    conn = connect_to_postgresql(local_port)
    
    # CONSULTA FATURA
    query = f''' 
    set schema '{schema_db}';
    select 
    i.account_id,
    i.live_api_token ,
    b.ds_hash_id_iugu
    from 
    tb_parcela a, 
    tb_registro_cobranca_parcela b, 
    tb_registro_cobranca c,
    tb_base_calculo d,
    tb_empresa e,
    tb_entidade f,
    tb_tabela_calculo g,
    tb_cobranca h left join tb_subconta_comissao_iugu i on h.cd_subconta_comissao_iugu = i.cd_subconta_comissao_iugu 
    where 
    a.cd_parcela = b.cd_parcela 
    and b.cd_registro_cobranca = c.cd_registro_cobranca 
    and c.cd_base_calculo = d.cd_base_calculo 
    and d.cd_empresa = e.cd_empresa 
    and e.cd_entidade = f.cd_entidade 
    and d.cd_tabela_calculo = g.cd_tabela_calculo 
    and g.cd_cobranca = h.cd_cobranca 
    and b.ds_hash_id_iugu = '{id_fatura}'
    '''
    with conn.cursor() as cursor:
        cursor.execute(query)
        
        resultado = cursor.fetchone()

        account_id=resultado[0]
        live_api_token=resultado[1]

    # Fechar a conexão ao banco de dados
    conn.close()

    #### CONSULTA FATURA IUGU ####

    url = f"https://api.iugu.com/v1/invoices/{id_fatura}?api_token={live_api_token}"

    headers = {"accept": "application/json"}

    response = requests.get(url, headers=headers)

    dados = response.json()

    # Salva os dados em variáveis

    id = dados['id']
    due_date = dados['due_date']
    due_date_obj = datetime.strptime(due_date, "%Y-%m-%d")
    data_vencimento=due_date_obj.strftime('%d/%m/%Y')
    #currency = dados['currency']
    discount_cents = dados['discount_cents']
    email = dados['email']
    items_total_cents = dados['items_total_cents']
    valor = items_total_cents / 100
    #notification_url = dados['notification_url']
    #return_url = dados['return_url']
    status = dados['status']
    tax_cents = dados['tax_cents']
    total_cents = dados['total_cents']
    #total_paid_cents = dados['total_paid_cents']
    #taxes_paid_cents = dados['taxes_paid_cents']
    #paid_at = dados['paid_at']
    #paid_cents = dados['paid_cents']
    #cc_emails = dados['cc_emails']
    #financial_return_date = dados['financial_return_date']
    payable_with = dados['payable_with']
    #overpaid_cents = dados['overpaid_cents']
    #ignore_due_email = dados['ignore_due_email']
    #ignore_canceled_email = dados['ignore_canceled_email']
    #advance_fee_cents = dados['advance_fee_cents']
    #commission_cents = dados['commission_cents']
    early_payment_discount = dados['early_payment_discount']
    order_id = dados['order_id']
    updated_at = dados['updated_at']
    #credit_card_brand = dados['credit_card_brand']
    #credit_card_bin = dados['credit_card_bin']
    #credit_card_last_4 = dados['credit_card_last_4']
    #credit_card_captured_at = dados['credit_card_captured_at']
    #credit_card_tid = dados['credit_card_tid']
    #external_reference = dados['external_reference']
    #max_installments_value = dados['max_installments_value']
    payer_name = dados['payer_name'][:54]
    payer_email = dados['payer_email']
    payer_cpf_cnpj = dados['payer_cpf_cnpj']
    payer_phone = dados['payer_phone']
    payer_phone_prefix = dados['payer_phone_prefix']
    payer_address_zip_code = dados['payer_address_zip_code']
    payer_address_street = dados['payer_address_street']
    payer_address_district = dados['payer_address_district']
    payer_address_city = dados['payer_address_city']
    payer_address_state = dados['payer_address_state']
    payer_address_number = dados['payer_address_number']
    payer_address_complement = dados['payer_address_complement']
    payer_address_country = dados['payer_address_country']
    late_payment_fine = dados['late_payment_fine']
    late_payment_fine_cents = dados['late_payment_fine_cents']
    #split_id = dados['split_id']
    #external_payment_id = dados['external_payment_id']
    #external_payment_description = dados['external_payment_description']
    #payment_booklet_id = dados['payment_booklet_id']
    #subscription_id = dados['subscription_id']
    #credit_card_transaction = dados['credit_card_transaction']
    #account_id = dados['account_id']
    bank_account_branch = dados['bank_account_branch']
    bank_account_number = dados['bank_account_number']
    account_name = dados['account_name']
    secure_id = dados['secure_id']
    #secure_url = dados['secure_url']
    #customer_id = dados['customer_id']
    #customer_ref = dados['customer_ref']
    #customer_name = dados['customer_name']
    #user_id = dados['user_id']
    total = dados['total']
    #taxes_paid = dados['taxes_paid']
    #total_paid = dados['total_paid']
    #total_overpaid = dados['total_overpaid']
    #total_refunded = dados['total_refunded']
    fine_cents = dados['fine_cents']
    #commission = dados['commission']
    fines_on_occurrence_day = dados['fines_on_occurrence_day']
    total_on_occurrence_day = dados['total_on_occurrence_day']
    #fines_on_occurrence_day_cents = dados['fines_on_occurrence_day_cents']
    #total_on_occurrence_day_cents = dados['total_on_occurrence_day_cents']
    #refunded_cents = dados['refunded_cents']
    #remaining_captured_cents = dados['remaining_captured_cents']
    #advance_fee = dados['advance_fee']
    #estimated_advance_fee = dados['estimated_advance_fee']
    #paid = dados['paid']
    #original_payment_id = dados['original_payment_id']
    #double_payment_id = dados['double_payment_id']
    per_day_interest = dados['per_day_interest']
    per_day_interest_value = dados['per_day_interest_value']
    per_day_interest_cents = dados['per_day_interest_cents']
    interest = dados['interest']
    discount = dados['discount']
    #duplicated_invoice_id = dados['duplicated_invoice_id']
    bank_slip_extra_due = dados['bank_slip_extra_due']
    expire_date = due_date_obj + timedelta(days=bank_slip_extra_due)
    data_expiracao = expire_date.strftime('%d/%m/%Y')
    created_at = dados['created_at']
    created_at_iso = dados['created_at_iso']
    data_emissao_obj = datetime.fromisoformat(created_at_iso)
    data_emissao = data_emissao_obj.strftime('%d/%m/%Y')
    #authorized_at = dados['authorized_at']
    #authorized_at_iso = dados['authorized_at_iso']
    #expired_at = dados['expired_at']
    #expired_at_iso = dados['expired_at_iso']
    #refunded_at = dados['refunded_at']
    #refunded_at_iso = dados['refunded_at_iso']
    #canceled_at = dados['canceled_at']
    #canceled_at_iso = dados['canceled_at_iso']
    #protested_at = dados['protested_at']
    #protested_at_iso = dados['protested_at_iso']
    #chargeback_at = dados['chargeback_at']
    #chargeback_at_iso = dados['chargeback_at_iso']
    occurrence_date = dados['occurrence_date']
    #refundable = dados['refundable']
    #installments = dados['installments']
    transaction_number = dados['transaction_number']
    #payment_method = dados['payment_method']
    #financial_return_dates = dados['financial_return_dates']
    bankslip = dados['bank_slip']
    if bankslip:
        digitable_line = bankslip['digitable_line']
        barcode_data = bankslip['barcode_data']
        barcode = bankslip['barcode']
    #bank_slip.bank_slip_url = dados['bank_slip.bank_slip_url']
    #bank_slip.bank_slip_pdf_url = dados['bank_slip.bank_slip_pdf_url']
        bank_slip_bank = bankslip['bank_slip_bank']
    #bank_slip.bank_slip_status = dados['bank_slip.bank_slip_status']
    #bank_slip.bank_slip_error_code = dados['bank_slip.bank_slip_error_code']
    #bank_slip.bank_slip_error_message = dados['bank_slip.bank_slip_error_message']
        recipient_cpf_cnpj = bankslip['recipient_cpf_cnpj']
    pix = dados['pix']
    if pix:
        qrcode = pix['qrcode']
        qrcode_text = pix['qrcode_text']
    #status = pix['status']
    #pix.payer_cpf_cnpj = dados['pix.payer_cpf_cnpj']
    #pix.payer_name = dados['pix.payer_name']
    #pix.end_to_end_id = dados['pix.end_to_end_id']
    #pix.end_to_end_refund_id = dados['pix.end_to_end_refund_id']
    #pix.account_number_last_digits = dados['pix.account_number_last_digits']
    #id = dados['items.id']
    items = dados['items'][0]
    description = items['description']
    price_cents = items['price_cents']
    quantity = items['quantity']
    #items.created_at = dados['items.created_at']
    #items.updated_at = dados['items.updated_at']
    price = items['price']
    #early_payment_discounts = dados['early_payment_discounts']
    #split_rules = dados['split_rules']


    #### CONSULTA CEDENTE ###

    url_cedente = f"https://api.iugu.com/v1/accounts/{account_id}?api_token={live_api_token}"

    response_cedente = requests.get(url_cedente, headers=headers)

    dados_cedente = response_cedente.json()


    cedente_logo_url = dados_cedente['custom_logo_small_url']
    contatos = dados_cedente['contact_data']
    cedente = contatos['name'][:40]
    cedente_documento = contatos['document_number']
    cedente_endereco = contatos['full_address']
    endereco_completo = cedente_endereco.split(",")
    endereco_cedente = ", ".join(endereco_completo[:2])[:40]
    cidade_cep_cedente = ", ".join(endereco_completo[-2:])[:40]

    # Criando o PDF
    pdf_filename = f"/mnt/api-boletos/boletos/{id_fatura}.pdf"
    c = canvas.Canvas(pdf_filename, pagesize=A4)
    width, height = A4

    # Definir a cor cinza (usando o formato RGB)
    cinza = Color(0.929, 0.91, 0.875)  # Cinza médio (valores entre 0 e 1)
    cinza_escuro = Color(0.6, 0.6, 0.6)  # Cinza médio (valores entre 0 e 1)
    preto = Color(0,0,0)
    verde = Color(0.024, 0.58, 0.02)
    branco = Color(1,1,1)
    vermelho = Color(0.961, 0.298, 0.298)

    # Definir a cor de preenchimento
    c.setFillColor(cinza)

    # Desenhar o retângulo
    # Rect(x, y, largura, altura)
    # (100, 500) é a posição do canto inferior esquerdo do retângulo
    # 400 é a largura e 200 é a altura
    c.rect(30, height-190, 535, 165, fill=1, stroke=0)  # fill=1 significa que o retângulo será preenchido com a cor definida

    # Insere a Logo
    logo = ImageReader(cedente_logo_url)
    c.drawImage(logo, width - 120, height - 100, width=80, height=60, mask='auto')

    # Cabeçalho Linha 01
    c.setFillColor(preto)
    c.setFont('Helvetica-Bold', 7)
    c.drawString(40, height - 100, "CLIENTE")
    c.drawString(width - 260, height - 100, "CEDENTE")

    # # Dados Linha 01
    c.setFont('Courier', 9)
    c.drawString(40, height - 115, f"{payer_name}")
    c.drawString(width - 260, height - 115, f"{cedente}")

    # Cabeçalho Linha 02
    c.setFont('Helvetica-Bold', 7)
    c.drawString(40, height - 130, "CPF / CNPJ")
    c.drawString(width - 260, height - 130, "CPF/CNPJ CEDENTE")

    # Dados Linha 02
    c.setFont('Courier', 9)
    c.drawString(40, height - 145, f"{payer_cpf_cnpj}")
    c.drawString(width - 260, height - 145, f"{cedente_documento}")

    # Cabeçalho Linha 02
    c.setFont('Helvetica-Bold', 7)
    c.drawString(40, height - 160, "ENDEREÇO CLIENTE")
    c.drawString(width - 260, height - 160, "ENDEREÇO CEDENTE")

    # Dados Linha 02
    c.setFont('Courier', 9)
    c.drawString(40, height - 175, f"{payer_address_street},{payer_address_number}")
    c.drawString(width - 260, height - 175, f"{endereco_cedente}")

    # Dados Linha 02
    c.drawString(40, height - 185, f"{payer_address_city}, {payer_address_state}")
    c.drawString(width - 265, height - 185, f"{cidade_cep_cedente}")

    # Dados Fatura
    c.setFillColor(cinza_escuro)
    c.setFont('Courier', 9)
    c.drawString(40, height - 205, f"ID Fatura: {id}")
    c.drawRightString(width - 40, height - 205, f"Data de Emissão: {data_emissao}")

    # Detalhes Fatura
    c.setFillColor(preto)
    c.setFont('Courier', 14)
    c.drawString(40, height - 235, "Detalhes da Fatura")
    c.setFillColor(cinza_escuro)
    c.setFont('Courier', 9)
    c.drawRightString(width - 40, height - 225, "Vencimento")

    c.setFillColor(preto)
    c.setFont('Courier-Bold', 10)   
    c.drawRightString(width - 40, height - 240, f"{data_vencimento}")     

    c.setFillColor(cinza_escuro)
    c.setFont('Courier', 8) 
    c.drawString(40, height - 260, "Descrição")  
    c.drawRightString(width - 40, height - 260, "Valor")  
    
    # Linha de separação
    c.setDash(1, 2)
    c.setStrokeColor(cinza_escuro)
    c.setLineWidth(3)
    c.line(40, height - 270, width - 40, height - 270)

    # Descrição da Fatura

    # Estilos de texto
    c.setFont('Courier', 9) 
    styles = getSampleStyleSheet()
    style_normal = styles['Normal']  # Estilo normal para o parágrafo

    style_normal.fontName = 'Courier'
    style_normal.fontSize = 9
    style_normal.alignment = 4
    style_normal.bulletAnchor = 'start'
    
    # Posição onde o parágrafo será inserido
    x = 40
    y = height - 315  # A partir de 695 para não ficar muito embaixo

    # Criação do parágrafo de descrição
    paragrafo = Paragraph(description, style_normal)

    # Desenhar o parágrafo no canvas, em uma posição (x, y) definida
    paragrafo.wrapOn(c, 400, 200)  # Ajusta o parágrafo dentro de uma caixa de 400x200
    paragrafo.drawOn(c, x, y)  # Desenha o parágrafo no canvas
    
    
    # Dados do Valor
    c.setFont('Courier', 9)
    c.setFillColor(preto)
    c.drawRightString(width - 40, height - 310, f"{total}") 
    #c.setFont("Helvetica", 12)
    #c.drawString(40, height - 140, f"Cedente: {id}")
    #c.drawString(40, height - 160, f"Documento: {status}")

    # Linha de separação
    c.setDash(1, 2)
    c.setStrokeColor(cinza_escuro)
    c.setLineWidth(1)
    c.line(40, height - 345, width - 40, height - 345)    

    # Subtotal
    c.setFont('Courier', 9)
    c.setFillColor(preto)
    c.drawRightString(width - 110, height - 355, "Subtotal") 
    c.drawRightString(width - 40, height - 355, f"{total}") 

    # Linha de separação
    c.setStrokeColor(cinza_escuro)
    c.setLineWidth(1)
    c.line(40, height - 365, width - 40, height - 365)    

    # Multa e Juros
    c.setFont('Courier', 9)
    c.setFillColor(preto)
    if fines_on_occurrence_day:
        c.drawRightString(width - 110, height - 375, "Multa e Juros") 
        c.drawRightString(width - 40, height - 375, f"{fines_on_occurrence_day}") 
    else: 
        c.drawRightString(width - 110, height - 375, "Multa e Juros")
        c.drawRightString(width - 40, height - 375, "R$ 0,00")

    # Linha de separação
    c.setStrokeColor(cinza_escuro)
    c.setLineWidth(1)
    c.line(40, height - 385, width - 40, height - 385)    

    # Desconto
    c.setFont('Courier', 9)
    c.setFillColor(preto)
    if discount:
        c.drawRightString(width - 110, height - 395, "Desconto") 
        c.drawRightString(width - 40, height - 395, f"{discount}") 
    else:
        c.drawRightString(width - 110, height - 395, "Desconto") 
        c.drawRightString(width - 40, height - 395, "R$ 0,00") 

    # Linha de separação
    c.setStrokeColor(cinza_escuro)
    c.setLineWidth(1)
    c.line(40, height - 405, width - 40, height - 405)    

    # Desconto
    c.setFont('Courier-Bold', 9)
    c.setFillColor(preto)
    c.drawRightString(width - 110, height - 415, "TOTAL") 
    c.drawRightString(width - 40, height - 415, f"{total}") 

    # Linha de separação pontilhada
    c.setDash(1, 2)
    c.setStrokeColor(cinza_escuro)
    c.setLineWidth(3)
    c.line(40, height - 425, width - 40, height - 425)   
    c.setDash() 


    #### FORMAS DE PAGAMENTO ####

    ## VERIFICA STATUS DO BOLETO ##
    #print (f"STATUS DA FATURA: {status}")
           
    if status == 'paid':
        c.setFillColor(verde)
        c.rect(40, height-80, 120, 40, fill=1, stroke=0)  # fill=1 significa que o retângulo será preenchido com a cor definida
        c.setFillColor(branco)
        c.setFont('Courier-Bold', 16)
        c.drawString(45, height - 65, "FATURA PAGA")

    if status == 'canceled':
        c.setFillColor(vermelho)
        c.rect(40, height-80, 165, 40, fill=1, stroke=0)  # fill=1 significa que o retângulo será preenchido com a cor definida
        c.setFillColor(branco)
        c.setFont('Courier-Bold', 16)
        c.drawString(45, height - 65, "FATURA CANCELADA")
    
    if status == 'expired':
        c.setFillColor(vermelho)
        c.rect(40, height-80, 160, 40, fill=1, stroke=0)  # fill=1 significa que o retângulo será preenchido com a cor definida
        c.setFillColor(branco)
        c.setFont('Courier-Bold', 16)
        c.drawString(45, height - 65, "FATURA EXPIRADA")
    
    else:
        if bankslip:
            c.setFillColor(preto)
            c.setFont('Courier', 14)
            c.drawString(40, height - 445, "Pagar Fatura")
            c.setFont('Courier', 8)
            c.drawString(40, height - 460, "Efetue o pagamento com segurança pela internet ou em uma agência bancária.")
            c.setFont('Courier-Bold', 8)
            c.drawString(40, height - 480, "Confira as opções de pagamento para esta fatura:")

            # Imagem SSL
            ssl = 'ssl.png'
            c.drawImage(ssl, width - 100, height - 490, width=65, height=60)

            # Linha de separação pontilhada
            c.setDash(1, 2)
            c.setStrokeColor(cinza_escuro)
            c.setLineWidth(1)
            c.line(40, height - 495, width - 40, height - 495)   
            c.setDash() 

            # QR Code (Imagem)
            if qrcode:
                qrcode_url = qrcode

                response_qrcode = requests.get(qrcode)

                if response_qrcode.status_code == 200:
                    # A imagem foi baixada com sucesso, agora carregamos ela para o PDF
                    img_qrcode = ImageReader(qrcode_url)
                #img_qrcode = ('qrcode.png')
                    c.drawImage(img_qrcode, 35, height - 595, width=95, height=95)

                # Posição onde o parágrafo será inserido
                x = 135
                y = height - 555  # A partir de 695 para não ficar muito embaixo

                descricao_pix = 'O Pix é a nova modalidade de transferências do banco central, que funcionam 24 horas por dia e possuem confirmação em tempo real. Procure em seu aplicativo de banco ou conta digital a funcionalidade e escaneie o QR Code ao lado para efetuar um pagamento.'

                # Criação do parágrafo de descrição
                paragrafo_pix = Paragraph(descricao_pix, style_normal)

                # Desenhar o parágrafo no canvas, em uma posição (x, y) definida
                paragrafo_pix.wrapOn(c, 400, 200)  # Ajusta o parágrafo dentro de uma caixa de 400x200
                paragrafo_pix.drawOn(c, x, y)  # Desenha o parágrafo no canvas


            # Linha de separação pontilhada
            c.setDash(1, 2)
            c.setStrokeColor(cinza_escuro)
            c.setLineWidth(1)
            c.line(40, height - 600, width - 40, height - 600)   
            c.setDash() 

            # Boleto 1a Linha
            c.setStrokeColor(preto)
            c.line(40, height - 605, 40, height - 630)
            c.line(40, height - 630, width - 40, height - 630)
            c.drawString(50, height - 610, "IUGU IP S.A.")
            c.setFont('Courier', 9)
            c.drawString(50, height - 625, f"{digitable_line}")
            iugu_logo = ('iugu_logo.png')
            c.drawImage(iugu_logo, width - 100, height - 627, width=55, height=22)


            # Boleto 2a Linha
            c.setStrokeColor(preto)
            c.line(40, height - 635, 40, height - 660)
            c.line(40, height - 660, width - 135, height - 660)
            c.line(width - 130, height - 635, width - 130, height - 660)
            c.line(width - 130, height - 660, width - 40, height - 660)
            c.setStrokeColor(cinza_escuro)
            c.setFont('Courier', 8)
            c.drawString(50, height - 640, "LOCAL DE PAGAMENTO")
            c.drawRightString(width - 40, height - 640, "NOSSO NÚMERO")
            c.setFont('Courier-Bold', 9)
            c.setStrokeColor(preto)
            c.drawString(50, height - 655, "Pagável em qualquer banco ou lotérica.")
            c.drawRightString(width - 40, height - 655, f"{transaction_number}")

            # Boleto 3a Linha
            c.line(40, height - 665, 40, height - 695)
            c.line(40, height - 695, width - 320, height - 695)
            c.line(width - 315, height - 665, width - 315, height - 695)
            c.line(width - 315, height - 695, width - 135, height - 695)
            c.line(width - 130, height - 665, width - 130, height - 695)
            c.line(width - 130, height - 695, width - 40, height - 695)
            c.setStrokeColor(cinza_escuro)
            c.setFont('Courier', 8)
            c.drawString(50, height - 670, "BENEFICIÁRIO")
            c.drawString(width - 310, height - 670, "SACADOR/AVALISTA")
            c.drawRightString(width - 40, height - 670, "VENCIMENTO")
            c.setStrokeColor(preto)
            c.setFont('Courier-Bold', 9)
            c.drawString(50, height - 680, f"{cedente}")
            c.setFont('Courier', 8)
            c.drawString(50, height - 690, f"CNPJ: {cedente_documento}")
            c.setFont('Courier-Bold', 9)
            c.drawRightString(width - 40, height - 690, f"{data_vencimento}")

            # Boleto 4a Linha
            c.setStrokeColor(preto)
            c.line(40, height - 700, 40, height - 730)
            c.line(40, height - 730, width - 135, height - 730)
            c.line(width - 130, height - 700, width - 130, height - 730)
            c.line(width - 130, height - 730, width - 40, height - 730)
            c.setStrokeColor(cinza_escuro)
            c.setFont('Courier', 8)
            c.drawString(50, height - 705, "INSTRUÇÕES")
            c.drawRightString(width - 40, height - 705, "MULTA/JUROS")
            c.setFont('Courier-Bold', 9)
            c.drawString(50, height - 715, f"NÃO RECEBER APÓS {data_expiracao}")
            c.setFont('Courier-Bold', 9)
            c.drawString(50, height - 725, "")
            c.setFont('Courier-Bold', 9)
            c.drawRightString(width - 40, height - 725, f"{fines_on_occurrence_day}")

            # Boleto 5a Linha
            c.setStrokeColor(preto)
            c.line(40, height - 735, 40, height - 765)
            c.line(40, height - 765, width - 135, height - 765)
            c.line(width - 130, height - 735, width - 130, height - 765)
            c.line(width - 130, height - 765, width - 40, height - 765)
            c.setStrokeColor(cinza_escuro)
            c.setFont('Courier', 8)
            c.drawString(50, height - 740, "CLIENTE")
            c.drawRightString(width - 40, height - 740, "VALOR A PAGAR")
            c.setFont('Courier-Bold', 9)
            c.drawString(50, height - 750, f"{payer_name}")
            c.setFont('Courier-Bold', 8)
            c.drawString(50, height - 760, f"CPF/CNPJ: {payer_cpf_cnpj}")
            c.setFont('Courier-Bold', 9)
            c.drawRightString(width - 40, height - 760, f"{total}")

            # CÓDIGO DE BARRAS
            c.setFont('Courier-Bold', 9)
            c.drawString(40, height - 775, "Código de Barras:")
            #c.drawString(50, height - 775, f"{linha_digitavel}")

            # Código de Barras (Imagem)
            barcode_url = barcode

            response = requests.get(barcode_url)

            if response.status_code == 200:
                # A imagem foi baixada com sucesso, agora carregamos ela para o PDF
                codigo_barras = ImageReader(barcode_url)

                c.drawImage(codigo_barras, 35, height - 830, width=300, height=50)

            #img_barcode = ('barcode.png')
            #c.drawImage(img_barcode, 35, height - 825, width=300, height=50)

            c.setStrokeColor(preto)
            c.setFont('Courier-Bold', 9)
            c.drawString(350, height - 775, "Autenticação Mecânica:")

    
    # Finaliza o PDF
    c.save()

    ### SALVAR O ARQUIVO NO S3
    bucket_name = 'isa-synd-boletos'
    object_name = pdf_filename.split("/")[-1]

    # Criando o cliente S3
    s3_client = boto3.client('s3')

    try:
        # Fazendo upload do arquivo PDF
        s3_client.upload_file(pdf_filename, bucket_name, object_name)

        # URL do arquivo no S3
        url_boleto = f"https://{bucket_name}.s3.amazonaws.com/{object_name}"

    except FileNotFoundError:
        return f"Erro: O arquivo {pdf_filename} não foi encontrado."
    except NoCredentialsError:
        return "Erro: Credenciais AWS não encontradas."
    except PartialCredentialsError:
        return "Erro: As credenciais AWS estão incompletas."
    except Exception as e:
        return f"Erro ao fazer upload para o S3: {str(e)}"

    boleto_gerado = BoletoModel(schema_db=schema_db,id_fatura=id_fatura,status_fatura=status,url_boleto=url_boleto)
    
    return boleto_gerado

