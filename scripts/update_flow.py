import json
import os

# Why: File paths defining inputs and outputs for our flow modification.
# Connectivity: Reads from yara_rag_prompt.md, writes into main_whatsapp_flow.json.
flow_path = "C:/Projects/Projects/Biligual Whatsapp Lead Generation System/main_whatsapp_flow.json"
prompt_path = "C:/Projects/Projects/Biligual Whatsapp Lead Generation System/prompts/yara_rag_prompt.md"

def update_workflow():
    # 1. Load the new RAG system prompt
    with open(prompt_path, "r", encoding="utf-8") as f:
        new_prompt = f.read()

    # 2. Parse the n8n JSON workflow file (resolves UTF-8 BOM automatically)
    with open(flow_path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)

    # 3. Locate and update Yara Qualification Agent's system prompt parameters
    yara_node = None
    for node in data.get("nodes", []):
        if node.get("name") == "Yara Qualification Agent":
            yara_node = node
            break

    if not yara_node:
        print("❌ Error: 'Yara Qualification Agent' node not found in flow!")
        return

    # Update system message text
    yara_node["parameters"]["options"]["systemMessage"] = new_prompt
    print("✅ Yara system prompt parameter successfully updated.")

    # 4. Check if 'Real Estate RAG Tool' is already defined, or insert it
    tool_node_name = "Real Estate RAG Tool"
    tool_node_exists = False
    for node in data.get("nodes", []):
        if node.get("name") == tool_node_name:
            tool_node_exists = True
            break

    # Why: Custom Javascript for n8n's LangChain Custom Tool.
    # Connectivity: Shoots an HTTP POST call over the Docker bridge network to Port 8000 of the rag-api.
    tool_js_code = """
const query = $input.first().json.query;
const response = await $http.request({
  method: 'POST',
  url: 'http://whatsapp_rag_api:8000/query',
  body: {
    question: query,
    chat_history: []
  }
});
return response.response;
""".strip()

    if not tool_node_exists:
        # Create a new Custom Tool node structure matching n8n schemas
        new_tool_node = {
            "parameters": {
                "name": "query_real_estate_market_data",
                "description": "Use this tool to query the Dubai real estate database for transactional sales history, average prices, rental rates, gross ROI yields, and volume trends. Input should be a single clear search question in English about JVC, Dubai Marina, or other Dubai areas.",
                "javascriptAndLibraries": {
                    "jsCode": tool_js_code
                }
            },
            "type": "@n8n/n8n-nodes-langchain.toolCustom",
            "typeVersion": 1,
            "position": [
                4800,
                -300
            ],
            "id": "e2a5d21a-e8d1-419b-ab84-88ff99cc2020",
            "name": tool_node_name
        }
        data["nodes"].append(new_tool_node)
        print(f"✅ Created new node: '{tool_node_name}'.")
    else:
        # Update existing tool node jsCode
        for node in data.get("nodes", []):
            if node.get("name") == tool_node_name:
                node["parameters"]["javascriptAndLibraries"]["jsCode"] = tool_js_code
                print(f"✅ Updated jsCode for existing node: '{tool_node_name}'.")

    # 5. Connect 'Real Estate RAG Tool' -> 'Yara Qualification Agent'
    connections = data.get("connections", {})
    if tool_node_name not in connections:
        connections[tool_node_name] = {
            "ai_tool": [
                [
                    {
                        "node": "Yara Qualification Agent",
                        "type": "ai_tool",
                        "index": 0
                    }
                ]
            ]
        }
        print("✅ Configured RAG Tool connections to Yara.")

    # 6. Save modifications back to main_whatsapp_flow.json
    with open(flow_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("🎉 Workflow file successfully written to disk!")

if __name__ == "__main__":
    update_workflow()
