<p align="center">
  <img src="assets/indagis-banner.png" alt="Banner de Indagis Agent" width="100%" />
</p>

<h1 align="center">Indagis Agent</h1>
<p align="center"><b>Workspace de IA para investigación en ciberseguridad — OSINT, inteligencia de amenazas, DFIR.</b></p>
<p align="center">
  Construido sobre <a href="https://hermes-agent.nousresearch.com/">Hermes Agent</a> (Nous Research, MIT)
</p>
<p align="center">
  <a href="https://hermes-agent.nousresearch.com/docs/"><img src="https://img.shields.io/badge/Docs%20del%20Motor-hermes--agent.nousresearch.com-FFD700?style=for-the-badge" alt="Documentación del motor"></a>
  <a href="https://github.com/agtktID/indagis-agent/issues"><img src="https://img.shields.io/badge/Issues-agtktID%2Findagis--agent-blue?style=for-the-badge&logo=github" alt="Issues"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/Licencia-MIT-green?style=for-the-badge" alt="Licencia: MIT"></a>
  <a href="https://discord.gg/NousResearch"><img src="https://img.shields.io/badge/Discord-Comunidad%20Hermes-5865F2?style=for-the-badge&logo=discord&logoColor=white" alt="Discord"></a>
  <a href="README.md"><img src="https://img.shields.io/badge/Lang-English-blue?style=for-the-badge" alt="English"></a>
  <a href="README.zh-CN.md"><img src="https://img.shields.io/badge/Lang-中文-red?style=for-the-badge" alt="中文"></a>
  <a href="README.ur-pk.md"><img src="https://img.shields.io/badge/Lang-اردو-green?style=for-the-badge" alt="اردو"></a>
</p>

**Indagis Agent es un workspace de IA open-core para investigación en ciberseguridad** — OSINT, inteligencia de amenazas y DFIR (forense digital y respuesta a incidentes). Registra el trabajo de seguridad como **Investigaciones** persistidas: un objetivo, un alcance autorizado, evidencia, hallazgos y una línea de tiempo, todo construido sobre un motor de agente con mejora continua — el único agente con un bucle de aprendizaje integrado, que crea y refina habilidades a partir de la experiencia, se impulsa a sí mismo a persistir el conocimiento y construye un modelo cada vez más profundo de quién eres a lo largo de las sesiones. Ejecútalo en un VPS de $5, un clúster de GPUs o infraestructura sin servidor que cuesta casi nada cuando está inactiva. No está atado a tu laptop — habla con él desde Telegram mientras trabaja en una VM en la nube.

Usa cualquier modelo que quieras — [Nous Portal](https://portal.nousresearch.com), [OpenRouter](https://openrouter.ai) (más de 200 modelos), [NovitaAI](https://novita.ai), [NVIDIA NIM](https://build.nvidia.com) (Nemotron), [Xiaomi MiMo](https://platform.xiaomimimo.com), [z.ai/GLM](https://z.ai), [Kimi/Moonshot](https://platform.moonshot.ai), [MiniMax](https://www.minimax.io), [Hugging Face](https://huggingface.co), OpenAI, o tu propio endpoint. Cambia con `hermes model` — sin cambios de código, sin dependencias.

<table>
<tr><td><b>Investigaciones con control de autorización</b></td><td>Modelo <code>Investigation</code> persistido — objetivo, alcance autorizado, evidencia, hallazgos, línea de tiempo. Cada destino registrado se verifica contra el alcance antes de escribirse (fail-closed, cierre seguro por defecto), con vistas previas <code>--dry-run</code> y exportación a Markdown/JSON.</td></tr>
<tr><td><b>Una interfaz de terminal real</b></td><td>TUI completa con edición multilínea, autocompletado de comandos, historial de conversaciones, interrupción y redirección, y salida de herramientas en streaming.</td></tr>
<tr><td><b>Vive donde tú vives</b></td><td>Telegram, Discord, Slack, WhatsApp, Signal y CLI — todo desde un único proceso gateway. Transcripción de notas de voz, continuidad de conversación entre plataformas.</td></tr>
<tr><td><b>Un bucle de aprendizaje cerrado</b></td><td>Memoria curada por el agente con recordatorios periódicos. Creación autónoma de habilidades tras tareas complejas. Las habilidades mejoran solas durante el uso. Búsqueda FTS5 de sesiones con resumención por LLM para recuperación entre sesiones. Modelado de usuario dialéctico <a href="https://github.com/plastic-labs/honcho">Honcho</a>. Compatible con el estándar abierto de <a href="https://agentskills.io">agentskills.io</a>.</td></tr>
<tr><td><b>Automatizaciones programadas</b></td><td>Planificador cron integrado con entrega a cualquier plataforma. Informes diarios, copias de seguridad nocturnas, auditorías semanales — todo en lenguaje natural, ejecutándose de forma autónoma.</td></tr>
<tr><td><b>Delega y paraleliza</b></td><td>Lanza subagentes aislados para flujos de trabajo paralelos. Escribe scripts de Python que llaman a herramientas vía RPC, convirtiendo pipelines de múltiples pasos en turnos de coste cero de contexto.</td></tr>
<tr><td><b>Funciona en cualquier lugar, no solo en tu laptop</b></td><td>Seis backends de terminal — local, Docker, SSH, Singularity, Modal y Daytona. Daytona y Modal ofrecen persistencia sin servidor — el entorno de tu agente hiberna cuando está inactivo y se activa bajo demanda, costando casi nada entre sesiones. Ejecútalo en un VPS de $5 o un clúster de GPUs.</td></tr>
<tr><td><b>Listo para investigación</b></td><td>Generación de trayectorias en lote, compresión de trayectorias para entrenar la próxima generación de modelos de llamadas a herramientas.</td></tr>
</table>

---

## Instalación rápida

### Linux, macOS, WSL2, Termux

```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
```

### Windows (nativo, PowerShell)

> **Nota:** En Windows nativo, Hermes funciona sin WSL — la CLI, el gateway, la TUI y las herramientas funcionan de forma nativa. Si prefieres usar WSL2, el comando de Linux/macOS de arriba también funciona allí. ¿Encontraste un error? Por favor [crea un issue](https://github.com/agtktID/indagis-agent/issues).

Ejecuta esto en PowerShell:

```powershell
iex (irm https://hermes-agent.nousresearch.com/install.ps1)
```

El instalador se encarga de todo: uv, Python 3.11, Node.js, ripgrep, ffmpeg, **y un Git Bash portátil** (MinGit, descomprimido en `%LOCALAPPDATA%\indagis\git` — no requiere administrador, completamente aislado de cualquier instalación de Git del sistema). Hermes usa este Git Bash incluido para ejecutar comandos de shell.

Si ya tienes Git instalado, el instalador lo detecta y lo usa en su lugar. De lo contrario, una descarga de ~45MB de MinGit es todo lo que necesitas — no tocará ni interferirá con ningún Git del sistema.

> **Android / Termux:** La ruta manual probada está documentada en la [guía de Termux](https://hermes-agent.nousresearch.com/docs/getting-started/termux). En Termux, Hermes instala el extra `.[termux]` curado porque el extra completo `.[all]` actualmente incluye dependencias de voz incompatibles con Android.
>
> **Windows:** Windows nativo es totalmente compatible — el comando de PowerShell de arriba instala todo. Si prefieres usar WSL2, el comando de Linux también funciona allí. La instalación nativa de Windows se encuentra en `%LOCALAPPDATA%\indagis`; WSL2 instala en `~/.indagis` como en Linux.

Después de la instalación:

```bash
source ~/.bashrc    # recargar shell (o: source ~/.zshrc)
hermes              # ¡empieza a chatear!
```

---

## Primeros pasos

```bash
hermes              # CLI interactiva — inicia una conversación
hermes model        # Elige tu proveedor y modelo LLM
hermes tools        # Configura qué herramientas están habilitadas
hermes config set   # Establece valores de configuración individuales
hermes gateway      # Inicia el gateway de mensajería (Telegram, Discord, etc.)
hermes setup        # Ejecuta el asistente de configuración completo
hermes claw migrate # Migra desde OpenClaw (si vienes de OpenClaw)
hermes update       # Actualiza a la última versión
hermes doctor       # Diagnostica cualquier problema
```

📖 **[Documentación completa →](https://hermes-agent.nousresearch.com/docs/)**

---

## Investigaciones

Indagis Agent registra el trabajo de seguridad como **Investigaciones** de primera clase — unidades de trabajo persistidas y delimitadas por autorización, con evidencia, hallazgos y una línea de tiempo. Cada resultado lleva su procedencia (fuente, herramienta, destino, fecha, hash opcional, nivel de confianza), y cada acción que registra un destino se verifica contra el alcance autorizado de la investigación antes de escribirse.

```bash
hermes investigation create "Assess acme-corp exposure" --scope acme.example

hermes investigation add-evidence <investigation> \
  --description "Open port 443" --source nmap-scan --tool nmap \
  --target acme.example --confidence high

hermes investigation add-finding <investigation> \
  --summary "TLS misconfiguration" --severity high --evidence <evidence-id> \
  --source analyst --tool manual --target acme.example --confidence high

hermes investigation show <investigation>
hermes investigation export <investigation> --format md --output ./reports
```

- **Autorización fail-closed (cierre seguro por defecto)** — la evidencia y los hallazgos para un destino fuera del alcance declarado de la investigación se rechazan con un motivo explícito; `--dry-run` muestra una vista previa del veredicto de autorización sin escribir nada.
- **Lista completa de comandos**: `create`, `list` (`ls`), `show` (`open`), `add-evidence`, `add-finding`, `export`, `close`, `reopen`, `archive`.
- **Exportación**: Markdown (con una línea de integridad SHA256 sobre el cuerpo exportado) o JSON, ambos con procedencia completa y la línea de tiempo.

---

## Evita la colección de claves API — Nous Portal

Hermes funciona con cualquier proveedor que quieras — eso no cambiará. Pero si prefieres no recopilar cinco claves API separadas para el modelo, búsqueda web, generación de imágenes, TTS y un navegador en la nube, **[Nous Portal](https://portal.nousresearch.com)** las cubre todas bajo una sola suscripción:

- **Más de 300 modelos** — elige cualquiera con `/model <nombre>`
- **Tool Gateway** — búsqueda web (Firecrawl), generación de imágenes (FAL), texto a voz (OpenAI), navegador en la nube (Browser Use), todo enrutado a través de tu suscripción. Sin cuentas adicionales.

Un comando desde una instalación nueva:

```bash
hermes setup --portal
```

Esto te autentica vía OAuth, establece Nous como tu proveedor y activa el Tool Gateway. Comprueba qué está conectado en cualquier momento con `hermes portal info`. Detalles completos en la [página de documentación del Tool Gateway](https://hermes-agent.nousresearch.com/docs/user-guide/features/tool-gateway).

Puedes seguir usando tus propias claves por herramienta cuando quieras — el gateway es por backend, no todo o nada.

---

## Referencia rápida: CLI vs Mensajería

Hermes tiene dos puntos de entrada: inicia la interfaz de terminal con `hermes`, o ejecuta el gateway y habla con él desde Telegram, Discord, Slack, WhatsApp, Signal o Email. Una vez en una conversación, muchos comandos de barra son compartidos entre ambas interfaces.

| Acción                              | CLI                                           | Plataformas de mensajería                                                         |
| ----------------------------------- | --------------------------------------------- | --------------------------------------------------------------------------------- |
| Empezar a chatear                   | `hermes`                                      | Ejecuta `hermes gateway setup` + `hermes gateway start`, luego envía un mensaje al bot |
| Nueva conversación                  | `/new` o `/reset`                             | `/new` o `/reset`                                                                 |
| Cambiar modelo                      | `/model [proveedor:modelo]`                   | `/model [proveedor:modelo]`                                                       |
| Establecer personalidad             | `/personality [nombre]`                       | `/personality [nombre]`                                                           |
| Reintentar o deshacer último turno  | `/retry`, `/undo`                             | `/retry`, `/undo`                                                                 |
| Comprimir contexto / ver uso        | `/compress`, `/usage`, `/insights [--days N]` | `/compress`, `/usage`, `/insights [days]`                                         |
| Explorar habilidades                | `/skills` o `/<nombre-habilidad>`             | `/<nombre-habilidad>`                                                             |
| Interrumpir trabajo actual          | `Ctrl+C` o enviar un nuevo mensaje            | `/stop` o enviar un nuevo mensaje                                                 |
| Estado específico de plataforma     | `/platforms`                                  | `/status`, `/sethome`                                                             |

Para las listas de comandos completas, consulta la [guía de CLI](https://hermes-agent.nousresearch.com/docs/user-guide/cli) y la [guía del Gateway de Mensajería](https://hermes-agent.nousresearch.com/docs/user-guide/messaging).

---

## Documentación

Toda la documentación está en **[hermes-agent.nousresearch.com/docs](https://hermes-agent.nousresearch.com/docs/)**:

| Sección                                                                                             | Contenido                                                    |
| --------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| [Inicio rápido](https://hermes-agent.nousresearch.com/docs/getting-started/quickstart)              | Instalar → configurar → primera conversación en 2 minutos   |
| [Uso de CLI](https://hermes-agent.nousresearch.com/docs/user-guide/cli)                             | Comandos, atajos de teclado, personalidades, sesiones        |
| [Configuración](https://hermes-agent.nousresearch.com/docs/user-guide/configuration)               | Archivo de configuración, proveedores, modelos, todas las opciones |
| [Gateway de Mensajería](https://hermes-agent.nousresearch.com/docs/user-guide/messaging)           | Telegram, Discord, Slack, WhatsApp, Signal, Home Assistant   |
| [Seguridad](https://hermes-agent.nousresearch.com/docs/user-guide/security)                        | Aprobación de comandos, emparejamiento por DM, aislamiento en contenedor |
| [Herramientas y Toolsets](https://hermes-agent.nousresearch.com/docs/user-guide/features/tools)   | Más de 40 herramientas, sistema de toolsets, backends de terminal |
| [Sistema de Habilidades](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills)   | Memoria procedimental, Skills Hub, creación de habilidades   |
| [Memoria](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory)                   | Memoria persistente, perfiles de usuario, mejores prácticas  |
| [Integración MCP](https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp)              | Conecta cualquier servidor MCP para capacidades extendidas   |
| [Programación Cron](https://hermes-agent.nousresearch.com/docs/user-guide/features/cron)           | Tareas programadas con entrega a plataforma                  |
| [Archivos de Contexto](https://hermes-agent.nousresearch.com/docs/user-guide/features/context-files) | Contexto de proyecto que da forma a cada conversación      |
| [Arquitectura](https://hermes-agent.nousresearch.com/docs/developer-guide/architecture)            | Estructura del proyecto, bucle del agente, clases principales |
| [Contribuir](https://hermes-agent.nousresearch.com/docs/developer-guide/contributing)              | Configuración de desarrollo, proceso de PR, estilo de código |
| [Referencia de CLI](https://hermes-agent.nousresearch.com/docs/reference/cli-commands)             | Todos los comandos y flags                                   |
| [Variables de Entorno](https://hermes-agent.nousresearch.com/docs/reference/environment-variables) | Referencia completa de variables de entorno                  |

---

## Migración desde OpenClaw

Si vienes de OpenClaw, Hermes puede importar automáticamente tu configuración, memorias, habilidades y claves API.

**Durante la configuración inicial:** El asistente de configuración (`hermes setup`) detecta automáticamente `~/.openclaw` y ofrece migrar antes de que comience la configuración.

**En cualquier momento después de instalar:**

```bash
hermes claw migrate              # Migración interactiva (preset completo)
hermes claw migrate --dry-run    # Vista previa de qué se migraría
hermes claw migrate --preset user-data   # Migrar sin secretos
hermes claw migrate --overwrite  # Sobreescribir conflictos existentes
```

Qué se importa:

- **SOUL.md** — archivo de personalidad
- **Memorias** — entradas de MEMORY.md y USER.md
- **Habilidades** — habilidades creadas por el usuario → `~/.indagis/skills/openclaw-imports/`
- **Lista de comandos permitidos** — patrones de aprobación
- **Configuración de mensajería** — configuración de plataformas, usuarios permitidos, directorio de trabajo
- **Claves API** — secretos en lista de permitidos (Telegram, OpenRouter, OpenAI, Anthropic, ElevenLabs)
- **Assets de TTS** — archivos de audio del espacio de trabajo
- **Instrucciones del espacio de trabajo** — AGENTS.md (con `--workspace-target`)

Consulta `hermes claw migrate --help` para todas las opciones, o usa la habilidad `openclaw-migration` para una migración guiada interactiva por el agente con vistas previas de dry-run.

---

## Contribuir

¡Las contribuciones son bienvenidas! Consulta la [Guía de Contribución](CONTRIBUTING.es.md) para la configuración del desarrollo, el estilo de código y el proceso de PR.

Inicio rápido para colaboradores — clona y comienza con `setup-hermes.sh`:

```bash
git clone https://github.com/NousResearch/hermes-agent.git
cd hermes-agent
./setup-hermes.sh     # instala uv, crea venv, instala .[all], enlaza ~/.local/bin/hermes
./hermes              # detecta automáticamente el venv, no necesitas hacer `source` primero
```

Ruta manual (equivalente a lo anterior):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv .venv --python 3.11
source .venv/bin/activate
uv pip install -e ".[all,dev]"
scripts/run_tests.sh
```

---

## Comunidad

- 💬 [Discord](https://discord.gg/NousResearch)
- 📚 [Skills Hub](https://agentskills.io)
- 🐛 [Issues](https://github.com/agtktID/indagis-agent/issues)
- 🔌 [computer-use-linux](https://github.com/avifenesh/computer-use-linux) — Servidor MCP de control de escritorio Linux para Hermes y otros hosts MCP, con árboles de accesibilidad AT-SPI, entrada Wayland/X11, capturas de pantalla y targeting de ventanas del compositor.
- 🔌 [HermesClaw](https://github.com/AaronWong1999/hermesclaw) — Puente WeChat comunitario: Ejecuta Hermes Agent y OpenClaw en la misma cuenta de WeChat.

---

## Fundamentos

Indagis Agent está construido sobre [Hermes Agent](https://github.com/NousResearch/hermes-agent) (Nous Research, Licencia MIT). Hermes Agent aporta el motor del agente, la capa de proveedores de LLM, el gateway de mensajería, la orquestación de habilidades y la persistencia de sesiones. Indagis Agent renueva la interfaz de cara al usuario, aplica la paleta de Indagis, adapta los componentes de la UI a un contexto de investigación en ciberseguridad, y añade encima el modelo de datos y la CLI específicos de investigación (`Investigation` / `Evidence` / `Finding` / `Timeline`).

| | |
|---|---|
| **Motor** | Hermes Agent v0.20 (MIT) — `agent/`, `providers/`, `tools/`, `gateway/`, `skills/` |
| **Capa de investigación** | Indagis Agent v0.1 (este repositorio) — `hermes_cli/investigation_*.py` |
| **Licencia** | MIT (Nous Research + colaboradores de Indagis Agent) |

## Licencia

MIT — ver [LICENSE](LICENSE).

Motor creado por [Nous Research](https://nousresearch.com).
