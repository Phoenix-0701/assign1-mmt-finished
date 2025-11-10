const urlParams = new URLSearchParams(window.location.search);
const peerName = urlParams.get('peer');
const peerIP = urlParams.get('ip');
console.log(peerIP)
const peerPort = urlParams.get('port');
console.log(peerPort)
const username = document.cookie.match(/username=([^;]+)/)[1];
console.log(`http://${peerIP}:${peerPort}/receive-message`)

document.getElementById("peerName").innerText = peerName;

const chatWindow = document.getElementById("messages");
const messageInput = document.getElementById("message-input");
const sendBtn = document.getElementById("send-btn");

function appendMessage(sender, text) {
            if (!chatWindow) return;
            const msgDiv = document.createElement("div");
            msgDiv.classList.add("message");
            msgDiv.innerHTML = `<b>${sender}:</b> ${text}`;
            chatWindow.appendChild(msgDiv);
            chatWindow.scrollTop = chatWindow.scrollHeight;
        }

async function sendMessage(text) {
            if (!peerIP || !peerPort) {
                appendMessage("System", "Peer IP or port missing.");
                return;
            }
            const now = new Date().toISOString();
            try {
                await fetch(`http://${peerIP}:${peerPort}/receive-message`, {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({"sender": username, "message": text, "time_stamp": now})
                });
                // appendMessage(username, text);
            } catch (err) {
                appendMessage("System", "Failed to send message to peer.");
            }
        }


async function fetchMessages() {
    if (!peerName) return;
    try {
        const resp = await fetch(`/get-messages?peer=${peerName}`);
        const data = await resp.json();
        chatWindow.innerHTML = ""; // Clear old messages
        data.messages.forEach(msg => {
            appendMessage(msg.sender, `${msg.message} <small>${msg.time_stamp}</small>`);
        });
    } catch (err) {
        console.error(err);
        appendMessage("System", "Failed to fetch messages");
    }
}

async function saveMessage(text) {
            if (!peerIP || !peerPort) {
                appendMessage("System", "Peer IP or port missing.");
                return;
            }
            const now = new Date().toISOString();
            try {
                await fetch(`/send-message`, {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({"receiver": peerName, "message": text, "time_stamp": now})
                });
                // appendMessage(username, text);
            } catch (err) {
                appendMessage("System", "Failed to send message to peer.");
            }
        }



// Gửi tin nhắn khi click
sendBtn.onclick = () => {
            const text = messageInput.value.trim();
            if (!text) return;
            sendMessage(text);
            saveMessage(text);
            messageInput.value = "";
        };

// Polling để nhận tin nhắn mỗi 1s
setInterval(fetchMessages, 1000);

