Vue.use(VueMarkdown);
const vue = new Vue({
    el: '#app',
    data: {
        userMessage: "",
        talks: [],
        selectedTalkIndex: 0,
        receiving: false,
        processing: false,
        maxTalkCount: 20,
        textAreaRows: 1,
    },
    watch: {
        userMessage: function () {
            // Set the number of lines in the input form according to the number of newline characters in the entered message.
            const match = this.userMessage.match(/\n/g);
            this.textAreaRows = match ? match.length + 1 : 1;
        },
    },
    async mounted() {
        await this.listTalks();
        if (this.talks.length == 0)
            this.addTalk();
    },
    methods: {
        listTalks: async function () {
            const resp = await axios.get("api/chat");
            this.talks = resp.data.chats;
        },
        sendUserMessage: async function () {
            this.userMessage = this.userMessage.trim();
            if (this.receiving || !this.userMessage.length) return;
            await this.sendMessage();
        },
        sendMessage: async function () {
            const talk = this.talks[this.selectedTalkIndex];
            talk.messages.push({ role: "user", content: this.userMessage });
            talk.messages.push({ role: "assistant", content: "Processing..." });
            const message = this.userMessage;

            this.receiving = true;
            this.userMessage = "";
            this.textAreaRows = 1;

            const resp = await fetch(`/api/chat/${talk.id}/message`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: message }),
            });
            if (!resp.ok) {
                talk.messages[talk.messages.length - 1].content = "Unexpected error occurred. Please try again later.";
                this.receiving = false;
                return;
            }

            let processingText = "";
            const reader = resp.body.getReader();
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                const text = new TextDecoder("utf-8").decode(value);
                try {
                    const val = JSON.parse(text);
                    switch (val.eventType) {
                        case "thread.message.delta":
                            processingText += val.delta;
                            talk.messages[talk.messages.length - 1].content = processingText;
                            break;
                        case "thread.message.completed":
                            processingText += "\n\n## Referenced Documents:\n"
                            processingText += val.content.annotations.map(a => {
                                return a.url_citation ? `- ${a.text}: [${a.url_citation.title}](${a.url_citation.url})` : null;
                            }).filter(a => a).join("\n");
                            talk.messages[talk.messages.length - 1].content = processingText;
                            break;
                        default:
                            break;
                    }
                } catch { } // For JSON parse error
            }
            this.receiving = false;
        },
        selectTalk: function (index) {
            this.selectedTalkIndex = index;
        },
        addTalk: async function () {
            this.processing = true;
            const chatTitle = `Chat ${this.talks.length + 1}`;
            const resp = await axios.post("/api/chat", { title: chatTitle });
            this.processing = false;
            this.talks.push({
                id: resp.data.id,
                title: resp.data.title,
                messages: resp.data.messages,
            });
            this.selectedTalkIndex = this.talks.length - 1;
        },
        deleteTalk: async function (index) {
            const talk = this.talks[index];

            this.processing = true;
            await axios.delete(`/api/chat/${talk.id}`);
            this.processing = false;

            this.talks.splice(index, 1);
            this.selectedTalkIndex--;
            if (this.selectedTalkIndex < 0)
                this.selectedTalkIndex = 0;
            if (this.talks.length == 0)
                this.addTalk();
        },
    }
});
