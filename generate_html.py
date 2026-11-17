import json
import os
import re

# Load Backup_Fumigacion.sql
sql_path = r'c:\Users\LENOVO\Documents\PROYECTOS IA\Visual Aplicación\Backup_Fumigacion.sql'
with open(sql_path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

prefix = "INSERT INTO system_backup (id, data) VALUES (1, '"
idx = content.find(prefix)
end_idx = content.rfind("');")
if end_idx == -1: end_idx = content.rfind("'")
json_str = content[idx + len(prefix) : end_idx]
try:
    data = json.loads(json_str)
except Exception:
    json_str_fixed = json_str.replace("\\'", "'").replace("''", "'").replace('\\"', '"')
    data = json.loads(json_str_fixed)

hist = data.get('historicoOperativo', {})
op = data.get('operativoData', [])
cfg = data.get('configLogica', {})

def clean_day(d):
    if not d: return 'Sin día'
    d_clean = str(d).strip()
    if 'Mi' in d_clean: return 'Miércoles'
    if 'bado' in d_clean or ('S' in d_clean and 'do' in d_clean): return 'Sábado'
    if 'Lun' in d_clean: return 'Lunes'
    if 'Mar' in d_clean: return 'Martes'
    if 'Jue' in d_clean: return 'Jueves'
    if 'Vie' in d_clean: return 'Viernes'
    if 'Dom' in d_clean: return 'Domingo'
    return d_clean

def normalize_block(b_name):
    norm = str(b_name).strip()
    if norm == 'BLOQUE 12CO': return 'BLOQUE 12 CO'
    if norm == 'BLOQUE 12FD': return 'BLOQUE 12 FD'
    if norm == 'BLOQUE BLOQUE 25B': return 'BLOQUE 25B'
    return norm

bloques_raw = cfg.get('bloques', '').split(',')
configured_bloques = []
seen = set()
for b in bloques_raw:
    b = normalize_block(b)
    if b and b not in seen:
        seen.add(b)
        configured_bloques.append(b)

schedule_data = {}
all_weeks = set()

# Process historicoOperativo
for b_name, b_val in hist.items():
    norm_b = normalize_block(b_name)
    if isinstance(b_val, dict):
        for k, items in b_val.items():
            if isinstance(items, list):
                for it in items:
                    w = str(it.get('semanaAplicacion') or it.get('semana') or '').strip()
                    if not w: continue
                    all_weeks.add(w)
                    dia = clean_day(it.get('dia'))
                    prod = (it.get('producto') or 'Sin producto').strip()
                    dosis = it.get('dosis')
                    tox = (it.get('tox') or 'N/A').strip()
                    reentrada = str(it.get('reentrada') or 'NA').strip()
                    tipo = (it.get('tipoAgroquimico') or '').strip()
                    blanco = (it.get('blanco') or '').strip()
                    ingrediente = (it.get('ingrediente') or it.get('ingredienteActivo') or '').strip()
                    cancelado = bool(it.get('cancelado') is True or str(it.get('estado', '')).lower() == 'cancelado')
                    observacion = str(it.get('observacion') or '').strip()

                    if w not in schedule_data: schedule_data[w] = {}
                    if norm_b not in schedule_data[w]: schedule_data[w][norm_b] = {}
                    if dia not in schedule_data[w][norm_b]: schedule_data[w][norm_b][dia] = []

                    schedule_data[w][norm_b][dia].append({
                        'producto': prod,
                        'dosis': dosis,
                        'tox': tox,
                        'reentrada': reentrada,
                        'tipo': tipo,
                        'blanco': blanco,
                        'ingrediente': ingrediente,
                        'cancelado': cancelado,
                        'observacion': observacion
                    })

# Process operativoData
if isinstance(op, list):
    for it in op:
        w = str(it.get('semanaAplicacion') or it.get('semana') or '').strip()
        if not w: continue
        all_weeks.add(w)
        b_name = normalize_block(it.get('bloque') or 'Sin Bloque')
        dia = clean_day(it.get('dia'))
        prod = (it.get('producto') or 'Sin producto').strip()
        dosis = it.get('dosis')
        tox = (it.get('tox') or 'N/A').strip()
        reentrada = str(it.get('reentrada') or 'NA').strip()
        tipo = (it.get('tipoAgroquimico') or '').strip()
        blanco = (it.get('blanco') or '').strip()
        ingrediente = (it.get('ingrediente') or it.get('ingredienteActivo') or '').strip()
        cancelado = bool(it.get('cancelado') is True or str(it.get('estado', '')).lower() == 'cancelado')
        observacion = str(it.get('observacion') or '').strip()

        if w not in schedule_data: schedule_data[w] = {}
        if b_name not in schedule_data[w]: schedule_data[w][b_name] = {}
        if dia not in schedule_data[w][b_name]: schedule_data[w][b_name][dia] = []

        schedule_data[w][b_name][dia].append({
            'producto': prod,
            'dosis': dosis,
            'tox': tox,
            'reentrada': reentrada,
            'tipo': tipo,
            'blanco': blanco,
            'ingrediente': ingrediente,
            'cancelado': cancelado,
            'observacion': observacion
        })

def block_sort_key(name):
    parts = re.split(r'(\d+)', name)
    key = []
    for part in parts:
        if part.isdigit():
            key.append(int(part))
        else:
            key.append(part.strip())
    return key

sorted_blocks = sorted(configured_bloques, key=block_sort_key)

# Calculate current ISO calendar week from system calendar (e.g. 2643 for Oct 23, 2026)
import datetime
now = datetime.date.today()
iso_y, iso_w, _ = now.isocalendar()
current_calendar_week = f"{str(iso_y)[2:]}{iso_w:02d}"

embedded_schedule = dict(schedule_data)

available_past_or_current = [w for w in schedule_data.keys() if w <= current_calendar_week]
semana_default = current_calendar_week if current_calendar_week in schedule_data else (max(available_past_or_current) if available_past_or_current else '2643')

embedded_payload = {
    'bloques': sorted_blocks,
    'semanaDefault': semana_default,
    'semanaCalendario': current_calendar_week,
    'scheduleData': embedded_schedule
}

html_code = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
  <meta name="theme-color" content="#FED700">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">

  <!-- Primary Meta Tags (EVERGREEN: Sin número de semana para que el link compartido sirva para siempre) -->
  <title>🌱 Fumigación PF Rosa • Programa de Aplicaciones</title>
  <meta name="title" content="🌱 Fumigación PF Rosa • Programa de Aplicaciones">
  <meta name="description" content="Consulta en tiempo real el programa semanal de fumigación por bloque, días de aplicación, productos, dosis y categoría toxicológica del cultivo PF Rosa.">
  <meta name="author" content="Proyecto PF Rosa">
  <meta name="robots" content="index, follow">

  <!-- Open Graph / WhatsApp / Facebook -->
  <meta property="og:type" content="website">
  <meta property="og:url" content="https://fintencipa-creator.github.io/PROGRAMA-DE-FUMIGACION-/">
  <meta property="og:title" content="🌱 Fumigación PF Rosa • Programa de Aplicaciones">
  <meta property="og:description" content="Consulta en tiempo real el programa de fumigación por bloque, días de aplicación, productos, dosis y categoría toxicológica.">
  <meta property="og:image" content="https://fintencipa-creator.github.io/PROGRAMA-DE-FUMIGACION-/preview.png">
  <meta property="og:image:secure_url" content="https://fintencipa-creator.github.io/PROGRAMA-DE-FUMIGACION-/preview.png">
  <meta property="og:image:type" content="image/png">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:site_name" content="PF Rosa Fumigación">
  <meta property="og:locale" content="es_CO">

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:url" content="https://fintencipa-creator.github.io/PROGRAMA-DE-FUMIGACION-/">
  <meta name="twitter:title" content="🌱 Fumigación PF Rosa • Programa de Aplicaciones">
  <meta name="twitter:description" content="Consulta en tiempo real el programa de fumigación por bloque, días de aplicación, productos, dosis y categoría toxicológica.">
  <meta name="twitter:image" content="https://fintencipa-creator.github.io/PROGRAMA-DE-FUMIGACION-/preview.png">

  <!-- Favicon & Mobile Touch Icons -->
  <link rel="icon" type="image/png" href="icon.png">
  <link rel="apple-touch-icon" href="icon.png">

  <style>
    :root {
      --bg-yellow: #FED700;
      --card-blue: #3247C5;
      --card-blue-hover: #24359D;
      --card-blue-active: #1D2C87;
      --border-dark: #000000;
      --text-dark: #000000;
      --modal-bg: #FFFFFF;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      -webkit-tap-highlight-color: transparent;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }

    body {
      background-color: var(--bg-yellow);
      min-height: 100vh;
      color: var(--text-dark);
      padding: 16px 12px 60px 12px;
      display: flex;
      flex-direction: column;
      align-items: center;
      touch-action: manipulation;
    }

    /* Minimalist Header */
    .header-bar {
      width: 100%;
      max-width: 580px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
      background: #FFFFFF;
      border: 3.5px solid var(--border-dark);
      box-shadow: 4px 4px 0px #000000;
      padding: 12px 14px;
      gap: 10px;
    }

    .header-title {
      font-size: 1.18rem;
      font-weight: 900;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: #000000;
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .badge-semana-actual {
      background-color: #1e7e34;
      color: #FFFFFF;
      font-size: 0.88rem;
      font-weight: 900;
      padding: 6px 12px;
      border: 2.5px solid var(--border-dark);
      box-shadow: 2px 2px 0px #000000;
      display: inline-flex;
      align-items: center;
      gap: 5px;
      letter-spacing: 0.3px;
      text-transform: uppercase;
      white-space: nowrap;
    }

    /* Blocks Container */
    .blocks-container {
      width: 100%;
      max-width: 580px;
      display: flex;
      flex-direction: column;
      gap: 14px;
    }

    /* Block Card - Matching User Drawing with Blue Header and Yellow Days Bar */
    .block-card {
      background-color: #FED700;
      border: 3.5px solid var(--border-dark);
      box-shadow: 4px 4px 0px rgba(0, 0, 0, 1);
      border-radius: 4px;
      cursor: pointer;
      user-select: none;
      transition: transform 0.08s ease, box-shadow 0.08s ease;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    .block-card:hover {
      transform: translateY(-2px);
      box-shadow: 5px 5px 0px rgba(0, 0, 0, 1);
    }

    .block-card:active {
      transform: translateY(2px) scale(0.99);
      box-shadow: 1px 1px 0px rgba(0, 0, 0, 1);
    }

    .block-card-header {
      background-color: var(--card-blue);
      padding: 12px 14px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-bottom: 3.5px solid var(--border-dark);
      transition: background-color 0.1s ease;
    }

    .block-card:hover .block-card-header {
      background-color: var(--card-blue-hover);
    }

    .block-card-header .block-title {
      font-size: 1.65rem;
      font-weight: 900;
      color: #000000;
      letter-spacing: 1px;
      text-transform: uppercase;
      text-align: center;
    }

    /* Days Section directly underneath the block title (Yellow Background) */
    .block-card-days {
      background-color: #FED700;
      padding: 10px 10px;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: center;
      gap: 8px;
      min-height: 44px;
    }

    /* Normal day chip (white box, thick black border, lowercase text) */
    .day-chip {
      background-color: #FFFFFF;
      border: 2.5px solid #000000;
      box-shadow: 2px 2px 0px #000000;
      color: #000000;
      font-size: 0.92rem;
      font-weight: 800;
      padding: 4px 12px;
      border-radius: 3px;
      text-transform: lowercase;
      letter-spacing: 0.3px;
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }

    /* 6 AM Highlighted Day Chip (Bright Red, High Alert, Bold) */
    .day-chip-6am {
      background-color: #DC2626 !important;
      color: #FFFFFF !important;
      border: 2.5px solid #000000 !important;
      box-shadow: 2px 2px 0px #000000 !important;
      font-weight: 900 !important;
      animation: alertPulse 2s infinite ease-in-out;
    }

    .day-chip-6am .chip-tag-6am {
      background-color: #FEF08A;
      color: #991B1B;
      font-size: 0.72rem;
      font-weight: 900;
      padding: 1px 5px;
      border: 1.5px solid #000000;
      border-radius: 2px;
      margin-left: 3px;
      letter-spacing: 0px;
      text-transform: uppercase;
    }

    @keyframes alertPulse {
      0%, 100% {
        transform: scale(1);
      }
      50% {
        transform: scale(1.03);
      }
    }

    .block-sin-dias {
      font-size: 0.82rem;
      font-weight: 700;
      color: #334155;
      font-style: italic;
      padding: 2px 0;
    }

    /* Modal / Pop-up Overlay */
    .modal-overlay {
      display: none;
      position: fixed;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      background: rgba(0, 0, 0, 0.78);
      backdrop-filter: blur(4px);
      z-index: 9999;
      justify-content: center;
      align-items: center;
      padding: 14px;
    }

    .modal-overlay.active {
      display: flex;
    }

    .modal-window {
      background: var(--modal-bg);
      border: 4px solid var(--border-dark);
      box-shadow: 6px 8px 0px rgba(0, 0, 0, 1);
      width: 100%;
      max-width: 540px;
      max-height: 90vh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      border-radius: 4px;
    }

    .modal-header {
      background: var(--card-blue);
      border-bottom: 3.5px solid var(--border-dark);
      padding: 14px 16px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-shrink: 0;
    }

    .modal-header .header-info {
      display: flex;
      flex-direction: column;
      gap: 5px;
    }

    .modal-header .header-bloque {
      font-size: 1.5rem;
      font-weight: 900;
      color: #000000;
      letter-spacing: 0.8px;
      text-transform: uppercase;
      background: #FED700;
      padding: 3px 10px;
      border: 2.5px solid #000;
      display: inline-block;
      width: fit-content;
      box-shadow: 2px 2px 0px #000;
    }

    .modal-header .header-sub-row {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .modal-header .modal-week-btn {
      width: 32px;
      height: 30px;
      border: 2px solid #000;
      background: #FFFFFF;
      color: #000;
      font-size: 0.85rem;
      font-weight: 900;
      cursor: pointer;
      box-shadow: 2px 2px 0 #000;
      border-radius: 4px;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.1s;
    }

    .modal-header .modal-week-btn:active {
      transform: translate(1px, 1px);
      box-shadow: 1px 1px 0 #000;
    }

    .modal-header .modal-week-btn:disabled {
      opacity: 0.35;
      cursor: not-allowed;
      box-shadow: none;
    }

    .modal-header .header-sub {
      font-size: 0.88rem;
      font-weight: 900;
      color: #000000;
      background: #FFFFFF;
      padding: 3px 9px;
      border: 2px solid #000;
      box-shadow: 2px 2px 0 #000;
      border-radius: 4px;
      letter-spacing: 0.3px;
      white-space: nowrap;
    }

    .modal-header .header-sub.pasada {
      background: #E2E8F0;
      color: #334155;
    }

    .btn-close-modal {
      background: #FFFFFF;
      color: #000000;
      border: 3px solid var(--border-dark);
      font-size: 1.6rem;
      font-weight: 900;
      width: 44px;
      height: 44px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.1s;
      flex-shrink: 0;
    }

    .btn-close-modal:active {
      background: #FF3838;
      color: #FFFFFF;
    }

    .modal-body {
      padding: 16px 14px;
      overflow-y: auto;
      -webkit-overflow-scrolling: touch;
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 16px;
      background-color: #F4F6F9;
    }

    /* DAY SECTION */
    .day-section {
      border: 3px solid #000000;
      box-shadow: 4px 4px 0px rgba(0, 0, 0, 0.9);
      padding: 14px 12px;
      border-radius: 4px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    /* Highlighted 6:00 AM Day without Reentry */
    .day-section.dia-sin-reentrada-6am {
      border: 4.5px solid #000000 !important;
      box-shadow: 6px 7px 0px #000000 !important;
      position: relative;
    }

    /* 6:00 AM Alert Banner (Exact user wording) */
    .alerta-6am-banner {
      background: #FFF7ED;
      border: 3px solid #000000;
      box-shadow: 3px 3px 0px #000000;
      padding: 12px 14px;
      display: flex;
      align-items: center;
      gap: 10px;
      border-left: 10px solid #EA580C;
      animation: alertPulse 2s infinite ease-in-out;
    }

    @keyframes alertPulse {
      0%, 100% { transform: scale(1); }
      50% { transform: scale(1.01); }
    }

    .alerta-6am-icon {
      font-size: 1.8rem;
      flex-shrink: 0;
      line-height: 1;
    }

    .alerta-6am-text {
      font-size: 0.96rem;
      font-weight: 900;
      color: #000000;
      line-height: 1.35;
      letter-spacing: 0.2px;
    }

    .day-title {
      font-size: 1.15rem;
      font-weight: 900;
      color: #000000;
      display: flex;
      align-items: center;
      gap: 6px;
      border-bottom: 2.5px solid #000000;
      padding-bottom: 6px;
      text-transform: uppercase;
      letter-spacing: 0.4px;
    }

    .day-badge {
      font-size: 0.78rem;
      font-weight: 900;
      margin-left: auto;
      padding: 3px 8px;
      border: 2px solid #000000;
      box-shadow: 1.5px 1.5px 0px #000000;
      text-transform: uppercase;
      letter-spacing: 0.3px;
    }

    /* Badge 6:00 AM on Day Header */
    .day-badge-6am {
      background: #FF4757 !important;
      color: #FFFFFF !important;
      font-size: 0.8rem;
      font-weight: 900;
      padding: 3px 9px;
      border: 2px solid #000000;
      box-shadow: 2px 2px 0px #000000;
      text-transform: uppercase;
      animation: flashBadge 1.5s infinite alternate;
    }

    @keyframes flashBadge {
      0% { opacity: 0.9; }
      100% { opacity: 1; transform: scale(1.03); }
    }

    /* Day Theme Backgrounds */
    .day-section.day-lunes {
      background-color: #DDF1FF;
      border-top: 8px solid #0284C7;
    }
    .day-section.day-lunes .day-badge {
      background-color: #0284C7;
      color: #FFFFFF;
    }

    .day-section.day-martes {
      background-color: #FFEADB;
      border-top: 8px solid #EA580C;
    }
    .day-section.day-martes .day-badge {
      background-color: #EA580C;
      color: #FFFFFF;
    }

    .day-section.day-miercoles {
      background-color: #DCFCE7;
      border-top: 8px solid #16A34A;
    }
    .day-section.day-miercoles .day-badge {
      background-color: #16A34A;
      color: #FFFFFF;
    }

    .day-section.day-jueves {
      background-color: #F3E8FF;
      border-top: 8px solid #9333EA;
    }
    .day-section.day-jueves .day-badge {
      background-color: #9333EA;
      color: #FFFFFF;
    }

    .day-section.day-viernes {
      background-color: #FFE4E6;
      border-top: 8px solid #E11D48;
    }
    .day-section.day-viernes .day-badge {
      background-color: #E11D48;
      color: #FFFFFF;
    }

    .day-section.day-sabado {
      background-color: #FEF9C3;
      border-top: 8px solid #CA8A04;
    }
    .day-section.day-sabado .day-badge {
      background-color: #FED700;
      color: #000000;
    }

    .day-section.day-domingo {
      background-color: #E2E8F0;
      border-top: 8px solid #475569;
    }
    .day-section.day-domingo .day-badge {
      background-color: #475569;
      color: #FFFFFF;
    }

    .day-section.day-default {
      background-color: #FFFFFF;
      border-top: 8px solid #000000;
    }

    .products-list {
      list-style: none;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    .product-item {
      background: #FFFFFF;
      border: 2px solid #000000;
      box-shadow: 2.5px 2.5px 0px rgba(0, 0, 0, 0.85);
      padding: 11px 12px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 10px;
    }

    .product-item.item-sin-reentrada {
      border: 2.5px solid #000000;
      background: #FFFFFF;
      border-left: 8px solid #FF9F1C;
    }

    /* Cancelled Product Styling */
    .product-item.item-cancelado {
      background: #F1F5F9 !important;
      border: 2px dashed #64748B !important;
      border-left: 8px solid #EF4444 !important;
      opacity: 0.88;
      box-shadow: 2px 2px 0px rgba(0, 0, 0, 0.4) !important;
    }

    .product-item.item-cancelado .product-name {
      text-decoration: line-through;
      color: #64748B !important;
    }

    .badge-cancelado-tag {
      font-size: 0.78rem;
      font-weight: 900;
      padding: 3px 8px;
      border: 2px solid #991B1B;
      white-space: nowrap;
      box-shadow: 1.5px 1.5px 0px #000000;
      text-transform: uppercase;
      letter-spacing: 0.4px;
      background-color: #EF4444;
      color: #FFFFFF;
      display: inline-flex;
      align-items: center;
      gap: 3px;
    }

    .product-detail-motivo {
      color: #B91C1C !important;
      font-weight: 800;
      font-style: italic;
    }

    .product-name {
      font-size: 1.05rem;
      font-weight: 900;
      color: #000000;
      letter-spacing: 0.2px;
      word-break: break-word;
      line-height: 1.25;
    }

    .product-badges {
      display: flex;
      align-items: center;
      gap: 6px;
      flex-wrap: wrap;
      justify-content: flex-end;
      flex-shrink: 0;
    }

    /* Product Technical Details: Ingrediente Activo & Blanco Biológico */
    .product-main-col {
      display: flex;
      flex-direction: column;
      gap: 4px;
      flex: 1;
      min-width: 0;
    }

    .product-details {
      display: flex;
      flex-direction: column;
      gap: 2px;
      margin-top: 2px;
    }

    .product-detail-row {
      font-size: 0.78rem;
      font-weight: 700;
      color: #334155;
      line-height: 1.25;
      word-break: break-word;
    }

    .product-detail-row strong {
      color: #0F172A;
      font-weight: 900;
    }

    .product-detail-ia {
      color: #1E40AF;
    }

    .product-detail-ia strong {
      color: #1E3A8A;
    }

    .product-detail-blanco {
      color: #166534;
    }

    .product-detail-blanco strong {
      color: #14532D;
    }

    .product-dosis {
      font-size: 0.85rem;
      font-weight: 900;
      background: #F1F5F9;
      color: #000000;
      padding: 3px 8px;
      border: 2px solid #000000;
      white-space: nowrap;
      box-shadow: 1.5px 1.5px 0px #000000;
    }

    .badge-reentrada-tag {
      font-size: 0.78rem;
      font-weight: 900;
      padding: 3px 7px;
      border: 2px solid #000000;
      white-space: nowrap;
      box-shadow: 1.5px 1.5px 0px #000000;
      text-transform: uppercase;
      letter-spacing: 0.3px;
    }

    .badge-reentrada-libre {
      background-color: #FED700;
      color: #000000;
    }

    .badge-reentrada-horas {
      background-color: #E2E8F0;
      color: #000000;
    }

    /* TOX CATEGORY BADGES */
    .product-tox {
      font-size: 0.8rem;
      font-weight: 900;
      padding: 3px 7px;
      border: 2px solid #000000;
      white-space: nowrap;
      box-shadow: 1.5px 1.5px 0px #000000;
      letter-spacing: 0.4px;
      text-transform: uppercase;
    }

    .tox-i {
      background-color: #FF3B30;
      color: #FFFFFF;
    }

    .tox-ii {
      background-color: #FFCC00;
      color: #000000;
    }

    .tox-iii {
      background-color: #007AFF;
      color: #FFFFFF;
    }

    .tox-iv {
      background-color: #34C759;
      color: #000000;
    }

    .tox-na {
      background-color: #E5E5EA;
      color: #1C1C1E;
    }

    .tox-other {
      background-color: #E5E5EA;
      color: #000000;
    }

    .no-data-msg {
      text-align: center;
      padding: 24px 16px;
      font-weight: 800;
      color: #000000;
      background: #FFFFFF;
      border: 3.5px dashed var(--border-dark);
      box-shadow: 3px 3px 0px #000;
      font-size: 0.95rem;
    }

    .modal-footer {
      background: #FFFFFF;
      border-top: 3.5px solid var(--border-dark);
      padding: 12px 14px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 10px;
      flex-shrink: 0;
    }

    .nav-btn {
      background: #F1F5F9;
      border: 2.5px solid var(--border-dark);
      font-weight: 900;
      font-size: 0.88rem;
      height: 44px;
      padding: 0 16px;
      cursor: pointer;
      text-transform: uppercase;
      box-shadow: 2px 2px 0px #000;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      flex: 1;
      transition: all 0.08s;
    }

    .nav-btn:active:not(:disabled) {
      background: #FED700;
      transform: translateY(1px);
      box-shadow: 1px 1px 0px #000;
    }

    .nav-btn:disabled {
      opacity: 0.35;
      cursor: not-allowed;
      box-shadow: none;
    }

    /* MOBILE-FIRST OPTIMIZATIONS (< 640px) */
    @media (max-width: 640px) {
      body {
        padding: 10px 8px 30px 8px;
      }

      .header-bar {
        padding: 10px 12px;
        margin-bottom: 12px;
      }

      .header-title {
        font-size: 1.05rem;
      }

      .badge-semana-actual {
        font-size: 0.78rem;
        padding: 5px 8px;
      }

      .blocks-container {
        gap: 10px;
      }

      .block-card {
        min-height: 72px;
        padding: 14px 12px;
        border-width: 3.5px;
        box-shadow: 3.5px 3.5px 0px #000;
      }

      .block-card .block-title {
        font-size: 1.45rem;
      }

      .modal-overlay {
        padding: 0;
        align-items: flex-end;
      }

      .modal-window {
        max-width: 100%;
        height: 92vh;
        max-height: 92vh;
        border-bottom: none;
        border-left: none;
        border-right: none;
        border-top: 4.5px solid #000;
        border-radius: 12px 12px 0 0;
        box-shadow: 0 -8px 24px rgba(0, 0, 0, 0.45);
        animation: slideUpMobile 0.22s cubic-bezier(0.16, 1, 0.3, 1) forwards;
      }

      @keyframes slideUpMobile {
        from { transform: translateY(100%); }
        to { transform: translateY(0); }
      }

      .modal-header {
        padding: 12px 14px;
        border-radius: 8px 8px 0 0;
      }

      .modal-header .header-bloque {
        font-size: 1.35rem;
      }

      .btn-close-modal {
        width: 40px;
        height: 40px;
        font-size: 1.4rem;
      }

      .modal-body {
        padding: 12px 10px;
        gap: 14px;
      }

      .day-section {
        padding: 12px 10px;
      }

      .alerta-6am-banner {
        padding: 10px 12px;
      }

      .alerta-6am-text {
        font-size: 0.88rem;
      }

      .day-title {
        font-size: 1.05rem;
      }

      .product-item {
        padding: 10px;
        flex-direction: column;
        align-items: flex-start;
        gap: 8px;
      }

      .product-name {
        font-size: 1rem;
      }

      .product-badges {
        width: 100%;
        justify-content: flex-start;
        gap: 5px;
      }

      .product-tox, .product-dosis, .badge-reentrada-tag {
        font-size: 0.78rem;
        padding: 2.5px 6px;
      }

      .modal-footer {
        padding: 10px 12px;
        padding-bottom: max(10px, env(safe-area-inset-bottom));
      }

      .nav-btn {
        height: 42px;
        font-size: 0.82rem;
      }
    }
  </style>
</head>
<body>

  <!-- Minimal Header -->
  <header class="header-bar">
    <div class="header-title">🌱 FUMIGACIÓN PF ROSA</div>
    <div class="week-nav">
      <button class="week-btn" id="btnWeekPrev" onclick="cambiarSemana(-1)" title="Semana anterior">&#9664;</button>
      <div class="badge-semana-actual" id="badgeSemanaActual">📅 SEMANA ACTUAL</div>
      <button class="week-btn" id="btnWeekNext" onclick="cambiarSemana(1)" title="Semana siguiente">&#9654;</button>
    </div>
    <style>
      .week-nav { display:flex; align-items:center; gap:8px; }
      .week-btn { width:42px; height:42px; border:3px solid #000; background:#fff; font-size:1rem; font-weight:900; cursor:pointer; box-shadow:3px 3px 0 #000; border-radius:6px; }
      .week-btn:active { transform:translate(2px,2px); box-shadow:1px 1px 0 #000; }
      .week-btn:disabled { opacity:.3; cursor:not-allowed; box-shadow:none; }
      .badge-semana-actual.pasada { background:#64748B !important; color:#fff !important; }
    </style>
  </header>

  <!-- Blocks List -->
  <div class="blocks-container" id="blocksContainer">
  </div>

  <!-- Modal Pop-up (Mobile Slide-up Sheet) -->
  <div class="modal-overlay" id="modalOverlay" onclick="handleOverlayClick(event)">
    <div class="modal-window" onclick="event.stopPropagation()">
      <div class="modal-header">
        <div class="header-info">
          <div class="header-bloque" id="modalBloqueTitle">BLOQUE 1A</div>
          <div class="header-sub-row">
            <button class="modal-week-btn" id="btnModalWeekPrev" onclick="cambiarSemanaModal(-1)" title="Semana anterior">&#9664;</button>
            <div class="header-sub" id="modalSemanaSub">Semana Actual</div>
            <button class="modal-week-btn" id="btnModalWeekNext" onclick="cambiarSemanaModal(1)" title="Semana siguiente">&#9654;</button>
          </div>
        </div>
        <button class="btn-close-modal" onclick="cerrarModal()" title="Cerrar ventana">&times;</button>
      </div>

      <div class="modal-body" id="modalBody">
      </div>

      <div class="modal-footer">
        <button class="nav-btn" id="btnPrevBlock" onclick="navegarBloque(-1)">&larr; Anterior</button>
        <button class="nav-btn" id="btnNextBlock" onclick="navegarBloque(1)">Siguiente &rarr;</button>
      </div>
    </div>
  </div>

  <script>
    const INITIAL_PAYLOAD = __INITIAL_PAYLOAD__;

    let appData = INITIAL_PAYLOAD;
    let currentWeek = calcularSemanaActual();
    let currentBloqueIndex = -1;
    const visibleBloques = [...appData.bloques];

    const DAY_ORDER = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo', 'Sin día'];

    function calcularSemanaActual() {
      const hoy = semanaISOHoy();
      if (appData && appData.scheduleData && appData.scheduleData[hoy]) {
        return hoy;
      }
      const lista = semanasPermitidas();
      if (lista.length > 0) {
        return lista[lista.length - 1];
      }
      return (appData && appData.semanaDefault) || '2643';
    }

    // Semana ISO de hoy en formato AASS (ej. 2643)
    function semanaISOHoy() {
      try {
        const d = new Date();
        d.setHours(0, 0, 0, 0);
        d.setDate(d.getDate() + 4 - (d.getDay() || 7));
        const yearStart = new Date(d.getFullYear(), 0, 1);
        const weekNo = Math.ceil((((d - yearStart) / 86400000) + 1) / 7);
        return String(d.getFullYear()).slice(-2) + String(weekNo).padStart(2, '0');
      } catch (e) {
        return (appData && appData.semanaCalendario) || '2643';
      }
    }

    // Solo semanas actuales o pasadas (nunca futuras)
    function semanasPermitidas() {
      const hoy = semanaISOHoy();
      return Object.keys((appData && appData.scheduleData) || {}).filter(w => w <= hoy).sort();
    }

    function cambiarSemana(delta) {
      const lista = semanasPermitidas();
      let idx = lista.indexOf(currentWeek);
      if (idx === -1) idx = lista.length - 1;
      const nuevo = idx + delta;
      if (nuevo < 0 || nuevo >= lista.length) return;
      currentWeek = lista[nuevo];
      actualizarTitulosSemana();
      renderBloques();
    }

    function cambiarSemanaModal(delta) {
      const lista = semanasPermitidas();
      let idx = lista.indexOf(currentWeek);
      if (idx === -1) idx = lista.length - 1;
      const nuevo = idx + delta;
      if (nuevo < 0 || nuevo >= lista.length) return;
      currentWeek = lista[nuevo];
      actualizarTitulosSemana();
      renderBloques();
      if (currentBloqueIndex >= 0 && currentBloqueIndex < visibleBloques.length) {
        abrirModal(visibleBloques[currentBloqueIndex], currentBloqueIndex);
      }
    }

    function actualizarTitulosSemana() {
      const esActual = currentWeek === semanaISOHoy();
      const badge = document.getElementById('badgeSemanaActual');
      if (badge) {
        badge.textContent = '📅 SEMANA ' + currentWeek;
        badge.classList.toggle('pasada', !esActual);
      }
      const sub = document.getElementById('modalSemanaSub');
      if (sub) {
        sub.textContent = (esActual ? 'Semana Actual: ' : 'Semana: ') + currentWeek;
        sub.classList.toggle('pasada', !esActual);
      }
      const lista = semanasPermitidas();
      const idx = lista.indexOf(currentWeek);

      // Botones barra superior principal
      const prev = document.getElementById('btnWeekPrev');
      const next = document.getElementById('btnWeekNext');
      if (prev) prev.disabled = idx <= 0;
      if (next) next.disabled = idx === -1 || idx >= lista.length - 1;

      // Botones navegación de semana dentro del modal
      const mPrev = document.getElementById('btnModalWeekPrev');
      const mNext = document.getElementById('btnModalWeekNext');
      if (mPrev) mPrev.disabled = idx <= 0;
      if (mNext) mNext.disabled = idx === -1 || idx >= lista.length - 1;
    }

    function getDayColorClass(dia) {
      const d = String(dia || '').toLowerCase();
      if (d.includes('lun')) return 'day-lunes';
      if (d.includes('mar')) return 'day-martes';
      if (d.includes('mi')) return 'day-miercoles';
      if (d.includes('jue')) return 'day-jueves';
      if (d.includes('vie')) return 'day-viernes';
      if (d.includes('s') && (d.includes('bado') || d.includes('ba'))) return 'day-sabado';
      if (d.includes('dom')) return 'day-domingo';
      return 'day-default';
    }

    function getToxBadgeHTML(rawTox) {
      if (!rawTox) return '';
      let t = String(rawTox).trim().toUpperCase();
      if (!t || t === 'NA' || t === 'N/A' || t === 'N.A.') {
        return '<span class="product-tox tox-na">TOX: N/A</span>';
      }
      if (t.includes('IV')) {
        return '<span class="product-tox tox-iv">TOX: IV</span>';
      }
      if (t.includes('III') || t.includes('I I I')) {
        return '<span class="product-tox tox-iii">TOX: III</span>';
      }
      if (t.includes('II') || t.includes('I I')) {
        return '<span class="product-tox tox-ii">TOX: II</span>';
      }
      if (t === 'I') {
        return '<span class="product-tox tox-i">TOX: I</span>';
      }
      return '<span class="product-tox tox-other">TOX: ' + t + '</span>';
    }

    function tieneHorasRestringidas(reentradaStr) {
      if (!reentradaStr) return false;
      const s = String(reentradaStr).toUpperCase().trim();
      if (s === 'NA' || s === 'N/A' || s === 'N.A.' || s === 'AL SECADO' || s === 'NO TIENE' || s === '0' || s === '') {
        return false;
      }
      if (s.includes('HORA') || s.includes('HR') || s.includes('DIA')) {
        return true;
      }
      return false;
    }

    function bloqueTieneAplicacion6AM(bloqueName) {
      const semanaData = (appData.scheduleData && appData.scheduleData[currentWeek]) || {};
      const bloqueData = semanaData[bloqueName] || {};
      for (let dia in bloqueData) {
        const prods = bloqueData[dia] || [];
        if (prods.length > 0) {
          const tieneHoras = prods.some(p => tieneHorasRestringidas(p.reentrada));
          if (!tieneHoras) return true;
        }
      }
      return false;
    }

    async function autoCargarDesdeSQL() {
      const posiblesArchivos = ['Backup_Fumigacion.sql', './Backup_Fumigacion.sql'];
      for (let ruta of posiblesArchivos) {
        try {
          const resp = await fetch(ruta);
          if (resp.ok) {
            const sqlText = await resp.text();
            if (sqlText && sqlText.includes('VALUES (1, ')) {
              procesarSQL(sqlText);
              return true;
            }
          }
        } catch (e) {
          // Local fallback
        }
      }
      return false;
    }

    function initApp() {
      actualizarTitulosSemana();
      renderBloques();

      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') cerrarModal();
        if (document.getElementById('modalOverlay').classList.contains('active')) {
          if (e.key === 'ArrowLeft') navegarBloque(-1);
          if (e.key === 'ArrowRight') navegarBloque(1);
        }
      });

      autoCargarDesdeSQL();
    }

    function cleanDayJS(d) {
      if (!d) return 'Sin día';
      d = String(d).trim();
      if (d.includes('Mi')) return 'Miércoles';
      if (d.includes('bado') || (d.includes('S') && d.includes('do'))) return 'Sábado';
      if (d.includes('Lun')) return 'Lunes';
      if (d.includes('Mar')) return 'Martes';
      if (d.includes('Jue')) return 'Jueves';
      if (d.includes('Vie')) return 'Viernes';
      if (d.includes('Dom')) return 'Domingo';
      return d;
    }

    function normalizeBlockJS(b) {
      if (!b) return 'Sin Bloque';
      let norm = String(b).trim();
      if (norm === 'BLOQUE 12CO') return 'BLOQUE 12 CO';
      if (norm === 'BLOQUE 12FD') return 'BLOQUE 12 FD';
      if (norm === 'BLOQUE BLOQUE 25B') return 'BLOQUE 25B';
      return norm;
    }

    function procesarSQL(content) {
      let jsonStr = '';
      const prefix = "VALUES (1, '";
      const idx = content.indexOf(prefix);
      if (idx !== -1) {
        const start = idx + prefix.length;
        let end = content.lastIndexOf("');");
        if (end === -1) end = content.lastIndexOf("'");
        jsonStr = content.substring(start, end);
      } else {
        const first = content.indexOf('{');
        const last = content.lastIndexOf('}');
        if (first !== -1 && last !== -1) {
          jsonStr = content.substring(first, last + 1);
        }
      }

      if (!jsonStr) return;

      let parsed = null;
      try {
        parsed = JSON.parse(jsonStr);
      } catch (e1) {
        try {
          let fixed = jsonStr.replace(/\\\\'/g, "'").replace(/''/g, "'");
          parsed = JSON.parse(fixed);
        } catch (e2) {
          return;
        }
      }

      const hist = parsed.historicoOperativo || {};
      const op = parsed.operativoData || [];

      const newSchedule = {};
      const weeksFound = new Set();

      for (let bName in hist) {
        const normB = normalizeBlockJS(bName);
        const bVal = hist[bName];
        if (typeof bVal === 'object' && bVal !== null) {
          for (let k in bVal) {
            const items = bVal[k];
            if (Array.isArray(items)) {
              items.forEach(it => {
                const w = String(it.semanaAplicacion || it.semana || '').trim();
                if (!w) return;
                weeksFound.add(w);
                const dia = cleanDayJS(it.dia);
                const prod = String(it.producto || 'Sin producto').trim();
                const dosis = it.dosis;
                const tox = String(it.tox || 'N/A').trim();
                const reentrada = String(it.reentrada || 'NA').trim();
                const tipo = String(it.tipoAgroquimico || '').trim();
                const blanco = String(it.blanco || '').trim();
                const ingrediente = String(it.ingrediente || it.ingredienteActivo || '').trim();
                const cancelado = Boolean(it.cancelado === true || String(it.estado || '').toLowerCase() === 'cancelado');
                const observacion = String(it.observacion || '').trim();

                if (!newSchedule[w]) newSchedule[w] = {};
                if (!newSchedule[w][normB]) newSchedule[w][normB] = {};
                if (!newSchedule[w][normB][dia]) newSchedule[w][normB][dia] = [];

                newSchedule[w][normB][dia].push({
                  producto: prod,
                  dosis: dosis,
                  tox: tox,
                  reentrada: reentrada,
                  tipo: tipo,
                  blanco: blanco,
                  ingrediente: ingrediente,
                  cancelado: cancelado,
                  observacion: observacion
                });
              });
            }
          }
        }
      }

      if (Array.isArray(op)) {
        op.forEach(it => {
          const w = String(it.semanaAplicacion || it.semana || '').trim();
          if (!w) return;
          weeksFound.add(w);
          const bName = normalizeBlockJS(it.bloque || 'Sin Bloque');
          const dia = cleanDayJS(it.dia);
          const prod = String(it.producto || 'Sin producto').trim();
          const dosis = it.dosis;
          const tox = String(it.tox || 'N/A').trim();
          const reentrada = String(it.reentrada || 'NA').trim();
          const tipo = String(it.tipoAgroquimico || '').trim();
          const blanco = String(it.blanco || '').trim();
          const ingrediente = String(it.ingrediente || it.ingredienteActivo || '').trim();
          const cancelado = Boolean(it.cancelado === true || String(it.estado || '').toLowerCase() === 'cancelado');
          const observacion = String(it.observacion || '').trim();

          if (!newSchedule[w]) newSchedule[w] = {};
          if (!newSchedule[w][bName]) newSchedule[w][bName] = {};
          if (!newSchedule[w][bName][dia]) newSchedule[w][bName][dia] = [];

          newSchedule[w][bName][dia].push({
            producto: prod,
            dosis: dosis,
            tox: tox,
            reentrada: reentrada,
            tipo: tipo,
            blanco: blanco,
            ingrediente: ingrediente,
            cancelado: cancelado,
            observacion: observacion
          });
        });
      }

      appData.scheduleData = newSchedule;
      
      // Auto-seleccionar la semana actual si está permitida
      const permitidas = semanasPermitidas();
      const isoNow = semanaISOHoy();
      if (permitidas.includes(isoNow)) {
        currentWeek = isoNow;
      } else if (permitidas.length > 0) {
        currentWeek = permitidas[permitidas.length - 1];
      }

      actualizarTitulosSemana();
      renderBloques();
    }

    function obtenerDiasBloque(bloqueName) {
      const semanaData = (appData.scheduleData && appData.scheduleData[currentWeek]) || {};
      const bloqueData = semanaData[bloqueName] || {};
      const dias = Object.keys(bloqueData);
      dias.sort((a, b) => {
        let idxA = DAY_ORDER.indexOf(a);
        let idxB = DAY_ORDER.indexOf(b);
        if (idxA === -1) idxA = 99;
        if (idxB === -1) idxB = 99;
        return idxA - idxB;
      });
      return dias.map(dia => {
        const prods = bloqueData[dia] || [];
        const prodsActivos = prods.filter(p => !p.cancelado);
        const tieneHoras = prodsActivos.some(p => tieneHorasRestringidas(p.reentrada));
        const es6am = prodsActivos.length > 0 && !tieneHoras;
        const tieneCancelados = prods.some(p => p.cancelado);
        return {
          dia: dia,
          es6am: es6am,
          tieneCancelados: tieneCancelados,
          numProductos: prodsActivos.length,
          totalProductos: prods.length
        };
      });
    }

    function renderBloques() {
      const container = document.getElementById('blocksContainer');
      container.innerHTML = '';

      visibleBloques.forEach((bloqueName, index) => {
        const card = document.createElement('div');
        card.className = 'block-card';
        card.onclick = () => abrirModal(bloqueName, index);

        // Header azul con título del bloque
        const header = document.createElement('div');
        header.className = 'block-card-header';

        const title = document.createElement('div');
        title.className = 'block-title';
        title.textContent = bloqueName;
        header.appendChild(title);
        card.appendChild(header);

        // Barra inferior amarilla con los días de aplicación
        const daysBar = document.createElement('div');
        daysBar.className = 'block-card-days';

        const diasInfo = obtenerDiasBloque(bloqueName);
        if (diasInfo.length === 0) {
          const sinDias = document.createElement('span');
          sinDias.className = 'block-sin-dias';
          sinDias.textContent = 'Sin aplicaciones esta semana';
          daysBar.appendChild(sinDias);
        } else {
          diasInfo.forEach(dInfo => {
            const chip = document.createElement('div');
            const diaNombre = dInfo.dia.toLowerCase();

            if (dInfo.es6am) {
              chip.className = 'day-chip day-chip-6am';
              chip.innerHTML = `<span>⏰</span> ${diaNombre} <span class="chip-tag-6am">6:00 - 8:00 AM</span>`;
            } else if (dInfo.numProductos === 0 && dInfo.tieneCancelados) {
              chip.className = 'day-chip';
              chip.style.background = '#F1F5F9';
              chip.style.color = '#EF4444';
              chip.style.border = '2px dashed #EF4444';
              chip.innerHTML = `<span>❌</span> ${diaNombre} <span style="font-size:0.7rem; font-weight:900;">(CANCELADO)</span>`;
            } else {
              chip.className = 'day-chip';
              chip.textContent = diaNombre;
            }
            daysBar.appendChild(chip);
          });
        }
        card.appendChild(daysBar);

        container.appendChild(card);
      });
    }

    function abrirModal(bloqueName, index) {
      if (typeof index === 'number') {
        currentBloqueIndex = index;
      } else {
        currentBloqueIndex = visibleBloques.indexOf(bloqueName);
      }

      document.getElementById('modalBloqueTitle').textContent = bloqueName;

      document.getElementById('btnPrevBlock').disabled = (currentBloqueIndex <= 0);
      document.getElementById('btnNextBlock').disabled = (currentBloqueIndex >= visibleBloques.length - 1);

      const semanaData = (appData.scheduleData && appData.scheduleData[currentWeek]) || {};
      const bloqueData = semanaData[bloqueName] || {};

      const modalBody = document.getElementById('modalBody');
      modalBody.innerHTML = '';

      const diasEncontrados = Object.keys(bloqueData);

      if (diasEncontrados.length === 0) {
        modalBody.innerHTML = `
          <div class="no-data-msg">
            <p style="font-size: 1.1rem; margin-bottom: 6px;">ℹ️ Sin aplicaciones registradas</p>
            <p>No se encontraron productos programados para <strong>${bloqueName}</strong> en la <strong>Semana ${currentWeek}</strong>.</p>
          </div>
        `;
      } else {
        diasEncontrados.sort((a, b) => {
          let idxA = DAY_ORDER.indexOf(a);
          let idxB = DAY_ORDER.indexOf(b);
          if (idxA === -1) idxA = 99;
          if (idxB === -1) idxB = 99;
          return idxA - idxB;
        });

        diasEncontrados.forEach(dia => {
          const productos = bloqueData[dia] || [];
          const daySec = document.createElement('div');

          const prodsActivos = productos.filter(p => !p.cancelado);
          const tieneHoras = prodsActivos.some(p => tieneHorasRestringidas(p.reentrada));
          const esSinReentrada = prodsActivos.length > 0 && !tieneHoras;
          
          const dayColorClass = getDayColorClass(dia);
          daySec.className = 'day-section ' + dayColorClass + (esSinReentrada ? ' dia-sin-reentrada-6am' : '');

          const dayHeader = document.createElement('div');
          dayHeader.className = 'day-title';
          
          let headerHTML = `<span>📅 ${dia}</span>`;
          if (esSinReentrada) {
            headerHTML += `<span class="day-badge-6am">⏰ 6:00 - 8:00 AM</span>`;
          }
          const numCanc = productos.filter(p => p.cancelado).length;
          if (numCanc > 0) {
            headerHTML += `<span class="badge-cancelado-tag" style="margin-left:auto; font-size:0.72rem; padding:2px 6px;">❌ ${numCanc} CANCELADA${numCanc > 1 ? 'S' : ''}</span>`;
          }
          headerHTML += `<span class="day-badge" style="${numCanc > 0 ? 'margin-left:0;' : ''}">${productos.length} ${productos.length === 1 ? 'PRODUCTO' : 'PRODUCTOS'}</span>`;
          dayHeader.innerHTML = headerHTML;
          daySec.appendChild(dayHeader);

          if (esSinReentrada) {
            const alertBox = document.createElement('div');
            alertBox.className = 'alerta-6am-banner';
            alertBox.innerHTML = `
              <span class="alerta-6am-icon">⏰</span>
              <div class="alerta-6am-text">
                Esta aplicación se hará en la franja de 6:00 a 8:00 de la mañana, espero contar con su apoyo.
              </div>
            `;
            daySec.appendChild(alertBox);
          }

          const list = document.createElement('ul');
          list.className = 'products-list';

          productos.forEach(p => {
            const li = document.createElement('li');
            const esCancelado = Boolean(p.cancelado);
            const itemSinReentrada = !tieneHorasRestringidas(p.reentrada);

            let itemClass = 'product-item';
            if (esCancelado) {
              itemClass += ' item-cancelado';
            } else if (itemSinReentrada) {
              itemClass += ' item-sin-reentrada';
            }
            li.className = itemClass;

            // Columna principal con Nombre, Ingrediente Activo, Blanco Biológico y Observación
            const mainCol = document.createElement('div');
            mainCol.className = 'product-main-col';

            const prodName = document.createElement('div');
            prodName.className = 'product-name';
            prodName.textContent = p.producto;
            mainCol.appendChild(prodName);

            const detailsWrapper = document.createElement('div');
            detailsWrapper.className = 'product-details';

            if (esCancelado) {
              const obs = String(p.observacion || '').trim();
              const cancelRow = document.createElement('div');
              cancelRow.className = 'product-detail-row product-detail-motivo';
              cancelRow.innerHTML = `⚠️ <strong>APLICACIÓN CANCELADA</strong>${obs ? ' • Motivo / Obs: ' + obs : ''}`;
              detailsWrapper.appendChild(cancelRow);
            }

            const ing = String(p.ingrediente || '').trim();
            if (ing) {
              const iaRow = document.createElement('div');
              iaRow.className = 'product-detail-row product-detail-ia';
              iaRow.innerHTML = `<strong>I.A.:</strong> ${ing}`;
              detailsWrapper.appendChild(iaRow);
            }

            const blk = String(p.blanco || '').trim();
            if (blk) {
              const blkRow = document.createElement('div');
              blkRow.className = 'product-detail-row product-detail-blanco';
              blkRow.innerHTML = `<strong>Blanco:</strong> ${blk}`;
              detailsWrapper.appendChild(blkRow);
            }

            if (detailsWrapper.children.length > 0) {
              mainCol.appendChild(detailsWrapper);
            }

            const badgesWrapper = document.createElement('div');
            badgesWrapper.className = 'product-badges';

            if (esCancelado) {
              const cancelBadge = document.createElement('span');
              cancelBadge.className = 'badge-cancelado-tag';
              cancelBadge.innerHTML = '❌ NO APLICADO';
              badgesWrapper.appendChild(cancelBadge);
            } else {
              const rStr = String(p.reentrada || 'NA').trim();
              const reentradaSpan = document.createElement('span');
              if (itemSinReentrada) {
                reentradaSpan.className = 'badge-reentrada-tag badge-reentrada-libre';
                reentradaSpan.textContent = rStr === 'AL SECADO' ? 'AL SECADO' : 'SIN REENTRADA';
              } else {
                reentradaSpan.className = 'badge-reentrada-tag badge-reentrada-horas';
                reentradaSpan.textContent = rStr;
              }
              badgesWrapper.appendChild(reentradaSpan);
            }

            const toxHTML = getToxBadgeHTML(p.tox);
            if (toxHTML) {
              const toxSpan = document.createElement('span');
              toxSpan.innerHTML = toxHTML;
              badgesWrapper.appendChild(toxSpan.firstElementChild);
            }

            if (p.dosis !== null && p.dosis !== undefined && p.dosis !== '') {
              const dosisBadge = document.createElement('span');
              dosisBadge.className = 'product-dosis';
              dosisBadge.textContent = 'Dosis: ' + p.dosis;
              badgesWrapper.appendChild(dosisBadge);
            }

            li.appendChild(mainCol);
            li.appendChild(badgesWrapper);
            list.appendChild(li);
          });

          daySec.appendChild(list);
          modalBody.appendChild(daySec);
        });
      }

      document.getElementById('modalOverlay').classList.add('active');
      document.body.style.overflow = 'hidden';
    }

    function cerrarModal() {
      document.getElementById('modalOverlay').classList.remove('active');
      document.body.style.overflow = 'auto';
    }

    function handleOverlayClick(event) {
      if (event.target.id === 'modalOverlay') {
        cerrarModal();
      }
    }

    function navegarBloque(direction) {
      const newIndex = currentBloqueIndex + direction;
      if (newIndex >= 0 && newIndex < visibleBloques.length) {
        abrirModal(visibleBloques[newIndex], newIndex);
      }
    }

    window.onload = initApp;
  </script>
</body>
</html>
"""

final_html = html_code.replace('__INITIAL_PAYLOAD__', json.dumps(embedded_payload, ensure_ascii=False))

target_path = r'c:\Users\LENOVO\Documents\PROYECTOS IA\Visual Aplicación\index.html'
with open(target_path, 'w', encoding='utf-8') as f:
    f.write(final_html)

print(f"Generated evergreen index.html without static week in title at {target_path} (size: {os.path.getsize(target_path)} bytes)")

