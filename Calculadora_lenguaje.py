import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
import re
import itertools

# --- LÓGICA DEL BACKEND ---

class LanguageProcessor:
    def __init__(self):
        self.alphabet = set()
        self.languages = {}
        # Límite de longitud para generar el Universo en el complemento
        self.universe_limit = 4 

    def set_alphabet(self, alphabet_str):
        clean_str = alphabet_str.replace(" ", "")
        if not clean_str:
            self.alphabet = set()
        else:
            self.alphabet = set(clean_str.split(','))

    def validate_string(self, s):
        if not self.alphabet: return True 
        if s == "": return True
        for char in s:
            if char not in self.alphabet: return False
        return True

    def add_language(self, lang_name, lang_str):
        clean_str = lang_str.replace(" ", "")
        new_set = set()
        if clean_str:
            if clean_str == "ε" or clean_str == "lambda":
                new_set = {""} 
            else:
                parts = clean_str.split(',')
                for part in parts:
                    if not self.validate_string(part):
                        bad_char = next((c for c in part if c not in self.alphabet), "?")
                        raise ValueError(f"Error en {lang_name}: El carácter '{bad_char}' no pertenece al Alfabeto.")
                    new_set.add(part)
        self.languages[lang_name] = new_set

    # --- OPERACIONES ---

    def concatenate(self, L1, L2):
        result = set()
        if not L1 or not L2: return set()
        for s1 in L1:
            for s2 in L2:
                result.add(s1 + s2)
        return result

    def generate_universe(self):
        """Genera Sigma* hasta cierta longitud para calcular el complemento finito."""
        universe = {""} # Incluye epsilon
        if not self.alphabet:
            return universe
        
        # Generar combinaciones desde longitud 1 hasta el límite
        chars = list(self.alphabet)
        for i in range(1, self.universe_limit + 1):
            for item in itertools.product(chars, repeat=i):
                universe.add("".join(item))
        return universe

    def complement(self, L1):
        """Calcula el complemento relativo al universo acotado (Sigma* - L)."""
        universe = self.generate_universe()
        return universe - L1
    
    # --- PARSER ---

    def _tokenize(self, expr):
        # Agregamos el símbolo ᶜ al regex
        pattern = r'(L\d+|[U∩\-Δ•()ᶜ]|\s+)'
        tokens = [t for t in re.split(pattern, expr) if t and not t.isspace()]
        return tokens

    def evaluate_expression(self, expression):
        if not expression: return set()
        tokens = self._tokenize(expression)
        output_queue = []
        operator_stack = []
        
        # Precedencia: El complemento (ᶜ) es unario y tiene la prioridad más alta (4)
        precedence = {'ᶜ': 4, '•': 3, '∩': 2, 'U': 1, '-': 1, 'Δ': 1, '(': 0}

        for token in tokens:
            if re.match(r'L\d+', token): 
                if token not in self.languages:
                     raise ValueError(f"El lenguaje {token} no existe.")
                output_queue.append(self.languages[token])
            
            elif token in precedence: 
                # Lógica especial para operadores unarios (postfijos como ᶜ) no necesitan sacar nada del stack aún
                # Pero en Shunting-yard estándar se tratan normal en precedencia
                while (operator_stack and operator_stack[-1] != '(' and
                       precedence[operator_stack[-1]] >= precedence[token]):
                    # Importante: El ᶜ es asociativo por derecha o izquierda da igual, pero tiene alta prioridad
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

        # --- EVALUACIÓN RPN ---
        eval_stack = []
        for token in output_queue:
            if isinstance(token, set):
                eval_stack.append(token)
            else: 
                # Es un operador
                if token == 'ᶜ':
                    # OPERADOR UNARIO: Solo saca 1 elemento
                    if len(eval_stack) < 1: raise ValueError("Error de sintaxis en complemento.")
                    val1 = eval_stack.pop()
                    eval_stack.append(self.complement(val1))
                else:
                    # OPERADORES BINARIOS: Sacan 2 elementos
                    if len(eval_stack) < 2: raise ValueError("Error de sintaxis.")
                    val2 = eval_stack.pop()
                    val1 = eval_stack.pop()

                    if token == 'U': eval_stack.append(val1 | val2)
                    elif token == '∩': eval_stack.append(val1 & val2)
                    elif token == '-': eval_stack.append(val1 - val2)
                    elif token == 'Δ': eval_stack.append(val1 ^ val2)
                    elif token == '•': eval_stack.append(self.concatenate(val1, val2))

        if len(eval_stack) != 1: raise ValueError("Error al evaluar.")
        return eval_stack[0]


# --- INTERFAZ GRÁFICA ---

class AutoLangsApp(ttk.Window):
    def __init__(self):
        super().__init__(themename="cosmo") 
        self.title("Calculadora de Lenguajes")
        self.geometry("1000x850")
        
        self.processor = LanguageProcessor()
        self.lang_entries = {} 
        self.is_dark_mode = tk.BooleanVar(value=False)
        self.setup_ui()

    def setup_ui(self):
        # Header
        header = ttk.Frame(self, padding=(20, 10))
        header.pack(fill=X)
        ttk.Label(header, text="Calculadora de Autómatas", font=("Helvetica", 16, "bold")).pack(side=LEFT)
        ttk.Checkbutton(header, text="Modo Oscuro", variable=self.is_dark_mode, command=self.toggle_theme, bootstyle="round-toggle").pack(side=RIGHT)

        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=BOTH, expand=YES)

        # 1. Alfabeto
        f1 = ttk.Labelframe(main_frame, text="1. Alfabeto (Σ)", padding=10)
        f1.pack(fill=X, pady=5)
        ttk.Label(f1, text="Símbolos (ej: a, b). Nota: El complemento se calcula hasta longitud 4.").pack(anchor=W)
        self.alphabet_entry = ttk.Entry(f1)
        self.alphabet_entry.pack(fill=X, pady=5)

        # 2. Lenguajes
        f2 = ttk.Labelframe(main_frame, text="2. Lenguajes (L)", padding=10)
        f2.pack(fill=BOTH, expand=YES, pady=10)
        
        self.langs_container = ScrolledFrame(f2, padding=5, height=200)
        self.langs_container.pack(fill=BOTH, expand=YES)

        ttk.Button(f2, text="+ Agregar Lenguaje", command=self.add_language_row, bootstyle="SUCCESS").pack(anchor=E, pady=5)

        # 3. Operaciones
        f3 = ttk.Labelframe(main_frame, text="3. Operaciones", padding=10)
        f3.pack(fill=X, pady=10)

        self.expr_entry = ttk.Entry(f3, font=("Consolas", 14), state="readonly")
        self.expr_entry.pack(fill=X, pady=(0, 10))

        btns_container = ttk.Frame(f3)
        btns_container.pack(fill=X)

        self.lang_btns_frame = ttk.Labelframe(btns_container, text="Lenguajes", padding=5)
        self.lang_btns_frame.pack(side=LEFT, fill=BOTH, expand=YES, padx=(0, 10))
        
        ops_btns_frame = ttk.Frame(btns_container)
        ops_btns_frame.pack(side=RIGHT)

        ctrl_frame = ttk.Frame(ops_btns_frame)
        ctrl_frame.pack(fill=X, pady=(0, 5))
        
        ttk.Button(ctrl_frame, text="C (Limpiar)", command=self.clear_expression, bootstyle="DANGER", width=10).pack(side=LEFT, padx=2)
        ttk.Button(ctrl_frame, text="⌫", command=self.backspace_expression, bootstyle="WARNING", width=5).pack(side=LEFT, padx=2)
        ttk.Button(ctrl_frame, text="CALCULAR (=)", command=self.calculate, bootstyle="PRIMARY", width=15).pack(side=LEFT, padx=2)

        sym_frame = ttk.Frame(ops_btns_frame)
        sym_frame.pack(fill=X)
        
        # Agregamos el Complemento a la lista de botones
        operators = [
            ("U (Unión)", " U "), ("∩ (Inter)", " ∩ "), 
            ("- (Dif)", " - "), ("Δ (Sim)", " Δ "), 
            ("• (Concat)", " • "), ("(..)", "("), ( "..)", ")"),
            ("Complemento (Lᶜ)", "ᶜ") 
        ]
        
        r, c = 0, 0
        for txt, val in operators:
            # El botón de complemento lo insertamos pegado, sin espacios extra a la izquierda necesariamente
            # pero para uniformidad lo trataremos como string
            action = lambda v=val: self.insert_symbol(v)
            
            b = ttk.Button(sym_frame, text=txt, command=action, bootstyle="secondary-outline", width=14)
            b.grid(row=r, column=c, padx=2, pady=2)
            c += 1
            if c > 3: 
                c = 0
                r += 1

        # 4. Resultado
        f4 = ttk.Labelframe(main_frame, text="4. Resultado", padding=10)
        f4.pack(fill=X)
        self.result_text = ttk.Text(f4, height=3, font=("Consolas", 11), state="disabled")
        self.result_text.pack(fill=X)

        self.add_language_row()
        self.add_language_row()

    def toggle_theme(self):
        style = "cyborg" if self.is_dark_mode.get() else "cosmo"
        self.style.theme_use(style)

    def refresh_lang_buttons(self):
        for widget in self.lang_btns_frame.winfo_children():
            widget.destroy()
        keys = list(self.lang_entries.keys())
        keys.sort(key=lambda x: int(x[1:]))
        for key in keys:
            btn = ttk.Button(self.lang_btns_frame, text=key, command=lambda k=key: self.insert_symbol(k), bootstyle="info")
            btn.pack(side=LEFT, padx=5, pady=5)

    def add_language_row(self):
        i = 1
        while f"L{i}" in self.lang_entries: i += 1
        l_name = f"L{i}"
        
        row = ttk.Frame(self.langs_container)
        row.pack(fill=X, pady=5)
        
        ttk.Label(row, text=f"{l_name} =", width=4, font="bold").pack(side=LEFT)
        e = ttk.Entry(row)
        e.pack(side=LEFT, fill=X, expand=YES, padx=5)
        ttk.Button(row, text="✕", bootstyle="DANGER-link", command=lambda n=l_name, f=row: self.remove_language_row(n, f)).pack(side=RIGHT)

        self.lang_entries[l_name] = e
        self.refresh_lang_buttons()

    def remove_language_row(self, l_name, row_frame):
        row_frame.destroy()
        if l_name in self.lang_entries: del self.lang_entries[l_name]
        self.refresh_lang_buttons()

    def insert_symbol(self, symbol):
        self.expr_entry.configure(state="normal")
        # Si es complemento, no ponemos espacios alrededor para que quede pegado a la letra (Ej: L1ᶜ)
        if symbol == "ᶜ":
             self.expr_entry.insert(tk.END, f"{symbol}")
        else:
             self.expr_entry.insert(tk.END, f"{symbol}")
        self.expr_entry.configure(state="readonly")

    def clear_expression(self):
        self.expr_entry.configure(state="normal")
        self.expr_entry.delete(0, tk.END)
        self.expr_entry.configure(state="readonly")

    def backspace_expression(self):
        current_text = self.expr_entry.get()
        if len(current_text) > 0:
            new_text = current_text[:-1]
            if current_text.endswith(" ") and len(new_text) > 0: new_text = new_text[:-1]
            self.expr_entry.configure(state="normal")
            self.expr_entry.delete(0, tk.END)
            self.expr_entry.insert(0, new_text)
            self.expr_entry.configure(state="readonly")

    def calculate(self):
        self.processor.set_alphabet(self.alphabet_entry.get())
        self.processor.languages = {} 
        try:
            for l_name, entry in self.lang_entries.items():
                self.processor.add_language(l_name, entry.get())
            
            expression = self.expr_entry.get()
            result = self.processor.evaluate_expression(expression)
            
            if not result:
                res_str = "∅"
            else:
                # Limitamos la visualización si hay demasiados elementos para que no se congele la UI
                res_list = sorted(list(result), key=len)
                if len(res_list) > 200:
                     res_str = "{ " + ", ".join(res_list[:200]) + " ... (truncado) }"
                else:
                     res_str = "{ " + ", ".join(res_list) + " }"

            self.result_text.configure(state="normal")
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert("1.0", res_str)
            self.result_text.configure(state="disabled")

        except ValueError as e: messagebox.showerror("Error", str(e))
        except Exception as e: messagebox.showerror("Error", f"Fallo crítico: {e}")

if __name__ == '__main__':
    app = AutoLangsApp()
    app.mainloop()