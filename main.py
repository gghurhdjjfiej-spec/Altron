import json, threading, os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.utils import platform
import urllib.request

OR_URL = "https://openrouter.ai/api/v1/chat/completions"
OR_MODEL = "inclusionai/ling-3.0-flash-sante:free"

def tts_speak(text):
    if platform == "android":
        try:
            from jnius import autoclass
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            TextToSpeech = autoclass("android.speech.tts.TextToSpeech")
            Locale = autoclass("java.util.Locale")
            act = PythonActivity.mActivity
            tts = TextToSpeech(act, None)
            tts.setLanguage(Locale("ru", "RU"))
            tts.speak(text, TextToSpeech.QUEUE_FLUSH, None, "altron")
        except Exception as e:
            print("tts err:", e)

def ask_ai(prompt, key):
    try:
        body = json.dumps({
            "model": OR_MODEL,
            "messages": [
                {"role": "system", "content":
                 "Ты Альтрон. Отвечай коротко на языке вопроса. Без markdown."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 500
        }).encode()
        req = urllib.request.Request(OR_URL, data=body, headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + key,
            "HTTP-Referer": "https://altron.local",
            "X-Title": "Altron"
        })
        d = json.load(urllib.request.urlopen(req, timeout=60))
        return d["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return "Ошибка: " + str(e)[:200]

class AltronUI(BoxLayout):
    def __init__(self, **kw):
        super().__init__(orientation="vertical", padding=15, spacing=10, **kw)
        self.add_widget(Label(text="АЛЬТРОН", size_hint=(1, 0.1),
                              font_size="28sp", color=(0.4, 0.9, 1, 1)))
        self.output = Label(text="Напиши вопрос",
                            size_hint=(1, 0.5), halign="center",
                            valign="middle", color=(0.85, 0.95, 1, 1))
        self.output.bind(size=self.output.setter("text_size"))
        self.add_widget(self.output)
        self.key_input = TextInput(
            hint_text="Ключ OpenRouter...", size_hint=(1, 0.1),
            multiline=False, background_color=(0.08, 0.15, 0.22, 1),
            foreground_color=(0.8, 0.95, 1, 1))
        self.add_widget(self.key_input)
        self.input = TextInput(
            hint_text="Вопрос...", size_hint=(1, 0.15),
            multiline=False, background_color=(0.08, 0.15, 0.22, 1),
            foreground_color=(0.8, 0.95, 1, 1))
        self.add_widget(self.input)
        row = BoxLayout(size_hint=(1, 0.15), spacing=10)
        b = Button(text="Отправить", background_color=(0.1, 0.5, 0.9, 1))
        b.bind(on_press=self.on_send)
        row.add_widget(b)
        m = Button(text="🎤", font_size="32sp",
                   background_color=(0.5, 0.1, 0.1, 1))
        m.bind(on_press=lambda *a: tts_speak("Проверка голоса"))
        row.add_widget(m)
        self.add_widget(row)

    def on_send(self, *a):
        q = self.input.text.strip()
        key = self.key_input.text.strip()
        if not q: return
        if not key:
            self.output.text = "Вставь ключ OpenRouter"
            return
        self.input.text = ""
        self.output.text = "Думаю..."
        threading.Thread(target=self._ask, args=(q, key)).start()

    def _ask(self, q, key):
        ans = ask_ai(q, key)
        Clock.schedule_once(lambda dt: self._show(ans), 0)

    def _show(self, ans):
        self.output.text = ans
        tts_speak(ans)

class AltronApp(App):
    def build(self):
        return AltronUI()

if __name__ == "__main__":
    AltronApp().run()
