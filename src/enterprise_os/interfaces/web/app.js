const chatContainer = document.getElementById('chat-container');
const goalInput = document.getElementById('goal-input');
const sendBtn = document.getElementById('send-btn');
const approvalModal = document.getElementById('approval-modal');
const approvalJustification = document.getElementById('approval-justification');
const approvalContext = document.getElementById('approval-context');
const btnApprove = document.getElementById('btn-approve');
const btnReject = document.getElementById('btn-reject');
const approvalCount = document.getElementById('approval-count');

let currentApprovalId = null;

function addMessage(text, type) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${type}`;
    const contentDiv = document.createElement('div');
    contentDiv.className = 'msg-content';
    contentDiv.textContent = text;
    msgDiv.appendChild(contentDiv);
    chatContainer.appendChild(msgDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

async function submitGoal() {
    const text = goalInput.value.trim();
    if (!text) return;
    
    addMessage(text, 'user-msg');
    goalInput.value = '';
    
    const id = "goal-" + Date.now();
    try {
        await fetch('/ceo/goal', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id, description: text })
        });
        addMessage("CEO: Analyzing objective...", 'ceo-msg');
    } catch (e) {
        addMessage("Error communicating with EnterpriseOS.", 'system-msg');
    }
}

sendBtn.addEventListener('click', submitGoal);
goalInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') submitGoal();
});

// Polling for Approvals
setInterval(async () => {
    try {
        const res = await fetch('/approvals');
        const data = await res.json();
        const pending = data.pending_approvals || [];
        
        if (pending.length > 0) {
            approvalCount.textContent = pending.length;
            approvalCount.classList.add('active');
            
            if (!currentApprovalId) {
                const item = pending[0];
                currentApprovalId = item.id;
                approvalJustification.textContent = item.justification;
                approvalContext.textContent = item.context;
                approvalModal.style.display = 'flex';
            }
        } else {
            approvalCount.classList.remove('active');
            approvalModal.style.display = 'none';
            currentApprovalId = null;
        }
    } catch (e) {
        console.error("Polling error", e);
    }
}, 2000);

async function resolveApproval(approved) {
    if (!currentApprovalId) return;
    try {
        await fetch(`/approvals/${currentApprovalId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ approved, feedback: approved ? "Approved by Founder" : "Rejected" })
        });
        approvalModal.style.display = 'none';
        currentApprovalId = null;
        addMessage(approved ? "✓ Approval Granted" : "✕ Approval Rejected", 'system-msg');
    } catch (e) {
        console.error(e);
    }
}

btnApprove.addEventListener('click', () => resolveApproval(true));
btnReject.addEventListener('click', () => resolveApproval(false));
