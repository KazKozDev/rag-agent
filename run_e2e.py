import os
import sys

# Ensure we are in the project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from app.ingestion.indexer import build_indexes
from app.agent.supervisor import build_graph
from app.retrieval.hybrid import HybridRetriever

def run_e2e():
    print("Building indexes...")
    vector_index, bm25 = build_indexes()
    print("Indexes built successfully.")

    print("Building graph...")
    retriever = HybridRetriever(vector_index=vector_index, bm25=bm25)
    graph = build_graph(retriever)

    queries = [
        "What is the termination policy at TechCorp?",
        "How much does the Enterprise Tier cost and what does it include?",
        "Who founded the company?",
        "hello", # Should be handled by FAQ
        "contract" # Should be handled by Clarification
    ]

    for q in queries:
        print(f"\n--- Query: {q} ---")
        try:
            state = graph.invoke({"query": q})
            print(f"Route: {state.get('route', 'unknown')}")
            if state.get("needs_clarification"):
                print(f"Needs Clarification: Yes")
                print(f"Question: {state.get('clarification_question')}")
            else:
                print(f"Answer: {state.get('answer')}")
                citations = state.get("citations", [])
                if citations:
                    print(f"Citations: {citations}")
                print(f"Validated: {state.get('validated')}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    run_e2e()
