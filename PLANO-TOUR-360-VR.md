# Tour 360° — Navegador + Óculos VR (Zeiss VR One Plus)

> Documento de descoberta, decisão e construção.
> Objetivo: **uma página única, simples e leve**, que mostra imagens 360° de vários ambientes, navegáveis pelo mouse/toque (tipo Kuula) **e** dentro de um óculos de VR de celular.

---

## 1. Descoberta: o que é o óculos do cliente

A foto mostra um **ZEISS VR One Plus**. O que importa saber sobre ele:

| Característica | Consequência para o projeto |
|---|---|
| É um **"cardboard premium"**: só lentes + bandeja onde se encaixa o celular | Quem roda tudo é o **celular**. A página precisa funcionar no navegador do celular. |
| **Não tem nenhum botão**, gatilho nem controle | O usuário **não consegue tocar na tela** com o celular dentro do óculos. A navegação tem que ser **pelo olhar** (gaze). |
| Celulares de ~4,7" a ~5,5"/6" (bandeja universal) | Celulares muito grandes (6,7"+) podem não caber — testar com o aparelho real do cliente. |
| Tampa frontal removível (para câmera) | Irrelevante para nós. |
| Lentes ~100° de campo de visão | A tela é dividida ao meio: **uma imagem para cada olho** (estéreo). |

### Como o cliente "navega" com ele

Como não há botão, o padrão da indústria para esse tipo de óculos é:

1. **Olhar para os lados = girar o ambiente.** O giroscópio do celular acompanha a cabeça (use uma cadeira giratória).
2. **Mira no centro da visão** (um pontinho/anel fixo).
3. **Olhar fixo num ponto de navegação (hotspot) por ~1,5 s** → um anel se preenche → ao completar, muda para o próximo ambiente. Isso se chama **"gaze + dwell"** (olhar e esperar).
4. Opcional: um **controle Bluetooth** (clicker de R$ 30–60 ou gamepad) pode servir de "clique". Funciona como teclado/Enter no navegador — vamos suportar, mas **não depender** dele.

> **Recomendação ao cliente:** navegação pelo olhar, com hotspots no chão apontando para as portas/passagens + um **menu de ambientes "olhando para baixo"** (olhar para o chão mostra miniaturas de todos os ambientes, também selecionáveis pelo olhar). Assim ninguém fica preso num cômodo.

---

## 2. A solução proposta

**Um único `index.html` + uma pasta de imagens + um `tour.json`.** Sem backend, sem build obrigatório.

Três modos de uso, mesmo arquivo:

| Modo | Dispositivo | Olhar em volta | Navegar entre ambientes |
|---|---|---|---|
| **Desktop** | Navegador no PC | Arrastar com o mouse, roda do mouse = zoom | Clicar no hotspot / barra de miniaturas |
| **Celular (mão)** | Navegador mobile | Arrastar com o dedo **ou** mover o celular (giroscópio, opcional) | Tocar no hotspot / miniaturas |
| **VR (óculos)** | Celular dentro do VR One Plus | Movimento da cabeça (giroscópio) | **Olhar fixo 1,5 s** no hotspot ou no menu do chão |

### Decisão técnica: Three.js puro, estéreo próprio

Avaliadas as opções:

| Opção | Prós | Contras | Veredito |
|---|---|---|---|
| **Kuula / Matterport** | Pronto | Pago, marca d'água, pouco controle; modo VR do Kuula exige toque | ❌ |
| **Pannellum / Marzipano** | Ótimos para desktop/mobile | **Não têm modo VR estéreo** | ❌ para VR |
| **A-Frame** | VR fácil via WebXR | No **iPhone (Safari) WebXR não existe** → sem modo VR. Pesado para algo simples | ⚠️ |
| **WebXR nativo** | Oficial | Só Android/Chrome. iPhone fica de fora | ⚠️ como extra |
| **Three.js + estéreo próprio (StereoCamera) + giroscópio** | Funciona em **Android e iPhone**, total controle visual, leve | Precisamos escrever ~400 linhas de JS | ✅ **Escolhido** |

**Por que:** o cliente não disse qual celular usa. Fazendo o estéreo "na mão" (tela dividida em dois + `DeviceOrientationEvent`), o mesmo código funciona em **iPhone e Android**, sem depender de WebXR. É exatamente o que o Google Cardboard fazia no navegador.

---

## 3. Requisitos obrigatórios (pegadinhas)

1. **HTTPS obrigatório.** Giroscópio e tela cheia só funcionam em contexto seguro. Hospedar em Netlify / Vercel / GitHub Pages / Cloudflare Pages (todos grátis com HTTPS). Para testar no celular localmente: `npx serve` + túnel (`npx localtunnel` ou `cloudflared`), ou servidor local com certificado.
2. **iPhone (iOS 13+) pede permissão do giroscópio.** `DeviceOrientationEvent.requestPermission()` **só pode ser chamado dentro de um toque do usuário** → o botão "Entrar no modo VR" faz essa chamada.
3. **Tela cheia no iPhone:** o Safari do iPhone **não permite** fullscreen de elementos. Solução: manifest PWA com `"display": "fullscreen"` + meta `apple-mobile-web-app-capable` → instruir o cliente a **"Adicionar à Tela de Início"** e abrir pelo ícone. No Android, `requestFullscreen()` + `screen.orientation.lock('landscape')` funcionam direto.
4. **Tela não pode apagar** durante o uso: `navigator.wakeLock.request('screen')` (com fallback silencioso).
5. **Tamanho de textura no celular:** muitos celulares limitam a **4096 px**. Gerar duas versões de cada imagem:
   - `*_8k.jpg` 8192×4096 (desktop, se `gl.MAX_TEXTURE_SIZE >= 8192`)
   - `*_4k.jpg` 4096×2048 (celular / VR) — qualidade JPG ~80, alvo < 1,5 MB
6. **Formato das imagens:** equirretangular **2:1** (saída padrão de Insta360, Ricoh Theta, render 360 do V-Ray/Corona/Enscape/D5, etc.).
7. **Pré-carregar** as imagens vizinhas (hotspots do ambiente atual) para a troca ser instantânea.
8. **Conforto em VR:** nada de movimento de câmera automático, nada de zoom no modo VR, transição por **fade para preto** (~300 ms) — nunca "voar" entre ambientes (causa enjoo).

---

## 4. Arquitetura

```
/
├── index.html          ← tudo: HTML + CSS + JS (módulo)
├── tour.json           ← ambientes e hotspots (o cliente/editor mexe só aqui)
├── manifest.webmanifest
├── icon-512.png
└── panos/
    ├── sala_4k.jpg   sala_8k.jpg   sala_thumb.jpg
    ├── cozinha_4k.jpg ...
```

Three.js via CDN fixo (sem build):

```html
<script type="importmap">
{ "imports": { "three": "https://cdn.jsdelivr.net/npm/three@0.169.0/build/three.module.js" } }
</script>
```

### 4.1 `tour.json`

```json
{
  "title": "Residencial Exemplo",
  "start": "sala",
  "scenes": {
    "sala": {
      "name": "Sala de Estar",
      "image": "panos/sala",
      "initialYaw": 0,
      "northOffset": 0,
      "hotspots": [
        { "to": "cozinha", "yaw": 72.5, "pitch": -18, "label": "Cozinha" },
        { "to": "suite",   "yaw": -140, "pitch": -15, "label": "Suíte" }
      ]
    },
    "cozinha": { "name": "Cozinha", "image": "panos/cozinha", "initialYaw": 180, "hotspots": [ { "to": "sala", "yaw": 250, "pitch": -20, "label": "Sala" } ] }
  }
}
```

- `yaw` = graus horizontais (0 = centro da imagem, positivo para a direita), `pitch` = graus verticais (negativo = para baixo/chão).
- `image` sem sufixo; o código escolhe `_4k` ou `_8k`.

### 4.2 Módulos internos do `index.html`

| Módulo | Responsabilidade |
|---|---|
| `Viewer` | Cena Three.js, esfera invertida (`SphereGeometry(500, 64, 32)` + `scale(-1,1,1)`), `MeshBasicMaterial`, `colorSpace = SRGBColorSpace` |
| `SceneManager` | Carrega `tour.json`, troca de ambiente com fade, pré-carrega vizinhos, cache de texturas (dispose das antigas, máx. 3 em memória no celular) |
| `PointerControls` | Arrastar (mouse/toque) → yaw/pitch com inércia; roda/pinça → FOV 30°–90°; pitch limitado a ±85° |
| `GyroControls` | `deviceorientation` → quaternion (alpha/beta/gamma + `screen.orientation.angle`), suavização leve. (O `DeviceOrientationControls` foi removido do Three; reimplementar as ~40 linhas.) |
| `StereoRenderer` | `THREE.StereoCamera` (eyeSep ~0,064), `renderer.setScissorTest`, desenha metade esquerda/direita; FOV vertical ~90° |
| `Hotspots` | Sprites/planos 3D posicionados na esfera (raio 450) a partir de yaw/pitch; sempre virados para a câmera |
| `GazeCursor` | Retícula no centro (em cada olho); `Raycaster` a partir do centro da câmera; dwell de **1500 ms** com anel de progresso; cooldown de 1 s após troca |
| `FloorMenu` | Só em VR: ao olhar para baixo (pitch < −55°) aparece um anel de miniaturas dos ambientes no chão, selecionáveis pelo olhar |
| `UI` | Overlay HTML (desktop/mobile): título, nome do ambiente, barra de miniaturas, botões Giroscópio / VR / Tela cheia |
| `Editor` (`?edit=1`) | Clicar na imagem mostra/copiar `yaw`/`pitch` → para montar o `tour.json` sem adivinhação |

Entrada extra: **Enter / Espaço / gamepad botão 0** = "clique" no que está na mira (para quem tiver controle Bluetooth).

### 4.3 Fluxo do modo VR

```
[Toque "Entrar em VR"]
   → requestPermission (iOS) → requestFullscreen + lock landscape (Android) → wakeLock
   → overlay "Coloque o celular no óculos" (contagem 5 s, com tela dividida já ativa)
   → render estéreo + giroscópio + mira
   → olhar hotspot 1,5 s → fade → novo ambiente
   → olhar pro chão → menu de ambientes
   → sair: tocar na tela 2x (fora do óculos) ou botão Voltar
```

> Dica: depois de entrar em VR, o yaw inicial é "zerado" para onde a pessoa está olhando, para o ambiente começar sempre de frente para o `initialYaw`.

---

## 5. Direção visual (UI fora do VR)

Tema: **"galeria noturna"** — a imagem é a protagonista; a interface é um passe-partout discreto.

- **Fundo/overlays:** grafite quente `#0E0D0B` com vidro fosco (`backdrop-filter: blur(14px)`, 60% opacidade), borda hairline `rgba(255,255,255,.08)`.
- **Acento único:** latão `#C9A46A` (anel do hotspot, progresso do gaze, item ativo).
- **Tipografia:** *Fraunces* (títulos, itálico óptico para o nome do ambiente) + *Manrope* (rótulos, UI). Google Fonts.
- **Hotspot:** círculo de 48 px com anel latão que "respira" (pulse 2,4 s), seta no chão em perspectiva; ao passar o mouse, o rótulo surge com o nome do destino.
- **Entrada da página:** fade do preto para a imagem + nome do ambiente em Fraunces itálico subindo e sumindo depois de 2 s (como legenda de filme).
- **Barra de miniaturas:** inferior, recolhível, miniaturas 16:9 arredondadas 10 px; atual com contorno latão.
- **Botão "Ver em VR":** destaque, ícone de óculos (SVG inline, sem emoji), só aparece em dispositivos com toque.
- **No VR:** zero UI em HTML (não aparece no estéreo). Tudo é 3D: mira branca 6 px + anel latão de progresso, rótulos em canvas-texture.
- Acessibilidade: alvos ≥ 44 px, `prefers-reduced-motion` desliga autorotação e pulsos, contraste AA nos rótulos.

---

## 6. Plano de construção (etapas)

| # | Etapa | Entrega / critério de pronto |
|---|---|---|
| 1 | **Esqueleto** | `index.html` com importmap, esfera, 1 imagem, arrastar com mouse/toque, zoom. Roda no PC e celular. |
| 2 | **Multiambiente** | `tour.json`, `SceneManager`, fade, pré-carga, miniaturas. Seleção 4k/8k por `MAX_TEXTURE_SIZE`. |
| 3 | **Hotspots** | Hotspots 3D clicáveis + `?edit=1` para capturar yaw/pitch. |
| 4 | **Giroscópio** | Botão de permissão (iOS), `GyroControls`, alternar toque ↔ giroscópio. |
| 5 | **Modo VR** | `StereoRenderer`, fullscreen/landscape/wakeLock, overlay "coloque no óculos". |
| 6 | **Gaze** | Mira, raycast central, dwell 1,5 s com anel, cooldown, suporte a Enter/gamepad. |
| 7 | **Menu do chão** | Miniaturas no chão ativadas por pitch < −55°. |
| 8 | **PWA + deploy** | Manifest, ícone, deploy HTTPS (Netlify/Vercel), instrução "Adicionar à Tela de Início" no iPhone. |
| 9 | **Teste real** | No celular do cliente **dentro do VR One Plus** (checklist abaixo). |

---

## 7. Checklist de teste

- [ ] PC (Chrome, Edge, Safari): arrastar, zoom, hotspot, miniaturas.
- [ ] Android Chrome: toque, giroscópio, VR, tela cheia em paisagem, tela não apaga.
- [ ] iPhone Safari: pedido de permissão aparece, giroscópio funciona, VR via ícone na Tela de Início (sem barras do Safari).
- [ ] Celular **cabe** na bandeja do VR One Plus; imagens alinhadas com as lentes (sem visão dupla). Se necessário, ajustar `eyeSep` e o centro de cada metade.
- [ ] Gaze: trocar de ambiente só olhando, sem disparos acidentais (cooldown funciona).
- [ ] Menu do chão acessível de qualquer ambiente.
- [ ] Imagens 4k carregam em < 2 s em 4G; sem travamento ao trocar.
- [ ] 5 minutos de uso sem esquentar demais / sem enjoo (sem animação de câmera em VR).

---

## 8. Perguntas para confirmar com o cliente

1. **Qual celular** vai no óculos? (iPhone ou Android, e tamanho — define testes e se cabe na bandeja)
2. Quantos ambientes e de onde vêm as imagens? (câmera 360 ou render 3D — se render, exportar já em 8192×4096)
3. A navegação pelo **olhar** atende, ou ele tem/quer um **controle Bluetooth**?
4. Precisa de logo/marca, textos ou planta baixa (minimapa) no tour?
5. Vai rodar **online** (link) ou **offline** em evento/stand sem internet? (se offline: PWA com cache de todas as imagens via Service Worker)

---

## 9. Resumo para o cliente (texto pronto)

> O tour vai abrir num link comum. No computador, a pessoa arrasta com o mouse e clica nas setas para trocar de ambiente. No celular, pode arrastar com o dedo ou mover o aparelho. Para usar no óculos ZEISS, basta tocar em **"Ver em VR"**, encaixar o celular no óculos e olhar em volta. Como o óculos não tem botões, **para ir a outro ambiente é só olhar para a seta por um segundo e meio** — um anel se completa e você é levado até lá. Olhando para o chão, aparece um menu com todos os ambientes.

---

## 10. Status da implementação (16/10/2026)

**Decisões confirmadas:** celular **Android**, tour **online** (offline fica para uma 2ª fase). 14 imagens do WEEMO em `360/` (originais, 8000–8192 px, fora do git).

Etapas 1–8 implementadas em `index.html` + `tour.json`:

| Item | Onde |
|---|---|
| Imagens web (4k celular/VR, 8k desktop, miniaturas) | `python tools/build_panos.py` → `panos/` (63 MB) |
| Ambientes e grupos (Áreas comuns, Tipo 04, Tipo 02, Cobertura) | `tour.json` |
| Desktop: arrastar com inércia, zoom, gaveta de ambientes, autorotação após 15 s parado | `index.html` |
| Celular: toque, pinça, giroscópio | botão de celular |
| VR: tela dividida + correção de lente + giroscópio + mira + navegação pelo olhar (1,5 s) + anel de ambientes ao olhar para baixo | botão **Ver em VR** |
| Ajuste do óculos (distância entre lentes, campo de visão, correção) salvo no aparelho | tocar na tela durante o VR → *Ajustar óculos* |
| Editor de hotspots | abrir com `?edit=1` |

**Falta:**
1. **Posicionar os hotspots** (`?edit=1`): clicar no ponto da porta/passagem → escolher destino → *Baixar tour.json* → substituir o arquivo. Sem hotspots o tour já funciona: no VR a navegação é pelo anel do chão.
2. Definir a vista inicial de cada ambiente (botão no editor).
3. **Deploy HTTPS** (Netlify Drop, Vercel ou GitHub Pages: subir a pasta sem `360/` e `tools/`).
4. **Teste no celular real dentro do ZEISS VR One Plus** e ajuste de lentes (seção 7).
5. **Fase 2, offline:** o Kuula não tem um modo offline documentado (o VR dele é WebXR no navegador, online). Opções: PWA com Service Worker que guarda as 63 MB no celular (mais simples, abre sem internet pelo ícone) ou um app Android (WebView/Capacitor) com as imagens embutidas.

**Teste local:** `npx serve .` (ou `python -m http.server`). No celular, o giroscópio exige HTTPS, então teste via deploy ou túnel (`npx localtunnel --port 3000`).
