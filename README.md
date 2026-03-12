# AURA — A Voice-Controlled AI Assistant for Visually Impaired Navigation

---

**AURA** (Visual Assistant for Visually Impaired) is an advanced, fully voice-operated personal assistant designed to bridge the gap between complex digital interactions and voice-first accessibility. By integrating computer vision, natural language processing, and an intuitive web interface, VAVI acts as both a digital companion and a navigational aid.

With over **50+ intelligent commands**, AURA can browse the web, send WhatsApp messages, recognize objects and faces, detect emotions, read text from documents, and even act as a navigational guide—all entirely hands-free.

---

## ✨ Features

AURA provides a robust suite of voice-activated features:

### 👁️‍🗨️ Vision & Accessibility
- **Scene Description & Navigation:** *"Describe my surroundings"* or *"Guide me"* — Real-time obstacle warnings and scene analysis using YOLOv8.
- **Face Recognition:** *"Remember this face as Mom"* / *"Who is in front of me?"* — Learns and recognizes family members.
- **Emotion Detection:** *"How do I look?"* — Analyzes your facial expression and responds empathetically.
- **Document Reader Mode:** *"Read document"* — Continuous OCR reading with voice controls (*"next page"*, *"repeat"*).
- **Object Detection & Depth:** *"Find my keys"* / *"How far is the chair?"* — Locates objects and estimates proximity.

### 🧠 Conversational AI
- **Context-Aware:** Powered by **Groq Llama 3**, AURA remembers previous turns in a conversation.
- **Deep Help System:** Interactive voice guide categories all 50+ commands.
- **Multi-Lingual:** Direct translation and definition support for global accessibility.

### 🚀 Productivity & Lifestyle
- **Mood-Based Music:** *"Play something relaxing"* or *"I need workout music"* — Automatically curates YouTube playlists.
- **Proactive Alerts:** Runs in the background to automatically warn you about low battery and scheduled medication reminders.
- **Daily Briefing & News:** Summarizes your day, local weather, and top headlines.
- **Utilities:** Alarms, timers, math, currency conversion, file finding, and to-do lists.

### 📱 System & Communication
- **Emergency SOS:** *"Emergency"* — Instantly WhatsApps your live location to a designated emergency contact.
- **Speed Dial & Messaging:** Call or message saved contacts via WhatsApp via voice.
- **System Controls:** Adjust brightness/volume, take screenshots, check battery, and open apps.

---

## 🛠️ Installation & Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/devanshrajput07/Virtual-Assistant-For-Visually-Impaired.git
   cd Virtual-Assistant-For-Visually-Impaired
   ```

2. **Create a Virtual Environment**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Mac/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   *Note: For Document Reader functionality, ensure [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) is installed on your system.*

4. **Environment Variables**
   Create a `.env` file in the root directory and add your API keys:
   ```env
   GROQ_API_KEY=your_groq_api_key
   NEWS_API_KEY=your_newsapi_org_key
   ```

---

## 🚀 Usage

**Run the Web UI Mode (Recommended)**
This launches a beautiful, accessible web interface with the "Hey AURA" wake word support.

```bash
python app.py
```

---
*Built with ❤️ to make the physical and digital world more accessible.*
