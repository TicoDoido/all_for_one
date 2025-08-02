# All For One - Game Plugin Manager  

A Python GUI application for managing and executing game plugins in a modular way.  

## 📦 Core Features  

- ✅ Dynamic plugin loading  
- 🖥️ Intuitive graphical interface  
- 🔄 Plugin reloading without restart  
- 📝 Integrated logging system  
- 🛠️ Easy-to-expand modular architecture  

## ⚙️ Prerequisites  

- Python 3.7 or higher  

## 🚀 Getting Started  

1. Clone the repository:  
```bash  
git clone https://github.com/TicoDoido/all_for_one.git  
cd all-for-one  
```  

2. Run the application:  
```bash  
ALL_FOR_ONE.py  
```  

## 🧩 Creating Plugins  

1. Create a `.py` file in the `plugins/` folder  
2. Use this basic template:  

```python  
def register_plugin():  
    return {  
        "name": "Plugin Name",  
        "description": "Description of what your plugin does",  
        "commands": [  
            {  
                "label": "Button Text",  
                "action": lambda: print("Action executed!")  
            }  
            # Add more commands as needed  
        ]  
    }  
```  

3. Save the file and reload in the application  

## 🖼️ Project Structure  

```
all-for-one/  
│  
├── ALL_FOR_ONE.py     # Main code  
├── README.md          # This file  
└── plugins/           # Folder for your plugins  
    ├── example1.py    # Example plugin  
    └── example2.py    # Another plugin  
```  

## 📜 Changelog  

- **v1.0.0** (2023-11-20)  
  - Initial version  
  - Basic plugin loading system  
  - Functional graphical interface  

## 🤝 How to Contribute  

1. Fork the project  
2. Create your branch (`git checkout -b feature/newfeature`)  
3. Commit your changes (`git commit -m 'Add new feature'`)  
4. Push to the branch (`git push origin feature/newfeature`)  
5. Open a Pull Request
