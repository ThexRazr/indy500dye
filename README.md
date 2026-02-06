# Indy 500 Dye Tourney App

A Flask-based web application for managing beer dye tournaments with snake drafts, team creation, and live match tracking.

## Features

- **Player Registration**: Everyone enters their name to join
- **Captain Voting**: Vote for 2 captains via card selection
- **Snake Draft**: Captains alternate picking players for their teams
- **Team Creation**: Each captain pairs their players into teams of 2
- **Match Setup**: Captains choose which of their teams face off
- **Live Tracking**: Record match results in real-time
- **Standings**: See who's winning with a visual leaderboard

## Install Instructions

- **Clone the repository locally, Python 3.11 is recommended**
- **Once /venv is created you can just activate it and then run the app through Step 4**

1. Create the virtual environment within the project folder
```bash
python -m venv venv
```
2. Activate the virtual environment
```bash
venv\Scripts\activate
```
3. Install dependencies
```bash
pip install flask
```
4. Run the app through local host
```bash
python app.py
```
5. Click the link http://127.0.0.1:5000 within your terminal, use CTRL+C to close

## File Structure

```
beer-dye-tournament/
├── app.py                    # Main Flask application
├── tournament_data.json      # Tournament state (auto-created)
├── static/
│   └── css/
│       └── style.css         # All styling
└── templates/
    ├── home.html            # Main navigation
    ├── registration.html    # Player signup
    ├── captain_voting.html  # Captain selection
    ├── draft.html           # Snake draft
    ├── team_creation.html   # Pair players into teams of 2
    ├── match_setup.html     # Create matchups
    ├── active.html          # Record results
    └── standings.html       # View leaderboard
```

## How It Works

1. **Start Tournament** - Players add their names
2. **Vote for Captains** - Everyone votes, top 2 become captains
3. **Snake Draft** - Captains alternate picking players (16 each for 32 total players)
4. **Create Teams** - Each captain makes 8 teams of 2 from their 16 players
5. **Set Matchups** - Captains pick which teams face each other
6. **Play & Track** - Record wins/losses as matches complete
7. **View Standings** - See which captain's teams are dominating

## Notes

- Handles odd player counts by adding a "GHOST PLAYER"
- All data stored in `tournament_data.json` (persists between runs)
- Reset button on home page clears everything
- Fully responsive design

## Customization

Want to change colors? Edit the CSS variables in `static/css/style.css`:
```css
:root {
  --primary: #ff6b35;      /* Main orange */
  --secondary: #f7931e;    /* Secondary orange */
  --accent: #fbb03b;       /* Yellow accent */
  --success: #4ecdc4;      /* Teal for wins */
  /* ... etc ... */
}
```

## Future Ideas

- Mobile voting via QR codes
- SQLite database for multiple tournaments
- Best-of-3 match formats
- Photo uploads for teams
- Playoff brackets

Enjoy the tournament! 🍻
