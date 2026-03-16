import tkinter as tk
from PIL import Image, ImageTk
import requests
import io
import random

class Generator:
    def __init__(self, root):
        self.root = root
        self.root.title("Генератор изображений")
        self.root.geometry("500x620")
        self.root.resizable(False, False)
        
        self.image_frame = tk.Frame(root, bg="#f0f0f0", width=450, height=450)
        self.image_frame.pack(pady=10)
        self.image_frame.pack_propagate(False) 
        
        self.image_label = tk.Label(self.image_frame)
        self.image_label.pack(expand=True)

        self.button = tk.Button(
            root,
            text="Следующее изображение", 
            command=self.load,
            font=("Arial", 11),
            bg="#4CAF50",
            fg="white"
        )
        self.button.pack(pady=15)

        self.status = tk.Label(root)
        self.status.pack(pady=5)
        self.load()
    
    def load(self):
        self.status.config(text="Загрузка...")
        self.button.config(state="disabled")
        self.root.update() 
        url = f"https://cataas.com/cat?random={random.randint(1, 999999)}"
        
        try:
            response = requests.get(url, timeout=15)
        
            image = Image.open(io.BytesIO(response.content))
            image.thumbnail((450, 450), Image.Resampling.LANCZOS)
            
           
            photo = ImageTk.PhotoImage(image)
            self.image_label.config(image=photo)
            self.image_label.image = photo  
            self.status.config(text="Загружено")
            

        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP ошибка: {http_err}")
        except requests.exceptions.ConnectionError as conn_err:
            print(f"Ошибка соединения: {conn_err}")
        except requests.exceptions.Timeout as timeout_err:
            print(f"Время ожидания истекло: {timeout_err}")
        except Exception as e:
            self.status.config(text=f"Ошибка обработки изображения")
            print(f"Debug: {e}")
        finally:
            self.button.config(state="normal")


if __name__ == "__main__":
    root = tk.Tk()
    app = Generator(root)
    root.mainloop()