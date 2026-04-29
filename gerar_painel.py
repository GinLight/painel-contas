import requests
from datetime import datetime
from collections import defaultdict
import os

NOTION_TOKEN  = os.environ.get("SECRET_NOTION_TOKEN", "")
DATABASE_ID   = "34d7b512-9145-80f1-8f06-ec62dc0b45a8"
ARQUIVO_SAIDA = "index.html"
MES_REF       = "Abril 2026"

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

EMOJIS = {"Raphael":"👨‍💻","Kiara":"👩‍🎨","Kawany":"👩‍💼","Thiago":"👨‍🔧","Zenilda":"👩‍🍳"}
CORES  = {"Raphael":"#3b82f6","Kiara":"#a855f7","Kawany":"#ec4899","Thiago":"#f59e0b","Zenilda":"#22c55e"}

def buscar_entradas():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    payload = {"filter": {"property": "Status", "status": {"does_not_equal": "Pago"}}, "page_size": 100}
    resp = requests.post(url, headers=HEADERS, json=payload)
    resp.raise_for_status()
    return resp.json()["results"]

def processar_dados(entradas):
    pessoas = defaultdict(lambda: {"despesaCasa": 0.0, "cartao": 0.0, "itens": []})
    for entrada in entradas:
        props = entrada["properties"]
        titulo = props.get("Descricao", props.get("Descrição", {})).get("title", [])
        descricao = titulo[0]["plain_text"] if titulo else "Sem descrição"
        tipo_select = props.get("Tipo", {}).get("select")
        tipo = tipo_select["name"] if tipo_select else None
        if not tipo:
            continue
        participantes = [opt["name"] for opt in props.get("Participantes", {}).get("multi_select", [])]
        if not participantes:
            continue
        valor_formula = props.get("Valor por Pessoa", {}).get("formula", {})
        if valor_formula.get("type") == "number":
            valor = valor_formula.get("number") or 0.0
        else:
            valor_total = props.get("Valor Total", {}).get("number") or 0.0
            valor = round(valor_total / len(participantes), 2)
        for pessoa in participantes:
            tipo_key = "casa" if tipo == "Despesa da Casa" else "cartao"
            pessoas[pessoa]["itens"].append({"nome": descricao, "tipo": tipo_key, "valor": valor})
            if tipo == "Despesa da Casa":
                pessoas[pessoa]["despesaCasa"] += valor
            else:
                pessoas[pessoa]["cartao"] += valor
    return pessoas

def fmt(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def gerar_html(pessoas_dict):
    total_geral = sum(p["despesaCasa"] + p["cartao"] for p in pessoas_dict.values())
    total_itens = sum(len(p["itens"]) for p in pessoas_dict.values())
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")

    def card_html(nome, dados):
        cor = CORES.get(nome, "#7c6af7")
        emoji = EMOJIS.get(nome, "👤")
        total = dados["despesaCasa"] + dados["cartao"]
        pct = round((total / total_geral) * 100, 1) if total_geral > 0 else 0
        itens_html = ""
        for it in dados["itens"]:
            tag_class = "tag-casa" if it["tipo"] == "casa" else "tag-cartao"
            tag_label = "🏠 Casa" if it["tipo"] == "casa" else "💳 Cartão"
            itens_html += f"""
            <div class="item-row">
              <span class="item-name">{it['nome']}</span>
              <span class="item-tag {tag_class}">{tag_label}</span>
              <span class="item-val">{fmt(it['valor'])}</span>
            </div>"""
        return f"""
    <div class="card" style="--accent:{cor}">
      <div class="card-header">
        <div class="avatar" style="background:color-mix(in oklch,{cor} 15%,var(--color-surface-2))"><span style="font-size:1.5rem">{emoji}</span></div>
        <div class="card-info"><h2 class="person-name">{nome}</h2><span class="status-badge">A Pagar</span></div>
        <div class="total-amount">{fmt(total)}</div>
      </div>
      <div class="progress-wrap">
        <div class="progress-bar"><div class="progress-fill" style="width:{pct}%;background:{cor}"></div></div>
        <span class="progress-pct">{pct}% do total</span>
      </div>
      <div class="breakdown">
        <div class="breakdown-item"><span class="breakdown-icon">🏠</span><div><div class="breakdown-label">Despesa da Casa</div><div class="breakdown-value">{fmt(dados['despesaCasa'])}</div></div></div>
        <div class="breakdown-item"><span class="breakdown-icon">💳</span><div><div class="breakdown-label">Compra no Cartão</div><div class="breakdown-value">{fmt(dados['cartao'])}</div></div></div>
      </div>
      <details class="details-section"><summary>Ver detalhes</summary><div class="items-list">{itens_html}</div></details>
    </div>"""

    cards = "".join(card_html(n, d) for n, d in pessoas_dict.items())
    return f"""<!DOCTYPE html>
<html lang="pt-BR" data-theme="dark">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Contas a Pagar</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300..700&display=swap" rel="stylesheet">
<style>
:root,[data-theme="light"]{{--color-bg:#f7f6f2;--color-surface:#f9f8f5;--color-surface-2:#fbfbf9;--color-surface-offset:#f3f0ec;--color-divider:#dcd9d5;--color-border:#d4d1ca;--color-text:#28251d;--color-text-muted:#7a7974;--color-text-faint:#bab9b4;--color-primary:#01696f;--shadow-sm:0 1px 2px oklch(0.2 0.01 80/.06);--shadow-md:0 4px 12px oklch(0.2 0.01 80/.08);--radius-md:.5rem;--radius-xl:1rem;--space-2:.5rem;--space-3:.75rem;--space-4:1rem;--space-6:1.5rem;--space-8:2rem;--text-xs:clamp(.75rem,.7rem + .25vw,.875rem);--text-sm:clamp(.875rem,.8rem + .35vw,1rem);--text-base:clamp(1rem,.95rem + .25vw,1.125rem);--text-lg:clamp(1.125rem,1rem + .75vw,1.5rem);--text-xl:clamp(1.5rem,1.2rem + 1.25vw,2.25rem);--transition:180ms cubic-bezier(.16,1,.3,1)}}
[data-theme="dark"]{{--color-bg:#111110;--color-surface:#18171a;--color-surface-2:#1e1d21;--color-surface-offset:#242328;--color-divider:#2a2930;--color-border:#32313a;--color-text:#e8e6f0;--color-text-muted:#8884a0;--color-text-faint:#4a4860;--color-primary:#7c6af7;--shadow-sm:0 1px 2px oklch(0 0 0/.3);--shadow-md:0 4px 16px oklch(0 0 0/.4)}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
html{{-webkit-font-smoothing:antialiased}}
body{{min-height:100dvh;font-family:Inter,sans-serif;font-size:var(--text-base);color:var(--color-text);background:var(--color-bg);padding:var(--space-6) var(--space-4)}}
.header{{max-width:860px;margin:0 auto var(--space-8);display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:var(--space-4)}}
.logo-area{{display:flex;align-items:center;gap:var(--space-3)}}.logo-svg{{color:var(--color-primary)}}
.header-title{{font-size:var(--text-lg);font-weight:700;letter-spacing:-.02em}}
.header-sub{{font-size:var(--text-xs);color:var(--color-text-muted);margin-top:2px}}
.theme-btn{{background:var(--color-surface-offset);border:1px solid var(--color-border);border-radius:var(--radius-md);padding:var(--space-2) var(--space-3);color:var(--color-text-muted);cursor:pointer;font-size:var(--text-sm);display:flex;align-items:center;gap:var(--space-2);transition:background var(--transition),color var(--transition)}}
.theme-btn:hover{{background:var(--color-divider);color:var(--color-text)}}
.summary{{max-width:860px;margin:0 auto var(--space-8);background:var(--color-surface);border:1px solid var(--color-border);border-radius:var(--radius-xl);padding:var(--space-6);display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:var(--space-4);box-shadow:var(--shadow-sm)}}
.summary-label{{font-size:var(--text-xs);color:var(--color-text-muted);text-transform:uppercase;letter-spacing:.08em;font-weight:600;margin-bottom:4px}}
.summary-value{{font-size:var(--text-xl);font-weight:700;letter-spacing:-.03em;color:var(--color-text)}}
.summary-divider{{width:1px;height:40px;background:var(--color-divider)}}.summary-stat{{text-align:center}}
.grid{{max-width:860px;margin:0 auto;display:grid;gap:var(--space-4)}}
@media(min-width:640px){{.grid{{grid-template-columns:1fr 1fr}}}}
.card{{background:var(--color-surface);border:1px solid var(--color-border);border-radius:var(--radius-xl);padding:var(--space-6);box-shadow:var(--shadow-sm);transition:box-shadow var(--transition),transform var(--transition);border-top:3px solid var(--accent,var(--color-primary))}}
.card:hover{{box-shadow:var(--shadow-md);transform:translateY(-2px)}}
.card-header{{display:flex;align-items:center;gap:var(--space-3);margin-bottom:var(--space-4)}}
.avatar{{width:44px;height:44px;border-radius:var(--radius-md);display:flex;align-items:center;justify-content:center;flex-shrink:0}}
.card-info{{flex:1}}.person-name{{font-size:var(--text-base);font-weight:700;letter-spacing:-.01em}}
.status-badge{{font-size:var(--text-xs);color:#f59e0b;background:color-mix(in oklch,#f59e0b 12%,transparent);border:1px solid color-mix(in oklch,#f59e0b 30%,transparent);border-radius:9999px;padding:2px 8px;font-weight:600;display:inline-block;margin-top:3px}}
.total-amount{{font-size:var(--text-lg);font-weight:800;letter-spacing:-.03em;color:var(--accent);text-align:right}}
.progress-wrap{{display:flex;align-items:center;gap:var(--space-3);margin-bottom:var(--space-4)}}
.progress-bar{{flex:1;height:6px;background:var(--color-surface-offset);border-radius:9999px;overflow:hidden}}
.progress-fill{{height:100%;border-radius:9999px;transition:width .8s cubic-bezier(.16,1,.3,1)}}.progress-pct{{font-size:var(--text-xs);color:var(--color-text-muted);white-space:nowrap}}
.breakdown{{display:flex;gap:var(--space-3);margin-bottom:var(--space-4)}}
.breakdown-item{{flex:1;background:var(--color-surface-2);border:1px solid var(--color-divider);border-radius:var(--radius-md);padding:var(--space-3);display:flex;align-items:center;gap:var(--space-2)}}
.breakdown-icon{{font-size:1rem}}.breakdown-label{{font-size:var(--text-xs);color:var(--color-text-muted)}}.breakdown-value{{font-size:var(--text-sm);font-weight:700;color:var(--color-text)}}
details.details-section summary{{font-size:var(--text-xs);color:var(--color-primary);cursor:pointer;user-select:none;list-style:none;display:flex;align-items:center;gap:var(--space-2);font-weight:600;padding:var(--space-2) 0;border-top:1px solid var(--color-divider)}}
details.details-section summary::-webkit-details-marker{{display:none}}
details.details-section summary::before{{content:'▶';font-size:.6rem;transition:transform .2s}}
details[open] summary::before{{transform:rotate(90deg)}}
.items-list{{margin-top:var(--space-3);display:flex;flex-direction:column;gap:var(--space-2)}}
.item-row{{display:flex;align-items:center;gap:var(--space-2);font-size:var(--text-xs)}}
.item-name{{flex:1;color:var(--color-text-muted)}}
.item-tag{{padding:2px 6px;border-radius:9999px;font-weight:600;font-size:.65rem;white-space:nowrap}}
.tag-casa{{background:color-mix(in oklch,#22c55e 12%,transparent);color:#22c55e;border:1px solid color-mix(in oklch,#22c55e 30%,transparent)}}
.tag-cartao{{background:color-mix(in oklch,#3b82f6 12%,transparent);color:#3b82f6;border:1px solid color-mix(in oklch,#3b82f6 30%,transparent)}}
.item-val{{font-weight:700;color:var(--color-text);white-space:nowrap}}
.footer{{max-width:860px;margin:var(--space-8) auto 0;text-align:center;font-size:var(--text-xs);color:var(--color-text-faint)}}
</style>
</head>
<body>
<header class="header">
  <div class="logo-area">
    <svg class="logo-svg" width="32" height="32" viewBox="0 0 32 32" fill="none">
      <rect x="4" y="4" width="24" height="24" rx="6" stroke="currentColor" stroke-width="2"/>
      <path d="M10 16h12M10 11h8M10 21h6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      <circle cx="24" cy="24" r="6" fill="var(--color-bg)" stroke="currentColor" stroke-width="1.5"/>
      <path d="M21.5 24l1.5 1.5 3-3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    <div>
      <div class="header-title">Contas a Pagar</div>
      <div class="header-sub">Resumo por pessoa · {MES_REF}</div>
    </div>
  </div>
  <button class="theme-btn" onclick="toggleTheme()">
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
    Tema
  </button>
</header>
<div class="summary">
  <div class="summary-stat"><div class="summary-label">Total em Aberto</div><div class="summary-value">{fmt(total_geral)}</div></div>
  <div class="summary-divider"></div>
  <div class="summary-stat"><div class="summary-label">Pessoas</div><div class="summary-value">{len(pessoas_dict)}</div></div>
  <div class="summary-divider"></div>
  <div class="summary-stat"><div class="summary-label">Lançamentos</div><div class="summary-value">{total_itens}</div></div>
  <div class="summary-divider"></div>
  <div class="summary-stat"><div class="summary-label">Status</div><div class="summary-value" style="font-size:var(--text-base);color:#f59e0b">⚠️ A Pagar</div></div>
</div>
<div class="grid">{cards}</div>
<div class="footer">Atualizado automaticamente · {agora}</div>
<script>function toggleTheme(){{const h=document.documentElement;h.setAttribute('data-theme',h.getAttribute('data-theme')==='dark'?'light':'dark')}}</script>
</body></html>"""

def main():
    print("Buscando dados do Notion...")
    entradas = buscar_entradas()
    print(f"{len(entradas)} lancamentos encontrados")
    pessoas = processar_dados(entradas)
    html = gerar_html(pessoas)
    with open(ARQUIVO_SAIDA, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Painel salvo em {ARQUIVO_SAIDA}")

if __name__ == "__main__":
    main()
