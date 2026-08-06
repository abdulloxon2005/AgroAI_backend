/* ==========================================================================
   AgroAI — Modern Landing Page JavaScript Interactions
   Author: Ro'ziyev Abdulloxon
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Sticky Navbar on Scroll
  const header = document.querySelector('.header');
  window.addEventListener('scroll', () => {
    if (window.scrollY > 40) {
      header.classList.add('scrolled');
    } else {
      header.classList.remove('scrolled');
    }
  });

  // 2. Interactive AI Chat Demo
  const chatBox = document.getElementById('chatBox');
  const chatInput = document.getElementById('chatInput');
  const sendBtn = document.getElementById('sendBtn');

  async function handleSendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;

    // Append User Message
    appendMessage(text, 'user');
    chatInput.value = '';

    // Typing indicator
    const typingElem = document.createElement('div');
    typingElem.className = 'chat-msg msg-ai';
    typingElem.innerText = 'AgroAI Agronom maslahati tayyorlanmoqda... ⏳';
    chatBox.appendChild(typingElem);
    chatBox.scrollTop = chatBox.scrollHeight;

    // Simulate or fetch AI Response
    try {
      let replyText = "";
      const lower = text.toLowerCase();
      
      if (lower.includes('sug\'or') || lower.includes('suv')) {
        replyText = "💧 **AgroAI Sug'orish Tavsiyasi:** Ekinlarni ertalabki salqinda yoki kechqurun sug'orish ma'qul. Tuproq namligini 15-20 sm chuqurlikda tekshiring!";
      } else if (lower.includes('o\'g\'it') || lower.includes('oziqlan')) {
        replyText = "🌿 **AgroAI O'g'itlash Tavsiyasi:** Maysalash va o'sish davrida Azotli (Selitra), gullashda esa Fosfor-Kaliy (NPK) o'g'itlari beriladi.";
      } else if (lower.includes('kasallik') || lower.includes('dori') || lower.includes('shira')) {
        replyText = "🛡️ **AgroAI Zararkunandaga Qarshi:** Zamburug'li kasalliklar uchun *Fitosporin-M*, shira va qurtlar uchun *Enjiyo* purkash tavsiya etiladi.";
      } else {
        replyText = "Assalomu alaykum! Men AgroAI — professional AI agronom maslahatchisiman. Ekin turi, sug'orish yoki kasallik haqida istalgan savolingizni berishingiz mumkin! 🌾";
      }

      setTimeout(() => {
        chatBox.removeChild(typingElem);
        appendMessage(replyText, 'ai');
      }, 700);

    } catch (err) {
      chatBox.removeChild(typingElem);
      appendMessage("Assalomu alaykum! Men AgroAI maslahatchisiman. Ekinlaringiz parvarishi bo'yicha savol bering! 🌾", 'ai');
    }
  }

  function appendMessage(msgText, sender) {
    const div = document.createElement('div');
    div.className = `chat-msg msg-${sender}`;
    div.innerText = msgText;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
  }

  if (sendBtn && chatInput) {
    sendBtn.addEventListener('click', handleSendMessage);
    chatInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') handleSendMessage();
    });
  }
});
