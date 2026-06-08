#!/usr/bin/env python3
"""The Unofficial Guide — Gradio interface with grounded RAG generation."""

import os
from typing import List, Dict, Any

import gradio as gr
from groq import Groq
from dotenv import load_dotenv

from embed import Embedder


load_dotenv()
GROQ_API_KEY = os.environ["GROQ_API_KEY"]
GROQ_MODEL = "llama-3.3-70b-versatile"
TOP_K = 5

SYSTEM_PROMPT = """You are "The Unofficial Guide," a helpful assistant that answers questions about UC Berkeley EECS courses and professors using ONLY the student-generated documents provided below.

Rules:
1. Answer using ONLY the information in the provided documents.
2. If the documents do not contain enough information to answer the question, say exactly: "I don't have enough information on that."
3. Cite the source document name(s) in your answer using the format [source: filename.txt].
4. Do not use outside knowledge, generalizations, or assumptions.
5. Be concise but specific.

Documents:
{context}

Question: {question}
Answer:"""


class RAGSystem:
    def __init__(self):
        self.embedder = Embedder()
        self.client = Groq(api_key=GROQ_API_KEY)

    def _format_context(self, chunks: List[Dict[str, Any]]) -> str:
        lines = []
        for i, chunk in enumerate(chunks, 1):
            lines.append(f"[{i}] Source: {chunk['source']}\n{chunk['text']}")
        return "\n\n".join(lines)

    def ask(self, question: str) -> Dict[str, str]:
        chunks = self.embedder.retrieve(question, top_k=TOP_K)
        context = self._format_context(chunks)

        prompt = SYSTEM_PROMPT.format(context=context, question=question)

        response = self.client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=512,
        )
        answer = response.choices[0].message.content.strip()

        # Programmatic source attribution (backup if LLM omits citations)
        sources = list({c["source"] for c in chunks})
        sources_text = "\n".join(f"- {s}" for s in sources)

        return {
            "answer": answer,
            "sources": sources_text,
            "raw_context": context,
        }


rag = RAGSystem()


def handle_query(question: str) -> tuple[str, str]:
    if not question or not question.strip():
        return "Please enter a question.", ""
    result = rag.ask(question)
    return result["answer"], result["sources"]


with gr.Blocks(title="The Unofficial Guide") as demo:
    gr.Markdown("# The Unofficial Guide")
    gr.Markdown(
        "Ask questions about UC Berkeley EECS courses, professors, and student experiences. "
        "Answers are grounded in collected student reviews and guides."
    )

    with gr.Row():
        inp = gr.Textbox(label="Your question", placeholder="e.g., What do students say about CS 61B projects?", scale=4)
        btn = gr.Button("Ask", scale=1)

    answer = gr.Textbox(label="Answer", lines=8)
    sources = gr.Textbox(label="Retrieved from", lines=4)

    btn.click(handle_query, inputs=inp, outputs=[answer, sources])
    inp.submit(handle_query, inputs=inp, outputs=[answer, sources])

    gr.Examples(
        examples=[
            "What do students say about DeNero's exam difficulty and grading?",
            "How many hours should students expect to spend on the Gitlet project in CS 61B?",
            "What is the recommended maximum number of hard upper-division CS courses per semester?",
            "Which CS course involves building a pipelined processor in Logisim?",
            "What do students recommend for securing an EECS research position?",
            "What is the best pizza place near campus?",
        ],
        inputs=inp,
        label="Example questions",
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
