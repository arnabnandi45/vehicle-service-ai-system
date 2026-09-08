const chatBox = document.getElementById("chat-box");
const questionInput = document.getElementById("question-input");
const sendButton = document.getElementById("send-button");
const fileInput = document.getElementById("file-input");
const uploadButton = document.getElementById("upload-button");


function addMessage(message, className) {

    const messageElement = document.createElement("div");

    messageElement.classList.add("message");
    messageElement.classList.add(className);

    messageElement.textContent = message;

    chatBox.appendChild(messageElement);

    chatBox.scrollTop = chatBox.scrollHeight;
}


async function sendQuestion() {

    const question = questionInput.value.trim();

    if (!question) {
        return;
    }


    // Show user's question
    addMessage(question, "user-message");

    // Clear input
    questionInput.value = "";

    // Disable button while waiting
    sendButton.disabled = true;
    sendButton.textContent = "Thinking...";


    try {

        const response = await fetch(
            `http://127.0.0.1:8000/chat?question=${encodeURIComponent(question)}`
        );


        if (!response.ok) {
            throw new Error("Failed to get response from server");
        }


        const data = await response.json();


        // Show AI answer
        addMessage(data.answer, "bot-message");


    } catch (error) {

        addMessage(
            "Sorry, something went wrong. Please try again.",
            "bot-message"
        );

        console.error(error);

    } finally {

        sendButton.disabled = false;
        sendButton.textContent = "Send";

        questionInput.focus();
    }
}


// Send when button is clicked
sendButton.addEventListener("click", sendQuestion);


// Send when Enter key is pressed
questionInput.addEventListener("keypress", function (event) {

    if (event.key === "Enter") {
        sendQuestion();
    }

});

async function uploadFile() {

    const file = fileInput.files[0];

    if (!file) {
        alert("Please select a PDF file first.");
        return;
    }

    const formData = new FormData();

    formData.append("file", file);

    uploadButton.disabled = true;
    uploadButton.textContent = "Uploading...";


    try {

        const response = await fetch(
            "http://127.0.0.1:8000/upload",
            {
                method: "POST",
                body: formData
            }
        );


        if (!response.ok) {
            throw new Error("Upload failed");
        }


        const data = await response.json();

        addMessage(
            `📄 PDF uploaded successfully: ${data.filename}. ` +
            `Created ${data.total_chunks} text chunks.`,
            "bot-message"
        );

        fileInput.value = "";


    } catch (error) {

        addMessage(
            "❌ File upload failed. Please try again.",
            "bot-message"
        );

        console.error(error);

    } finally {

        uploadButton.disabled = false;
        uploadButton.textContent = "Upload PDF";
    }
}


uploadButton.addEventListener(
    "click",
    uploadFile
);