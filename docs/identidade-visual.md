# Identidade Visual — Bora Contratar

## Visão Geral

| Item | Detalhe |
|------|---------|
| Marca | Bora Contratar |
| Stack CSS | Tailwind CSS 3.x (CDN) |
| Fonte | Inter (Google Fonts) |
| Icones | FontAwesome 6.4.0 |
| Graficos | Chart.js 4.4.7 |
| Tema escuro | `prefers-color-scheme: media` |
| Responsivo | Breakpoints sm / md / lg / xl |

---

## Paleta de Cores

### Cores Primarias da Marca

Customizadas via `tailwind.config.colors.brand` no `base.html`:

| Token | Hex | Tailwind | Uso |
|-------|-----|----------|-----|
| brand-50 | `#fff7ed` | orange-50 | Fundo badge / hover claro |
| brand-100 | `#ffedd5` | orange-100 | Fundo hover claro |
| brand-500 | `#f97316` | orange-500 | Icones, grafico linha, hover |
| brand-600 | `#ea580c` | orange-600 | Botoes primarios, links, logo |
| brand-900 | `#7c2d12` | orange-900 | Texto em fundo claro da marca |

### Cores Neutras (Fundo e Texto)

| Contexto | Light | Dark |
|----------|-------|------|
| Fundo pagina | `#f8fafc` (slate-50) | `#0f172a` (slate-900) |
| Cartao / painel | `bg-white` | `bg-slate-800` |
| Texto principal | `text-slate-900` | `text-white` |
| Texto secundario | `text-slate-500/600` | `text-slate-300/400` |
| Texto muted | `text-slate-400` | `text-slate-500` |

### Cores de Status (Vagas)

| Status | Hex | Light (bg/text) | Dark (bg/text) |
|--------|-----|-----------------|----------------|
| solicitada | `#f59e0b` | amber-100 / amber-700 | amber-900/40 / amber-300 |
| em_triagem | `#3b82f6` | blue-100 / blue-700 | blue-900/40 / blue-300 |
| aguardando_aprovacao | `#8b5cf6` | purple-100 / purple-700 | purple-900/40 / purple-300 |
| aprovada | `#10b981` | emerald-100 / emerald-700 | emerald-900/40 / emerald-300 |
| aprovada_ressalvas | `#f59e0b` | amber-100 / amber-700 | amber-900/40 / amber-300 |
| em_recrutamento | `#06b6d4` | cyan-100 / cyan-700 | cyan-900/40 / cyan-300 |
| publicada | `#10b981` | emerald-100 / emerald-700 | emerald-900/40 / emerald-300 |
| rascunho | `#94a3b8` | slate-100 / slate-600 | slate-700 / slate-400 |
| encerrada | `#ef4444` | red-100 / red-700 | red-900/40 / red-300 |

### Cores de Status (Candidatos)

| Status | Hex sugerido |
|--------|-------------|
| Pendente / Em Andamento | `#f59e0b` (amber) |
| Aprovado | `#10b981` (emerald) |
| Reprovado | `#ef4444` (red) |
| Contratado | `#8b5cf6` (purple) |

### Cores de Papeis (Badges)

| Papel | Hex | Light | Dark |
|-------|-----|-------|------|
| superadmin | `#10b981` | green-100 / green-700 | green-900/40 / green-300 |
| admin | `#8b5cf6` | purple-100 / purple-700 | purple-900/40 / purple-300 |
| rh | `#3b82f6` | blue-100 / blue-700 | blue-900/40 / blue-300 |
| gestor | `#f59e0b` | amber-100 / amber-700 | amber-900/40 / amber-300 |
| aprovador | `#4f46e5` | indigo-100 / indigo-700 | indigo-900/40 / indigo-300 |

### Cores de Feedback (Flash Messages)

| Tipo | Light | Dark |
|------|-------|------|
| success | bg-green-50 / text-green-800 / border-green-200 | bg-green-900/30 / text-green-300 / border-green-800 |
| error | bg-red-50 / text-red-800 / border-red-200 | bg-red-900/30 / text-red-300 / border-red-800 |
| warning | bg-yellow-50 / text-yellow-800 / border-yellow-200 | bg-yellow-900/30 / text-yellow-300 / border-yellow-800 |
| info | bg-blue-50 / text-blue-800 / border-blue-200 | bg-blue-900/30 / text-blue-300 / border-blue-800 |

### Cores de Graficos (Chart.js)

| Grafico | Cores |
|---------|-------|
| Donut vagas/status | Mesmas cores dos status de vagas |
| Barras candidatos/status | `#3b82f6`, `#10b981`, `#f59e0b`, `#ef4444`, `#8b5cf6`, `#06b6d4`, `#ec4899` |
| Barras distribuicao scores | `#ef4444`, `#f59e0b`, `#3b82f6`, `#10b981`, `#059669` |
| Linha vagas/mes | Linha `#f97316`, fill `rgba(249,115,22,0.1)`, pontos `#f97316` |
| Grid (light) | `rgba(148,163,184,0.2)` |
| Grid (dark) | `rgba(148,163,184,0.1)` |
| Texto eixos (light) | `#64748b` (slate-500) |
| Texto eixos (dark) | `#94a3b8` (slate-400) |
| Borda donut (light) | `#ffffff` |
| Borda donut (dark) | `#1e293b` (slate-800) |

---

## Tipografia

### Fonte Primaria

**Inter** — Google Fonts  
`https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap`

Configuracao Tailwind:

```js
fontFamily: { sans: ['Inter', 'sans-serif'] }
```

### Pesos e Usos

| Peso | Classe | Uso |
|------|--------|-----|
| 300 | `font-light` | Parte "Contratar" no logo da sidebar |
| 400 | `font-normal` | Corpo de texto, paragrafos |
| 500 | `font-medium` | Subtitulos, botoes, labels |
| 600 | `font-semibold` | Titulos de secao, cabeçalhos de tabela |
| 700 | `font-bold` | Titulos de pagina, headings principais, KPIs |

### Tamanhos

| Elemento | Classe | Tamanho |
|----------|--------|---------|
| Heading pagina | `text-2xl` | 24px |
| Titulo card | `text-sm font-bold` | 14px |
| Corpo | `text-sm` | 14px |
| Texto secundario | `text-xs` | 12px |
| Badge / tag | `text-[10px]` | 10px |

---

## Logo & Marca

### Logo Iconografico

`/static/Logo-maleta.png` — icone de maleta (briefcase).

Usos:
- Favicon (`<link rel="icon">`)
- Pagina de login (`class="h-16"`)
- Sidebar admin (renderizado como icone FontAwesome `fa-briefcase` em quadrado `bg-brand-600 rounded-lg p-2`)

### Logo Textual

**Navbar publica:**

```html
<i class="fa-solid fa-briefcase text-brand-600"></i>
Bora<span class="text-slate-800 dark:text-white">Contratar</span>
```

**Sidebar admin:**

```html
<span class="text-base font-bold tracking-tight">Bora</span>
<span class="text-base font-light text-slate-300">Contratar</span>
```

### Tagline

> "Plataforma de Recrutamento Inteligente"

Usada na pagina de login como subtitulo.

---

## Iconografia

Todos os icones sao **FontAwesome 6.4.0** (Free Solid + Regular), carregados via CDN:

```
https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css
```

### Inventario de Icones por Contexto

| Contexto | Icones |
|----------|--------|
| Navegacao | `fa-briefcase`, `fa-gauge-high`, `fa-users-gear`, `fa-file-lines`, `fa-chart-pie` |
| Acoes | `fa-plus`, `fa-pen-to-square`, `fa-trash-can`, `fa-ban`, `fa-play`, `fa-globe`, `fa-paper-plane`, `fa-archive` |
| Aprovacao | `fa-check`, `fa-check-double`, `fa-flag`, `fa-clipboard-check`, `fa-arrow-right` |
| Feedback | `fa-circle-check`, `fa-circle-exclamation`, `fa-triangle-exclamation`, `fa-circle-info` |
| Busca | `fa-magnifying-glass`, `fa-search` |
| Candidatos | `fa-users`, `fa-user-plus`, `fa-users-slash`, `fa-robot`, `fa-hourglass-half`, `fa-chevron-right`, `fa-file-pdf` |
| Contato | `fa-envelope`, `fa-phone`, `fa-id-card` |
| Dashboard | `fa-microchip`, `fa-chart-line`, `fa-chart-bar`, `fa-clock-rotate-left`, `fa-clock` |
| Utilitarios | `fa-bars` (hamburguer), `fa-xmark` (fechar), `fa-arrow-left` (voltar), `fa-right-from-bracket` (logout), `fa-bell`, `fa-inbox`, `fa-file-csv`, `fa-lock`, `fa-location-dot`, `fa-file-contract`, `fa-hashtag` |

---

## Componentes e Estilos

### Border Radius

| Nivel | Classe | Raio |
|-------|--------|------|
| Cartoes principais | `rounded-2xl` | 16px |
| Cartoes secundarios | `rounded-xl` | 12px |
| Botoes, inputs, KPI container | `rounded-lg` | 8px |
| Badges, avatares, mini-tags | `rounded-full` | 9999px |

### Sombras

| Nivel | Classe |
|-------|--------|
| Padrao | `shadow-sm` |
| Hover | `shadow-md` |
| Sidebar | Nenhuma (fundo solido) |
| Efeito glass | `backdrop-filter: blur(10px)` + `border: 1px solid rgba(255,255,255,0.2)` |

### Espacamento

| Contexto | Padding/Margin |
|----------|---------------|
| Cartoes | `p-5` (20px) ou `p-6` (24px) |
| Conteudo main | `py-8`, `px-4 sm:px-6 lg:px-8` |
| Grid entre secoes | `gap-4` ou `gap-6` |
| Celulas de tabela | `px-5 py-3.5` |
| Sidebar nav | `px-2 lg:px-3` |
| Sidebar header | `px-4 lg:px-5` |
| Espacamento vertical | `space-y-4`, `space-y-5`, `space-y-6` |

### Tema Escuro

Ativado por `prefers-color-scheme: dark` (Tailwind `darkMode: 'media'`).

Nenhum toggle manual — respeita a preferencia do sistema operacional.

Todas as transicoes de cor usam `transition-colors duration-200` para suavizar a troca entre temas.

### Responsividade

| Breakpoint | Largura | Comportamento sidebar |
|------------|---------|-----------------------|
| Padrao (<640px) | Mobile | Sidebar oculta, hamburguer `fa-bars` abre drawer |
| sm (640px) | Tablet | Drawer com overlay |
| lg (1024px) | Desktop | Sidebar fixa visivel (w-64), layout normal |

### Efeito Glass (Pagina de Login)

```css
.glass-panel {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
}
```

---

## Design Tokens (Resumo Rapido)

```yaml
colors:
  brand:
    50:  '#fff7ed'
    100: '#ffedd5'
    500: '#f97316'   # primaria
    600: '#ea580c'   # hover / botoes
    900: '#7c2d12'
  surface:
    light: '#f8fafc'  # slate-50
    dark:  '#0f172a'   # slate-900
    card-light: '#ffffff'
    card-dark:  '#1e293b'  # slate-800
  text:
    primary-light:  '#0f172a'  # slate-900
    primary-dark:   '#ffffff'
    secondary-light: '#64748b' # slate-500
    secondary-dark:  '#94a3b8' # slate-400

font:
  family: 'Inter, sans-serif'
  weights: [300, 400, 500, 600, 700]

radius:
  card:   '16px'    # rounded-2xl
  panel:  '12px'    # rounded-xl
  button: '8px'     # rounded-lg
  badge:  '9999px'  # rounded-full

shadow:
  default: '0 1px 2px 0 rgb(0 0 0 / 0.05)'  # shadow-sm
  hover:   '0 4px 6px -1px rgb(0 0 0 / 0.1)' # shadow-md

icon:
  library: 'FontAwesome 6.4.0 Free'
  style: 'solid (fa-solid) / regular (fa-regular)'

chart:
  library: 'Chart.js 4.4.7'
  default_border_light: '#ffffff'
  default_border_dark:  '#1e293b'
  grid_light: 'rgba(148,163,184,0.2)'
  grid_dark:  'rgba(148,163,184,0.1)'
  text_light: '#64748b'
  text_dark:  '#94a3b8'
```
