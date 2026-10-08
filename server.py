from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from datetime import date
from decimal import Decimal, InvalidOperation
from xml.sax.saxutils import escape
import json, uuid, io, os
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data'
DATA.mkdir(exist_ok=True)
STATE=DATA/'state.json'
def write_state(s):
    temp=STATE.with_suffix('.tmp'); temp.write_text(json.dumps(s,ensure_ascii=False,indent=2)); temp.replace(STATE)
if not STATE.exists():
    write_state({'accounts':[
        {'id':'arq-eur','label':'ARQ • Euro','currency':'EUR','details':{'Recipient name':'TAIRO ROBERTO MIGUEL DE ASSUNÇÃO','IBAN':'LU47 4080 0000 4889 6497','Bank name':'Banking Circle S.A.','Bank address':'Bartycka 22B/21A, Warsaw, 00-716, Poland'}},
        {'id':'arq-usd','label':'ARQ • US Dollar','currency':'USD','details':{'Beneficiary name':'Tairo Assunção','Bank name':'Lead Bank','Account number':'215487907141','Routing number':'101019644','Account type':'Checking','Address':'Rua José Leite da Silva, 219, São José dos Campos, São Paulo 12209-110, Brazil'}}],
        'defaults':{'sender':'Tairo Roberto Miguel De Assunção','tax':'019.602.181-23','address':'Rua José Leite da Silva, nº 219, Jardim Bela Vista. São José dos Campos - SP, Brazil. Zip Code: 12209-110','email':'tairoroberto@gmail.com','client':'PSYTECH DIGITAL','clientAddress':'Ashgrove House, Ashgrove Industrial Estate, Dun Laoghaire Co Dublin A96N9K0','description':'Software development\nMobile Development Leader','amount':'5100.00','accountId':'arq-eur'},'invoices':[]})
def state(): return json.loads(STATE.read_text())
def validate(d,s):
    for k in ['number','issued','due','sender','client','description','amount','accountId']:
        if not str(d.get(k,'')).strip(): raise ValueError('Preencha o campo: '+k)
    if len(d['number'])>80: raise ValueError('Número muito longo')
    date.fromisoformat(d['issued']); date.fromisoformat(d['due'])
    if d['due']<d['issued']: raise ValueError('Vencimento anterior à emissão')
    try: amount=Decimal(str(d['amount']))
    except InvalidOperation: raise ValueError('Valor inválido')
    if not amount.is_finite() or amount<=0 or amount>Decimal('999999999.99') or amount!=amount.quantize(Decimal('.01')): raise ValueError('Use um valor positivo com até duas casas decimais')
    a=next((a for a in s['accounts'] if a['id']==d['accountId']),None)
    if not a: raise ValueError('Selecione uma conta válida')
    d=dict(d); d['account']=a; d['amount']=str(amount); return d

def pdf(d):
    from reportlab.platypus import Flowable, HRFlowable
    from reportlab.lib.styles import ParagraphStyle
    buf=io.BytesIO(); styles=getSampleStyleSheet()
    styles['Normal'].fontName='Helvetica'; styles['Normal'].fontSize=10; styles['Normal'].leading=14
    styles.add(ParagraphStyle('Sender',fontName='Helvetica-Bold',fontSize=17,leading=21))
    styles.add(ParagraphStyle('InvoiceLabel',fontName='Helvetica',fontSize=16,leading=20,alignment=TA_RIGHT))
    styles.add(ParagraphStyle('Right',parent=styles['Normal'],alignment=TA_RIGHT))
    styles.add(ParagraphStyle('Section',parent=styles['Normal'],fontName='Helvetica-Bold',spaceAfter=0))
    def p(t,style='Normal'): return Paragraph(escape(str(t)).replace('\n','<br/>'),styles[style])
    styles.add(ParagraphStyle('RightBold',parent=styles['Right'],fontName='Helvetica-Bold'))
    def rule(): return HRFlowable(width='100%',thickness=.65,color=colors.HexColor('#c8c8c8'),spaceBefore=0,spaceAfter=0)
    money=d['account']['currency']+' '+format(Decimal(d['amount']),',.2f')
    class TotalCard(Flowable):
        def __init__(self): Flowable.__init__(self);self.width=530;self.height=62
        def draw(self):
            c=self.canv
            c.setFillColor(colors.HexColor('#f1f6fa'));c.roundRect(0,0,self.width,62,5,fill=1,stroke=0)
            c.setFillColor(colors.black);right=self.width-16
            c.setFont('Helvetica-Bold',19);c.drawRightString(right,25,money)
            c.setFont('Helvetica',19);c.drawRightString(right-c.stringWidth(money,'Helvetica-Bold',19)-5,25,'Total')
    header=Table([[p(d['sender'],'Sender'),p('Invoice #'+d['number'],'InvoiceLabel')],
                  [Paragraph('<b>CPF:</b> '+escape(d.get('tax','')),styles['Normal']),Paragraph('<b>Creation date:</b> '+escape(d['issued'])+'<br/><b>Due date:</b> '+escape(d['due']),styles['Right'])]],colWidths=[310,220])
    header.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,0),10)]))
    def address_block(label,name,address):
        block=Table([[p(label,'Section')],[p(name,'Section')],[p(address)]],colWidths=[310],hAlign='LEFT')
        block.setStyle(TableStyle([('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0)]))
        return block
    story=[header,Spacer(1,14),rule(),Spacer(1,22),address_block('Bill From:',d['sender'],d.get('address','')),Spacer(1,16),address_block('Bill To:',d['client'],d.get('clientAddress','')),Spacer(1,24)]
    lines=d['description'].split('\n')
    description=Paragraph(escape(lines[0])+(' <br/><font color="#72909d">'+ '<br/>'.join(escape(x) for x in lines[1:])+'</font>' if len(lines)>1 else ''),styles['Normal'])
    service=Table([[p('Services','Section'),p('Amount','RightBold')],[description,p(money,'Right')]],colWidths=[384,146])
    service.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),('LINEBELOW',(0,0),(-1,0),.7,colors.HexColor('#c8c8c8')),('LINEBELOW',(0,1),(-1,1),.7,colors.HexColor('#c8c8c8')),('BOTTOMPADDING',(0,0),(-1,0),12),('TOPPADDING',(0,1),(-1,1),16),('BOTTOMPADDING',(0,1),(-1,1),16)]))
    story.extend([service,Spacer(1,14),TotalCard(),Spacer(1,28)])
    bank=[p('Pay to banking details below:','Section'),Spacer(1,4)]+[Paragraph('<b>'+escape(k)+':</b> '+escape(v),styles['Normal']) for k,v in d['account']['details'].items() if v]
    story.append(KeepTogether(bank))
    if d.get('notes'): story.extend([Spacer(1,18),p(d['notes'])])
    story.extend([Spacer(1,48),rule(),Spacer(1,20),Paragraph('<b>Questions?</b> Send an email to '+escape(d.get('email','')),styles['Normal'])])
    SimpleDocTemplate(buf,pagesize=(612,792),rightMargin=35,leftMargin=35,topMargin=35,bottomMargin=35,title='Invoice '+d['number'],author=d['sender']).build(story)
    return buf.getvalue()
class Handler(BaseHTTPRequestHandler):
    def respond(self,data,kind='application/json',code=200):
        if not isinstance(data,bytes): data=json.dumps(data,ensure_ascii=False).encode()
        self.send_response(code); self.send_header('Content-Type',kind); self.send_header('Content-Length',str(len(data))); self.send_header('Cache-Control','no-store'); self.end_headers(); self.wfile.write(data)
    def do_GET(self):
        if self.path=='/api/state': return self.respond(state())
        if self.path.startswith('/api/invoice/'):
            d=next((i for i in state()['invoices'] if i['id']==self.path.split('/')[-1]),None)
            return self.respond(pdf(d),'application/pdf') if d else self.respond({'error':'Não encontrada'},code=404)
        if self.path in ['/', '/index.html']: return self.respond((ROOT/'static/index.html').read_bytes(),'text/html; charset=utf-8')
        self.respond({'error':'Não encontrado'},code=404)
    def do_POST(self):
        try:
            size=int(self.headers.get('Content-Length',0))
            if size>200000: raise ValueError('Dados muito grandes')
            d=json.loads(self.rfile.read(size)); s=state()
            if self.path=='/api/accounts':
                accounts=d['accounts']
                if not isinstance(accounts,list) or not accounts: raise ValueError('Cadastre ao menos uma conta')
                ids=set()
                for a in accounts:
                    if not a.get('id') or a['id'] in ids or not a.get('label') or a.get('currency') not in ['EUR','USD'] or not isinstance(a.get('details'),dict) or not all(isinstance(k,str) and isinstance(v,str) for k,v in a['details'].items()): raise ValueError('Formato de conta inválido')
                    ids.add(a['id'])
                s['accounts']=accounts;write_state(s);return self.respond(s)
            if self.path in ['/api/preview','/api/generate']:
                d=validate(d,s); output=pdf(d)
                if self.path=='/api/preview': return self.respond(output,'application/pdf')
                if any(i['number']==d['number'] for i in s['invoices']): raise ValueError('Número já usado. Escolha outro número.')
                d['id']=uuid.uuid4().hex;s['invoices'].insert(0,d)
                s['defaults']={k:v for k,v in d.items() if k not in ['id','account','number','issued','due','notes']};write_state(s)
                (ROOT/'output/pdf'/('invoice-'+d['id']+'.pdf')).write_bytes(output)
                return self.respond({'id':d['id']})
            self.respond({'error':'Não encontrado'},code=404)
        except (ValueError,KeyError,TypeError) as e: self.respond({'error':str(e)},code=400)
        except Exception: self.respond({'error':'Não foi possível gerar o documento. Verifique os campos.'},code=500)
if __name__=='__main__':
    print('Gerador disponível em http://127.0.0.1:8765',flush=True)
    ThreadingHTTPServer(('127.0.0.1',8765),Handler).serve_forever()
