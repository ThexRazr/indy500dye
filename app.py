from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)
app.config["SECRET_KEY"] = "beer-dye-tournament-secret-key"

# Path to our JSON "database"
DATA_FILE = "tournament_data.json"

def load_data():
    """Load tournament data from JSON file"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {
        "players": [],
        "captains": [],
        "teams": {"captain1": [], "captain2": []},
        "matches": [],
        "phase": "registration",  # registration, voting, draft, team_creation, match_setup, active
        "draft_order": [],
        "current_draft_turn": 0,
        "match_results": []
    }

def save_data(data):
    """Save tournament data to JSON file"""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@app.get("/")
def home():
    data = load_data()
    return render_template("home.html", phase=data.get("phase", "registration"))

@app.get("/registration")
def registration():
    data = load_data()
    return render_template("registration.html", players=data["players"])

@app.post("/registration/add")
def add_player():
    data = load_data()
    player_name = request.form.get("player_name", "").strip()
    
    if player_name and player_name not in data["players"]:
        data["players"].append(player_name)
        save_data(data)
    
    return redirect(url_for("registration"))

@app.post("/registration/remove")
def remove_player():
    data = load_data()
    player_name = request.form.get("player_name", "").strip()
    
    if player_name in data["players"]:
        data["players"].remove(player_name)
        save_data(data)
    
    return redirect(url_for("registration"))

@app.post("/registration/complete")
def complete_registration():
    data = load_data()
    
    # Handle odd number of players by adding ghost
    if len(data["players"]) % 2 != 0:
        data["players"].append("GHOST PLAYER")
    
    data["phase"] = "voting"
    data["captain_votes"] = {player: 0 for player in data["players"]}
    save_data(data)
    
    return redirect(url_for("captain_voting"))

@app.get("/captain-voting")
def captain_voting():
    data = load_data()
    return render_template("captain_voting.html", 
                         players=data["players"],
                         votes=data.get("captain_votes", {}))

@app.post("/captain-voting/vote")
def vote_captain():
    data = load_data()
    captain1 = request.form.get("captain1")
    captain2 = request.form.get("captain2")
    
    if captain1 and captain2 and captain1 != captain2:
        data["captain_votes"][captain1] = data["captain_votes"].get(captain1, 0) + 1
        data["captain_votes"][captain2] = data["captain_votes"].get(captain2, 0) + 1
    
    save_data(data)
    return redirect(url_for("captain_voting"))

@app.post("/captain-voting/finalize")
def finalize_captains():
    data = load_data()
    
    # Get top 2 voted players
    sorted_votes = sorted(data["captain_votes"].items(), key=lambda x: x[1], reverse=True)
    data["captains"] = [sorted_votes[0][0], sorted_votes[1][0]]
    
    # Remove captains from player pool for draft
    available_players = [p for p in data["players"] if p not in data["captains"]]
    data["available_players"] = available_players
    
    # Initialize draft
    data["teams"] = {"captain1": [data["captains"][0]], "captain2": [data["captains"][1]]}
    data["draft_order"] = []
    data["current_draft_turn"] = 0
    data["phase"] = "team_naming"
    
    save_data(data)
    return redirect(url_for("team_naming"))

@app.get("/team-naming")
def team_naming():
    data = load_data()
    return render_template("team_naming.html", captains=data["captains"])

@app.post("/team-naming/save")
def save_team_names():
    data = load_data()
    
    team1_name = request.form.get("team1_name", "").strip()
    team2_name = request.form.get("team2_name", "").strip()
    
    data["team_names"] = {
        "captain1": team1_name if team1_name else f"{data['captains'][0]}'s Team",
        "captain2": team2_name if team2_name else f"{data['captains'][1]}'s Team"
    }
    data["phase"] = "draft"
    
    save_data(data)
    return redirect(url_for("draft"))

@app.get("/draft")
def draft():
    data = load_data()
    return render_template("draft.html", 
                         captains=data["captains"],
                         teams=data["teams"],
                         available=data["available_players"],
                         draft_order=data.get("draft_order", []),
                         current_turn=data.get("current_draft_turn", 0),
                         team_names=data.get("team_names", {}),
                         players=data["players"])

@app.post("/draft/pick")
def draft_pick():
    data = load_data()
    player = request.form.get("player")
    turn = data["current_draft_turn"]
    
    if player and player in data["available_players"]:
        # True snake draft logic
        # Turn 0: captain1 (A)
        # Turns 1-2: captain2 (B-B)
        # Turns 3-4: captain1 (A-A)
        # Turns 5-6: captain2 (B-B)
        # etc.
        
        if turn == 0:
            team_key = "captain1"
            captain_idx = 0
        elif turn % 4 in [1, 2]:
            team_key = "captain2"
            captain_idx = 1
        else:
            team_key = "captain1"
            captain_idx = 0
        
        data["teams"][team_key].append(player)
        data["available_players"].remove(player)
        data["draft_order"].append({
            "pick": turn + 1, 
            "captain": data["captains"][captain_idx], 
            "player": player
        })
        data["current_draft_turn"] += 1
        
        # Check if draft is complete
        if len(data["available_players"]) == 0:
            data["phase"] = "team_creation"
        
        save_data(data)
    
    return redirect(url_for("draft"))

@app.get("/team-creation")
def team_creation():
    data = load_data()
    
    # Check which captain needs to go
    if "team_pairings" not in data:
        data["team_pairings"] = {}
    
    if "captain1" not in data["team_pairings"]:
        current_captain = 0
    elif "captain2" not in data["team_pairings"]:
        current_captain = 1
    else:
        # Both done, move to match setup
        data["phase"] = "match_setup"
        save_data(data)
        return redirect(url_for("match_setup"))
    
    return render_template("team_creation.html", 
                         captains=data["captains"],
                         team_names=data.get("team_names", {}),
                         teams=data["teams"],
                         current_captain=current_captain)

@app.post("/team-creation/save")
def save_team_pairings():
    data = load_data()
    current_captain = int(request.form.get("current_captain"))
    
    teams = []
    i = 0
    while f"team{i}_p1" in request.form:
        p1 = request.form.get(f"team{i}_p1")
        p2 = request.form.get(f"team{i}_p2")
        if p1 and p2:
            teams.append([p1, p2])
        i += 1
    
    captain_key = f"captain{current_captain + 1}"
    data["team_pairings"][captain_key] = teams
    
    save_data(data)
    return redirect(url_for("team_creation"))

@app.get("/match-setup")
def match_setup():
    data = load_data()
    return render_template("match_setup.html",
                         captains=data["captains"],
                         pairings=data.get("team_pairings", {}))

@app.post("/match-setup/create")
def create_matches():
    data = load_data()
    
    matches = []
    match_num = 1
    
    # Get all matchups from form
    i = 0
    while f"match{i}_team1_idx" in request.form:
        team1_idx = int(request.form.get(f"match{i}_team1_idx"))
        team2_idx = int(request.form.get(f"match{i}_team2_idx"))
        
        team1 = data["team_pairings"]["captain1"][team1_idx]
        team2 = data["team_pairings"]["captain2"][team2_idx]
        
        matches.append({
            "id": match_num,
            "team1": team1,
            "team2": team2,
            "captain1": data["captains"][0],
            "captain2": data["captains"][1],
            "result": None  # Will be "team1", "team2", or "tie"
        })
        match_num += 1
        i += 1
    
    data["matches"] = matches
    data["phase"] = "active"
    
    save_data(data)
    return redirect(url_for("active_tournament"))

@app.get("/active")
def active_tournament():
    data = load_data()
    return render_template("active.html",
                         matches=data.get("matches", []),
                         captains=data["captains"])

@app.post("/active/record-result")
def record_result():
    data = load_data()
    match_id = int(request.form.get("match_id"))
    result = request.form.get("result")  # "team1", "team2", or "tie"
    
    # Find and update match
    for match in data["matches"]:
        if match["id"] == match_id:
            match["result"] = result
            break
    
    save_data(data)
    return redirect(url_for("active_tournament"))

@app.get("/standings")
def standings():
    data = load_data()
    
    # Calculate standings
    captain1_wins = 0
    captain2_wins = 0
    ties = 0
    
    for match in data.get("matches", []):
        if match["result"] == "team1":
            captain1_wins += 1
        elif match["result"] == "team2":
            captain2_wins += 1
        elif match["result"] == "tie":
            ties += 1
    
    return render_template("standings.html",
                         captains=data.get("captains", []),
                         matches=data.get("matches", []),
                         captain1_wins=captain1_wins,
                         captain2_wins=captain2_wins,
                         ties=ties)

@app.post("/reset")
def reset_tournament():
    """Reset everything and start fresh"""
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)