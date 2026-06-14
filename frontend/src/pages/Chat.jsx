import { useState } from "react";
import client from "../api/client";

const SUGGESTED_QUESTIONS = [
    "Which region had the highest net revenue in Q1 2024?",
    "What is the gross profit margin for the Snacks category?",
    "Which sales rep closed the most units in 2025?",
    "Compare E-Commerce vs Modern Trade net revenue.",
    "What was the best performing product in the West region?",
];

const Chat = () => {
    const [input, setInput] = useState("");
    const [messages, setMessages] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleSend = async () => {
        const question = input.trim();
        if (!question || loading) return;

        setInput("");
        setError(null);
        setLoading(true);

        try {
            const res = await client.post("/api/chat", { question });
            setMessages((prev) => [
                ...prev,
                { question, answer: res.data.answer },
            ]);
        } catch (err) {
            setError("Something went wrong. Make sure the backend is running on port 8000.");
        } finally {
            setLoading(false);
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <div className="min-h-screen bg-slate-50 px-6 py-8">
            <div className="max-w-3xl mx-auto">

                {/* Page Header */}
                <div className="mb-6">
                    <h1 className="text-3xl font-bold text-gray-900">Ask NovaBite AI</h1>
                    <p className="mt-1 text-gray-500">Ask anything about sales performance</p>
                </div>

                {/* Suggested Question Chips */}
                <div className="mb-6">
                    <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">
                        Suggested Questions
                    </p>
                    <div className="flex flex-wrap gap-2">
                        {SUGGESTED_QUESTIONS.map((q) => (
                            <button
                                key={q}
                                onClick={() => setInput(q)}
                                className="text-sm bg-white border border-gray-200 text-gray-600 px-3 py-1.5 rounded-full shadow-sm hover:border-blue-400 hover:text-blue-600 transition-colors duration-150"
                            >
                                {q}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Input Row */}
                <div className="flex gap-3 mb-8">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Type your question here..."
                        disabled={loading}
                        className="flex-1 border border-gray-200 rounded-lg px-4 py-3 text-sm text-gray-800 bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
                    />
                    <button
                        onClick={handleSend}
                        disabled={loading || !input.trim()}
                        className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold px-5 py-3 rounded-lg shadow-sm transition-colors duration-150"
                    >
                        Send
                    </button>
                </div>

                {/* Error */}
                {error && (
                    <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
                        {error}
                    </div>
                )}

                {/* Loading State */}
                {loading && (
                    <div className="flex items-center gap-3 mb-6">
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                        <span className="text-sm text-gray-500">Thinking...</span>
                    </div>
                )}

                {/* Chat History */}
                <div className="flex flex-col gap-6">
                    {messages.map((msg, idx) => (
                        <div key={idx} className="flex flex-col gap-3">

                            {/* Question — right aligned */}
                            <div className="flex justify-end">
                                <div className="bg-blue-600 text-white text-sm px-4 py-3 rounded-2xl rounded-tr-sm max-w-[80%] shadow-sm">
                                    {msg.question}
                                </div>
                            </div>

                            {/* Answer — left aligned */}
                            <div className="flex justify-start">
                                <div className="bg-white text-gray-800 text-sm px-4 py-3 rounded-2xl rounded-tl-sm max-w-[80%] shadow-md border border-gray-100 leading-relaxed whitespace-pre-wrap">
                                    {msg.answer}
                                </div>
                            </div>

                        </div>
                    ))}
                </div>

            </div>
        </div>
    );
};

export default Chat;