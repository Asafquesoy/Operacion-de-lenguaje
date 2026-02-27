import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
import re

# --- LÓGICA DEL BACKEND ---

class LanguageProcessor:
    def __init__(self):
        self.alphabet = set()
        self.languages = {}
        self.closure_limit = 3 # Límite por defecto para cerraduras

    def set_alphabet(self, alphabet_str):
        if not alphabet_str.strip():
            self.alphabet = set()
        else:
            self.alphabet = set(alphabet_str.split())

    def validate_string(self, s):
        if not self.alphabet: return True 
        if s == "": return True
        escaped_alpha = [re.escape(sym) for sym in sorted(list(self.alphabet), key=len, reverse=True)]
        pattern = re.compile(f"^({'|'.join(escaped_alpha)})+$")
        return bool(pattern.match(s))

    def add_language(self, lang_name, lang_str):
        new_set = set()
        if lang_str.strip():
            if lang_str.strip() in ["ε", "lambda"]:
                new_set = {""} 
            else:
                parts = lang_str.split()
                for part in parts:
                    if not self.validate_string(part):
                        raise ValueError(f"Error en {lang_name}: La cadena '{part}' no se puede formar con los símbolos del Alfabeto.")
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

    def complement(self, L1):
        if not self.alphabet: return set() 
        result = set()
        sorted_alpha = sorted(list(self.alphabet))
        escaped_alpha = [re.escape(sym) for sym in sorted(list(self.alphabet), key=len, reverse=True)]
        pattern = re.compile(f"({'|'.join(escaped_alpha)})")
        
        for string in L1:
            symbols_in_string = set(pattern.findall(string))
            for sym in sorted_alpha:
                if sym not in symbols_in_string:
                    result.add(sym)
        return result

    def kleene_star(self, L1):
        """Cerradura de Kleene L* (Incluye L^0 que es la cadena vacía epsilon)"""
        result = {""} # L^0 = {epsilon}
        current_power = {""}
        
        for _ in range(self.closure_limit):
            current_power = self.concatenate(current_power, L1)
            result.update(current_power)
        return result

    def positive_closure(self, L1):
        """Cerradura Positiva L+ (No incluye L^0 por defecto)"""
        if self.closure_limit < 1:
            return set()
            
        result = set(L1) # Empieza en L^1
        current_power = set(L1)
        
        for _ in range(self.closure_limit - 1):
            current_power = self.concatenate(current_power, L1)
            result.update(current_power)
        return result
    
    # --- PARSER ---

    def _tokenize(self, expr):
        # Agregamos los símbolos * y + a la lista de tokens permitidos
        pattern = r'(L\d+|[U∩\-Δ•()ᶜ*+]|\s+)'
        tokens = [t for t in re.split(pattern, expr) if t and not t.isspace()]
        return tokens

    def evaluate_expression(self, expression):
        if not expression: return set()
        tokens = self._tokenize(expression)
        output_queue = []
        operator_stack = []
        
        # Precedencia: Complemento, Kleene y Positiva tienen la mayor prioridad (Unarios)
        precedence = {'ᶜ': 4, '*': 4, '+': 4, '•': 3, '∩': 2, 'U': 1, '-': 1, 'Δ': 1, '(': 0}

        for token in tokens:
            if re.match(r'L\d+', token): 
                if token not in self.languages:
                     raise ValueError(f"El lenguaje {token} no existe.")
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
                
                if not operator_stack:
                    raise ValueError("Error de sintaxis: Hay paréntesis ')' de más.")
                operator_stack.pop() 

        while operator_stack:
            op = operator_stack.pop()
            if op == '(':
                 raise ValueError("Error de sintaxis: Falta cerrar paréntesis '('.")
            output_queue.append(op)

        eval_stack = []
        for token in output_queue:
            if isinstance(token, set):
                eval_stack.append(token)
            else: 
                # Operadores Unarios (sacan 1 operando)
                if token in ['ᶜ', '*', '+']:
                    if len(eval_stack) < 1: raise ValueError(f"Error en operación '{token}': falta operando.")
                    val1 = eval_stack.pop()
                    if token == 'ᶜ': eval_stack.append(self.complement(val1))
                    elif token == '*': eval_stack.append(self.kleene_star(val1))
                    elif token == '+': eval_stack.append(self.positive_closure(val1))
                
                # Operadores Binarios (sacan 2 operandos)
                else:
                    if len(eval_stack) < 2: 
                        raise ValueError(f"Error en operación '{token}': faltan operandos.")
                    val2 = eval_stack.pop()
                    val1 = eval_stack.pop()
                    
                    if token == 'U': eval_stack.append(val1 | val2)
                    elif token == '∩': eval_stack.append(val1 & val2)
                    elif token == '-': eval_stack.append(val1 - val2)
                    elif token == 'Δ': eval_stack.append(val1 ^ val2)
                    elif token == '•': eval_stack.append(self.concatenate(val1, val2))

        if len(eval_stack) != 1: 
            raise ValueError("Error: Fórmula incompleta. ¿Olvidaste un operador (ej: •)?")
            
        return eval_stack[0]


# --- INTERFAZ GRÁFICA ---

class AutoLangsApp(ttk.Window):
    def __init__(self):
        super().__init__(themename="cosmo") 
        self.title("Calculadora de Lenguajes")
        self.geometry("1100x900") # Un poco más alto para los nuevos botones
        
        self.processor = LanguageProcessor()
        self.lang_entries = {} 
        self.is_dark_mode = tk.BooleanVar(value=False)
        self.setup_ui()

    def setup_ui(self):
        header = ttk.Frame(self, padding=(20, 10))
        header.pack(fill=X)
        ttk.Label(header, text="Calculadora de Autómatas", font=("Helvetica", 16, "bold")).pack(side=LEFT)
        ttk.Checkbutton(header, text="Modo Oscuro", variable=self.is_dark_mode, command=self.toggle_theme, bootstyle="round-toggle").pack(side=RIGHT)

        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=BOTH, expand=YES)

        # 1. Alfabeto
        f1 = ttk.Labelframe(main_frame, text="1. Alfabeto (Σ)", padding=10)
        f1.pack(fill=X, pady=5)
        ttk.Label(f1, text="Símbolos separados por ESPACIO. (Ejemplo: a b ( ) 10 1)").pack(anchor=W)
        self.alphabet_entry = ttk.Entry(f1)
        self.alphabet_entry.pack(fill=X, pady=5)

        # 2. Lenguajes
        f2 = ttk.Labelframe(main_frame, text="2. Definición de Lenguajes (L)", padding=10)
        f2.pack(fill=BOTH, expand=YES, pady=10)
        
        self.langs_container = ScrolledFrame(f2, padding=5, height=200)
        self.langs_container.pack(fill=BOTH, expand=YES)
        
        ttk.Label(f2, text="Nota: Separe los elementos con ESPACIOS.", font=("Arial", 9, "bold")).pack(anchor=E)
        ttk.Button(f2, text="+ Agregar Lenguaje", command=self.add_language_row, bootstyle="SUCCESS").pack(anchor=E, pady=5)

        # 3. Operaciones
        f3 = ttk.Labelframe(main_frame, text="3. Operaciones", padding=10)
        f3.pack(fill=X, pady=10)

        # --- NUEVO: Cuadro para el límite de cerradura ---
        limit_frame = ttk.Frame(f3)
        limit_frame.pack(fill=X, pady=(0, 10))
        ttk.Label(limit_frame, text="Límite máximo (n) para cerraduras (*, +):", font=("Arial", 10, "bold")).pack(side=LEFT)
        self.limit_entry = ttk.Entry(limit_frame, width=5)
        self.limit_entry.pack(side=LEFT, padx=10)
        self.limit_entry.insert(0, "3") # Valor por defecto

        self.expr_entry = ttk.Entry(f3, font=("Consolas", 14))
        self.expr_entry.pack(fill=X, pady=(0, 10))

        btns_container = ttk.Frame(f3)
        btns_container.pack(fill=X)

        self.lang_btns_wrapper = ttk.Labelframe(btns_container, text="Lenguajes Disponibles", padding=5, width=350)
        self.lang_btns_wrapper.pack_propagate(False) 
        self.lang_btns_wrapper.pack(side=LEFT, fill=BOTH, padx=(0, 10))

        self.lang_btns_scroll = ScrolledFrame(self.lang_btns_wrapper, height=180) # Un poco más alto
        self.lang_btns_scroll.pack(fill=BOTH, expand=YES)
        
        ops_btns_frame = ttk.Frame(btns_container)
        ops_btns_frame.pack(side=RIGHT, fill=BOTH, expand=YES)

        ctrl_frame = ttk.Frame(ops_btns_frame)
        ctrl_frame.pack(fill=X, pady=(0, 5))
        
        ttk.Button(ctrl_frame, text="Limpiar Fórmula", command=self.clear_formula, bootstyle="DANGER", width=15).pack(side=LEFT, padx=2)
        ttk.Button(ctrl_frame, text="⌫", command=self.backspace_expression, bootstyle="WARNING", width=5).pack(side=LEFT, padx=2)
        ttk.Button(ctrl_frame, text="CALCULAR (=)", command=self.calculate, bootstyle="PRIMARY", width=15).pack(side=LEFT, padx=2)

        sym_frame = ttk.Frame(ops_btns_frame)
        sym_frame.pack(fill=X)
        
        # --- NUEVO: Agregamos Kleene y Positiva ---
        operators = [
            ("U (Unión)", "U"), ("∩ (Inter)", "∩"), 
            ("- (Dif)", "-"), ("Δ (Sim)", "Δ"), 
            ("• (Concat)", "•"), ("(", "("), ( ")", ")"),
            ("Complemento (Lᶜ)", "ᶜ"),
            ("Kleene (L*)", "*"), ("Positiva (L+)", "+")
        ]
        
        r, c = 0, 0
        for txt, val in operators:
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
        self.result_text = ttk.Text(f4, height=4, font=("Consolas", 11), state="disabled")
        self.result_text.pack(fill=X)

        self.add_language_row()
        self.add_language_row()

    def toggle_theme(self):
        style = "cyborg" if self.is_dark_mode.get() else "cosmo"
        self.style.theme_use(style)

    def refresh_lang_buttons(self):
        for widget in self.lang_btns_scroll.winfo_children():
            widget.destroy()
        keys = list(self.lang_entries.keys())
        keys.sort(key=lambda x: int(x[1:]))
        r, c = 0, 0
        for key in keys:
            btn = ttk.Button(self.lang_btns_scroll, text=key, command=lambda k=key: self.insert_symbol(k), bootstyle="info", width=5)
            btn.grid(row=r, column=c, padx=3, pady=3)
            c += 1
            if c >= 4:
                c = 0
                r += 1

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
        self.expr_entry.insert(tk.INSERT, f"{symbol}")
        self.expr_entry.focus() 

    def clear_formula(self):
        self.expr_entry.delete(0, tk.END)

    def backspace_expression(self):
        try:
            idx = self.expr_entry.index(tk.INSERT)
            if idx > 0:
                self.expr_entry.delete(idx-1, idx)
        except Exception:
            pass

    def calculate(self):
        # 1. Recuperar el límite de las cerraduras con protección
        try:
            limit_val = int(self.limit_entry.get())
            if limit_val < 0: raise ValueError
            
            # Protección contra congelamiento: limitamos a 6 como máximo internamente
            if limit_val > 6:
                messagebox.showwarning("Límite ajustado", "Para evitar que tu computadora se congele calculando infinitos, el límite máximo permitido es 6.\nSe calculará usando n=6.")
                limit_val = 6
                self.limit_entry.delete(0, tk.END)
                self.limit_entry.insert(0, "6")
                
            self.processor.closure_limit = limit_val
        except ValueError:
            messagebox.showwarning("Aviso", "El límite de cerradura debe ser un número entero positivo. Se usará 3 por defecto.")
            self.limit_entry.delete(0, tk.END)
            self.limit_entry.insert(0, "3")
            self.processor.closure_limit = 3

        # 2. Continúa normal
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
                # Ordenamos primero por longitud, luego alfabéticamente
                res_list = sorted(list(result), key=lambda x: (len(x), x))
                # Reemplazamos las cadenas vacías ("") por el símbolo Epsilon para que se vea bien
                res_list = ["ε" if s == "" else s for s in res_list]
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