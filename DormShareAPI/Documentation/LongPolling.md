# DormShare — Long Polling Chat Guide

## Overview
Instead of WebSockets, DormShare uses **long polling** for real-time chat.
The frontend periodically asks the server "are there any new messages?" and displays them if there are.

---

## How It Works

```
1. User opens a chat
2. Frontend loads chat history via GET /chat/get/{chat_id}
3. Frontend saves the timestamp of the last message
4. Every 3 seconds, frontend calls GET /chat/messages/{chat_id}?after={lastTimestamp}
5. If new messages exist → display them, update lastTimestamp
6. If no new messages → do nothing, wait for next poll
```

---

## Endpoints

### Send a Message
```
POST /chat/messages/{chat_id}
Authorization: Bearer {token}
Content-Type: application/json

Body:
{
  "content": "Hello!"
}
```

Response:
```json
{
  "id": "uuid",
  "content": "Hello!",
  "sender_id": "uuid",
  "timestamp": "2026-05-30T12:00:00",
  "is_viewed": false,
  "reaction": null
}
```

---

### Poll for New Messages
```
GET /chat/messages/{chat_id}?after={timestamp}
Authorization: Bearer {token}
```

- `after` — ISO 8601 timestamp of the last message you received
- Returns only messages **newer** than that timestamp
- Returns empty array if no new messages

Response:
```json
{
  "messages": [
    {
      "id": "uuid",
      "content": "Hello!",
      "sender_id": "uuid",
      "timestamp": "2026-05-30T12:00:05",
      "is_viewed": false,
      "reaction": null
    }
  ]
}
```

---

## Frontend Implementation Example

```javascript
let lastTimestamp = null;
let pollingInterval = null;

// Step 1: Load chat on open
async function openChat(chatId) {
  const res = await fetch(`/chat/get/${chatId}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  const chat = await res.json();

  // Display existing messages
  displayMessages(chat.messages);

  // Save last timestamp
  if (chat.messages.length > 0) {
    lastTimestamp = chat.messages.at(-1).timestamp;
  } else {
    lastTimestamp = new Date().toISOString(); // start polling from now
  }

  // Step 2: Start polling
  startPolling(chatId);
}

// Step 3: Poll every 3 seconds
function startPolling(chatId) {
  pollingInterval = setInterval(async () => {
    const res = await fetch(
      `/chat/messages/${chatId}?after=${encodeURIComponent(lastTimestamp)}`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    const data = await res.json();

    if (data.messages.length > 0) {
      displayMessages(data.messages);
      lastTimestamp = data.messages.at(-1).timestamp;
    }
  }, 3000);
}

// Step 4: Stop polling when chat is closed
function closeChat() {
  clearInterval(pollingInterval);
}

// Step 5: Send a message
async function sendMessage(chatId, content) {
  await fetch(`/chat/messages/${chatId}`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ content })
  });
  // No need to manually add the message to UI — 
  // the next poll will pick it up automatically.
  // Or you can optimistically add it right away for better UX.
}
```

---

## Important Notes

- Always **stop polling** when the user navigates away from the chat (`clearInterval`)
- The `after` parameter must be **URL encoded** (`encodeURIComponent`)
- Timestamp format: ISO 8601 — `2026-05-30T12:00:00.000000`
- Poll interval: **3 seconds** is recommended — fast enough for chat, not too heavy on the server
- On sending a message, you can either wait for the next poll or optimistically render it immediately in the UI

---

## Transaction Events via Polling

Since WebSockets are removed, transaction status changes are not pushed to the client automatically.

**Recommended approach:** when the user is inside a chat, also poll `GET /transaction/by-chat/{chat_id}` every 5 seconds and update the UI based on the transaction status:

| status | UI |
|---|---|
| `pending` | Show "Waiting for lender approval..." |
| `active` | Show "Confirm End of Rental" button |
| `completing` | Show "Partner confirmed, waiting for you..." |
| `completed` | Show "Leave a Review" button (borrower only) |
| no transaction | Show "Request to Borrow" button |