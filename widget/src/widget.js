(function () {
  // Совпадает с MAX_MESSAGE_LENGTH в конфиге бэкенда (app/config.py) —
  // при изменении лимита там же обновите и здесь.
  const MAX_MESSAGE_LENGTH = 1000;

  let config = { apiUrl: "http://127.0.0.1:8000" };
  let shadowRoot = null;

  window.LimeAI = {
    init: function (options) {
      if (options && options.apiUrl) {
        config.apiUrl = options.apiUrl.replace(/\/$/, "");
      }
      // Повторный init() в этом же документе не пересоздаёт виджет и не дублирует историю
      if (document.getElementById("lime-ai-root")) return;

      createWidget();
      loadHistory();
    },
    toggleChat: toggleChat,
    clearHistory: clearHistory,
    sendQuickMessage: sendQuickMessage,
  };

  // Разметка карточки приветствия с быстрыми ответами.
  // Клики обрабатываются делегированием в createWidget() через data-msg,
  // а не через inline onclick — иначе кнопки молча не сработали бы на сайтах
  // со строгим Content-Security-Policy (script-src без unsafe-inline).
  const welcomeHTML = `
    <div class="welcome-card" id="lime-welcome">
        <h5>Привет! Я AI-ассистент Lime HD TV</h5>
        <p>Готов ответить на вопросы по работе сервиса, подпискам и настройке приложений.</p>
        <div class="chips-wrapper">
            <button class="chip-btn" data-msg="Как смотреть ТВ бесплатно?">Смотреть бесплатно</button>
            <button class="chip-btn" data-msg="На каких устройствах работает Lime HD?">Поддерживаемые устройства</button>

            <button class="chip-btn chip-extra" data-msg="Как отменить подписку?">Отменить подписку</button>
            <button class="chip-btn chip-extra" data-msg="Как подключить к Smart TV?">Настроить Smart TV</button>
            <button class="chip-btn chip-extra" data-msg="Не работает трансляция">Ошибки видео</button>
            <button class="chip-btn chip-extra" data-msg="Где взять промокод?">Промокоды</button>
            <button class="chip-btn chip-extra" data-msg="Какие каналы есть в подписке?">Список каналов</button>
        </div>
    </div>
  `;

  function createWidget() {
    if (document.getElementById("lime-ai-root")) return;

    const host = document.createElement("div");
    host.id = "lime-ai-root";
    document.body.appendChild(host);

    shadowRoot = host.attachShadow({ mode: "open" });

    const fontLink = document.createElement("link");
    fontLink.rel = "stylesheet";
    fontLink.href = "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Unbounded:wght@600;700;800&display=swap&family=Montserrat:wght@800";
    shadowRoot.appendChild(fontLink);

    const style = document.createElement("style");
    style.textContent = `
    * {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
        font-family: 'Unbounded', sans-serif;
        font-weight: 600;
    }

    :host {
        /* Пастельные акценты для карточек, чипсов и кнопок шапки */
        --pastel-lime: #D9F99D;
        --pastel-lime-bg: #F4FCE8;
        --pastel-red: #FCA5A5;
        --pastel-red-bg: #FEF2F2;
        --pastel-blue: #BAE6FD;
        --pastel-blue-bg: #F0F9FF;

        --lime-green: #6BB023;

        --dark-bg: #0F0F0F;
        --border-light: rgba(255, 255, 255, 0.85);

        --shadow-tile:
            0 16px 32px -8px rgba(15, 23, 42, 0.12),
            0 6px 12px -4px rgba(15, 23, 42, 0.08),
            inset 0 1px 2px rgba(255, 255, 255, 0.9);
        --shadow-hover:
            0 20px 40px -10px rgba(15, 23, 42, 0.16),
            0 8px 16px -6px rgba(15, 23, 42, 0.1),
            inset 0 1px 2px rgba(255, 255, 255, 1);
        --shadow-hover-lime:
            0 16px 32px -8px rgba(15, 23, 42, 0.1),
            0 0 16px rgba(217, 249, 157, 0.6),
            inset 0 1px 2px rgba(255, 255, 255, 1);

        /* Токены кастомного скроллбара (см. .tile-messages ниже) */
        --scrollbar-track: rgba(255, 255, 255, 0.25);
        --scrollbar-thumb: rgba(226, 232, 240, 0.55);
        --scrollbar-thumb-hover: rgba(217, 249, 157, 0.75);
    }

    .tile {
        background: linear-gradient(145deg, #f8fafc 0%, #e2e8f0 100%);
        border: 1px solid var(--border-light);
        border-radius: 20px;
        box-shadow: var(--shadow-tile);
        transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1),
                    box-shadow 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    }

    .launcher-btn {
        position: fixed;
        bottom: 28px;
        right: 28px;
        height: 52px;
        padding: 12px 22px;
        border-radius: 20px;
        background: linear-gradient(145deg, #ffffff 0%, var(--pastel-lime-bg) 100%);
        color: var(--dark-bg);
        border: 1px solid var(--border-light);
        outline: none;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        font-family: 'Unbounded', sans-serif;
        font-size: 15px;
        font-weight: 700;
        letter-spacing: -0.02em;
        white-space: nowrap;
        box-shadow: var(--shadow-tile);
        transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1),
                    box-shadow 0.25s cubic-bezier(0.16, 1, 0.3, 1),
                    background 0.25s ease;
        z-index: 999999;
    }

    .launcher-btn:hover {
        transform: translateY(-3px);
        box-shadow: var(--shadow-hover);
        background: linear-gradient(145deg, #ffffff 0%, #E6F4D7 100%);
    }

    .launcher-btn:active {
        transform: translateY(-1px);
    }

    .launcher-btn svg {
        width: 20px;
        height: 20px;
        fill: #4D8B12;
        flex-shrink: 0;
        transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    }

    .launcher-btn:hover svg {
        transform: scale(1.1);
    }

    .launcher-btn,
    .launcher-btn * {
        font-family: 'Montserrat', sans-serif;
        font-weight: 800;
    }

    .chat-window {
        position: fixed;
        bottom: 96px;
        right: 28px;
        width: 400px;
        height: 600px;
        max-height: calc(100vh - 120px);
        display: flex;
        flex-direction: column;
        gap: 12px;
        opacity: 0;
        transform: translateY(20px) scale(0.96);
        pointer-events: none;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        z-index: 999999;
    }

    .chat-window.active {
        opacity: 1;
        transform: translateY(0) scale(1);
        pointer-events: all;
    }

    .chat-window.expanded {
        width: 70vw;
        height: calc(100vh - 64px);
        bottom: 32px;
        right: 15vw;
        max-height: none;
    }

    .header-grid {
        display: flex;
        align-items: center;
        gap: 10px;
        flex-shrink: 0;
        position: relative;
    }

    .tile-brand {
        flex: 1;
        padding: 12px 18px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    .brand-title {
        font-size: 14px;
        font-weight: 700;
        color: var(--dark-bg);
        letter-spacing: -0.01em;
    }

    .status-indicator {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 12px;
        font-weight: 600;
        color: #475569;
    }

    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--lime-green);
        box-shadow: 0 0 8px var(--lime-green);
    }

    .tile-btn {
        width: 44px;
        height: 44px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        border-radius: 14px;
        background: linear-gradient(145deg, #f8fafc 0%, #e2e8f0 100%);
        border: 1px solid var(--border-light);
        box-shadow: var(--shadow-tile);
        color: var(--dark-bg);
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        outline: none;
    }

    .tile-btn:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-hover);
        background: #FFFFFF;
    }

    .tile-btn svg {
        width: 18px;
        height: 18px;
        stroke: currentColor;
        stroke-width: 2;
        fill: none;
        stroke-linecap: round;
        stroke-linejoin: round;
    }

    .menu-dropdown {
        position: absolute;
        top: 52px;
        right: 44px;
        background: linear-gradient(145deg, #ffffff 0%, #f8fafc 100%);
        border: 1px solid var(--border-light);
        border-radius: 16px;
        box-shadow: var(--shadow-hover);
        padding: 6px;
        display: flex;
        flex-direction: column;
        opacity: 0;
        transform: translateY(-8px) scale(0.95);
        pointer-events: none;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        z-index: 1000;
        min-width: 180px;
    }

    .menu-dropdown.active {
        opacity: 1;
        transform: translateY(0) scale(1);
        pointer-events: all;
    }

    .dropdown-item {
        display: flex;
        align-items: center;
        gap: 10px;
        width: 100%;
        padding: 10px 12px;
        border: none;
        background: transparent;
        border-radius: 12px;
        font-family: 'Inter', sans-serif;
        font-size: 13px;
        font-weight: 600;
        color: #EF4444;
        cursor: pointer;
        transition: background 0.2s ease, transform 0.2s ease;
    }

    .dropdown-item:hover {
        background: #FEF2F2;
        transform: translateX(2px);
    }

    .dropdown-item svg {
        width: 16px;
        height: 16px;
        stroke: #EF4444;
        stroke-width: 2;
        fill: none;
        stroke-linecap: round;
        stroke-linejoin: round;
        flex-shrink: 0;
    }

    .tile-messages {
        flex: 1;
        padding: 20px;
        overflow-y: auto;
        display: flex;
        flex-direction: column;
        gap: 14px;

        /* Firefox поддерживает только цвет скроллбара (без теней/градиентов) —
           это ограничение спецификации, а не выбор дизайна */
        scrollbar-width: thin;
        scrollbar-color: var(--scrollbar-thumb) var(--scrollbar-track);
    }

    /* Кастомный «стеклянный» скроллбар для Chrome / Safari / Edge (WebKit/Blink) */
    .tile-messages::-webkit-scrollbar {
        width: 8px;
    }

    .tile-messages::-webkit-scrollbar-track {
        background: var(--scrollbar-track);
        border-radius: 10px;
        margin: 6px 0;
    }

    .tile-messages::-webkit-scrollbar-thumb {
        background: var(--scrollbar-thumb);
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.7);
        box-shadow:
            0 2px 6px rgba(15, 23, 42, 0.14),
            inset 0 1px 1px rgba(255, 255, 255, 0.9);
        -webkit-backdrop-filter: blur(4px);
        backdrop-filter: blur(4px);
    }

    .tile-messages::-webkit-scrollbar-thumb:hover {
        background: var(--scrollbar-thumb-hover);
        box-shadow:
            0 4px 10px rgba(107, 176, 35, 0.25),
            inset 0 1px 1px rgba(255, 255, 255, 0.95);
    }

    .input-grid {
        display: flex;
        align-items: center;
        gap: 10px;
        flex-shrink: 0;
    }

    .tile-input-box {
        flex: 1;
        padding: 6px 14px;
        display: flex;
        align-items: center;
        transition: all 0.2s ease;
    }

    .tile-input-box:focus-within {
        border-color: var(--pastel-lime);
    }

    .chat-input {
        width: 100%;
        border: none;
        outline: none;
        background: transparent;
        font-size: 14px;
        color: #0F0F0F;
        padding: 8px 0;
    }

    .chat-input::placeholder {
        color: #64748B;
    }

    .chat-input:disabled {
        opacity: 0.6;
    }

    .tile-send {
        width: 48px;
        height: 48px;
        background: var(--dark-bg);
        color: #FFFFFF;
        border-radius: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        border: 1px solid rgba(255, 255, 255, 0.15);
        box-shadow: 0 8px 16px rgba(15, 15, 15, 0.2);
    }

    .tile-send:hover {
        transform: translateY(-2px);
        background: var(--lime-green);
        border-color: var(--lime-green);
    }

    .tile-send:disabled {
        opacity: 0.5;
        cursor: default;
        transform: none;
        background: var(--dark-bg);
    }

    .tile-send svg {
        width: 20px;
        height: 20px;
        stroke: currentColor;
        stroke-width: 2;
        fill: none;
        stroke-linecap: round;
        stroke-linejoin: round;
    }

    .welcome-card {
        background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
        border: 1px solid rgba(255, 255, 255, 0.95);
        border-radius: 18px;
        padding: 18px;
        box-shadow:
            0 8px 20px -4px rgba(15, 23, 42, 0.08),
            0 2px 6px -2px rgba(15, 23, 42, 0.04),
            inset 0 1px 1px rgba(255, 255, 255, 1);
        margin-bottom: 8px;
    }
    .welcome-card h5 {
        font-size: 14px;
        font-weight: 700;
        color: var(--dark-bg);
        margin-bottom: 12px;
    }
    .welcome-card p {
        font-size: 13px;
        color: #475569;
        line-height: 1.45;
        margin-bottom: 12px;
    }

    .chips-wrapper {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
    }
    .chip-btn {
        background: #FFFFFF;
        border: 1px solid rgba(226, 232, 240, 0.8);
        border-radius: 12px;
        padding: 9px 13px;
        font-size: 12px;
        font-weight: 600;
        color: var(--dark-bg);
        text-align: center;
        cursor: pointer;
        box-shadow: 0 2px 4px rgba(15, 23, 42, 0.03);
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        width: fit-content;
        white-space: nowrap;
    }
    .chip-btn:hover {
        border-color: var(--pastel-lime);
        background: var(--pastel-lime-bg);
        transform: translateY(-1px) translateX(2px);
        box-shadow: 0 4px 10px rgba(107, 176, 35, 0.12);
    }

    .chip-extra {
        display: none;
    }

    .chat-window.expanded .chip-extra {
        display: block;
    }

    .msg {
        max-width: 84%;
        padding: 12px 16px;
        font-size: 13px;
        line-height: 1.5;
        word-break: break-word;
        animation: fadeIn 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    }

    .msg-user {
        align-self: flex-end;
        background: linear-gradient(145deg, #1E293B 0%, #0F172A 100%);
        color: #FFFFFF;
        border-radius: 18px 18px 4px 18px;
        border: 1px solid rgba(255, 255, 255, 0.12);
        box-shadow:
            0 8px 18px -4px rgba(15, 23, 42, 0.25),
            0 2px 6px -2px rgba(15, 23, 42, 0.15),
            inset 0 1px 1px rgba(255, 255, 255, 0.18);
    }

    .msg-bot {
        align-self: flex-start;
        background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
        color: #0F172A;
        border: 1px solid rgba(255, 255, 255, 0.95);
        border-radius: 18px 18px 18px 4px;
        box-shadow:
            0 8px 18px -4px rgba(15, 23, 42, 0.07),
            0 2px 6px -2px rgba(15, 23, 42, 0.04),
            inset 0 1px 1px rgba(255, 255, 255, 1);
    }

    .typing-indicator {
        align-self: flex-start;
        background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
        border: 1px solid rgba(255, 255, 255, 0.95);
        padding: 12px 18px;
        border-radius: 18px 18px 18px 4px;
        display: none;
        gap: 6px;
        align-items: center;
        box-shadow:
            0 8px 18px -4px rgba(15, 23, 42, 0.07),
            0 2px 6px -2px rgba(15, 23, 42, 0.04),
            inset 0 1px 1px rgba(255, 255, 255, 1);
    }

    .dot { width: 6px; height: 6px; background: var(--lime-green); border-radius: 50%; animation: bounce 1.4s infinite ease-in-out both; }
    .dot:nth-child(1) { animation-delay: -0.32s; }
    .dot:nth-child(2) { animation-delay: -0.16s; }

    @keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }

    #lime-expand {
        background: var(--pastel-lime-bg);
        border: 1px solid var(--pastel-lime);
    }
    #lime-expand:hover {
        background: var(--pastel-lime);
        box-shadow: var(--shadow-hover-lime);
    }

    #lime-menu {
        background: var(--pastel-blue-bg);
        border: 1px solid var(--pastel-blue);
    }
    #lime-menu:hover {
        background: var(--pastel-blue);
        box-shadow: 0 16px 32px -8px rgba(15, 23, 42, 0.1), 0 0 16px rgba(186, 230, 253, 0.5), inset 0 1px 2px rgba(255, 255, 255, 1);
    }

    #lime-close {
        background: var(--pastel-red-bg);
        border: 1px solid var(--pastel-red);
    }
    #lime-close:hover {
        background: var(--pastel-red);
        box-shadow: 0 16px 32px -8px rgba(15, 23, 42, 0.1), 0 0 16px rgba(252, 165, 165, 0.5), inset 0 1px 2px rgba(255, 255, 255, 1);
    }

    @media (max-width: 600px) {
        .chat-window { width: calc(100vw - 32px); right: 16px; bottom: 84px; height: 75vh; }
        .launcher-btn { bottom: 16px; right: 16px; }
        .expand-btn { display: none; }
    }
`;

    const container = document.createElement("div");
    container.innerHTML = `
    <button class="launcher-btn" id="lime-launcher" aria-label="Обратная связь" title="Чат поддержки">
        <svg viewBox="0 0 24 24">
            <path d="M20 2H4c-1.1 0-1.99.9-1.99 2L2 22l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zM6 9h12v2H6V9zm8 5H6v-2h8v2zm4-6H6V6h12v2z"/>
        </svg>
        <span>Задать вопрос</span>
    </button>

    <div class="chat-window" id="lime-window" role="dialog" aria-label="Чат поддержки Lime HD TV">

        <div class="header-grid">
            <div class="tile tile-brand">
                <span class="brand-title">LIME HD SUPPORT</span>
                <div class="status-indicator">
                    <span class="status-dot"></span>
                    <span>Онлайн</span>
                </div>
            </div>

            <button class="tile tile-btn expand-btn" id="lime-expand" title="Развернуть">
                <svg id="svg-expand" viewBox="0 0 24 24">
                    <path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"/>
                </svg>
            </button>

            <button class="tile tile-btn" id="lime-menu" title="Меню" aria-haspopup="true">
                <svg viewBox="0 0 24 24">
                    <circle cx="12" cy="6" r="1.5" fill="currentColor"/>
                    <circle cx="12" cy="12" r="1.5" fill="currentColor"/>
                    <circle cx="12" cy="18" r="1.5" fill="currentColor"/>
                </svg>
            </button>

            <div class="menu-dropdown" id="lime-dropdown">
                <button class="dropdown-item" id="lime-clear-all">
                    <svg viewBox="0 0 24 24">
                        <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2M10 11v6M14 11v6"/>
                    </svg>
                    <span>Новый диалог</span>
                </button>
            </div>

            <button class="tile tile-btn" id="lime-close" title="Закрыть">
                <svg viewBox="0 0 24 24">
                    <path d="M18 6L6 18M6 6l12 12"/>
                </svg>
            </button>
        </div>

        <div class="tile tile-messages" id="lime-messages">
            ${welcomeHTML}
            <div class="typing-indicator" id="lime-typing">
                <div class="dot"></div><div class="dot"></div><div class="dot"></div>
            </div>
        </div>

        <div class="input-grid">
            <div class="tile tile-input-box">
                <input type="text" class="chat-input" id="lime-input" placeholder="Задайте вопрос..." autocomplete="off" maxlength="${MAX_MESSAGE_LENGTH}" aria-label="Введите сообщение" />
            </div>

            <button class="tile tile-send" id="lime-send" title="Отправить" aria-label="Отправить сообщение">
                <svg viewBox="0 0 24 24">
                    <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/>
                </svg>
            </button>
        </div>

    </div>
`;

    shadowRoot.appendChild(style);
    shadowRoot.appendChild(container);

    shadowRoot.getElementById("lime-launcher").onclick = toggleChat;
    shadowRoot.getElementById("lime-close").onclick = toggleChat;
    shadowRoot.getElementById("lime-menu").onclick = toggleMenu;
    shadowRoot.getElementById("lime-clear-all").onclick = clearHistory;
    shadowRoot.getElementById("lime-send").onclick = handleSend;
    shadowRoot.getElementById("lime-expand").onclick = toggleExpand;

    shadowRoot.getElementById("lime-input").addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        handleSend();
      }
    });

    // Единый делегированный обработчик:
    // 1) клики по чипсам быстрых ответов (работает с CSP без unsafe-inline
    //    и переживает clearHistory(), т.к. слушатель висит на shadowRoot, а не на кнопках)
    // 2) закрытие выпадающего меню по клику вне его
    shadowRoot.addEventListener("click", (e) => {
      const chip = e.target.closest(".chip-btn[data-msg]");
      if (chip) {
        sendQuickMessage(chip.dataset.msg);
        return;
      }

      const dropdown = shadowRoot.getElementById("lime-dropdown");
      const menuBtn = shadowRoot.getElementById("lime-menu");
      if (
        dropdown.classList.contains("active") &&
        !dropdown.contains(e.target) &&
        !menuBtn.contains(e.target)
      ) {
        dropdown.classList.remove("active");
      }
    });
  }

  function toggleExpand() {
    const win = shadowRoot.getElementById("lime-window");
    const expandBtn = shadowRoot.getElementById("lime-expand");
    const svg = expandBtn.querySelector("svg");

    win.classList.toggle("expanded");

    if (win.classList.contains("expanded")) {
      expandBtn.title = "Свернуть";
      svg.innerHTML = '<path d="M4 14h6v6M20 10h-6V4M14 10l7-7M3 21l7-7"/>';
    } else {
      expandBtn.title = "Развернуть";
      svg.innerHTML = '<path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"/>';
    }
  }

  function toggleChat() {
    if (!shadowRoot) return;
    const win = shadowRoot.getElementById("lime-window");
    win.classList.toggle("active");

    if (win.classList.contains("active")) {
      const input = shadowRoot.getElementById("lime-input");
      // Небольшая задержка — чтобы фокус ставился уже после начала CSS-перехода открытия
      setTimeout(() => input && input.focus(), 50);
    }
  }

  function sendQuickMessage(text) {
    if (!shadowRoot) return;
    const input = shadowRoot.getElementById("lime-input");
    input.value = text;
    handleSend();
  }

  function setInputEnabled(enabled) {
    const input = shadowRoot.getElementById("lime-input");
    const sendBtn = shadowRoot.getElementById("lime-send");
    input.disabled = !enabled;
    sendBtn.disabled = !enabled;
  }

  async function handleSend() {
    const input = shadowRoot.getElementById("lime-input");
    if (input.disabled) return; // запрос уже выполняется — игнорируем повторные клики/Enter

    const text = input.value.trim().slice(0, MAX_MESSAGE_LENGTH);
    if (!text) return;

    const welcome = shadowRoot.getElementById("lime-welcome");
    if (welcome) welcome.style.display = "none";

    appendMessage(text, "user");
    input.value = "";
    setInputEnabled(false);
    showTyping(true);

    let botReply = "Не удалось получить ответ. Проверьте соединение с сервером.";

    try {
      const res = await fetch(`${config.apiUrl}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });

      const data = await res.json().catch(() => null);

      if (res.ok && data && typeof data.answer === "string") {
        botReply = data.answer || "Получен пустой ответ от сервера.";
      } else if (data && typeof data.detail === "string") {
        // Сервер ответил с ошибкой (400/429 и т.п.) — текст уже безопасен для показа пользователю
        botReply = data.detail;
      } else {
        console.error("LimeAI: неожиданный ответ сервера", res.status);
      }
    } catch (e) {
      console.error("LimeAI: сбой сети при обращении к API", e);
    }

    appendMessage(botReply, "bot");
    showTyping(false);
    setInputEnabled(true);
    input.focus();
  }

  function appendMessage(text, sender, options = {}) {
    const { persist = true } = options;

    const msg = document.createElement("div");
    msg.className = `msg msg-${sender}`;
    msg.innerText = text;

    const container = shadowRoot.getElementById("lime-messages");
    const typing = shadowRoot.getElementById("lime-typing");
    // Вставляем ПЕРЕД индикатором печати, а не в конец — так typing-indicator
    // всегда остаётся последним элементом и появляется под последним сообщением,
    // а не «прилипает» к верху списка.
    container.insertBefore(msg, typing);
    container.scrollTop = container.scrollHeight;

    // При воспроизведении истории (loadHistory) сообщения уже есть в sessionStorage —
    // повторное сохранение здесь удваивало бы историю при каждой перезагрузке страницы.
    if (persist) {
      saveToHistory({ text, sender });
    }
  }

  function showTyping(show) {
    const typing = shadowRoot.getElementById("lime-typing");
    const container = shadowRoot.getElementById("lime-messages");
    typing.style.display = show ? "flex" : "none";
    if (show) container.scrollTop = container.scrollHeight;
  }

  function saveToHistory(item) {
    const history = JSON.parse(
      sessionStorage.getItem("lime_ai_history") || "[]",
    );
    history.push(item);
    sessionStorage.setItem("lime_ai_history", JSON.stringify(history));
  }

  function loadHistory() {
    const history = JSON.parse(
      sessionStorage.getItem("lime_ai_history") || "[]",
    );
    if (history.length > 0) {
      const welcome = shadowRoot.getElementById("lime-welcome");
      if (welcome) welcome.style.display = "none";
      history.forEach((m) => appendMessage(m.text, m.sender, { persist: false }));
    }
  }

  function toggleMenu() {
    const dropdown = shadowRoot.getElementById("lime-dropdown");
    dropdown.classList.toggle("active");
  }

  function clearHistory() {
    if (!shadowRoot) return;

    sessionStorage.removeItem("lime_ai_history");
    const container = shadowRoot.getElementById("lime-messages");
    container.innerHTML = `
        ${welcomeHTML}
        <div class="typing-indicator" id="lime-typing">
            <div class="dot"></div><div class="dot"></div><div class="dot"></div>
        </div>
    `;
    const dropdown = shadowRoot.getElementById("lime-dropdown");
    if (dropdown) dropdown.classList.remove("active");
  }

})();