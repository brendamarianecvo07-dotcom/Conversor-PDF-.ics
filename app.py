import streamlit as st
import pdfplumber
from icalendar import Calendar, Event
from datetime import datetime, timedelta
import re
import io

st.set_page_config(page_title="Conversor PDF para Calendário", page_icon="📅")
st.title("📅 Conversor de Calendário Escolar/Anual")

MESES_PT = {
    'JANEIRO': 1, 'FEVEREIRO': 2, 'MARÇO': 3, 'ABRIL': 4,
    'MAIO': 5, 'JUNHO': 6, 'JULHO': 7, 'AGOSTO': 8,
    'SETEMBRO': 9, 'OUTUBRO': 10, 'NOVEMBRO': 11, 'DEZEMBRO': 12
}

def processar_pdf(pdf_file):
    cal = Calendar()
    cal.add('prodid', '-//Conversor PDF//meuapp//')
    cal.add('version', '2.0')
    
    eventos = []
    ano_atual = datetime.now().year # Valor padrão
    mes_atual = None
    
    with pdfplumber.open(pdf_file) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if not texto: continue
            
            linhas = texto.split('\n')
            for linha in linhas:
                linha = linha.strip()
                if not linha: continue
                
                # 1. Detectar Mudança de Ano (Ex: "Ano de 2026")
                match_ano = re.search(r'Ano de (\d{4})', linha, re.IGNORECASE)
                if match_ano:
                    ano_atual = int(match_ano.group(1))
                    continue

                # 2. Detectar Mudança de Mês (Ex: "Janeiro")
                if linha.upper() in MESES_PT:
                    mes_atual = MESES_PT[linha.upper()]
                    continue
                
                # 3. Detectar Evento (Ex: "16 Volta as aulas")
                match_evento = re.match(r'^(\d{1,2})\s+(.*)', linha)
                
                if match_evento and mes_atual:
                    dia = int(match_evento.group(1))
                    descricao = match_evento.group(2)
                    
                    try:
                        data_inicio = datetime(ano_atual, mes_atual, dia)
                        eventos.append({
                            'inicio': data_inicio,
                            'desc': descricao
                        })
                    except ValueError:
                        continue # Pula datas inválidas como 31 de fevereiro
                
                # 4. Se a linha for apenas texto e já tivermos um evento, é continuação
                elif eventos and mes_atual and not re.match(r'^\d', linha):
                    # Evita que o nome do próximo mês entre na descrição
                    if linha.upper() not in MESES_PT and "Ano de" not in linha:
                        eventos[-1]['desc'] += " " + linha

    for ev in eventos:
        evento = Event()
        evento.add('summary', ev['desc'])
        evento.add('dtstart', ev['inicio'].date())
        evento.add('dtend', ev['inicio'].date() + timedelta(days=1))
        cal.add_component(evento)
        
    return cal.to_ical(), len(eventos)

# Interface
arquivo = st.file_uploader("Suba o arquivo teste2.pdf aqui", type="pdf")

if arquivo:
    if st.button("Gerar Calendário"):
        conteudo_ics, total = processar_pdf(arquivo)
        if total > 0:
            st.success(f"Foram encontrados {total} eventos em {arquivo.name}")
            st.download_button(
                label="📥 Baixar arquivo .ics",
                data=conteudo_ics,
                file_name="calendario_escola.ics",
                mime="text/calendar"
            )
        else:
            st.warning("Nenhum evento encontrado. O formato do PDF pode ter mudado.")