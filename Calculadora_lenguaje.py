import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
# Mantenemos la corrección del error anterior
from ttkbootstrap.scrolled import ScrolledFrame
import re

# --- LÓGICA DEL BACKEND (Igual que antes) ---

class LanguageProcessor:
    def __init__(self):
        self.alphabet = set()
        self.languages = {}

    def set_alphabet(self, alphabet_str):
        clean_str = alphabet_str.replace(" ", "")
        if not clean_str:
            self.alphabet = set()
        else:
            self.alphabet = set(clean_str.split(','))

    def add_language(self, lang_name, lang_str):
        clean_str = lang_str.replace(" ", "")
        if not clean_str:
             new_set = set()
        elif clean_str == "ε" or clean_str == "lambda":
             new_set = {""} 
        else:
            new_set = set(clean_str.split(','))
        self.languages[lang_name] = new_set

    def concatenate(self, L1, L2):
        result = set()
        if not L1 or not L2:
            return set()
        for s1 in L1:
            for s2 in L2:
                result.add(s1 + s2)
        return result
    
    def _tokenize(self, expr):
        pattern = r'(L\d+|[U∩\-Δ•()]|\s+)'
        tokens = [t for t in re.split(pattern, expr) if t and not t.isspace()]
        return tokens

    def evaluate_expression(self, expression):
        if not expression:
            return set()

        tokens = self._tokenize(expression)
        output_queue = []
        operator_stack = []

        precedence = {'•': 3, '∩': 2, 'U': 1, '-': 1, 'Δ': 1, '(': 0}

        for token in tokens:
            if re.match(r'L\d+', token): 
                if token not in self.languages:
                     raise ValueError(f"El lenguaje {token} no ha sido definido.")
                output_queue.append(self.languages[token])
            elif token in precedence: 
                while (operator_stack and operator_stack[-1] != '(' and
                       precedence[operator_stack[-1]] >= precedence[token]):
                    output_queue.append(operator_stack.pop())
                operator_stack.append(token)
            elif token == '(':
                operator_stack.append(token)
            elif token == ')':
                while operator_stack and operator_stack[-1] != '(':
                    output_queue.append(operator_stack.pop())
                operator_stack.pop() 

        while operator_stack:
            output_queue.append(operator_stack.pop())

        eval_stack = []
        for token in output_queue:
            if isinstance(token, set):
                eval_stack.append(token)
            else: 
                if len(eval_stack) < 2:
                     raise ValueError("Error de sintaxis.")
                val2 = eval_stack.pop()
                val1 = eval_stack.pop()

                if token == 'U': eval_stack.append(val1 | val2)
                elif token == '∩': eval_stack.append(val1 & val2)
                elif token == '-': eval_stack.append(val1 - val2)
                elif token == 'Δ': eval_stack.append(val1 ^ val2)
                elif token == '•': eval_stack.append(self.concatenate(val1, val2))

        if len(eval_stack) != 1:
             raise ValueError("Error al evaluar.")
        return eval_stack[0]


# --- INTERFAZ GRÁFICA ---

class AutoLangsApp(ttk.Window):
    def __init__(self):
        # Iniciamos con el tema claro "cosmo" por defecto
        super().__init__(themename="cosmo") 
        self.title("Operaciones con lenguajes")
        self.geometry("900x750")
        
        self.processor = LanguageProcessor()
        self.lang_entries = {} 
        self.lang_counter = 1
        
        # Variable para controlar el estado del switch
        self.is_dark_mode = tk.BooleanVar(value=False)

        self.setup_ui()

    def setup_ui(self):
        # --- Cabecera con Switch de Modo Oscuro ---
        header_frame = ttk.Frame(self, padding=(20, 10, 20, 0))
        header_frame.pack(fill=X)

        title_lbl = ttk.Label(header_frame, text="Operaciones con lenguajes", font=("Helvetica", 16, "bold"))
        title_lbl.pack(side=LEFT)

        # Interruptor para cambio de tema
        self.theme_switch = ttk.Checkbutton(
            header_frame, 
            text="Modo Oscuro", 
            variable=self.is_dark_mode,
            command=self.toggle_theme,
            bootstyle="round-toggle" # Estilo de interruptor moderno
        )
        self.theme_switch.pack(side=RIGHT)

        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=BOTH, expand=YES)

        # --- 1. Alfabeto ---
        alphabet_frame = ttk.Labelframe(main_frame, text="1. Definir Alfabeto (Σ)", padding=10)
        alphabet_frame.pack(fill=X, pady=(0, 20))
        
        ttk.Label(alphabet_frame, text="Símbolos (ej: a, b, c):").pack(anchor=W)
        self.alphabet_entry = ttk.Entry(alphabet_frame)
        self.alphabet_entry.pack(fill=X, pady=(5,0))

        # --- 2. Lenguajes ---
        langs_frame = ttk.Labelframe(main_frame, text="2. Definir Lenguajes (L)", padding=10)
        langs_frame.pack(fill=BOTH, expand=YES, pady=(0, 20))

        self.langs_container = ScrolledFrame(langs_frame, padding=5)
        self.langs_container.pack(fill=BOTH, expand=YES)

        btn_add_lang = ttk.Button(langs_frame, text="+ Agregar Lenguaje", command=self.add_language_row, bootstyle="SUCCESS")
        btn_add_lang.pack(anchor=E, pady=(10,0))

        self.add_language_row()
        self.add_language_row() 

        # --- 3. Operaciones ---
        ops_frame = ttk.Labelframe(main_frame, text="3. Operaciones", padding=10)
        ops_frame.pack(fill=X, pady=(0, 20))

        ttk.Label(ops_frame, text="Fórmula:").pack(anchor=W)
        
        input_frame = ttk.Frame(ops_frame)
        input_frame.pack(fill=X, pady=5)
        
        self.expr_entry = ttk.Entry(input_frame, font=("Helvetica", 12))
        self.expr_entry.pack(side=LEFT, fill=X, expand=YES, padx=(0, 10))
        
        btn_calc = ttk.Button(input_frame, text="Calcular", command=self.calculate, bootstyle="PRIMARY")
        btn_calc.pack(side=RIGHT)

        symbols_frame = ttk.Frame(ops_frame)
        symbols_frame.pack(fill=X, pady=(5,0))
        
        symbols = [("U", "U"), ("∩", "∩"), ("-", "-"), ("Δ", "Δ"), ("•", "•"), ("(", "("), (")", ")")]

        for text, sym in symbols:
            # bootstyle="outline" hace que los botones se vean bien en ambos modos
            btn = ttk.Button(symbols_frame, text=text, command=lambda s=sym: self.insert_symbol(s), bootstyle="secondary-outline")
            btn.pack(side=LEFT, padx=2)

        # --- 4. Resultados ---
        result_frame = ttk.Labelframe(main_frame, text="4. Resultado", padding=10)
        result_frame.pack(fill=X)
        
        self.result_text = ttk.Text(result_frame, height=4, font=("Consolas", 11), state="disabled")
        self.result_text.pack(fill=X)

    def toggle_theme(self):
        """Cambia entre modo claro y oscuro dinámicamente"""
        if self.is_dark_mode.get():
            self.style.theme_use("cyborg") # Tema oscuro estilo hacker
        else:
            self.style.theme_use("cosmo")  # Tema claro limpio

    def add_language_row(self):
        row_frame = ttk.Frame(self.langs_container)
        row_frame.pack(fill=X, pady=5)
        l_name = f"L{self.lang_counter}"
        lbl = ttk.Label(row_frame, text=f"{l_name} =", width=5, font=("Helvetica", 10, "bold"))
        lbl.pack(side=LEFT)
        entry = ttk.Entry(row_frame)
        entry.pack(side=LEFT, fill=X, expand=YES, padx=10)
        entry.insert(0, "") 
        self.lang_entries[l_name] = entry
        self.lang_counter += 1

    def insert_symbol(self, symbol):
        self.expr_entry.insert(tk.INSERT, f" {symbol} ")
        self.expr_entry.focus()

    def calculate(self):
        self.processor.set_alphabet(self.alphabet_entry.get())
        self.processor.languages = {} 
        for l_name, entry_widget in self.lang_entries.items():
            lang_content = entry_widget.get()
            self.processor.add_language(l_name, lang_content)

        expression = self.expr_entry.get()
        try:
            result_set = self.processor.evaluate_expression(expression)
            if not result_set:
                result_str = "∅"
            else:
                sorted_list = sorted(list(result_set), key=len)
                result_str = "{ " + ", ".join(sorted_list) + " }"

            self.result_text.configure(state="normal")
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert("1.0", result_str)
            self.result_text.configure(state="disabled")

        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
             messagebox.showerror("Error", f"Ocurrió un error: {e}")

if __name__ == '__main__':
    app = AutoLangsApp()
    app.mainloop()