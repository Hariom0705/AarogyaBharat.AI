const USER_ID = "user";
let SESSION_ID = localStorage.getItem("aarogya_session_id");
if (!SESSION_ID) {
    SESSION_ID = "session_" + Math.random().toString(36).substring(2, 15);
    localStorage.setItem("aarogya_session_id", SESSION_ID);
}

const chatMessages = document.getElementById("chat-messages");
const chatInput = document.getElementById("chat-input");
const chatSend = document.getElementById("chat-send");
const bookingModal = document.getElementById("booking-modal");
const btnCloseModal = document.getElementById("btn-close-modal");
const bookingForm = document.getElementById("booking-form");
const bookingResult = document.getElementById("booking-result");

// Modal pre-populate targets
const modalDoctorName = document.getElementById("modal-doctor-name");
const modalDoctorSpecialty = document.getElementById("modal-doctor-specialty");
const modalDoctorAvailability = document.getElementById("modal-doctor-availability");

let selectedDoctorName = "";
let selectedDoctorSpecialty = "";

function appendMessage(sender, text, htmlContent = null) {
    const bubble = document.createElement("div");
    bubble.className = `chat-bubble ${sender === "user" ? "user-message" : "bot-message"}`;
    if (htmlContent) {
        bubble.innerHTML = htmlContent;
    } else {
        bubble.textContent = text;
    }
    chatMessages.appendChild(bubble);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Custom Markdown to HTML formatter for cleaner display
function formatMarkdown(text) {
    // Replace headers
    let html = text.replace(/### (.*)/g, '<h3>$1</h3>');
    // Bold
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Italic
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
    // Bullet points
    html = html.replace(/^- (.*)/gm, '<li>$1</li>');
    // Wrap lists
    html = html.replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>');
    // Paragraphs (newline replacement)
    html = html.replace(/\n\n/g, '<p></p>');
    return html;
}

// Scrape doctors from bot response to generate interactive buttons
function processDoctorCards(text) {
    const formatted = formatMarkdown(text);
    
    // Matches doctor list formatting e.g.:
    // - **Dr. Rajesh Kumar** - AIIMS Delhi (Mon-Fri 9AM-1PM)
    const docRegex = /-\s*\*\*Dr\.\s*([^*]+)\*\*\s*-\s*([^(]+)\s*\(([^)]+)\)/g;
    const matches = [...text.matchAll(docRegex)];
    
    if (matches.length === 0) {
        return formatted;
    }

    let customHtml = formatted;
    matches.forEach(m => {
        const docName = m[1].trim();
        const hospital = m[2].trim();
        const avail = m[3].replace("Availability:", "").trim();
        
        const cardHtml = `
            <div class="doctor-booking-card">
                <div>
                    <strong>Dr. ${docName}</strong><br>
                    <small>${hospital} (${avail})</small>
                </div>
                <button class="btn-book-action" onclick="openBookingPopup('${docName}', '${hospital}', '${avail}')">📅 Book Appointment</button>
            </div>
        `;
        // Replace list elements in HTML representation
        const targetListItem = `<li><strong>Dr. ${docName}</strong> - ${hospital} (${m[3]})</li>`;
        const targetAlternative = `<li><strong>Dr. ${docName}</strong> - ${hospital} (Availability: ${m[3]})</li>`;
        
        customHtml = customHtml.replace(targetListItem, cardHtml);
        customHtml = customHtml.replace(targetAlternative, cardHtml);
    });

    return customHtml;
}

window.openBookingPopup = function(name, specialtyAndHospital, availability) {
    selectedDoctorName = name;
    selectedDoctorSpecialty = specialtyAndHospital;
    
    modalDoctorName.textContent = `Dr. ${name}`;
    modalDoctorSpecialty.textContent = specialtyAndHospital;
    modalDoctorAvailability.textContent = `Availability: ${availability}`;
    
    // Reset form and result states
    bookingForm.style.display = "flex";
    bookingResult.style.display = "none";
    document.getElementById("booking-date").value = "";
    document.getElementById("booking-time").value = "";
    
    bookingModal.classList.add("active");
};

btnCloseModal.onclick = function() {
    bookingModal.classList.remove("active");
};

// Close modal when clicking outside
window.onclick = function(event) {
    if (event.target === bookingModal) {
        bookingModal.classList.remove("active");
    }
};

async function sendMessage(text) {
    if (!text.trim()) return;
    
    appendMessage("user", text);
    chatInput.value = "";
    
    // Append loading indicator
    const typingBubble = document.createElement("div");
    typingBubble.className = "chat-bubble bot-message typing";
    typingBubble.textContent = "AI Health Coordinator is thinking...";
    chatMessages.appendChild(typingBubble);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
        const response = await fetch("/run", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                app_name: "app",
                user_id: USER_ID,
                session_id: SESSION_ID,
                new_message: {
                    role: "user",
                    parts: [{ text: text }]
                }
            })
        });

        // Remove typing indicator
        chatMessages.removeChild(typingBubble);

        if (!response.ok) {
            throw new Error(`HTTP Error ${response.status}`);
        }

        const events = await response.json();
        
        // Find the model response event
        const modelEvent = events.find(e => e.content && e.content.role === "model");
        if (modelEvent && modelEvent.content.parts && modelEvent.content.parts[0].text) {
            const botResponse = modelEvent.content.parts[0].text;
            
            // Check if there are doctors listed in response to generate cards
            const processedHtml = processDoctorCards(botResponse);
            appendMessage("bot", botResponse, processedHtml);

            // Update dashboard content dynamically based on output
            if (modelEvent.output) {
                updateDashboard(modelEvent.output);
            }
        } else {
            appendMessage("bot", "I processed your request, but could not formulate a response. Please try again.");
        }

    } catch (err) {
        if (chatMessages.contains(typingBubble)) {
            chatMessages.removeChild(typingBubble);
        }
        appendMessage("bot", `Failed to connect to AarogyaBharat AI engine: ${err.message}`);
    }
}

function updateDashboard(output) {
    // Dynamic updates for medications, vaccines, or timeline
    if (output.medications) {
        const medList = document.querySelector(".medication-list");
        medList.innerHTML = "";
        output.medications.forEach(m => {
            medList.innerHTML += `
                <li>
                    <span class="med-icon">💊</span>
                    <div class="med-details">
                        <strong>${m.name}</strong>
                        <span>${m.dosage} - ${m.timing}</span>
                    </div>
                </li>
            `;
        });
    }

    if (output.vaccines) {
        const vacList = document.querySelector(".vaccination-list");
        vacList.innerHTML = "";
        output.vaccines.forEach(v => {
            vacList.innerHTML += `
                <li class="${v.status === 'completed' ? 'completed' : 'due'}">
                    <span class="vac-status">${v.status === 'completed' ? '✓' : '!'}</span>
                    <div class="vac-details">
                        <strong>${v.name}</strong>
                        <span>Status: ${v.status}</span>
                    </div>
                </li>
            `;
        });
    }
}

bookingForm.onsubmit = async function(e) {
    e.preventDefault();
    
    const dateVal = document.getElementById("booking-date").value;
    const timeVal = document.getElementById("booking-time").value;
    const btnSubmit = document.getElementById("btn-submit-booking");
    
    btnSubmit.disabled = true;
    btnSubmit.textContent = "Booking slot...";
    
    try {
        const bookingRequestText = `Book an appointment with Dr. ${selectedDoctorName} on ${dateVal} at ${timeVal}. My Health ID is HB-1234.`;
        
        const response = await fetch("/run", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                app_name: "app",
                user_id: USER_ID,
                session_id: SESSION_ID,
                new_message: {
                    role: "user",
                    parts: [{ text: bookingRequestText }]
                }
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP Error ${response.status}`);
        }

        const events = await response.json();
        const modelEvent = events.find(e => e.content && e.content.role === "model");
        
        if (modelEvent && modelEvent.output && modelEvent.output.appointment_id) {
            const out = modelEvent.output;
            
            // Show checkmark result elements
            document.getElementById("booking-result-id").textContent = `Appointment ID: ${out.appointment_id}`;
            document.getElementById("booking-result-details").textContent = out.details;
            
            bookingForm.style.display = "none";
            bookingResult.style.display = "flex";
            
            appendMessage("bot", `I've successfully booked your appointment! Details: ${out.details} (ID: ${out.appointment_id})`);
            
            // Prepend new appointment to left dashboard timeline
            const timelineContainer = document.querySelector(".timeline-container");
            const newAptHtml = `
                <div class="timeline-item completed">
                    <div class="timeline-marker"></div>
                    <div class="timeline-content">
                        <span class="timeline-date">${dateVal}</span>
                        <h4>Appointment Scheduled</h4>
                        <p>Dr. ${selectedDoctorName} | Slot: ${timeVal} | ID: ${out.appointment_id}</p>
                    </div>
                </div>
            `;
            timelineContainer.insertAdjacentHTML('afterbegin', newAptHtml);

            // Automatically close modal after 3 seconds
            setTimeout(() => {
                bookingModal.classList.remove("active");
            }, 3000);

        } else if (modelEvent && modelEvent.output && modelEvent.output.status === "failed") {
            alert(`Booking Failed: ${modelEvent.output.details}`);
            btnSubmit.disabled = false;
            btnSubmit.textContent = "Confirm Appointment";
        } else {
            alert("Booking could not be confirmed by the agent. Please try again.");
            btnSubmit.disabled = false;
            btnSubmit.textContent = "Confirm Appointment";
        }

    } catch (err) {
        alert(`Error booking appointment: ${err.message}`);
        btnSubmit.disabled = false;
        btnSubmit.textContent = "Confirm Appointment";
    }
};

chatInput.onkeydown = function(e) {
    if (e.key === "Enter") {
        sendMessage(chatInput.value);
    }
};

chatSend.onclick = function() {
    sendMessage(chatInput.value);
};
