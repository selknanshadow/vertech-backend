<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Vertech TdF — QA Mapas de Emergencia</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@3.19.0/tabler-icons.min.css">
  <link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --void:#02060d; --deep:#050d1a; --panel:#071220; --card:#0a1828;
      --border:#0d2440; --border-hi:#1a3d6b;
      --amber:#ffb300; --amber-dim:rgba(255,179,0,.08); --amber-glow:rgba(255,179,0,.3);
      --green:#00e5a0; --green-dim:rgba(0,229,160,.08);
      --red:#ff3d3d; --red-dim:rgba(255,61,61,.08);
      --blue:#2196f3; --blue-dim:rgba(33,150,243,.08);
      --cyan:#00d4ff;
      --text:#8eb4d4; --text-hi:#c8e0f4; --white:#e8f4ff;
      --mono:'Share Tech Mono',monospace; --sans:'Inter',system-ui,sans-serif;
    }
    body{font-family:var(--sans);background:var(--void);color:var(--text);font-size:12px;line-height:1.45;min-height:100vh;display:flex;flex-direction:column;overflow-x:hidden}
    body::before{content:'';position:fixed;inset:0;background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(255,179,0,.008) 2px,rgba(255,179,0,.008) 4px);pointer-events:none;z-index:0}
 
    /* HEADER */
    header{background:var(--deep);border-bottom:1px solid var(--border);padding:.6rem 1.5rem;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100;flex-shrink:0}
    .hdr-left{display:flex;align-items:center;gap:16px}
    .hdr-brand{display:flex;flex-direction:column;line-height:1.1}
    .brand-name{font-family:var(--mono);font-size:14px;color:var(--white);letter-spacing:.12em}
    .brand-name span{color:var(--amber)}
    .brand-sub{font-size:9px;color:var(--text);letter-spacing:.18em;text-transform:uppercase;margin-top:2px}
    .hdr-nav{display:flex;gap:2px}
    .nav-link{font-family:var(--mono);font-size:10px;letter-spacing:.1em;color:var(--text);text-decoration:none;padding:5px 13px;border-radius:3px;border:1px solid transparent;transition:all .15s;text-transform:uppercase}
    .nav-link:hover{color:var(--white);border-color:var(--border-hi)}
    .nav-link.active{color:var(--amber);border-color:var(--amber);background:var(--amber-dim)}
    .hdr-right{display:flex;align-items:center;gap:12px}
    .hdr-status{display:flex;align-items:center;gap:6px;font-family:var(--mono);font-size:10px;color:var(--amber);letter-spacing:.08em}
    .status-dot{width:7px;height:7px;border-radius:50%;background:var(--amber);box-shadow:0 0 8px var(--amber-glow);animation:blink 2s ease-in-out infinite}
    @keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}
    .hdr-flag{height:30px;border-radius:3px;border:1px solid var(--border-hi)}
 
    .main{flex:1;padding:1rem 1.5rem;display:flex;flex-direction:column;gap:10px;position:relative;z-index:1}
 
    /* AVISO SEGURIDAD */
    .security-bar{display:flex;align-items:center;gap:10px;padding:7px 12px;background:var(--green-dim);border:1px solid rgba(0,229,160,.2);border-radius:3px;font-family:var(--mono);font-size:9px;color:var(--green);letter-spacing:.06em}
    .security-bar .ti{font-size:14px}
    .security-bar strong{color:var(--white)}
 
    /* UPLOAD BAR */
    .upload-bar{background:var(--panel);border:1px solid var(--border);border-radius:4px;padding:.75rem 1rem;display:grid;grid-template-columns:180px 1fr auto auto;gap:10px;align-items:end}
    .field{display:flex;flex-direction:column;gap:4px}
    .field-lbl{font-family:var(--mono);font-size:9px;color:var(--text);letter-spacing:.12em;text-transform:uppercase}
    .field-input,.field-select{background:var(--card);border:1px solid var(--border);border-radius:3px;padding:6px 10px;font-size:11px;font-family:var(--mono);color:var(--white);outline:none;transition:border-color .2s;letter-spacing:.04em;height:29px}
    .field-input:focus,.field-select:focus{border-color:var(--amber)}
    .field-input::placeholder{color:var(--border-hi)}
    .field-select option{background:var(--card);color:var(--white)}
    .upload-btn{background:var(--card);border:1px dashed var(--border-hi);border-radius:3px;padding:6px 14px;font-family:var(--mono);font-size:10px;color:var(--amber);cursor:pointer;position:relative;transition:all .15s;letter-spacing:.08em;white-space:nowrap;display:flex;align-items:center;gap:6px;height:29px}
    .upload-btn:hover,.upload-btn.drag{border-color:var(--amber);background:var(--amber-dim)}
    .upload-btn input{position:absolute;inset:0;opacity:0;cursor:pointer}
    .run-btn{background:var(--amber);border:none;border-radius:3px;padding:6px 18px;font-family:var(--mono);font-size:10px;font-weight:600;color:var(--void);cursor:pointer;display:flex;align-items:center;gap:6px;letter-spacing:.1em;transition:all .15s;white-space:nowrap;height:29px}
    .run-btn:hover:not(:disabled){box-shadow:0 0 16px var(--amber-glow)}
    .run-btn:disabled{background:var(--border);color:var(--text);cursor:not-allowed;box-shadow:none}
 
    .preview-strip{display:none;align-items:center;gap:10px;padding:6px 10px;background:var(--panel);border:1px solid var(--border);border-radius:3px}
    .preview-strip.visible{display:flex}
    .preview-strip img{height:36px;width:54px;object-fit:cover;border-radius:2px;border:1px solid var(--border-hi)}
    .preview-fname{font-family:var(--mono);font-size:10px;color:var(--text-hi);flex:1}
    .btn-swap{font-family:var(--mono);font-size:9px;color:var(--text);background:none;border:1px solid var(--border);border-radius:3px;padding:3px 8px;cursor:pointer;letter-spacing:.06em}
    .btn-swap:hover{border-color:var(--border-hi);color:var(--text-hi)}
 
    .proc-bar{display:none;align-items:center;gap:10px;padding:8px 12px;background:var(--amber-dim);border:1px solid rgba(255,179,0,.2);border-radius:3px;font-family:var(--mono);font-size:10px;color:var(--amber);letter-spacing:.06em}
    .proc-bar.visible{display:flex}
    .proc-spin{width:12px;height:12px;border:2px solid rgba(255,179,0,.2);border-top-color:var(--amber);border-radius:50%;animation:spin .7s linear infinite;flex-shrink:0}
    @keyframes spin{to{transform:rotate(360deg)}}
 
    .section-eyebrow{font-family:var(--mono);font-size:9px;color:var(--text);letter-spacing:.2em;text-transform:uppercase;display:flex;align-items:center;gap:10px;padding:2px 0}
    .section-eyebrow::after{content:'';flex:1;height:1px;background:var(--border)}
 
    /* SCORES */
    .scores-row{display:grid;grid-template-columns:1.4fr repeat(4,1fr) auto;gap:8px}
    .score-card{background:var(--panel);border:1px solid var(--border);border-radius:4px;padding:10px 12px;position:relative;overflow:hidden}
    .score-card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:var(--amber);opacity:.5}
    .score-card.principal::before{height:3px;opacity:1}
    .score-lbl{font-family:var(--mono);font-size:8px;color:var(--text);letter-spacing:.12em;text-transform:uppercase;margin-bottom:4px}
    .score-val{font-family:var(--mono);font-size:26px;font-weight:400;line-height:1;color:var(--white)}
    .score-card.principal .score-val{font-size:34px}
    .score-val.g{color:var(--green)} .score-val.a{color:var(--amber)} .score-val.r{color:var(--red)}
    .score-sub{font-size:9px;color:var(--text);margin-top:3px}
    .score-track{height:3px;background:var(--void);border-radius:2px;overflow:hidden;margin-top:6px}
    .score-fill{height:100%;border-radius:2px;transition:width 1s ease}
 
    /* VEREDICTO */
    .verdict{display:flex;flex-direction:column;justify-content:center;align-items:center;padding:10px 16px;border-radius:4px;border:1px solid;min-width:150px}
    .verdict.si{background:var(--green-dim);border-color:var(--green)}
    .verdict.no{background:var(--red-dim);border-color:var(--red)}
    .verdict.con_correcciones{background:var(--amber-dim);border-color:var(--amber)}
    .verdict-lbl{font-family:var(--mono);font-size:8px;letter-spacing:.14em;text-transform:uppercase;color:var(--text);margin-bottom:3px}
    .verdict-val{font-family:var(--mono);font-size:15px;font-weight:700;letter-spacing:.06em;text-align:center;line-height:1.2}
    .verdict.si .verdict-val{color:var(--green)}
    .verdict.no .verdict-val{color:var(--red)}
    .verdict.con_correcciones .verdict-val{color:var(--amber)}
 
    /* GRID CENTRAL */
    .qa-grid{display:grid;grid-template-columns:1fr 300px 340px;gap:8px;align-items:start}
 
    /* PANEL MAPA */
    .map-panel{background:var(--card);border:1px solid var(--border);border-radius:4px;overflow:hidden;position:relative}
    .map-panel-hdr{padding:6px 10px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;background:rgba(0,0,0,.3)}
    .map-panel-title{font-family:var(--mono);font-size:10px;color:var(--text-hi);letter-spacing:.08em}
    .map-panel-sub{font-size:9px;color:var(--text);font-family:var(--mono)}
    .map-panel img{display:block;width:100%;height:400px;object-fit:contain;background:#050a12}
 
    /* CHECKLIST */
    .check-panel{background:var(--panel);border:1px solid var(--border);border-radius:4px;overflow:hidden;display:flex;flex-direction:column;max-height:465px}
    .panel-hdr{padding:6px 10px;border-bottom:1px solid var(--border);font-family:var(--mono);font-size:9px;color:var(--text);letter-spacing:.12em;text-transform:uppercase;display:flex;align-items:center;gap:6px;background:rgba(0,0,0,.2);flex-shrink:0}
    .panel-hdr .ti{font-size:12px}
    .check-body{padding:6px;display:flex;flex-direction:column;gap:2px;overflow-y:auto}
    .check-row{display:flex;align-items:flex-start;gap:7px;padding:5px 7px;border-radius:3px;background:rgba(0,0,0,.2)}
    .check-icon{font-size:13px;flex-shrink:0;margin-top:1px}
    .check-row.ok .check-icon{color:var(--green)}
    .check-row.falta .check-icon{color:var(--red)}
    .check-row.revisar .check-icon{color:var(--amber)}
    .check-item{font-size:10px;font-weight:600;color:var(--text-hi)}
    .check-obs{font-size:9px;color:var(--text);line-height:1.4;margin-top:1px}
 
    /* CHAT */
    .chat-panel{background:var(--panel);border:1px solid var(--border);border-radius:4px;display:flex;flex-direction:column;height:465px;overflow:hidden}
    .chat-body{flex:1;overflow-y:auto;padding:10px;display:flex;flex-direction:column;gap:8px}
    .chat-msg{max-width:88%;padding:7px 10px;border-radius:4px;font-size:11px;line-height:1.55;white-space:pre-wrap;word-wrap:break-word}
    .chat-msg.bot{background:var(--card);border:1px solid var(--border);border-left:2px solid var(--amber);align-self:flex-start;color:var(--text-hi)}
    .chat-msg.user{background:var(--blue-dim);border:1px solid rgba(33,150,243,.25);align-self:flex-end;color:var(--white)}
    .chat-msg.typing{color:var(--amber);font-family:var(--mono);font-size:10px}
    .chat-empty{color:var(--border-hi);font-family:var(--mono);font-size:10px;text-align:center;padding:2rem 1rem;line-height:1.8}
    .chat-suggestions{display:flex;flex-wrap:wrap;gap:4px;padding:6px 10px;border-top:1px solid var(--border);flex-shrink:0}
    .sugg{font-family:var(--mono);font-size:9px;color:var(--text);background:var(--card);border:1px solid var(--border);border-radius:3px;padding:3px 7px;cursor:pointer;transition:all .15s}
    .sugg:hover{border-color:var(--amber);color:var(--amber)}
    .chat-input-row{display:flex;gap:6px;padding:8px 10px;border-top:1px solid var(--border);flex-shrink:0}
    .chat-input{flex:1;background:var(--card);border:1px solid var(--border);border-radius:3px;padding:7px 10px;font-size:11px;font-family:var(--sans);color:var(--white);outline:none;transition:border-color .2s}
    .chat-input:focus{border-color:var(--amber)}
    .chat-input::placeholder{color:var(--border-hi)}
    .chat-input:disabled{opacity:.4;cursor:not-allowed}
    .chat-send{background:var(--amber);border:none;border-radius:3px;padding:0 12px;color:var(--void);cursor:pointer;font-size:15px;display:flex;align-items:center;transition:all .15s}
    .chat-send:hover:not(:disabled){box-shadow:0 0 12px var(--amber-glow)}
    .chat-send:disabled{background:var(--border);color:var(--text);cursor:not-allowed}
 
    /* HALLAZGOS */
    .findings-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px}
    .find-panel{background:var(--panel);border:1px solid var(--border);border-radius:4px;overflow:hidden}
    .find-body{padding:8px;display:flex;flex-direction:column;gap:6px;max-height:230px;overflow-y:auto}
    .find-item{padding:7px 9px;border-radius:3px;background:rgba(0,0,0,.25);border-left:2px solid var(--border)}
    .find-item.crit{border-left-color:var(--red);background:rgba(255,61,61,.04)}
    .find-item.warn{border-left-color:var(--amber)}
    .find-item.text{border-left-color:var(--blue)}
    .find-title{font-size:10px;font-weight:700;color:var(--white);margin-bottom:2px}
    .find-desc{font-size:9px;color:var(--text);line-height:1.5}
    .find-action{font-size:9px;color:var(--green);line-height:1.5;margin-top:3px;font-style:italic}
    .find-empty{font-family:var(--mono);font-size:9px;color:var(--border-hi);padding:12px 4px;text-align:center}
    .txt-old{color:var(--red);text-decoration:line-through;font-family:var(--mono);font-size:10px}
    .txt-new{color:var(--green);font-family:var(--mono);font-size:10px}
    .txt-motivo{font-size:8px;color:var(--text);font-family:var(--mono);letter-spacing:.06em;text-transform:uppercase;margin-top:2px}
 
    /* RESUMEN */
    .summary-panel{background:var(--panel);border:1px solid var(--border);border-radius:4px;overflow:hidden}
    .summary-hdr{padding:6px 12px;border-bottom:1px solid var(--border);font-family:var(--mono);font-size:9px;color:var(--amber);letter-spacing:.14em;text-transform:uppercase;display:flex;align-items:center;justify-content:space-between;background:var(--amber-dim)}
    .summary-hdr-l{display:flex;align-items:center;gap:8px}
    .btn-report{font-family:var(--mono);font-size:9px;color:var(--amber);background:none;border:1px solid var(--amber);border-radius:3px;padding:3px 10px;cursor:pointer;letter-spacing:.08em;transition:all .15s;display:flex;align-items:center;gap:5px}
    .btn-report:hover{background:var(--amber);color:var(--void)}
    .summary-body{padding:12px 14px;font-size:11px;color:var(--text-hi);line-height:1.8}
 
    footer{background:var(--deep);border-top:1px solid var(--border);padding:.4rem 1.5rem;display:flex;justify-content:space-between;font-family:var(--mono);font-size:9px;color:var(--text);letter-spacing:.06em;flex-shrink:0}
 
    #results{display:none;flex-direction:column;gap:10px}
    #results.visible{display:flex}
 
    @media(max-width:1300px){.qa-grid{grid-template-columns:1fr 1fr}.chat-panel{grid-column:span 2;height:380px}}
    @media(max-width:900px){.scores-row{grid-template-columns:repeat(3,1fr)}.qa-grid{grid-template-columns:1fr}.chat-panel{grid-column:span 1}.findings-grid{grid-template-columns:1fr}.upload-bar{grid-template-columns:1fr}}
  </style>
</head>
<body>
 
<header>
  <div class="hdr-left">
    <img src="logo2.png" alt="Vertech TdF" style="height:38px;width:auto;object-fit:contain;">
    <div class="hdr-brand">
      <span class="brand-name">VERTECH <span>TdF</span></span>
      <span class="brand-sub">Earth Observation Intelligence</span>
    </div>
  </div>
  <nav class="hdr-nav">
    <a href="agro.html" class="nav-link">AgroTech</a>
    <a href="mar.html"  class="nav-link">Economía Azul</a>
    <a href="ch4.html"  class="nav-link">Metano CH₄</a>
    <a href="qa.html"   class="nav-link active">QA Emergencias</a>
  </nav>
  <div class="hdr-right">
    <div class="hdr-status"><span class="status-dot"></span> MODO LOCAL</div>
    <img src="Bandera.png" alt="TdF" class="hdr-flag">
  </div>
</header>
 
<div class="main">
 
  <div class="security-bar">
    <i class="ti ti-shield-lock"></i>
    <span><strong>PROCESAMIENTO INSTITUCIONAL</strong> — Arquitectura desacoplada del motor IA. Desplegable on-premise dentro del entorno CONAE. Los mapas no se almacenan ni se registran en base de datos.</span>
  </div>
 
  <div class="upload-bar">
    <div class="field">
      <label class="field-lbl">Tipo de Evento</label>
      <select id="evento" class="field-select">
        <option value="incendio">Incendio forestal</option>
        <option value="inundacion">Inundación</option>
        <option value="volcanico">Erupción volcánica</option>
        <option value="nevada">Nevada extrema</option>
        <option value="general" selected>Emergencia general</option>
      </select>
    </div>
    <div class="field">
      <label class="field-lbl">Descripción declarada del mapa (opcional)</label>
      <input type="text" id="descripcion" class="field-input" placeholder="Ej: Área quemada Parque Nacional Los Alerces — SAOCOM 1B, 18/06/2026">
    </div>
    <div class="field">
      <label class="field-lbl">Mapa Temático</label>
      <div class="upload-btn" id="drop-zone">
        <input type="file" id="file-input" accept="image/*">
        <i class="ti ti-file-upload"></i> CARGAR MAPA
      </div>
    </div>
    <div class="field">
      <label class="field-lbl">&nbsp;</label>
      <button class="run-btn" id="btn-run" disabled><i class="ti ti-checkup-list"></i> REVISAR</button>
    </div>
  </div>
 
  <div class="preview-strip" id="preview-strip">
    <img id="prev-thumb" src="" alt="">
    <span class="preview-fname" id="prev-name">—</span>
    <button class="btn-swap" id="btn-swap">↺ REEMPLAZAR</button>
  </div>
 
  <div class="proc-bar" id="proc-bar">
    <div class="proc-spin"></div>
    <span id="proc-txt">Iniciando control de calidad cartográfica...</span>
  </div>
 
  <div class="section-eyebrow">CONTROL DE CALIDAD — MAPAS TEMÁTICOS DE EMERGENCIA · UNIDAD DE ALERTAS TEMPRANAS</div>
 
  <!-- RESULTADOS -->
  <div id="results">
 
    <!-- Scores -->
    <div class="scores-row">
      <div class="score-card principal">
        <div class="score-lbl">Score Global</div>
        <div class="score-val" id="sc-global">—</div>
        <div class="score-sub" id="sc-tipo">—</div>
        <div class="score-track"><div class="score-fill" id="fill-global" style="width:0%"></div></div>
      </div>
      <div class="score-card">
        <div class="score-lbl">Cartográfico</div>
        <div class="score-val" id="sc-carto">—</div>
        <div class="score-sub">Escala · Norte · Grilla</div>
        <div class="score-track"><div class="score-fill" id="fill-carto" style="width:0%"></div></div>
      </div>
      <div class="score-card">
        <div class="score-lbl">Institucional</div>
        <div class="score-val" id="sc-inst">—</div>
        <div class="score-sub">Logos · Créditos</div>
        <div class="score-track"><div class="score-fill" id="fill-inst" style="width:0%"></div></div>
      </div>
      <div class="score-card">
        <div class="score-lbl">Redacción</div>
        <div class="score-val" id="sc-red">—</div>
        <div class="score-sub">Ortografía · Gramática</div>
        <div class="score-track"><div class="score-fill" id="fill-red" style="width:0%"></div></div>
      </div>
      <div class="score-card">
        <div class="score-lbl">Coherencia</div>
        <div class="score-val" id="sc-coh">—</div>
        <div class="score-sub">Contenido vs Descripción</div>
        <div class="score-track"><div class="score-fill" id="fill-coh" style="width:0%"></div></div>
      </div>
      <div class="verdict" id="verdict">
        <div class="verdict-lbl">Apto Entrega</div>
        <div class="verdict-val" id="verdict-val">—</div>
      </div>
    </div>
 
    <!-- Grid principal -->
    <div class="qa-grid">
 
      <div class="map-panel">
        <div class="map-panel-hdr">
          <span class="map-panel-title" id="map-title">MAPA BAJO REVISIÓN</span>
          <span class="map-panel-sub" id="map-sub">—</span>
        </div>
        <img id="map-img" src="" alt="Mapa en revisión">
      </div>
 
      <div class="check-panel">
        <div class="panel-hdr"><i class="ti ti-list-check"></i> CHECKLIST CARTOGRÁFICO</div>
        <div class="check-body" id="check-body"></div>
      </div>
 
      <div class="chat-panel">
        <div class="panel-hdr"><i class="ti ti-message-2"></i> ASISTENTE DE REVISIÓN</div>
        <div class="chat-body" id="chat-body"></div>
        <div class="chat-suggestions" id="chat-sugg">
          <div class="sugg" data-q="¿Qué debo corregir con más urgencia antes de entregar?">Prioridad de corrección</div>
          <div class="sugg" data-q="¿La leyenda está completa y es coherente con los símbolos del mapa?">Revisar leyenda</div>
          <div class="sugg" data-q="¿Falta algún elemento cartográfico obligatorio?">Elementos faltantes</div>
          <div class="sugg" data-q="¿El mapa es legible para un tomador de decisión sin formación técnica?">Legibilidad</div>
        </div>
        <div class="chat-input-row">
          <input type="text" id="chat-input" class="chat-input" placeholder="Consultá sobre el mapa..." disabled>
          <button class="chat-send" id="chat-send" disabled><i class="ti ti-send"></i></button>
        </div>
      </div>
 
    </div>
 
    <!-- Hallazgos -->
    <div class="findings-grid">
      <div class="find-panel">
        <div class="panel-hdr" style="color:var(--red)"><i class="ti ti-alert-octagon"></i> ERRORES CRÍTICOS</div>
        <div class="find-body" id="criticos-body"></div>
      </div>
      <div class="find-panel">
        <div class="panel-hdr" style="color:var(--amber)"><i class="ti ti-alert-triangle"></i> ADVERTENCIAS</div>
        <div class="find-body" id="advert-body"></div>
      </div>
      <div class="find-panel">
        <div class="panel-hdr" style="color:var(--blue)"><i class="ti ti-typography"></i> CORRECCIONES DE TEXTO</div>
        <div class="find-body" id="texto-body"></div>
      </div>
    </div>
 
    <!-- Resumen -->
    <div class="summary-panel">
      <div class="summary-hdr">
        <div class="summary-hdr-l"><i class="ti ti-file-description"></i> DICTAMEN DE CONTROL DE CALIDAD</div>
        <button class="btn-report" id="btn-report"><i class="ti ti-printer"></i> GENERAR REPORTE</button>
      </div>
      <div class="summary-body" id="summary-body">—</div>
    </div>
 
  </div>
 
</div>
 
<footer>
  <span>VERTECH TdF · RÍO GRANDE, TIERRA DEL FUEGO, ARGENTINA</span>
  <span>INNOVATÓN SPACE 2025 · CONAE · UNIDAD DE EMERGENCIAS Y ALERTAS TEMPRANAS · v4.0</span>
</footer>
 
<script>
  const BACKEND = 'https://vertech-backend.onrender.com';
  let b64 = null, mtype = 'image/jpeg', imgDataUrl = '';
  let historial = [], qaData = null, fileName = '';
 
  const $ = id => document.getElementById(id);
  const dropZone = $('drop-zone'), fileInput = $('file-input');
  const strip = $('preview-strip'), thumb = $('prev-thumb'), fname = $('prev-name');
  const btnSwap = $('btn-swap'), btnRun = $('btn-run');
  const procBar = $('proc-bar'), procTxt = $('proc-txt');
  const results = $('results'), chatBody = $('chat-body');
  const chatInput = $('chat-input'), chatSend = $('chat-send');
 
  // ── Upload ──
  dropZone.addEventListener('click', e => { if(e.target !== fileInput) fileInput.click(); });
  dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('drag'); });
  dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag'));
  dropZone.addEventListener('drop', e => { e.preventDefault(); dropZone.classList.remove('drag'); if(e.dataTransfer.files[0]) load(e.dataTransfer.files[0]); });
  fileInput.addEventListener('change', e => { if(e.target.files[0]) load(e.target.files[0]); });
  btnSwap.addEventListener('click', () => { fileInput.value = ''; fileInput.click(); });
 
  function load(file) {
    if(!file.type.startsWith('image/')) { alert('Seleccioná una imagen del mapa (PNG, JPEG).'); return; }
    const r = new FileReader();
    r.onload = e => {
      imgDataUrl = e.target.result;
      b64 = imgDataUrl.split(',')[1];
      mtype = file.type || 'image/jpeg';
      fileName = file.name;
      thumb.src = imgDataUrl;
      fname.textContent = file.name;
      strip.classList.add('visible');
      btnRun.disabled = false;
    };
    r.readAsDataURL(file);
  }
 
  const PASOS = [
    'Verificando elementos cartográficos obligatorios...',
    'Analizando completitud y coherencia de la leyenda...',
    'Detectando identidad institucional y créditos de fuente...',
    'Revisando ortografía, gramática y terminología...',
    'Evaluando coherencia entre contenido y descripción...',
    'Generando dictamen de control de calidad...'
  ];
 
  // ── Revisar ──
  btnRun.addEventListener('click', async () => {
    if(!b64) return;
    btnRun.disabled = true;
    results.classList.remove('visible');
    procBar.classList.add('visible');
    historial = [];
 
    let p = 0;
    const iv = setInterval(() => { if(p < PASOS.length) procTxt.textContent = PASOS[p++]; }, 900);
 
    try {
      const res = await fetch(`${BACKEND}/qa-mapa`, {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({
          imagen_base64: b64,
          media_type: mtype,
          tipo_evento: $('evento').value,
          descripcion: $('descripcion').value.trim(),
          organismo: 'CONAE'
        })
      });
 
      clearInterval(iv);
      procBar.classList.remove('visible');
      if(!res.ok) throw new Error((await res.json().catch(()=>({}))).detail || `HTTP ${res.status}`);
 
      qaData = await res.json();
      render(qaData);
 
    } catch(e) {
      clearInterval(iv);
      procBar.classList.remove('visible');
      console.error(e);
      alert(`Error en el control de calidad:\n${e.message}`);
    }
    btnRun.disabled = false;
  });
 
  // ── Render ──
  function color(n){ return n >= 80 ? 'g' : n >= 60 ? 'a' : 'r'; }
  function hex(n){ return n >= 80 ? '#00e5a0' : n >= 60 ? '#ffb300' : '#ff3d3d'; }
 
  function render(d) {
    const s = d.score || {};
    const sets = [
      ['sc-global','fill-global', s.global],
      ['sc-carto','fill-carto', s.cartografico],
      ['sc-inst','fill-inst', s.institucional],
      ['sc-red','fill-red', s.redaccion],
      ['sc-coh','fill-coh', s.coherencia]
    ];
    sets.forEach(([idv, idf, val]) => {
      const v = typeof val === 'number' ? val : 0;
      const el = $(idv);
      el.textContent = v;
      el.className = 'score-val ' + color(v);
      $(idf).style.width = v + '%';
      $(idf).style.background = hex(v);
    });
 
    $('sc-tipo').textContent = d.tipo_producto || 'Producto cartográfico';
 
    // Veredicto
    const apto = (d.apto_entrega || 'CON_CORRECCIONES').toUpperCase();
    const vd = $('verdict');
    vd.className = 'verdict ' + apto.toLowerCase();
    $('verdict-val').textContent = apto === 'SI' ? 'APTO' : apto === 'NO' ? 'NO APTO' : 'CON\nCORRECCIONES';
 
    // Mapa
    $('map-img').src = imgDataUrl;
    $('map-title').textContent = (d.titulo_detectado || 'Mapa sin título detectado').toUpperCase();
    $('map-sub').textContent = fileName + ' · ' + new Date().toLocaleDateString('es-AR');
 
    // Checklist
    const icons = { ok:'ti-circle-check', falta:'ti-circle-x', revisar:'ti-alert-circle' };
    $('check-body').innerHTML = (d.checklist||[]).map(c => `
      <div class="check-row ${c.estado||'revisar'}">
        <i class="ti ${icons[c.estado]||'ti-alert-circle'} check-icon"></i>
        <div>
          <div class="check-item">${c.item}</div>
          <div class="check-obs">${c.obs||''}</div>
        </div>
      </div>`).join('') || '<div class="find-empty">Sin datos</div>';
 
    // Críticos
    $('criticos-body').innerHTML = (d.criticos||[]).length
      ? d.criticos.map(c => `
        <div class="find-item crit">
          <div class="find-title">${c.titulo}</div>
          <div class="find-desc">${c.desc}</div>
          ${c.accion ? `<div class="find-action">→ ${c.accion}</div>` : ''}
        </div>`).join('')
      : '<div class="find-empty">✓ SIN ERRORES CRÍTICOS</div>';
 
    // Advertencias
    $('advert-body').innerHTML = (d.advertencias||[]).length
      ? d.advertencias.map(a => `
        <div class="find-item warn">
          <div class="find-title">${a.titulo}</div>
          <div class="find-desc">${a.desc}</div>
          ${a.accion ? `<div class="find-action">→ ${a.accion}</div>` : ''}
        </div>`).join('')
      : '<div class="find-empty">✓ SIN ADVERTENCIAS</div>';
 
    // Texto
    $('texto-body').innerHTML = (d.correcciones_texto||[]).length
      ? d.correcciones_texto.map(t => `
        <div class="find-item text">
          <div class="txt-old">${t.encontrado}</div>
          <div class="txt-new">→ ${t.sugerido}</div>
          <div class="txt-motivo">${t.motivo||''}</div>
        </div>`).join('')
      : '<div class="find-empty">✓ SIN ERRORES DE REDACCIÓN</div>';
 
    // Resumen
    $('summary-body').textContent = d.resumen || '—';
 
    // Chat
    chatBody.innerHTML = '';
    addMsg('bot', `Control de calidad completado. Score global: ${s.global ?? '—'}/100.\n\n${d.resumen || ''}\n\nPodés consultarme sobre cualquier aspecto del mapa.`);
    chatInput.disabled = false;
    chatSend.disabled = false;
 
    results.classList.add('visible');
    results.scrollIntoView({ behavior:'smooth', block:'start' });
  }
 
  // ── Chat ──
  function addMsg(role, text) {
    const div = document.createElement('div');
    div.className = 'chat-msg ' + (role === 'user' ? 'user' : 'bot');
    div.textContent = text;
    chatBody.appendChild(div);
    chatBody.scrollTop = chatBody.scrollHeight;
    return div;
  }
 
  async function enviar(pregunta) {
    if(!pregunta.trim() || !b64) return;
    addMsg('user', pregunta);
    chatInput.value = '';
    chatInput.disabled = true;
    chatSend.disabled = true;
 
    const typing = addMsg('bot', 'Analizando...');
    typing.classList.add('typing');
 
    try {
      const res = await fetch(`${BACKEND}/qa-chat`, {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({
          imagen_base64: b64,
          media_type: mtype,
          historial: historial,
          pregunta: pregunta,
          tipo_evento: $('evento').value
        })
      });
 
      if(!res.ok) throw new Error((await res.json().catch(()=>({}))).detail || `HTTP ${res.status}`);
      const data = await res.json();
 
      typing.remove();
      addMsg('bot', data.respuesta);
 
      historial.push({ role:'user', content: pregunta });
      historial.push({ role:'assistant', content: data.respuesta });
      if(historial.length > 12) historial = historial.slice(-12);
 
    } catch(e) {
      typing.remove();
      addMsg('bot', `Error de conexión: ${e.message}`);
      console.error(e);
    }
 
    chatInput.disabled = false;
    chatSend.disabled = false;
    chatInput.focus();
  }
 
  chatSend.addEventListener('click', () => enviar(chatInput.value));
  chatInput.addEventListener('keydown', e => { if(e.key === 'Enter') enviar(chatInput.value); });
  document.querySelectorAll('.sugg').forEach(s => {
    s.addEventListener('click', () => { if(!chatInput.disabled) enviar(s.dataset.q); });
  });
 
  // ── Reporte imprimible ──
  $('btn-report').addEventListener('click', () => {
    if(!qaData) return;
    const d = qaData, s = d.score || {};
    const fecha = new Date().toLocaleString('es-AR');
    const icon = e => e === 'ok' ? '✓' : e === 'falta' ? '✗' : '!';
 
    const w = window.open('', '_blank');
    w.document.write(`
<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Reporte QA — ${fileName}</title>
<style>
  @page{size:A4;margin:15mm}
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:system-ui,sans-serif;font-size:10pt;color:#1a1a1a;line-height:1.5}
  .hdr{border-bottom:2px solid #0d2440;padding-bottom:10px;margin-bottom:16px;display:flex;justify-content:space-between;align-items:flex-end}
  .hdr h1{font-size:15pt;color:#0d2440}
  .hdr .sub{font-size:8.5pt;color:#666;margin-top:3px}
  .hdr .meta{font-size:8pt;color:#666;text-align:right}
  h2{font-size:10pt;color:#0d2440;margin:16px 0 7px;padding-bottom:3px;border-bottom:1px solid #ddd;text-transform:uppercase;letter-spacing:.5px}
  .scores{display:flex;gap:8px;margin-bottom:6px}
  .sc{flex:1;border:1px solid #ddd;border-radius:3px;padding:8px;text-align:center}
  .sc .l{font-size:7pt;color:#666;text-transform:uppercase;letter-spacing:.5px}
  .sc .v{font-size:19pt;font-weight:700;margin-top:2px}
  .g{color:#0a8f5f}.a{color:#b37700}.r{color:#c92a2a}
  .verdict{padding:9px 12px;border-radius:3px;font-weight:700;font-size:11pt;text-align:center;margin:10px 0}
  .v-si{background:#e6f9f1;color:#0a8f5f;border:1px solid #0a8f5f}
  .v-no{background:#fdeaea;color:#c92a2a;border:1px solid #c92a2a}
  .v-cc{background:#fff6e0;color:#b37700;border:1px solid #b37700}
  table{width:100%;border-collapse:collapse;font-size:9pt;margin-bottom:6px}
  th{background:#f2f5f8;text-align:left;padding:5px 7px;font-size:8pt;text-transform:uppercase;letter-spacing:.4px;border:1px solid #ddd;color:#0d2440}
  td{padding:5px 7px;border:1px solid #ddd;vertical-align:top}
  .st{font-weight:700;text-align:center;width:28px}
  .item{border-left:3px solid #ddd;padding:7px 10px;margin-bottom:6px;background:#fafbfc}
  .item.c{border-left-color:#c92a2a}
  .item.w{border-left-color:#b37700}
  .item.t{border-left-color:#1971c2}
  .item .t{font-weight:700;font-size:9.5pt;margin-bottom:2px}
  .item .d{font-size:9pt;color:#444}
  .item .a{font-size:8.5pt;color:#0a8f5f;font-style:italic;margin-top:3px}
  .resumen{background:#f8f9fa;border:1px solid #ddd;border-radius:3px;padding:11px;font-size:9.5pt;line-height:1.7}
  .img-box{text-align:center;margin:10px 0}
  .img-box img{max-width:100%;max-height:150mm;border:1px solid #ccc}
  .ft{margin-top:20px;padding-top:8px;border-top:1px solid #ddd;font-size:7.5pt;color:#888;display:flex;justify-content:space-between}
  .none{color:#0a8f5f;font-size:9pt;padding:5px 0}
  @media print{.noprint{display:none}}
</style></head><body>
 
<div class="hdr">
  <div>
    <h1>Reporte de Control de Calidad Cartográfica</h1>
    <div class="sub">Vertech TdF · Asistente IA para Mapas de Emergencia · CONAE</div>
  </div>
  <div class="meta">
    <div><strong>Archivo:</strong> ${fileName}</div>
    <div><strong>Evento:</strong> ${$('evento').selectedOptions[0].text}</div>
    <div><strong>Fecha:</strong> ${fecha}</div>
  </div>
</div>
 
<h2>Evaluación General</h2>
<div class="scores">
  <div class="sc"><div class="l">Global</div><div class="v ${color(s.global||0)}">${s.global ?? '—'}</div></div>
  <div class="sc"><div class="l">Cartográfico</div><div class="v ${color(s.cartografico||0)}">${s.cartografico ?? '—'}</div></div>
  <div class="sc"><div class="l">Institucional</div><div class="v ${color(s.institucional||0)}">${s.institucional ?? '—'}</div></div>
  <div class="sc"><div class="l">Redacción</div><div class="v ${color(s.redaccion||0)}">${s.redaccion ?? '—'}</div></div>
  <div class="sc"><div class="l">Coherencia</div><div class="v ${color(s.coherencia||0)}">${s.coherencia ?? '—'}</div></div>
</div>
 
<div class="verdict ${d.apto_entrega==='SI'?'v-si':d.apto_entrega==='NO'?'v-no':'v-cc'}">
  APTO PARA ENTREGA: ${d.apto_entrega === 'SI' ? 'SÍ' : d.apto_entrega === 'NO' ? 'NO' : 'CON CORRECCIONES'}
</div>
 
<h2>Dictamen</h2>
<div class="resumen">${d.resumen || '—'}</div>
 
<h2>Checklist Cartográfico</h2>
<table>
  <thead><tr><th class="st">—</th><th style="width:32%">Elemento</th><th>Observación</th></tr></thead>
  <tbody>
    ${(d.checklist||[]).map(c => `<tr>
      <td class="st ${c.estado==='ok'?'g':c.estado==='falta'?'r':'a'}">${icon(c.estado)}</td>
      <td><strong>${c.item}</strong></td>
      <td>${c.obs||'—'}</td>
    </tr>`).join('')}
  </tbody>
</table>
 
<h2>Errores Críticos</h2>
${(d.criticos||[]).length ? d.criticos.map(c => `
  <div class="item c">
    <div class="t">${c.titulo}</div>
    <div class="d">${c.desc}</div>
    ${c.accion?`<div class="a">Corrección: ${c.accion}</div>`:''}
  </div>`).join('') : '<div class="none">✓ No se detectaron errores críticos.</div>'}
 
<h2>Advertencias</h2>
${(d.advertencias||[]).length ? d.advertencias.map(a => `
  <div class="item w">
    <div class="t">${a.titulo}</div>
    <div class="d">${a.desc}</div>
    ${a.accion?`<div class="a">Sugerencia: ${a.accion}</div>`:''}
  </div>`).join('') : '<div class="none">✓ No se detectaron advertencias.</div>'}
 
<h2>Correcciones de Redacción</h2>
${(d.correcciones_texto||[]).length ? `
<table>
  <thead><tr><th style="width:38%">Encontrado</th><th style="width:38%">Sugerido</th><th>Motivo</th></tr></thead>
  <tbody>${d.correcciones_texto.map(t => `<tr>
    <td style="color:#c92a2a">${t.encontrado}</td>
    <td style="color:#0a8f5f"><strong>${t.sugerido}</strong></td>
    <td style="font-size:8pt">${t.motivo||'—'}</td>
  </tr>`).join('')}</tbody>
</table>` : '<div class="none">✓ No se detectaron errores de redacción.</div>'}
 
<h2>Mapa Revisado</h2>
<div class="img-box"><img src="${imgDataUrl}"></div>
 
<div class="ft">
  <span>Vertech TdF · Río Grande, Tierra del Fuego, Argentina</span>
  <span>Documento generado por asistente IA — No reemplaza el criterio técnico del operador</span>
</div>
 
<script>window.onload=()=>setTimeout(()=>window.print(),400)<\/script>
</body></html>`);
    w.document.close();
  });
</script>
</body>
</html>
 
