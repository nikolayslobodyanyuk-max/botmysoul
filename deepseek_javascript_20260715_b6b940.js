// Инициализация Telegram WebApp
const tg = window.Telegram.WebApp;
tg.expand();

// Получение данных пользователя
const user = tg.initDataUnsafe?.user || { id: 'unknown', first_name: 'Гость' };
const userId = user.id;
const userName = user.first_name;

// DOM элементы
const statusText = document.getElementById('statusText');
const findBtn = document.getElementById('findBtn');
const nextBtn = document.getElementById('nextBtn');
const stopBtn = document.getElementById('stopBtn');
const chatArea = document.getElementById('chatArea');
const messages = document.getElementById('messages');
const msgInput = document.getElementById('msgInput');
const sendBtn = document.getElementById('sendBtn');

// Состояние
let isInChat = false;
let isWaiting = false;
let messageQueue = [];

// Отправка данных в бота
function sendToBot(action, data = {}) {
    const payload = {
        action: action,
        userId: userId,
        userName: userName,
        ...data
    };
    tg.sendData(JSON.stringify(payload));
}

// Обновление интерфейса
function updateUI(status, inChat, waiting = false) {
    isInChat = inChat;
    isWaiting = waiting;
    
    statusText.textContent = status;
    
    if (inChat) {
        findBtn.classList.add('hidden');
        nextBtn.classList.remove('hidden');
        stopBtn.classList.remove('hidden');
        chatArea.classList.remove('hidden');
        findBtn.disabled = false;
    } else {
        findBtn.classList.remove('hidden');
        nextBtn.classList.add('hidden');
        stopBtn.classList.add('hidden');
        chatArea.classList.add('hidden');
        findBtn.disabled = false;
    }
    
    if (waiting) {
        findBtn.disabled = true;
        findBtn.textContent = '⏳ Поиск...';
    } else {
        findBtn.textContent = '🔍 Найти собеседника';
    }
}

// Добавление сообщения
function addMessage(text, type = 'incoming') {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${type}`;
    msgDiv.textContent = text;
    messages.appendChild(msgDiv);
    messages.scrollTop = messages.scrollHeight;
}

// Добавление системного сообщения
function addSystemMessage(text) {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message system';
    msgDiv.textContent = text;
    messages.appendChild(msgDiv);
    messages.scrollTop = messages.scrollHeight;
}

// Очистка чата
function clearChat() {
    messages.innerHTML = '';
}

// Обработка данных из бота
tg.onEvent('message', (data) => {
    try {
        const parsed = JSON.parse(data);
        console.log('Получено от бота:', parsed);
        
        switch (parsed.action) {
            case 'chat_started':
                updateUI('✅ Собеседник найден!', true);
                clearChat();
                if (parsed.message) {
                    addSystemMessage('🎉 ' + parsed.message);
                }
                break;
                
            case 'chat_ended':
                updateUI('👋 Диалог завершен', false);
                clearChat();
                if (parsed.text) {
                    addSystemMessage(parsed.text);
                }
                break;
                
            case 'partner_left':
                updateUI('👋 Собеседник вышел', false);
                clearChat();
                if (parsed.text) {
                    addSystemMessage(parsed.text);
                }
                break;
                
            case 'waiting':
                updateUI('⏳ ' + parsed.text, false, true);
                break;
                
            case 'new_message':
                if (isInChat) {
                    addMessage(parsed.text, 'incoming');
                }
                break;
                
            case 'message_sent':
                // Сообщение уже добавлено локально
                break;
                
            case 'error':
                statusText.textContent = '❌ ' + parsed.text;
                findBtn.disabled = false;
                break;
                
            case 'status':
                // Обновление статуса
                break;
                
            default:
                console.log('Неизвестное действие:', parsed.action);
        }
    } catch (e) {
        console.error('Ошибка парсинга:', e);
    }
});

// Обработчики кнопок
findBtn.addEventListener('click', () => {
    sendToBot('find');
    statusText.textContent = '🔍 Ищем собеседника...';
    findBtn.disabled = true;
});

nextBtn.addEventListener('click', () => {
    sendToBot('next');
    statusText.textContent = '🔍 Ищем нового...';
    clearChat();
    addSystemMessage('⏳ Ищем нового собеседника...');
});

stopBtn.addEventListener('click', () => {
    sendToBot('stop');
    updateUI('👋 Завершаем...', false);
    clearChat();
    addSystemMessage('👋 Диалог завершен');
});

sendBtn.addEventListener('click', () => {
    const text = msgInput.value.trim();
    if (text && isInChat) {
        sendToBot('message', { text: text });
        addMessage(text, 'outgoing');
        msgInput.value = '';
        msgInput.style.height = 'auto';
    }
});

msgInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendBtn.click();
    }
});

// Автоматическое изменение высоты textarea
msgInput.addEventListener('input', () => {
    msgInput.style.height = 'auto';
    msgInput.style.height = msgInput.scrollHeight + 'px';
});

// Запрос статуса при открытии
setTimeout(() => {
    sendToBot('get_status');
}, 500);

// Обработка закрытия
tg.onEvent('close', () => {
    console.log('Приложение закрыто');
});

// Готовность
tg.ready();
console.log('Mini App готов к работе!');
console.log('Пользователь:', userId, userName);