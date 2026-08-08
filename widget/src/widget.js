(function () {
  let config = { apiUrl: "http://127.0.0.1:8000" };

  window.LimeAI = {
    init: function (options) {
      if (options && options.apiUrl) {
        config.apiUrl = options.apiUrl.replace(/\/$/, "");
      }
      createWidget();
      loadHistory();
    },
    toggleChat: toggleChat,
    clearHistory: clearHistory,
    sendQuickMessage: sendQuickMessage,
  };

  let shadowRoot = null;

  // Сохраняем разметку карточки приветствия с чипсами в константу,
  // чтобы переиспользовать ее при инициализации и при очистке истории
  const welcomeHTML = `
    <div class="welcome-card" id="lime-welcome">
        <h5>Привет! Я AI-ассистент Lime HD TV</h5>
        <p>Готов ответить на вопросы по работе сервиса, подпискам и настройке приложений.</p>
        <div class="chips-wrapper">
            <!-- Основные 2 плитки (видны всегда) -->
            <button class="chip-btn" onclick="window.LimeAI.sendQuickMessage('Как смотреть ТВ бесплатно?')">Смотреть бесплатно</button>
            <button class="chip-btn" onclick="window.LimeAI.sendQuickMessage('На каких устройствах работает Lime HD?')">Поддерживаемые устройства</button>
            
            <!-- Дополнительные плитки (видны только в развернутом окне) -->
            <button class="chip-btn chip-extra" onclick="window.LimeAI.sendQuickMessage('Как отменить подписку?')">Отменить подписку</button>
            <button class="chip-btn chip-extra" onclick="window.LimeAI.sendQuickMessage('Как подключить к Smart TV?')">Настроить Smart TV</button>
            <button class="chip-btn chip-extra" onclick="window.LimeAI.sendQuickMessage('Не работает трансляция')">Ошибки видео</button>
            <button class="chip-btn chip-extra" onclick="window.LimeAI.sendQuickMessage('Где взять промокод?')">Промокоды</button>
            <button class="chip-btn chip-extra" onclick="window.LimeAI.sendQuickMessage('Какие каналы есть в подписке?')">Список каналов</button>
        </div>
    </div>
  `;

  function createWidget() {
    if (document.getElementById("lime-ai-root")) return;

    // Создаем контейнер-хост
    const host = document.createElement("div");
    host.id = "lime-ai-root";
    document.body.appendChild(host);

    // Изолируем стили через Shadow DOM
    shadowRoot = host.attachShadow({ mode: "open" });

    // Подключаем шрифт Inter внутрь Shadow DOM
    const fontLink = document.createElement("link");
    fontLink.rel = "stylesheet";
    fontLink.href = "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Unbounded:wght@600;700;800&display=swap&family=Montserrat:wght@800";
    shadowRoot.appendChild(fontLink);

    // Внедряем стили
    const style = document.createElement("style");
    style.textContent = `
    * {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
        font-family: 'Unbounded', sans-serif;
        font-weight: 600;

        /* font-family: 'Montserrat', -apple-system, sans-serif; */
        /* font-family: 'Roboto', -apple-system, sans-serif; */
    }
    
    :host {

        /* Пастельная палитра */
        --pastel-lime: #D9F99D;         /* Легкий лаймовый */
        --pastel-lime-bg: #F4FCE8;
        --pastel-lime-hover: #ECFDF5;
        
        --pastel-red: #FCA5A5;          /* Легкий красный / коралловый */
        --pastel-red-bg: #FEF2F2;
        
        --pastel-orange: #FDBA74;       /* Легкий оранжевый / персиковый */
        --pastel-orange-bg: #FFF7ED;
        
        --pastel-blue: #BAE6FD;         /* Легкий голубой */
        --pastel-blue-bg: #F0F9FF;
        
        --dark-bg: #1E293B;             /* Мягкий графитовый текст вместо жесткого черного */
        --border-light: rgba(255, 255, 255, 0.9);

        /* Тени и нежное свечение при фокусе/ховере */
        --shadow-tile: 
            0 12px 28px -6px rgba(15, 23, 42, 0.06),
            0 4px 10px -2px rgba(15, 23, 42, 0.04),
            inset 0 1px 2px rgba(255, 255, 255, 0.95);

        --shadow-hover-lime: 
            0 16px 32px -8px rgba(15, 23, 42, 0.1),
            0 0 16px rgba(217, 249, 157, 0.6), /* Нежное лаймовое свечение */
            inset 0 1px 2px rgba(255, 255, 255, 1);
            
        --shadow-hover-orange: 
            0 16px 32px -8px rgba(15, 23, 42, 0.1),
            0 0 16px rgba(253, 186, 116, 0.5), /* Нежное оранжевое свечение */
            inset 0 1px 2px rgba(255, 255, 255, 1);

        --lime-green: #6BB023;
        --lime-hover: #78C427;
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
    }

    /* Базовый стиль для всех плиток виджета */
    .tile {
        background: linear-gradient(145deg, #f8fafc 0%, #e2e8f0 100%);
        border: 1px solid var(--border-light);
        border-radius: 20px;
        box-shadow: var(--shadow-tile);
        transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1),
                    box-shadow 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    }

    /* Кнопка вызова чата в стиле плиток с акцентным шрифтом Unbounded */
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
        fill: #4D8B12; /* Более глубокий зеленый для хорошей контрастности */
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
    
    /* Прозрачный контейнер сетки чата (без собственного фона) */
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

    /* --- ВЕРХНИЙ РЯД: Шапка из отдельных плиток --- */
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

    /* Выпадающее меню */
    .menu-dropdown {
        position: absolute;
        top: 52px;
        right: 44px; /* Позиционирование ровно под кнопкой 3 точек */
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

    /* Плитка-кнопка внутри выпадающего меню */
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
        color: #EF4444; /* Акцентный красный цвет */
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

    /* --- СРЕДНЯЯ ОБЛАСТЬ: Плитка сообщений --- */
    .tile-messages {
        flex: 1;
        padding: 20px;
        overflow-y: auto;
        display: flex;
        flex-direction: column;
        gap: 14px;
    }

    /* --- НИЖНИЙ РЯД: Ввод текста и отправка --- */
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

    /* Легкий пастельный фокус при клике на поле ввода */
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

    .tile-send svg {
        width: 20px;
        height: 20px;
        stroke: currentColor;
        stroke-width: 2;
        fill: none;
        stroke-linecap: round;
        stroke-linejoin: round;
    }

    /* --- Стили сообщений и чипсов --- */
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
    
    /*
    .chips-wrapper { display: flex; flex-direction: column; gap: 6px; }
    .chip-btn {
        background: #F8FAFC; border: 1px solid rgba(15, 15, 15, 0.08);
        border-radius: 10px; padding: 8px 12px; font-size: 12px; font-weight: 500;
        color: var(--dark-bg); text-align: left; cursor: pointer; transition: all 0.2s ease;
    }
    .chip-btn:hover { border-color: var(--lime-green); background: #F4FCE8; transform: translateX(2px); }
    */
   
   .chips-wrapper { 
        display: flex; 
        flex-wrap: wrap; /* Позволяем перенос на новую строку */
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
        width: fit-content; /* Заполнение строго по ширине текста */
        white-space: nowrap; /* Чтобы текст не разрывался на несколько строк */
    }
    .chip-btn:hover { 
        border-color: var(--pastel-lime); 
        background: var(--pastel-lime-bg); 
        transform: translateY(-1px) translateX(2px); 
        box-shadow: 0 4px 10px rgba(107, 176, 35, 0.12);
    }
    
    /* Дополнительные чипсы скрыты по умолчанию */
    .chip-extra {
        display: none;
    }

    /* Когда окно получает класс expanded - показываем дополнительные чипсы */
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

    /* Сообщение пользователя: тёмный объёмный парящий блок */
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

    /* Сообщение бота: белоснежный чистый парящий блок */
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

    /* Индикатор набора текста */
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


        /* --- Индивидуальные цвета для кнопок шапки --- */
    
    /* Кнопка разворота (пастельно-зеленый) */
    #lime-expand {
        background: var(--pastel-lime-bg);
        border: 1px solid var(--pastel-lime);
    }
    #lime-expand:hover {
        background: var(--pastel-lime);
        box-shadow: var(--shadow-hover-lime);
    }

    /* Кнопка меню (пастельно-голубой) */
    #lime-menu {
        background: var(--pastel-blue-bg);
        border: 1px solid var(--pastel-blue);
    }
    #lime-menu:hover {
        background: var(--pastel-blue);
        /* Добавляем легкое голубое свечение по аналогии с остальными */
        box-shadow: 0 16px 32px -8px rgba(15, 23, 42, 0.1), 0 0 16px rgba(186, 230, 253, 0.5), inset 0 1px 2px rgba(255, 255, 255, 1);
    }

    /* Кнопка закрытия (пастельно-красный) */
    #lime-close {
        background: var(--pastel-red-bg);
        border: 1px solid var(--pastel-red);
    }
    #lime-close:hover {
        background: var(--pastel-red);
        /* Добавляем легкое красное свечение */
        box-shadow: 0 16px 32px -8px rgba(15, 23, 42, 0.1), 0 0 16px rgba(252, 165, 165, 0.5), inset 0 1px 2px rgba(255, 255, 255, 1);
    }

    /* Мобильная адаптивность */
    @media (max-width: 600px) {
        .chat-window { width: calc(100vw - 32px); right: 16px; bottom: 84px; height: 75vh; }
        .launcher-btn { bottom: 16px; right: 16px; }
        .expand-btn { display: none; }
    }
`;

    // Разметка с чистыми SVG без эмодзи
    const container = document.createElement("div");
    container.innerHTML = `
    <!-- Плиточная кнопка вызова чата -->
    <button class="launcher-btn" id="lime-launcher" aria-label="Обратная связь" title="Чат поддержки">
        <svg viewBox="0 0 24 24">
            <path d="M20 2H4c-1.1 0-1.99.9-1.99 2L2 22l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zM6 9h12v2H6V9zm8 5H6v-2h8v2zm4-6H6V6h12v2z"/>
        </svg>
        <span>Задать вопрос</span>
    </button>

    <!-- Окно чата из независимых плиток -->
    <div class="chat-window" id="lime-window">
        
        <!-- 1. Верхний ряд плиток -->
        <div class="header-grid">
            <div class="tile tile-brand">
                <span class="brand-title">LIME HD SUPPORT</span>
                <div class="status-indicator">
                    <span class="status-dot"></span>
                    <span>Онлайн</span>
                </div>
            </div>
            
            <!-- Плитка: Развернуть (SVG) -->
            <button class="tile tile-btn expand-btn" id="lime-expand" title="Развернуть">
                <svg id="svg-expand" viewBox="0 0 24 24">
                    <path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"/>
                </svg>
            </button>

            <!-- Плитка: Меню / Очистить чат (SVG - 3 точки) -->
            <button class="tile tile-btn" id="lime-menu" title="Очистить историю">
                <svg viewBox="0 0 24 24">
                    <circle cx="12" cy="6" r="1.5" fill="currentColor"/>
                    <circle cx="12" cy="12" r="1.5" fill="currentColor"/>
                    <circle cx="12" cy="18" r="1.5" fill="currentColor"/>
                </svg>
            </button>

            <!-- Выпадающее меню с одной плиткой удаления -->
            <div class="menu-dropdown" id="lime-dropdown">
                <button class="dropdown-item" id="lime-clear-all">
                    <svg viewBox="0 0 24 24">
                        <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2M10 11v6M14 11v6"/>
                    </svg>
                    <span>Очистить историю</span>
                </button>
            </div>

            <!-- Плитка: Закрыть (SVG - крестик) -->
            <button class="tile tile-btn" id="lime-close" title="Закрыть">
                <svg viewBox="0 0 24 24">
                    <path d="M18 6L6 18M6 6l12 12"/>
                </svg>
            </button>
        </div>

        <!-- 2. Средняя большая плитка: История чата -->
        <div class="tile tile-messages" id="lime-messages">
            ${welcomeHTML}
            <div class="typing-indicator" id="lime-typing">
                <div class="dot"></div><div class="dot"></div><div class="dot"></div>
            </div>
        </div>

        <!-- 3. Нижний ряд плиток: Ввод + Отправка -->
        <div class="input-grid">
            <div class="tile tile-input-box">
                <input type="text" class="chat-input" id="lime-input" placeholder="Задайте вопрос..." autocomplete="off" />
            </div>
            
            <!-- Плитка: Отправить (SVG) -->
            <button class="tile tile-send" id="lime-send" title="Отправить">
                <svg viewBox="0 0 24 24">
                    <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/>
                </svg>
            </button>
        </div>

    </div>
`;

    shadowRoot.appendChild(style);
    shadowRoot.appendChild(container);

    // Обработчики событий
    shadowRoot.getElementById("lime-launcher").onclick = toggleChat;
    shadowRoot.getElementById("lime-close").onclick = toggleChat;
    shadowRoot.getElementById("lime-menu").onclick = toggleMenu;
    shadowRoot.getElementById("lime-clear-all").onclick = clearHistory;
    shadowRoot.getElementById("lime-send").onclick = handleSend;
    shadowRoot.getElementById("lime-input").onkeypress = (e) => {
      if (e.key === "Enter") handleSend();
    };
    shadowRoot.getElementById("lime-expand").onclick = toggleExpand;
  }

  function toggleExpand() {
    const win = shadowRoot.getElementById("lime-window");
    const expandBtn = shadowRoot.getElementById("lime-expand");
    const svg = expandBtn.querySelector("svg");

    win.classList.toggle("expanded");

    if (win.classList.contains("expanded")) {
      expandBtn.title = "Свернуть";
      // Иконка сжатия углов внутрь
      svg.innerHTML = '<path d="M4 14h6v6M20 10h-6V4M14 10l7-7M3 21l7-7"/>';
    } else {
      expandBtn.title = "Развернуть";
      // Иконка расширения углов наружу
      svg.innerHTML = '<path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"/>';
    }
  }

  function toggleChat() {
    const win = shadowRoot.getElementById("lime-window");
    win.classList.toggle("active");
  }

  function sendQuickMessage(text) {
    const input = shadowRoot.getElementById("lime-input");
    input.value = text;
    handleSend();
  }

  async function handleSend() {
    const input = shadowRoot.getElementById("lime-input");
    const text = input.value.trim();
    if (!text) return;

    // Прячем приветственный блок
    const welcome = shadowRoot.getElementById("lime-welcome");
    if (welcome) welcome.style.display = "none";

    appendMessage(text, "user");
    input.value = "";
    showTyping(true);

    try {
      const res = await fetch(`${config.apiUrl}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });

      if (!res.ok) throw new Error("Ошибка сервера");
      const data = await res.json();
      appendMessage(data.answer || "Получен пустой ответ от сервера.", "bot");
    } catch (e) {
      appendMessage(
        "Не удалось получить ответ. Проверьте соединение с сервером.",
        "bot",
      );
    } finally {
      showTyping(false);
    }
  }

  function appendMessage(text, sender) {
    const msg = document.createElement("div");
    msg.className = `msg msg-${sender}`;
    msg.innerText = text;

    const container = shadowRoot.getElementById("lime-messages");
    container.appendChild(msg);
    container.scrollTop = container.scrollHeight;

    saveToHistory({ text, sender });
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
      history.forEach((m) => appendMessage(m.text, m.sender));
    }
  }

  function toggleMenu() {
    const dropdown = shadowRoot.getElementById("lime-dropdown");
    dropdown.classList.toggle("active");
  }

  function clearHistory() {
    sessionStorage.removeItem("lime_ai_history");
    const container = shadowRoot.getElementById("lime-messages");
    container.innerHTML = `
        ${welcomeHTML}
        <div class="typing-indicator" id="lime-typing">
            <div class="dot"></div><div class="dot"></div><div class="dot"></div>
        </div>
    `; // Переиспользуем нашу HTML константу при очистке, чтобы вернуть чипсы на место
    const dropdown = shadowRoot.getElementById("lime-dropdown");
    if (dropdown) dropdown.classList.remove("active");
  }
  
})();
