from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json
import os
import secrets

app = Flask(__name__)
app.config["SECRET_KEY"] = "beer-dye-tournament-secret-key"

# Admin password (change this to whatever you want)
ADMIN_PASSWORD = "beerdye2025"

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
        "phase": "registration",
        "voting_open": False,  # Admin controls when voting opens
        "draft_order": [],
        "current_draft_turn": 0,
        "match_results": [],
        "voted_players": []  # Track who has voted
    }

def save_data(data):
    """Save tournament data to JSON file"""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def is_admin():
    """Check if current session has admin access"""
    return session.get("is_admin", False)

def get_voter_name():
    """Get the registered voter name from session"""
    return session.get("voter_name")

@app.get("/")
def home():
    data = load_data()
    return render_template("home.html", 
                         phase=data.get("phase", "registration"),
                         is_admin=is_admin())

@app.get("/admin-login")
def admin_login_page():
    return render_template("admin_login.html")

@app.post("/admin-login")
def admin_login():
    password = request.form.get("password", "")
    if password == ADMIN_PASSWORD:
        session["is_admin"] = True
        return redirect(url_for("home"))
    else:
        return render_template("admin_login.html", error="Incorrect password")

@app.get("/admin-logout")
def admin_logout():
    session["is_admin"] = False
    return redirect(url_for("home"))

@app.get("/registration")
def registration():
    data = load_data()
    voter_name = get_voter_name()
    return render_template("registration.html", 
                         players=data["players"],
                         is_admin=is_admin(),
                         voter_name=voter_name,
                         voting_open=data.get("voting_open", False))

@app.post("/registration/add")
def add_player():
    data = load_data()
    player_name = request.form.get("player_name", "").strip()
    
    if player_name and player_name not in data["players"]:
        data["players"].append(player_name)
        save_data(data)
        
        # Set this player as the voter for this session (unless admin)
        if not is_admin():
            session["voter_name"] = player_name
    
    return redirect(url_for("registration"))

@app.post("/registration/remove")
def remove_player():
    if not is_admin():
        return redirect(url_for("registration"))
    
    data = load_data()
    player_name = request.form.get("player_name", "").strip()
    
    if player_name in data["players"]:
        data["players"].remove(player_name)
        save_data(data)
    
    return redirect(url_for("registration"))

@app.post("/registration/complete")
def complete_registration():
    if not is_admin():
        return redirect(url_for("registration"))
    
    data = load_data()
    
    # Handle odd number of players by adding ghost
    if len(data["players"]) % 2 != 0:
        data["players"].append("GHOST PLAYER")
    
    data["phase"] = "voting"
    data["voting_open"] = True  # Open voting for users
    data["captain_votes"] = {player: 0 for player in data["players"]}
    data["voted_players"] = []
    save_data(data)
    
    return redirect(url_for("captain_voting"))

@app.get("/captain-voting")
def captain_voting():
    data = load_data()
    voter_name = get_voter_name()
    has_voted = voter_name in data.get("voted_players", [])
    
    return render_template("captain_voting.html", 
                         players=data["players"],
                         votes=data.get("captain_votes", {}),
                         is_admin=is_admin(),
                         voter_name=voter_name,
                         has_voted=has_voted,
                         voting_open=data.get("voting_open", False))

@app.post("/captain-voting/vote")
def vote_captain():
    data = load_data()
    voter_name = get_voter_name()
    
    # Check if voting is open
    if not data.get("voting_open", False):
        return redirect(url_for("captain_voting"))
    
    # Check if this person has already voted
    if voter_name in data.get("voted_players", []):
        return redirect(url_for("captain_voting"))
    
    # Check if voter is registered
    if not voter_name or voter_name not in data["players"]:
        return redirect(url_for("registration"))
    
    captain1 = request.form.get("captain1")
    captain2 = request.form.get("captain2")
    
    if captain1 and captain2 and captain1 != captain2:
        data["captain_votes"][captain1] = data["captain_votes"].get(captain1, 0) + 1
        data["captain_votes"][captain2] = data["captain_votes"].get(captain2, 0) + 1
        
        # Mark this player as having voted
        if "voted_players" not in data:
            data["voted_players"] = []
        data["voted_players"].append(voter_name)
    
    save_data(data)
    return redirect(url_for("captain_voting"))

@app.post("/captain-voting/finalize")
def finalize_captains():
    if not is_admin():
        return redirect(url_for("captain_voting"))
    
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
    data["voting_open"] = False  # Close voting
    
    save_data(data)
    return redirect(url_for("team_naming"))

@app.get("/team-naming")
def team_naming():
    if not is_admin():
        return redirect(url_for("home"))
    
    data = load_data()
    return render_template("team_naming.html", captains=data["captains"])

@app.post("/team-naming/save")
def save_team_names():
    if not is_admin():
        return redirect(url_for("home"))
    
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
    if not is_admin():
        return redirect(url_for("home"))
    
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
    if not is_admin():
        return redirect(url_for("draft"))
    
    data = load_data()
    player = request.form.get("player")
    turn = data["current_draft_turn"]
    
    if player and player in data["available_players"]:
        # True snake draft logic
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
        
        if len(data["available_players"]) == 0:
            data["phase"] = "team_creation"
        
        save_data(data)
    
    return redirect(url_for("draft"))

@app.get("/team-creation")
def team_creation():
    if not is_admin():
        return redirect(url_for("home"))
    
    data = load_data()
    
    if "team_pairings" not in data:
        data["team_pairings"] = {}
    
    if "captain1" not in data["team_pairings"]:
        current_captain = 0
    elif "captain2" not in data["team_pairings"]:
        current_captain = 1
    else:
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
    if not is_admin():
        return redirect(url_for("team_creation"))
    
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
    
    if "team_pairings" not in data:
        data["team_pairings"] = {}
    
    captain_key = f"captain{current_captain + 1}"
    data["team_pairings"][captain_key] = teams
    
    save_data(data)
    return redirect(url_for("team_creation"))

@app.get("/match-setup")
def match_setup():
    if not is_admin():
        return redirect(url_for("home"))
    
    data = load_data()
    return render_template("match_setup.html",
                         captains=data["captains"],
                         team_names=data.get("team_names", {}),
                         pairings=data.get("team_pairings", {}))

@app.post("/match-setup/create")
def create_matches():
    if not is_admin():
        return redirect(url_for("match_setup"))
    
    data = load_data()
    
    matches = []
    match_num = 1
    
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
            "result": None
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
                         captains=data.get("captains", []),
                         team_names=data.get("team_names", {}),
                         is_admin=is_admin())

@app.post("/active/record-result")
def record_result():
    if not is_admin():
        return redirect(url_for("active_tournament"))
    
    data = load_data()
    match_id = int(request.form.get("match_id"))
    result = request.form.get("result")
    
    for match in data["matches"]:
        if match["id"] == match_id:
            match["result"] = result
            break
    
    save_data(data)
    return redirect(url_for("active_tournament"))

@app.get("/standings")
def standings():
    data = load_data()
    
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
                         ties=ties,
                         team_names=data.get("team_names", {}))

@app.post("/reset")
def reset_tournament():
    if not is_admin():
        return redirect(url_for("home"))
    
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)