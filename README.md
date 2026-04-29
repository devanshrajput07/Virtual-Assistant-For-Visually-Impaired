# AURA — A Voice-Controlled AI Assistant for Visually Impaired Navigation

[![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Framework-Flask-lightgrey?logo=flask)](https://flask.palletsprojects.com/)
[![MongoDB](https://img.shields.io/badge/Database-MongoDB%20Atlas-green?logo=mongodb)](https://www.mongodb.com/atlas)
[![AI](https://img.shields.io/badge/AI-Llama%203%20(Groq)-orange)](https://groq.com/)

---

**AURA** (Visual Assistant for Visually Impaired) is a state-of-the-art, fully voice-operated personal assistant designed to bridge the gap between complex digital interactions and voice-first accessibility. By integrating advanced computer vision, real-time spatial analysis, and high-performance LLMs, AURA acts as both a digital companion and a navigational aid for the visually impaired.

With over **50+ intelligent commands**, AURA can browse the web, send WhatsApp messages, recognize objects and faces, detect emotions, and read documents—all entirely hands-free.

---

## 🛠️ Technology Stack

- **Core Engine:** Python 3.9+ & Flask (Web Interface)
- **Intelligence:** Groq Llama 3.1 (High-speed Conversational AI)
- **Computer Vision:** OpenCV & YOLOv8 (Object Detection & Spatial Awareness)
- **Automation:** PyAutoGUI & Win32GUI (Desktop UI interaction for WhatsApp Calling)
- **Database:** MongoDB Atlas (Cloud-synced profiles, contacts, and face data)
- **Speech:** Google Speech-to-Text & Edge-TTS (Natural voice synthesis)
- **OCR:** Tesseract OCR (Document & Text Reading)

---

## ✨ Key Features

### 👁️‍🗨️ Vision & Accessibility
- **Real-time Face Recognition:** *"Who is in front of me?"* — Uses MongoDB to learn and recognize people across devices.
- **Scene Description:** *"Describe my surroundings"* — Comprehensive scene analysis and obstacle detection.
- **Document Reader Mode:** *"Read document"* — Intelligent OCR with voice-controlled navigation (*repeat, next page*).
- **Emotion Analysis:** *"How do I look?"* — Empathetic feedback based on facial expression analysis.
- **Spatial Awareness:** *"How far is the chair?"* — Depth estimation and object proximity alerts.

### 🧠 Conversational Intelligence
- **Contextual Memory:** Remembers previous interactions for a natural conversation flow.
- **Deep Help System:** Interactive voice guide for all system commands.
- **Global Knowledge:** Instant definitions, translations, and Wikipedia searches.

### 🚀 Productivity & Communication
- **WhatsApp Voice & Video Calling:** *"Make a video call to Ashwin"* — Fully automated hands-free calling using coordinate-based desktop interaction.
- **Emergency SOS:** *"Help me"* — Instantly sends live location and emergency alerts via WhatsApp.
- **Proactive Alerts:** Automatic background monitoring for low battery and medication reminders.
- **Daily Briefing:** Summarized weather, news, and daily agenda upon wake-up.
- **Lifestyle Utilities:** Voice-controlled Alarms, Timers, Math, and Currency Conversion.

---

## ⚙️ Installation & Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/devanshrajput07/Virtual-Assistant-For-Visually-Impaired.git
   cd Virtual-Assistant-For-Visually-Impaired
   ```

2. **Environment Setup**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Mac/Linux:
   source venv/bin/activate
   
   pip install -r requirements.txt
   ```
   *Note: Ensure [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) is installed for Document Reader features.*

3. **Configuration**
   Create a `.env` file in the root directory:
   ```env
   GROQ_API_KEY=your_groq_key
   NEWS_API_KEY=your_news_key
   MONGODB_URI=your_mongodb_atlas_uri
   DB_NAME=db_name
   LOG_LEVEL=INFO
   ```

---

## 🚀 Execution

Launch the AURA ecosystem with the beautiful spatial web interface:

```bash
python app.py
```

---
*Built with ❤️ to make the physical and digital world more accessible.*
