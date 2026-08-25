import os
from dotenv import load_dotenv
load_dotenv('backend/.env')
from backend.agents.viz_gen import viz_gen_node

state = {
    "user_query": "Berapa total market share internasional di bulan Februari 2024?",
    "sql_error": "Maksimal percobaan Self-Healing tercapai. Menyerah.",
    "query_result": []
}

res = viz_gen_node(state)
print(res)
