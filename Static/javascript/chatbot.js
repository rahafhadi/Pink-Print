
document.addEventListener('DOMContentLoaded', async () => {
    const chatMessages = document.getElementById('chatMessages');
    const chatForm = document.getElementById('chatForm');
    const chatInput = document.getElementById('chatInput');
    const suggestedContainer = document.getElementById('suggestedPillsContainer');
    const toggleSuggestionsBtn = document.getElementById('toggleSuggestionsBtn');
    const clearChatBtn = document.getElementById('clearChatBtn');

    // Patient data consent elements
    const patientDataConsentCheckbox = document.getElementById(
        'patientDataConsentCheckbox'
    );
    const consentStatus = document.getElementById('consentStatus');
    const consentPanel = document.getElementById('patientDataConsent');

    // Conversation history elements
    const historyBtn = document.getElementById('conversationHistoryBtn');
    const historyDropdown = document.getElementById('conversationHistoryDropdown');
    const conversationList = document.getElementById('conversationList');

    let currentConversationId = null;
    let isSending = false;
    let savedConsent = false;
    let consentLoaded = false;
    let isSavingConsent = false;

    // Preserve the welcome message
    const welcomeMessage = chatMessages.firstElementChild
        ? chatMessages.firstElementChild.cloneNode(true)
        : null;

    // Backend API request
    async function apiRequest(url, options = {}) {
        const response = await fetch(url, {
            credentials: 'same-origin',
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'حدث خطأ في الاتصال');
        }

        return data;
    }

    // -------------------------------
    // Patient data consent management
    // -------------------------------

    async function loadPatientDataConsent() {
        if (!patientDataConsentCheckbox || !consentStatus) {
            return;
        }

        patientDataConsentCheckbox.disabled = true;

        try {
            const data = await apiRequest(
                '/api/chat/patient-data-consent'
            );

            savedConsent = data.consent === true;
            consentLoaded = true;

            patientDataConsentCheckbox.checked = savedConsent;
            patientDataConsentCheckbox.disabled = false;

            // Hide the consent panel if consent is already active
            if (consentPanel) {
                consentPanel.hidden = savedConsent;
            }

            consentStatus.textContent = savedConsent
                ? 'الموافقة مفعّلة.'
                : 'استخدام البيانات الشخصية غير مفعّل.';

        } catch (error) {
            console.error('Consent loading error:', error);

            consentStatus.textContent =
                'تعذر تحميل حالة الموافقة. حاولي تحديث الصفحة.';

            patientDataConsentCheckbox.checked = false;
            patientDataConsentCheckbox.disabled = true;

            // Keep the consent panel visible if loading fails
            if (consentPanel) {
                consentPanel.hidden = false;
            }
        }
    }

    async function savePatientDataConsent() {
        if (
            !patientDataConsentCheckbox ||
            !consentStatus ||
            !consentLoaded ||
            isSavingConsent
        ) {
            return;
        }

        const newConsent = patientDataConsentCheckbox.checked;

        isSavingConsent = true;
        patientDataConsentCheckbox.disabled = true;

        consentStatus.textContent = 'جارٍ حفظ التغيير...';

        try {
            const data = await apiRequest(
                '/api/chat/patient-data-consent',
                {
                    method: 'POST',
                    body: JSON.stringify({
                        consent: newConsent
                    })
                }
            );

            savedConsent = data.consent === true;
            patientDataConsentCheckbox.checked = savedConsent;

            // Hide the panel only after successful server confirmation
            if (consentPanel) {
                consentPanel.hidden = savedConsent;
            }

            consentStatus.textContent = savedConsent
                ? 'الموافقة مفعّلة.'
                : 'تم إيقاف استخدام البيانات الشخصية.';

        } catch (error) {
            console.error('Consent saving error:', error);

            // Restore the last confirmed server value
            patientDataConsentCheckbox.checked = savedConsent;

            consentStatus.textContent =
                'تعذر حفظ التغيير. لم تتغير حالة الموافقة المحفوظة.';

        } finally {
            isSavingConsent = false;
            patientDataConsentCheckbox.disabled = false;
        }
    }

    if (patientDataConsentCheckbox) {
        // Prevent changing consent before loading its saved value
        patientDataConsentCheckbox.disabled = true;

        patientDataConsentCheckbox.addEventListener(
            'change',
            savePatientDataConsent
        );
    }

    // -------------------------------
    // General UI helpers
    // -------------------------------

    function getCurrentTime() {
        return new Date().toLocaleTimeString('ar-EG', {
            hour: 'numeric',
            minute: '2-digit'
        });
    }

    function formatDate(dateString) {
        if (!dateString) return '';

        const date = new Date(dateString.replace(' ', 'T'));

        if (isNaN(date.getTime())) return '';

        return date.toLocaleDateString('ar-EG', {
            day: 'numeric',
            month: 'short'
        });
    }

    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function resetMessages() {
        chatMessages.innerHTML = '';

        if (welcomeMessage) {
            chatMessages.appendChild(welcomeMessage.cloneNode(true));
        }
    }

    // -------------------------------
    // Message rendering
    // -------------------------------

    function appendUserMessage(text) {
        const row = document.createElement('div');
        row.className = 'msg-row user';

        const bubble = document.createElement('div');
        bubble.className = 'msg-bubble';

        const paragraph = document.createElement('p');
        paragraph.textContent = text;

        const time = document.createElement('span');
        time.className = 'msg-time';
        time.textContent = getCurrentTime();

        bubble.append(paragraph, time);
        row.appendChild(bubble);
        chatMessages.appendChild(row);

        scrollToBottom();

        const welcomeSuggestions =
            chatMessages.querySelector('.welcome-suggestions');

        if (welcomeSuggestions) {
            welcomeSuggestions.remove();
        }
    }

    function appendBotMessage(text) {
        const row = document.createElement('div');
        row.className = 'msg-row bot';

        const bubble = document.createElement('div');
        bubble.className = 'msg-bubble';

        const content = document.createElement('div');
        content.className = 'markdown-body';

        const markdownText = String(text ?? '');

        const cleanedMarkdown = markdownText.replace(
            /(?:^|\n)\s*#{0,6}\s*(?:\*\*)?المراجع المستخدمة(?:\*\*)?\s*:?[ \t]*\n[\s\S]*$/i,
            ''
        ).trim();

        const renderedHTML = marked.parse(cleanedMarkdown, {
            gfm: true,
            breaks: true
        });

        content.innerHTML = DOMPurify.sanitize(renderedHTML, {
            USE_PROFILES: { html: true }
        });

        bubble.appendChild(content);
        row.appendChild(bubble);

        chatMessages.appendChild(row);
        scrollToBottom();
    }

    // -------------------------------
    // Typing indicator
    // -------------------------------

    let typingIndicator = null;

    function showLoadingIndicator() {
        if (typingIndicator) return;

        typingIndicator = document.createElement('div');
        typingIndicator.className = 'typing-indicator-row';

        typingIndicator.innerHTML = `
            <div class="typing-bubble">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;

        chatMessages.appendChild(typingIndicator);
        scrollToBottom();
    }

    function hideLoadingIndicator() {
        if (typingIndicator) {
            typingIndicator.remove();
            typingIndicator = null;
        }
    }

    // -------------------------------
    // Conversation history dropdown
    // -------------------------------

    function closeHistoryDropdown() {
        if (!historyDropdown || !historyBtn) return;

        historyDropdown.hidden = true;
        historyBtn.setAttribute('aria-expanded', 'false');
    }

    if (historyBtn && historyDropdown) {
        historyBtn.addEventListener('click', async (event) => {
            event.stopPropagation();

            const isOpen = !historyDropdown.hidden;

            if (isOpen) {
                closeHistoryDropdown();
                return;
            }

            historyDropdown.hidden = false;
            historyBtn.setAttribute('aria-expanded', 'true');

            await loadConversations();
        });

        document.addEventListener('click', (event) => {
            if (
                !historyDropdown.contains(event.target) &&
                !historyBtn.contains(event.target)
            ) {
                closeHistoryDropdown();
            }
        });

        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') {
                closeHistoryDropdown();
            }
        });
    }

    // -------------------------------
    // Load conversations
    // -------------------------------

    async function loadConversations() {
        if (!conversationList) return;

        try {
            const conversations = await apiRequest(
                '/api/chat/conversations'
            );

            conversationList.innerHTML = '';

            if (conversations.length === 0) {
                const emptyMessage = document.createElement('div');
                emptyMessage.className = 'conversation-empty';
                emptyMessage.textContent = 'لا توجد محادثات سابقة';

                conversationList.appendChild(emptyMessage);
                return;
            }

            conversations.forEach(conversation => {
                const item = document.createElement('button');
                item.type = 'button';
                item.className = 'conversation-item';

                if (conversation.id === currentConversationId) {
                    item.classList.add('active');
                }

                const title = document.createElement('div');
                title.textContent =
                    conversation.preview ||
                    conversation.title ||
                    'محادثة جديدة';

                const date = document.createElement('small');
                date.textContent = formatDate(conversation.updated_at);

                item.append(title, date);

                item.addEventListener('click', async () => {
                    if (isSending) return;

                    try {
                        await openConversation(conversation.id);
                    } catch (error) {
                        console.error('Load conversation error:', error);
                        alert('تعذر تحميل المحادثة.');
                    }
                });

                conversationList.appendChild(item);
            });

        } catch (error) {
            console.error('Conversation list error:', error);

            conversationList.innerHTML = '';

            const errorMessage = document.createElement('div');
            errorMessage.className = 'conversation-empty';
            errorMessage.textContent = 'تعذر تحميل المحادثات';

            conversationList.appendChild(errorMessage);
        }
    }

    // -------------------------------
    // Create a new conversation
    // -------------------------------

    async function createConversation() {
        const data = await apiRequest('/api/chat/conversations', {
            method: 'POST',
            body: JSON.stringify({})
        });

        currentConversationId = data.conversation_id;

        await loadConversations();
    }

    // -------------------------------
    // Load conversation messages
    // -------------------------------

    async function loadMessages() {
        const messages = await apiRequest(
            `/api/chat/conversations/${currentConversationId}/messages`
        );

        resetMessages();

        messages.forEach(message => {
            if (message.role === 'user') {
                appendUserMessage(message.content);
            } else {
                appendBotMessage(message.content);
            }
        });
    }

    // -------------------------------
    // Open an old conversation
    // -------------------------------

    async function openConversation(conversationId) {
        currentConversationId = conversationId;

        await loadMessages();

        chatInput.value = '';
        closeHistoryDropdown();
        await loadConversations();
    }

    // -------------------------------
    // Initialize chat
    // -------------------------------

    async function initializeChat() {
        const conversations = await apiRequest(
            '/api/chat/conversations'
        );

        if (conversations.length > 0) {
            currentConversationId = conversations[0].id;
            await loadMessages();
        } else {
            await createConversation();
        }

        await loadConversations();
    }

    // -------------------------------
    // Send a message
    // -------------------------------

    async function sendMessage(text) {
        if (!text || isSending) return;

        isSending = true;
        chatInput.disabled = true;
        showLoadingIndicator();

        try {
            if (!currentConversationId) {
                await createConversation();
            }

            appendUserMessage(text);
            chatInput.value = '';

            const data = await apiRequest(
                `/api/chat/conversations/${currentConversationId}/messages`,
                {
                    method: 'POST',
                    body: JSON.stringify({
                        content: text
                    })
                }
            );

            hideLoadingIndicator();

            if (data.answer) {
                appendBotMessage(data.answer);
            } else {
                appendBotMessage(
                    'وصلت الرسالة، لكن لم يصل رد من المساعد.'
                );
            }

            await loadConversations();

        } catch (error) {
            hideLoadingIndicator();

            appendBotMessage(
                error.message ||
                'حدث خطأ أثناء إرسال الرسالة. حاولي مرة أخرى.'
            );

            console.error('Chat error:', error);

        } finally {
            hideLoadingIndicator();
            isSending = false;
            chatInput.disabled = false;
            chatInput.focus();
        }
    }

    // -------------------------------
    // Chat form submission
    // -------------------------------

    chatForm.addEventListener('submit', event => {
        event.preventDefault();
        sendMessage(chatInput.value.trim());
    });

    // -------------------------------
    // Suggested questions
    // -------------------------------

    document.querySelectorAll('.suggested-pill').forEach(pill => {
        pill.addEventListener('click', () => {
            const question =
                pill.getAttribute('data-title') ||
                pill.innerText.trim();

            sendMessage(question);
        });
    });

    // -------------------------------
    // Toggle suggested questions
    // -------------------------------

    if (toggleSuggestionsBtn && suggestedContainer) {
        toggleSuggestionsBtn.addEventListener('click', () => {
            const hidden = suggestedContainer.style.display === 'none';

            suggestedContainer.style.display = hidden ? 'flex' : 'none';

            toggleSuggestionsBtn.textContent = hidden
                ? 'إخفاء المقترحات'
                : 'عرض المقترحات';
        });
    }

    // -------------------------------
    // Start a new conversation
    // -------------------------------

    if (clearChatBtn) {
        clearChatBtn.addEventListener('click', async () => {
            if (isSending) return;

            if (!confirm('هل تريدين بدء محادثة جديدة؟')) return;

            clearChatBtn.disabled = true;

            try {
                await createConversation();

                resetMessages();
                chatInput.value = '';
                closeHistoryDropdown();
                chatInput.focus();

            } catch (error) {
                console.error('New conversation error:', error);
                alert('تعذر إنشاء محادثة جديدة.');

            } finally {
                clearChatBtn.disabled = false;
            }
        });
    }

    // -------------------------------
    // Start application
    // -------------------------------

    try {
        // Load the saved consent state before enabling the checkbox
        await loadPatientDataConsent();

        // Initialize the chat
        await initializeChat();

    } catch (error) {
        console.error('Chat initialization error:', error);

        appendBotMessage(
            'تعذر تحميل المحادثات. تأكدي من تسجيل الدخول وحاولي مجددًا.'
        );
    }
});
