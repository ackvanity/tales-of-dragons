import json
import os

STORY_DIR = "./data/location"
CONNECTIONS_FILE = os.path.join(STORY_DIR, "connections.json")

# Load connections.json
with open(CONNECTIONS_FILE, "r", encoding="utf-8") as f:
    connections = json.load(f)

# Build a map from each location id to its actions
actions_map = {}

for conn_id, conn in connections.items():
    src = conn["from"]
    dest = conn["to"]
    action_text = conn["action"]

    # Prepare the action entry
    action_entry = {
        "line": action_text,
        "event": f"finn.LocationTeleportEngineEvent('{dest}')"
    }

    # Add to the source location's action list
    actions_map.setdefault(src, []).append(action_entry)

# Now, update each location file
for filename in os.listdir(STORY_DIR):
    if not filename.endswith(".json"):
        continue
    if filename == "connections.json":
        continue

    filepath = os.path.join(STORY_DIR, filename)

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    loc_id = data.get("id")
    if loc_id in actions_map:
        data["actions"] = actions_map[loc_id]
    else:
        data["actions"] = []

    # Write back the updated JSON
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

print("Locations updated with adjacency actions!")
