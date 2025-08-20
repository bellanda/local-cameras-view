# Local Camera Viewer v2.0 🚀

Sistema avançado de visualização de câmeras locais e IP com suporte a múltiplos clientes simultâneos.

## ✨ Novas Funcionalidades v2.0

- **🔀 Suporte a Múltiplos Clientes**: Múltiplas pessoas podem assistir à mesma câmera simultaneamente
- **⚡ Servidor Intermediário**: Usa PyFFMPEG e OpenCV para otimização de performance
- **📊 Monitoramento em Tempo Real**: Endpoints de status para acompanhar o sistema
- **🔄 Gerenciamento Inteligente**: Reconexão automática e fallback para diferentes backends
- **🌐 API REST**: Documentação automática com Swagger/OpenAPI

## 🏗️ Arquitetura

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Cliente 1     │    │   Cliente 2      │    │   Cliente N     │
│   (Navegador)   │    │   (Navegador)    │    │   (Navegador)   │
└─────────┬───────┘    └──────────┬───────┘    └─────────┬───────┘
          │                        │                      │
          └────────────────────────┼──────────────────────┘
                                   │
                    ┌───────────────▼───────────────┐
                    │      FastAPI Server           │
                    │   (Stream Manager)            │
                    └───────────────┬───────────────┘
                                   │
                    ┌───────────────▼───────────────┐
                    │    Camera Stream Manager      │
                    │   (Single Connection)         │
                    └───────────────┬───────────────┘
                                   │
                    ┌───────────────▼───────────────┐
                    │      Camera (RTSP/Webcam)     │
                    └───────────────────────────────┘
```

## 🚀 Instalação

### Pré-requisitos

- Python 3.12+
- FFmpeg instalado no sistema
- Webcam ou câmeras IP configuradas

### Instalação das Dependências

```bash
# Usar uv (recomendado)
uv sync

# Ou instalar manualmente
pip install -r requirements.txt
```

## ⚙️ Configuração

### 1. Configurar Câmeras

Edite o arquivo `cameras.xlsx` com suas câmeras:

| Nome    | Usuário | Senha  | IP            | Marca     |
| ------- | ------- | ------ | ------------- | --------- |
| WEBCAM  | -       | -      | -             | WEBCAM    |
| Câmera1 | admin   | 123456 | 192.168.1.100 | HIKVISION |
| Câmera2 | admin   | 123456 | 192.168.1.101 | INTELBRAS |

### 2. Configurações de Performance

Edite `utils/config.py` para otimizar:

```python
CAMERA_CONFIG = {
    "max_buffer_size": 30,      # Frames no buffer
    "target_fps": 30,           # FPS alvo
    "jpeg_quality": 85,         # Qualidade JPEG
    "frame_timeout": 30.0,      # Timeout de frame
}
```

## 🎯 Uso

### 1. Iniciar o Servidor

```bash
uv run main.py
```

### 2. Acessar a Interface

- **Local**: http://localhost:8000
- **Rede**: http://[SEU_IP]:8000
- **API Docs**: http://localhost:8000/docs
- **Status**: http://localhost:8000/api/status

### 3. Visualizar Câmeras

- Abra múltiplas abas do navegador
- Acesse a mesma câmera em diferentes dispositivos
- Todas as conexões funcionarão simultaneamente

## 🧪 Testes

### Teste de Múltiplos Clientes

```bash
# Instalar dependência de teste
uv add aiohttp

# Executar testes
uv run test_multi_client.py
```

### Teste Manual

1. Abra 3-5 abas do navegador
2. Acesse a mesma câmera em todas
3. Verifique se todas funcionam simultaneamente
4. Monitore o status em `/api/status`

## 📊 Monitoramento

### Endpoints de Status

- `GET /api/status` - Status geral do sistema
- `GET /api/cameras/{nome}/status` - Status de câmera específica
- `POST /api/cameras/{nome}/restart` - Reiniciar câmera

### Métricas Disponíveis

- Número de clientes por câmera
- Tamanho do buffer de frames
- Status de conexão
- Tempo do último frame

## 🔧 Troubleshooting

### Problema: Câmera não conecta

```bash
# Verificar logs do servidor
# Verificar configuração da câmera
# Testar RTSP URL manualmente
```

### Problema: Performance baixa

```python
# Ajustar em utils/config.py:
CAMERA_CONFIG["jpeg_quality"] = 70  # Reduzir qualidade
CAMERA_CONFIG["target_fps"] = 15    # Reduzir FPS
```

### Problema: Muitos clientes simultâneos

```python
# Ajustar em utils/config.py:
PERFORMANCE_CONFIG["max_clients_per_camera"] = 25
```

## 🏗️ Estrutura do Projeto

```
local-cameras-view/
├── main.py                      # Servidor principal
├── constants/
│   ├── camera.py               # Configuração de câmeras
│   └── paths.py                # Caminhos do sistema
├── utils/
│   ├── camera_stream_manager.py # Gerenciador de streams
│   ├── construct_rtsp_url.py   # Construtor de URLs RTSP
│   ├── status_endpoint.py      # Endpoints de status
│   └── config.py               # Configurações do sistema
├── cameras.xlsx                 # Configuração de câmeras
├── test_multi_client.py        # Script de teste
└── pyproject.toml              # Dependências do projeto
```

## 🚀 Performance

### Otimizações Implementadas

- **Buffer Circular**: Evita vazamento de memória
- **Rate Limiting**: Controle de FPS para evitar sobrecarga
- **Fallback Automático**: PyFFMPEG → OpenCV se necessário
- **Queue Management**: Gerenciamento inteligente de clientes
- **Keep-alive**: Frames de manutenção para conexões estáveis

### Benchmarks Esperados

- **Webcam**: 10-20 clientes simultâneos
- **IP Camera**: 5-15 clientes simultâneos
- **Latência**: < 500ms para novos clientes
- **Uso de CPU**: < 30% por câmera ativa

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para detalhes.

## 🙏 Agradecimentos

- OpenCV para processamento de vídeo
- PyFFMPEG para otimização de streams RTSP
- FastAPI para o servidor web
- Comunidade Python para as bibliotecas utilizadas

---

**🎯 Objetivo**: Permitir que múltiplas pessoas visualizem câmeras simultaneamente sem degradação de performance.
