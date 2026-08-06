/* ==========================================================================
   AgroAI — Interactive Futuristic Particle Canvas & Live AI Script
   Author: Ro'ziyev Abdulloxon
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Futuristic Canvas Matrix Particle Network Background
  const canvas = document.getElementById('bgCanvas');
  if (canvas) {
    const ctx = canvas.getContext('2d');
    let width = canvas.width = window.innerWidth;
    let height = canvas.height = window.innerHeight;

    window.addEventListener('resize', () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    });

    const particles = [];
    const particleCount = Math.min(Math.floor(width / 20), 65);

    for (let i = 0; i < particleCount; i++) {
      particles.push({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.6,
        vy: (Math.random() - 0.5) * 0.6,
        radius: Math.random() * 2 + 1,
      });
    }

    function animate() {
      ctx.clearRect(0, 0, width, height);

      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];
        p.x += p.vx;
        p.y += p.vy;

        if (p.x < 0 || p.x > width) p.vx *= -1;
        if (p.y < 0 || p.y > height) p.vy *= -1;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(0, 245, 160, 0.4)';
        ctx.fill();

        for (let j = i + 1; j < particles.length; j++) {
          const p2 = particles[j];
          const dist = Math.hypot(p.x - p2.x, p.y - p2.y);
          if (dist < 130) {
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.strokeStyle = `rgba(0, 245, 160, ${0.15 * (1 - dist / 130)})`;
            ctx.lineWidth = 0.8;
            ctx.stroke();
          }
        }
      }
      requestAnimationFrame(animate);
    }
    animate();
  }

  // 2. Sticky Glass Navbar
  const header = document.querySelector('.header');
  window.addEventListener('scroll', () => {
    if (window.scrollY > 40) {
      header.classList.add('scrolled');
    } else {
      header.classList.remove('scrolled');
    }
  });

  // 3. Interactive AI Chat Demo
  const chatBox = document.getElementById('chatBox');
  const chatInput = document.getElementById('chatInput');
  const sendBtn = document.getElementById('sendBtn');

  async function handleSendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;

    appendMessage(text, 'user');
    chatInput.value = '';

    const typingElem = document.createElement('div');
    typingElem.className = 'chat-msg msg-ai';
    typingElem.innerText = 'AgroAI Agronom maslahati tayyorlanmoqda... ⏳';
    chatBox.appendChild(typingElem);
    chatBox.scrollTop = chatBox.scrollHeight;

    setTimeout(() => {
      chatBox.removeChild(typingElem);
      let replyText = "";
      const lower = text.toLowerCase();

      if (lower.includes('sug\'or') || lower.includes('suv')) {
        replyText = "💧 **AgroAI Sug'orish Tavsiyasi:** Ekinlarni ertalabki salqinda yoki kechqurun sug'orish ma'qul. Tuproq namligini 15-20 sm chuqurlikda tekshiring!";
      } else if (lower.includes('o\'g\'it') || lower.includes('oziqlan')) {
        replyText = "🌿 **AgroAI O'g'itlash Tavsiyasi:** Maysalash va o'sish davrida Azotli (Selitra), gullashda esa Fosfor-Kaliy (NPK) o'g'itlari beriladi.";
      } else if (lower.includes('kasallik') || lower.includes('dori') || lower.includes('shira')) {
        replyText = "🛡️ **AgroAI Zararkunandaga Qarshi:** Zamburug'li kasalliklar uchun *Fitosporin-M*, shira va qurtlar uchun *Enjiyo* purkash tavsiya etiladi.";
      } else {
        replyText = "Assalomu alaykum! Men AgroAI — professional AI agronom maslahatchisiman. Ekin turi, sug'orish yoki kasallik haqida istalgan savolingizga javob beraman! 🌾";
      }
      appendMessage(replyText, 'ai');
    }, 700);
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
