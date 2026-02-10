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

    def set_alphabet(self, alphabet_str):
        # Separa por espacios cualquier símbolo
        if not alphabet_str.strip():
            self.alphabet = set()
        else:
            self.alphabet = set(alphabet_str.split())

    def validate_string(self, s):
        """Valida si una cadena está compuesta por símbolos del alfabeto."""
        if not self.alphabet: return True 
        if s == "": return True
        
        # Estrategia: Verificar caracter por caracter es lo más seguro para alfabetos simples
        for char in s:
            if char not in self.alphabet:
                return False
        return True

    def add_language(self, lang_name, lang_str):
        new_set = set()
        if lang_str.strip():
            if lang_str.strip() in ["ε", "lambda"]:
                new_set = {""} 
            else:
                # Separamos por espacios
                parts = lang_str.split()
                for part in parts:
                    if not self.validate_string(part):
                        # Buscamos qué caracter falló para avisar al usuario
                        bad_char = next((c for c in part if c not in self.alphabet), "?")
                        raise ValueError(f"Error en {lang_name}: El carácter '{bad_char}' no está en el Alfabeto.\n(Recuerda definir el alfabeto primero: ej: ( ) a b)")
                    new_set.add(part)
        self.languages[lang_name] = new_set

    # --- OPERACIONES DE CONJUNTOS ---

    def concatenate(self, L1, L2):
        result = set()
        if not L1 or not L2: return set()
        for s1 in L1:
            for s2 in L2:
                result.add(s1 + s2)
        return result

    def complement(self, L1):
        """Complemento relativo: Qué caracteres del alfabeto le faltan a cada cadena."""
        if not self.alphabet: return set() 
        result = set()
        # Ordenamos para consistencia visual
        sorted_alpha = sorted(list(self.alphabet))
        
        for string in L1:
            chars_in_string = set(string)
            for char in sorted_alpha:
                # Si el caracter del alfabeto NO está en la cadena, se agrega
                if char not in chars_in_string:
                    result.add(char)
        return result
    
    # --- PARSER BLINDADO (Analizador de Fórmulas) ---

    def _tokenize(self, expr):
        # Este regex solo busca operadores y nombres de variables (L1, L2...).
        # NO mira el contenido de los lenguajes, por lo que es seguro usar '(' en el alfabeto.
        pattern = r'(L\d+|[U∩\-Δ•()ᶜ]|\s+)'
        tokens = [t for t in re.split(pattern, expr) if t and not t.isspace()]
        return tokens

    def evaluate_expression(self, expression):
        if not expression: return set()
        
        tokens = self._tokenize(expression)
        output_queue = []
        operator_stack = []
        
        # Precedencia de operadores
        precedence = {'ᶜ': 4, '•': 3, '∩': 2, 'U': 1, '-': 1, 'Δ': 1, '(': 0}

        for token in tokens:
            if re.match(r'L\d+', token): 
                # Es un lenguaje (L1, L2...)
                if token not in self.languages:
                     raise ValueError(f"El lenguaje {token} no existe.")
                # Aquí obtenemos el conjunto real. Puede contener '(', ')', lo que sea.
                # Como ya es un objeto 'set', no interfiere con el análisis de texto.
                output_queue.append(self.languages[token])
            
            elif token in precedence: 
                # Es un operador o paréntesis DE LA FÓRMULA
                while (operator_stack and operator_stack[-1] != '(' and
                       precedence[operator_stack[-1]] >= precedence[token]):
                    output_queue.append(operator_stack.pop())
                operator_stack.append(token)
            
            elif token == '(':
                operator_stack.append(token)
            
            elif token == ')':
                # Sacar todo hasta encontrar el paréntesis de apertura
                while operator_stack and operator_stack[-1] != '(':
                    output_queue.append(operator_stack.pop())
                
                # Validación crítica de paréntesis desbalanceados
                if not operator_stack:
                    raise ValueError("Error de sintaxis: Hay paréntesis ')' de más en la fórmula.")
                
                operator_stack.pop() # Eliminar el '(' del stack

        # Vaciamos el resto de la pila
        while operator_stack:
            op = operator_stack.pop()
            if op == '(':
                 raise ValueError("Error de sintaxis: Falta cerrar paréntesis '('.")
            output_queue.append(op)

        # --- EVALUACIÓN (Notación Polaca Inversa) ---
        eval_stack = []
        for token in output_queue:
            if isinstance(token, set):
                eval_stack.append(token)
            else: 
                # Es un operador, sacamos operandos del stack
                if token == 'ᶜ': # Unario
                    if len(eval_stack) < 1: raise ValueError("Error en Complemento: falta operando.")
                    val1 = eval_stack.pop()
                    eval_stack.append(self.complement(val1))
                else: # Binario
                    if len(eval_stack) < 2: 
                        raise ValueError(f"Error en operación: faltan operandos para '{token}'.")
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
        self.geometry("1100x850") 
        
        self.processor = LanguageProcessor()
        self.lang_entries = {} 
        self.is_dark_mode = tk.BooleanVar(value=False)
        self.setup_ui()

    def setup_ui(self):
        # Cabecera
        header = ttk.Frame(self, padding=(20, 10))
        header.pack(fill=X)
        ttk.Label(header, text="Calculadora de Autómatas", font=("Helvetica", 16, "bold")).pack(side=LEFT)
        ttk.Checkbutton(header, text="Modo Oscuro", variable=self.is_dark_mode, command=self.toggle_theme, bootstyle="round-toggle").pack(side=RIGHT)

        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=BOTH, expand=YES)

        # 1. Alfabeto
        f1 = ttk.Labelframe(main_frame, text="1. Alfabeto (Σ)", padding=10)
        f1.pack(fill=X, pady=5)
        # Instrucción clara sobre espacios
        ttk.Label(f1, text="Símbolos separados por ESPACIO. (Ejemplo: a b ( ) 1 0)").pack(anchor=W)
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

        # Pantalla de fórmula (Solo lectura)
        self.expr_entry = ttk.Entry(f3, font=("Consolas", 14), state="readonly")
        self.expr_entry.pack(fill=X, pady=(0, 10))

        btns_container = ttk.Frame(f3)
        btns_container.pack(fill=X)

        # Panel Izquierdo con SCROLL (Botones L)
        self.lang_btns_wrapper = ttk.Labelframe(btns_container, text="Lenguajes Disponibles", padding=5, width=350)
        self.lang_btns_wrapper.pack_propagate(False) 
        self.lang_btns_wrapper.pack(side=LEFT, fill=BOTH, padx=(0, 10))

        self.lang_btns_scroll = ScrolledFrame(self.lang_btns_wrapper, height=150)
        self.lang_btns_scroll.pack(fill=BOTH, expand=YES)
        
        # Panel Derecho (Botones Operadores)
        ops_btns_frame = ttk.Frame(btns_container)
        ops_btns_frame.pack(side=RIGHT, fill=BOTH, expand=YES)

        ctrl_frame = ttk.Frame(ops_btns_frame)
        ctrl_frame.pack(fill=X, pady=(0, 5))
        
        ttk.Button(ctrl_frame, text="Limpiar Fórmula", command=self.clear_formula, bootstyle="DANGER", width=15).pack(side=LEFT, padx=2)
        ttk.Button(ctrl_frame, text="⌫", command=self.backspace_expression, bootstyle="WARNING", width=5).pack(side=LEFT, padx=2)
        ttk.Button(ctrl_frame, text="CALCULAR (=)", command=self.calculate, bootstyle="PRIMARY", width=15).pack(side=LEFT, padx=2)

        sym_frame = ttk.Frame(ops_btns_frame)
        sym_frame.pack(fill=X)
        
        operators = [
            ("U (Unión)", " U "), ("∩ (Inter)", " ∩ "), 
            ("- (Dif)", " - "), ("Δ (Sim)", " Δ "), 
            ("• (Concat)", " • "), ("(..)", "("), ( "..)", ")"),
            ("Complemento (Lᶜ)", "ᶜ") 
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
        self.result_text = ttk.Text(f4, height=3, font=("Consolas", 11), state="disabled")
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
        self.expr_entry.configure(state="normal")
        self.expr_entry.insert(tk.END, f"{symbol}")
        self.expr_entry.configure(state="readonly")

    def clear_formula(self):
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
                res_list = sorted(list(result), key=len)
                # Formateamos bonito con llaves
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