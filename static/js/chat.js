const chatLog = document.getElementById("chat-log");
const chatForm = document.getElementById("chat-form");
const messageInput = document.getElementById("message");
const sendButton = document.getElementById("send-btn");
const counter = document.getElementById("counter");
const newChatBtn = document.getElementById("new-chat-btn");
const maxLength = Number(window.APP_CONFIG?.maxLength || 500);
const sessionStorageKey = "dfds-it-support-session-id";
const thinkingPhrases = [
	"Thinking",
	"Reviewing internal knowledge",
    "Searching for similar issues",
	"Checking related tickets",
	"Cross-referencing known fixes",
    "Analyzing the issue",
	"Preparing the best answer",
    "Almost there"
];

function startNewChat() {
	window.localStorage.removeItem(sessionStorageKey);
	const oldSessionId = getSessionId();
	const oldChatHistoryKey = `chat-history-${oldSessionId}`;
	window.localStorage.removeItem(oldChatHistoryKey);

	chatLog.innerHTML = "";
	messageInput.value = "";
	updateCounter();
	
	const newSessionId = window.crypto?.randomUUID
		? window.crypto.randomUUID()
		: `session-${Date.now()}-${Math.random().toString(16).slice(2)}`;
	window.localStorage.setItem(sessionStorageKey, newSessionId);
	messageInput.focus();
	appendMessage("Hello! I'm ready to help with IT requests.", "bot");
}

function getChatHistoryKey() {
	return `chat-history-${getSessionId()}`;
}

function saveChatMessage(text, kind) {
	const historyKey = getChatHistoryKey();
	let history = [];
	
	const stored = window.localStorage.getItem(historyKey);
	if (stored) {
		try {
			history = JSON.parse(stored);
		} catch {
			history = [];
		}
	}
	
	history.push({ text, kind, timestamp: Date.now() });
	window.localStorage.setItem(historyKey, JSON.stringify(history));
}

function loadChatHistory() {
	const historyKey = getChatHistoryKey();
	const stored = window.localStorage.getItem(historyKey);
	
	if (!stored) {
		return;
	}
	
	try {
		const history = JSON.parse(stored);
		for (const { text, kind } of history) {
			appendMessage(text, kind, { persist: false });
		}
	} catch {
		console.error("Failed to load chat history");
	}
}

function getSessionId() {
	const storedSessionId = window.localStorage.getItem(sessionStorageKey);

	if (storedSessionId) {
		return storedSessionId;
	}

	const generatedSessionId = window.crypto?.randomUUID
		? window.crypto.randomUUID()
		: `session-${Date.now()}-${Math.random().toString(16).slice(2)}`;

	window.localStorage.setItem(sessionStorageKey, generatedSessionId);
	return generatedSessionId;
}

function appendMessage(text, kind, options = {}) {
	const { persist = true } = options;
	
	const node = document.createElement("article");
	node.className = `msg msg-${kind}`;
	node.textContent = text;
	chatLog.appendChild(node);
	chatLog.scrollTop = chatLog.scrollHeight;
	
	if (persist) {
		saveChatMessage(text, kind);
	}
	
	return node;
}

function updateCounter() {
	counter.textContent = `${messageInput.value.length} / ${maxLength}`;
}

function setBusy(isBusy) {
	sendButton.disabled = isBusy;
	messageInput.disabled = isBusy;
}

function startThinkingMessage() {
	const loadingNode = appendMessage(thinkingPhrases[0], "bot", { persist: false });
	loadingNode.classList.add("is-thinking");
	let phraseIndex = 0;

	const intervalId = window.setInterval(() => {
		phraseIndex = (phraseIndex + 1) % thinkingPhrases.length;
		loadingNode.style.opacity = "0.45";

		window.setTimeout(() => {
			loadingNode.textContent = thinkingPhrases[phraseIndex];
			loadingNode.style.opacity = "1";
		}, 320);
	}, 3200);

	return {
		node: loadingNode,
		stop: () => window.clearInterval(intervalId)
	};
}

chatForm.addEventListener("submit", async (event) => {
	event.preventDefault();
	const chatInput = messageInput.value.trim();

	if (!chatInput) {
		appendMessage("Please enter a message before sending.", "system");
		return;
	}

	if (chatInput.length > maxLength) {
		appendMessage(`Message is too long. Limit: ${maxLength} characters.`, "system");
		return;
	}

	appendMessage(chatInput, "user");
	messageInput.value = "";
	updateCounter();

	const thinking = startThinkingMessage();
	setBusy(true);

	try {
		const response = await fetch("/api/chat", {
			method: "POST",
			headers: {
				"Content-Type": "application/json"
			},
			body: JSON.stringify({
				chatInput,
				sessionId: getSessionId()
			})
		});

		const payload = await response.json();
		thinking.stop();
		thinking.node.remove();

		if (!response.ok) {
			appendMessage(payload.error || "An error occurred while processing your request.", "system");
			return;
		}

		appendMessage(payload.reply || "The bot returned an empty response.", "bot");
	} catch (error) {
		thinking.stop();
		thinking.node.remove();
		appendMessage("Network error. Check your connection and the server availability.", "system");
	} finally {
		thinking.stop();
		setBusy(false);
		messageInput.focus();
	}
});

messageInput.addEventListener("input", updateCounter);

messageInput.addEventListener("keydown", (event) => {
	if (event.key === "Enter" && !event.shiftKey) {
		event.preventDefault();
		chatForm.requestSubmit();
	}
});

newChatBtn.addEventListener("click", (event) => {
	event.preventDefault();
	startNewChat();
});

// Load previous chat history and ensure greeting is added if none exists
loadChatHistory();
if (chatLog.children.length === 0) {
	appendMessage("Hello! I'm ready to help with IT requests.", "bot");
}
updateCounter();
