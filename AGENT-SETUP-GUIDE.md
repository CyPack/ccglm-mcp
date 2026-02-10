# 🤖 GLM Hybrid Orchestration - Agent-Friendly Setup Guide

> **Bu dosyayı Claude Code'a okut ve "Bu sistemi kur" de. Otonom olarak tüm kurulumu yapacaktır.**

---

## 📋 Özet

Bu rehber, Claude Code (Opus/Sonnet) ile Z.AI GLM modellerini hibrit bir şekilde kullanmanı sağlar:
- **Opus**: Orchestrator (planlama, review, tool kullanımı)
- **GLM**: Worker (kod yazma, generation, boilerplate)
- **Maliyet optimizasyonu**: Ağır işler ucuz GLM'e delege edilir

---

## 🚀 AGENT KURULUM PROMPT'U

Aşağıdaki prompt'u Claude Code'a ver:

```
Bu AGENT-SETUP-GUIDE.md dosyasını oku ve GLM Hybrid Orchestration sistemini kur:
1. Gerekli dosyaları oluştur
2. MCP server'ı kaydet
3. CLAUDE.md'ye kuralları ekle
4. Test et ve doğrula
```

---

## 📁 Dosya Yapısı

```
~/projects/ccglm-mcp/           # Ana dizin
├── ccglm_mcp_server.py         # MCP Server (ana dosya)
├── .env                        # API credentials (GİZLİ)
├── .env.example                # Örnek .env
├── requirements.txt            # Python bağımlılıkları
├── test_server.py              # Test suite
└── README.md                   # Dokümantasyon

~/.claude/
├── settings.json               # MCP server kaydı
└── CLAUDE.md                   # GLM routing kuralları
```

---

## 🔧 KURULUM ADIMLARI

### Adım 1: Repository'yi Klonla

```bash
cd ~/projects
git clone https://github.com/CyPack/ccglm-mcp.git
cd ccglm-mcp
```

### Adım 2: Python Bağımlılıklarını Kur

```bash
pip install -r requirements.txt
```

**requirements.txt içeriği:**
```
mcp>=1.0.0
python-dotenv>=1.0.0
```

### Adım 3: API Credentials Ayarla

`.env` dosyası oluştur:

```bash
cat > .env << 'EOF'
# Z.AI GLM Configuration
GLM_BASE_URL=https://api.z.ai/api/anthropic
GLM_AUTH_TOKEN=YOUR_API_TOKEN_HERE
EOF
chmod 600 .env
```

> ⚠️ `YOUR_API_TOKEN_HERE` kısmını kendi Z.AI API token'ınla değiştir.
> Token almak için: https://z.ai adresinden kayıt ol.

### Adım 4: MCP Server'ı Kaydet

`~/.claude.json` dosyasına ekle (veya oluştur):

```json
{
  "mcpServers": {
    "ccglm-mcp": {
      "type": "stdio",
      "command": "python3",
      "args": ["/FULL/PATH/TO/ccglm-mcp/ccglm_mcp_server.py"],
      "env": {}
    }
  }
}
```

> ⚠️ `/FULL/PATH/TO/` kısmını kendi path'inle değiştir (örn: `/home/username/projects/`)

**Veya CLI ile:**
```bash
# Mevcut config'i kontrol et
cat ~/.claude.json | jq '.mcpServers'

# Manuel ekle veya Claude Code'a "MCP server kaydet" de
```

### Adım 5: CLAUDE.md'ye GLM Kurallarını Ekle

`~/.claude/CLAUDE.md` dosyasına aşağıdaki bölümü ekle:

```markdown
---

## 🤖 GLM HYBRID ORCHESTRATION

### Mimari: Opus Master + GLM Worker

```
┌─────────────────────────────────────────────────────────────┐
│                    OPUS (Orchestrator)                       │
│  • Görev analizi ve planlama                                │
│  • Kod review ve kalite kontrolü                            │
│  • Karmaşık reasoning ve karar verme                        │
│  • Tool kullanımı (MCP, file ops, git)                      │
│  • Sonuç birleştirme ve raporlama                           │
└───────────────────────┬─────────────────────────────────────┘
                        │ Delege
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    GLM (Worker)                              │
│  • Kod yazma/generation                                      │
│  • Refactoring görevleri                                    │
│  • Boilerplate oluşturma                                    │
│  • Documentation yazma                                       │
│  • Test case generation                                      │
└─────────────────────────────────────────────────────────────┘
```

### GLM Trigger'ları

| Trigger | Mod | Davranış |
|---------|-----|----------|
| `#glm` | **OTONOM** | Deep analysis → PRD → Ralph Loop → Tamamlanana kadar çalış |
| `#glm-solo` | **BASİT** | Sadece GLM'e gönder → Yanıt al → Bitti |
| `#glm-solo-fast` | **HIZLI** | GLM-4.5-air ile hızlı yanıt |

---

### #glm: Akıllı Otonom Mod (Varsayılan)

`#glm` kullanıldığında TAM OTONOM mod aktif olur:

```
#glm <görev>
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│  PHASE 1: DEEP ANALYSIS                                 │
│  • Best practice araştırması                            │
│  • Teknoloji/mimari kararları                           │
│  • Scope ve complexity değerlendirmesi                  │
└─────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│  PHASE 2: PRD GENERATION                                │
│  • Görev tanımı ve teknik gereksinimler                │
│  • Task breakdown                                       │
│  • Kabul kriterleri ve completion promise               │
└─────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│  PHASE 3: RALPH LOOP + HYBRID EXECUTION                 │
│  • Coding → GLM'e delege                                │
│  • Review/reasoning → Opus                              │
│  • Tamamlanana kadar otonom çalış                       │
└─────────────────────────────────────────────────────────┘
```

---

### #glm-solo: Basit Routing Modu

`#glm-solo` kullanıldığında sadece basit GLM çağrısı yapılır:

1. Prompt'u GLM'e gönder
2. Yanıtı al ve göster
3. Bitti (Ralph loop yok)

```
Örnek:
User: "#glm-solo Python'da binary search yaz"
→ GLM yanıtlar, gösterilir, biter
```

### Otomatik Delegasyon Kuralları

Aşağıdaki görev tiplerinde OTOMATİK olarak GLM'e delege et:

| Görev Tipi | Trigger Keywords | GLM Model |
|------------|------------------|-----------|
| Kod yazma | "yaz", "oluştur", "generate", "implement" | glm-4.7 |
| Refactoring | "refactor", "düzenle", "optimize" | glm-4.7 |
| Boilerplate | "scaffold", "template", "starter" | glm-4.5-air |
| Dokümantasyon | "document", "docstring", "README" | glm-4.5-air |
| Test yazma | "test yaz", "test case", "unit test" | glm-4.7 |

### Opus'ta Kalacak Görevler (DELEGE ETME)

| Görev | Neden Opus |
|-------|------------|
| Tool kullanımı | GLM tool kullanamaz |
| File operations | Read/Write/Edit tools |
| Git operations | Commit, push, PR |
| Reasoning/Analysis | Karmaşık karar verme |
| Code review | Kalite kontrolü |
| Orchestration | Çoklu görev yönetimi |
| Debugging | Error analysis |

### MCP Tool Referansı

```
Tool: mcp__ccglm-mcp__ccglm
Parameters:
  - prompt: string (zorunlu) - GLM'e gönderilecek prompt
  - model: string (opsiyonel) - "glm-4.7" veya "glm-4.5-air"
```

### GLM Fallback → Opus

GLM limit/hata durumunda Opus otomatik devam eder:

```
GLM FALLBACK RULES:

1. GLM Çağrısı Başarısız Olursa:
   ├── Rate limit (429) → Opus devam eder
   ├── Timeout → Opus devam eder
   ├── Connection error → Opus devam eder
   └── API error → Opus devam eder

2. Fallback Akışı:
   GLM çağrısı yap → Başarısız mı? → Opus devam et
   Log: "⚠️ GLM limit/hata, Opus olarak devam ediyorum"
```

### Örnek Kullanımlar

```
# OTONOM MOD - analiz, PRD, Ralph Loop, tamamlanana kadar çalış
User: "#glm REST API endpoint yaz"
→ Deep analysis yapar
→ PRD oluşturur
→ Ralph loop başlatır
→ Kod yazar, test eder, tamamlar

# BASİT MOD - sadece GLM'e sor
User: "#glm-solo Fibonacci fonksiyonu yaz"
→ GLM'e gönderir
→ Yanıtı gösterir
→ Bitti

# HIZLI BASİT MOD
User: "#glm-solo-fast Merhaba de"
→ GLM-4.5-air ile hızlı yanıt
→ Bitti
```
```

### Adım 6: Claude Code'u Yeniden Başlat

```bash
# Terminal'i kapat ve yeniden aç
# veya
claude --version  # MCP server'ların yüklendiğini doğrula
```

### Adım 7: Test Et

```bash
# Test suite çalıştır
cd ~/projects/ccglm-mcp
python3 test_server.py
```

**Claude Code içinde test:**
```
#glm-solo Merhaba, kendini tanıt
```

Yanıt alıyorsan kurulum başarılı! ✅

> **Not:** `#glm` (otonom mod) Ralph Loop başlatır. Basit test için `#glm-solo` kullan.

---

## 🎯 KULLANIM ÖRNEKLERİ

### Otonom Mod (#glm) - Tam Güç

```
#glm REST API endpoint yaz
#glm Login sistemi implement et
#glm Kanban dashboard oluştur
#glm CSV parser yaz ve test et
```

Bu mod:
- Deep analysis yapar
- PRD oluşturur
- Ralph loop başlatır
- Tamamlanana kadar otonom çalışır

### Basit Mod (#glm-solo) - Hızlı Yanıt

```
#glm-solo Python'da quick sort yaz
#glm-solo Bu fonksiyonu açıkla
#glm-solo Regex pattern öner
```

Bu mod sadece GLM'e sorar ve yanıtı gösterir.

### Hızlı Basit Mod (#glm-solo-fast)

```
#glm-solo-fast Merhaba de
#glm-solo-fast 1+1 kaç?
```

GLM-4.5-air modeli ile çok hızlı yanıt alır.

---

## 🔍 TROUBLESHOOTING

### MCP Tool Görünmüyor

1. `~/.claude.json` dosyasını kontrol et
2. Path'in doğru olduğundan emin ol
3. Claude Code'u yeniden başlat

### GLM Timeout

- Uzun promptlarda timeout olabilir
- `glm-4.5-air` daha hızlı, timeout riski düşük
- Fallback aktif: Opus otomatik devam eder

### API Token Hatası

1. `.env` dosyasını kontrol et
2. Token'ın geçerli olduğunu doğrula
3. Z.AI hesabında kredi olduğundan emin ol

---

## 📊 MİMARİ DİYAGRAM

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER                                     │
│                          │                                       │
│                          ▼                                       │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                 CLAUDE CODE (Opus/Sonnet)                  │  │
│  │                                                            │  │
│  │   #glm detected? ──────────────────────────┐              │  │
│  │        │                                    │              │  │
│  │        ▼                                    ▼              │  │
│  │   ┌─────────┐                        ┌───────────┐        │  │
│  │   │  OPUS   │◄── Fallback ───────────│    GLM    │        │  │
│  │   │ Master  │                        │  Worker   │        │  │
│  │   └────┬────┘                        └─────┬─────┘        │  │
│  │        │                                   │              │  │
│  │        ▼                                   ▼              │  │
│  │   • Planning          MCP Tool:  mcp__ccglm-mcp__ccglm   │  │
│  │   • Review                   │                            │  │
│  │   • Tool use                 ▼                            │  │
│  │   • Git ops           ┌─────────────┐                     │  │
│  │                       │ Z.AI GLM API│                     │  │
│  │                       │  glm-4.7    │                     │  │
│  │                       │glm-4.5-air  │                     │  │
│  │                       └─────────────┘                     │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📝 DOSYA İÇERİKLERİ

### ccglm_mcp_server.py (Ana Kod)

```python
#!/usr/bin/env python3
"""
CCGLM MCP Server - Routes prompts to GLM via Claude CLI with Z.AI credentials
"""

import asyncio
import os
import sys
import time
from typing import Any, Dict, List, Set
from dotenv import load_dotenv

import mcp.server.stdio
import mcp.types as types
from mcp.server import Server

load_dotenv()

# Configuration
DEFAULT_TIMEOUT = 300
MAX_TIMEOUT = 600
GLM_BASE_URL = os.getenv("GLM_BASE_URL", "https://api.z.ai/api/anthropic")
GLM_AUTH_TOKEN = os.getenv("GLM_AUTH_TOKEN")

server = Server("ccglm-mcp")

@server.list_tools()
async def list_tools() -> List[types.Tool]:
    return [
        types.Tool(
            name="ccglm",
            description="Route prompt to GLM-4.7 (default) or glm-4.5-air (fast)",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Prompt to send to GLM"},
                    "model": {
                        "type": "string",
                        "description": "GLM model to use",
                        "default": "glm-4.7",
                        "enum": ["glm-4.7", "glm-4.5-air"]
                    }
                },
                "required": ["prompt"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    if name == "ccglm":
        result = await ccglm_route(arguments)
        if "error" in result:
            return [types.TextContent(type="text", text=f"❌ Error: {result['error']}")]
        return [types.TextContent(type="text", text=result.get("response", "No response"))]
    return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

async def ccglm_route(args: Dict[str, Any]) -> Dict[str, Any]:
    prompt = args.get("prompt", "")
    model = args.get("model", "glm-4.7")

    if not prompt:
        return {"error": "No prompt provided"}

    env = os.environ.copy()
    env["ANTHROPIC_BASE_URL"] = GLM_BASE_URL
    env["ANTHROPIC_AUTH_TOKEN"] = GLM_AUTH_TOKEN
    env["ANTHROPIC_MODEL"] = model

    timeout = 120 if model == "glm-4.5-air" else DEFAULT_TIMEOUT

    cmd = ["claude", "--dangerously-skip-permissions", "-c", "-p"]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        stdin=asyncio.subprocess.PIPE,
        env=env
    )

    try:
        stdout, stderr = await asyncio.wait_for(
            process.communicate(input=prompt.encode('utf-8')),
            timeout=timeout
        )
        return {"response": stdout.decode('utf-8', errors='replace').strip()}
    except asyncio.TimeoutError:
        process.kill()
        return {"error": f"Timeout after {timeout}s"}

async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
```

### .env.example

```bash
# Z.AI GLM Configuration
# Get your token from https://z.ai
GLM_BASE_URL=https://api.z.ai/api/anthropic
GLM_AUTH_TOKEN=your_api_token_here
```

### requirements.txt

```
mcp>=1.0.0
python-dotenv>=1.0.0
```

---

## ✅ KURULUM KONTROL LİSTESİ

Agent için kontrol listesi:

- [ ] Repository klonlandı
- [ ] Python bağımlılıkları kuruldu (`pip install -r requirements.txt`)
- [ ] `.env` dosyası oluşturuldu ve token eklendi
- [ ] `.env` dosyası `chmod 600` ile korunuyor
- [ ] MCP server `~/.claude.json`'a kaydedildi
- [ ] CLAUDE.md'ye GLM kuralları eklendi
- [ ] Claude Code yeniden başlatıldı
- [ ] `#glm test` ile test edildi ve yanıt alındı
- [ ] `python3 test_server.py` tüm testler geçti

---

## 🔗 KAYNAKLAR

- **Repository:** https://github.com/CyPack/ccglm-mcp
- **Z.AI:** https://z.ai
- **MCP Protocol:** https://github.com/anthropics/mcp

---

## 📄 LİSANS

Bu proje MIT lisansı altında sunulmaktadır.

---

**Son Güncelleme:** 2026-02-01
**Versiyon:** 1.0.0
