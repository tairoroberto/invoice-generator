# Invoice Studio

Gerador local de invoices em inglês, com interface em português. Sem serviços externos.

## Abrir no Mac

Dê dois cliques em `Iniciar.command`. Mantenha o terminal aberto enquanto usa o gerador em http://127.0.0.1:8765. Para encerrar, pressione Ctrl+C no terminal. Se a página abrir antes do servidor, recarregue-a.

Alternativa: instale `python3 -m pip install -r requirements.txt` e execute `python3 server.py` nesta pasta.

## Todo mês

1. Selecione ARQ Euro ou ARQ US Dollar. A moeda segue a conta; o valor não é convertido.
2. Confira número, emissão, vencimento, valor, serviço e cliente.
3. Clique em **Visualizar PDF** e confira os dados bancários.
4. Clique em **Salvar e baixar PDF**. Envie o documento pelo canal habitual.

PSYTECH DIGITAL, endereço, emitente e EUR 5.100 foram copiados da invoice de referência. São editáveis. Nenhuma invoice é enviada automaticamente. Não foi acrescentado SWIFT às contas ARQ porque não foi informado.

## Persistência e backup

- `data/state.json`: contas, últimos dados utilizados e histórico completo.
- `output/pdf/`: cópias dos PDFs salvos, identificadas por ID interno.
- Cada invoice guarda uma cópia dos dados bancários daquela emissão; editar uma conta não altera invoices anteriores.
- **Gerenciar contas** oferece uma tabela com + Adicionar, Editar e Excluir. Clique em Salvar contas para gravar no JSON. Exportar/importar backup permanece disponível; a importação requer salvar para aplicar.
- Para adicionar uma conta, clique em + Adicionar, selecione a moeda e preencha os campos bancários. Os identificadores são gerados automaticamente. A última conta não pode ser excluída.
- Faça backup da pasta inteira. O JSON contém dados pessoais e bancários em texto simples.

O servidor escuta apenas no computador local. Use uma instância por vez. Não há cálculo de impostos ou conversão de câmbio; confira os dados comerciais antes do envio.
