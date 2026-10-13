/**
 * OnisAgent Voice Interaction Controller
 * Web Speech API (STT & TTS) with Audio Visualizer
 */

class VoiceController {
  constructor(options = {}) {
    this.lang = options.lang || 'vi-VN';
    this.autoSpeak = options.autoSpeak !== false;
    this.onTranscript = options.onTranscript || (() => {});
    this.onInterim = options.onInterim || (() => {});
    this.onStatusChange = options.onStatusChange || (() => {});

    this.recognition = null;
    this.isRecording = false;
    this.isSpeaking = false;
    this.synth = window.speechSynthesis;
    this.voices = [];

    this.initRecognition();
    this.loadVoices();
  }

  initRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.warn("Trình duyệt không hỗ trợ Web Speech API Recognition.");
      return;
    }

    this.recognition = new SpeechRecognition();
    this.recognition.continuous = false;
    this.recognition.interimResults = true;
    this.recognition.lang = this.lang;

    this.lastInterim = '';

    this.recognition.onstart = () => {
      this.isRecording = true;
      this.lastInterim = '';
      this.onStatusChange('recording', 'Đang nghe bạn nói...');
      this.setVisualizer(true);
    };

    this.recognition.onresult = (event) => {
      let interimTranscript = '';
      let finalTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        } else {
          interimTranscript += event.results[i][0].transcript;
        }
      }

      if (interimTranscript) {
        this.lastInterim = interimTranscript;
        this.onInterim(interimTranscript);
      }

      if (finalTranscript) {
        this.lastInterim = '';
        this.onTranscript(finalTranscript.trim());
      }
    };

    this.recognition.onerror = (event) => {
      console.warn("Speech recognition error:", event.error);
      this.isRecording = false;
      this.setVisualizer(false);
      this.onStatusChange('idle', 'Nhấn micro hoặc gõ tin nhắn để bắt đầu');
    };

    this.recognition.onend = () => {
      this.isRecording = false;
      this.setVisualizer(false);
      this.onStatusChange('idle', 'Nhấn micro để nói tiếng Việt');
    };
  }

  loadVoices() {
    if (!this.synth) return;
    this.voices = this.synth.getVoices();
    if (this.synth.onvoiceschanged !== undefined) {
      this.synth.onvoiceschanged = () => {
        this.voices = this.synth.getVoices();
      };
    }
  }

  toggleListening() {
    if (this.isRecording) {
      this.stopListening();
    } else {
      this.startListening();
    }
  }

  startListening() {
    if (!this.recognition) {
      alert("Trình duyệt của bạn chưa bật hoặc không hỗ trợ Speech Recognition. Vui lòng sử dụng Chrome/Edge hoặc nhập tin nhắn bằng bàn phím.");
      return;
    }
    if (this.isRecording) {
      this.stopListening();
      return;
    }
    this.stopSpeaking();
    this.lastInterim = '';
    try {
      this.recognition.lang = this.lang || 'vi-VN';
      this.recognition.start();
    } catch (e) {
      console.error(e);
    }
  }

  stopListening() {
    if (this.recognition && this.isRecording) {
      try {
        this.recognition.stop();
      } catch (e) {}
      this.isRecording = false;
      this.setVisualizer(false);

      if (this.lastInterim && this.lastInterim.trim().length > 0) {
        const text = this.lastInterim.trim();
        this.lastInterim = '';
        this.onTranscript(text);
      }
    }
  }

  speak(text, force = false) {
    if (!this.autoSpeak && !force) return;

    this.stopSpeaking();

    // Clean markdown formatting before speaking
    let cleanText = text
      .replace(/\*\*(.*?)\*\*/g, '$1')
      .replace(/\*(.*?)\*/g, '$1')
      .replace(/`([^`]+)`/g, '$1')
      .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1')
      .replace(/⚡|🧠|⚠️|🛡️|•|---|#/g, '')
      .replace(/\[System 1 Fast Path\]/g, '')
      .replace(/\[LLM Reasoning Path[^\]]*\]/g, '')
      .replace(/\s+/g, ' ')
      .trim();

    if (!cleanText) return;

    // Use Natural Vietnamese Voice from Server (100% Vietnamese, perfect pronunciation)
    if (this.lang.startsWith('vi')) {
      const audioUrl = `/api/voice/tts?text=${encodeURIComponent(cleanText)}`;
      this.currentAudio = new Audio(audioUrl);
      this.isSpeaking = true;
      this.setVisualizer(true);
      this.onStatusChange('speaking', 'OnisAgent đang nói (Giọng tiếng Việt chuẩn)...');

      this.currentAudio.onplay = () => {
        this.isSpeaking = true;
        this.setVisualizer(true);
      };

      this.currentAudio.onended = () => {
        this.isSpeaking = false;
        this.setVisualizer(false);
        this.onStatusChange('idle', 'Sẵn sàng');
        this.currentAudio = null;
      };

      this.currentAudio.onerror = (e) => {
        console.warn("Server TTS audio error, falling back to browser speech synthesis:", e);
        this.speakBrowserFallback(cleanText);
      };

      this.currentAudio.play().catch(err => {
        console.warn("Audio play prevented or failed, trying browser synthesis:", err);
        this.speakBrowserFallback(cleanText);
      });
      return;
    }

    this.speakBrowserFallback(cleanText);
  }

  speakBrowserFallback(cleanText) {
    if (!this.synth) return;
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = this.lang;
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    if (this.voices.length > 0) {
      const viVoice = this.voices.find(v => v.lang.includes('vi') || v.lang.includes('VIE'));
      if (viVoice) utterance.voice = viVoice;
    }

    utterance.onstart = () => {
      this.isSpeaking = true;
      this.setVisualizer(true);
      this.onStatusChange('speaking', 'OnisAgent đang nói...');
    };

    utterance.onend = () => {
      this.isSpeaking = false;
      this.setVisualizer(false);
      this.onStatusChange('idle', 'Sẵn sàng');
    };

    utterance.onerror = () => {
      this.isSpeaking = false;
      this.setVisualizer(false);
    };

    this.synth.speak(utterance);
  }

  stopSpeaking() {
    if (this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio.currentTime = 0;
      this.currentAudio = null;
    }
    if (this.synth && this.synth.speaking) {
      this.synth.cancel();
    }
    this.isSpeaking = false;
    this.setVisualizer(false);
  }

  setVisualizer(active) {
    document.querySelectorAll('.visualizer').forEach(el => {
      if (active) el.classList.add('active');
      else el.classList.remove('active');
    });
  }

  setLang(newLang) {
    this.lang = newLang;
    if (this.recognition) this.recognition.lang = newLang;
  }

  toggleAutoSpeak() {
    this.autoSpeak = !this.autoSpeak;
    return this.autoSpeak;
  }
}

window.VoiceController = VoiceController;
