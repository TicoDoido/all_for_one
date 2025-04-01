# All For One - Gerenciador de Plugins para Jogos  

Uma aplicação GUI em Python para gerenciar e executar plugins de jogos de forma modular.  

## 📦 Funcionalidades Principais  

- ✅ Carregamento dinâmico de plugins  
- 🖥️ Interface gráfica intuitiva  
- 🔄 Recarregamento de plugins sem reiniciar  
- 📝 Sistema de log integrado  
- 🛠️ Arquitetura modular fácil de expandir  

## ⚙️ Pré-requisitos  

- Python 3.7 ou superior  

## 🚀 Como Começar  

1. Clone o repositório:  
```bash
git clone https://github.com/TicoDoido/all_for_one.git
cd all-for-one
```

2. Execute o aplicativo:  
```bash
ALL_FOR_ONE.py
```

## 🧩 Criando Plugins  

1. Crie um arquivo `.py` na pasta `plugins/`  
2. Use este template básico:  

```python
def register_plugin():
    return {
        "name": "Nome do Plugin",
        "description": "Descrição do que seu plugin faz",
        "commands": [
            {
                "label": "Texto do Botão",
                "action": lambda: print("Ação executada!")
            }
            # Adicione mais comandos conforme necessário
        ]
    }
```

3. Salve o arquivo e recarregue no aplicativo  

## 🖼️ Estrutura do Projeto  

```
all-for-one/
│
├── main.py            # Código principal
├── README.md          # Este arquivo
└── plugins/           # Pasta para seus plugins
    ├── exemplo1.py    # Plugin de exemplo
    └── exemplo2.py    # Outro plugin
```

## 📜 Log de Alterações  

- **v1.0.0** (2023-11-20)  
  - Versão inicial  
  - Sistema básico de carregamento de plugins  
  - Interface gráfica funcional  

## 🤝 Como Contribuir  

1. Faça um fork do projeto  
2. Crie sua branch (`git checkout -b feature/novafeature`)  
3. Commit suas mudanças (`git commit -m 'Add new feature'`)  
4. Push para a branch (`git push origin feature/novafeature`)  
5. Abra um Pull Request  
