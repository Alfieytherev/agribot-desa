"""
AgriBot Desa - Core AI Agent
AI-powered farming assistant for Indonesian farmers via WhatsApp
Author: Alfieytherev
AMD ROCm Ready
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from langchain_ollama import OllamaLLM
from langchain.agents import AgentExecutor, create_react_agent
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import tool

from agent.tools import (
    get_weather_info,
    get_market_price,
    identify_pest_disease,
    get_crop_calendar,
)

load_dotenv()

# ── Knowledge base paths ───────────────────────────────────────────────────────
KB_PATH = Path(__file__).parent.parent / "knowledge"

def load_knowledge_base() -> dict:
    """Load all farming knowledge JSON files into memory."""
    kb = {}
    for fname in ["tanaman.json", "hama.json", "cuaca.json"]:
        fpath = KB_PATH / fname
        if fpath.exists():
            with open(fpath, "r", encoding="utf-8") as f:
                kb[fname.replace(".json", "")] = json.load(f)
    return kb

KNOWLEDGE_BASE = load_knowledge_base()

# ── System prompt ──────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """Kamu adalah AgriBot Desa, asisten pertanian AI untuk petani Indonesia.

Tugasmu:
- Membantu petani mengenali hama, penyakit, dan masalah tanaman
- Memberikan saran perawatan dan pemupukan yang tepat
- Informasi harga komoditas dan cuaca terkini
- Jadwal tanam berdasarkan musim dan lokasi

Aturan:
- Selalu jawab dalam Bahasa Indonesia yang mudah dipahami petani
- Gunakan satuan yang familiar (kg, hektar, liter)
- Jika tidak yakin, sarankan konsultasi dengan penyuluh pertanian setempat
- Jawaban harus praktis dan langsung bisa diterapkan
- Jangan gunakan istilah teknis yang sulit tanpa penjelasan

Kamu memiliki akses ke tools berikut:
{tools}

Format jawaban:
Question: pertanyaan petani
Thought: analisis masalah
Action: nama_tool
Action Input: input untuk tool
Observation: hasil tool
... (ulangi jika perlu)
Thought: sudah cukup informasi
Final Answer: jawaban lengkap untuk petani

Mulai!

Question: {input}
Thought: {agent_scratchpad}
"""

# ── LLM setup (AMD ROCm optimized via Ollama) ─────────────────────────────────
def create_llm() -> OllamaLLM:
    """
    Initialize LLM via Ollama.
    Ollama automatically uses AMD ROCm if available.
    Set OLLAMA_NUM_GPU=-1 in .env to use all AMD GPU VRAM.
    """
    return OllamaLLM(
        model=os.getenv("MODEL_NAME", "llama3"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        temperature=0.3,        # lower = more factual farming advice
        num_predict=512,        # max tokens per response
        num_ctx=4096,           # context window
    )

# ── Per-user memory store ──────────────────────────────────────────────────────
_memory_store: dict[str, ConversationBufferWindowMemory] = {}

def get_user_memory(user_id: str) -> ConversationBufferWindowMemory:
    """Return or create conversation memory for a specific WhatsApp user."""
    if user_id not in _memory_store:
        _memory_store[user_id] = ConversationBufferWindowMemory(
            k=5,                          # remember last 5 exchanges
            memory_key="chat_history",
            return_messages=True,
        )
    return _memory_store[user_id]

# ── Agent factory ──────────────────────────────────────────────────────────────
def create_agent(user_id: str) -> AgentExecutor:
    """Build a ReAct agent with tools and per-user memory."""
    llm = create_llm()
    tools = [
        get_weather_info,
        get_market_price,
        identify_pest_disease,
        get_crop_calendar,
    ]
    prompt = PromptTemplate.from_template(SYSTEM_PROMPT)
    agent = create_react_agent(llm, tools, prompt)
    memory = get_user_memory(user_id)

    return AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=5,
    )

# ── Main entry point ───────────────────────────────────────────────────────────
def process_message(user_id: str, message: str) -> str:
    """
    Process an incoming WhatsApp message and return AI response.

    Args:
        user_id: WhatsApp phone number (used as memory key)
        message: Farmer's question in Bahasa Indonesia

    Returns:
        AI-generated farming advice as string
    """
    try:
        agent_executor = create_agent(user_id)
        result = agent_executor.invoke({"input": message})
        return result.get("output", "Maaf, saya tidak bisa memproses pertanyaan Anda saat ini.")

    except Exception as e:
        print(f"[AgriBot Error] user={user_id} error={e}")
        return (
            "Maaf, terjadi kesalahan teknis. "
            "Silakan coba lagi dalam beberapa menit 🙏"
        )


# ── CLI test mode ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🌾 AgriBot Desa — Mode Test CLI")
    print("Ketik 'keluar' untuk berhenti\n")

    test_user = "cli_test_user"
    while True:
        try:
            user_input = input("Petani: ").strip()
            if user_input.lower() in ["keluar", "exit", "quit"]:
                print("Sampai jumpa! 🌾")
                break
            if not user_input:
                continue

            response = process_message(test_user, user_input)
            print(f"\nAgriBot: {response}\n")

        except KeyboardInterrupt:
            print("\nSampai jumpa! 🌾")
            break
