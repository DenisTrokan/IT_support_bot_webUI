const chatLog = document.getElementById("chat-log");
const chatForm = document.getElementById("chat-form");
const messageInput = document.getElementById("message");
const sendButton = document.getElementById("send-btn");
const counter = document.getElementById("counter");
const newChatBtn = document.getElementById("new-chat-btn");
const emptyState = document.getElementById("empty-state");
const quickActionButtons = document.querySelectorAll(".quick-action-btn");
const chatHeader = document.querySelector(".chat-header");
const headerToggleBtn = document.getElementById("header-toggle-btn");
const headerToggleLabel = document.getElementById("header-toggle-label");
const maxLength = Number(window.APP_CONFIG?.maxLength || 500);
const sessionStorageKey = "dfds-it-support-session-id";
const headerExpandedStorageKey = "dfds-it-support-header-expanded";
const headerDesktopMinWidth = 1001;
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
	if (emptyState) {
		chatLog.appendChild(emptyState);
	}
	messageInput.value = "";
	updateCounter();
	autoResizeMessageInput();
	
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
	refreshEmptyState();
	
	if (persist) {
		saveChatMessage(text, kind);
	}
	
	return node;
}

function updateCounter() {
	counter.textContent = `${messageInput.value.length} / ${maxLength}`;
}

function autoResizeMessageInput() {
	messageInput.style.height = "auto";
	messageInput.style.height = `${Math.min(messageInput.scrollHeight, 180)}px`;
}

function refreshEmptyState() {
	if (!emptyState) {
		return;
	}

	const hasMessages = chatLog.querySelector(".msg") !== null;
	emptyState.classList.toggle("is-hidden", hasMessages);
}

function setDraftMessage(text) {
	messageInput.value = text;
	updateCounter();
	autoResizeMessageInput();
	messageInput.focus();
}

function setBusy(isBusy) {
	sendButton.disabled = isBusy;
	messageInput.disabled = isBusy;
	sendButton.textContent = isBusy ? "Sending..." : "Send message";
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

function isDesktopViewport() {
	return window.matchMedia(`(min-width: ${headerDesktopMinWidth}px)`).matches;
}

function readStoredHeaderState() {
	try {
		const storedState = window.localStorage.getItem(headerExpandedStorageKey);
		if (storedState === "true") {
			return true;
		}

		if (storedState === "false") {
			return false;
		}
	} catch {
		return null;
	}

	return null;
}

function setHeaderExpanded(isExpanded, options = {}) {
	const { persist = true } = options;

	if (!chatHeader || !headerToggleBtn || !headerToggleLabel) {
		return;
	}

	chatHeader.classList.toggle("is-collapsed", !isExpanded);
	headerToggleBtn.setAttribute("aria-expanded", String(isExpanded));
	headerToggleLabel.textContent = isExpanded ? "Hide details" : "Show details";

	if (persist) {
		try {
			window.localStorage.setItem(headerExpandedStorageKey, String(isExpanded));
		} catch {
			// Ignore storage errors and keep UI responsive.
		}
	}
}

function initializeHeaderState() {
	if (!chatHeader || !headerToggleBtn || !headerToggleLabel) {
		return;
	}

	const storedState = readStoredHeaderState();
	const defaultState = isDesktopViewport();
	setHeaderExpanded(storedState ?? defaultState, { persist: false });
}

function handleHeaderViewportChange() {
	if (readStoredHeaderState() !== null) {
		return;
	}

	setHeaderExpanded(isDesktopViewport(), { persist: false });
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
	autoResizeMessageInput();

	const thinking = startThinkingMessage();
	setBusy(true);

	try {
		const response = await fetch("/api/chat", {
			method: "POST",
			headers: {
				"Content-Type": "application/json"
			},
			credentials: "same-origin",
			body: JSON.stringify({
				chatInput,
				sessionId: getSessionId()
			})
		});

		const payload = await response.json().catch(() => ({}));
		thinking.stop();
		thinking.node.remove();

		if (response.status === 401) {
			window.location.assign(payload.loginUrl || "/login");
			return;
		}

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

messageInput.addEventListener("input", () => {
	updateCounter();
	autoResizeMessageInput();
});

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

for (const button of quickActionButtons) {
	button.addEventListener("click", () => {
		const prompt = button.dataset.prompt;
		if (prompt) {
			setDraftMessage(prompt);
		}
	});
}

if (headerToggleBtn) {
	headerToggleBtn.addEventListener("click", () => {
		const isExpanded = headerToggleBtn.getAttribute("aria-expanded") === "true";
		setHeaderExpanded(!isExpanded);
	});
}

window.addEventListener("resize", handleHeaderViewportChange);

// Load previous chat history and ensure greeting is added if none exists
loadChatHistory();
initializeHeaderState();
if (chatLog.children.length === 0) {
	appendMessage("Hello! I'm ready to help with IT requests.", "bot");
}
updateCounter();
autoResizeMessageInput();
refreshEmptyState();
